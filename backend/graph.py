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
from backend.schemas.places import PlaceCandidate
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
from backend.services.knowledge_service import KnowledgeService
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
        self.knowledge_service = KnowledgeService(self.cache_service)
        
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
        logger.info("ENTER input_analyzer trip_id=%s user_input=%s", state.trip_id or "unknown", state.user_input)
        result = self.input_analyzer.run(state)
        parsed = result.get("parsed_request", {}) if isinstance(result, dict) else {}
        logger.info(
            "EXIT input_analyzer trip_id=%s destination=%s origin=%s",
            state.trip_id or "unknown",
            parsed.get("destination") if isinstance(parsed, dict) else None,
            parsed.get("origin") if isinstance(parsed, dict) else None,
        )
        return result
    
    def _node_constraint_extractor(self, state: TripState) -> Dict[str, Any]:
        """Extract structured constraints."""
        logger.info("ENTER constraint_extractor trip_id=%s", state.trip_id or "unknown")
        result = self.constraint_extractor.run(state)
        constraints = result.get("constraints", {}) if isinstance(result, dict) else {}
        hard = constraints.get("hard", {}) if isinstance(constraints, dict) else {}
        logger.info(
            "EXIT constraint_extractor trip_id=%s origin=%s destination=%s duration_days=%s travelers=%s budget=%s diet=%s transport_mode=%s errors=%s",
            state.trip_id or "unknown",
            hard.get("origin"),
            hard.get("destination"),
            hard.get("duration_days"),
            hard.get("travelers"),
            hard.get("budget_per_person"),
            hard.get("diet"),
            hard.get("transport_mode"),
            result.get("errors", []) if isinstance(result, dict) else [],
        )
        return result
    
    def _node_grounding_data_fetcher(self, state: TripState) -> Dict[str, Any]:
        """Fetch grounding data: places, weather, routes."""
        logger.info("ENTER grounding_data_fetcher trip_id=%s", state.trip_id or "unknown")
        
        if not state.constraints:
            logger.info("EXIT grounding_data_fetcher trip_id=%s errors=1 reason=no_constraints", state.trip_id or "unknown")
            return {"errors": ["No constraints available"]}
        
        constraints = state.constraints
        hard = constraints.get("hard", {})
        soft = constraints.get("soft", {})
        destination = hard.get("destination", "Unknown")
        if not destination or destination in {"Unknown", "Your Trip", "Trip destination"}:
            logger.info("EXIT grounding_data_fetcher trip_id=%s candidates_count=0 reason=missing_destination", state.trip_id or "unknown")
            return {
                "service_status": {
                    "geocoding": {"provider": "geoapify", "status": "skipped", "used_fallback": False, "coordinates_found": False, "reason": "missing_destination"},
                    "places": {"provider": "geoapify", "status": "skipped", "count": 0, "used_fallback": False, "reason": "missing_destination"},
                    "weather": {"provider": "open_meteo", "status": "skipped", "used_fallback": False, "reason": "missing_destination"},
                    "routing": {"provider": "openrouteservice", "status": "skipped", "used_fallback": False, "count": 0, "reason": "missing_destination"},
                },
                "errors": ["Grounding failed: no destination extracted"],
            }
        logger.info(
            "Grounding selected destination trip_id=%s destination=%s origin=%s duration_days=%s travelers=%s budget=%s diet=%s transport_mode=%s",
            state.trip_id or "unknown",
            destination,
            hard.get("origin"),
            hard.get("duration_days"),
            hard.get("travelers"),
            hard.get("budget_per_person"),
            hard.get("diet"),
            hard.get("transport_mode"),
        )
        interests = list(soft.get("interests", []) or hard.get("interests", []) or [])
        interests.extend(["attraction", "museum", "park", "viewpoint", "landmark"])
        if hard.get("diet"):
            interests = [*interests, "food", "restaurant"]
        interests = list(dict.fromkeys(interest for interest in interests if interest))
        
        try:
            warnings = []
            destination_coordinates = None
            self.places_service.last_geocoding_status = {
                "provider": "geoapify",
                "status": "not_started",
                "used_fallback": False,
                "coordinates_found": False,
            }
            self.places_service.last_places_status = {
                "provider": "geoapify",
                "status": "not_started",
                "count": 0,
                "used_fallback": False,
            }
            self.weather_service.last_status = {
                "provider": "open_meteo",
                "status": "not_started",
                "used_fallback": False,
            }
            self.routing_service.last_matrix_status = {
                "provider": "openrouteservice",
                "status": "not_started",
                "used_fallback": False,
                "count": 0,
            }

            # 1. Geocode destination using Geoapify.
            dest_coords = None
            if destination and destination != "Unknown":
                dest_coords = self.places_service.geocode_destination(destination)
                if dest_coords:
                    destination_coordinates = {
                        "latitude": float(dest_coords[0]),
                        "longitude": float(dest_coords[1]),
                    }
                    logger.info(
                        "Grounding geocoding debug trip_id=%s status=%s coordinates=%s",
                        state.trip_id or "unknown",
                        self.places_service.last_geocoding_status,
                        destination_coordinates,
                    )
                else:
                    warnings.append(f"Geoapify geocoding failed for destination: {destination}")

            # 2. Fetch place candidates from Geoapify.
            logger.info("Fetching places for %s", destination)
            place_candidates = self.places_service.get_place_candidates(
                destination or "Unknown",
                interests,
                constraints
            )
            logger.info(f"Found {len(place_candidates)} place candidates")
            logger.info(
                "Grounding places debug trip_id=%s geoapify_places_count=%s candidates_passed_to_builder=%s status=%s",
                state.trip_id or "unknown",
                self.places_service.last_places_status.get("count", len(place_candidates)),
                len(place_candidates),
                self.places_service.last_places_status,
            )
            if self.places_service.last_places_status.get("used_fallback"):
                warnings.append(self.places_service.last_places_status.get(
                    "warning",
                    "Geoapify returned no usable places; low-confidence fallback data was used.",
                ))
            elif not place_candidates:
                warnings.append(self.places_service.last_places_status.get(
                    "warning",
                    "Geoapify returned no usable places.",
                ))
            
            # 3. Fetch weather data for destination
            weather_data = {}
            if dest_coords:
                logger.info("Fetching weather for %s", dest_coords)
                weather_forecast = self.weather_service.get_forecast(
                    dest_coords[0],
                    dest_coords[1],
                    days=14
                )
                weather_data = {
                    "destination": destination,
                    "coordinates": dest_coords,
                    "forecast": weather_forecast,
                }
            else:
                self.weather_service.last_status = {
                    "provider": "open_meteo",
                    "status": "skipped",
                    "used_fallback": False,
                    "reason": "missing_destination_coordinates",
                }
            
            # 4. Fetch route matrix if we have multiple locations
            route_matrix = {}
            if len(place_candidates) >= 2:
                logger.info(f"Building route matrix for {len(place_candidates)} places")
                matrix_places = place_candidates[:10]
                locations = [(p.longitude, p.latitude) for p in matrix_places]  # ORS expects lon, lat
                
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
                    durations = matrix_data.get("durations") or []
                    distances = matrix_data.get("distances") or []
                    if isinstance(durations, list):
                        route_matrix = {
                            matrix_places[i].id: {
                                matrix_places[j].id: int((durations[i][j] or 0) / 60)
                                for j in range(len(matrix_places))
                                if (
                                    i < len(durations)
                                    and isinstance(durations[i], list)
                                    and j < len(durations[i])
                                    and i != j
                                )
                            }
                            for i in range(len(matrix_places))
                        }
                    elif isinstance(durations, dict):
                        route_matrix = durations
                    else:
                        route_matrix = {}
                    route_matrix = {
                        **route_matrix,
                        "_meta": {
                            "locations": locations,
                            "place_ids": [p.id for p in matrix_places],
                            "distances": distances,
                            "durations": durations,
                        },
                        "profile": profile,
                    }
                    logger.info(f"Route matrix built: {len(locations)} locations")
                    logger.info(
                        "Route matrix debug trip_id=%s locations=%s status=%s",
                        state.trip_id or "unknown",
                        len(locations),
                        self.routing_service.last_matrix_status,
                    )
                except Exception as e:
                    logger.warning(f"Route matrix failed: {e}")
            else:
                self.routing_service.last_matrix_status = {
                    "provider": "openrouteservice",
                    "status": "skipped",
                    "used_fallback": False,
                    "count": len(place_candidates),
                    "reason": "not_enough_place_candidates",
                }

            service_status = {
                "geocoding": self.places_service.last_geocoding_status,
                "places": self.places_service.last_places_status,
                "weather": self.weather_service.last_status,
                "routing": self.routing_service.last_matrix_status,
                "knowledge": {
                    "provider": "wikidata_wikipedia",
                    "status": "skipped",
                    "used_fallback": False,
                },
            }
            
            item_count = len(place_candidates)
            logger.info(
                "EXIT grounding_data_fetcher trip_id=%s candidates_count=%s geocoding_status=%s places_count=%s weather_status=%s routing_status=%s warnings=%s",
                state.trip_id or "unknown",
                item_count,
                self.places_service.last_geocoding_status.get("status"),
                item_count,
                self.weather_service.last_status.get("status"),
                self.routing_service.last_matrix_status.get("status"),
                len(warnings),
            )
            return {
                "destination_coordinates": destination_coordinates,
                "place_candidates": [p.model_dump() for p in place_candidates],
                "weather_data": weather_data,
                "route_matrix": route_matrix,
                "service_status": service_status,
                "warnings": warnings,
            }
        
        except Exception as e:
            logger.error(f"Data fetcher failed: {e}", exc_info=True)
            return {"errors": ["Data fetching failed. Please check provider configuration and try again."]}
    
    def _node_candidate_itinerary_builder(self, state: TripState) -> Dict[str, Any]:
        """Build candidate itinerary."""
        logger.info(
            "ENTER candidate_itinerary_builder trip_id=%s place_candidates=%s",
            state.trip_id or "unknown",
            len(state.place_candidates or []),
        )
        result = self.itinerary_builder.run(state)
        itinerary = result.get("itinerary", {}) if isinstance(result, dict) else {}
        days = itinerary.get("days", []) if isinstance(itinerary, dict) else []
        item_count = sum(len(day.get("items", []) or []) for day in days)
        logger.info(
            "EXIT candidate_itinerary_builder trip_id=%s days=%s items=%s generation_method=%s warnings=%s errors=%s",
            state.trip_id or "unknown",
            len(days),
            item_count,
            itinerary.get("generation_method") if isinstance(itinerary, dict) else None,
            itinerary.get("warnings") if isinstance(itinerary, dict) else None,
            result.get("errors", []) if isinstance(result, dict) else [],
        )
        return result
    
    def _node_validate_itinerary(self, state: TripState) -> Dict[str, Any]:
        """Run all validators on itinerary."""
        logger.info("ENTER validate_itinerary trip_id=%s", state.trip_id or "unknown")
        
        if not state.itinerary:
            logger.info("EXIT validate_itinerary trip_id=%s errors=1 reason=no_itinerary", state.trip_id or "unknown")
            return {"validation_reports": [], "errors": ["No itinerary to validate"]}
        
        itinerary = state.itinerary if isinstance(state.itinerary, Itinerary) else Itinerary(**state.itinerary)
        if not itinerary.days:
            logger.info("EXIT validate_itinerary trip_id=%s errors=1 reason=no_itinerary_days", state.trip_id or "unknown")
            return {"validation_reports": [], "errors": ["No itinerary days to validate"]}
        validation_reports = []
        places_map = {
            p.get("id", ""): PlaceCandidate(**p) if isinstance(p, dict) else p
            for p in state.place_candidates
        } if state.place_candidates else {}
        
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
                logger.info(
                    "Budget report debug trip_id=%s budget_report=%s",
                    state.trip_id or "unknown",
                    budget_report.model_dump(),
                )
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
            logger.info(
                "EXIT validate_itinerary trip_id=%s validation_reports=%s errors=%s",
                state.trip_id or "unknown",
                len(validation_reports),
                state.errors or [],
            )
            return return_val
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            logger.info(
                "EXIT validate_itinerary trip_id=%s validation_reports=%s errors=1",
                state.trip_id or "unknown",
                len(validation_reports),
            )
            return {"errors": ["Validation failed. The trip response could not be fully checked."], "validation_reports": validation_reports}
    
    def _should_repair(self, state: TripState) -> Literal["repair", "score"]:
        """
        Conditional edge: decide whether to repair or proceed to scoring.
        
        Returns:
            "repair" if critical issues remain and attempts < max
            "score" otherwise
        """
        critical_issues = []
        for report in state.validation_reports or []:
            report_dict = report if isinstance(report, dict) else report.model_dump()
            for issue in report_dict.get("issues", []) or []:
                issue_dict = issue if isinstance(issue, dict) else issue.model_dump()
                if issue_dict.get("severity") in ["critical", "error"]:
                    critical_issues.append(issue_dict)

        if critical_issues and state.repair_attempts < config.MAX_REPAIR_ATTEMPTS:
            logger.info(
                "should_repair: YES (attempt %s/%s critical_issues=%s)",
                state.repair_attempts + 1,
                config.MAX_REPAIR_ATTEMPTS,
                len(critical_issues),
            )
            return "repair"
        
        logger.info("should_repair: NO, proceeding to scoring")
        return "score"
    
    def _node_auto_repair(self, state: TripState) -> Dict[str, Any]:
        """Auto-repair failed validations."""
        logger.info("ENTER auto_repair trip_id=%s attempts=%s", state.trip_id or "unknown", state.repair_attempts)
        result = self.repair_agent.run(state)
        logger.info(
            "EXIT auto_repair trip_id=%s repair_attempts=%s errors=%s",
            state.trip_id or "unknown",
            result.get("repair_attempts") if isinstance(result, dict) else None,
            result.get("errors", []) if isinstance(result, dict) else [],
        )
        return result
    
    def _node_feasibility_scorer(self, state: TripState) -> Dict[str, Any]:
        """Score feasibility."""
        logger.info("ENTER feasibility_scorer trip_id=%s", state.trip_id or "unknown")
        
        try:
            # Get validators for scoring
            places_map = {
                p.get("id", ""): PlaceCandidate(**p) if isinstance(p, dict) else p
                for p in state.place_candidates
            } if state.place_candidates else {}
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
            
            logger.info("EXIT feasibility_scorer trip_id=%s score=%s grade=%s", state.trip_id or "unknown", score.overall_score, score.grade)
            
            return {"feasibility_score": score.model_dump()}
        
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            logger.info("EXIT feasibility_scorer trip_id=%s errors=1", state.trip_id or "unknown")
            return {"errors": [f"Scoring failed: {e}"]}
    
    def _node_explanation_agent(self, state: TripState) -> Dict[str, Any]:
        """Generate final explanation."""
        logger.info("ENTER explanation_agent trip_id=%s", state.trip_id or "unknown")
        result = self.explanation_agent.run(state)
        explanation = result.get("final_explanation") if isinstance(result, dict) else None
        logger.info(
            "EXIT explanation_agent trip_id=%s explanation_chars=%s",
            state.trip_id or "unknown",
            len(explanation or ""),
        )
        return result
