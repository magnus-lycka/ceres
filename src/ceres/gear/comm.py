from ceres.shared import Equipment


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
