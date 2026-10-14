from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from planetracker.opensky import PositionSource, StatesResponse, StateVector
from planetracker.silver import Observation, to_observation, to_silver

type RowFactory = Callable[..., list[Any]]  # matches the make_row fixture
SNAPSHOT_TIME = datetime(2026, 10, 14, 18, 18, 39, tzinfo=UTC)


def observe(row: list[Any]) -> Observation:
    return to_observation(StateVector.from_row(row), SNAPSHOT_TIME)


class TestToSilver:
    def test_real_response_is_fully_accepted(self, sample_response: bytes) -> None:
        batch = to_silver(StatesResponse.model_validate_json(sample_response))

        assert batch.rejected == []
        assert len(batch.observations) == 82
        assert batch.snapshot_time == SNAPSHOT_TIME
        assert {o.snapshot_time for o in batch.observations} == {SNAPSHOT_TIME}

    def test_bad_rows_are_rejected_without_losing_good_ones(
        self, make_row: RowFactory
    ) -> None:
        response = StatesResponse(
            time=1792001919,
            states=[
                make_row(icao24="aaaaaa"),
                make_row()[:5],  # truncated row
                make_row(icao24="bbbbbb", latitude=95.0),  # off the globe
                make_row(icao24="cccccc"),
            ],
        )

        batch = to_silver(response)

        assert [o.icao24 for o in batch.observations] == ["aaaaaa", "cccccc"]
        assert [r.index for r in batch.rejected] == [1, 2]
        assert "17 or 18 fields" in batch.rejected[0].reason
        assert "latitude" in batch.rejected[1].reason

    def test_is_deterministic(self, sample_response: bytes) -> None:
        response = StatesResponse.model_validate_json(sample_response)

        assert to_silver(response) == to_silver(response)


class TestToObservation:
    def test_normalizes_icao24(self, make_row: RowFactory) -> None:
        assert observe(make_row(icao24=" 4ACB59 ")).icao24 == "4acb59"

    @pytest.mark.parametrize("icao24", ["", "4acb5", "4acb59a", "zzzzzz", "~4acb5"])
    def test_rejects_invalid_icao24(self, make_row: RowFactory, icao24: str) -> None:
        with pytest.raises(ValidationError, match="icao24"):
            observe(make_row(icao24=icao24))

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("SAS28K  ", "SAS28K"), ("        ", None), (None, None)],
    )
    def test_cleans_callsign(
        self, make_row: RowFactory, raw: str | None, expected: str | None
    ) -> None:
        assert observe(make_row(callsign=raw)).callsign == expected

    def test_converts_epochs_to_utc(self, make_row: RowFactory) -> None:
        obs = observe(make_row(time_position=1792001917, last_contact=0))

        assert obs.time_position == datetime(2026, 10, 14, 18, 18, 37, tzinfo=UTC)
        assert obs.last_contact == datetime(1970, 1, 1, tzinfo=UTC)

    def test_keeps_missing_time_position(self, make_row: RowFactory) -> None:
        assert observe(make_row(time_position=None)).time_position is None

    def test_renames_fields_with_units(self, make_row: RowFactory) -> None:
        obs = observe(make_row())

        assert obs.baro_altitude_m == 8542.02
        assert obs.geo_altitude_m == 8999.22
        assert obs.velocity_mps == 212.5
        assert obs.true_track_deg == 359.03
        assert obs.vertical_rate_mps == 9.43

    def test_decodes_position_source(self, make_row: RowFactory) -> None:
        obs = observe(make_row(position_source=2))

        assert obs.position_source is PositionSource.MLAT

    def test_allows_no_position(self, make_row: RowFactory) -> None:
        obs = observe(make_row(latitude=None, longitude=None))

        assert (obs.latitude, obs.longitude) == (None, None)

    @pytest.mark.parametrize(
        "overrides",
        [
            {"latitude": 90.5},
            {"longitude": -180.5},
            {"latitude": None},  # longitude without latitude
            {"velocity": -1.0},
            {"true_track": 360.5},
            {"category": 21},
        ],
    )
    def test_rejects_impossible_values(
        self, make_row: RowFactory, overrides: dict[str, Any]
    ) -> None:
        with pytest.raises(ValidationError):
            observe(make_row(**overrides))

    def test_rejects_unknown_position_source(self, make_row: RowFactory) -> None:
        with pytest.raises(ValueError, match="PositionSource"):
            observe(make_row(position_source=7))
