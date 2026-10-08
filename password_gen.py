#!/usr/bin/env python3
"""
password_gen.py - A cryptographically secure random password generator CLI.

Usage examples:
    python password_gen.py
    python password_gen.py -l 24
    python password_gen.py -l 20 --no-special
    python password_gen.py -l 12 -s -n -u -c
"""

import argparse
import math
import os
import secrets
import string
import sys

# pyperclip is an optional runtime dependency. If it isn't installed we still
# want the tool to work, so we import it defensively and degrade gracefully.
try:
    import pyperclip
except ImportError:  # pragma: no cover
    pyperclip = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MIN_LENGTH = 4
DEFAULT_LENGTH = 16

LOWERCASE = string.ascii_lowercase       # a-z (always enabled)
UPPERCASE = string.ascii_uppercase       # A-Z
DIGITS = string.digits                   # 0-9
SPECIAL = "!@#$%^&*()-_=+[]{};:,.<>?/"   # curated symbol set


# ---------------------------------------------------------------------------
# Terminal colors (ANSI escape codes)
# ---------------------------------------------------------------------------
class Color:
    """ANSI color helper. Colors are disabled when output isn't a terminal
    (e.g. piped to a file) or when the NO_COLOR env variable is set."""

    ENABLED = sys.stderr.isatty() and "NO_COLOR" not in os.environ

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"

    @classmethod
    def paint(cls, text: str, *codes: str) -> str:
        if not cls.ENABLED:
            return text
        return "".join(codes) + text + cls.RESET


def info(message: str) -> None:
    """Print status/feedback messages to stderr so that stdout contains ONLY
    the password. This keeps the tool pipe-friendly:
        python password_gen.py | some_other_command
    """
    print(message, file=sys.stderr)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def valid_length(value: str) -> int:
    """argparse 'type' function: converts to int and enforces the minimum."""
    try:
        length = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer.")
    if length < MIN_LENGTH:
        raise argparse.ArgumentTypeError(
            f"length must be at least {MIN_LENGTH} (got {length})."
        )
    return length


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a cryptographically secure random password.",
        epilog="Lowercase letters are always included.",
    )
    parser.add_argument(
        "-l", "--length", type=valid_length, default=DEFAULT_LENGTH,
        help=f"password length (default: {DEFAULT_LENGTH}, minimum: {MIN_LENGTH})",
    )
    parser.add_argument(
        "-s", "--no-special", action="store_true",
        help="exclude special characters (!@#$%%^&*...)",
    )
    parser.add_argument(
        "-n", "--no-numbers", action="store_true",
        help="exclude digits (0-9)",
    )
    parser.add_argument(
        "-u", "--no-uppercase", action="store_true",
        help="exclude uppercase letters (A-Z)",
    )
    parser.add_argument(
        "-c", "--copy", action="store_true",
        help="copy the generated password to the clipboard",
    )
    return parser


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def build_pools(use_upper: bool, use_digits: bool, use_special: bool) -> list[str]:
    """Return the list of active character pools. Lowercase is always on,
    which guarantees at least one pool exists."""
    pools = [LOWERCASE]
    if use_upper:
        pools.append(UPPERCASE)
    if use_digits:
        pools.append(DIGITS)
    if use_special:
        pools.append(SPECIAL)
    return pools


def generate_password(length: int, pools: list[str]) -> str:
    """Generate a password of `length` characters that contains at least one
    character from EVERY active pool.

    Algorithm:
      1. Pick one guaranteed character from each pool.
      2. Fill the remaining slots from the combined alphabet.
      3. Shuffle with a CSPRNG so the guaranteed characters don't sit in
         predictable positions (e.g. always at the start).
    """
    if length < len(pools):
        raise ValueError("length is too short to include every character type.")

    # Step 1: one guaranteed character per active pool
    chars = [secrets.choice(pool) for pool in pools]

    # Step 2: fill the rest from the combined alphabet
    combined = "".join(pools)
    chars.extend(secrets.choice(combined) for _ in range(length - len(chars)))

    # Step 3: secure shuffle. SystemRandom draws from the OS's CSPRNG,
    # unlike the default random.shuffle which uses the predictable
    # Mersenne Twister.
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def estimate_entropy(length: int, pools: list[str]) -> float:
    """Approximate entropy in bits: length * log2(alphabet size).

    This is a slight over-estimate because the 'at least one of each type'
    rule removes a small number of possible passwords, but it's a standard,
    useful rule of thumb.
    """
    alphabet_size = len("".join(pools))
    return length * math.log2(alphabet_size)


def rate_strength(entropy: float) -> tuple[str, str]:
    """Map entropy bits to a (label, color) pair."""
    if entropy < 40:
        return "Weak", Color.RED
    if entropy < 60:
        return "Fair", Color.YELLOW
    if entropy < 100:
        return "Strong", Color.GREEN
    return "Very Strong", Color.GREEN


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------
def copy_to_clipboard(password: str) -> None:
    """Copy to clipboard, warning (not crashing) if it isn't possible."""
    if pyperclip is None:
        info(Color.paint(
            "Warning: 'pyperclip' is not installed, so nothing was copied.\n"
            "         Install it with:  pip install pyperclip",
            Color.YELLOW,
        ))
        return
    try:
        pyperclip.copy(password)
        info(Color.paint("✔ Password copied to clipboard.", Color.GREEN))
    except pyperclip.PyperclipException:
        info(Color.paint(
            "Warning: no clipboard mechanism found (common on headless Linux).\n"
            "         Install one, e.g.:  sudo apt install xclip   (or xsel / wl-clipboard)\n"
            "         The password was NOT copied; use the output above.",
            Color.YELLOW,
        ))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    args = build_parser().parse_args()

    pools = build_pools(
        use_upper=not args.no_uppercase,
        use_digits=not args.no_numbers,
        use_special=not args.no_special,
    )

    password = generate_password(args.length, pools)
    entropy = estimate_entropy(args.length, pools)
    label, color = rate_strength(entropy)

    # Feedback goes to stderr; the password alone goes to stdout.
    info(Color.paint("\n🔐 Password generated successfully!", Color.BOLD, Color.CYAN))
    print(password)
    info(
        f"\nLength:   {args.length}"
        f"\nPool size: {len(''.join(pools))} characters"
        f"\nEntropy:  ~{entropy:.1f} bits"
        f"\nStrength: {Color.paint(label, Color.BOLD, color)}\n"
    )

    if args.copy:
        copy_to_clipboard(password)

    return 0


if __name__ == "__main__":
    sys.exit(main())
