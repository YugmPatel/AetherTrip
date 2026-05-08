"""
InputAnalyzerAgent: parses user input to extract basic structure.
"""

import re
import json
import logging
from typing import Dict, Any

from backend.state import TripState
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class InputAnalyzerAgent:
    """Parses raw user input into structured fields."""
    
    def __init__(self):
        self.llm = LLMService()
    
    def run(self, state: TripState) -> Dict[str, Any]:
        """
        Parse user input.
        
        Returns:
            Updated state with parsed_request
        """
        logger.info(f"InputAnalyzerAgent: parsing '{state.user_input[:50]}...'")
        
        # Try regex extraction first (fast)
        parsed = self._regex_extract(state.user_input)
        
        if parsed:
            logger.info(f"Regex extraction succeeded: {parsed}")
            return {"parsed_request": parsed}
        
        # Fallback to LLM
        logger.info("Regex extraction inconclusive; using LLM")
        parsed = self._llm_extract(state.user_input)
        
        return {"parsed_request": parsed}
    
    def _regex_extract(self, text: str) -> Dict[str, Any]:
        """
        Extract fields using regex patterns.
        
        Returns:
            Dict with (origin, destination, duration, travelers, budget) or None if unclear
        """
        text_lower = text.lower()
        
        # Extract destination (after "to", "visit", "in")
        dest_match = re.search(r"(?:to|visit|in)\s+([a-z\s]+?)(?:\s+for|\s+during|\s+from|\s*$)", text, re.IGNORECASE)
        destination = dest_match.group(1).strip().title() if dest_match else None
        
        if not destination:
            return None
        
        # Extract duration
        duration_match = re.search(r"(\d+)\s*(?:-\s*)?days?", text, re.IGNORECASE)
        duration = f"{duration_match.group(1)} days" if duration_match else "Upcoming Trip"
        
        # Extract travelers
        travelers_match = re.search(r"for\s+(\d+)\s+(?:people|friends|travelers|person)", text, re.IGNORECASE)
        travelers = int(travelers_match.group(1)) if travelers_match else 1
        
        # Extract budget
        budget_match = re.search(r"(?:under|budget|max)\s+\$?([\d,]+)", text, re.IGNORECASE)
        budget_str = budget_match.group(1).replace(",", "") if budget_match else None
        budget_per_person = float(budget_str) if budget_str else None
        
        # Extract origin
        origin_match = re.search(r"(?:from|starting\s+in)\s+([a-z\s]+?)(?:\s+to|\s+visit|\s*$)", text, re.IGNORECASE)
        origin = origin_match.group(1).strip().title() if origin_match else "New York"
        
        return {
            "origin": origin,
            "destination": [destination],
            "dates": duration,
            "travelers": travelers,
            "budget_per_person": budget_per_person,
            "interests": []
        }
    
    def _llm_extract(self, text: str) -> Dict[str, Any]:
        """
        Extract using LLM.
        
        Returns:
            Dict with parsed fields
        """
        prompt = f"""
        Parse this trip request and extract key fields:
        "{text}"
        
        Return JSON:
        {{
            "origin": "starting city",
            "destination": ["target city"],
            "dates": "duration or date range",
            "travelers": 1,
            "budget_per_person": null or number,
            "interests": ["interest1", "interest2"]
        }}
        """
        
        try:
            response = self.llm.call_gemini(prompt)
            data = self.llm.extract_json(response)
            
            # Ensure destination is list
            if isinstance(data.get("destination"), str):
                data["destination"] = [data["destination"]]
            
            return data
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {
                "origin": "Unknown",
                "destination": ["Unknown"],
                "dates": "Upcoming Trip",
                "travelers": 1,
                "budget_per_person": None,
                "interests": []
            }
