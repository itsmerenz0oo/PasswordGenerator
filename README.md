# Password Generator

A cryptographically secure random password generator, available as a **Python command-line tool** and a **single-file web app**.

Both versions use the same algorithm and the operating system's secure random source. Neither one sends your passwords anywhere.

## Contents

| File | What it is |
| --- | --- |
| `password_gen.py` | The CLI tool (Python 3.9+) |
| `password_generator.html` | A self-contained web front end. Open it in any browser, no build step. |

## Features

- Secure randomness from Python's `secrets` module (CLI) and `crypto.getRandomValues` (web). Never `random`.
- Guaranteed character diversity: every enabled character type appears at least once.
- Secure shuffle, so the guaranteed characters don't sit in predictable positions.
- Adjustable length, from 4 characters up.
- Optional exclusion of uppercase letters, digits and symbols.
- Entropy estimate and a strength rating (Weak, Fair, Strong, Very Strong).
- Clipboard support in the CLI through `pyperclip`, with a clear warning if no clipboard is available (for example on headless Linux).
- Pipe-friendly output: only the password goes to `stdout`; status messages go to `stderr`.

## CLI

### Install

```bash
git clone <your-repo-url>
cd <your-repo-folder>
pip install pyperclip
```

`pyperclip` is optional. Without it the tool works normally and only `--copy` is unavailable.

On headless Linux, `pyperclip` also needs a clipboard backend:

```bash
sudo apt install xclip     # or xsel / wl-clipboard
```

### Usage

```bash
python password_gen.py [-l LENGTH] [-s] [-n] [-u] [-c]
```

| Flag | Long form | Description |
| --- | --- | --- |
| `-l` | `--length` | Password length (default `16`, minimum `4`) |
| `-s` | `--no-special` | Exclude special characters |
| `-n` | `--no-numbers` | Exclude digits `0-9` |
| `-u` | `--no-uppercase` | Exclude uppercase letters `A-Z` |
| `-c` | `--copy` | Copy the password to the clipboard |
| `-h` | `--help` | Show help |

Lowercase letters are always included, so there is always at least one character pool.

### Examples

```bash
python password_gen.py                  # 16 characters, all character types
python password_gen.py -l 32            # longer password
python password_gen.py -l 20 -s         # no special characters
python password_gen.py -l 8 -n -s       # letters only
python password_gen.py -l 24 -c         # generate and copy to clipboard
python password_gen.py | xclip          # pipe only the password elsewhere
```

Sample output:

```
🔐 Password generated successfully!
?;tC4djZQAe%:Y*03:IQ

Length:   20
Pool size: 88 characters
Entropy:  ~129.2 bits
Strength: Very Strong
```

## Web app

Open `password_generator.html` in a browser. It works offline apart from the Google Fonts, which fall back to system fonts if they can't load.

- The password is shown as colored tiles: lowercase, uppercase, digits and symbols each have their own color and corner mark.
- The character-type toggles double as the legend.
- A slider sets the length (4 to 64), and the page updates the entropy, strength and estimated crack time live.
- A command line under the password shows the equivalent `password_gen.py` command for your current settings.

The web app copies with the browser clipboard API. Some embedded or sandboxed views block it, in which case the page tells you.

## How it works

1. Pick one random character from each active pool (lowercase, plus uppercase, digits and symbols if enabled).
2. Fill the remaining positions with random characters from the combined alphabet.
3. Shuffle the result with a cryptographically secure shuffle.

Entropy is estimated as `length × log2(alphabet size)`. The "at least one of each type" rule removes a small number of possible passwords, so the figure is a slight overestimate, but it is a useful guide.

| Entropy | Rating |
| --- | --- |
| under 40 bits | Weak |
| 40 to 59 bits | Fair |
| 60 to 99 bits | Strong |
| 100 bits or more | Very Strong |

The symbol set is `!@#$%^&*()-_=+[]{};:,.<>?/`.

## Security notes

- Passwords are generated locally and are not logged, stored or transmitted.
- Passwords you copy to the clipboard stay there until something else replaces them. Clear your clipboard if you are on a shared machine.
- Terminal output can end up in your shell scrollback. Use `--copy` or a pipe if that matters to you.
- Use a password manager to store what you generate.

## Requirements

- Python 3.9 or newer (CLI)
- `pyperclip` (optional, for `--copy`)
- Any modern browser (web app)

## License

Add a `LICENSE` file and name your license here.
