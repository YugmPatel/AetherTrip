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


CITY_ALIASES = {
    "nyc": "New York City",
    "new york": "New York City",
    "new york city": "New York City",
    "la": "Los Angeles",
    "l.a.": "Los Angeles",
    "los angeles": "Los Angeles",
    "sf": "San Francisco",
    "s.f.": "San Francisco",
    "san francisco": "San Francisco",
    "seattle": "Seattle",
}


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
        logger.info("InputAnalyzerAgent: parsing raw user input=%s", state.user_input)
        
        # Try deterministic extraction first. This keeps common prompts reliable even
        # when the LLM provider is unavailable.
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
        
        # Extract destination from common forms:
        # "trip to Los Angeles", "in Los Angeles", or "3-day Los Angeles trip".
        destination = self._extract_destination(text)
        destination_patterns = [
            r"\b(?:trip|travel|vacation)\s+(?:to|in)\s+([a-z][a-z\s]+?)(?:\s+from|\s+for|\s+under|\s+with|,|\.|$)",
            r"\b(?:to|visit|in)\s+([a-z][a-z\s]+?)(?:\s+from|\s+for|\s+during|\s+under|\s+with|,|\.|$)",
            r"\b(?:\d+\s*-\s*day|\d+\s*day|weekend|day)\s+([a-z][a-z\s]+?)\s+(?:trip|travel|vacation)\b",
        ]
        if not destination:
            for pattern in destination_patterns:
                dest_match = re.search(pattern, text, re.IGNORECASE)
                if dest_match:
                    destination = self._clean_place_name(dest_match.group(1))
                    break
        
        if not destination:
            return None
        
        # Extract duration
        duration_match = re.search(r"(\d+)\s*(?:-\s*)?days?", text, re.IGNORECASE)
        if duration_match:
            duration = f"{duration_match.group(1)} days"
        elif "weekend" in text_lower:
            duration = "2 days"
        else:
            duration = "3 days"
        
        # Extract travelers
        travelers_match = re.search(r"(?:for|with)\s+(\d+)\s+(?:people|friends|travelers|travellers|persons?|adults?)", text, re.IGNORECASE)
        travelers = int(travelers_match.group(1)) if travelers_match else 1
        
        # Extract budget
        budget_match = re.search(r"(?:under|less than|budget|max(?:imum)?|up to)\s+\$?([\d,]+)", text, re.IGNORECASE)
        budget_str = budget_match.group(1).replace(",", "") if budget_match else None
        budget_per_person = float(budget_str) if budget_str else None
        
        # Extract origin
        origin_match = re.search(
            r"(?:from|starting\s+in|leaving\s+from)\s+([a-z][a-z\s]+?)(?:\s+to|\s+for\s+\d+|\s+under|\s+with|,|\.|$)",
            text,
            re.IGNORECASE,
        )
        origin = self._clean_place_name(origin_match.group(1)) if origin_match else None

        diet = []
        diet_keywords = {
            "vegetarian": "vegetarian",
            "vegan": "vegan",
            "gluten-free": "gluten-free",
            "gluten free": "gluten-free",
            "halal": "halal",
            "kosher": "kosher",
        }
        for phrase, value in diet_keywords.items():
            if phrase in text_lower and value not in diet:
                diet.append(value)

        transport_mode = "public_transit"
        if re.search(r"\b(no car|without a car|car[-\s]?free|public transit|public transport|transit)\b", text_lower):
            transport_mode = "no_car" if "no car" in text_lower or "no-car" in text_lower or "without a car" in text_lower or "car-free" in text_lower else "public_transit"
        elif re.search(r"\bwalk(?:ing)?\b", text_lower):
            transport_mode = "walking"
        elif re.search(r"\bdrive|driving|rental car|car\b", text_lower):
            transport_mode = "car"

        interests = []
        interest_keywords = {
            "food": ["food", "restaurant", "dining"],
            "museum": ["museum", "art", "gallery"],
            "beach": ["beach", "coast", "ocean"],
            "nature": ["park", "hiking", "nature", "outdoor"],
            "attraction": ["sightseeing", "landmark", "attraction"],
        }
        for interest, keywords in interest_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                interests.append(interest)

        defaults_applied = []
        if not origin:
            defaults_applied.append("origin=null")
        if not duration_match and "weekend" not in text_lower:
            defaults_applied.append("duration_days=3")
        if not travelers_match:
            defaults_applied.append("travelers=1")
        if not budget_match:
            defaults_applied.append("budget_per_person=null")
        if "vegetarian" in text_lower and "food" not in interests:
            interests.append("food")
        
        return {
            "origin": origin,
            "destination": [destination],
            "dates": duration,
            "travelers": travelers,
            "budget_per_person": budget_per_person,
            "budget_status": "unknown" if budget_per_person is None else "specified",
            "budget_style": "budget" if "budget" in text_lower else None,
            "currency": "USD",
            "transport_mode": transport_mode,
            "no_car": transport_mode == "no_car",
            "weather_preference": "rain_safe" if "rain-safe" in text_lower or "rain safe" in text_lower else None,
            "diet": diet,
            "interests": interests,
            "pace": "balanced",
            "defaults_applied": defaults_applied,
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
            "currency": "USD",
            "transport_mode": "mixed|no_car|public_transit|walking|car",
            "diet": ["vegetarian"],
            "interests": ["interest1", "interest2"],
            "defaults_applied": []
        }}
        """
        
        try:
            response = self.llm.call_openrouter(prompt)
            data = self.llm.extract_json(response)
            
            # Ensure destination is list
            if isinstance(data.get("destination"), str):
                data["destination"] = [data["destination"]]
            if not data.get("destination"):
                regex_data = self._regex_extract(text)
                if regex_data:
                    data.update({k: v for k, v in regex_data.items() if v not in (None, [], "")})
            data = self._apply_safe_defaults(data, text)
            
            return data
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            fallback = self._regex_extract(text) or {}
            return self._apply_safe_defaults(fallback, text)

    def _extract_destination(self, text: str) -> str:
        """Recognize common destination aliases and compact quick-prompt city names."""
        text_lower = text.lower()
        for alias, canonical in sorted(CITY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            pattern = r"(?<![a-z])" + re.escape(alias.lower()) + r"(?![a-z])"
            if re.search(pattern, text_lower):
                return canonical

        quick_match = re.search(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:itinerary|trip|weekend)\b",
            text,
        )
        if quick_match:
            return self._clean_place_name(quick_match.group(1))

        return ""

    def _apply_safe_defaults(self, data: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Apply non-fatal defaults for destination-only travel prompts."""
        text_lower = text.lower()
        data = dict(data or {})
        defaults_applied = list(data.get("defaults_applied") or [])

        destination = data.get("destination") or data.get("destinations")
        if isinstance(destination, list):
            destination_value = destination[0] if destination else None
        else:
            destination_value = destination
        if destination_value in (None, "", "Unknown", "Your Trip"):
            destination_value = self._extract_destination(text)
            if destination_value:
                defaults_applied.append("destination=deterministic_alias")
        if destination_value:
            data["destination"] = [self._clean_place_name(destination_value)]

        if not data.get("dates") and not data.get("duration_days"):
            data["dates"] = "2 days" if "weekend" in text_lower else "3 days"
            defaults_applied.append("duration_days=2" if "weekend" in text_lower else "duration_days=3")

        if not data.get("travelers"):
            data["travelers"] = 1
            defaults_applied.append("travelers=1")

        if "budget_per_person" not in data:
            data["budget_per_person"] = None
        data["budget_status"] = "specified" if data.get("budget_per_person") is not None else "unknown"
        if "budget" in text_lower and not data.get("budget_style"):
            data["budget_style"] = "budget"

        diet = list(data.get("diet") or [])
        if "vegetarian" in text_lower and "vegetarian" not in diet:
            diet.append("vegetarian")
        data["diet"] = diet

        transport = data.get("transport_mode")
        if not transport or transport in {"mixed", "Unknown"}:
            transport = "public_transit"
            defaults_applied.append("transport_mode=public_transit")
        if "no car" in text_lower or "no-car" in text_lower or "without a car" in text_lower:
            transport = "no_car"
        data["transport_mode"] = transport
        data["no_car"] = transport == "no_car"

        if "rain-safe" in text_lower or "rain safe" in text_lower:
            data["weather_preference"] = "rain_safe"

        interests = list(data.get("interests") or [])
        if diet and "food" not in interests:
            interests.append("food")
        data["interests"] = interests
        data["pace"] = data.get("pace") or "balanced"
        data["defaults_applied"] = defaults_applied
        data.setdefault("currency", "USD")
        data["origin"] = data.get("origin") if data.get("origin") not in {"Unknown", ""} else None
        return data

    def _clean_place_name(self, value: str) -> str:
        """Normalize a captured place name without stripping meaningful spaces."""
        if value is None:
            return ""
        alias = CITY_ALIASES.get(str(value).strip().lower())
        if alias:
            return alias
        cleaned = re.sub(r"\b(trip|travel|vacation|plan|a|an|the)\b", "", value, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.")
        alias = CITY_ALIASES.get(cleaned.lower())
        if alias:
            return alias
        return cleaned.title()
