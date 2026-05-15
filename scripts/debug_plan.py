"""Debug one AetherTrip planning request without using the frontend."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


PROMPT = "Plan a 3-day Los Angeles trip from San Jose for 4 friends under $400 each, vegetarian, no car."
API_URL = os.getenv("AETHERTRIP_API_URL", "http://localhost:8000/api/trips/plan")


def _post_plan(prompt: str) -> dict[str, Any]:
    body = json.dumps({"user_input": prompt}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Backend returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach backend at {API_URL}: {exc}") from exc


def _items(trip: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for day in trip.get("itinerary", {}).get("days", []) or []
        for item in (day.get("items", []) or [])
    ]


def main() -> int:
    trip = _post_plan(PROMPT)
    constraints = trip.get("constraints") or {}
    hard = constraints.get("hard") or constraints
    places = trip.get("place_candidates") or []
    itinerary = trip.get("itinerary") or {}
    days = itinerary.get("days") or []
    validation_reports = trip.get("validation_reports") or []

    print("Prompt:")
    print(f"  {PROMPT}")
    print("\nConstraints:")
    print(json.dumps(constraints, indent=2, default=str))
    print(f"\nDestination: {hard.get('destination') or itinerary.get('destination')}")
    print(f"Place candidates: {len(places)}")
    print("\nFirst 5 place candidates:")
    for place in places[:5]:
        print(f"  - {place.get('name')} | id={place.get('id')} | lat={place.get('latitude')} | lon={place.get('longitude')}")

    print(f"\nItinerary days count: {len(days)}")
    print("Itinerary items:")
    for day in days:
        print(f"  Day {day.get('day') or day.get('day_number')}:")
        for item in day.get("items", []) or []:
            print(
                "    - "
                f"{item.get('place_name')} | id={item.get('place_id')} | "
                f"lat={item.get('latitude')} | lon={item.get('longitude')}"
            )

    print("\nBudget report:")
    print(json.dumps(trip.get("budget_report") or {}, indent=2, default=str))

    print("\nValidation warnings/errors:")
    for report in validation_reports:
        for issue in (report.get("issues") or []) + (report.get("warnings") or []):
            print(f"  - [{issue.get('severity')}] {issue.get('type')}: {issue.get('message')}")
    if not validation_reports:
        print("  none")

    print("\nService status:")
    print(json.dumps(trip.get("service_status") or trip.get("data_sources") or {}, indent=2, default=str))

    items = _items(trip)
    print("\nSummary:")
    print(json.dumps({
        "trip_id": trip.get("trip_id"),
        "destination": hard.get("destination") or itinerary.get("destination"),
        "days": len(days),
        "items": len(items),
        "missing_coordinates": sum(1 for item in items if item.get("latitude") is None or item.get("longitude") is None),
        "unknown_place_ids": [item.get("place_id") for item in items if "unknown" in str(item.get("place_id", "")).lower()],
        "status": trip.get("status"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
