from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from planetracker.opensky import StatesResponse, StateVector

type RowFactory = Callable[..., list[Any]]  # matches the make_row fixture


class TestStatesResponse:
    def test_parses_real_response(self, sample_response: bytes) -> None:
        response = StatesResponse.model_validate_json(sample_response)

        assert response.time == 1792001919
        assert len(response.states) == 82

    def test_null_states_means_no_aircraft(self) -> None:
        response = StatesResponse.model_validate_json(b'{"time": 1, "states": null}')

        assert response.states == []

    @pytest.mark.parametrize(
        "body",
        [
            b'{"states": []}',  # no time
            b'{"time": "1792001919", "states": []}',  # time as a string
            b"<html>Service Unavailable</html>",  # not JSON at all
        ],
    )
    def test_rejects_unusable_body(self, body: bytes) -> None:
        with pytest.raises(ValidationError):
            StatesResponse.model_validate_json(body)


class TestStateVectorFromRow:
    def test_maps_fields_by_position(self, sample_response: bytes) -> None:
        # Uses the real response, not make_row, so a wrong field order can't hide.
        row = StatesResponse.model_validate_json(sample_response).states[0]

        state = StateVector.from_row(row)

        assert state.icao24 == "4acb59"
        assert state.callsign == "SAS28K  "  # decoded as sent; cleanup is Silver's job
        assert state.origin_country == "Sweden"
        assert (state.longitude, state.latitude) == (6.1802, 47.1115)
        assert state.on_ground is False
        assert state.squawk == "5745"
        assert state.category == 0

    def test_17_field_row_has_no_category(self, make_row: RowFactory) -> None:
        state = StateVector.from_row(make_row()[:17])

        assert state.category is None

    def test_whole_number_in_float_field_becomes_float(
        self, make_row: RowFactory
    ) -> None:
        state = StateVector.from_row(make_row(velocity=212))

        assert state.velocity == 212.0
        assert isinstance(state.velocity, float)

    @pytest.mark.parametrize("length", [0, 16, 19])
    def test_rejects_wrong_field_count(self, length: int) -> None:
        with pytest.raises(ValueError, match="17 or 18 fields"):
            StateVector.from_row([None] * length)

    @pytest.mark.parametrize("row", [None, "4acb59", {"icao24": "4acb59"}])
    def test_rejects_non_list(self, row: object) -> None:
        with pytest.raises(ValueError, match="17 or 18 fields"):
            StateVector.from_row(row)

    @pytest.mark.parametrize(
        "field",
        [
            "icao24",
            "origin_country",
            "last_contact",
            "on_ground",
            "spi",
            "position_source",
        ],
    )
    def test_rejects_null_in_documented_non_null_field(
        self, make_row: RowFactory, field: str
    ) -> None:
        with pytest.raises(ValidationError, match=field):
            StateVector.from_row(make_row(**{field: None}))

    @pytest.mark.parametrize(
        ("field", "value"),
        [("on_ground", "false"), ("last_contact", "1792001918"), ("velocity", "212.5")],
    )
    def test_strict_types_do_not_coerce_strings(
        self, make_row: RowFactory, field: str, value: str
    ) -> None:
        with pytest.raises(ValidationError, match=field):
            StateVector.from_row(make_row(**{field: value}))
