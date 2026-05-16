from typing import Any, ClassVar, Literal

from pydantic import Field, model_validator

from ceres.gear.computer import ComputerPart
from ceres.shared import CeresPart, Equipment


def _format_range(range_km: int) -> str:
    return f'{range_km:,}km'


class TransceiverPart(CeresPart):
    """Generic transceiver part, independent of where it is installed."""

    medium: Literal['radio', 'laser', 'meson'] = 'radio'
    range_km: int
    mass_kg: float = 0.0

    @property
    def integrated_computer_processing(self) -> int | None:
        if 10 <= self.tl <= 12:
            return 0
        if self.tl >= 13:
            return 1
        return None

    @property
    def description(self) -> str:
        return f'{self.medium.title()} Transceiver {_format_range(self.range_km)}'

    def build_item(self) -> str | None:
        return self.description


class RadioTransceiverPart(TransceiverPart):
    medium: Literal['radio'] = 'radio'


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

    def build_item(self) -> str | None:
        return self.description


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

    def build_item(self) -> str | None:
        return self.description


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

    def build_item(self) -> str | None:
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
            if part.medium != 'radio':
                raise ValueError('Satellite uplinks are only available for radio transceivers')
            if part.range_km < 500:
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


class RadioTransceiverEquipment(TransceiverEquipment):
    """CSC radio transceiver equipment.

    This is the stand-alone item a Traveller buys from the Central Supply
    Catalogue. Context-specific installations, such as robot zero-slot
    transceivers, should combine or wrap `RadioTransceiverPart` separately.
    """

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

    @model_validator(mode='before')
    @classmethod
    def _resolve_range(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        range_km = data.get('range_km')
        if range_km is None or 'parts' in data:
            return data
        tl = data.get('tl')
        spec_tl = cls._resolve_spec_tl(int(range_km), int(tl) if tl is not None else None)
        spec = cls._specs[(spec_tl, int(range_km))]
        part = RadioTransceiverPart(
            tl=spec_tl,
            cost=float(spec['cost']),
            range_km=int(range_km),
            mass_kg=float(spec['mass_kg']),
        )
        return cls.resolve_transceiver_data(data, part, spec)

    @classmethod
    def _resolve_spec_tl(cls, range_km: int, tl: int | None) -> int:
        if tl is not None:
            if (tl, range_km) in cls._specs:
                return tl
            supported = ', '.join(f'TL{spec_tl}' for spec_tl in cls.supported_tls(range_km))
            if supported:
                raise ValueError(
                    f'Unsupported radio transceiver {_format_range(range_km)} at TL{tl}; expected {supported}'
                )
            raise ValueError(f'Unsupported radio transceiver range {_format_range(range_km)}')
        supported_tls = cls.supported_tls(range_km)
        if not supported_tls:
            raise ValueError(f'Unsupported radio transceiver range {_format_range(range_km)}')
        return supported_tls[0]

    @classmethod
    def supported_tls(cls, range_km: int) -> list[int]:
        return sorted(spec_tl for spec_tl, spec_range in cls._specs if spec_range == range_km)


class LaserTransceiverEquipment(TransceiverEquipment):
    """CSC laser transceiver equipment."""

    _specs: ClassVar[dict[tuple[int, int], dict[str, int | float]]] = {
        (9, 500): {'mass_kg': 1.5, 'cost': 2_500.0},
        (11, 500): {'mass_kg': 0.5, 'cost': 1_500.0},
        (13, 500): {'mass_kg': 0.0, 'cost': 500.0},
    }

    @model_validator(mode='before')
    @classmethod
    def _resolve_range(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        range_km = data.get('range_km')
        if range_km is None or 'parts' in data:
            return data
        tl = data.get('tl')
        spec_tl = cls._resolve_spec_tl(int(range_km), int(tl) if tl is not None else None)
        spec = cls._specs[(spec_tl, int(range_km))]
        part = LaserTransceiverPart(
            tl=spec_tl,
            cost=float(spec['cost']),
            range_km=int(range_km),
            mass_kg=float(spec['mass_kg']),
        )
        return cls.resolve_transceiver_data(data, part, spec)

    @classmethod
    def _resolve_spec_tl(cls, range_km: int, tl: int | None) -> int:
        if tl is not None:
            if (tl, range_km) in cls._specs:
                return tl
            supported = ', '.join(f'TL{spec_tl}' for spec_tl in cls.supported_tls(range_km))
            if supported:
                raise ValueError(
                    f'Unsupported laser transceiver {_format_range(range_km)} at TL{tl}; expected {supported}'
                )
            raise ValueError(f'Unsupported laser transceiver range {_format_range(range_km)}')
        supported_tls = cls.supported_tls(range_km)
        if not supported_tls:
            raise ValueError(f'Unsupported laser transceiver range {_format_range(range_km)}')
        return supported_tls[0]

    @classmethod
    def supported_tls(cls, range_km: int) -> list[int]:
        return sorted(spec_tl for spec_tl, spec_range in cls._specs if spec_range == range_km)


class MesonTransceiverEquipment(TransceiverEquipment):
    """CSC meson transceiver equipment."""

    _specs: ClassVar[dict[tuple[int, int], dict[str, int | float]]] = {
        (12, 50_000): {'mass_kg': 200.0, 'cost': 50_000.0},
        (12, 500_000): {'mass_kg': 500.0, 'cost': 100_000.0},
        (14, 50_000): {'mass_kg': 100.0, 'cost': 25_000.0},
        (14, 500_000): {'mass_kg': 200.0, 'cost': 50_000.0},
    }

    @model_validator(mode='before')
    @classmethod
    def _resolve_range(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        range_km = data.get('range_km')
        if range_km is None or 'parts' in data:
            return data
        tl = data.get('tl')
        spec_tl = cls._resolve_spec_tl(int(range_km), int(tl) if tl is not None else None)
        spec = cls._specs[(spec_tl, int(range_km))]
        part = MesonTransceiverPart(
            tl=spec_tl,
            cost=float(spec['cost']),
            range_km=int(range_km),
            mass_kg=float(spec['mass_kg']),
        )
        return cls.resolve_transceiver_data(data, part, spec)

    @classmethod
    def _resolve_spec_tl(cls, range_km: int, tl: int | None) -> int:
        if tl is not None:
            if (tl, range_km) in cls._specs:
                return tl
            supported = ', '.join(f'TL{spec_tl}' for spec_tl in cls.supported_tls(range_km))
            if supported:
                raise ValueError(
                    f'Unsupported meson transceiver {_format_range(range_km)} at TL{tl}; expected {supported}'
                )
            raise ValueError(f'Unsupported meson transceiver range {_format_range(range_km)}')
        supported_tls = cls.supported_tls(range_km)
        if not supported_tls:
            raise ValueError(f'Unsupported meson transceiver range {_format_range(range_km)}')
        return supported_tls[0]

    @classmethod
    def supported_tls(cls, range_km: int) -> list[int]:
        return sorted(spec_tl for spec_tl, spec_range in cls._specs if spec_range == range_km)


class BugWiredAudio(Equipment):
    """
    Microphone, wiring and a tube amplifier in the other end.
    Either someone listens with headphones or it's connected to a separate radio transmitter.
    Microphone is usually hidden in a radio, telephone, ventilation duct etc.
    """

    tl: int = 5
    mass_kg: int = 3
    cost: int = 50

    def build_item(self) -> str | None:
        return 'Wired Audio Bug'


class BugPassiveAudio(Equipment):
    """
    Small Tape Recorder.
    Voice activated.
    Can record up to 1D hours during 1D days.
    """

    tl: int = 6
    mass_kg: int = 1
    cost: int = 50

    def build_item(self) -> str | None:
        return 'Recording Audio Bug'


class BugPassivePhoto(Equipment):
    pass


class BugWiredVideo(Equipment):
    pass


class BugPassiveVideo(Equipment):
    pass
