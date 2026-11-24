# Nim-kegle

Interactive GUI game of Nim (normal play: whoever takes the last stone wins) for a presentation.
It offers **player vs player** and **player vs computer** modes. In computer mode the app checks
the starting position and chooses who moves first so the computer can force a win.

## Requirements

- Python 3 (tested with 3.12)
- A desktop environment with a working display
- Tkinter 8.6 (`tkinter` Python module plus Tcl/Tk runtime)

## Setup

### Option A: system Tkinter

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install python3-tk
```

On Fedora: `sudo dnf install python3-tkinter`. On Windows, the official Python installer includes
tkinter by default. On macOS with Homebrew: `brew install python-tk`.

### Option B: bundled local Tkinter (no root access)

This project includes a `.deps/` folder with an extracted Tkinter and Tcl/Tk runtime. `nim.py`
detects it automatically: it re-launches itself with the correct `PYTHONPATH`, `LD_LIBRARY_PATH`
and `TK_LIBRARY`, so no environment variables need to be set by hand.

To recreate `.deps/` from scratch on Ubuntu/Debian without root access, run these commands from
the project directory:

```bash
PROJECT_DIR="$(pwd)"
mkdir -p /tmp/nim-packages .deps
cd /tmp/nim-packages
apt-get download python3-tk libtk8.6 tk8.6 blt tk8.6-blt2.5
for package in *.deb; do dpkg-deb -x "$package" "$PROJECT_DIR/.deps"; done
```

The bundled build is for Python 3.12; with another Python version, use Option A or build matching
`python3-tk` packages. The `.deps/` folder is only needed when the system Python cannot import
`tkinter`.

## Run

From the project directory:

```bash
python3 nim.py
```

On Windows, use `python nim.py`. There are no command-line arguments and no installed packages
beyond those described above.

## How to play

1. Choose **Play against the computer** or **Play against a person**.
2. Set the number of piles (1–8) and the stones in each pile (1–40), then press **Start game**.
3. Click a pile to select it, choose how many stones to take, and press **Take stones** (or Enter).
4. Stones can only be taken from one pile per move. The player who takes the last stone wins.
5. **New game** restarts the same setup; **Change setup** returns to the start screen.

Against the computer, if the starting position has a nonzero nim-sum the computer moves first;
otherwise you move first. The computer then always replies with an optimal move.
