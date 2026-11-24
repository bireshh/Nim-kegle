import os
import sys
from pathlib import Path

DEPS_ROOT = Path(__file__).resolve().parent / ".deps" / "usr"
PY_DIR = DEPS_ROOT / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"


def bootstrap_tkinter():
    if os.environ.get("NIM_LOCAL_TK") == "1":
        raise RuntimeError("Local tkinter installation could not be loaded")
    env = os.environ.copy()
    env["NIM_LOCAL_TK"] = "1"
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
    from tkinter import ttk
except ImportError:
    bootstrap_tkinter()

BG = "#171821"
PANEL = "#22243a"
ACCENT = "#f2a65a"
TEXT = "#f5f3ef"
MUTED = "#a6a9c2"
STONE = "#f2a65a"
STONE_SELECTED = "#7ee2c0"

TITLE_FONT = ("DejaVu Sans", 38, "bold")
HEADING_FONT = ("DejaVu Sans", 18, "bold")
BODY_FONT = ("DejaVu Sans", 13)
TURN_FONT = ("DejaVu Sans", 24, "bold")


def nim_sum(piles):
    total = 0
    for pile in piles:
        total ^= pile
    return total


def winning_move(piles):
    total = nim_sum(piles)
    if total:
        for index, count in enumerate(piles):
            target = count ^ total
            if target < count:
                return index, count - target
    index = max(range(len(piles)), key=lambda i: piles[i])
    return index, 1


class NimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nim")
        self.root.geometry("980x680")
        self.root.minsize(760, 560)
        self.root.configure(bg=BG)

        self.mode = tk.StringVar(value="pc")
        self.pile_count = tk.IntVar(value=3)
        self.pile_vars = []
        self.piles = []
        self.selected = None
        self.turn = None
        self.first_turn = "p1"
        self.winner = None
        self.vs_pc = False
        self.game_over = False
        self.message = ""
        self.amount = tk.IntVar(value=1)
        self.pc_job = None

        self.setup_frame = tk.Frame(root, bg=BG)
        self.game_frame = tk.Frame(root, bg=BG)
        self._build_setup()
        self._build_game()
        self.setup_frame.pack(fill="both", expand=True)
        self.root.bind("<Return>", self._on_return)

    def _build_setup(self):
        frame = self.setup_frame
        tk.Label(frame, text="NIM", font=TITLE_FONT, fg=ACCENT, bg=BG).pack(pady=(30, 4))
        tk.Label(
            frame,
            text="Remove stones from one pile. Whoever takes the last stone wins.",
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

        piles_box = tk.LabelFrame(
            frame, text="Starting position", font=HEADING_FONT, fg=TEXT, bg=PANEL,
            padx=18, pady=14, bd=0,
        )
        piles_box.pack(padx=40, pady=18, fill="x")
        count_row = tk.Frame(piles_box, bg=PANEL)
        count_row.pack(anchor="w")
        tk.Label(count_row, text="Number of piles:", font=BODY_FONT, fg=TEXT, bg=PANEL).pack(side="left")
        count_spin = tk.Spinbox(
            count_row, from_=1, to=8, textvariable=self.pile_count,
            width=4, font=BODY_FONT, bg=BG, fg=TEXT, buttonbackground=PANEL,
            command=self._build_pile_inputs,
        )
        count_spin.pack(side="left", padx=10)
        self.pile_inputs = tk.Frame(piles_box, bg=PANEL)
        self.pile_inputs.pack(anchor="w", pady=12)
        self._build_pile_inputs()

        self.setup_error = tk.Label(frame, text="", font=BODY_FONT, fg="#ff8f8f", bg=BG)
        self.setup_error.pack()
        tk.Button(
            frame, text="Start game", font=HEADING_FONT, bg=ACCENT, fg=BG,
            activebackground="#ffc184", bd=0, padx=28, pady=10,
            command=self._start_game,
        ).pack(pady=(8, 30))

    def _build_pile_inputs(self):
        for child in self.pile_inputs.winfo_children():
            child.destroy()
        self.pile_vars = []
        defaults = [3, 4, 5, 3, 4, 5, 3, 4]
        try:
            count = max(1, min(8, int(self.pile_count.get())))
        except (ValueError, tk.TclError):
            count = 3
        for index in range(count):
            cell = tk.Frame(self.pile_inputs, bg=PANEL)
            cell.grid(row=index // 4, column=index % 4, padx=10, pady=6)
            tk.Label(cell, text=f"Pile {index + 1}", font=BODY_FONT, fg=MUTED, bg=PANEL).pack()
            value = tk.IntVar(value=defaults[index])
            spin = tk.Spinbox(
                cell, from_=1, to=40, textvariable=value, width=5,
                font=BODY_FONT, bg=BG, fg=TEXT, buttonbackground=PANEL,
            )
            spin.pack(pady=(2, 0))
            self.pile_vars.append(value)

    def _build_game(self):
        frame = self.game_frame
        top = tk.Frame(frame, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 6))
        self.turn_label = tk.Label(top, text="", font=TURN_FONT, fg=TEXT, bg=BG)
        self.turn_label.pack(anchor="w")
        self.mode_label = tk.Label(top, text="", font=BODY_FONT, fg=MUTED, bg=BG)
        self.mode_label.pack(anchor="w")

        self.board = tk.Frame(frame, bg=BG)
        self.board.pack(fill="both", expand=True, padx=24, pady=10)

        bottom = tk.Frame(frame, bg=PANEL, padx=16, pady=12)
        bottom.pack(fill="x", padx=24, pady=(0, 18))
        self.selected_label = tk.Label(bottom, text="", font=BODY_FONT, fg=TEXT, bg=PANEL)
        self.selected_label.pack(side="left")
        tk.Label(bottom, text="Take:", font=BODY_FONT, fg=TEXT, bg=PANEL).pack(side="left", padx=(18, 6))
        self.amount_spin = tk.Spinbox(
            bottom, from_=1, to=1, textvariable=self.amount, width=4,
            font=BODY_FONT, bg=BG, fg=TEXT, buttonbackground=PANEL,
        )
        self.amount_spin.pack(side="left")
        self.take_button = tk.Button(
            bottom, text="Take stones", font=BODY_FONT, bg=ACCENT, fg=BG,
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
            piles = [int(var.get()) for var in self.pile_vars]
        except (ValueError, tk.TclError):
            piles = []
        if not piles or any(count < 1 or count > 40 for count in piles):
            self.setup_error.config(text="Pile sizes must be whole numbers from 1 to 40.")
            return
        self.setup_error.config(text="")
        self._cancel_pc()
        self.vs_pc = self.mode.get() == "pc"
        self.piles = piles
        self.selected = None
        self.winner = None
        self.game_over = False
        self.first_turn = ("pc" if nim_sum(piles) else "human") if self.vs_pc else "p1"
        self.message = self._start_message()
        self.turn = self.first_turn
        self.amount.set(1)
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
        index, amount = winning_move(self.piles)
        self.piles[index] -= amount
        self.message = f"Computer took {amount} stone(s) from pile {index + 1}."
        self._finish_turn("pc")
        self._refresh()

    def _take(self):
        if self.game_over or self.turn is None or self.turn == "pc":
            return
        if self.selected is None:
            self.message = "Select a pile first."
            self._refresh()
            return
        try:
            amount = int(self.amount.get())
        except (ValueError, tk.TclError):
            amount = 0
        if amount < 1 or amount > self.piles[self.selected]:
            self.message = f"Choose between 1 and {self.piles[self.selected]} stones."
            self._refresh()
            return
        index = self.selected
        self.piles[index] -= amount
        self.message = f"{self._name(self.turn)} took {amount} stone(s) from pile {index + 1}."
        mover = self.turn
        self._finish_turn(mover)
        self._refresh()
        if self.turn == "pc":
            self._schedule_pc()

    def _finish_turn(self, mover):
        if not any(self.piles):
            self.game_over = True
            self.winner = mover
            self.turn = None
            self.selected = None
            return
        if self.vs_pc:
            self.turn = "human" if mover == "pc" else "pc"
        else:
            self.turn = "p2" if mover == "p1" else "p1"
        self.selected = None

    def _name(self, player):
        return {"p1": "Player 1", "p2": "Player 2", "pc": "Computer", "human": "You"}[player]

    def _select(self, index):
        if self.game_over or self.turn in (None, "pc") or self.piles[index] == 0:
            return
        self.selected = index
        self.amount.set(1)
        self.message = ""
        self._refresh()

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
        if self.selected is not None:
            self.selected_label.config(text=f"Selected: pile {self.selected + 1}")
            limit = self.piles[self.selected]
        else:
            self.selected_label.config(text="Selected: none")
            limit = 1
        self.amount_spin.config(to=limit)
        human_turn = self.turn not in (None, "pc") and not self.game_over
        self.take_button.config(state="normal" if human_turn else "disabled")
        self.amount_spin.config(state="normal" if human_turn else "disabled")
        if self.game_over:
            self.message = f"{self._name(self.winner)} took the last stone."
        self.message_label.config(text=self.message, fg=ACCENT if self.game_over else MUTED)

    def _render_board(self):
        for child in self.board.winfo_children():
            child.destroy()
        for index, count in enumerate(self.piles):
            row = tk.Frame(self.board, bg=BG)
            row.pack(fill="x", pady=3)
            active = index == self.selected
            button = tk.Button(
                row, text=f"Pile {index + 1}", width=10, font=BODY_FONT,
                bg=ACCENT if active else PANEL, fg=BG if active else TEXT,
                activebackground=ACCENT, bd=0, pady=6,
                state="disabled" if count == 0 or self.game_over else "normal",
                command=lambda i=index: self._select(i),
            )
            button.pack(side="left", padx=(0, 14))
            canvas = tk.Canvas(
                row, width=360, height=max(38, (count + 9) // 10 * 34 + 12),
                bg=BG, highlightthickness=0,
            )
            for stone in range(count):
                column, line = stone % 10, stone // 10
                x, y = 22 + column * 34, 20 + line * 34
                color = STONE_SELECTED if active else STONE
                canvas.create_oval(x - 11, y - 11, x + 11, y + 11, fill=color, outline="")
            canvas.bind("<Button-1>", lambda event, i=index: self._select(i))
            canvas.pack(side="left")
            tk.Label(
                row, text=f"{count} stone(s)", font=BODY_FONT,
                fg=ACCENT if active else MUTED, bg=BG,
            ).pack(side="left", padx=14)

    def _new_game(self):
        self._cancel_pc()
        self.selected = None
        self.winner = None
        self.game_over = False
        self.message = self._start_message()
        self.turn = self.first_turn
        self.amount.set(1)
        self._refresh()
        if self.turn == "pc":
            self._schedule_pc()

    def _change_setup(self):
        self._cancel_pc()
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)


def main():
    root = tk.Tk()
    NimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
