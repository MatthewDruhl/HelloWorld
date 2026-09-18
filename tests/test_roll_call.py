def test_roll_call_numbers_each_greeting_on_its_own_line():
    """ACCEPT (#21): roll_call(names) numbers each greeting on its own line.

    Plain: calling roll_call with a list of names returns one numbered
    greeting per name, "N. Hello, Name!" with 1-based numbering in the
    input's order, newline-joined with no trailing newline. Each line is
    exactly what greet would say for that name, behind its number.
    Duplicates keep their own numbers. A single-element list returns just
    "1. " plus that one greeting with no newline, and an empty list returns
    an empty string (the issue's stated edge). The two-name example is
    verbatim from issue #21; the four-name example pins order (neither
    ascending nor descending), length beyond two, a preserved duplicate with
    its own number, and numbering that keeps counting past it. (Finite
    examples cannot rule out a lookup table; genuine list processing is
    enforced by spec-dev review of the implementation.) While PENDING, any
    failure is expected by design; the implementing PR removes the marker,
    and only then do these assertions gate for real.

    technical (contract):
      roll_call(["Matt", "Ada"]) -> "1. Hello, Matt!\\n2. Hello, Ada!"
      roll_call(["Matt", "Ada", "World", "Matt"])
          -> "1. Hello, Matt!\\n2. Hello, Ada!\\n3. Hello, World!\\n4. Hello, Matt!"
      roll_call(["Wendy"]) -> "1. Hello, Wendy!"
      roll_call([])        -> ""
    """
    from hello import roll_call  # imported here so absence is an xfail, not a collection error

    assert roll_call(["Matt", "Ada"]) == "1. Hello, Matt!\n2. Hello, Ada!"
    assert roll_call(["Matt", "Ada", "World", "Matt"]) == "1. Hello, Matt!\n2. Hello, Ada!\n3. Hello, World!\n4. Hello, Matt!"
    assert roll_call(["Wendy"]) == "1. Hello, Wendy!"
    assert roll_call([]) == ""
