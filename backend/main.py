"""
AetherTrip FastAPI backend: accuracy-first travel planner.
"""

import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.state import TripState
from backend.graph import AetherTripGraph
from backend.schemas import TripRequest, TripResponse
from backend.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
config = get_config()

graph = None
trip_store = {}


PIPELINE_STAGES = [
    {
        "stage": "understanding_request",
        "label": "Understanding Request",
        "message": "Parsing the natural-language request and identifying travel intent.",
        "agent": "InputAnalyzerAgent",
        "service": "OpenRouter LLM",
    },
    {
        "stage": "extracting_constraints",
        "label": "Extracting Constraints",
        "message": "Identifying destination, duration, budget, travelers, diet, and mobility requirements.",
        "agent": "ConstraintExtractorAgent",
        "service": "OpenRouter LLM",
    },
    {
        "stage": "geocoding_destination",
        "label": "Geocoding Destination",
        "message": "Resolving destination coordinates with Geoapify.",
        "agent": "GroundingDataFetcher",
        "service": "Geoapify",
    },
    {
        "stage": "fetching_places_geoapify",
        "label": "Fetching Real Places",
        "message": "Searching verified attractions and restaurants with Geoapify Places.",
        "agent": "GroundingDataFetcher",
        "service": "Geoapify Places",
    },
    {
        "stage": "fetching_weather_open_meteo",
        "label": "Checking Weather",
        "message": "Fetching forecast context with Open-Meteo.",
        "agent": "GroundingDataFetcher",
        "service": "Open-Meteo Weather",
    },
    {
        "stage": "building_route_matrix_openrouteservice",
        "label": "Calculating Travel Times",
        "message": "Building route matrix with OpenRouteService.",
        "agent": "GroundingDataFetcher",
        "service": "OpenRouteService Routing",
    },
    {
        "stage": "building_candidate_itinerary",
        "label": "Building Candidate Itinerary",
        "message": "Composing a candidate day-by-day itinerary from grounded data.",
        "agent": "ItineraryBuilderAgent",
        "service": "OpenRouter LLM",
    },
    {
        "stage": "validating_opening_hours",
        "label": "Validating Opening Hours",
        "message": "Checking scheduled stops against available opening-hour evidence.",
        "agent": "OpeningHoursValidator",
        "service": "Geoapify Places",
    },
    {
        "stage": "validating_travel_time",
        "label": "Validating Travel Time",
        "message": "Checking route feasibility using the computed travel matrix.",
        "agent": "RouteTimeValidator",
        "service": "OpenRouteService Routing",
    },
    {
        "stage": "validating_budget",
        "label": "Validating Budget",
        "message": "Summing base costs, hidden costs, and budget buffers.",
        "agent": "BudgetValidator",
        "service": "AetherTrip Budget Validator",
    },
    {
        "stage": "validating_weather",
        "label": "Validating Weather",
        "message": "Checking weather-sensitive itinerary items.",
        "agent": "WeatherValidator",
        "service": "Open-Meteo Weather",
    },
    {
        "stage": "auto_repair_if_needed",
        "label": "Repairing If Needed",
        "message": "Applying repair cycles if validators found critical issues.",
        "agent": "RepairAgent",
        "service": "AetherTrip Repair Engine",
    },
    {
        "stage": "scoring_feasibility",
        "label": "Scoring Feasibility",
        "message": "Calculating the final multi-layer feasibility score.",
        "agent": "FeasibilityScorer",
        "service": "AetherTrip Scoring Engine",
    },
    {
        "stage": "explanation_agent",
        "label": "Generating Explanation",
        "message": "Generating a concise explanation from validation facts.",
        "agent": "ExplanationAgent",
        "service": "OpenRouter LLM",
    },
    {
        "stage": "completed",
        "label": "Completed",
        "message": "Trip plan is ready.",
        "agent": "AetherTripGraph",
        "service": "AetherTrip API",
    },
]


def _progress_for(stage: str) -> int:
    index = next((i for i, item in enumerate(PIPELINE_STAGES) if item["stage"] == stage), 0)
    return round((index / (len(PIPELINE_STAGES) - 1)) * 100)


def _pipeline_event(
    stage: str,
    status: str,
    *,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    trip: Optional[TripResponse] = None,
) -> Dict[str, Any]:
    meta = next((item for item in PIPELINE_STAGES if item["stage"] == stage), PIPELINE_STAGES[0])
    event = {
        "stage": stage,
        "label": meta["label"],
        "status": status,
        "message": message or meta["message"],
        "agent": meta["agent"],
        "service": meta["service"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "details": details or {},
        "progress_percent": 100 if stage == "completed" and status == "completed" else _progress_for(stage),
    }
    if trip is not None:
        event["trip"] = trip.model_dump()
    return event


def _as_sse(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


def _merge_state_update(state: TripState, update: Dict[str, Any]) -> TripState:
    state_data = state.model_dump()
    for key, value in update.items():
        if key == "errors":
            state_data["errors"] = [*state_data.get("errors", []), *[_clean_error_message(v) for v in (value or [])]]
        elif key == "warnings":
            state_data["warnings"] = [*state_data.get("warnings", []), *[_clean_error_message(v) for v in (value or [])]]
        elif key == "service_status":
            state_data["service_status"] = {**state_data.get("service_status", {}), **(value or {})}
        else:
            state_data[key] = value
    return TripState(**state_data)


def _clean_error_message(message: Any) -> str:
    """Convert internal exceptions into short user-safe messages."""
    text = str(message)
    text = re.sub(r"https://errors\.pydantic\.dev/\S+", "", text).strip()
    if "validation error" in text.lower() and "pydantic" in text.lower():
        return "Trip data validation failed. Please retry after checking the request details."
    return text or "Trip planning encountered an internal validation issue."


def _clean_message_list(messages: Any) -> list[str]:
    cleaned = []
    seen = set()
    for message in messages or []:
        text = _clean_error_message(message)
        if text not in seen:
            cleaned.append(text)
            seen.add(text)
    return cleaned


def _failure_message_from_state(state: Optional[TripState], fallback: Any = None) -> str:
    """Return a user-safe stream failure message without stack traces or secrets."""
    errors = list(getattr(state, "errors", []) or [])
    joined = " ".join(str(error) for error in errors)
    if "no destination" in joined.lower() or "need destination" in joined.lower():
        return "Grounding failed: no destination extracted"
    if "no place candidates" in joined.lower() or "No verified place candidates" in joined:
        return "Itinerary generation failed: no place candidates available"
    if errors:
        return _clean_error_message(errors[-1])
    if fallback:
        return _clean_error_message(fallback)
    return "Trip planning failed."


def _default_service_status() -> Dict[str, Any]:
    return {
        "llm": {"provider": "openrouter", "status": "skipped", "model": config.OPENROUTER_MODEL, "used_fallback": False},
        "geocoding": {"provider": "geoapify", "status": "not_started", "used_fallback": False, "coordinates_found": False},
        "places": {"provider": "geoapify", "status": "not_started", "count": 0, "used_fallback": False},
        "weather": {"provider": "open_meteo", "status": "not_started", "used_fallback": False},
        "routing": {"provider": "openrouteservice", "status": "not_started", "used_fallback": False},
        "knowledge": {"provider": "wikidata_wikipedia", "status": "skipped", "used_fallback": False},
        "itinerary_builder": {"provider": "aethertrip", "status": "not_started", "days_count": 0, "items_count": 0},
    }


def _has_unresolved_critical(validation_reports: Any) -> bool:
    for report in validation_reports or []:
        report_dict = report if isinstance(report, dict) else report.model_dump()
        for issue in report_dict.get("issues", []) or []:
            issue_dict = issue if isinstance(issue, dict) else issue.model_dump()
            if issue_dict.get("severity") in {"critical", "error"}:
                return True
    return False


def _overall_score(feasibility_score: Any) -> Optional[int]:
    if not feasibility_score:
        return None
    score_dict = feasibility_score if isinstance(feasibility_score, dict) else feasibility_score.model_dump()
    raw_score = score_dict.get("overall_score")
    return int(raw_score) if raw_score is not None else None


def _build_trip_response(user_input: str, final_state: TripState, start_time: float) -> TripResponse:
    service_status = {**_default_service_status(), **(final_state.service_status or {})}
    warnings = _clean_message_list(final_state.warnings)
    errors = _clean_message_list(final_state.errors)
    trip_id = final_state.trip_id or f"trip_{uuid.uuid4().hex[:12]}"
    if isinstance(final_state.itinerary, dict):
        itinerary_days = final_state.itinerary.get("days", []) or []
    elif final_state.itinerary and getattr(final_state.itinerary, "days", None) is not None:
        itinerary_days = [day.model_dump() if hasattr(day, "model_dump") else day for day in final_state.itinerary.days]
    else:
        itinerary_days = []
    itinerary_item_count = sum(len(day.get("items", []) or []) for day in itinerary_days)
    score = _overall_score(final_state.feasibility_score)
    has_critical = _has_unresolved_critical(final_state.validation_reports)
    if not itinerary_item_count:
        status = "failed"
    elif has_critical or score is None or score < 70:
        status = "needs_review"
    else:
        status = "completed"
    response = TripResponse(
        trip_id=trip_id,
        user_input=user_input,
        parsed_request=final_state.parsed_request,
        constraints=final_state.constraints,
        itinerary=final_state.itinerary,
        budget_report=final_state.budget_report,
        validation_reports=final_state.validation_reports or [],
        repair_history=final_state.repair_history or [],
        feasibility_score=final_state.feasibility_score,
        place_candidates=final_state.place_candidates or [],
        service_status=service_status,
        data_sources=service_status,
        why_this_trip_works=final_state.why_this_trip_works or final_state.final_explanation,
        status=status,
        warnings=warnings,
        errors=errors,
        created_at=datetime.utcnow().isoformat() + "Z",
        completed_at=datetime.utcnow().isoformat() + "Z",
        processing_time_seconds=time.time() - start_time,
    )
    trip_store[response.trip_id] = response.model_dump()
    _log_trip_response_debug(response)
    return response


def _coerce_trip_state(raw_state: Any, user_input: str) -> TripState:
    if isinstance(raw_state, TripState):
        return raw_state

    state_data = dict(raw_state or {})
    state_data.setdefault("user_input", user_input)
    return TripState(**state_data)


def _count_itinerary_items(response: TripResponse) -> int:
    return sum(len(day.items or []) for day in (response.itinerary.days if response.itinerary else []))


def _log_trip_response_debug(response: TripResponse) -> None:
    hard = response.constraints.hard if response.constraints else None
    budget = response.budget_report.model_dump() if response.budget_report else {}
    logger.info(
        "Trip response debug trip_id=%s destination=%s origin=%s duration_days=%s travelers=%s budget=%s diet=%s transport_mode=%s place_candidates=%s itinerary_days=%s itinerary_items=%s budget_report=%s validation_reports=%s errors=%s",
        response.trip_id,
        hard.destination if hard else None,
        hard.origin if hard else None,
        hard.duration_days if hard else None,
        hard.travelers if hard else None,
        hard.budget_per_person if hard else None,
        hard.diet if hard else [],
        hard.transport_mode if hard else None,
        len(response.place_candidates or []),
        len(response.itinerary.days or []) if response.itinerary else 0,
        _count_itinerary_items(response),
        budget,
        len(response.validation_reports or []),
        response.errors or [],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared backend resources during app lifespan."""
    global graph
    if graph is None:
        graph = AetherTripGraph()
        logger.info("AetherTripGraph initialized")
    yield


# Initialize FastAPI
app = FastAPI(
    title="AetherTrip API",
    description="AI-powered trip planner with accuracy-first approach",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AetherTrip API"}


@app.post("/api/trips/plan", response_model=TripResponse)
async def plan_trip(request: TripRequest) -> TripResponse:
    """
    Plan a trip based on user input.
    
    Args:
        request: TripRequest with user_input
        
    Returns:
        TripResponse with complete trip plan
    """
    if not graph:
        raise HTTPException(status_code=500, detail="Graph not initialized")
    
    start_time = time.time()
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    logger.info("Planning trip trip_id=%s user_input=%s", trip_id, request.user_input)
    
    try:
        # Initialize state
        initial_state = TripState(trip_id=trip_id, user_input=request.user_input)
        
        # Compile and invoke graph
        compiled_graph = graph.compile()
        final_state = compiled_graph.invoke(initial_state)
        
        response = _build_trip_response(
            request.user_input,
            _coerce_trip_state(final_state, request.user_input),
            start_time,
        )
        
        logger.info(f"Trip planned in {response.processing_time_seconds:.2f}s")
        
        return response
    
    except Exception as e:
        logger.error(f"Trip planning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Trip planning failed. Please try again with a clearer request.")


@app.post("/api/trips/plan/stream")
async def plan_trip_stream(request: TripRequest):
    """Plan a trip and stream real pipeline stage events as graph nodes execute."""
    if not graph:
        raise HTTPException(status_code=500, detail="Graph not initialized")

    def event_stream():
        start_time = time.time()
        trip_id = f"trip_{uuid.uuid4().hex[:12]}"
        logger.info("Planning trip stream trip_id=%s user_input=%s", trip_id, request.user_input)
        state = TripState(trip_id=trip_id, user_input=request.user_input)

        def run_update(stage: str, fn: Callable[[TripState], Dict[str, Any]], running_message: Optional[str] = None):
            nonlocal state
            yield _as_sse(_pipeline_event(stage, "running", message=running_message))
            update = fn(state)
            state = _merge_state_update(state, update or {})
            yield _as_sse(_pipeline_event(stage, "completed"))

        try:
            for output in run_update("understanding_request", graph._node_input_analyzer):
                yield output
            for output in run_update("extracting_constraints", graph._node_constraint_extractor):
                yield output
            hard = state.constraints.get("hard", {}) if state.constraints else {}
            if not hard.get("destination"):
                yield _as_sse(_pipeline_event(
                    "failed",
                    "failed",
                    message="Grounding failed: no destination extracted",
                    details={"error": _failure_message_from_state(state)},
                ))
                return

            for grounding_stage in [
                "geocoding_destination",
                "fetching_places_geoapify",
                "fetching_weather_open_meteo",
                "building_route_matrix_openrouteservice",
            ]:
                yield _as_sse(_pipeline_event(grounding_stage, "running"))
            grounding_update = graph._node_grounding_data_fetcher(state)
            state = _merge_state_update(state, grounding_update or {})
            for grounding_stage in [
                "geocoding_destination",
                "fetching_places_geoapify",
                "fetching_weather_open_meteo",
                "building_route_matrix_openrouteservice",
            ]:
                yield _as_sse(_pipeline_event(grounding_stage, "completed"))

            for output in run_update("building_candidate_itinerary", graph._node_candidate_itinerary_builder):
                yield output

            for validation_stage in [
                "validating_opening_hours",
                "validating_travel_time",
                "validating_budget",
                "validating_weather",
            ]:
                yield _as_sse(_pipeline_event(validation_stage, "running"))
            validation_update = graph._node_validate_itinerary(state)
            state = _merge_state_update(state, validation_update or {})
            for validation_stage in [
                "validating_opening_hours",
                "validating_travel_time",
                "validating_budget",
                "validating_weather",
            ]:
                yield _as_sse(_pipeline_event(validation_stage, "completed"))

            repair_decision = graph._should_repair(state)
            if repair_decision == "repair":
                while repair_decision == "repair":
                    for output in run_update("auto_repair_if_needed", graph._node_auto_repair):
                        yield output
                    validation_update = graph._node_validate_itinerary(state)
                    state = _merge_state_update(state, validation_update or {})
                    repair_decision = graph._should_repair(state)
            else:
                yield _as_sse(_pipeline_event("auto_repair_if_needed", "completed", message="No repair needed."))

            for output in run_update("scoring_feasibility", graph._node_feasibility_scorer):
                yield output
            for output in run_update("explanation_agent", graph._node_explanation_agent):
                yield output

            response = _build_trip_response(request.user_input, state, start_time)
            yield _as_sse(_pipeline_event("completed", "completed", trip=response))

        except Exception as e:
            logger.error(f"Streaming trip planning failed: {e}", exc_info=True)
            failed_event = _pipeline_event(
                "failed",
                "failed",
                message=_failure_message_from_state(state, e),
                details={"error": _clean_error_message(e)},
            )
            yield _as_sse(failed_event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str) -> TripResponse:
    """Retrieve a previously planned trip by ID."""
    stored_trip = trip_store.get(trip_id)
    if not stored_trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return TripResponse(**stored_trip)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AetherTrip",
        "version": "2.0.0",
        "description": "AI-powered trip planner",
        "endpoints": {
            "health": "/api/health",
            "plan_trip": "POST /api/trips/plan"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
