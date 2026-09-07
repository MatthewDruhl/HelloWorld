def greet(name: str) -> str:
    """Return a friendly greeting for name."""
    return f"Hello, {name}!"


def farewell(name: str) -> str:
    """Return a friendly goodbye for name."""
    return f"Goodbye, {name}!"


def whisper(name: str) -> str:
    """Return a quiet, lowercased aside greeting for name."""
    return f"(hello, {name.lower()})"
