"""
LLM Service: OpenRouter (primary) + Ollama (fallback) with structured outputs.
"""

import json
import re
from typing import Optional, Dict, Any
import logging

from openai import OpenAI, APIError, RateLimitError

from backend.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class LLMService:
    """LLM service with OpenRouter primary and Ollama fallback."""
    
    def __init__(self):
        """Initialize LLM clients."""
        # OpenRouter client (OpenAI-compatible)
        if config.OPENROUTER_API_KEY:
            self.openrouter_client = OpenAI(
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL,
            )
            logger.info("OpenRouter client initialized")
        else:
            self.openrouter_client = None
            logger.warning("OPENROUTER_API_KEY not set; will use Ollama only")
        
        # Ollama client (OpenAI-compatible endpoint)
        self.ollama_client = OpenAI(
            api_key="ollama",  # Dummy key for local
            base_url=config.OLLAMA_BASE_URL,
        )
    
    @staticmethod
    def call_openrouter(
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Call OpenRouter API (OpenAI-compatible).
        
        Args:
            prompt: User prompt
            system_instruction: Optional system message
            model: Model name (defaults to config.OPENROUTER_MODEL)
            
        Returns:
            Response text
        """
        if not config.OPENROUTER_API_KEY:
            logger.warning(
                "OpenRouter LLM call failed provider=openrouter endpoint=chat status=missing_api_key fallback_used=true"
            )
            return LLMService.call_ollama(prompt, system_instruction)
        
        model = model or config.OPENROUTER_MODEL
        
        try:
            logger.info(
                "OpenRouter LLM call started provider=openrouter endpoint=chat model=%s fallback_used=false",
                model,
            )
            client = OpenAI(
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL,
            )
            
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            request_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000,
            }
            if response_format:
                request_kwargs["response_format"] = response_format

            response = client.chat.completions.create(**request_kwargs)
            
            text = response.choices[0].message.content
            logger.info(
                "OpenRouter LLM call succeeded provider=openrouter endpoint=chat model=%s fallback_used=false",
                model,
            )
            return text
        
        except RateLimitError as e:
            logger.warning(
                "OpenRouter LLM call failed provider=openrouter endpoint=chat model=%s error_type=rate_limit fallback_used=true",
                model,
            )
            return LLMService.call_ollama(prompt, system_instruction)
        
        except APIError as e:
            logger.error(
                "OpenRouter LLM call failed provider=openrouter endpoint=chat model=%s error_type=api_error fallback_used=true",
                model,
            )
            return LLMService.call_ollama(prompt, system_instruction)

        except Exception:
            logger.exception(
                "OpenRouter LLM call failed provider=openrouter endpoint=chat model=%s error_type=unexpected fallback_used=true",
                model,
            )
            return LLMService.call_ollama(prompt, system_instruction)
    
    @staticmethod
    def call_ollama(
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Call Ollama API (local fallback).
        
        Args:
            prompt: User prompt
            system_instruction: Optional system message
            model: Model name (defaults to config.OLLAMA_MODEL)
            
        Returns:
            Response text
        """
        model = model or config.OLLAMA_MODEL
        
        try:
            logger.info(
                "Ollama LLM fallback call started provider=ollama endpoint=chat model=%s fallback_used=true",
                model,
            )
            client = OpenAI(
                api_key="ollama",
                base_url=config.OLLAMA_BASE_URL,
            )
            
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
            )
            
            text = response.choices[0].message.content
            logger.info(
                "Ollama LLM fallback call succeeded provider=ollama endpoint=chat model=%s fallback_used=true",
                model,
            )
            return text
        
        except Exception as e:
            logger.error(
                "Ollama LLM fallback call failed provider=ollama endpoint=chat model=%s fallback_used=true",
                model,
            )
            return LLMService._mock_response(prompt)
    
    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.
        
        Returns:
            Parsed JSON dict, or empty dict if extraction fails
        """
        try:
            # Try to find JSON block
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            logger.warning(f"JSON extraction failed: {e}")
        
        return {}
    
    @staticmethod
    def _mock_response(prompt: str) -> str:
        """
        Generate a mock response for dev/testing without API keys.
        Provides plausible defaults based on prompt keywords.
        """
        prompt_lower = prompt.lower()
        
        # Constraint extraction mock
        if "analyze" in prompt_lower and "trip" in prompt_lower:
            return json.dumps({
                "origin": "San Francisco",
                "destinations": ["Los Angeles", "San Diego"],
                "start_date": "2026-05-15",
                "end_date": "2026-05-18",
                "duration_days": 3,
                "travelers": 4,
                "budget_per_person": 400,
                "currency": "USD",
                "transport_mode": "car",
                "interests": ["beaches", "food", "nature"],
                "diet": ["vegetarian"],
                "must_visit": ["beaches"],
            })
        
        # Place candidates mock
        if "places" in prompt_lower or "attractions" in prompt_lower:
            return json.dumps({
                "places": [
                    {
                        "id": "mock_place_1",
                        "name": "Griffith Observatory",
                        "category": "attraction",
                        "address": "Los Angeles, CA",
                        "latitude": 34.1186,
                        "longitude": -118.3041,
                        "rating": 4.7,
                        "price_level": 1,
                        "estimated_cost": 0,
                        "opening_hours": {"hours": "9:00 AM - 10:00 PM"},
                        "confidence": 0.9
                    },
                    {
                        "id": "mock_place_2",
                        "name": "Santa Monica Beach",
                        "category": "attraction",
                        "address": "Santa Monica, CA",
                        "latitude": 34.0195,
                        "longitude": -118.4912,
                        "rating": 4.5,
                        "price_level": 1,
                        "estimated_cost": 0,
                        "opening_hours": {"hours": "Dawn - Dusk"},
                        "confidence": 0.95
                    }
                ]
            })
        
        # Itinerary mock
        if "itinerary" in prompt_lower:
            return json.dumps({
                "days": [
                    {
                        "day": 1,
                        "date": "2026-05-15",
                        "items": [
                            {
                                "start_time": "14:00",
                                "end_time": "17:00",
                                "place_name": "Hotel Check-in",
                                "category": "hotel",
                                "estimated_cost": 150,
                            },
                            {
                                "start_time": "18:00",
                                "end_time": "20:00",
                                "place_name": "Dinner at Local Restaurant",
                                "category": "restaurant",
                                "estimated_cost": 40,
                            }
                        ]
                    }
                ]
            })
        
        # Repair mock
        if "repair" in prompt_lower:
            return json.dumps({
                "repairs": [
                    {
                        "issue_type": "opening_hours_conflict",
                        "place": "Museum",
                        "fix": "Move visit to 9:00 AM when museum opens",
                        "confidence": 0.9
                    }
                ]
            })
        
        # Explanation mock
        if "explain" in prompt_lower or "why" in prompt_lower:
            return json.dumps({
                "explanation": "This is a well-planned trip with verified attractions, realistic travel times, and good budget allocation.",
                "highlights": [
                    "All attractions verified open during scheduled times",
                    "Travel distances and times are feasible",
                    "Budget includes hidden costs and contingency buffer",
                    "Activities match user preferences and interests",
                ]
            })
        
        # Default
        return json.dumps({"status": "ok"})
