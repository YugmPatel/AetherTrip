"""
AetherTrip FastAPI backend: accuracy-first travel planner.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.state import TripState
from backend.graph import AetherTripGraph
from backend.schemas import TripRequest, TripResponse
from backend.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
config = get_config()

graph = None
trip_store = {}


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
    
    logger.info(f"Planning trip: {request.user_input[:50]}...")
    start_time = time.time()
    
    try:
        # Initialize state
        initial_state = TripState(user_input=request.user_input)
        
        # Compile and invoke graph
        compiled_graph = graph.compile()
        final_state = compiled_graph.invoke(initial_state)
        
        # Build response
        processing_time = time.time() - start_time
        
        response = TripResponse(
            trip_id=f"trip_{int(time.time())}",
            user_input=request.user_input,
            parsed_request=final_state.get("parsed_request"),
            constraints=final_state.get("constraints"),
            itinerary=final_state.get("itinerary"),
            budget_report=final_state.get("budget_report"),
            validation_reports=final_state.get("validation_reports", []),
            repair_history=final_state.get("repair_history", []),
            feasibility_score=final_state.get("feasibility_score"),
            why_this_trip_works=final_state.get("final_explanation"),
            status="completed" if final_state.get("feasibility_score") else "completed_with_issues",
            warnings=final_state.get("errors", []),
            errors=final_state.get("errors", []),
            created_at=datetime.utcnow().isoformat() + "Z",
            completed_at=datetime.utcnow().isoformat() + "Z",
            processing_time_seconds=processing_time,
        )

        trip_store[response.trip_id] = response.model_dump()
        
        logger.info(f"Trip planned in {processing_time:.2f}s")
        
        return response
    
    except Exception as e:
        logger.error(f"Trip planning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trip planning failed: {str(e)}")


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
