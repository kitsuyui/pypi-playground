"""Hello, World! package.

This package provides a simple function to generate a greeting message "Hello, World!".
And also provides a function to print the message.
This package is just for example.

Example:
    >>> import kitsuyui.hello
    >>> kitsuyui.hello.hello_world()
    'Hello, World!'
    >>> kitsuyui.hello.print_hello_world()
    Hello, World!
"""

# https://packaging-guide.openastronomy.org/en/latest/advanced/versioning.html
from ._version import __version__


def hello_world() -> str:
    """Generate greeting message "Hello, World!"."""
    return "Hello, World!"


def print_hello_world():
    """Print greeting message "Hello, World!"."""
    print(hello_world())


__all__ = [
    "__version__",
    "hello_world",
    "print_hello_world",
]
