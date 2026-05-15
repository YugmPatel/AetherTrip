from datetime import datetime

from backend.agents.itinerary_builder import ItineraryBuilderAgent
from backend.schemas.places import PlaceCandidate, SourceRef
from backend.services.cache_service import CacheService
from backend.services.image_service import ImageService
from backend.services.places_service import PlacesService


def _candidate(image_url=None):
    return PlaceCandidate(
        id="p1",
        name="Balboa Park",
        category="park",
        address="San Diego, CA",
        latitude=32.7341,
        longitude=-117.1446,
        estimated_cost=0,
        sources=[SourceRef(name="Geoapify", fetched_at=datetime.utcnow().isoformat(), confidence=0.9)],
        source="geoapify",
        source_provider="geoapify",
        verification_status="verified",
        confidence=0.9,
        source_confidence=0.9,
        candidate_rank_score=100,
        image_url=image_url,
        image_source="wikimedia" if image_url else None,
        image_credit="Wikimedia Commons" if image_url else None,
        image_confidence=0.92 if image_url else None,
    )


def test_image_service_returns_none_gracefully_when_api_fails(monkeypatch, tmp_path):
    def failing_get(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("backend.services.image_service.httpx.get", failing_get)
    service = ImageService(CacheService(tmp_path))

    assert service.search_wikipedia_image("Balboa Park", "San Diego") is None
    assert service.search_wikimedia_commons_image("Balboa Park", "San Diego") is None


def test_category_placeholder_returned_for_missing_image(tmp_path):
    service = ImageService(CacheService(tmp_path))

    result = service.get_category_placeholder("museum")

    assert result.url is None
    assert result.source == "category_placeholder"
    assert result.confidence > 0
    assert "museum" in (result.credit or "")


def test_short_ambiguous_place_name_has_low_image_confidence(tmp_path):
    service = ImageService(CacheService(tmp_path))

    confidence = service._match_confidence("Bum", "San Diego", "Bum", "Unrelated article")

    assert confidence == 0


def test_itinerary_hydration_copies_image_url_from_candidate():
    candidate = _candidate("https://upload.wikimedia.org/example.jpg")
    item = ItineraryBuilderAgent()._item_from_candidate(
        candidate,
        day=1,
        start_time="09:00",
        end_time="11:00",
    )

    assert item["image_url"] == "https://upload.wikimedia.org/example.jpg"
    assert item["image_source"] == "wikimedia"
    assert item["image_credit"] == "Wikimedia Commons"
    assert item["image_confidence"] == 0.92


def test_image_enrichment_does_not_block_itinerary_generation(monkeypatch, tmp_path):
    service = PlacesService(CacheService(tmp_path))
    candidate = _candidate()

    def failing_enrichment(*args, **kwargs):
        raise RuntimeError("image api unavailable")

    monkeypatch.setattr(service.image_service, "enrich_place_image", failing_enrichment)
    enriched = service._enrich_candidate_images([candidate], "San Diego")

    assert enriched == [candidate]
