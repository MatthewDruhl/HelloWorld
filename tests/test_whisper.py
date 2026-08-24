import pytest


@pytest.mark.xfail(strict=True, reason="PENDING (#7)")
def test_whisper_quietly_greets_the_name():
    """ACCEPT (#7): whisper(name) quietly greets the name.

    Plain: calling whisper with a person's name returns the greeting as a
    quiet aside: all lowercase, wrapped in parentheses, no exclamation mark.
    Three different names produce three different asides, so a single
    hardcoded string cannot pass; the all-caps case forces every letter of
    the name to be lowercased, not just the first.

    technical (contract):
      whisper("World") -> "(hello, world)"
      whisper("Matt")  -> "(hello, matt)"
      whisper("ALICE") -> "(hello, alice)"
    """
    from hello import whisper  # imported here so absence is an xfail, not a collection error

    assert whisper("World") == "(hello, world)"
    assert whisper("Matt") == "(hello, matt)"
    assert whisper("ALICE") == "(hello, alice)"
