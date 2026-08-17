import pytest


@pytest.mark.xfail(strict=True, reason="PENDING (#7)")
def test_whisper_quietly_greets_the_name():
    """ACCEPT (#7): whisper(name) returns a quiet, lowercased aside.

    Plain: calling whisper with a person's name returns the greeting as a
    quiet aside: everything lowercased and wrapped in parentheses. Two
    different names produce two different asides, so a hardcoded string cannot
    satisfy this, and a capitalized input name comes out lowercased, so
    skipping the lowercasing fails too. The whisper("World") example is
    verbatim from issue #7.

    technical (contract):
      whisper("World") -> "(hello, world)"
      whisper("Matt")  -> "(hello, matt)"
    """
    from hello import whisper  # imported here so absence is an xfail, not a collection error

    assert whisper("World") == "(hello, world)"
    assert whisper("Matt") == "(hello, matt)"
