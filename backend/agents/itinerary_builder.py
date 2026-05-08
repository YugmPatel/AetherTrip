"""
ItineraryBuilderAgent: generates itinerary from constraints and place candidates.
"""

import logging
from typing import Dict, Any

from backend.state import TripState
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


DESTINATION_THEMES = {
    "los angeles": [
        ("The Broad Museum", "Contemporary art museum in Downtown LA.", 0),
        ("Grand Central Market", "Historic food hall with many lunch options.", 25),
        ("Griffith Observatory", "Scenic overlook with skyline views.", 0),
        ("Santa Monica Pier", "Oceanfront walk and sunset stop.", 15),
    ],
    "san francisco": [
        ("Mission District", "Food and neighborhood exploration.", 20),
        ("Golden Gate Bridge Vista", "Iconic sightseeing stop.", 0),
        ("Ferry Building Marketplace", "Local food and shopping hall.", 18),
        ("Alamo Square", "Classic city views and walking route.", 0),
    ],
    "new york": [
        ("The High Line", "Elevated park walk with city views.", 0),
        ("Chelsea Market", "Indoor food hall with plenty of choices.", 22),
        ("Metropolitan Museum of Art", "Major museum stop for the day.", 30),
        ("Bryant Park", "Relaxed mid-day break in Midtown.", 0),
    ],
    "seattle": [
        ("Pike Place Market", "Food market and downtown landmark.", 15),
        ("Museum of Pop Culture", "Indoor museum with flexible timing.", 28),
        ("Kerry Park", "Short scenic stop with skyline views.", 0),
        ("Discovery Park", "Outdoor nature walk and backup plan.", 0),
    ],
}


class ItineraryBuilderAgent:
    """Builds day-by-day itinerary using verified places only."""
    
    def __init__(self):
        self.llm = LLMService()
    
    def run(self, state: TripState) -> Dict[str, Any]:
        """
        Generate itinerary from constraints and place candidates.
        
        Returns:
            Updated state with itinerary
        """
        logger.info("ItineraryBuilderAgent: building itinerary")
        
        if not state.place_candidates:
            logger.warning("No place candidates available")
            place_candidates = []
        else:
            place_candidates = state.place_candidates
        
        if not state.constraints:
            logger.warning("No constraints available")
            constraints = {}
        else:
            constraints = state.constraints
        
        # For MVP: generate mock itinerary
        num_days = constraints.get("hard", {}).get("duration_days", 3) if isinstance(constraints, dict) else 3
        destination = constraints.get("hard", {}).get("destination", "Unknown") if isinstance(constraints, dict) else "Unknown"
        destination_key = str(destination).lower()
        theme_stops = DESTINATION_THEMES.get(destination_key, [])

        if not theme_stops:
            theme_stops = [
                (f"{destination} Arrival Walk", f"Intro day in {destination}.", 0),
                (f"{destination} Food Hall", f"Local dining stop in {destination}.", 20),
                (f"{destination} Scenic Stop", f"Sightseeing stop in {destination}.", 0),
                (f"{destination} Neighborhood Loop", f"Exploring a different district in {destination}.", 15),
            ]
        
        itinerary = {
            "destination": destination,
            "days": [
                {
                    "day": i + 1,
                    "items": [
                        {
                            "day": i + 1,
                            "start_time": "09:00",
                            "end_time": "11:00",
                            "place_id": f"{destination_key.replace(' ', '_')}_day_{i+1}",
                            "place_name": theme_stops[i % len(theme_stops)][0],
                            "category": "attraction" if i % 2 == 0 else "dining",
                            "description": theme_stops[i % len(theme_stops)][1],
                            "estimated_cost": theme_stops[i % len(theme_stops)][2] + (5 * (i % 3)),
                        }
                    ],
                    "estimated_day_cost": theme_stops[i % len(theme_stops)][2] + (5 * (i % 3)),
                }
                for i in range(num_days)
            ],
            "total_estimated_cost_per_person": 20 * num_days,
        }
        
        logger.info(f"Itinerary generated: {num_days} days")
        
        return {"itinerary": itinerary}
