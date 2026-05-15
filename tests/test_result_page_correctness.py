from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_place_detail_drawer_shows_opening_hours_unknown():
    drawer = read_source("frontend/components/PlaceDetailDrawer.tsx")
    helpers = read_source("frontend/lib/resultPage.ts")

    assert "getPlaceDetailValidation" in drawer
    assert "openingHoursStatus" in drawer
    assert "Unknown — verify manually" in helpers


def test_place_detail_drawer_shows_weather_risk_unknown():
    drawer = read_source("frontend/components/PlaceDetailDrawer.tsx")
    helpers = read_source("frontend/lib/resultPage.ts")

    assert "weatherRisk" in drawer
    assert "weatherServiceSucceeded" in helpers
    assert "Unknown — verify manually" in helpers


def test_why_this_trip_works_no_raw_markdown():
    component = read_source("frontend/components/WhyThisTripWorks.tsx")
    helpers = read_source("frontend/lib/resultPage.ts")

    assert "buildWhyTripSections" in component
    assert "whitespace-pre-line" not in component
    assert "Why This Trip Needs Review" in helpers
    assert "cleanMarkdownText" in helpers


def test_repair_history_no_object_object():
    component = read_source("frontend/components/RepairHistory.tsx")
    helpers = read_source("frontend/lib/resultPage.ts")

    assert "formatRepairHistoryItem" in component
    assert "formatRepairValue" in helpers
    assert "[object Object]" not in component


def test_warning_grouping_repeated_unknown_opening_hours():
    component = read_source("frontend/components/ValidationWarnings.tsx")
    helpers = read_source("frontend/lib/resultPage.ts")

    assert "getGroupedValidationIssues" in component
    assert "unknown_opening_hours_grouped" in helpers
    assert "places have" in helpers
    assert "unknown opening hours" in helpers
