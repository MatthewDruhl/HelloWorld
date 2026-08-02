from hello import greet


def test_greet_uses_name():
    assert greet("World") == "Hello, World!"
