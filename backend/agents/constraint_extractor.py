"""
ConstraintExtractorAgent: converts parsed input to TripConstraints schema.
"""

import logging
import re
from typing import Dict, Any

from backend.state import TripState
from backend.schemas.constraints import HardConstraints, SoftPreferences, TripConstraints
from backend.services.llm_service import LLMService
from backend.agents.input_analyzer import CITY_ALIASES

logger = logging.getLogger(__name__)


class ConstraintExtractorAgent:
    """Extracts structured constraints from parsed request."""
    
    def __init__(self):
        self.llm = LLMService()
    
    def run(self, state: TripState) -> Dict[str, Any]:
        """
        Convert parsed_request to TripConstraints schema.
        
        Returns:
            Updated state with constraints
        """
        logger.info("ConstraintExtractorAgent: extracting constraints raw user input=%s", state.user_input)
        
        try:
            parsed = self._merge_with_fallback(state.parsed_request or {}, state.user_input)
            destination_value = parsed.get("destination") or parsed.get("destinations")
            if isinstance(destination_value, list):
                destination = destination_value[0] if destination_value else None
            else:
                destination = destination_value

            if not destination:
                destination = parsed.get("destination")
            destination = self._clean_place_name(destination)
            if not destination:
                logger.info("ConstraintExtractorAgent: no destination extracted defaults_applied=%s", parsed.get("defaults_applied", []))
                return {
                    "errors": ["Need destination: please include a city or place to plan around."],
                    "destination": None,
                }

            origin = self._clean_origin_name(parsed.get("origin")) or None
            duration_days = parsed.get("duration_days") or self._extract_duration_days(parsed.get("dates", ""), state.user_input)
            travelers = parsed.get("travelers") or 1
            budget_per_person = parsed.get("budget_per_person")
            diet = list(parsed.get("diet") or [])
            text_lower = (state.user_input or "").lower()
            transport_mode = parsed.get("transport_mode")
            if not transport_mode or transport_mode in {"mixed", "Unknown"}:
                transport_mode = "public_transit"
            if any(phrase in text_lower for phrase in ["no car", "no-car", "without a car", "car-free"]):
                transport_mode = "no_car"
            no_car = transport_mode == "no_car"
            budget_status = "specified" if budget_per_person is not None else "unknown"
            defaults_applied = list(parsed.get("defaults_applied") or [])
            
            # Build hard constraints from parsed request
            hard = HardConstraints(
                origin=origin,
                destination=destination,
                duration_days=duration_days,
                travelers=travelers,
                budget_per_person=budget_per_person,
                budget_status=budget_status,
                currency=parsed.get("currency", "USD"),
                transport_mode=transport_mode,
                diet=diet,
                no_car=no_car,
                weather_preference=parsed.get("weather_preference"),
                must_visit=parsed.get("must_visit", []),
                avoid=parsed.get("avoid", []),
            )
            
            # Build soft preferences
            soft = SoftPreferences(
                pace="balanced",
                interests=parsed.get("interests", []),
                trip_style=parsed.get("trip_style"),
                budget_style=parsed.get("budget_style"),
                food_style=parsed.get("food_style"),
                hotel_style=parsed.get("hotel_style"),
            )
            
            constraints = TripConstraints(hard=hard, soft=soft)
            
            logger.info(
                "Constraints extracted destination=%s duration_days=%s travelers=%s budget_per_person=%s diet=%s transport_mode=%s defaults_applied=%s",
                hard.destination,
                hard.duration_days,
                hard.travelers,
                hard.budget_per_person,
                hard.diet,
                hard.transport_mode,
                defaults_applied,
            )
            
            return {
                "constraints": constraints.model_dump(),
                "origin": hard.origin,
                "destination": hard.destination,
                "duration_days": hard.duration_days,
                "travelers": hard.travelers,
                "budget_per_person": hard.budget_per_person,
                "budget_status": hard.budget_status,
                "budget_style": soft.budget_style,
                "dietary_preferences": hard.diet,
                "transport_mode": hard.transport_mode,
                "no_car": hard.no_car,
                "weather_preference": hard.weather_preference,
            }
        
        except Exception as e:
            logger.error(f"Constraint extraction failed: {e}")
            return {"errors": [f"Constraint extraction failed: {e}"]}
    
    def _extract_duration_days(self, dates_str: str, user_input: str = "") -> int:
        """Extract number of days from duration string."""
        combined = f"{dates_str or ''} {user_input or ''}"
        match = re.search(r"(\d+)\s*(?:-\s*)?days?", combined, re.IGNORECASE)
        if match:
            return int(match.group(1))
        if "weekend" in combined.lower():
            return 2
        
        # Default
        return 3

    def _fallback_parse_from_input(self, text: str) -> Dict[str, Any]:
        """Small safety net so known prompt values never collapse to Unknown."""
        parsed: Dict[str, Any] = {}
        text_lower = text.lower()
        destination = self._extract_destination(text)
        if destination:
            parsed["destination"] = destination

        destination_match = re.search(
            r"\b(?:\d+\s*-\s*day|\d+\s*day|weekend|day)\s+([a-z][a-z\s]+?)\s+(?:trip|travel|vacation)\b",
            text,
            re.IGNORECASE,
        ) or re.search(
            r"\b(?:to|visit|in)\s+([a-z][a-z\s]+?)(?:\s+from|\s+for|\s+under|\s+with|,|\.|$)",
            text,
            re.IGNORECASE,
        )
        if destination_match and not parsed.get("destination"):
            parsed["destination"] = self._clean_place_name(destination_match.group(1))

        origin_match = re.search(
            r"(?:from|starting\s+in|leaving\s+from)\s+([a-z][a-z\s]+?)(?:\s+to|\s+for\s+\d+|\s+under|\s+with|,|\.|$)",
            text,
            re.IGNORECASE,
        )
        if origin_match:
            parsed["origin"] = origin_match.group(1).strip().title()

        duration_match = re.search(r"(\d+)\s*(?:-\s*)?days?", text, re.IGNORECASE)
        if duration_match:
            parsed["duration_days"] = int(duration_match.group(1))

        travelers_match = re.search(r"(?:for|with)\s+(\d+)\s+(?:people|friends|travelers|travellers|persons?|adults?)", text, re.IGNORECASE)
        if travelers_match:
            parsed["travelers"] = int(travelers_match.group(1))

        budget_match = re.search(r"(?:under|less than|budget|max(?:imum)?|up to)\s+\$?([\d,]+)", text, re.IGNORECASE)
        if budget_match:
            parsed["budget_per_person"] = float(budget_match.group(1).replace(",", ""))

        if "vegetarian" in text_lower:
            parsed["diet"] = ["vegetarian"]
        if "no car" in text_lower or "no-car" in text_lower or "without a car" in text_lower or "car-free" in text_lower:
            parsed["transport_mode"] = "no_car"
        elif "public transit" in text_lower or "public transport" in text_lower:
            parsed["transport_mode"] = "public_transit"
        else:
            parsed["transport_mode"] = "public_transit"

        if "weekend" in text_lower and "duration_days" not in parsed:
            parsed["duration_days"] = 2
        parsed.setdefault("duration_days", 3)
        parsed.setdefault("travelers", 1)
        parsed["budget_status"] = "specified" if parsed.get("budget_per_person") is not None else "unknown"
        if "budget" in text_lower:
            parsed["budget_style"] = "budget"
        if "rain-safe" in text_lower or "rain safe" in text_lower:
            parsed["weather_preference"] = "rain_safe"

        interests = list(parsed.get("interests") or [])
        if parsed.get("diet") and "food" not in interests:
            interests.append("food")
        if "rain-safe" in text_lower or "rain safe" in text_lower:
            interests.extend([interest for interest in ["museum", "attraction"] if interest not in interests])
        parsed["interests"] = interests

        defaults_applied = []
        if "duration_days" not in parsed:
            defaults_applied.append("duration_days=3")
        if not parsed.get("origin"):
            defaults_applied.append("origin=null")
        if parsed.get("budget_per_person") is None:
            defaults_applied.append("budget_per_person=null")
        parsed["defaults_applied"] = defaults_applied

        return parsed

    def _merge_with_fallback(self, parsed_request: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Fill missing/invalid parsed fields with deterministic regex extraction."""
        parsed = dict(parsed_request or {})
        fallback = self._fallback_parse_from_input(user_input)

        for key, value in fallback.items():
            current = parsed.get(key)
            if key == "destination":
                if isinstance(current, list):
                    current_missing = not current or current[0] in (None, "", "Unknown", "Your Trip")
                else:
                    current_missing = current in (None, "", "Unknown", "Your Trip")
            else:
                current_missing = current in (None, "", [], "Unknown", "Your Trip")

            if current_missing:
                parsed[key] = value

        if isinstance(parsed.get("destination"), str):
            parsed["destination"] = [parsed["destination"]]

        text_lower = (user_input or "").lower()
        if not parsed.get("dates") and not parsed.get("duration_days"):
            parsed["dates"] = "2 days" if "weekend" in text_lower else "3 days"
        if not parsed.get("duration_days"):
            parsed["duration_days"] = 2 if "weekend" in text_lower else 3
        if not parsed.get("travelers"):
            parsed["travelers"] = 1
        if "budget_per_person" not in parsed:
            parsed["budget_per_person"] = None
        if not parsed.get("budget_status"):
            parsed["budget_status"] = "unknown"
        if not parsed.get("transport_mode"):
            parsed["transport_mode"] = "public_transit"
        if not parsed.get("pace"):
            parsed["pace"] = "balanced"
        if "budget" in text_lower and not parsed.get("budget_style"):
            parsed["budget_style"] = "budget"
        if "rain-safe" in text_lower or "rain safe" in text_lower:
            parsed["weather_preference"] = "rain_safe"
        if parsed.get("origin") in {"Unknown", ""}:
            parsed["origin"] = None

        return parsed

    def _extract_destination(self, text: str) -> str:
        """Recognize compact city aliases and leading destination phrases."""
        text_lower = (text or "").lower()
        for alias, canonical in sorted(CITY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            pattern = r"(?<![a-z])" + re.escape(alias.lower()) + r"(?![a-z])"
            if re.search(pattern, text_lower):
                return canonical

        quick_match = re.search(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:itinerary|trip|weekend)\b",
            text or "",
        )
        if quick_match:
            return self._clean_place_name(quick_match.group(1))
        return ""

    def _clean_place_name(self, value: Any) -> str:
        """Normalize place names without converting known missing sentinels to real values."""
        if value is None:
            return ""
        if isinstance(value, list):
            value = value[0] if value else ""
        cleaned = re.sub(r"\s+", " ", str(value)).strip(" ,.")
        if cleaned.lower() in {"unknown", "your trip", "trip destination"}:
            return ""
        alias = CITY_ALIASES.get(cleaned.lower())
        if alias:
            return alias
        if cleaned.isupper() and len(cleaned) <= 4:
            return CITY_ALIASES.get(cleaned.lower(), cleaned)
        return cleaned.title()

    def _clean_origin_name(self, value: Any) -> str:
        """Normalize origin without expanding abbreviations the user supplied."""
        if value is None:
            return ""
        cleaned = re.sub(r"\s+", " ", str(value)).strip(" ,.")
        if cleaned.lower() in {"unknown", "your trip", "trip destination"}:
            return ""
        if cleaned.isupper() and len(cleaned) <= 4:
            return cleaned
        return cleaned.title()
