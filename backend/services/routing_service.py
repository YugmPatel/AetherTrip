"""
Routing Service: OpenRouteService integration for travel times and distance calculations.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

import httpx

from backend.config import get_config
from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)
config = get_config()


class RoutingService:
    """Calculate routing, distance, and travel times using OpenRouteService."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize routing service with optional caching."""
        self.cache_service = cache_service or CacheService()
        self.base_url = config.OPENROUTESERVICE_BASE_URL
        self.api_key = config.OPENROUTESERVICE_API_KEY
        self.last_matrix_status: Dict[str, Any] = {
            "provider": "openrouteservice",
            "status": "not_started",
            "used_fallback": False,
            "count": 0,
        }
    
    def get_distance_and_time(
        self,
        origin: Tuple[float, float],  # (lon, lat)
        destination: Tuple[float, float],  # (lon, lat)
        profile: str = "driving-car",  # driving-car, foot-walking, cycling-regular
    ) -> Dict[str, Any]:
        """
        Get distance and time between two points.
        
        Args:
            origin: (longitude, latitude)
            destination: (longitude, latitude)
            profile: Travel profile
            
        Returns:
            Dict with distance (m) and duration (seconds)
        """
        cache_key = f"route_{origin[0]}_{origin[1]}_{destination[0]}_{destination[1]}_{profile}"
        cached = self.cache_service.get(cache_key)
        if cached:
            logger.info(f"Route cache hit")
            return cached
        
        try:
            url = f"{self.base_url}/v2/directions/{profile}"
            
            params = {
                "api_key": self.api_key,
                "start": f"{origin[0]},{origin[1]}",
                "end": f"{destination[0]},{destination[1]}",
            }
            
            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("routes"):
                route = data["routes"][0]
                result = {
                    "distance_meters": route.get("summary", {}).get("distance"),
                    "duration_seconds": route.get("summary", {}).get("duration"),
                    "geometry": route.get("geometry"),
                }
                
                # Cache result
                self.cache_service.set(cache_key, result)
                logger.info(f"Route retrieved: {result['distance_meters']}m, {result['duration_seconds']}s")
                
                return result
            
            logger.warning("No routes found")
            return {}
        
        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            return self._mock_route(origin, destination)
    
    def get_route_matrix(
        self,
        locations: List[Tuple[float, float]],  # List of (lon, lat)
        profile: str = "driving-car",
    ) -> Dict[str, Any]:
        """
        Get distance/time matrix between multiple locations.
        More efficient than multiple individual calls.
        
        Args:
            locations: List of (longitude, latitude) tuples
            profile: Travel profile
            
        Returns:
            Dict with distance and duration matrices
        """
        if len(locations) < 2:
            logger.warning("Need at least 2 locations for matrix")
            self.last_matrix_status = {
                "provider": "openrouteservice",
                "status": "skipped",
                "count": len(locations),
                "used_fallback": False,
                "reason": "not_enough_locations",
            }
            return {}
        
        cache_key = f"matrix_{profile}_{len(locations)}"
        cached = self.cache_service.get(cache_key)
        if cached:
            logger.info(
                "OpenRouteService matrix call succeeded provider=openrouteservice endpoint_type=matrix destination=place_candidates count=%s fallback_used=false cache_hit=true",
                len(locations),
            )
            self.last_matrix_status = {
                "provider": "openrouteservice",
                "status": "success",
                "count": len(locations),
                "used_fallback": False,
                "cache_hit": True,
            }
            return cached

        if not self.api_key:
            logger.warning(
                "OpenRouteService matrix call failed provider=openrouteservice endpoint_type=matrix destination=place_candidates count=%s fallback_used=true reason=missing_api_key",
                len(locations),
            )
            self.last_matrix_status = {
                "provider": "openrouteservice",
                "status": "failed",
                "count": len(locations),
                "used_fallback": True,
                "reason": "missing_api_key",
            }
            return self._mock_matrix(locations)
        
        try:
            logger.info(
                "OpenRouteService matrix call started provider=openrouteservice endpoint_type=matrix destination=place_candidates count=%s fallback_used=false",
                len(locations),
            )
            url = f"{self.base_url}/v2/matrix/{profile}"
            
            # Format locations as [lon, lat] pairs
            locations_list = [[loc[0], loc[1]] for loc in locations]
            
            params = {
                "api_key": self.api_key,
            }
            
            body = {
                "locations": locations_list,
                "metrics": ["distance", "duration"],
            }
            
            response = httpx.post(
                url,
                params=params,
                json=body,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            result = {
                "distances": data.get("distances"),  # m
                "durations": data.get("durations"),  # seconds
            }
            
            # Cache result
            self.cache_service.set(cache_key, result)
            logger.info(
                "OpenRouteService matrix call succeeded provider=openrouteservice endpoint_type=matrix destination=place_candidates count=%s fallback_used=false",
                len(locations),
            )
            self.last_matrix_status = {
                "provider": "openrouteservice",
                "status": "success",
                "count": len(locations),
                "used_fallback": False,
            }
            
            return result
        
        except Exception as e:
            logger.error(
                "OpenRouteService matrix call failed provider=openrouteservice endpoint_type=matrix destination=place_candidates count=%s fallback_used=true",
                len(locations),
            )
            self.last_matrix_status = {
                "provider": "openrouteservice",
                "status": "failed",
                "count": len(locations),
                "used_fallback": True,
                "reason": type(e).__name__,
            }
            return self._mock_matrix(locations)
    
    def get_isochrone(
        self,
        location: Tuple[float, float],  # (lon, lat)
        range_meters: int = 10000,
        profile: str = "driving-car",
    ) -> Dict[str, Any]:
        """
        Get reachable area within distance/time range.
        
        Args:
            location: (longitude, latitude)
            range_meters: Maximum distance in meters
            profile: Travel profile
            
        Returns:
            Isochrone polygon (GeoJSON)
        """
        try:
            url = f"{self.base_url}/v2/isochrones/{profile}"
            
            params = {
                "api_key": self.api_key,
                "locations": f"{location[0]},{location[1]}",
                "range": range_meters,
                "range_type": "distance",
            }
            
            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            return data
        
        except Exception as e:
            logger.error(f"Isochrone calculation failed: {e}")
            return {}
    
    def _mock_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
    ) -> Dict[str, Any]:
        """Generate mock route for testing."""
        import math
        
        # Approximate distance using Haversine formula
        lon1, lat1 = origin
        lon2, lat2 = destination
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        km = 6371 * c
        
        distance_meters = km * 1000
        # Assume average speed of 40 mph for driving
        duration_seconds = int((distance_meters / 1609) / 40 * 3600)
        
        return {
            "distance_meters": distance_meters,
            "duration_seconds": duration_seconds,
        }
    
    def _mock_matrix(self, locations: List[Tuple[float, float]]) -> Dict[str, Any]:
        """Generate mock route matrix for testing."""
        import random
        
        n = len(locations)
        distances = [[0 if i == j else random.randint(5000, 50000) for j in range(n)] for i in range(n)]
        durations = [[0 if i == j else random.randint(300, 3000) for j in range(n)] for i in range(n)]
        
        return {
            "distances": distances,
            "durations": durations,
        }
