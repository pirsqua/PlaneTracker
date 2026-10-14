"""OpenSky Network wire format: decode /states/all responses into typed rows.

This module only decodes what OpenSky sends, using the field types and nullability
documented at https://openskynetwork.github.io/opensky-api/rest.html#all-state-vectors.
Our own cleanup rules live in silver.py.
"""

from enum import IntEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, field_validator

# Positional fields of a state vector row, in OpenSky's documented order.
# "category" (index 17) is only sent when the request includes extended=1.
STATE_FIELDS = (
    "icao24",
    "callsign",
    "origin_country",
    "time_position",
    "last_contact",
    "longitude",
    "latitude",
    "baro_altitude",
    "on_ground",
    "velocity",
    "true_track",
    "vertical_rate",
    "sensors",
    "geo_altitude",
    "squawk",
    "spi",
    "position_source",
    "category",
)


class PositionSource(IntEnum):
    ADS_B = 0
    ASTERIX = 1
    MLAT = 2
    FLARM = 3


class StatesResponse(BaseModel):
    """The /states/all response body.

    Rows are left undecoded here so that one malformed row can't reject the batch.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    time: int
    states: list[Any]

    @field_validator("states", mode="before")
    @classmethod
    def _null_means_no_aircraft(cls, value: object) -> object:
        return [] if value is None else value


class StateVector(BaseModel):
    """One row of the states array, typed exactly as OpenSky documents it."""

    # strict: no silent coercion like "123" -> 123, so format changes surface as errors.
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    icao24: str
    callsign: str | None
    origin_country: str
    time_position: int | None
    last_contact: int
    longitude: float | None
    latitude: float | None
    baro_altitude: float | None
    on_ground: bool
    velocity: float | None
    true_track: float | None
    vertical_rate: float | None
    sensors: list[int] | None
    geo_altitude: float | None
    squawk: str | None
    spi: bool
    position_source: int
    category: int | None = None

    @classmethod
    def from_row(cls, row: object) -> Self:
        if not isinstance(row, list) or len(row) not in (17, 18):
            raise ValueError(f"expected a list of 17 or 18 fields, got {row!r:.80}")
        # strict=False: a 17-field row leaves "category" unset (None).
        return cls.model_validate(dict(zip(STATE_FIELDS, row, strict=False)))
