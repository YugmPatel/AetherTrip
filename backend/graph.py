"""
LangGraph workflow: multi-stage trip planning with validation and auto-repair.
"""

import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END

from backend.state import TripState
from backend.schemas.itinerary import Itinerary
from backend.schemas.constraints import HardConstraints
from backend.schemas.budget import BudgetBreakdown
from backend.agents import (
    InputAnalyzerAgent,
    ConstraintExtractorAgent,
    ItineraryBuilderAgent,
    RepairAgent,
    ExplanationAgent,
)
from backend.validators import (
    OpeningHoursValidator,
    RouteTimeValidator,
    BudgetValidator,
    ConstraintValidator,
    VerificationValidator,
    WeatherValidator,
)
from backend.scoring import FeasibilityScorer
from backend.services import CacheService, PlacesService
from backend.services.weather_service import WeatherService
from backend.services.routing_service import RoutingService
from backend.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class AetherTripGraph:
    """LangGraph workflow for accuracy-first trip planning."""
    
    def __init__(self):
        """Initialize agents and services."""
        self.workflow = StateGraph(TripState)
        
        # Initialize agents
        self.input_analyzer = InputAnalyzerAgent()
        self.constraint_extractor = ConstraintExtractorAgent()
        self.itinerary_builder = ItineraryBuilderAgent()
        self.repair_agent = RepairAgent()
        self.explanation_agent = ExplanationAgent()
        
        # Initialize services
        self.cache_service = CacheService()
        self.places_service = PlacesService(self.cache_service)
        self.weather_service = WeatherService(self.cache_service)
        self.routing_service = RoutingService(self.cache_service)
        
        self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow."""
        
        # Add nodes
        self.workflow.add_node("input_analyzer", self._node_input_analyzer)
        self.workflow.add_node("constraint_extractor", self._node_constraint_extractor)
        self.workflow.add_node("grounding_data_fetcher", self._node_grounding_data_fetcher)
        self.workflow.add_node("candidate_itinerary_builder", self._node_candidate_itinerary_builder)
        self.workflow.add_node("validate_itinerary", self._node_validate_itinerary)
        self.workflow.add_node("auto_repair", self._node_auto_repair)
        self.workflow.add_node("feasibility_scorer", self._node_feasibility_scorer)
        self.workflow.add_node("explanation_agent", self._node_explanation_agent)
        
        # Set entry point
        self.workflow.set_entry_point("input_analyzer")
        
        # Add edges (linear path until validation)
        self.workflow.add_edge("input_analyzer", "constraint_extractor")
        self.workflow.add_edge("constraint_extractor", "grounding_data_fetcher")
        self.workflow.add_edge("grounding_data_fetcher", "candidate_itinerary_builder")
        self.workflow.add_edge("candidate_itinerary_builder", "validate_itinerary")
        
        # Conditional edge after validation (repair loop)
        self.workflow.add_conditional_edges(
            "validate_itinerary",
            self._should_repair,
            {
                "repair": "auto_repair",
                "score": "feasibility_scorer",
            }
        )
        
        # Repair loop: validate again after repair
        self.workflow.add_edge("auto_repair", "validate_itinerary")
        
        # Final path
        self.workflow.add_edge("feasibility_scorer", "explanation_agent")
        self.workflow.add_edge("explanation_agent", END)
    
    def compile(self):
        """Compile and return the LangGraph."""
        return self.workflow.compile()
    
    # ========== Node Functions ==========
    
    def _node_input_analyzer(self, state: TripState) -> Dict[str, Any]:
        """Parse raw user input."""
        logger.info("→ input_analyzer")
        result = self.input_analyzer.run(state)
        return result
    
    def _node_constraint_extractor(self, state: TripState) -> Dict[str, Any]:
        """Extract structured constraints."""
        logger.info("→ constraint_extractor")
        result = self.constraint_extractor.run(state)
        return result
    
    def _node_grounding_data_fetcher(self, state: TripState) -> Dict[str, Any]:
        """Fetch grounding data: places, weather, routes."""
        logger.info("→ grounding_data_fetcher")
        
        if not state.constraints:
            return {"errors": ["No constraints available"]}
        
        constraints = state.constraints
        hard = constraints.get("hard", {})
        destination = hard.get("destination", "Unknown")
        destinations = hard.get("destinations", [destination]) if not isinstance(hard.get("destinations"), list) else hard.get("destinations", [])
        interests = hard.get("interests", [])
        start_date = hard.get("start_date", "")
        end_date = hard.get("end_date", "")
        
        try:
            # 1. Fetch place candidates from Geoapify
            logger.info(f"Fetching places for {destination}")
            place_candidates = self.places_service.get_place_candidates(
                destination or "Unknown",
                interests,
                constraints
            )
            logger.info(f"Found {len(place_candidates)} place candidates")
            
            # 2. Fetch weather data for destination
            weather_data = {}
            if destinations and destinations[0]:
                dest_coords = self.places_service.geocode_destination(destinations[0])
                if dest_coords:
                    logger.info(f"Fetching weather for {dest_coords}")
                    weather_forecast = self.weather_service.get_forecast(
                        dest_coords[0],
                        dest_coords[1],
                        days=14
                    )
                    weather_data = {
                        "destination": destinations[0],
                        "coordinates": dest_coords,
                        "forecast": weather_forecast,
                    }
            
            # 3. Fetch route matrix if we have multiple locations
            route_matrix = {}
            if len(place_candidates) >= 2:
                logger.info(f"Building route matrix for {len(place_candidates)} places")
                locations = [(p.longitude, p.latitude) for p in place_candidates[:10]]  # Limit to 10 for API
                
                transport_mode = hard.get("transport_mode", "driving-car")
                profile_map = {
                    "car": "driving-car",
                    "public_transit": "driving-car",  # Use driving for now
                    "walking": "foot-walking",
                    "mixed": "driving-car",
                    "no_car": "foot-walking",
                }
                profile = profile_map.get(transport_mode, "driving-car")
                
                try:
                    matrix_data = self.routing_service.get_route_matrix(locations, profile=profile)
                    route_matrix = {
                        "locations": locations,
                        "profile": profile,
                        "distances": matrix_data.get("distances"),  # meters
                        "durations": matrix_data.get("durations"),  # seconds
                    }
                    logger.info(f"Route matrix built: {len(locations)} locations")
                except Exception as e:
                    logger.warning(f"Route matrix failed: {e}")
            
            return {
                "place_candidates": [p.model_dump() for p in place_candidates],
                "weather_data": weather_data,
                "route_matrix": route_matrix,
            }
        
        except Exception as e:
            logger.error(f"Data fetcher failed: {e}", exc_info=True)
            return {"errors": [f"Data fetching failed: {e}"]}
    
    def _node_candidate_itinerary_builder(self, state: TripState) -> Dict[str, Any]:
        """Build candidate itinerary."""
        logger.info("→ candidate_itinerary_builder")
        result = self.itinerary_builder.run(state)
        return result
    
    def _node_validate_itinerary(self, state: TripState) -> Dict[str, Any]:
        """Run all validators on itinerary."""
        logger.info("→ validate_itinerary")
        
        if not state.itinerary:
            return {"validation_reports": [], "errors": ["No itinerary to validate"]}
        
        itinerary = state.itinerary if isinstance(state.itinerary, Itinerary) else Itinerary(**state.itinerary)
        validation_reports = []
        places_map = {p.get("id", ""): p for p in state.place_candidates} if state.place_candidates else {}
        
        try:
            # Opening hours validation
            oh_validator = OpeningHoursValidator(places_map)
            oh_report = oh_validator.validate(itinerary)
            validation_reports.append(oh_report.model_dump())
            
            # Route time validation
            rt_validator = RouteTimeValidator(state.route_matrix)
            rt_report = rt_validator.validate(itinerary)
            validation_reports.append(rt_report.model_dump())
            
            # Budget validation (if constraints available)
            if state.constraints:
                hard_constraints = state.constraints.get("hard", {}) if isinstance(state.constraints, dict) else {}
                hard_constraints_model = hard_constraints if isinstance(hard_constraints, HardConstraints) else HardConstraints(**hard_constraints)
                budget_validator = BudgetValidator()
                budget_report, budget_validation = budget_validator.validate(
                    itinerary,
                    hard_constraints_model,
                    len(itinerary.days)
                )
                validation_reports.append(budget_validation.model_dump())
                return_val = {"budget_report": budget_report.model_dump()}
            else:
                return_val = {}
            
            # Verification validator
            if places_map:
                verify_validator = VerificationValidator(places_map)
                verify_report = verify_validator.validate(itinerary)
                validation_reports.append(verify_report.model_dump())
            
            # Weather validator
            weather_validator = WeatherValidator(places_map, state.weather_data)
            weather_report = weather_validator.validate(itinerary)
            validation_reports.append(weather_report.model_dump())
            
            return_val["validation_reports"] = validation_reports
            return return_val
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"errors": [f"Validation error: {e}"], "validation_reports": validation_reports}
    
    def _should_repair(self, state: TripState) -> Literal["repair", "score"]:
        """
        Conditional edge: decide whether to repair or proceed to scoring.
        
        Returns:
            "repair" if critical issues remain and attempts < max
            "score" otherwise
        """
        latest_report = state.validation_reports[-1] if state.validation_reports else None
        
        if latest_report:
            passed = latest_report.get("passed", True)
            critical_issues = len([i for i in latest_report.get("issues", []) if i.get("severity") in ["critical", "error"]])
            
            if not passed and critical_issues > 0 and state.repair_attempts < config.MAX_REPAIR_ATTEMPTS:
                logger.info(f"→ should_repair: YES (attempt {state.repair_attempts + 1}/{config.MAX_REPAIR_ATTEMPTS})")
                return "repair"
        
        logger.info("→ should_repair: NO, proceeding to scoring")
        return "score"
    
    def _node_auto_repair(self, state: TripState) -> Dict[str, Any]:
        """Auto-repair failed validations."""
        logger.info("→ auto_repair")
        result = self.repair_agent.run(state)
        return result
    
    def _node_feasibility_scorer(self, state: TripState) -> Dict[str, Any]:
        """Score feasibility."""
        logger.info("→ feasibility_scorer")
        
        try:
            # Get validators for scoring
            places_map = {p.get("id", ""): p for p in state.place_candidates} if state.place_candidates else {}
            verify_validator = VerificationValidator(places_map)
            itinerary = state.itinerary if isinstance(state.itinerary, Itinerary) else Itinerary(**state.itinerary)
            budget_report = (
                state.budget_report
                if isinstance(state.budget_report, BudgetBreakdown)
                else BudgetBreakdown(**state.budget_report)
            ) if state.budget_report else BudgetBreakdown(
                currency="USD",
                travelers=1,
                lodging_base=0,
                intercity_transport=0,
                local_transport=0,
                food=0,
                attraction_tickets=0,
                lodging_taxes=0,
                lodging_fees=0,
                booking_fees=0,
                baggage_fees=0,
                seat_selection=0,
                parking=0,
                tolls=0,
                tips=0,
                currency_fees=0,
                emergency_buffer=0,
                total_base_cost=0,
                total_hidden_costs=0,
                total_per_person=0,
                total_for_group=0,
                user_budget_per_person=None,
                is_over_budget=False,
                budget_remaining_per_person=None,
            )
            
            scorer = FeasibilityScorer(verify_validator)
            score = scorer.score(
                itinerary,
                state.validation_reports or [],
                budget_report,
                state.repair_attempts
            )
            
            logger.info(f"Feasibility score: {score.overall_score}/100 (Grade {score.grade})")
            
            return {"feasibility_score": score.model_dump()}
        
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return {"errors": [f"Scoring failed: {e}"]}
    
    def _node_explanation_agent(self, state: TripState) -> Dict[str, Any]:
        """Generate final explanation."""
        logger.info("→ explanation_agent")
        result = self.explanation_agent.run(state)
        return result
