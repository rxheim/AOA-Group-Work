# Author: Raheim Burkett- 2210198
# Date: 2026-11-18
"""Interactive human-versus-computer Moldy Chocolate game.

Run with: python3 moldy_chocolate_game.py
Requires Python 3 with tkinter (included with most desktop Python installs).
"""

from functools import lru_cache
import tkinter as tk
from tkinter import messagebox, ttk


# -------------------- GAME-STRATEGY FUNCTIONS --------------------
# Determine whether the player whose turn it is can force a win.
@lru_cache(maxsize=None)
def is_winning_state(rows: int, cols: int, mold_row: int, mold_col: int) -> bool:
    """Return whether the player to move can force a win from this state.

    Coordinates are zero-based within the remaining rectangular piece. A move
    cuts along any internal grid line; the piece without the mold is eaten.
    The one-square mold piece is terminal and losing for the player to move.
    """
    # The last square contains the mold. The player forced to take it loses.
    if rows == 1 and cols == 1:
        return False

    # Try every horizontal cut. Only the side containing the mold remains.
    for cut in range(1, rows):
        child = (cut, cols, mold_row, mold_col) if mold_row < cut else (
            rows - cut, cols, mold_row - cut, mold_col
        )
        if not is_winning_state(*child):
            return True

    # Try every vertical cut and keep only the side containing the mold.
    for cut in range(1, cols):
        child = (rows, cut, mold_row, mold_col) if mold_col < cut else (
            rows, cols - cut, mold_row, mold_col - cut
        )
        if not is_winning_state(*child):
            return True

    # No cut can force a loss for the opponent, so this position is losing.
    return False


# List every legal cut and the smaller board it leaves behind.
def legal_moves(rows: int, cols: int, mold_row: int, mold_col: int):
    """Yield each cut label and the remaining board dimensions and mold position."""
    # Internal coordinates start at zero; labels shown to players start at one.
    # Horizontal cuts split the rows; keep whichever section contains the mold.
    for cut in range(1, rows):
        if mold_row < cut:
            yield (f"Horizontal cut after row {cut}", cut, cols, mold_row, mold_col)
        else:
            yield (f"Horizontal cut after row {cut}", rows - cut, cols,
                   mold_row - cut, mold_col)
    # Vertical cuts split the columns; keep whichever section contains the mold.
    for cut in range(1, cols):
        if mold_col < cut:
            yield (f"Vertical cut after column {cut}", rows, cut, mold_row, mold_col)
        else:
            yield (f"Vertical cut after column {cut}", rows, cols - cut,
                   mold_row, mold_col - cut)

# -------------------- GAME WINDOW AND INTERFACE --------------------
class MoldyChocolateApp:
    # Preferred size, in pixels, for one chocolate square.
    CELL = 54

    def __init__(self, root):
        # Keep the main window so later methods can update the interface.
        self.root = root
        root.title("Moldy Chocolate | Human vs Computer")

        root.minsize(700, 590)
        root.configure(bg="#f5f1e9")

        # Set shared fonts and colors used by the interface.
        style = ttk.Style(root)
        style.configure("Title.TLabel", font=("Helvetica", 20, "bold"),
                        background="#f5f1e9", foreground="#442b20")
        style.configure("Info.TLabel", font=("Helvetica", 11),
                        background="#f5f1e9", foreground="#453b35")
        style.configure("Move.TButton", font=("Helvetica", 10), padding=7)

        ttk.Label(root, text="MOLDY CHOCOLATE", style="Title.TLabel").pack(pady=(16, 4))
        ttk.Label(root, text="Make a cut. The chocolate without the mold is eaten.",
                  style="Info.TLabel").pack(pady=(0, 10))
    

        # Input controls let players choose board size and mold position.
        setup = ttk.LabelFrame(root, text="New game", padding=10)
        setup.pack(fill="x", padx=18, pady=4)
        self.rows_var = tk.IntVar(value=4)
        self.cols_var = tk.IntVar(value=5)
        self.mold_row_var = tk.IntVar(value=2)
        self.mold_col_var = tk.IntVar(value=3)
        fields = (("Rows", self.rows_var), ("Columns", self.cols_var),
                  ("Mold row", self.mold_row_var), ("Mold column", self.mold_col_var))
        for col, (label, var) in enumerate(fields):
            ttk.Label(setup, text=label).grid(row=0, column=col * 2, padx=(4, 3))
            ttk.Spinbox(setup, from_=1, to=12, width=4, textvariable=var).grid(
                row=0, column=col * 2 + 1, padx=(0, 10))
        ttk.Button(setup, text="Start game", command=self.start_game).grid(
            row=0, column=8, padx=6)

        # The status line, board drawing, move buttons, and game history.
        self.status_var = tk.StringVar(value="Choose a board and start a game.")
        ttk.Label(root, textvariable=self.status_var, style="Info.TLabel").pack(pady=8)

        self.board = tk.Canvas(root, width=500, height=310, bg="#fbf8f2",
                               highlightthickness=0)
        self.board.pack(padx=16, pady=6)

        moves_frame = ttk.LabelFrame(root, text="Your legal cuts", padding=8)
        moves_frame.pack(fill="x", padx=18, pady=5)
        self.moves_box = ttk.Frame(moves_frame)
        self.moves_box.pack(fill="x")

        history_frame = ttk.LabelFrame(root, text="Game progress", padding=8)
        history_frame.pack(fill="both", expand=True, padx=18, pady=(4, 14))
        self.history = tk.Listbox(history_frame, height=5, font=("Helvetica", 10),
                                  bg="#fffdf9", relief="flat")
        self.history.pack(fill="both", expand=True)

        # Track whether a game is running and whose turn is next.
        self.game_active = False
        self.turn = "human"
        self.start_game()
# Start Game Function
    # -------------------- START AND DRAW A GAME --------------------
    def start_game(self):
        # Read and validate values entered in the spin boxes.
        try:
            rows, cols = self.rows_var.get(), self.cols_var.get()
            mold_row, mold_col = self.mold_row_var.get(), self.mold_col_var.get()
        except (tk.TclError, ValueError):
            messagebox.showerror("Invalid board", "Enter whole-number board dimensions and mold coordinates.")
            return
        if not (1 <= rows <= 12 and 1 <= cols <= 12):
            messagebox.showerror("Invalid board", "Rows and columns must be between 1 and 12.")
            return
        if not (1 <= mold_row <= rows and 1 <= mold_col <= cols):
            messagebox.showerror("Invalid mold location",
                                 f"Mold row must be 1–{rows} and mold column 1–{cols}.")
            return

        # Save board dimensions. Convert mold coordinates to zero-based indexes.
        self.rows, self.cols = rows, cols
        self.mold_row, self.mold_col = mold_row - 1, mold_col - 1
        self.turn = "human"
        self.game_active = True
        self.history.delete(0, tk.END)
        self.history.insert(tk.END, f"New game: {rows} × {cols}; mold at row {mold_row}, column {mold_col}.")
        self.status_var.set("Your turn. Choose a horizontal or vertical cut.")
        self.draw_board()
        self.show_moves()
        # Reaching the mold square ends the game; the player making that cut loses.
        if rows == 1 and cols == 1:
            self.finish_game("human")
# Board 
    def draw_board(self):
        # Clear the old picture, then choose a cell size that fits the board.
        self.board.delete("all")
        cell = min(self.CELL, 480 // max(1, self.cols), 280 // max(1, self.rows))
        left, top = 250 - self.cols * cell / 2, 155 - self.rows * cell / 2
        self.board.configure(width=max(500, int(self.cols * cell + 20)),
                             height=max(310, int(self.rows * cell + 20)))
        # Draw each square, coloring the mold square differently.
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = left + c * cell, top + r * cell
                x2, y2 = x1 + cell, y1 + cell
                spoiled = (r == self.mold_row and c == self.mold_col)
                self.board.create_rectangle(x1, y1, x2, y2,
                    fill="#8a563e" if spoiled else ("#d9a066" if (r + c) % 2 == 0 else "#c98954"),
                    outline="#fff2d8", width=2)
                if spoiled:
                    self.board.create_text((x1+x2)/2, (y1+y2)/2, text="MOLD",
                                           fill="white", font=("Helvetica", max(8, cell // 7), "bold"))
        self.board.create_text(left - 12, top - 8, text="Rows and columns are numbered from 1",
                               anchor="sw", fill="#66564d", font=("Helvetica", 9))

    # -------------------- TURN AND MOVE HANDLING --------------------
    def show_moves(self):
        # Rebuild buttons so they match the current board.
        for widget in self.moves_box.winfo_children():
            widget.destroy()
        if not self.game_active or self.turn != "human":
            return
        for label, nr, nc, mr, mc in legal_moves(self.rows, self.cols,
                                                  self.mold_row, self.mold_col):
            ttk.Button(self.moves_box, text=label, style="Move.TButton",
                       command=lambda x=(label, nr, nc, mr, mc): self.make_move(*x)).pack(
                           side="left", padx=4, pady=3)

    def make_move(self, label, rows, cols, mold_row, mold_col, player="human"):
        # Ignore a click if the game has already ended.
        if not self.game_active:
            return
        self.rows, self.cols = rows, cols
        self.mold_row, self.mold_col = mold_row, mold_col
        who = "You" if player == "human" else "Computer"
        self.history.insert(tk.END, f"{who}: {label}. Remaining piece: {rows} × {cols}.")
        self.history.yview_moveto(1)
        self.draw_board()
        if rows == 1 and cols == 1:
            self.finish_game("computer" if player == "human" else "human")
            return
        if player == "human":
            self.turn = "computer"
            self.status_var.set("Computer is choosing a move…")
            self.show_moves()
            self.root.after(450, self.computer_move)
        else:
            self.turn = "human"
            self.status_var.set("Your turn. Choose a horizontal or vertical cut.")
            self.show_moves()

    def computer_move(self):
        # Stop if the game ended or it is no longer the computer's turn.
        if not self.game_active or self.turn != "computer":
            return
        moves = list(legal_moves(self.rows, self.cols, self.mold_row, self.mold_col))
        if not moves:
            self.finish_game("computer")
            return
        # Prefer a move that leaves the opponent in a losing position.
        # If none is available, take the first legal move.
        move = next((m for m in moves if not is_winning_state(*m[1:])), moves[0])
        self.make_move(*move, player="computer")

    def finish_game(self, loser):
        # Stop play and display who won and why.
        self.game_active = False
        winner = "Computer" if loser == "human" else "You"
        self.status_var.set(f"Game over: {winner} win! The player left with the mold loses.")
        self.history.insert(tk.END, f"{winner} win. The {loser} player is left with the mold and loses.")
        self.show_moves()



# -------------------- PROGRAM ENTRY POINT --------------------
def main():
    """Create the window, build the game, and start Tkinter event handling."""
    root = tk.Tk()
    MoldyChocolateApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
