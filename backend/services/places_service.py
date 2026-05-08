"""
Places Service: Geoapify integration for place search, geocoding, and POI discovery.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging

import httpx

from backend.config import get_config
from backend.schemas.places import PlaceCandidate, SourceRef
from backend.services.cache_service import CacheService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
config = get_config()


class PlacesService:
    """Fetch places and POIs from Geoapify with LLM-powered candidate generation."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize PlacesService."""
        self.cache_service = cache_service or CacheService()
        self.llm = LLMService()
        self.base_url = config.GEOAPIFY_BASE_URL
        self.api_key = config.GEOAPIFY_API_KEY
    
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
            logger.info(f"Geocode cache hit for {destination}")
            return tuple(cached)
        
        try:
            params = {
                "text": destination,
                "apiKey": self.api_key,
            }
            
            response = httpx.get(
                f"{self.base_url}/v1/geocode/search",
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("features"):
                feature = data["features"][0]
                coords = feature.get("properties", {}).get("lon"), feature.get("properties", {}).get("lat")
                
                # Cache result
                self.cache_service.set(cache_key, [coords[1], coords[0]])  # Store as [lat, lon]
                logger.info(f"Geocoded {destination}: {coords}")
                
                return coords
            
            logger.warning(f"No geocoding results for {destination}")
            return None
        
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
            return None
    
    def search_pois(
        self,
        location: Tuple[float, float],  # (lat, lon)
        categories: List[str],
        radius_meters: int = 5000,
        limit: int = 20,
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
            logger.info(f"POI cache hit for {location}")
            return cached
        
        try:
            params = {
                "lat": location[0],
                "lon": location[1],
                "radius": radius_meters,
                "categories": ",".join(categories),
                "limit": limit,
                "apiKey": self.api_key,
            }
            
            response = httpx.get(
                f"{self.base_url}/v2/places",
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            pois = data.get("features", [])
            
            # Cache result
            self.cache_service.set(cache_key, pois)
            logger.info(f"Found {len(pois)} POIs near {location}")
            
            return pois
        
        except Exception as e:
            logger.error(f"POI search failed: {e}")
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
        cache_key = f"place_candidates_{destination}_{','.join(interests)}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(f"Place candidates cache hit for {destination}")
            return [PlaceCandidate(**p) for p in cached]
        
        # Get coordinates
        coords = self.geocode_destination(destination)
        if not coords:
            logger.warning(f"Could not geocode {destination}")
            return []
        
        # Map interests to Geoapify categories
        category_map = {
            "beach": ["tourism.beach"],
            "museum": ["tourism.museum"],
            "restaurant": ["catering.restaurant"],
            "attraction": ["tourism.attraction"],
            "hotel": ["accommodation.hotel"],
            "hiking": ["tourism.hiking"],
            "nature": ["tourism.nature"],
            "food": ["catering"],
        }
        
        categories = []
        for interest in interests:
            categories.extend(category_map.get(interest.lower(), []))
        
        if not categories:
            categories = ["tourism.attraction", "catering.restaurant"]
        
        # Search POIs
        pois = self.search_pois(coords, categories, radius_meters=20000, limit=30)
        
        # Convert POIs to PlaceCandidates
        places = []
        for poi in pois[:15]:
            try:
                properties = poi.get("properties", {})
                
                place = PlaceCandidate(
                    id=properties.get("place_id", f"poi_{len(places)}"),
                    name=properties.get("name", "Unknown"),
                    category=self._categorize_poi(properties.get("kind")),
                    address=properties.get("address_line1", ""),
                    latitude=poi.get("geometry", {}).get("coordinates", [0, 0])[1],
                    longitude=poi.get("geometry", {}).get("coordinates", [0, 0])[0],
                    rating=properties.get("rating"),
                    price_level=properties.get("price"),
                    opening_hours={"hours": properties.get("opening_hours", "Check website")},
                    sources=[SourceRef(
                        name="Geoapify",
                        url=properties.get("website"),
                        fetched_at=datetime.utcnow().isoformat(),
                        confidence=0.85,
                    )],
                    verification_status="verified",
                    confidence=0.85,
                    description=properties.get("description", ""),
                    phone=properties.get("phone"),
                    website=properties.get("website"),
                )
                places.append(place)
            except Exception as e:
                logger.warning(f"Failed to convert POI: {e}")
                continue
        
        # Cache results
        self.cache_service.set(cache_key, [p.model_dump() for p in places])
        logger.info(f"Found {len(places)} place candidates for {destination}")
        
        return places
    
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
    
    def _categorize_poi(self, kind: str) -> str:
        """Map Geoapify POI kind to PlaceCandidate category."""
        if not kind:
            return "attraction"
        
        kind_lower = kind.lower()
        
        if "hotel" in kind_lower or "accommodation" in kind_lower or "hostel" in kind_lower:
            return "hotel"
        elif "restaurant" in kind_lower or "cafe" in kind_lower or "bar" in kind_lower:
            return "restaurant"
        elif "beach" in kind_lower or "park" in kind_lower or "hiking" in kind_lower:
            return "attraction"
        elif "museum" in kind_lower or "gallery" in kind_lower or "art" in kind_lower:
            return "attraction"
        else:
            return "attraction"
