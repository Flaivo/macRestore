"""Interactive single-key input with a safe non-terminal fallback."""

import sys


def _read_raw_key():
    import termios
    import tty

    file_descriptor = sys.stdin.fileno()
    settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setraw(file_descriptor)
        return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, settings)


def read_key(prompt, valid_keys=None):
    """Read one key without requiring Enter when attached to a terminal."""
    valid = {key.lower() for key in valid_keys} if valid_keys else None

    while True:
        print(prompt, end="", flush=True)

        if not sys.stdin.isatty():
            value = input().strip().lower()
            key = value[:1]
        else:
            key = _read_raw_key()
            print()

        if not valid or key in valid:
            return key

        print(f"Invalid choice '{key}'. Please try again.")


def read_number(prompt, maximum):
    """Read a numeric menu choice, including two-digit choices, without Enter."""
    while True:
        print(prompt, end="", flush=True)

        if not sys.stdin.isatty():
            value = input().strip()
        else:
            first = _read_raw_key()
            print()
            if not first.isdigit():
                print(f"Invalid choice '{first}'. Please try again.")
                continue

            value = first
            if first != "0" and maximum >= 10:
                import select

                ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                if ready:
                    second = _read_raw_key()
                    if second.isdigit():
                        value += second

        if value.isdigit() and 0 <= int(value) <= maximum:
            return value

        print(f"Invalid choice '{value}'. Please try again.")
