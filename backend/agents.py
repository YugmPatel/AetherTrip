import json
from typing import Dict, Any
from backend.state import TripState
from backend.apis import call_llm, get_city_comprehensive_info, _clean_json
from backend.utils import setup_logger

logger = setup_logger("Agents")

class BaseAgent:
    def run(self, state: TripState) -> Dict[str, Any]:
        """Returns a partial state update."""
        raise NotImplementedError

class InputAnalyzerAgent(BaseAgent):
    """Parses user input into structured data."""
    def run(self, state: TripState) -> Dict[str, Any]:
        logger.info("InputAnalyzerAgent running...")
        
        # 1. Try Regex Extraction first (Save 1 LLM Call)
        import re
        text = state.user_input.lower()
        
        # Extract Duration
        duration = "Upcoming Trip"
        days_match = re.search(r"(\d+)\s*-?\s*days?", text)
        if days_match:
            duration = f"{days_match.group(1)} Days"
        elif "week" in text:
            duration = "1 Week"
            
        # Extract Destination (Naive: assume "to [Destination]" or "visit [Destination]")
        destination = []
        dest_match = re.search(r"(?:to|visit|in)\s+([a-zA-Z\s]+?)(?:\s+for|\s+during|\s+in|\s*$)", text, re.IGNORECASE)
        if dest_match:
            possible_dest = dest_match.group(1).strip()
            # Filter out common stop words if needed
            if len(possible_dest) > 2:
                destination = [possible_dest.title()]
        
        # If we found a destination, use it and SKIP LLM
        if destination:
            logger.info(f"Regex extracted: {destination}, {duration}")
            return {
                "parsed_request": {
                    "origin": "New York",
                    "destination": destination,
                    "dates": duration,
                    "interests": ["General"] # Default
                }
            }
        else:
            logger.info(f"Regex failed to extract destination from: '{text}'")
            
        # 2. Fallback to LLM if Regex fails
        prompt = f"""
        Analyze this trip request: "{state.user_input}"
        
        Extract the following fields into a JSON object:
        - origin: The starting city (default to "New York" if not specified)
        - destination: The main destination or region mentioned. Return as a LIST of strings.
        - dates: The travel dates or duration (e.g. "1 week", "July 2025"). Default to "Upcoming Trip" if not specified.
        - interests: A list of interests mentioned or implied (e.g. ["Hiking", "Food"]).
        
        Return JSON ONLY. No markdown formatting.
        Example: {{ "origin": "NYC", "destination": ["Swiss Alps"], "dates": "5 days", "interests": ["Hiking"] }}
        """
        
        try:
            response = call_llm(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            parsed = _clean_json(response)
            
            if not parsed or not parsed.get("destination"):
                return {"errors": [f"Could not understand request: {state.user_input}"]}
                
            return {"parsed_request": parsed}
        except Exception as e:
             return {"errors": [f"Input analysis failed: {e}"]}

class CitySelectorAgent(BaseAgent):
    """Selects the best cities based on the request."""
    def run(self, state: TripState) -> Dict[str, Any]:
        logger.info("CitySelectorAgent running...")
        if not state.parsed_request:
            return {}
        
        dests = state.parsed_request.get("destination", [])
        if isinstance(dests, str): dests = [dests]
        
        # Ask LLM to refine the destination list
        # This handles cases like "Swiss Alps" -> ["Zermatt", "Interlaken"]
        # And also validates if "Paris" is a valid city.
        prompt = f"""
        The user wants to go to: {dests}
        Interests: {state.parsed_request.get('interests')}
        
        If the destination is a REGION or COUNTRY (e.g. "Swiss Alps", "Italy"), suggest 3 specific cities/towns to visit.
        If the destination is already specific cities, just return them.
        
        Return JSON ONLY: {{ "cities": ["City1", "City2", "City3"] }}
        """
        
        try:
            resp = call_llm(prompt)
            data = _clean_json(resp)
            selected = data.get("cities", dests)
            return {"selected_cities": selected}
        except Exception as e:
            logger.error(f"CitySelector failed: {e}")
            return {"errors": [f"Could not select cities: {e}"]}

class DataFetcherAgent(BaseAgent):
    """
    Fetches ALL data (Weather, Flights, Hotels, Attractions) for selected cities.
    Uses a consolidated API call to minimize LLM usage and avoid rate limits.
    """
    def run(self, state: TripState) -> Dict[str, Any]:
        logger.info("DataFetcherAgent running...")
        if not state.selected_cities: return {}
        
        weather_data = {}
        flight_data = {}
        hotel_data = {}
        attractions_data = {}
        
        origin = state.parsed_request.get("origin", "New York")
        dates = state.parsed_request.get("dates", "upcoming trip")
        
        for city in state.selected_cities:
            try:
                # Single LLM call per city instead of 4
                city_info = get_city_comprehensive_info(city, origin, dates)
                
                weather_data[city] = city_info.get("weather", {})
                flight_data[city] = city_info.get("flights", {})
                hotel_data[city] = city_info.get("hotels", {})
                attractions_data[city] = city_info.get("attractions", {})
            except Exception as e:
                logger.error(f"Data fetch failed for {city}: {e}")
                # Continue to next city instead of failing completely
            
        return {
            "weather_data": weather_data,
            "flight_data": flight_data,
            "hotel_data": hotel_data,
            "attractions_data": attractions_data
        }

class ItineraryAgent(BaseAgent):
    """Builds the itinerary."""
    def run(self, state: TripState) -> Dict[str, Any]:
        logger.info("ItineraryAgent running...")
        
        context = {
            "cities": state.selected_cities,
            "weather": state.weather_data,
            "flights": state.flight_data,
            "hotels": state.hotel_data,
            "attractions": state.attractions_data,
            "interests": state.parsed_request.get("interests") if state.parsed_request else [],
            "dates": state.parsed_request.get("dates", "Upcoming") if state.parsed_request else "Upcoming"
        }
        
        prompt = f"""
        Create a detailed day-by-day itinerary based on this data: {json.dumps(context)}
        
        Format JSON ONLY: 
        {{ 
            "plan": [
                {{ "day": 1, "title": "Arrival", "description": "..." }},
                {{ "day": 2, "title": "Exploring...", "description": "..." }}
            ]
        }}
        """
        resp = call_llm(prompt)
        data = _clean_json(resp)
        
        if not data or "plan" not in data:
            return {"itinerary": {"plan": resp}}
        else:
            return {"itinerary": data}

class CostAgent(BaseAgent):
    """Estimates costs."""
    def run(self, state: TripState) -> Dict[str, Any]:
        logger.info("CostAgent running...")
        
        # Calculate Flight Costs
        total_flights = 0
        if state.flight_data:
            for f in state.flight_data.values():
                price = f.get("price")
                if isinstance(price, (int, float)):
                    total_flights += int(price)
        
        # Fallback if no flight data found (e.g. API failed)
        if total_flights == 0 and len(state.selected_cities) > 0:
            total_flights = 500 * len(state.selected_cities) # Rough estimate
        
        # Estimate hotel cost (avg price * 3 nights per city)
        total_hotels = 0
        if state.hotel_data:
            for city_data in state.hotel_data.values():
                hotels = city_data.get("hotels", [])
                if hotels and isinstance(hotels, list) and len(hotels) > 0:
                    price = hotels[0].get("price")
                    if isinstance(price, (int, float)):
                        total_hotels += int(price) * 3
        
        # Fallback if no hotel data found
        if total_hotels == 0 and len(state.selected_cities) > 0:
            total_hotels = 150 * 3 * len(state.selected_cities) # Rough estimate
        
        total = total_flights + total_hotels + 500 # Buffer for food/activities
        
        return {
            "cost_estimate": {
                "total": total,
                "flights": total_flights,
                "hotels": total_hotels,
                "currency": "USD"
            }
        }
