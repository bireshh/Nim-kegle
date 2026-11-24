import os
import sys
from functools import lru_cache
from pathlib import Path

DEPS_ROOT = Path(__file__).resolve().parent / ".deps" / "usr"
PY_DIR = DEPS_ROOT / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"


def bootstrap_tkinter():
    if os.environ.get("KEGLE_LOCAL_TK") == "1":
        raise RuntimeError("Local tkinter installation could not be loaded")
    env = os.environ.copy()
    env["KEGLE_LOCAL_TK"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(PY_DIR), str(PY_DIR / "lib-dynload"), env.get("PYTHONPATH", "")]
    )
    lib_dirs = [DEPS_ROOT / "lib", DEPS_ROOT / "lib" / "x86_64-linux-gnu"]
    env["LD_LIBRARY_PATH"] = os.pathsep.join(
        [str(path) for path in lib_dirs]
        + ([env["LD_LIBRARY_PATH"]] if env.get("LD_LIBRARY_PATH") else [])
    )
    for name, key in (("tk8.6", "TK_LIBRARY"), ("tcl8.6", "TCL_LIBRARY")):
        scripts = DEPS_ROOT / "share" / "tcltk" / name
        if scripts.is_dir():
            env[key] = str(scripts)
    os.execvpe(sys.executable, [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]], env)


try:
    import tkinter as tk
except ImportError:
    bootstrap_tkinter()

BG = "#171821"
PANEL = "#22243a"
ACCENT = "#f2a65a"
TEXT = "#f5f3ef"
MUTED = "#a6a9c2"
STONE = "#f2a65a"
STONE_SELECTED = "#7ee2c0"
BAND = "#d9534f"
EMPTY = "#3a3d55"

TITLE_FONT = ("DejaVu Sans", 38, "bold")
HEADING_FONT = ("DejaVu Sans", 18, "bold")
BODY_FONT = ("DejaVu Sans", 13)
TURN_FONT = ("DejaVu Sans", 24, "bold")


@lru_cache(maxsize=None)
def grundy(length):
    if length == 0:
        return 0
    options = set()
    for count in (1, 2):
        for left in range(length - count + 1):
            right = length - left - count
            options.add(grundy(left) ^ grundy(right))
    value = 0
    while value in options:
        value += 1
    return value


def segments(board):
    result = []
    start = None
    for index, standing in enumerate(board):
        if standing and start is None:
            start = index
        elif not standing and start is not None:
            result.append((start, index - start))
            start = None
    if start is not None:
        result.append((start, len(board) - start))
    return result


def position_value(board):
    value = 0
    for _, length in segments(board):
        value ^= grundy(length)
    return value


def legal_move(board, selection):
    if len(selection) not in (1, 2):
        return False
    for index in selection:
        if index < 0 or index >= len(board) or not board[index]:
            return False
    return len(selection) == 1 or abs(selection[0] - selection[1]) == 1


def apply_move(board, selection):
    result = board[:]
    for index in selection:
        result[index] = False
    return result


def optimal_move(board):
    if position_value(board):
        for start, length in segments(board):
            for count in (1, 2):
                for offset in range(length - count + 1):
                    first = start + offset
                    move = (first,) if count == 1 else (first, first + 1)
                    if position_value(apply_move(board, move)) == 0:
                        return list(move)
    for index, standing in enumerate(board):
        if standing:
            return [index]
    return []


def describe(selection):
    if len(selection) == 2:
        return f"pins {selection[0] + 1}–{selection[1] + 1}"
    return f"pin {selection[0] + 1}"


class KegleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kegle")
        self.root.geometry("980x680")
        self.root.minsize(760, 560)
        self.root.configure(bg=BG)

        self.mode = tk.StringVar(value="pc")
        self.pin_count = tk.IntVar(value=8)
        self.starting_pins = 8
        self.board = []
        self.selection = []
        self.canvas_geometry = (0, 30)
        self.turn = None
        self.first_turn = "p1"
        self.winner = None
        self.vs_pc = False
        self.game_over = False
        self.message = ""
        self.pc_job = None

        self.setup_frame = tk.Frame(root, bg=BG)
        self.game_frame = tk.Frame(root, bg=BG)
        self._build_setup()
        self._build_game()
        self.setup_frame.pack(fill="both", expand=True)
        self.root.bind("<Return>", self._on_return)

    def _build_setup(self):
        frame = self.setup_frame
        tk.Label(frame, text="KEGLE", font=TITLE_FONT, fg=ACCENT, bg=BG).pack(pady=(30, 4))
        tk.Label(
            frame,
            text="A row of pins: take 1 or 2 neighbouring pins. Whoever takes the last pin wins.",
            font=BODY_FONT,
            fg=MUTED,
            bg=BG,
        ).pack(pady=(0, 24))

        opponents = tk.LabelFrame(
            frame, text="Opponent", font=HEADING_FONT, fg=TEXT, bg=PANEL,
            padx=18, pady=14, bd=0,
        )
        opponents.pack(padx=40, fill="x")
        for text, value in (("Play against the computer", "pc"), ("Play against a person", "human")):
            tk.Radiobutton(
                opponents, text=text, value=value, variable=self.mode,
                font=BODY_FONT, fg=TEXT, bg=PANEL, selectcolor=BG,
                activebackground=PANEL, highlightthickness=0,
            ).pack(anchor="w", pady=3)

        row_box = tk.LabelFrame(
            frame, text="Starting row", font=HEADING_FONT, fg=TEXT, bg=PANEL,
            padx=18, pady=14, bd=0,
        )
        row_box.pack(padx=40, pady=18, fill="x")
        count_row = tk.Frame(row_box, bg=PANEL)
        count_row.pack(anchor="w")
        tk.Label(count_row, text="Number of pins:", font=BODY_FONT, fg=TEXT, bg=PANEL).pack(side="left")
        tk.Spinbox(
            count_row, from_=1, to=40, textvariable=self.pin_count,
            width=4, font=BODY_FONT, bg=BG, fg=TEXT, buttonbackground=PANEL,
        ).pack(side="left", padx=10)

        self.setup_error = tk.Label(frame, text="", font=BODY_FONT, fg="#ff8f8f", bg=BG)
        self.setup_error.pack()
        tk.Button(
            frame, text="Start game", font=HEADING_FONT, bg=ACCENT, fg=BG,
            activebackground="#ffc184", bd=0, padx=28, pady=10,
            command=self._start_game,
        ).pack(pady=(8, 30))

    def _build_game(self):
        frame = self.game_frame
        top = tk.Frame(frame, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 6))
        self.turn_label = tk.Label(top, text="", font=TURN_FONT, fg=TEXT, bg=BG)
        self.turn_label.pack(anchor="w")
        self.mode_label = tk.Label(top, text="", font=BODY_FONT, fg=MUTED, bg=BG)
        self.mode_label.pack(anchor="w")

        self.board_frame = tk.Frame(frame, bg=BG)
        self.board_frame.pack(fill="both", expand=True, padx=24, pady=10)

        bottom = tk.Frame(frame, bg=PANEL, padx=16, pady=12)
        bottom.pack(fill="x", padx=24, pady=(0, 18))
        self.selected_label = tk.Label(bottom, text="", font=BODY_FONT, fg=TEXT, bg=PANEL)
        self.selected_label.pack(side="left")
        self.take_button = tk.Button(
            bottom, text="Take pins", font=BODY_FONT, bg=ACCENT, fg=BG,
            activebackground="#ffc184", bd=0, padx=14, pady=4, command=self._take,
        )
        self.take_button.pack(side="left", padx=12)
        tk.Button(
            bottom, text="New game", font=BODY_FONT, bg=BG, fg=TEXT,
            activebackground=PANEL, bd=0, padx=12, pady=4, command=self._new_game,
        ).pack(side="left", padx=4)
        tk.Button(
            bottom, text="Change setup", font=BODY_FONT, bg=BG, fg=MUTED,
            activebackground=PANEL, bd=0, padx=12, pady=4, command=self._change_setup,
        ).pack(side="left", padx=4)

        self.message_label = tk.Label(frame, text="", font=BODY_FONT, fg=MUTED, bg=BG)
        self.message_label.pack(anchor="w", padx=26, pady=(0, 10))

    def _start_game(self):
        try:
            count = int(self.pin_count.get())
        except (ValueError, tk.TclError):
            count = 0
        if count < 1 or count > 40:
            self.setup_error.config(text="Number of pins must be between 1 and 40.")
            return
        self.setup_error.config(text="")
        self._cancel_pc()
        self.vs_pc = self.mode.get() == "pc"
        self.starting_pins = count
        self.board = [True] * count
        self.selection = []
        self.winner = None
        self.game_over = False
        self.first_turn = ("pc" if position_value(self.board) else "human") if self.vs_pc else "p1"
        self.message = self._start_message()
        self.turn = self.first_turn
        self.mode_label.config(
            text="Mode: Player vs Computer" if self.vs_pc else "Mode: Player vs Player"
        )
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self._refresh()
        if self.turn == "pc":
            self._schedule_pc()

    def _start_message(self):
        if self.first_turn == "pc":
            return "Computer plays first."
        return "You play first." if self.vs_pc else "Player 1 starts."

    def _cancel_pc(self):
        if self.pc_job is not None:
            self.root.after_cancel(self.pc_job)
            self.pc_job = None

    def _schedule_pc(self):
        self._cancel_pc()
        self.pc_job = self.root.after(700, self._pc_move)

    def _pc_move(self):
        self.pc_job = None
        if self.game_over or self.turn != "pc":
            return
        move = optimal_move(self.board)
        self.board = apply_move(self.board, move)
        self.message = f"Computer removed {describe(move)}."
        self._finish_turn("pc")
        self._refresh()

    def _take(self):
        if self.game_over or self.turn is None or self.turn == "pc":
            return
        if not legal_move(self.board, self.selection):
            self.message = "Select one pin or two neighbouring pins."
            self._refresh()
            return
        move = self.selection[:]
        self.board = apply_move(self.board, move)
        self.message = f"{self._name(self.turn)} removed {describe(move)}."
        mover = self.turn
        self._finish_turn(mover)
        self._refresh()
        if self.turn == "pc":
            self._schedule_pc()

    def _finish_turn(self, mover):
        if not any(self.board):
            self.game_over = True
            self.winner = mover
            self.turn = None
            self.selection = []
            return
        if self.vs_pc:
            self.turn = "human" if mover == "pc" else "pc"
        else:
            self.turn = "p2" if mover == "p1" else "p1"
        self.selection = []

    def _name(self, player):
        return {"p1": "Player 1", "p2": "Player 2", "pc": "Computer", "human": "You"}[player]

    def _select_pin(self, index):
        if (
            self.game_over
            or self.turn in (None, "pc")
            or index < 0
            or index >= len(self.board)
            or not self.board[index]
        ):
            return
        current = self.selection[:]
        if len(current) == 1:
            if index == current[0]:
                self.selection = []
            elif abs(index - current[0]) == 1:
                self.selection = [min(index, current[0]), max(index, current[0])]
            else:
                self.selection = [index]
        elif len(current) == 2:
            self.selection = [] if index in current else [index]
        else:
            self.selection = [index]
        self.message = ""
        self._refresh()

    def _on_canvas_click(self, event):
        origin, spacing = self.canvas_geometry
        index = round((event.x - origin) / spacing)
        self._select_pin(index)

    def _on_return(self, event):
        if self.game_frame.winfo_ismapped() and not self.game_over:
            self._take()

    def _refresh(self):
        if self.game_over:
            winner = "You win!" if self.winner == "human" else f"{self._name(self.winner)} wins!"
            self.turn_label.config(text=winner, fg=ACCENT)
        elif self.turn == "pc":
            self.turn_label.config(text="Computer's turn", fg=ACCENT)
        else:
            self.turn_label.config(text=f"{self._name(self.turn)}'s turn", fg=STONE_SELECTED)

        self._render_board()
        if len(self.selection) == 2:
            self.selected_label.config(text=f"Selected: pins {self.selection[0] + 1}–{self.selection[1] + 1}")
        elif self.selection:
            self.selected_label.config(text=f"Selected: pin {self.selection[0] + 1}")
        else:
            self.selected_label.config(text="Selected: none")
        human_turn = self.turn not in (None, "pc") and not self.game_over
        self.take_button.config(state="normal" if human_turn and legal_move(self.board, self.selection) else "disabled")
        if self.game_over:
            self.message = f"{self._name(self.winner)} took the last pin."
        self.message_label.config(text=self.message, fg=ACCENT if self.game_over else MUTED)

    def _render_board(self):
        for child in self.board_frame.winfo_children():
            child.destroy()
        canvas = tk.Canvas(self.board_frame, width=900, height=100, bg=BG, highlightthickness=0)
        count = len(self.board)
        spacing = min(30, 860 / count) if count else 30
        origin = (900 - (count - 1) * spacing) / 2
        self.canvas_geometry = (origin, spacing)
        for index, standing in enumerate(self.board):
            x = origin + index * spacing
            if standing:
                color = STONE_SELECTED if index in self.selection else STONE
                canvas.create_polygon(
                    [x - 8, 74, x - 5, 38, x + 5, 38, x + 8, 74], fill=color, outline=""
                )
                canvas.create_oval(x - 7, 22, x + 7, 40, fill=color, outline="")
                canvas.create_rectangle(x - 5, 44, x + 5, 49, fill=BAND, outline="")
            else:
                canvas.create_oval(x - 3, 51, x + 3, 57, fill=EMPTY, outline="")
        canvas.bind("<Button-1>", self._on_canvas_click)
        canvas.pack()
        tk.Label(
            self.board_frame,
            text=f"Pins standing: {sum(self.board)}",
            font=BODY_FONT,
            fg=MUTED,
            bg=BG,
        ).pack(pady=(4, 0))

    def _new_game(self):
        self._cancel_pc()
        self.board = [True] * self.starting_pins
        self.selection = []
        self.winner = None
        self.game_over = False
        self.message = self._start_message()
        self.turn = self.first_turn
        self._refresh()
        if self.turn == "pc":
            self._schedule_pc()

    def _change_setup(self):
        self._cancel_pc()
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)


def main():
    root = tk.Tk()
    KegleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
