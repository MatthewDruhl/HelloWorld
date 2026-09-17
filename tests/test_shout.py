def test_shout_uppercases_and_triple_exclaims_the_greeting():
    """ACCEPT (#6): shout(name) returns the greeting uppercased and triple-exclaimed.

    Plain: calling shout with a person's name returns the whole greeting
    shouted: everything uppercased (the whole name, not just its first
    letter) and ending in exactly three exclamation marks. Two different
    names produce two different shouts, so a single hardcoded return cannot
    satisfy this, and a mixed-case input name comes out fully uppercased, so
    uppercasing only the first character fails too. The "Wendy" example
    shares "world"'s initial, so a prefix lookup cannot satisfy this either,
    and the long hyphenated-and-spaced example pins full-name preservation:
    no truncation, no first-word-only, no stripping of spaces or hyphens.
    (Finite examples cannot rule out a lookup table; genuine interpolation is
    enforced by spec-dev review of the implementation.) The shout("world")
    example is verbatim from issue #6. While PENDING, any failure is expected
    by design; the implementing PR removes the marker, and only then do these
    assertions gate for real.

    technical (contract):
      shout("world")           -> "HELLO, WORLD!!!"
      shout("Matt")            -> "HELLO, MATT!!!"
      shout("mAtT")            -> "HELLO, MATT!!!"
      shout("Wendy")           -> "HELLO, WENDY!!!"
      shout("Mary Anne-Marie") -> "HELLO, MARY ANNE-MARIE!!!"
    """
    from hello import shout  # imported here so absence is an xfail, not a collection error

    assert shout("world") == "HELLO, WORLD!!!"
    assert shout("Matt") == "HELLO, MATT!!!"
    assert shout("mAtT") == "HELLO, MATT!!!"
    assert shout("Wendy") == "HELLO, WENDY!!!"
    assert shout("Mary Anne-Marie") == "HELLO, MARY ANNE-MARIE!!!"
