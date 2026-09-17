import pytest


@pytest.mark.xfail(strict=True, reason="PENDING (#8)")
def test_greet_many_greets_each_name_on_its_own_line():
    """ACCEPT (#8): greet_many(names) greets each name on its own line.

    Plain: calling greet_many with a list of names returns one greeting per
    name, each on its own line, newline-joined with no trailing newline, in
    the input's order, with duplicates preserved (a repeated name is greeted
    again). A single-element list returns just that one greeting with no
    newline, and an empty list returns an empty string (the issue's stated
    edge). The four-name example pins order (neither ascending nor
    descending), length beyond two, and a preserved duplicate, so a sorted or
    deduplicated implementation fails. (Finite examples cannot rule out a
    lookup table; genuine list processing is enforced by spec-dev review of
    the implementation.) The examples are derived from issue #8's behavior
    statement. While PENDING, any failure is expected by design; the
    implementing PR removes the marker, and only then do these assertions
    gate for real.

    technical (contract):
      greet_many(["Matt", "Ada", "World", "Matt"])
          -> "Hello, Matt!\\nHello, Ada!\\nHello, World!\\nHello, Matt!"
      greet_many(["World", "Matt"]) -> "Hello, World!\\nHello, Matt!"
      greet_many(["World"])         -> "Hello, World!"
      greet_many([])                -> ""
    """
    from hello import greet_many  # imported here so absence is an xfail, not a collection error

    assert greet_many(["Matt", "Ada", "World", "Matt"]) == "Hello, Matt!\nHello, Ada!\nHello, World!\nHello, Matt!"
    assert greet_many(["World", "Matt"]) == "Hello, World!\nHello, Matt!"
    assert greet_many(["World"]) == "Hello, World!"
    assert greet_many([]) == ""
