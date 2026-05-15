"""Image enrichment using Wikimedia/Wikipedia APIs only."""

import logging
import re
import time
from html import unescape
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

from backend.config import get_config
from backend.schemas.places import PlaceCandidate
from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)
config = get_config()

IMAGE_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


class ImageResult(BaseModel):
    """Trusted image lookup result."""

    url: Optional[str] = None
    source: str = Field(default="none")
    credit: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0, le=1)


class ImageService:
    """Finds safe place images from Wikimedia/Wikipedia and category placeholders."""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.wikipedia_base_url = config.WIKIPEDIA_BASE_URL
        self.commons_base_url = "https://commons.wikimedia.org/w/api.php"
        self.user_agent = config.WIKIMEDIA_USER_AGENT

    def enrich_place_image(self, place: PlaceCandidate, destination: str) -> PlaceCandidate:
        """Return a copy of a place candidate with image metadata populated."""
        existing_url = place.image_url or place.place_image_url
        if existing_url:
            return place.model_copy(update={
                "image_url": existing_url,
                "image_source": place.image_source or "existing",
                "image_credit": place.image_credit,
                "image_confidence": place.image_confidence if place.image_confidence is not None else 0.8,
            })

        cache_key = self._cache_key(place.name, destination)
        cached = self._get_cached(cache_key)
        if cached:
            return self._apply_result(place, cached)

        result = None
        if self._should_try_real_image(place):
            result = self.search_wikipedia_image(place.name, destination)
            if not result:
                result = self.search_wikimedia_commons_image(place.name, destination)

        if not result:
            result = self.get_category_placeholder(place.category)

        self._set_cached(cache_key, result)
        return self._apply_result(place, result)

    def search_wikipedia_image(self, place_name: str, destination: str) -> Optional[ImageResult]:
        """Search English Wikipedia for a page image that confidently matches the place."""
        query = self._query(place_name, destination)
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": 5,
            "prop": "pageimages|info|extracts",
            "piprop": "original|thumbnail",
            "pithumbsize": 900,
            "inprop": "url",
            "exintro": True,
            "explaintext": True,
            "format": "json",
        }
        try:
            response = httpx.get(self.wikipedia_base_url, params=params, headers=self._headers(), timeout=5.0)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
        except Exception as exc:
            logger.info("Wikipedia image lookup failed for %s: %s", place_name, type(exc).__name__)
            return None

        best: Optional[ImageResult] = None
        for page in pages.values():
            title = page.get("title") or ""
            extract = page.get("extract") or ""
            if self._is_bad_page(title, extract):
                continue
            image = page.get("original") or page.get("thumbnail") or {}
            url = image.get("source")
            if not self._trusted_image_url(url):
                continue
            confidence = self._match_confidence(place_name, destination, title, extract)
            if confidence < 0.7:
                continue
            result = ImageResult(
                url=url,
                source="wikipedia",
                credit=page.get("fullurl") or f"Wikipedia: {title}",
                confidence=confidence,
            )
            if not best or result.confidence > best.confidence:
                best = result

        return best

    def search_wikimedia_commons_image(self, place_name: str, destination: str) -> Optional[ImageResult]:
        """Search Wikimedia Commons file results for a confident place image."""
        query = self._query(place_name, destination)
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": 900,
            "format": "json",
        }
        try:
            response = httpx.get(self.commons_base_url, params=params, headers=self._headers(), timeout=5.0)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
        except Exception as exc:
            logger.info("Wikimedia Commons image lookup failed for %s: %s", place_name, type(exc).__name__)
            return None

        best: Optional[ImageResult] = None
        for page in pages.values():
            title = page.get("title") or ""
            if self._is_bad_image_title(title):
                continue
            image_info = (page.get("imageinfo") or [{}])[0]
            url = image_info.get("thumburl") or image_info.get("url")
            if not self._trusted_image_url(url):
                continue
            metadata = image_info.get("extmetadata") or {}
            confidence = self._match_confidence(place_name, destination, title, "")
            if confidence < 0.7:
                continue
            result = ImageResult(
                url=url,
                source="wikimedia",
                credit=self._metadata_credit(metadata) or title,
                confidence=confidence,
            )
            if not best or result.confidence > best.confidence:
                best = result

        return best

    def get_category_placeholder(self, category: str) -> ImageResult:
        """Return metadata for frontend-rendered local category placeholders."""
        return ImageResult(
            url=None,
            source="category_placeholder",
            credit=f"Local {self._placeholder_label(category)} placeholder",
            confidence=0.35,
        )

    def _apply_result(self, place: PlaceCandidate, result: ImageResult) -> PlaceCandidate:
        return place.model_copy(update={
            "image_url": result.url,
            "image_source": result.source,
            "image_credit": result.credit,
            "image_confidence": result.confidence,
        })

    def _should_try_real_image(self, place: PlaceCandidate) -> bool:
        category = (place.category or "").lower()
        text = f"{category} {place.name}".lower()
        return any(term in text for term in [
            "attraction",
            "landmark",
            "museum",
            "park",
            "monument",
            "viewpoint",
            "view",
            "sight",
            "historic",
            "nature",
            "trail",
        ])

    def _headers(self) -> Dict[str, str]:
        return {"User-Agent": self.user_agent}

    def _query(self, place_name: str, destination: str) -> str:
        return " ".join(part for part in [place_name, destination] if part).strip()

    def _cache_key(self, place_name: str, destination: str) -> str:
        raw = f"image_v2:{place_name}:{destination}".lower()
        return re.sub(r"[^a-z0-9_-]+", "_", raw).strip("_")[:180]

    def _get_cached(self, key: str) -> Optional[ImageResult]:
        cached = self.cache_service.get(key)
        if not isinstance(cached, dict):
            return None
        cached_at = cached.get("cached_at")
        if not isinstance(cached_at, (int, float)) or time.time() - cached_at > IMAGE_CACHE_TTL_SECONDS:
            return None
        result = cached.get("result")
        if not isinstance(result, dict):
            return None
        try:
            return ImageResult(**result)
        except Exception:
            return None

    def _set_cached(self, key: str, result: ImageResult) -> None:
        self.cache_service.set(key, {"cached_at": time.time(), "result": result.model_dump()})

    def _trusted_image_url(self, url: Optional[str]) -> bool:
        if not url:
            return False
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return parsed.scheme in {"http", "https"} and (
            host.endswith("wikimedia.org") or host.endswith("wikipedia.org")
        )

    def _is_bad_page(self, title: str, extract: str) -> bool:
        text = f"{title} {extract}".lower()
        return "disambiguation" in text or "may refer to" in text

    def _is_bad_image_title(self, title: str) -> bool:
        text = title.lower()
        return any(term in text for term in ["disambiguation", "logo", "seal", "flag", "map"])

    def _match_confidence(self, place_name: str, destination: str, title: str, extract: str) -> float:
        place_tokens = self._tokens(place_name)
        destination_tokens = self._tokens(destination)
        haystack = f"{title} {extract}".lower()
        if not place_tokens:
            return 0.0
        if len(place_tokens) == 1 and len(place_tokens[0]) < 5:
            return 0.0

        place_hits = sum(1 for token in place_tokens if token in haystack)
        destination_hits = sum(1 for token in destination_tokens if token in haystack)
        place_ratio = place_hits / max(len(place_tokens), 1)
        confidence = 0.45 + place_ratio * 0.4
        if destination_tokens and destination_hits:
            confidence += 0.1
        if self._normalize_title(place_name) == self._normalize_title(title):
            confidence += 0.15
        return min(confidence, 0.98)

    def _tokens(self, value: str) -> list[str]:
        stopwords = {"the", "a", "an", "and", "of", "at", "in", "on", "view", "spot"}
        return [
            token
            for token in re.findall(r"[a-z0-9]+", (value or "").lower())
            if len(token) > 2 and token not in stopwords
        ]

    def _normalize_title(self, value: str) -> str:
        return " ".join(self._tokens(value))

    def _metadata_credit(self, metadata: Dict[str, Any]) -> Optional[str]:
        for key in ["Credit", "Artist", "ObjectName"]:
            value = (metadata.get(key) or {}).get("value")
            if value:
                text = re.sub(r"<[^>]+>", "", str(value))
                text = unescape(text).strip()
                if text:
                    return text[:180]
        return None

    def _placeholder_label(self, category: str) -> str:
        category_lower = (category or "").lower()
        if "museum" in category_lower:
            return "museum"
        if any(term in category_lower for term in ["restaurant", "food", "cafe"]):
            return "food"
        if any(term in category_lower for term in ["park", "nature", "trail"]):
            return "park"
        if "view" in category_lower:
            return "viewpoint"
        if "attraction" in category_lower:
            return "attraction"
        return "place"
