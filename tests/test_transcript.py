"""Tests for chat transcript rendering."""

import pytest

from animaos.app import ChatTranscript


@pytest.mark.parametrize(
    "turns",
    [
        [("you", "Hello")],
        [("agent", "Response line 1\nline 2")],
    ],
)
def test_transcript_render(turns):
    transcript = ChatTranscript()
    for role, content in turns:
        transcript.append(role, content)

    assert transcript.render() is not None

