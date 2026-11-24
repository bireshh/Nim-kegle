# Nim-kegle

Two interactive GUI games for a presentation:

- `nim.py` — classic Nim with piles of stones.
- `kegle.py` — a row of pins; each move removes 1 or 2 neighbouring pins, splitting the row into strips.

Both offer **player vs player** and **player vs computer** modes. Whoever takes the last stone or
pin wins. In computer mode the app checks whether the starting position is winning and chooses who
moves first so the computer can force a win; the computer then always plays optimally.

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

Both games also support a local, uncommitted `.deps/` folder containing an extracted Tkinter and
Tcl/Tk runtime. They detect it automatically: if `tkinter` cannot be imported, they re-launch
themselves with the correct `PYTHONPATH`, `LD_LIBRARY_PATH` and `TK_LIBRARY`, so no environment
variables need to be set by hand. The folder is ignored by Git and must be created once if the
system Python has no Tkinter.

To create `.deps/` from scratch on Ubuntu/Debian without root access, run these commands from the
project directory:

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

Or, for the pin-row game:

```bash
python3 kegle.py
```

On Windows, use `python nim.py` or `python kegle.py`. The two files are independent, with their own
rules and interface. There are no command-line arguments and no installed packages beyond those
described above.

## How to play

### Nim (`nim.py`)

1. Choose **Play against the computer** or **Play against a person**.
2. Set the number of piles (1–8) and the stones in each pile (1–40), then press **Start game**.
3. Click a pile to select it, choose how many stones to take, and press **Take stones** (or Enter).
4. Stones can only be taken from one pile per move. The player who takes the last stone wins.
5. **New game** restarts the same setup; **Change setup** returns to the start screen.

### Kegle (`kegle.py`)

1. Choose **Play against the computer** or **Play against a person**.
2. Set the number of pins (1–40) in the starting row and press **Start game**.
3. Click one pin to select it. Click a neighbouring pin to select two pins; click the same pin to
   clear the selection, or a non-neighbouring pin to start again.
4. Press **Take pins** (or Enter). Removed pins leave gaps, so the row splits into separate strips.
5. The two pins must be neighbouring inside the same strip. The player who takes the last pin wins.
6. **New game** restarts with the same row length; **Change setup** returns to the start screen.

In both games, against the computer the app compares the nim-value of the starting position with
zero: the computer moves first only when the position is winning, otherwise you move first. The
computer's moves are optimal — in kegle it computes Grundy numbers for every strip.
