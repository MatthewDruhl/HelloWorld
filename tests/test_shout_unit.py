from hello import shout


def test_shout_uppercases_full_name():
    assert shout("mAtT") == "HELLO, MATT!!!"
    assert shout("Mary Anne-Marie") == "HELLO, MARY ANNE-MARIE!!!"
