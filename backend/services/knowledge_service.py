"""
Knowledge Service: Wikidata + Wikipedia enrichment for places.
No API key required; includes caching.
"""

import logging
from typing import Optional, Dict, Any

import httpx

from backend.config import get_config
from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)
config = get_config()


class KnowledgeService:
    """Enrich places with knowledge from Wikidata and Wikipedia."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize knowledge service with optional caching."""
        self.cache_service = cache_service or CacheService()
        self.wikidata_base_url = config.WIKIDATA_BASE_URL
        self.wikipedia_base_url = config.WIKIPEDIA_BASE_URL
        self.user_agent = config.WIKIMEDIA_USER_AGENT
        self.last_status: Dict[str, Any] = {
            "provider": "wikidata_wikipedia",
            "status": "not_started",
            "used_fallback": False,
            "count": 0,
        }
    
    def get_place_summary(self, place_name: str) -> Optional[str]:
        """
        Get Wikipedia summary for a place.
        
        Args:
            place_name: Name of the place
            
        Returns:
            Summary text or None
        """
        cache_key = f"wiki_summary_{place_name}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(
                "Wikidata/Wikipedia enrichment succeeded provider=wikidata_wikipedia endpoint_type=wikipedia_summary destination=%s count=1 fallback_used=false cache_hit=true",
                place_name,
            )
            return cached
        
        try:
            logger.info(
                "Wikidata/Wikipedia enrichment started provider=wikidata_wikipedia endpoint_type=wikipedia_summary destination=%s fallback_used=false",
                place_name,
            )
            params = {
                "action": "query",
                "titles": place_name,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "format": "json",
            }
            
            headers = {"User-Agent": self.user_agent}
            
            response = httpx.get(
                self.wikipedia_base_url,
                params=params,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract summary from pages
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "extract" in page_data:
                    summary = page_data["extract"][:500]  # First 500 chars
                    
                    # Cache result
                    self.cache_service.set(cache_key, summary)
                    logger.info(
                        "Wikidata/Wikipedia enrichment succeeded provider=wikidata_wikipedia endpoint_type=wikipedia_summary destination=%s count=1 fallback_used=false",
                        place_name,
                    )
                    
                    return summary
            
            logger.warning(
                "Wikidata/Wikipedia enrichment succeeded provider=wikidata_wikipedia endpoint_type=wikipedia_summary destination=%s count=0 fallback_used=false",
                place_name,
            )
            return None
        
        except Exception as e:
            logger.error(
                "Wikidata/Wikipedia enrichment failed provider=wikidata_wikipedia endpoint_type=wikipedia_summary destination=%s count=0 fallback_used=false",
                place_name,
            )
            return None
    
    def get_wikidata_facts(self, place_name: str) -> Dict[str, Any]:
        """
        Get structured facts from Wikidata.
        
        Args:
            place_name: Name of the place
            
        Returns:
            Dictionary of facts (opening hours, website, etc.)
        """
        cache_key = f"wikidata_facts_{place_name}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(
                "Wikidata/Wikipedia enrichment succeeded provider=wikidata_wikipedia endpoint_type=wikidata_facts destination=%s count=1 fallback_used=false cache_hit=true",
                place_name,
            )
            return cached
        
        try:
            logger.info(
                "Wikidata/Wikipedia enrichment started provider=wikidata_wikipedia endpoint_type=wikidata_facts destination=%s fallback_used=false",
                place_name,
            )
            params = {
                "action": "wbsearchentities",
                "search": place_name,
                "language": "en",
                "format": "json",
            }
            
            headers = {"User-Agent": self.user_agent}
            
            response = httpx.get(
                self.wikidata_base_url,
                params=params,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            results = data.get("search", [])
            if not results:
                logger.warning(
                    "Wikidata/Wikipedia enrichment succeeded provider=wikidata_wikipedia endpoint_type=wikidata_facts destination=%s count=0 fallback_used=false",
                    place_name,
                )
                return {}
            
            # Get first result
            entity_id = results[0].get("id")
            if not entity_id:
                return {}
            
            # Get entity details
            entity_data = self._get_entity_details(entity_id)
            
            # Cache result
            self.cache_service.set(cache_key, entity_data)
            logger.info(
                "Wikidata/Wikipedia enrichment succeeded provider=wikidata_wikipedia endpoint_type=wikidata_facts destination=%s count=%s fallback_used=false",
                place_name,
                1 if entity_data else 0,
            )
            
            return entity_data
        
        except Exception as e:
            logger.error(
                "Wikidata/Wikipedia enrichment failed provider=wikidata_wikipedia endpoint_type=wikidata_facts destination=%s count=0 fallback_used=false",
                place_name,
            )
            return {}
    
    def _get_entity_details(self, entity_id: str) -> Dict[str, Any]:
        """Get details for a Wikidata entity."""
        try:
            params = {
                "action": "wbgetentities",
                "ids": entity_id,
                "format": "json",
            }
            
            headers = {"User-Agent": self.user_agent}
            
            response = httpx.get(
                self.wikidata_base_url,
                params=params,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            entities = data.get("entities", {})
            
            if entity_id in entities:
                entity = entities[entity_id]
                
                # Extract useful properties
                facts = {}
                
                if "descriptions" in entity:
                    desc = entity["descriptions"].get("en", {})
                    if "value" in desc:
                        facts["description"] = desc["value"]
                
                # Extract claims (properties)
                if "claims" in entity:
                    claims = entity["claims"]
                    
                    # Common properties
                    # P625 = coordinate location
                    # P625 = website
                    # P856 = official website
                    # P1566 = GeoNames ID
                    
                    if "P625" in claims:
                        coord_claim = claims["P625"][0]
                        if "mainsnak" in coord_claim:
                            datavalue = coord_claim["mainsnak"].get("datavalue", {})
                            if "value" in datavalue:
                                coord = datavalue["value"]
                                facts["latitude"] = coord.get("latitude")
                                facts["longitude"] = coord.get("longitude")
                    
                    if "P856" in claims:
                        website_claim = claims["P856"][0]
                        if "mainsnak" in website_claim:
                            datavalue = website_claim["mainsnak"].get("datavalue", {})
                            facts["website"] = datavalue.get("value")
                
                return facts
        
        except Exception as e:
            logger.error(f"Entity details fetch failed: {e}")
            return {}
    
    def enrich_place(self, place_name: str) -> Dict[str, Any]:
        """
        Enrich a place with Wikipedia summary and Wikidata facts.
        
        Args:
            place_name: Name of the place
            
        Returns:
            Dictionary with summary and facts
        """
        cache_key = f"enriched_place_{place_name}"
        cached = self.cache_service.get(cache_key)
        
        if cached:
            logger.info(
                "Wikidata/Wikipedia enrichment succeeded provider=wikidata_wikipedia endpoint_type=enrichment destination=%s count=1 fallback_used=false cache_hit=true",
                place_name,
            )
            self.last_status = {
                "provider": "wikidata_wikipedia",
                "status": "success",
                "destination": place_name,
                "count": 1,
                "used_fallback": False,
                "cache_hit": True,
            }
            return cached
        
        result = {
            "name": place_name,
            "summary": self.get_place_summary(place_name),
            "facts": self.get_wikidata_facts(place_name),
        }
        
        # Cache result
        self.cache_service.set(cache_key, result)
        self.last_status = {
            "provider": "wikidata_wikipedia",
            "status": "success" if result.get("summary") or result.get("facts") else "skipped",
            "destination": place_name,
            "count": 1 if result.get("summary") or result.get("facts") else 0,
            "used_fallback": False,
        }
        
        return result
