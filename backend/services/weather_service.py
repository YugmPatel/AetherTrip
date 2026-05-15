"""
Weather Service: Open-Meteo integration for weather forecasting.
No API key required; includes caching.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx

from backend.config import get_config
from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)
config = get_config()


class WeatherService:
    """Fetch weather data from Open-Meteo API."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize weather service with optional caching."""
        self.cache_service = cache_service or CacheService()
        self.base_url = config.OPEN_METEO_BASE_URL
        self.last_status: Dict[str, Any] = {
            "provider": "open_meteo",
            "status": "not_started",
            "used_fallback": False,
        }
    
    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days: Number of days to forecast (default: 7, max: 16)
            
        Returns:
            Weather data with daily forecasts
        """
        # Check cache first
        cache_key = f"weather_{latitude}_{longitude}_{days}"
        cached = self.cache_service.get(cache_key)
        if cached:
            logger.info(
                "Open-Meteo weather call succeeded provider=open_meteo endpoint_type=weather destination=%s,%s count=%s fallback_used=false cache_hit=true",
                latitude,
                longitude,
                days,
            )
            self.last_status = {
                "provider": "open_meteo",
                "status": "success",
                "destination": f"{latitude},{longitude}",
                "count": days,
                "used_fallback": False,
                "cache_hit": True,
            }
            return cached
        
        try:
            logger.info(
                "Open-Meteo weather call started provider=open_meteo endpoint_type=weather destination=%s,%s count=%s fallback_used=false",
                latitude,
                longitude,
                days,
            )
            # Query parameters
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code,wind_speed_10m_max",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "forecast_days": min(days, 16),  # Open-Meteo max is 16 days
            }
            
            # Make request
            response = httpx.get(
                self.base_url,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(
                "Open-Meteo weather call succeeded provider=open_meteo endpoint_type=weather destination=%s,%s count=%s fallback_used=false",
                latitude,
                longitude,
                len(data.get("daily", {}).get("time", [])) if isinstance(data, dict) else days,
            )
            self.last_status = {
                "provider": "open_meteo",
                "status": "success",
                "destination": f"{latitude},{longitude}",
                "count": len(data.get("daily", {}).get("time", [])) if isinstance(data, dict) else days,
                "used_fallback": False,
            }
            
            # Cache result
            self.cache_service.set(cache_key, data)
            
            return data
        
        except Exception as e:
            logger.error(
                "Open-Meteo weather call failed provider=open_meteo endpoint_type=weather destination=%s,%s count=0 fallback_used=true",
                latitude,
                longitude,
            )
            self.last_status = {
                "provider": "open_meteo",
                "status": "failed",
                "destination": f"{latitude},{longitude}",
                "count": 0,
                "used_fallback": True,
                "reason": type(e).__name__,
            }
            return self._mock_forecast(latitude, longitude, days)
    
    def get_weather_summary(
        self,
        latitude: float,
        longitude: float,
        date: str,  # YYYY-MM-DD format
    ) -> Dict[str, Any]:
        """
        Get weather summary for a specific date.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            date: Date in YYYY-MM-DD format
            
        Returns:
            Weather data for the date
        """
        try:
            # Parse date to determine days ahead
            target_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_ahead = (target_date - today).days
            
            if days_ahead < 0:
                logger.warning(f"Cannot forecast weather for past date: {date}")
                return {}
            
            # Get forecast
            forecast = self.get_forecast(latitude, longitude, days=days_ahead + 1)
            
            if not forecast or "daily" not in forecast:
                return {}
            
            daily = forecast["daily"]
            dates = daily.get("time", [])
            
            # Find index for the date
            try:
                date_idx = dates.index(date)
            except ValueError:
                logger.warning(f"Date {date} not in forecast")
                return {}
            
            # Extract data for this date
            weather_data = {
                "date": date,
                "temperature_max_f": daily.get("temperature_2m_max", [])[date_idx] if date_idx < len(daily.get("temperature_2m_max", [])) else None,
                "temperature_min_f": daily.get("temperature_2m_min", [])[date_idx] if date_idx < len(daily.get("temperature_2m_min", [])) else None,
                "precipitation_mm": daily.get("precipitation_sum", [])[date_idx] if date_idx < len(daily.get("precipitation_sum", [])) else 0,
                "precipitation_probability_percent": daily.get("precipitation_probability_max", [])[date_idx] if date_idx < len(daily.get("precipitation_probability_max", [])) else 0,
                "weather_code": daily.get("weather_code", [])[date_idx] if date_idx < len(daily.get("weather_code", [])) else None,
                "wind_speed_mph": daily.get("wind_speed_10m_max", [])[date_idx] if date_idx < len(daily.get("wind_speed_10m_max", [])) else None,
            }
            
            return weather_data
        
        except Exception as e:
            logger.error(f"Weather summary failed: {e}")
            return {}
    
    def is_risky_weather(
        self,
        latitude: float,
        longitude: float,
        date: str,
        activity_type: str = "outdoor",
    ) -> bool:
        """
        Check if weather is risky for an activity.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            date: Date in YYYY-MM-DD format
            activity_type: Type of activity (outdoor, indoor, water, hiking)
            
        Returns:
            True if weather is risky
        """
        weather = self.get_weather_summary(latitude, longitude, date)
        
        if not weather:
            return False
        
        # Risky conditions by activity type
        temp_max = weather.get("temperature_max_f") or 0
        temp_min = weather.get("temperature_min_f") or 0
        precip_prob = weather.get("precipitation_probability_percent") or 0
        weather_code = weather.get("weather_code")
        wind_speed = weather.get("wind_speed_mph") or 0
        
        # Extreme temperatures
        if temp_max > 95 or temp_min < 32:
            return True
        
        # Heavy precipitation
        if precip_prob > 80:
            return True
        
        # Extreme wind (> 30 mph)
        if wind_speed > 30:
            return True
        
        # Weather code interpretation (WMO codes)
        # 80-82 = rain, 85-86 = snow, 95-96 = thunderstorm, 99 = tornado
        risky_codes = [80, 81, 82, 85, 86, 95, 96, 99]
        if weather_code in risky_codes:
            return True
        
        return False
    
    def _mock_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int,
    ) -> Dict[str, Any]:
        """Generate mock weather forecast for testing."""
        import random
        
        forecast_days = min(days, 7)
        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(forecast_days)]
        
        daily = {
            "time": dates,
            "temperature_2m_max": [random.randint(60, 85) for _ in range(forecast_days)],
            "temperature_2m_min": [random.randint(50, 65) for _ in range(forecast_days)],
            "precipitation_sum": [random.randint(0, 5) for _ in range(forecast_days)],
            "precipitation_probability_max": [random.randint(0, 60) for _ in range(forecast_days)],
            "weather_code": [random.choice([0, 1, 3, 45, 51, 80]) for _ in range(forecast_days)],
            "wind_speed_10m_max": [random.randint(5, 15) for _ in range(forecast_days)],
        }
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "daily": daily,
        }
