"""
Places Service: Geoapify integration for place search, geocoding, and POI discovery.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import re
import math

import httpx

from backend.config import get_config
from backend.schemas.places import PlaceCandidate, SourceRef
from backend.services.cache_service import CacheService
from backend.services.image_service import ImageService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
config = get_config()


class PlacesService:
    """Fetch places and POIs from Geoapify with LLM-powered candidate generation."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize PlacesService."""
        self.cache_service = cache_service or CacheService()
        self.llm = LLMService()
        self.image_service = ImageService(self.cache_service)
        self.base_url = config.GEOAPIFY_BASE_URL
        self.api_key = config.GEOAPIFY_API_KEY
        self.allow_mock_places = os.getenv("AETHERTRIP_DEV_MOCK_PLACES", "false").lower() in {"1", "true", "yes"}
        self.last_geocoding_status: Dict[str, Any] = {
            "provider": "geoapify",
            "status": "not_started",
            "used_fallback": False,
        }
        self.last_places_status: Dict[str, Any] = {
            "provider": "geoapify",
            "status": "not_started",
            "count": 0,
            "used_fallback": False,
        }

    def _url(self, version: str, path: str) -> str:
        """Build a Geoapify URL even if env base includes /v1 or /v2."""
        root = re.sub(r"/v[12]/?$", "", self.base_url.rstrip("/"))
        return f"{root}/{version}/{path.lstrip('/')}"
    
    def geocode_destination(self, destination: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a destination city/place.
        
        Args:
            destination: City or place name
            
        Returns:
            (latitude, longitude) tuple or None
        """
        cache_key = f"geocode_{destination}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(
                "Geoapify geocoding call succeeded provider=geoapify endpoint_type=geocoding destination=%s count=1 fallback_used=false cache_hit=true",
                destination,
            )
            self.last_geocoding_status = {
                "provider": "geoapify",
                "status": "success",
                "destination": destination,
                "used_fallback": False,
                "cache_hit": True,
                "coordinates_found": True,
            }
            return tuple(cached)

        if not self.api_key:
            logger.warning(
                "Geoapify geocoding call failed provider=geoapify endpoint_type=geocoding destination=%s count=0 fallback_used=false reason=missing_api_key",
                destination,
            )
            self.last_geocoding_status = {
                "provider": "geoapify",
                "status": "failed",
                "destination": destination,
                "used_fallback": False,
                "reason": "missing_api_key",
                "coordinates_found": False,
            }
            return None
        
        try:
            logger.info(
                "Geoapify geocoding call started provider=geoapify endpoint_type=geocoding destination=%s fallback_used=false",
                destination,
            )
            params = {
                "text": destination,
                "apiKey": self.api_key,
            }
            
            response = httpx.get(
                self._url("v1", "geocode/search"),
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("features"):
                feature = data["features"][0]
                properties = feature.get("properties", {})
                lat = properties.get("lat")
                lon = properties.get("lon")
                if lat is None or lon is None:
                    coordinates = feature.get("geometry", {}).get("coordinates", [])
                    lon = coordinates[0] if len(coordinates) > 0 else None
                    lat = coordinates[1] if len(coordinates) > 1 else None
                if lat is None or lon is None:
                    raise ValueError("Geoapify geocode result missing coordinates")
                coords = (float(lat), float(lon))
                
                # Cache result
                self.cache_service.set(cache_key, [coords[0], coords[1]])  # Store as [lat, lon]
                logger.info(
                    "Geoapify geocoding call succeeded provider=geoapify endpoint_type=geocoding destination=%s count=1 fallback_used=false",
                    destination,
                )
                self.last_geocoding_status = {
                    "provider": "geoapify",
                    "status": "success",
                    "destination": destination,
                    "used_fallback": False,
                    "count": 1,
                    "coordinates_found": True,
                }
                
                return coords
            
            logger.warning(
                "Geoapify geocoding call succeeded provider=geoapify endpoint_type=geocoding destination=%s count=0 fallback_used=false",
                destination,
            )
            self.last_geocoding_status = {
                "provider": "geoapify",
                "status": "zero_results",
                "destination": destination,
                "used_fallback": False,
                "count": 0,
                "coordinates_found": False,
            }
            return None
        
        except Exception as e:
            logger.error(
                "Geoapify geocoding call failed provider=geoapify endpoint_type=geocoding destination=%s count=0 fallback_used=false",
                destination,
            )
            self.last_geocoding_status = {
                "provider": "geoapify",
                "status": "failed",
                "destination": destination,
                "used_fallback": False,
                "reason": type(e).__name__,
                "coordinates_found": False,
            }
            return None
    
    def search_pois(
        self,
        location: Tuple[float, float],  # (lat, lon)
        categories: List[str],
        radius_meters: int = 5000,
        limit: int = 20,
        destination: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Search for POIs (points of interest) near a location.
        
        Args:
            location: (latitude, longitude)
            categories: Geoapify categories (e.g., catering, tourism, entertainment, accommodation)
            radius_meters: Search radius in meters
            limit: Max results
            
        Returns:
            List of POI dictionaries
        """
        cache_key = f"pois_{location[0]}_{location[1]}_{','.join(categories)}_{radius_meters}_{limit}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(
                "Geoapify places call succeeded provider=geoapify endpoint_type=places destination=%s count=%s fallback_used=false cache_hit=true",
                destination or location,
                len(cached),
            )
            self.last_places_status = {
                "provider": "geoapify",
                "status": "success",
                "destination": destination,
                "count": len(cached),
                "used_fallback": False,
                "cache_hit": True,
            }
            return cached

        if not self.api_key:
            logger.warning(
                "Geoapify places call failed provider=geoapify endpoint_type=places destination=%s count=0 fallback_used=false reason=missing_api_key",
                destination or location,
            )
            self.last_places_status = {
                "provider": "geoapify",
                "status": "failed",
                "destination": destination,
                "count": 0,
                "used_fallback": False,
                "reason": "missing_api_key",
            }
            return []
        
        try:
            logger.info(
                "Geoapify places call started provider=geoapify endpoint_type=places destination=%s fallback_used=false",
                destination or location,
            )
            lat, lon = location
            params = {
                "filter": f"circle:{lon},{lat},{radius_meters}",
                "bias": f"proximity:{lon},{lat}",
                "categories": ",".join(categories),
                "limit": limit,
                "apiKey": self.api_key,
            }
            
            response = httpx.get(
                self._url("v2", "places"),
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            pois = data.get("features", [])
            
            # Cache result
            self.cache_service.set(cache_key, pois)
            logger.info(
                "Geoapify places call succeeded provider=geoapify endpoint_type=places destination=%s count=%s fallback_used=false",
                destination or location,
                len(pois),
            )
            self.last_places_status = {
                "provider": "geoapify",
                "status": "success" if pois else "zero_results",
                "destination": destination,
                "count": len(pois),
                "used_fallback": False,
            }
            
            return pois
        
        except Exception as e:
            logger.error(
                "Geoapify places call failed provider=geoapify endpoint_type=places destination=%s count=0 fallback_used=false",
                destination or location,
            )
            self.last_places_status = {
                "provider": "geoapify",
                "status": "failed",
                "destination": destination,
                "count": 0,
                "used_fallback": False,
                "reason": type(e).__name__,
            }
            return []
    
    def get_place_details(
        self,
        place_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id: Geoapify place ID
            
        Returns:
            Place details dictionary
        """
        cache_key = f"place_details_{place_id}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(f"Place details cache hit for {place_id}")
            return cached
        
        try:
            params = {
                "id": place_id,
                "apiKey": self.api_key,
            }
            
            response = httpx.get(
                f"{self.base_url}/v1/staticmap",
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Cache result
            self.cache_service.set(cache_key, data)
            
            return data
        
        except Exception as e:
            logger.error(f"Place details fetch failed: {e}")
            return {}
    
    def get_place_candidates(
        self,
        destination: str,
        interests: List[str],
        constraints: Dict[str, Any],
    ) -> List[PlaceCandidate]:
        """
        Get place candidates for a destination using LLM + Geoapify.
        
        Args:
            destination: City name
            interests: Activity interests
            constraints: Trip constraints
            
        Returns:
            List of PlaceCandidate objects
        """
        cache_key = f"place_candidates_v9_{destination}_{','.join(interests)}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(
                "Geoapify places candidates ready provider=geoapify endpoint_type=places destination=%s count=%s fallback_used=false cache_hit=true",
                destination,
                len(cached),
            )
            self.last_places_status = {
                "provider": "geoapify",
                "status": "success",
                "destination": destination,
                "count": len(cached),
                "used_fallback": False,
                "cache_hit": True,
            }
            return [PlaceCandidate(**p) for p in cached]
        
        # Get coordinates
        coords = self.geocode_destination(destination)
        if not coords:
            logger.warning(f"Could not geocode {destination}")
            self.last_places_status = {
                "provider": "geoapify",
                "status": "failed",
                "destination": destination,
                "count": 0,
                "used_fallback": False,
                "reason": "geocoding_failed",
            }
            return []
        
        category_groups = self._category_groups_for(destination, interests, constraints)

        # Search multiple focused category groups and merge unique POIs before ranking.
        poi_by_id: Dict[str, Dict[str, Any]] = {}
        for group in category_groups:
            pois = self.search_pois(
                coords,
                group["categories"],
                radius_meters=group["radius_meters"],
                limit=group["limit"],
                destination=destination,
            )
            for poi in pois:
                properties = poi.get("properties", {}) if isinstance(poi, dict) else {}
                coordinates = poi.get("geometry", {}).get("coordinates", []) if isinstance(poi, dict) else []
                poi_id = properties.get("place_id") or properties.get("osm_id") or "|".join([
                    str(properties.get("name") or ""),
                    str(coordinates[:2]),
                ])
                if poi_id:
                    poi_by_id[str(poi_id)] = poi
        pois = list(poi_by_id.values())
        
        # Convert POIs to PlaceCandidates
        places = []
        for poi in pois:
            try:
                properties = poi.get("properties", {})
                coordinates = poi.get("geometry", {}).get("coordinates", [])
                lon = coordinates[0] if len(coordinates) > 0 else properties.get("lon")
                lat = coordinates[1] if len(coordinates) > 1 else properties.get("lat")
                name = properties.get("name")
                if not name or lat is None or lon is None:
                    continue

                category = self._categorize_poi(properties)
                confidence = 0.85 if properties.get("address_line1") or properties.get("formatted") else 0.75
                
                place_id = properties.get("place_id") or properties.get("osm_id") or f"geoapify_{len(places)}"
                address = properties.get("formatted") or properties.get("address_line2") or properties.get("address_line1") or destination

                candidate_rank_score = self._score_candidate(
                    name=name,
                    category=category,
                    address=address,
                    latitude=float(lat),
                    longitude=float(lon),
                    confidence=confidence,
                    properties=properties,
                    destination_center=coords,
                    destination=destination,
                    constraints=constraints,
                )

                place = PlaceCandidate(
                    id=str(place_id),
                    name=name,
                    category=category,
                    address=address,
                    latitude=float(lat),
                    longitude=float(lon),
                    rating=properties.get("rating"),
                    price_level=properties.get("price"),
                    estimated_cost=self._default_estimated_cost(category),
                    opening_hours={"hours": properties.get("opening_hours")} if properties.get("opening_hours") else None,
                    sources=[SourceRef(
                        name="Geoapify",
                        url=properties.get("website"),
                        fetched_at=datetime.utcnow().isoformat(),
                        confidence=confidence,
                    )],
                    source="geoapify",
                    source_provider="geoapify",
                    verification_status="verified" if confidence >= 0.8 else "partially_verified",
                    confidence=confidence,
                    source_confidence=confidence,
                    candidate_rank_score=candidate_rank_score,
                    description=properties.get("description", ""),
                    phone=properties.get("phone"),
                    website=properties.get("website"),
                )
                places.append(place)
            except Exception as e:
                logger.warning(f"Failed to convert POI: {e}")
                continue
        
        places = self._dedupe_and_rank_candidates(places, destination, constraints)
        places = self._enrich_candidate_images(places, destination, limit=20)

        if not places and coords and self.allow_mock_places:
            logger.warning(
                "Geoapify places returned no usable candidates provider=geoapify endpoint_type=places destination=%s count=0 fallback_used=true",
                destination,
            )
            fallback = self._controlled_fallback_place(destination, coords)
            places = [fallback]
            self.last_places_status = {
                "provider": "geoapify",
                "status": "fallback",
                "destination": destination,
                "count": len(places),
                "used_fallback": True,
                "warning": "Geoapify returned zero usable places; using low-confidence city-center fallback.",
            }
        elif not places:
            logger.warning(
                "Geoapify places returned no usable candidates provider=geoapify endpoint_type=places destination=%s count=0 fallback_used=false",
                destination,
            )
            self.last_places_status = {
                "provider": "geoapify",
                "status": "zero_results",
                "destination": destination,
                "count": 0,
                "used_fallback": False,
                "warning": "Geoapify returned zero usable places; no itinerary can be generated from grounding data.",
            }
        else:
            self.last_places_status = {
                "provider": "geoapify",
                "status": "success",
                "destination": destination,
                "count": len(places),
                "used_fallback": False,
            }

        # Cache real provider results and explicit dev fallback results only when present.
        if places:
            self.cache_service.set(cache_key, [p.model_dump() for p in places])
        logger.info(
            "Geoapify places candidates ready provider=geoapify endpoint_type=places destination=%s count=%s fallback_used=%s",
            destination,
            len(places),
            str(self.last_places_status.get("used_fallback", False)).lower(),
        )
        
        return places

    def _category_groups_for(self, destination: str, interests: List[str], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build destination-sensitive Geoapify category searches."""
        destination_lower = (destination or "").lower()
        interest_set = {str(interest).lower() for interest in interests or []}
        hard = constraints.get("hard", {}) if isinstance(constraints, dict) else {}
        soft = constraints.get("soft", {}) if isinstance(constraints, dict) else {}
        asks_lodging = any(term in interest_set for term in {"hotel", "lodging", "accommodation"}) or bool(soft.get("hotel_style"))
        needs_food = bool(hard.get("diet")) or any(term in interest_set for term in {"food", "restaurant", "catering"})
        is_nature = self._is_nature_destination(destination, interests)

        if is_nature:
            groups = [
                {"categories": ["natural", "tourism.sights", "tourism.attraction.viewpoint"], "radius_meters": 60000, "limit": 35},
                {"categories": ["leisure.park", "tourism.information"], "radius_meters": 60000, "limit": 25},
                {"categories": ["tourism", "entertainment.museum"], "radius_meters": 60000, "limit": 20},
            ]
        else:
            groups = [
                {"categories": ["tourism", "tourism.sights", "tourism.attraction.viewpoint"], "radius_meters": 25000, "limit": 30},
                {"categories": ["entertainment.museum", "leisure.park"], "radius_meters": 25000, "limit": 25},
            ]

        if needs_food:
            groups.append({"categories": ["catering.restaurant", "catering.cafe"], "radius_meters": 25000 if not is_nature else 60000, "limit": 20})
        if asks_lodging:
            groups.append({"categories": ["accommodation.hotel"], "radius_meters": 25000 if not is_nature else 60000, "limit": 10})

        # If the destination is a named neighborhood/city with explicit food interests, keep a broad fallback.
        if not groups:
            groups.append({"categories": ["tourism", "tourism.sights", "leisure.park", "catering.restaurant"], "radius_meters": 25000, "limit": 30})
        return groups

    def _is_nature_destination(self, destination: str, interests: List[str]) -> bool:
        text = f"{destination or ''} {' '.join(interests or [])}".lower()
        return any(term in text for term in [
            "national park",
            "state park",
            "yosemite",
            "zion",
            "grand canyon",
            "yellowstone",
            "mountain",
            "forest",
            "valley",
            "trail",
            "nature",
            "hiking",
        ])

    def _dedupe_and_rank_candidates(
        self,
        places: List[PlaceCandidate],
        destination: str,
        constraints: Dict[str, Any],
    ) -> List[PlaceCandidate]:
        """Apply duplicate penalties, remove exact duplicates, and sort strongest candidates first."""
        exact_seen = set()
        unique_places: List[PlaceCandidate] = []
        normalized_counts: Dict[str, int] = {}
        for place in places:
            normalized = self._normalize_candidate_name(place.name)
            normalized_counts[normalized] = normalized_counts.get(normalized, 0) + 1

        for place in places:
            exact_key = (self._normalize_candidate_name(place.name), round(place.latitude, 5), round(place.longitude, 5))
            if exact_key in exact_seen:
                continue
            exact_seen.add(exact_key)
            normalized = self._normalize_candidate_name(place.name)
            score = place.candidate_rank_score
            if normalized_counts.get(normalized, 0) > 1:
                score -= 25
            unique_places.append(place.model_copy(update={"candidate_rank_score": score}))

        unique_places.sort(key=lambda place: place.candidate_rank_score, reverse=True)
        return unique_places[:30]

    def _enrich_candidate_images(
        self,
        places: List[PlaceCandidate],
        destination: str,
        limit: int = 20,
    ) -> List[PlaceCandidate]:
        """Enrich only the top candidates with non-blocking Wikimedia image metadata."""
        enriched: List[PlaceCandidate] = []
        for index, place in enumerate(places):
            if index >= limit:
                enriched.append(place)
                continue
            try:
                enriched.append(self.image_service.enrich_place_image(place, destination))
            except Exception as exc:
                logger.info("Image enrichment skipped for %s: %s", place.name, type(exc).__name__)
                enriched.append(place)
        return enriched

    def _score_candidate(
        self,
        *,
        name: str,
        category: str,
        address: Optional[str],
        latitude: float,
        longitude: float,
        confidence: float,
        properties: Dict[str, Any],
        destination_center: Tuple[float, float],
        destination: str,
        constraints: Dict[str, Any],
    ) -> float:
        """Rank provider candidates for itinerary quality without hardcoding destinations."""
        categories = properties.get("categories") or []
        if isinstance(categories, str):
            categories = [categories]
        text = " ".join([
            name or "",
            category or "",
            str(properties.get("kind") or ""),
            " ".join(str(c) for c in categories),
            str(properties.get("formatted") or ""),
        ]).lower()
        score = 0.0

        major_terms = [
            "tourism",
            "sights",
            "natural",
            "viewpoint",
            "park",
            "trail",
            "waterfall",
            "valley",
            "lake",
            "peak",
            "visitor center",
            "information",
        ]
        if any(term in text for term in major_terms):
            score += 50
        if any(term in text for term in ["museum", "historic", "monument", "memorial", "gallery", "cultural"]):
            score += 20
        if address:
            score += 15
        if latitude is not None and longitude is not None:
            score += 15
        if confidence >= 0.8:
            score += 10

        bad_terms = [
            "parking",
            "car park",
            "road",
            "atm",
            "bank",
            "fuel",
            "gas station",
            "generic service",
            "railway",
            "railroad",
            "caboose",
            "locomotive",
            "platform",
            "crossing",
            "station",
        ]
        if "visitor center" in text:
            bad_terms.remove("station")
        if any(term in text for term in bad_terms):
            score -= 60
        hard = constraints.get("hard", {}) if isinstance(constraints, dict) else {}
        soft = constraints.get("soft", {}) if isinstance(constraints, dict) else {}
        asks_lodging = bool(soft.get("hotel_style")) or "hotel" in text and "hotel" in str(soft.get("interests", [])).lower()
        if any(term in text for term in ["hotel", "motel", "lodging", "accommodation"]) and not asks_lodging:
            score -= 40
        if confidence < 0.7:
            score -= 15

        is_nature_destination = self._is_nature_destination(destination, [])
        nature_terms = [
            "viewpoint",
            "view ",
            "overlook",
            "vista",
            "fall",
            "falls",
            "waterfall",
            "trail",
            "dome",
            "peak",
            "point",
            "valley",
            "grove",
            "meadow",
            "lake",
            "creek",
            "cascade",
            "natural",
            "lookout",
        ]
        has_nature_signal = any(term in text for term in nature_terms)
        if is_nature_destination and has_nature_signal:
            score += 30
        has_peripheral_nature_poi = any(term in text for term in [
            "historic district",
            "historical marker",
            "mine",
            "mining",
            "mineral",
            "roundhouse",
            "village",
            "flume",
            "post",
        ])
        if is_nature_destination and has_peripheral_nature_poi:
            score -= 30 if has_nature_signal else 50

        distance_km = self._distance_km(destination_center[0], destination_center[1], latitude, longitude)
        road_trip = "road trip" in str(hard).lower() or "road trip" in str(soft).lower()
        too_far_threshold = 100 if is_nature_destination else 50
        if not road_trip and distance_km > too_far_threshold:
            score -= 20

        normalized = self._normalize_candidate_name(name)
        name_lower = (name or "").lower()
        if (
            re.search(r"\b(number|no\.?|#)\s*\d+\b", name_lower)
            or re.search(r"\b\d+\b", name_lower)
            or re.search(r"\b(number|no)\s*\d+\b", normalized)
            or re.search(r"\b\d+\b", normalized)
        ):
            score -= 10

        return score

    def _normalize_candidate_name(self, name: str) -> str:
        normalized = re.sub(r"\b(no\.?|number|#)\s*\d+\b", "", (name or "").lower())
        normalized = re.sub(r"\b\d+\b", "", normalized)
        normalized = re.sub(r"[^a-z]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def _distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return radius * 2 * math.asin(math.sqrt(a))
    
    def search_places_by_keyword(
        self,
        keyword: str,
        destination: str,
    ) -> List[PlaceCandidate]:
        """Search for places matching a keyword in destination."""
        cache_key = f"search_{destination}_{keyword}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(f"Search cache hit for {keyword} in {destination}")
            return [PlaceCandidate(**p) for p in cached]
        
        # Get coordinates
        coords = self.geocode_destination(destination)
        if not coords:
            logger.warning(f"Could not geocode {destination}")
            return []
        
        # For MVP, use mock data
        mock_places = [
            PlaceCandidate(
                id=f"mock_{keyword}_{i}",
                name=f"Sample {keyword} Attraction {i+1}",
                category="attraction",
                latitude=coords[0] + i*0.01,
                longitude=coords[1] + i*0.01,
                rating=4.0 + i*0.1,
                estimated_cost=20 + i*10,
                confidence=0.8,
            )
            for i in range(3)
        ]
        
        self.cache_service.set(cache_key, [p.model_dump() for p in mock_places])
        return mock_places
    
    def _categorize_poi(self, properties: Any) -> str:
        """Map Geoapify POI kind to PlaceCandidate category."""
        if isinstance(properties, dict):
            categories = properties.get("categories") or []
            if isinstance(categories, str):
                categories = [categories]
            kind = " ".join([str(properties.get("kind") or ""), *[str(c) for c in categories]])
        else:
            kind = str(properties or "")

        if not kind:
            return "attraction"
        
        kind_lower = kind.lower()
        
        if "hotel" in kind_lower or "accommodation" in kind_lower or "hostel" in kind_lower:
            return "hotel"
        elif "restaurant" in kind_lower or "cafe" in kind_lower or "bar" in kind_lower:
            return "restaurant"
        elif "viewpoint" in kind_lower:
            return "viewpoint"
        elif "park" in kind_lower or "natural" in kind_lower or "trail" in kind_lower or "hiking" in kind_lower or "beach" in kind_lower:
            return "park"
        elif "museum" in kind_lower or "gallery" in kind_lower or "art" in kind_lower:
            return "museum"
        else:
            return "attraction"

    def _default_estimated_cost(self, category: str) -> float:
        """Conservative per-person estimate when provider has no price."""
        category_lower = (category or "").lower()
        if category_lower == "restaurant":
            return 25
        if category_lower == "hotel":
            return 150
        if category_lower in {"park", "viewpoint"}:
            return 0
        return 15

    def _controlled_fallback_place(self, destination: str, coords: Tuple[float, float]) -> PlaceCandidate:
        """Low-confidence fallback used only when Geoapify has no usable candidates."""
        slug = re.sub(r"[^a-z0-9]+", "_", destination.lower()).strip("_") or "destination"
        return PlaceCandidate(
            id=f"fallback_{slug}_center",
            name=f"{destination} city center",
            category="attraction",
            address=destination,
            latitude=coords[0],
            longitude=coords[1],
            estimated_cost=0,
            opening_hours=None,
            sources=[SourceRef(
                name="Geoapify geocoding fallback",
                fetched_at=datetime.utcnow().isoformat(),
                confidence=0.35,
            )],
            source="fallback_mock",
            source_provider="fallback_mock",
            verification_status="partially_verified",
            confidence=0.35,
            source_confidence=0.35,
            candidate_rank_score=20,
            image_source="category_placeholder",
            image_credit="Local attraction placeholder",
            image_confidence=0.35,
            description="Low-confidence fallback based on destination geocoding only.",
        )
