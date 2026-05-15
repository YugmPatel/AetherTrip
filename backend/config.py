"""
Configuration: environment variables and constants.
Phase 2: Real API Integration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file)


class Config:
    """Global configuration."""
    
    # ===== LLM Services =====
    # OpenRouter (Primary)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4-turbo")
    
    # Ollama (Fallback)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    
    # ===== Routing =====
    OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")
    OPENROUTESERVICE_BASE_URL = os.getenv("OPENROUTESERVICE_BASE_URL", "https://api.openrouteservice.org")
    
    # ===== Places & Geocoding =====
    GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
    GEOAPIFY_BASE_URL = os.getenv("GEOAPIFY_BASE_URL", "https://api.geoapify.com/v1")
    
    # ===== Weather =====
    OPEN_METEO_BASE_URL = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")
    
    # ===== Knowledge Enrichment =====
    WIKIMEDIA_USER_AGENT = os.getenv("WIKIMEDIA_USER_AGENT", "AetherTrip/1.0 (your-email@example.com)")
    WIKIDATA_BASE_URL = "https://www.wikidata.org/w/api.php"
    WIKIPEDIA_BASE_URL = "https://en.wikipedia.org/w/api.php"
    
    # ===== Database (Future) =====
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # ===== Frontend =====
    NEXT_PUBLIC_GEOAPIFY_API_KEY = os.getenv("NEXT_PUBLIC_GEOAPIFY_API_KEY", "")
    NEXT_PUBLIC_API_BASE_URL = os.getenv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000")
    
    # ===== Cache =====
    CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
    
    # ===== Repair Loop =====
    MAX_REPAIR_ATTEMPTS = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
    
    # ===== Budget =====
    BUDGET_EMERGENCY_BUFFER_PERCENT = float(os.getenv("BUDGET_EMERGENCY_BUFFER_PERCENT", "0.05"))
    
    # ===== Logging =====
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # ===== Paths =====
    PROJECT_ROOT = Path(__file__).parent.parent
    CACHE_DIR = PROJECT_ROOT / ".cache"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # Ensure directories exist
    CACHE_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)


def get_config() -> Config:
    """Get global config instance."""
    return Config()
