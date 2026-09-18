from hello import roll_call


def test_roll_call_numbers_names_in_order():
    assert roll_call(["Matt", "Ada"]) == "1. Hello, Matt!\n2. Hello, Ada!"
    assert roll_call([]) == ""
