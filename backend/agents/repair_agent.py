"""RepairAgent: deterministic repairs for validation failures."""

import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional

from backend.state import TripState
from backend.schemas.itinerary import Itinerary
from backend.schemas.places import PlaceCandidate
from backend.validators.route_time_validator import RouteTimeValidator

logger = logging.getLogger(__name__)


class RepairAgent:
    """Applies bounded, auditable repairs for failed validation checks."""

    def run(self, state: TripState) -> Dict[str, Any]:
        logger.info("RepairAgent: analyzing %s validation reports", len(state.validation_reports))

        if not state.validation_reports or state.repair_attempts >= 3:
            logger.info("No repairs needed or max attempts reached")
            return {"repair_history": []}

        itinerary = deepcopy(state.itinerary or {})
        repairs: List[Dict[str, Any]] = []
        warnings: List[str] = []

        route_issues = self._issues_by_type(state.validation_reports, "travel_time")
        if route_issues and itinerary.get("days"):
            before = self._summarize_itinerary(itinerary)
            itinerary, route_repairs = self._repair_route_time(itinerary, state.route_matrix or {}, state.place_candidates or [])
            after = self._summarize_itinerary(itinerary)
            repairs.extend(route_repairs)
            if before != after and route_repairs:
                repairs[-1]["before"] = before
                repairs[-1]["after"] = after

        budget_issues = self._issues_by_type(state.validation_reports, "budget") + self._issues_by_type(state.validation_reports, "over_budget")
        if budget_issues or self._budget_far_over(state.budget_report):
            repair = self._budget_repair_note(state.budget_report)
            repairs.append(repair)
            if repair.get("infeasible"):
                warnings.append("Trip is not feasible within the requested budget.")

        if not repairs and self._has_failed_validation(state.validation_reports):
            repairs.append({
                "type": "validation_repair_assessment",
                "changed": False,
                "why": "Validation reported an issue that has no deterministic repair path yet.",
                "before": self._summarize_itinerary(itinerary),
                "after": self._summarize_itinerary(itinerary),
            })

        if repairs:
            state.repair_attempts += 1
            logger.info("Applied/recorded %s repair actions (attempt %s)", len(repairs), state.repair_attempts)

        return {
            "repair_history": repairs,
            "repair_attempts": state.repair_attempts,
            "itinerary": itinerary,
            "warnings": warnings,
        }

    def _issues_by_type(self, reports: List[Dict[str, Any]], needle: str) -> List[Dict[str, Any]]:
        issues = []
        for report in reports or []:
            report_dict = report if isinstance(report, dict) else report.model_dump()
            for issue in report_dict.get("issues", []) or []:
                issue_dict = issue if isinstance(issue, dict) else issue.model_dump()
                if needle in str(issue_dict.get("type", "")) or needle in str(issue_dict.get("message", "")).lower():
                    issues.append(issue_dict)
        return issues

    def _repair_route_time(
        self,
        itinerary: Dict[str, Any],
        route_matrix: Dict[str, Any],
        raw_candidates: List[Dict[str, Any]],
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        repairs: List[Dict[str, Any]] = []
        candidate_scores = {}
        for raw in raw_candidates:
            try:
                candidate = raw if isinstance(raw, PlaceCandidate) else PlaceCandidate(**raw)
                candidate_scores[candidate.id] = candidate.candidate_rank_score
            except Exception:
                continue

        for day in itinerary.get("days", []) or []:
            items = day.get("items", []) or []
            if len(items) < 2:
                continue

            original_ids = [item.get("place_id") for item in items]
            reordered = self._nearest_neighbor_order(items, route_matrix)
            day["items"] = self._assign_standard_times(reordered, day.get("day") or day.get("day_number") or 1)
            repairs.append({
                "type": "route_time_reorder",
                "changed": original_ids != [item.get("place_id") for item in day["items"]],
                "why": "Route-time validator reported an impossible transition; reordered stops by nearest available travel time.",
                "day": day.get("day") or day.get("day_number"),
            })

            while self._day_has_route_conflicts(day, route_matrix) and len(day.get("items", []) or []) > 1:
                moved = self._move_lowest_ranked_to_capacity_day(day, itinerary, candidate_scores, route_matrix)
                if moved:
                    repairs.append({
                        "type": "route_time_move_stop",
                        "changed": True,
                        "why": "Schedule remained impossible after reordering; moved a lower-ranked stop to another day with capacity.",
                        "day": day.get("day") or day.get("day_number"),
                        "target_day": moved["target_day"],
                        "moved_place_id": moved["item"].get("place_id"),
                        "moved_place_name": moved["item"].get("place_name"),
                        "before": moved["before"],
                        "after": self._summarize_itinerary(itinerary),
                    })
                    continue

                removed = self._remove_lowest_ranked_stop(day, candidate_scores)
                if not removed:
                    break
                repairs.append({
                    "type": "route_time_remove_stop",
                    "changed": True,
                    "why": "Schedule remained impossible after reordering; removed the lowest-ranked stop from the affected day.",
                    "day": day.get("day") or day.get("day_number"),
                    "removed_place_id": removed.get("place_id"),
                    "removed_place_name": removed.get("place_name"),
                    "before": {"place_ids": [item.get("place_id") for item in items]},
                    "after": {"place_ids": [item.get("place_id") for item in day.get("items", []) or []]},
                })
                day["items"] = self._assign_standard_times(day.get("items", []), day.get("day") or day.get("day_number") or 1)

        return itinerary, repairs

    def _nearest_neighbor_order(self, items: List[Dict[str, Any]], route_matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        if len(items) < 3 or not route_matrix:
            return list(items)

        remaining = list(items)
        ordered = [remaining.pop(0)]
        while remaining:
            current_id = ordered[-1].get("place_id")
            next_index = min(
                range(len(remaining)),
                key=lambda idx: (route_matrix.get(current_id, {}).get(remaining[idx].get("place_id"), 9999), idx),
            )
            ordered.append(remaining.pop(next_index))
        return ordered

    def _assign_standard_times(self, items: List[Dict[str, Any]], day_number: int) -> List[Dict[str, Any]]:
        slots = [("09:00", "11:00"), ("12:00", "13:30"), ("15:00", "17:00")]
        repaired = []
        for index, item in enumerate(items[: len(slots)]):
            start_time, end_time = slots[index]
            repaired_item = {**item, "day": day_number, "start_time": start_time, "end_time": end_time}
            repaired.append(repaired_item)
        return repaired

    def _has_route_conflicts(self, itinerary: Dict[str, Any], route_matrix: Dict[str, Any]) -> bool:
        try:
            report = RouteTimeValidator(route_matrix=route_matrix).validate(Itinerary(**itinerary))
        except Exception:
            return False
        return any(issue.type == "travel_time_conflict" for issue in report.issues)

    def _day_has_route_conflicts(self, day: Dict[str, Any], route_matrix: Dict[str, Any]) -> bool:
        itinerary = {
            "destination": "Repair check",
            "days": [{
                "day": day.get("day") or day.get("day_number") or 1,
                "day_number": day.get("day") or day.get("day_number") or 1,
                "items": day.get("items", []) or [],
            }],
        }
        return self._has_route_conflicts(itinerary, route_matrix)

    def _move_lowest_ranked_to_capacity_day(
        self,
        source_day: Dict[str, Any],
        itinerary: Dict[str, Any],
        candidate_scores: Dict[str, float],
        route_matrix: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        source_items = source_day.get("items", []) or []
        if len(source_items) <= 1:
            return None

        source_day_number = source_day.get("day") or source_day.get("day_number") or 1
        source_index = min(
            range(len(source_items)),
            key=lambda idx: (candidate_scores.get(source_items[idx].get("place_id"), 0), idx),
        )
        moved_item = source_items.pop(source_index)
        before = self._summarize_itinerary(itinerary)

        for target_day in itinerary.get("days", []) or []:
            target_day_number = target_day.get("day") or target_day.get("day_number") or 1
            if target_day is source_day or target_day_number == source_day_number:
                continue
            target_items = target_day.get("items", []) or []
            if len(target_items) >= 3:
                continue

            original_target_items = deepcopy(target_items)
            target_items.append(moved_item)
            source_day["items"] = self._assign_standard_times(source_items, source_day_number)
            target_day["items"] = self._assign_standard_times(target_items, target_day_number)
            if not self._day_has_route_conflicts(source_day, route_matrix) and not self._day_has_route_conflicts(target_day, route_matrix):
                return {
                    "item": moved_item,
                    "target_day": target_day_number,
                    "before": before,
                }
            target_day["items"] = original_target_items

        source_items.insert(source_index, moved_item)
        source_day["items"] = self._assign_standard_times(source_items, source_day_number)
        return None

    def _remove_lowest_ranked_stop(self, day: Dict[str, Any], candidate_scores: Dict[str, float]) -> Optional[Dict[str, Any]]:
        items = day.get("items", []) or []
        if len(items) <= 1:
            return None
        index = min(
            range(len(items)),
            key=lambda idx: (candidate_scores.get(items[idx].get("place_id"), 0), idx),
        )
        return items.pop(index)

    def _budget_far_over(self, budget_report: Optional[Dict[str, Any]]) -> bool:
        if not budget_report:
            return False
        report = budget_report if isinstance(budget_report, dict) else budget_report.model_dump()
        budget = report.get("user_budget_per_person") or report.get("budget_limit")
        actual = report.get("total_per_person") or report.get("per_person_cost")
        return bool(budget and actual and actual > budget * 1.25)

    def _has_failed_validation(self, reports: List[Dict[str, Any]]) -> bool:
        for report in reports or []:
            report_dict = report if isinstance(report, dict) else report.model_dump()
            if report_dict.get("passed") is False:
                return True
            for issue in report_dict.get("issues", []) or []:
                issue_dict = issue if isinstance(issue, dict) else issue.model_dump()
                if issue_dict.get("severity") in ["critical", "error"]:
                    return True
        return False

    def _budget_repair_note(self, budget_report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        report = budget_report if isinstance(budget_report, dict) else budget_report.model_dump() if budget_report else {}
        budget = report.get("user_budget_per_person") or report.get("budget_limit")
        actual = report.get("total_per_person") or report.get("per_person_cost")
        over_pct = ((actual - budget) / budget) if budget and actual else None
        infeasible = bool(over_pct is not None and over_pct > 0.25)
        return {
            "type": "budget_repair_assessment",
            "changed": False,
            "why": "Budget validator reported the trip exceeds the requested budget.",
            "infeasible": infeasible,
            "before": {"budget_per_person": budget, "estimated_per_person": actual},
            "after": {"budget_per_person": budget, "estimated_per_person": actual},
            "suggestions": [
                "Reduce trip duration.",
                "Increase budget.",
                "Use cheaper lodging mode.",
                "Remove paid activities.",
            ],
        }

    def _summarize_itinerary(self, itinerary: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "days": [
                {
                    "day": day.get("day") or day.get("day_number"),
                    "place_ids": [item.get("place_id") for item in day.get("items", []) or []],
                }
                for day in itinerary.get("days", []) or []
            ]
        }
