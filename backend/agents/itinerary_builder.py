"""ItineraryBuilderAgent: generates itinerary from verified place candidates."""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

from backend.state import TripState
from backend.schemas.places import PlaceCandidate
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class LLMItineraryItem(BaseModel):
    place_id: str
    start_time: str
    end_time: str
    description: str
    estimated_cost: float = Field(default=0, ge=0)
    notes: str = ""


class LLMDayPlan(BaseModel):
    day_number: int = Field(..., ge=1)
    title: str
    items: List[LLMItineraryItem] = Field(default_factory=list)


class LLMItinerary(BaseModel):
    destination: str
    days: List[LLMDayPlan] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


ITINERARY_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "aethertrip_itinerary",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["destination", "days", "warnings"],
            "properties": {
                "destination": {"type": "string"},
                "warnings": {"type": "array", "items": {"type": "string"}},
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["day_number", "title", "items"],
                        "properties": {
                            "day_number": {"type": "integer", "minimum": 1},
                            "title": {"type": "string"},
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": [
                                        "place_id",
                                        "start_time",
                                        "end_time",
                                        "description",
                                        "estimated_cost",
                                        "notes",
                                    ],
                                    "properties": {
                                        "place_id": {"type": "string"},
                                        "start_time": {"type": "string"},
                                        "end_time": {"type": "string"},
                                        "description": {"type": "string"},
                                        "estimated_cost": {"type": "number", "minimum": 0},
                                        "notes": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


FALLBACK_WARNING = (
    "LLM itinerary generation failed or was invalid; used verified candidate fallback."
)


class ItineraryBuilderAgent:
    """Builds day-by-day itineraries using verified place candidates only."""

    def __init__(self):
        self.llm = LLMService()
        self.use_llm = os.getenv("AETHERTRIP_USE_LLM_ITINERARY", "true").lower() == "true"
        self.model_name = os.getenv("OPENROUTER_MODEL", "openai/gpt-4-turbo")

    def run(self, state: TripState) -> Dict[str, Any]:
        """Generate itinerary from constraints and place candidates."""
        logger.info("ItineraryBuilderAgent started trip_id=%s", state.trip_id or "unknown")

        constraints = state.constraints or {}
        hard = constraints.get("hard", {}) if isinstance(constraints, dict) else {}
        num_days = max(1, int(hard.get("duration_days") or state.duration_days or 3))
        destination = hard.get("destination") or state.destination or "Trip destination"
        candidates = self._coerce_candidates(state.place_candidates)
        candidate_lookup = {place.id: place for place in candidates}

        logger.info(
            "ItineraryBuilderAgent input trip_id=%s destination=%s duration_days=%s travelers=%s budget=%s candidates=%s weather_available=%s route_matrix_available=%s",
            state.trip_id or "unknown",
            destination,
            num_days,
            hard.get("travelers") or state.travelers,
            hard.get("budget_per_person") or state.budget_per_person,
            len(candidates),
            bool(state.weather_data),
            bool(state.route_matrix),
        )

        if not candidates:
            logger.error("ItineraryBuilderAgent: no place candidates available; refusing to invent stops")
            return {
                "itinerary": {
                    "destination": destination,
                    "days": [],
                    "total_estimated_cost_per_person": 0,
                    "generation_method": None,
                    "warnings": [],
                },
                "errors": ["No place candidates available for itinerary generation"],
                "service_status": {
                    "llm": {
                        "provider": "openrouter",
                        "status": "skipped",
                        "model": self.model_name,
                        "used_fallback": False,
                    },
                    "itinerary_builder": self._builder_status("failed", 0, 0),
                },
            }

        llm_status = {
            "provider": "openrouter",
            "status": "skipped",
            "model": self.model_name,
            "used_fallback": False,
        }
        warnings: List[str] = []

        llm_itinerary = self._generate_llm_itinerary(
            destination,
            num_days,
            candidates,
            constraints,
            weather_data=state.weather_data,
            route_matrix=state.route_matrix,
        )

        if llm_itinerary:
            llm_status = {
                "provider": "openrouter",
                "status": "success",
                "model": self.model_name,
                "used_fallback": False,
            }
            hydrated, invalid_ids = self._hydrate_itinerary(llm_itinerary, destination, candidate_lookup)
            if invalid_ids:
                warnings.append(f"Removed itinerary items with unknown place IDs: {', '.join(invalid_ids)}")
                llm_status = {
                    **llm_status,
                    "status": "rejected_invalid_place_ids",
                    "used_fallback": True,
                    "unknown_place_ids": invalid_ids,
                }

            hydrated_item_count = self._count_items(hydrated)
            if hydrated_item_count > 0 and len(hydrated.get("days", [])) >= num_days and not invalid_ids:
                hydrated["generation_method"] = "openrouter_structured"
                days_count = len(hydrated.get("days", []))
                logger.info(
                    "ItineraryBuilderAgent completed trip_id=%s generation_method=openrouter_structured days=%s items=%s",
                    state.trip_id or "unknown",
                    days_count,
                    hydrated_item_count,
                )
                return {
                    "itinerary": hydrated,
                    "service_status": {
                        "llm": llm_status,
                        "itinerary_builder": self._builder_status("success", days_count, hydrated_item_count),
                    },
                    "warnings": warnings,
                }

            if hydrated_item_count == 0:
                warnings.append("LLM itinerary contained no valid candidate place IDs.")
            elif len(hydrated.get("days", [])) < num_days:
                warnings.append("LLM itinerary returned fewer days than requested.")

        elif self.use_llm:
            llm_status = {
                **llm_status,
                "status": "fallback",
                "used_fallback": True,
            }

        if self.use_llm:
            if FALLBACK_WARNING not in warnings:
                warnings.append(FALLBACK_WARNING)
        else:
            warnings.append("LLM itinerary generation disabled; used deterministic itinerary from verified candidates.")

        itinerary = self.build_deterministic_fallback(
            destination,
            num_days,
            candidates,
            warnings,
            route_matrix=state.route_matrix or {},
        )
        unknown_ids = self._unknown_place_ids(itinerary, candidate_lookup)
        days_count = len(itinerary.get("days", []))
        item_count = self._count_items(itinerary)

        if unknown_ids or item_count == 0:
            logger.error("Candidate itinerary invalid after fallback; unknown place_ids=%s", unknown_ids)
            failed_llm_status = llm_status if not self.use_llm else {**llm_status, "used_fallback": True}
            return {
                "itinerary": {
                    "destination": destination,
                    "days": [],
                    "total_estimated_cost_per_person": 0,
                    "generation_method": None,
                    "warnings": warnings,
                },
                "errors": ["Itinerary validation failed because generated stops did not match place candidates."],
                "service_status": {
                    "llm": failed_llm_status,
                    "itinerary_builder": self._builder_status("failed", 0, 0),
                },
                "warnings": warnings,
            }

        final_llm_status = llm_status if not self.use_llm else {**llm_status, "used_fallback": True}

        logger.info(
            "ItineraryBuilderAgent completed trip_id=%s generation_method=deterministic_candidate_fallback days=%s items=%s",
            state.trip_id or "unknown",
            days_count,
            item_count,
        )
        return {
            "itinerary": itinerary,
            "service_status": {
                "llm": final_llm_status,
                "itinerary_builder": self._builder_status("fallback", days_count, item_count),
            },
            "warnings": warnings,
        }

    def _coerce_candidates(self, raw_candidates: List[Any]) -> List[PlaceCandidate]:
        """Convert state dictionaries to PlaceCandidate models."""
        candidates: List[PlaceCandidate] = []
        for raw in raw_candidates or []:
            try:
                candidate = raw if isinstance(raw, PlaceCandidate) else PlaceCandidate(**raw)
            except Exception as exc:
                logger.warning("Skipping invalid place candidate: %s", type(exc).__name__)
                continue
            if candidate.id and candidate.name and candidate.latitude is not None and candidate.longitude is not None:
                candidates.append(candidate)
        return candidates

    def _generate_llm_itinerary(
        self,
        destination: str,
        num_days: int,
        candidates: List[PlaceCandidate],
        constraints: Dict[str, Any],
        *,
        weather_data: Optional[Dict[str, Any]] = None,
        route_matrix: Optional[Dict[str, Any]] = None,
    ) -> Optional[LLMItinerary]:
        """Ask OpenRouter for sequencing and validate the response with Pydantic."""
        if not self.use_llm:
            return None

        safe_candidates = [
            {
                "id": place.id,
                "name": place.name,
                "category": place.category,
                "address": place.address,
                "lat": place.latitude,
                "lon": place.longitude,
                "cost": place.estimated_cost,
                "confidence": place.source_confidence or place.confidence,
                "rank_score": place.candidate_rank_score,
            }
            for place in self._rank_candidates_for_mix(candidates)
        ]
        prompt = f"""
Build a {num_days}-day itinerary for {destination}.

User constraints:
{json.dumps(constraints, default=str)}

Candidate places:
{json.dumps(safe_candidates, default=str)}

Weather summary, if available:
{json.dumps(self._compact_weather(weather_data), default=str)}

Route matrix summary, if available:
{json.dumps(self._compact_route_matrix(route_matrix), default=str)}

Strict rules:
- Use ONLY place_id values from the provided Candidate places list.
- Do not invent places, IDs, coordinates, or placeholder stops.
- Return JSON only, matching the requested schema exactly.
- If there are not enough unique candidates, reuse candidate IDs rather than inventing new IDs.
"""
        try:
            response = self.llm.call_openrouter(
                prompt,
                system_instruction="You are AetherTrip's itinerary sequencer. Return only valid JSON matching the schema.",
                response_format=ITINERARY_JSON_SCHEMA,
            )
            logger.info(
                "ItineraryBuilderAgent raw LLM response length=%s destination=%s model=%s",
                len(response or ""),
                destination,
                self.model_name,
            )
            parsed = self._parse_llm_response(response)
            logger.info(
                "ItineraryBuilderAgent JSON validation %s destination=%s days=%s",
                "success" if parsed else "failed",
                destination,
                len(parsed.days) if parsed else 0,
            )
            return parsed
        except Exception:
            logger.exception("LLM itinerary generation failed; falling back to verified candidates")
            return None

    def _parse_llm_response(self, response: str) -> Optional[LLMItinerary]:
        """Validate LLM JSON with Pydantic, with a small fence-stripping fallback."""
        if not response:
            return None
        try:
            return LLMItinerary.model_validate_json(response)
        except ValidationError:
            pass

        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first >= 0 and last > first:
            cleaned = cleaned[first:last + 1]
        try:
            return LLMItinerary.model_validate_json(cleaned)
        except ValidationError as exc:
            logger.warning("LLM itinerary schema validation failed: %s", exc.errors()[:2])
            return None

    def build_deterministic_fallback(
        self,
        destination: str,
        num_days: int,
        candidates: List[PlaceCandidate],
        warnings: Optional[List[str]] = None,
        route_matrix: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a deterministic schedule using only candidate IDs and metadata."""
        time_slots = [("09:00", "11:00"), ("12:00", "13:30"), ("15:00", "17:00")]
        ordered = self._rank_candidates_for_mix(candidates)
        days = []
        total_cost = 0.0
        fallback_warnings = list(warnings or [])
        requested_minimum_slots = num_days * 2
        enough_unique = len(ordered) >= requested_minimum_slots
        if not enough_unique:
            fallback_warnings.append("Fewer than two unique candidates per day were available; verified candidates may be reused.")
        item_target = 3 if len(ordered) >= num_days * 3 else 2 if len(ordered) >= 2 else 1
        used_place_ids: set[str] = set()
        used_name_keys: set[str] = set()
        route_matrix = route_matrix or {}

        for day_index in range(num_days):
            day_items = []
            for slot_index in range(item_target):
                start_time, end_time = time_slots[slot_index]
                role = "morning" if slot_index == 0 else "lunch" if slot_index == 1 else "afternoon"
                previous_item = day_items[-1] if day_items else None
                candidate = self._select_candidate_for_slot(
                    ordered,
                    role=role,
                    used_place_ids=used_place_ids,
                    used_name_keys=used_name_keys,
                    enough_unique=enough_unique,
                    previous_item=previous_item,
                    start_time=start_time,
                    route_matrix=route_matrix,
                )
                if not candidate:
                    continue
                item = self._item_from_candidate(
                    candidate,
                    day=day_index + 1,
                    start_time=start_time,
                    end_time=end_time,
                )
                day_items.append(item)
                used_place_ids.add(candidate.id)
                used_name_keys.add(self._name_key(candidate.name))
                total_cost += item["estimated_cost"]

            days.append({
                "day": day_index + 1,
                "day_number": day_index + 1,
                "title": f"Day {day_index + 1}",
                "items": day_items,
                "estimated_day_cost": sum(item["estimated_cost"] for item in day_items),
            })

        return {
            "destination": destination,
            "days": days,
            "total_estimated_cost_per_person": total_cost,
            "generation_method": "deterministic_candidate_fallback",
            "warnings": fallback_warnings,
        }

    def _rank_candidates_for_mix(self, candidates: List[PlaceCandidate]) -> List[PlaceCandidate]:
        """Prefer a practical mix of attractions, parks/viewpoints, museums, and restaurants."""
        candidates = sorted(candidates, key=lambda place: place.candidate_rank_score, reverse=True)
        buckets: Dict[str, List[PlaceCandidate]] = {
            "viewpoint": [],
            "park": [],
            "museum": [],
            "restaurant": [],
            "attraction": [],
            "other": [],
        }
        for place in candidates:
            text = f"{place.category} {place.name} {place.description or ''}".lower()
            if "viewpoint" in text or "view" in text or "overlook" in text or "vista" in text:
                buckets["viewpoint"].append(place)
            elif "park" in text or "trail" in text or "waterfall" in text or "valley" in text or "beach" in text or "observatory" in text:
                buckets["park"].append(place)
            elif "museum" in text or "gallery" in text:
                buckets["museum"].append(place)
            elif "restaurant" in text or "cafe" in text or "food" in text or "market" in text:
                buckets["restaurant"].append(place)
            elif "attraction" in text or "tourism" in text or "landmark" in text:
                buckets["attraction"].append(place)
            else:
                buckets["other"].append(place)

        ordered: List[PlaceCandidate] = []
        seen = set()
        cycle = ["viewpoint", "park", "attraction", "museum", "restaurant", "other"]
        while len(ordered) < len(candidates):
            progressed = False
            for key in cycle:
                while buckets[key] and buckets[key][0].id in seen:
                    buckets[key].pop(0)
                if buckets[key]:
                    place = buckets[key].pop(0)
                    ordered.append(place)
                    seen.add(place.id)
                    progressed = True
            if not progressed:
                break
        return ordered or candidates

    def _select_candidate_for_slot(
        self,
        candidates: List[PlaceCandidate],
        *,
        role: str,
        used_place_ids: set[str],
        used_name_keys: set[str],
        enough_unique: bool,
        previous_item: Optional[Dict[str, Any]],
        start_time: str,
        route_matrix: Dict[str, Any],
    ) -> Optional[PlaceCandidate]:
        preferred = []
        fallback = []
        for candidate in candidates:
            if enough_unique and candidate.id in used_place_ids:
                continue
            name_key = self._name_key(candidate.name)
            if enough_unique and name_key in used_name_keys:
                continue
            if previous_item and not self._transition_fits(previous_item, candidate.id, start_time, route_matrix):
                continue
            if self._candidate_matches_role(candidate, role):
                preferred.append(candidate)
            else:
                fallback.append(candidate)

        preferred_strong = [candidate for candidate in preferred if not self._is_weak_candidate(candidate)]
        fallback_strong = [candidate for candidate in fallback if not self._is_weak_candidate(candidate)]
        pool = preferred_strong or fallback_strong or preferred or fallback
        if pool:
            return sorted(pool, key=lambda candidate: candidate.candidate_rank_score, reverse=True)[0]
        if enough_unique:
            return None

        for candidate in candidates:
            if previous_item and not self._transition_fits(previous_item, candidate.id, start_time, route_matrix):
                continue
            return candidate
        return None

    def _is_weak_candidate(self, candidate: PlaceCandidate) -> bool:
        text = f"{candidate.category} {candidate.name} {candidate.address or ''} {candidate.description or ''}".lower()
        weak_terms = [
            "parking",
            "car park",
            "road",
            "atm",
            "bank",
            "fuel",
            "gas station",
            "railway",
            "railroad",
            "caboose",
            "locomotive",
            "platform",
            "crossing",
            "hotel",
            "motel",
            "lodging",
        ]
        return any(term in text for term in weak_terms) or candidate.candidate_rank_score < 35

    def _candidate_matches_role(self, candidate: PlaceCandidate, role: str) -> bool:
        text = f"{candidate.category} {candidate.name} {candidate.description or ''}".lower()
        if role == "lunch":
            return any(term in text for term in ["restaurant", "cafe", "food", "market"])
        if role == "morning":
            return any(term in text for term in ["view", "viewpoint", "overlook", "vista", "attraction", "sights", "waterfall", "trail", "valley", "park", "observatory"])
        return any(term in text for term in ["park", "museum", "view", "viewpoint", "gallery", "trail", "waterfall", "attraction", "sights"])

    def _transition_fits(
        self,
        previous_item: Dict[str, Any],
        next_place_id: str,
        next_start_time: str,
        route_matrix: Dict[str, Any],
    ) -> bool:
        if not route_matrix:
            return True
        travel_time = (route_matrix.get(previous_item.get("place_id")) or {}).get(next_place_id)
        if travel_time is None:
            return True
        available = self._minutes_between(previous_item.get("end_time"), next_start_time)
        return available >= int(travel_time) + 15

    def _minutes_between(self, end_time: Optional[str], start_time: Optional[str]) -> int:
        try:
            end_hour, end_minute = [int(part) for part in (end_time or "").split(":")]
            start_hour, start_minute = [int(part) for part in (start_time or "").split(":")]
        except ValueError:
            return 0
        return (start_hour * 60 + start_minute) - (end_hour * 60 + end_minute)

    def _name_key(self, name: str) -> str:
        normalized = re.sub(r"\b(no\.?|number|#)\s*\d+\b", "", (name or "").lower())
        normalized = re.sub(r"\b\d+\b", "", normalized)
        normalized = re.sub(r"[^a-z]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def _hydrate_itinerary(
        self,
        raw_itinerary: Any,
        destination: str,
        candidate_lookup: Dict[str, PlaceCandidate],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Replace LLM item display data with trusted candidate data and drop unknown IDs."""
        itinerary_model = (
            raw_itinerary
            if isinstance(raw_itinerary, LLMItinerary)
            else LLMItinerary.model_validate(self._normalize_raw_itinerary(raw_itinerary, destination))
        )
        hydrated_days = []
        invalid_ids: List[str] = []
        total_cost = 0.0
        used_ids: set[str] = set()
        used_name_keys: set[str] = set()

        for day in itinerary_model.days:
            day_items = []
            for item in day.items:
                place = candidate_lookup.get(item.place_id)
                if not place:
                    invalid_ids.append(item.place_id)
                    continue
                name_key = self._name_key(place.name)
                if place.id in used_ids and len(candidate_lookup) >= 2:
                    invalid_ids.append(item.place_id)
                    continue
                if name_key in used_name_keys and len(candidate_lookup) >= 2:
                    invalid_ids.append(item.place_id)
                    continue
                hydrated_item = self._item_from_candidate(
                    place,
                    day=day.day_number,
                    start_time=item.start_time or "09:00",
                    end_time=item.end_time or "11:00",
                    description=item.description,
                    estimated_cost=item.estimated_cost,
                    notes=item.notes,
                )
                day_items.append(hydrated_item)
                used_ids.add(place.id)
                used_name_keys.add(name_key)
                total_cost += hydrated_item["estimated_cost"]
            if day_items:
                hydrated_days.append({
                    "day": day.day_number,
                    "day_number": day.day_number,
                    "title": day.title or f"Day {day.day_number}",
                    "items": day_items,
                    "estimated_day_cost": sum(float(item.get("estimated_cost") or 0) for item in day_items),
                })

        return {
            "destination": itinerary_model.destination or destination,
            "days": hydrated_days,
            "total_estimated_cost_per_person": total_cost,
            "warnings": itinerary_model.warnings,
        }, sorted(set(invalid_ids))

    def _normalize_raw_itinerary(self, raw_itinerary: Any, destination: str) -> Dict[str, Any]:
        """Accept legacy dict shapes from tests or older model responses before validation."""
        raw = dict(raw_itinerary or {})
        normalized_days = []
        for index, day in enumerate(raw.get("days", []) or [], start=1):
            day_dict = dict(day or {})
            normalized_items = []
            for item in day_dict.get("items", []) or []:
                item_dict = dict(item or {})
                normalized_items.append({
                    "place_id": item_dict.get("place_id") or "",
                    "start_time": item_dict.get("start_time") or "09:00",
                    "end_time": item_dict.get("end_time") or "11:00",
                    "description": item_dict.get("description") or "",
                    "estimated_cost": item_dict.get("estimated_cost") or 0,
                    "notes": item_dict.get("notes") or "",
                })
            day_number = day_dict.get("day_number") or day_dict.get("day") or index
            normalized_days.append({
                "day_number": day_number,
                "title": day_dict.get("title") or f"Day {day_number}",
                "items": normalized_items,
            })
        return {
            "destination": raw.get("destination") or destination,
            "days": normalized_days,
            "warnings": raw.get("warnings") or [],
        }

    def _item_from_candidate(
        self,
        place: PlaceCandidate,
        *,
        day: int,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        estimated_cost: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        cost = float(estimated_cost if estimated_cost is not None else place.estimated_cost or 0)
        item_description = description or place.description or self._default_description(place)
        return {
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "place_id": place.id,
            "place_name": place.name,
            "category": place.category,
            "description": item_description,
            "estimated_cost": cost,
            "source_confidence": place.source_confidence or place.confidence,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "address": place.address,
            "verification_status": place.verification_status,
            "candidate_rank_score": place.candidate_rank_score,
            "image_url": place.image_url or place.place_image_url,
            "image_source": place.image_source,
            "image_credit": place.image_credit,
            "image_confidence": place.image_confidence,
            "notes": notes or "",
        }

    def _unknown_place_ids(self, itinerary: Dict[str, Any], candidate_lookup: Dict[str, PlaceCandidate]) -> List[str]:
        unknown = []
        for day in itinerary.get("days", []) or []:
            for item in day.get("items", []) or []:
                place_id = item.get("place_id")
                if place_id not in candidate_lookup:
                    unknown.append(str(place_id))
        return sorted(set(unknown))

    def _count_items(self, itinerary: Dict[str, Any]) -> int:
        return sum(len(day.get("items", []) or []) for day in itinerary.get("days", []) or [])

    def _builder_status(self, status: str, days_count: int, items_count: int) -> Dict[str, Any]:
        return {
            "provider": "aethertrip",
            "status": status,
            "days_count": days_count,
            "items_count": items_count,
        }

    def _compact_weather(self, weather_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not weather_data:
            return {}
        forecast = weather_data.get("forecast") if isinstance(weather_data, dict) else {}
        daily = forecast.get("daily", {}) if isinstance(forecast, dict) else {}
        return {
            "destination": weather_data.get("destination"),
            "dates": (daily.get("time") or [])[:5],
            "precipitation_probability_max": (daily.get("precipitation_probability_max") or [])[:5],
            "weather_code": (daily.get("weather_code") or [])[:5],
        }

    def _compact_route_matrix(self, route_matrix: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not route_matrix:
            return {}
        return {
            key: value
            for key, value in route_matrix.items()
            if key != "_meta"
        }

    def _default_description(self, place: PlaceCandidate) -> str:
        if place.category == "restaurant":
            return f"Meal stop at {place.name}."
        if place.category == "hotel":
            return f"Accommodation or rest stop at {place.name}."
        return f"Visit {place.name}."
