from typing import Any, ClassVar, Literal

from pydantic import Field, model_validator

from ceres.gear.computer import ComputerPart
from ceres.shared import CeresPart, Equipment

INTEGRATED_COMPUTER_0_MIN_TL = 10
INTEGRATED_COMPUTER_0_MAX_TL = 12
INTEGRATED_COMPUTER_1_MIN_TL = 13
SATELLITE_UPLINK_MIN_RANGE_KM = 500
# refs/csc/02_equipment_availability.md — Retrotech: electronics halve in cost
# and mass for each TL past their model, for at most three TLs (RIG-001).
RETROTECH_MAX_ELECTRONICS_LEVELS = 3
# refs/csc/05_communications.md — planetary and longer-range transceivers do not
# decrease in size past TL12.
PLANETARY_RANGE_KM = 50_000
PLANETARY_MIN_SIZE_TL = 12


def _format_range(range_km: int) -> str:
    return f'{range_km:,}km'


class TransceiverPart(CeresPart):
    """Generic transceiver part, independent of where it is installed."""

    medium: Literal['radio_comm', 'laser', 'meson'] = 'radio_comm'
    range_km: int
    mass_kg: float = 0.0

    _MEDIUM_DISPLAY: ClassVar[dict[str, str]] = {
        'radio_comm': 'Radio',
        'laser': 'Laser',
        'meson': 'Meson',
    }

    @property
    def integrated_computer_processing(self) -> int | None:
        if INTEGRATED_COMPUTER_0_MIN_TL <= self.tl <= INTEGRATED_COMPUTER_0_MAX_TL:
            return 0
        if self.tl >= INTEGRATED_COMPUTER_1_MIN_TL:
            return 1
        return None

    @property
    def description(self) -> str:
        return f'{self._MEDIUM_DISPLAY[self.medium]} Transceiver {_format_range(self.range_km)}'


class RadioTransceiverPart(TransceiverPart):
    medium: Literal['radio_comm'] = 'radio_comm'


class LaserTransceiverPart(TransceiverPart):
    medium: Literal['laser'] = 'laser'


class MesonTransceiverPart(TransceiverPart):
    medium: Literal['meson'] = 'meson'


class TransceiverEncryptionPart(CeresPart):
    """CSC hardware encryption module for transceivers."""

    tl: int = 6
    cost: float = 4_000.0

    @property
    def description(self) -> str:
        return 'Hardware Encryption Module'


class SatelliteUplinkPart(CeresPart):
    """CSC satellite uplink option for radio transceivers."""

    cost: float
    mass_kg: float
    static: bool = False
    range_multiplier: int = 100

    @property
    def description(self) -> str:
        if self.static:
            return 'Static Satellite Uplink'
        return 'Satellite Uplink'


class TransceiverEquipment(Equipment):
    """Generic transceiver equipment container."""

    range_km: int | None = Field(default=None, exclude=True)
    encryption: bool = False
    satellite_uplink: Literal['none', 'standard', 'static'] | bool = 'none'
    parts: list[CeresPart] = Field(default_factory=list)
    _specs: ClassVar[dict[tuple[int, int], dict[str, int | float]]] = {}

    @property
    def transceiver_part(self) -> TransceiverPart:
        for part in self.parts:
            if isinstance(part, TransceiverPart):
                return part
        raise RuntimeError(f'{type(self).__name__} has no transceiver part')

    def item_description(self) -> str:
        return self.transceiver_part.description

    @staticmethod
    def parts_for_transceiver(part: TransceiverPart) -> list[CeresPart]:
        parts: list[CeresPart] = [part]
        if (processing := part.integrated_computer_processing) is not None:
            parts.append(ComputerPart(processing=processing, tl=part.tl))
        return parts

    @classmethod
    def resolve_transceiver_data(cls, data: dict, part: TransceiverPart, spec: dict[str, int | float]) -> dict:
        base_cost = float(spec['cost'])
        base_mass = float(spec['mass_kg'])
        parts = cls.parts_for_transceiver(part)
        total_cost = base_cost
        total_mass = base_mass
        tl = part.tl

        if data.get('encryption', False):
            encryption = TransceiverEncryptionPart()
            parts.append(encryption)
            total_cost += encryption.cost
            tl = max(tl, encryption.tl)

        satellite_uplink = cls._normalise_satellite_uplink(data.get('satellite_uplink', 'none'))
        if satellite_uplink != 'none':
            if part.medium != 'radio_comm':
                raise ValueError('Satellite uplinks are only available for radio transceivers')
            if part.range_km < SATELLITE_UPLINK_MIN_RANGE_KM:
                raise ValueError('Satellite uplink requires a radio transceiver with at least 500km range')
            static = satellite_uplink == 'static'
            uplink_cost = base_cost * 0.5 if static else max(base_cost * 0.5, 1_000.0)
            uplink_mass = max(base_mass, 2.0)
            uplink = SatelliteUplinkPart(tl=6, cost=uplink_cost, mass_kg=uplink_mass, static=static)
            parts.append(uplink)
            total_cost += uplink.cost
            total_mass += uplink.mass_kg
            tl = max(tl, uplink.tl)

        data.setdefault('parts', parts)
        data.setdefault('tl', tl)
        data.setdefault('cost', total_cost)
        data.setdefault('mass_kg', total_mass)
        return data

    @staticmethod
    def _normalise_satellite_uplink(value: Literal['none', 'standard', 'static'] | bool) -> str:
        if value is True:
            return 'standard'
        if value is False or value is None:
            return 'none'
        if value not in {'none', 'standard', 'static'}:
            raise ValueError("satellite_uplink must be one of: 'none', 'standard', 'static'")
        return value

    _medium_name: ClassVar[str]
    _part_cls: ClassVar[type[TransceiverPart]]

    @model_validator(mode='before')
    @classmethod
    def _resolve_range(cls, data: Any) -> Any:
        if not isinstance(data, dict) or cls is TransceiverEquipment:
            return data
        range_km = data.get('range_km')
        if range_km is None or 'parts' in data:
            return data
        tl = data.get('tl')
        model_tl = cls._resolve_spec_tl(int(range_km), int(tl) if tl is not None else None)
        built_tl = model_tl if tl is None else int(tl)
        spec = cls._retrotech_spec(cls._specs[(model_tl, int(range_km))], model_tl, built_tl, int(range_km))
        part = cls._part_cls(
            tl=built_tl,
            cost=float(spec['cost']),
            range_km=int(range_km),
            mass_kg=float(spec['mass_kg']),
        )
        return cls.resolve_transceiver_data(data, part, spec)

    @staticmethod
    def _retrotech_spec(spec: dict[str, int | float], model_tl: int, built_tl: int, range_km: int) -> dict[str, float]:
        """The model's figures, as built some TLs after its introduction.

        Cost and mass halve for each TL past the model, for no more than three
        TLs. A planetary or longer-range transceiver keeps getting cheaper but
        stops getting smaller past TL12.
        """
        levels = min(built_tl - model_tl, RETROTECH_MAX_ELECTRONICS_LEVELS)
        size_levels = levels
        if range_km >= PLANETARY_RANGE_KM:
            size_levels = min(levels, max(PLANETARY_MIN_SIZE_TL - model_tl, 0))
        return {
            'cost': float(spec['cost']) / 2**levels,
            'mass_kg': float(spec['mass_kg']) / 2**size_levels,
        }

    @classmethod
    def model_tl(cls, range_km: int, tl: int) -> int:
        """The Tech Level of the listed model a transceiver built at `tl` starts from."""
        return cls._resolve_spec_tl(range_km, tl)

    @classmethod
    def _resolve_spec_tl(cls, range_km: int, tl: int | None) -> int:
        """The TL of the model a transceiver of this range is built from.

        With no TL given, the earliest model. With one given, the latest model
        already introduced by then, which retrotech then carries forward.
        """
        supported = cls.supported_tls(range_km)
        if not supported:
            raise ValueError(f'Unsupported {cls._medium_name} transceiver range {_format_range(range_km)}')
        if tl is None:
            return supported[0]
        introduced = [model_tl for model_tl in supported if model_tl <= tl]
        if not introduced:
            raise ValueError(
                f'Unsupported {cls._medium_name} transceiver {_format_range(range_km)} at TL{tl}; '
                f'the earliest is TL{supported[0]}'
            )
        return introduced[-1]

    @classmethod
    def supported_tls(cls, range_km: int) -> list[int]:
        return sorted(spec_tl for spec_tl, spec_range in cls._specs if spec_range == range_km)


class RadioTransceiverEquipment(TransceiverEquipment):
    """CSC radio transceiver equipment.

    This is the stand-alone item a Traveller buys from the Central Supply
    Catalogue. Context-specific installations, such as robot zero-slot
    transceivers, should combine or wrap `RadioTransceiverPart` separately.
    """

    _medium_name: ClassVar[str] = 'radio'
    _part_cls: ClassVar[type[TransceiverPart]] = RadioTransceiverPart

    _specs: ClassVar[dict[tuple[int, int], dict[str, int | float]]] = {
        (5, 5): {'mass_kg': 20.0, 'cost': 225.0},
        (5, 50): {'mass_kg': 70.0, 'cost': 750.0},
        (5, 50_000): {'mass_kg': 1_000.0, 'cost': 500_000.0},
        (7, 5): {'mass_kg': 1.0, 'cost': 100.0},
        (7, 50): {'mass_kg': 5.0, 'cost': 250.0},
        (7, 500): {'mass_kg': 10.0, 'cost': 500.0},
        (7, 5_000): {'mass_kg': 20.0, 'cost': 5_000.0},
        (7, 50_000): {'mass_kg': 200.0, 'cost': 50_000.0},
        (7, 500_000): {'mass_kg': 2_000.0, 'cost': 500_000.0},
        (8, 5): {'mass_kg': 0.0, 'cost': 75.0},
        (8, 50): {'mass_kg': 0.0, 'cost': 500.0},
        (9, 500): {'mass_kg': 0.0, 'cost': 500.0},
        (9, 5_000): {'mass_kg': 0.0, 'cost': 5_000.0},
        (9, 50_000): {'mass_kg': 10.0, 'cost': 15_000.0},
        (9, 500_000): {'mass_kg': 20.0, 'cost': 30_000.0},
        (12, 5_000): {'mass_kg': 0.0, 'cost': 500.0},
        (12, 50_000): {'mass_kg': 2.0, 'cost': 2_000.0},
        (12, 500_000): {'mass_kg': 5.0, 'cost': 5_000.0},
    }


class LaserTransceiverEquipment(TransceiverEquipment):
    """CSC laser transceiver equipment."""

    _medium_name: ClassVar[str] = 'laser'
    _part_cls: ClassVar[type[TransceiverPart]] = LaserTransceiverPart

    _specs: ClassVar[dict[tuple[int, int], dict[str, int | float]]] = {
        (9, 500): {'mass_kg': 1.5, 'cost': 2_500.0},
        (11, 500): {'mass_kg': 0.5, 'cost': 1_500.0},
        (13, 500): {'mass_kg': 0.0, 'cost': 500.0},
    }


class MesonTransceiverEquipment(TransceiverEquipment):
    """CSC meson transceiver equipment."""

    _medium_name: ClassVar[str] = 'meson'
    _part_cls: ClassVar[type[TransceiverPart]] = MesonTransceiverPart

    _specs: ClassVar[dict[tuple[int, int], dict[str, int | float]]] = {
        (12, 50_000): {'mass_kg': 200.0, 'cost': 50_000.0},
        (12, 500_000): {'mass_kg': 500.0, 'cost': 100_000.0},
        (14, 50_000): {'mass_kg': 100.0, 'cost': 25_000.0},
        (14, 500_000): {'mass_kg': 200.0, 'cost': 50_000.0},
    }


class BugWiredAudio(Equipment):
    """
    Microphone, wiring and a tube amplifier in the other end.
    Either someone listens with headphones or it's connected to a separate radio transmitter.
    Microphone is usually hidden in a radio, telephone, ventilation duct etc.
    """

    tl: int = 5
    mass_kg: int = 3
    cost: int = 50

    description: Literal['Wired Audio Bug'] = 'Wired Audio Bug'


class BugPassiveAudio(Equipment):
    """
    Small Tape Recorder.
    Voice activated.
    Can record up to 1D hours during 1D days.
    """

    tl: int = 6
    mass_kg: int = 1
    cost: int = 50

    description: Literal['Recording Audio Bug'] = 'Recording Audio Bug'


class BugPassivePhoto(Equipment):
    pass


class BugWiredVideo(Equipment):
    pass


class BugPassiveVideo(Equipment):
    pass
