import sys

from hello import greet

name = sys.argv[1] if len(sys.argv) > 1 else "World"
print(greet(name))
