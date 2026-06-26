import pytest

from ceres.character.mechanism.errors import ReplayError


def test_replay_error_is_exception():
    assert issubclass(ReplayError, Exception)


def test_replay_error_can_be_raised_and_caught():
    with pytest.raises(ReplayError):
        raise ReplayError('replay failed')


def test_replay_error_message_is_preserved():
    with pytest.raises(ReplayError, match='bad state'):
        raise ReplayError('bad state')


def test_replay_error_not_caught_as_value_error():
    with pytest.raises(ReplayError):
        try:
            raise ReplayError()
        except ValueError:
            pass
