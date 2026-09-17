def greet(name: str) -> str:
    """Return a friendly greeting for name."""
    return f"Hello, {name}!"


def greet_many(names: list[str]) -> str:
    """Return one greeting per name, newline-joined."""
    return "\n".join(greet(name) for name in names)


def farewell(name: str) -> str:
    """Return a friendly goodbye for name."""
    return f"Goodbye, {name}!"


def shout(name: str) -> str:
    """Return a loud, uppercased greeting for name."""
    return f"HELLO, {name.upper()}!!!"


def whisper(name: str) -> str:
    """Return a quiet, lowercased aside greeting for name."""
    return f"(hello, {name.lower()})"
