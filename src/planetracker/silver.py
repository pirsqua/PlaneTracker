"""Silver layer: normalize OpenSky state vectors into aircraft observations.

Pure functions only (no I/O, no clock reads), so replaying the same Bronze
response always produces the same Silver rows.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

from planetracker.opensky import PositionSource, StatesResponse, StateVector

Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]


class Observation(BaseModel):
    """One aircraft's state at one OpenSky snapshot. Units are in the field names."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    snapshot_time: AwareDatetime
    icao24: str = Field(pattern=r"^[0-9a-f]{6}$")
    callsign: str | None
    origin_country: str
    time_position: AwareDatetime | None
    last_contact: AwareDatetime
    latitude: Latitude | None
    longitude: Longitude | None
    baro_altitude_m: float | None
    geo_altitude_m: float | None
    on_ground: bool
    velocity_mps: Annotated[float, Field(ge=0)] | None
    true_track_deg: Annotated[float, Field(ge=0, le=360)] | None
    vertical_rate_mps: float | None
    squawk: str | None
    spi: bool
    position_source: PositionSource
    category: Annotated[int, Field(ge=0, le=20)] | None

    @model_validator(mode="after")
    def _position_is_complete(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must both be set or both be null")
        return self


@dataclass(frozen=True)
class Rejected:
    """A row that couldn't become an Observation. index points into the Bronze rows."""

    index: int
    reason: str


@dataclass(frozen=True)
class SilverBatch:
    snapshot_time: datetime
    observations: list[Observation]
    rejected: list[Rejected]


def to_silver(response: StatesResponse) -> SilverBatch:
    """Normalize every row of a response, collecting bad rows instead of failing."""
    snapshot_time = _utc(response.time)
    observations = []
    rejected = []
    for index, row in enumerate(response.states):
        try:
            state = StateVector.from_row(row)
            observations.append(to_observation(state, snapshot_time))
        except ValueError as error:  # pydantic's ValidationError is a ValueError
            rejected.append(Rejected(index, _describe(error)))
    return SilverBatch(snapshot_time, observations, rejected)


def to_observation(state: StateVector, snapshot_time: datetime) -> Observation:
    return Observation(
        snapshot_time=snapshot_time,
        icao24=state.icao24.strip().lower(),
        callsign=_blank_to_none(state.callsign),
        origin_country=state.origin_country,
        time_position=(
            _utc(state.time_position) if state.time_position is not None else None
        ),
        last_contact=_utc(state.last_contact),
        latitude=state.latitude,
        longitude=state.longitude,
        baro_altitude_m=state.baro_altitude,
        geo_altitude_m=state.geo_altitude,
        on_ground=state.on_ground,
        velocity_mps=state.velocity,
        true_track_deg=state.true_track,
        vertical_rate_mps=state.vertical_rate,
        squawk=_blank_to_none(state.squawk),
        spi=state.spi,
        position_source=PositionSource(state.position_source),
        category=state.category,
    )


def _utc(epoch_seconds: int) -> datetime:
    return datetime.fromtimestamp(epoch_seconds, tz=UTC)


def _blank_to_none(text: str | None) -> str | None:
    return (text or "").strip() or None


def _describe(error: ValueError) -> str:
    if not isinstance(error, ValidationError):
        return str(error)
    return "; ".join(
        f"{'.'.join(map(str, e['loc'])) or 'row'}: {e['msg']}" for e in error.errors()
    )
