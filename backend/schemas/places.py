"""
Place candidates schema: verified attractions, restaurants, accommodations, etc.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict


class SourceRef(BaseModel):
    """Reference to data source (URL, API, etc.)."""
    
    name: str = Field(..., description="Source name (e.g., 'Google Places', 'OpenWeather')")
    url: Optional[str] = Field(None, description="URL to source")
    fetched_at: str = Field(..., description="ISO 8601 timestamp when data was fetched")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Confidence 0–1 (1=verified)")


class PlaceCandidate(BaseModel):
    """A single verified place candidate for inclusion in itinerary."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "gp_the_getty",
                "name": "The Getty Museum",
                "category": "attraction",
                "address": "1200 Getty Center Drive, LA, CA 90049",
                "latitude": 34.0784,
                "longitude": -118.4733,
                "rating": 4.8,
                "estimated_cost": 15,
                "opening_hours": {
                    "monday_to_friday": "9:30 AM – 5:30 PM",
                    "saturday": "10:00 AM – 9:00 PM",
                    "closed": ["Sunday"]
                },
                "sources": [
                    {
                        "name": "Google Places",
                        "url": "https://maps.google.com/...",
                        "fetched_at": "2026-05-07T10:00:00Z",
                        "confidence": 0.95
                    }
                ],
                "verification_status": "verified",
                "confidence": 0.95
            }
        }
    )
    
    id: str = Field(..., description="Unique place ID")
    name: str = Field(..., description="Place name")
    category: str = Field(..., description="Category (e.g., 'restaurant', 'attraction', 'hotel')")
    address: Optional[str] = Field(None, description="Physical address")
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating (0–5)")
    price_level: Optional[str] = Field(None, description="Price level indicator")
    estimated_cost: Optional[float] = Field(None, ge=0, description="Estimated cost per person")
    
    opening_hours: Optional[Dict] = Field(
        None,
        description="Opening hours dict with keys like 'monday', 'tuesday', etc. or 'hours' if simple format"
    )
    dietary_tags: List[str] = Field(
        default_factory=list,
        description="Dietary indicators (e.g., ['vegetarian', 'vegan'])"
    )
    
    sources: List[SourceRef] = Field(
        default_factory=list,
        description="List of data sources this place came from"
    )
    source: str = Field(
        default="unknown",
        description="Primary provider alias for frontend/debug display"
    )
    source_provider: str = Field(
        default="unknown",
        description="Primary provider for this place candidate (e.g., geoapify)"
    )
    verification_status: str = Field(
        default="unverified",
        description="Status: 'unverified', 'verified', 'partially_verified'"
    )
    confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Overall confidence in place data (weighted from sources)"
    )
    source_confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Alias for source confidence used by frontend/debug tooling"
    )
    candidate_rank_score: float = Field(
        default=0.0,
        description="Internal ranking score used to prioritize itinerary-quality candidates"
    )
    image_url: Optional[str] = Field(None, description="Optional image URL from a trusted image provider")
    place_image_url: Optional[str] = Field(None, description="Legacy/provider image URL alias, if supplied")
    image_source: Optional[str] = Field(None, description="Image source: wikimedia, wikipedia, category_placeholder, none")
    image_credit: Optional[str] = Field(None, description="Image attribution or source credit")
    image_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence that the image matches the place")
    
    description: Optional[str] = Field(None, description="Brief description or summary")
    phone: Optional[str] = Field(None, description="Phone number if available")
    website: Optional[str] = Field(None, description="Official website URL")
    
