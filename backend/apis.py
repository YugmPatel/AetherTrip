import os
import requests
import json
import random
from typing import Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path
from backend.utils import setup_logger

# Load environment variables from .env file explicitly
# Assuming structure: AetherTrip/backend/apis.py -> .env is in AetherTrip/
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = setup_logger("APIs")

from backend.cache import get_cache_key, load_from_cache, save_to_cache

def search_web(query: str) -> str:
    """Performs a live web search using DuckDuckGo (Cached)."""
    cache_key = get_cache_key("search_web", query)
    cached = load_from_cache(cache_key)
    if cached:
        logger.info(f"Cache hit for search: {query[:20]}...")
        return cached

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                data = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
                save_to_cache(cache_key, data)
                return data
    except Exception as e:
        logger.error(f"Search failed: {e}")
    return "No live data available."

# ------------------------------------------------------------------
# LLM WRAPPER (Gemini)
# ------------------------------------------------------------------
def call_llm(prompt: str, system_instruction: str = None) -> str:
    """
    Calls Gemini API (Cached). Requires GOOGLE_API_KEY environment variable.
    """
    cache_key = get_cache_key("call_llm", prompt, system_instruction)
    cached = load_from_cache(cache_key)
    if cached:
        logger.info("Cache hit for LLM call.")
        return cached

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found. Returning mock response.")
        return _mock_llm_response(prompt)
    else:
        logger.info(f"API Key found: {api_key[:5]}...")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Construct payload
    full_prompt = prompt
    if system_instruction:
        full_prompt = f"System: {system_instruction}\nUser: {prompt}"
        
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }

    import time
    
    max_retries = 5
    base_delay = 10
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception("Rate limit exceeded after retries.")
            
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            save_to_cache(cache_key, text)
            return text
            
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"LLM API failed after {max_retries} attempts: {e}")
                raise e
            logger.warning(f"LLM call failed ({e}). Retrying...")
            time.sleep(1)

def _mock_llm_response(prompt: str) -> str:
    """
    Smart fallback that generates plausible JSON based on keywords in the prompt.
    This ensures the app looks functional even without an API key.
    """
    prompt_lower = prompt.lower()
    
    # 1. Input Analysis Mock
    if "analyze this trip request" in prompt_lower:
        # Extract destination from prompt if possible
        import re
        dest_match = re.search(r"request: \"(.*?)\"", prompt_lower)
        destination = "MOCK_TRIGGERED" # CHANGED FROM PARIS
        if dest_match:
            # Naive extraction: look for capitalized words or known countries
            text = dest_match.group(1)
            if "tokyo" in text: destination = "Tokyo"
            elif "paris" in text: destination = "Paris"
            elif "london" in text: destination = "London"
            elif "swiss" in text or "switzerland" in text: destination = "Swiss Alps"
            
        return json.dumps({
            "origin": "New York",
            "destination": [destination],
            "dates": "7 days",
            "interests": ["Sightseeing", "Food"]
        })

    # 2. City Selection Mock
    if "suggest 3 best cities" in prompt_lower:
        # Infer region
        if "italy" in prompt_lower:
            return json.dumps({"cities": ["Rome", "Venice", "Florence"]})
        if "japan" in prompt_lower:
            return json.dumps({"cities": ["Tokyo", "Kyoto", "Osaka"]})
        if "france" in prompt_lower:
            return json.dumps({"cities": ["Paris", "Nice", "Lyon"]})
        return json.dumps({"cities": ["City A", "City B", "City C"]})

    # 3. Itinerary Mock
    if "create a detailed day-by-day itinerary" in prompt_lower:
        # Check for duration in the prompt context (this is a heuristic)
        # In a real scenario, the agent passes this info more explicitly.
        days = 3
        if "1-week" in prompt_lower or "7 days" in prompt_lower or "week" in prompt_lower:
            days = 7
            
        plan = []
        activities = [
            ("Arrival & Exploration", "Arrive at the destination and check into the hotel. Enjoy a relaxing evening walk and local dinner."),
            ("Cultural Deep Dive", "Visit the main historical landmarks and museums. Experience the local culture and heritage."),
            ("Adventure & Leisure", "Take a day trip to nearby scenic spots or enjoy leisure activities like shopping and dining."),
            ("Hidden Gems", "Explore off-the-beaten-path neighborhoods and local markets."),
            ("Culinary Journey", "Take a food tour or cooking class to experience the local cuisine."),
            ("Nature & Relaxation", "Visit a nearby park, beach, or nature reserve for a relaxing day."),
            ("Farewell", "Buy souvenirs, enjoy a final special meal, and prepare for departure.")
        ]
        
        for i in range(days):
            act = activities[i % len(activities)]
            plan.append({"day": i+1, "title": act[0], "description": act[1]})
            
        return json.dumps({"plan": plan})

    # 4. Data Fetching Mocks (Weather, Flights, etc)
    if "weather" in prompt_lower:
        return json.dumps({"summary": "Sunny and pleasant", "temp": "22-25°C", "condition": "Clear Sky"})
    
    if "flight" in prompt_lower:
        return json.dumps({"airline": "Global Airways", "flight_number": "GA101", "price": 850, "duration": "8h 30m", "summary": "Direct Flight"})
        
    if "hotel" in prompt_lower:
        return json.dumps({"hotels": [{"name": "Grand Plaza", "price": 250, "rating": 4.8}, {"name": "City View Inn", "price": 180, "rating": 4.5}], "summary": "Grand Plaza, City View Inn"})
        
    if "attractions" in prompt_lower:
        return json.dumps({"highlights": ["Historic Old Town", "National Museum", "City Park"]})

    # Default JSON
    if "json" in prompt_lower:
        return "{}"
        
    return "Simulation: Unable to generate content."

# ------------------------------------------------------------------
# DATA FETCHING TOOLS (Simulated via LLM for Demo)
# ------------------------------------------------------------------
# In a production app, these would call Amadeus, OpenWeather, etc.
# Here, we use the LLM to generate *realistic* data to ensure the 
# end-to-end flow works beautifully for the user without 5 API keys.



def get_city_comprehensive_info(city: str, origin: str, dates: str) -> Dict[str, Any]:
    """
    Fetches ALL data for a city (Weather, Flights, Hotels, Attractions) in ONE LLM call.
    This drastically reduces API usage to avoid rate limits.
    """
    # 1. Perform Parallel-ish Searches (Fast, no LLM)
    weather_ctx = search_web(f"weather forecast {city} {dates}")
    flight_ctx = search_web(f"flights from {origin} to {city} price duration")
    hotel_ctx = search_web(f"best hotels in {city} price per night")
    attraction_ctx = search_web(f"top tourist attractions in {city} must visit")
    
    # 2. Single LLM Call to Synthesize Everything
    prompt = f"""
    Synthesize the following real-time search data for a trip to {city}.
    
    [Weather Search]: {weather_ctx}
    [Flight Search]: {flight_ctx}
    [Hotel Search]: {hotel_ctx}
    [Attraction Search]: {attraction_ctx}
    
    Return a SINGLE JSON object with these exact keys:
    {{
        "weather": {{ "summary": "...", "temp": "...", "condition": "..." }},
        "flights": {{ "airline": "...", "flight_number": "...", "price": 123, "duration": "...", "summary": "..." }},
        "hotels": {{ "hotels": [{{ "name": "...", "price": 123, "rating": 4.5 }}], "summary": "..." }},
        "attractions": {{ "highlights": ["...", "...", "..."] }}
    }}
    """
    
    try:
        resp = call_llm(prompt)
        return _clean_json(resp)
    except Exception as e:
        logger.error(f"Comprehensive fetch failed for {city}: {e}")
        return {}

def _clean_json(text: str) -> Dict[str, Any]:
    """Extracts JSON from LLM response text."""
    try:
        import re
        # Find JSON block
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {}
    except:
        return {}
