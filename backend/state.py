from typing import List, Dict, Optional, Any, Annotated
import operator
from pydantic import BaseModel, Field

def overwrite(left: Any, right: Any) -> Any:
    """Simple reducer that overwrites the left value with the right value."""
    return right

class TripState(BaseModel):
    user_input: str = ""
    parsed_request: Optional[Dict[str, Any]] = None
    selected_cities: Optional[List[str]] = None
    
    # Use Annotated with a reducer for ALL fields involved in parallel execution
    # This tells LangGraph how to handle updates from multiple nodes, even if they target different keys.
    # In Pydantic v2 / LangGraph, explicit reducers prevent the "InvalidConcurrentGraphUpdate" error.
    
    weather_data: Annotated[Optional[Dict[str, Any]], overwrite] = None
    flight_data: Annotated[Optional[Dict[str, Any]], overwrite] = None
    hotel_data: Annotated[Optional[Dict[str, Any]], overwrite] = None
    attractions_data: Annotated[Optional[Dict[str, Any]], overwrite] = None
    
    itinerary: Optional[Dict[str, Any]] = None
    cost_estimate: Optional[Dict[str, Any]] = None
    
    # Allow parallel agents to append errors
    errors: Annotated[List[str], operator.add] = Field(default_factory=list)

    def merge(self, **kwargs):
        """Updates state fields with provided keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
