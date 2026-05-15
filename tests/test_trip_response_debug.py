from backend.main import _build_trip_response
from backend.state import TripState


def test_trip_response_no_raw_pydantic_errors():
    state = TripState(
        user_input="Plan a trip",
        errors=["Pydantic validation error https://errors.pydantic.dev/2.0/v/bool_type"],
        service_status={"places": {"provider": "geoapify", "status": "success", "count": 1}},
    )

    response = _build_trip_response("Plan a trip", state, start_time=0)

    assert "errors.pydantic.dev" not in " ".join(response.errors)
    assert "errors.pydantic.dev" not in " ".join(response.warnings)
    assert response.service_status["places"]["provider"] == "geoapify"
    assert response.data_sources["places"]["count"] == 1
