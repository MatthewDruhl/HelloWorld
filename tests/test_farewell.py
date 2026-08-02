import pytest


@pytest.mark.xfail(strict=True, reason="PENDING (#1)")
def test_farewell_greets_the_name():
    """ACCEPT (#1): farewell(name) returns a personalized goodbye.

    Plain: calling farewell with a person's name returns a goodbye line that
    greets that exact name. Two different names produce two different lines, so
    a hardcoded string cannot satisfy this — the name has to be interpolated.

    technical (contract):
      farewell("World") -> "Goodbye, World!"
      farewell("Matt")  -> "Goodbye, Matt!"
    """
    from hello import farewell  # imported here so absence is an xfail, not a collection error

    assert farewell("World") == "Goodbye, World!"
    assert farewell("Matt") == "Goodbye, Matt!"
