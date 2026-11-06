"""WASD Chess.

A full chess game using tkinter.

Controls:
    WASD       Move the cursor.
    SPACE      Select a piece or make a move.
    Left click Select a piece or make a move.
    Right drag Draw an arrow; right click highlights a square.
    H          Toggle an engine hint.
    U          Undo the last move.
    V          Open game review.
    T          Toggle dark mode.
    R          Return to the menu.
"""

import random
import tkinter as tk
from tkinter import messagebox


SIZE = 80
MINI_SIZE = 48
BOARD_PIXELS = SIZE * 8
STATUS_HEIGHT = 50

UNICODE_BY_TYPE = {
    "K": "\u2654", "Q": "\u2655", "R": "\u2656",
    "B": "\u2657", "N": "\u2658", "P": "\u2659",
}
KNIGHT_OFFSETS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                  (1, -2), (1, 2), (2, -1), (2, 1)]
KING_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                (0, 1), (1, -1), (1, 0), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}

PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]
KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

MIN_ELO = 400
MAX_ELO = 3000
DEFAULT_ELO = 1500
REVIEW_DEPTH = 2
HINT_DEPTH = 3

LIGHT_THEME = {
    "bg": "#f0f0f0", "fg": "#000000", "panel_bg": "#f0f0f0",
    "board_light": "#EEEED2", "board_dark": "#769656",
    "canvas_bg": "white", "status_bg": "#222222", "status_fg": "white",
    "cursor": "#FFEB3B", "select": "#F44336", "move_dot": "#1E88E5",
    "arrow": "#15A22C", "highlight": "#E81E1E", "hint": "#8E24AA",
}
DARK_THEME = {
    "bg": "#1e1e1e", "fg": "#f0f0f0", "panel_bg": "#2a2a2a",
    "board_light": "#b7b7b7", "board_dark": "#4a4a4a",
    "canvas_bg": "#1e1e1e", "status_bg": "#000000", "status_fg": "#f0f0f0",
    "cursor": "#FFD54F", "select": "#EF5350", "move_dot": "#42A5F5",
    "arrow": "#2ECC71", "highlight": "#FF5252", "hint": "#BA68C8",
}

PUZZLES = [
    {
        "fen": "6k1/5ppp/8/8/8/8/8/4R2K", "side": "w",
        "solution": [((7, 4), (0, 4))], "title": "Back-Rank Mate",
        "desc": "White to move: deliver checkmate in one.",
    },
    {
        "fen": "r3k3/8/8/1N6/8/8/8/4K3", "side": "w",
        "solution": [((3, 1), (1, 2))], "title": "Family Fork",
        "desc": "White to move: fork the king and rook to win material.",
    },
    {
        "fen": "4k3/8/2n5/1B6/8/8/8/4K3", "side": "w",
        "solution": [((3, 1), (2, 2))], "title": "Win the Piece",
        "desc": "White to move: win a piece with check.",
    },
    {
        "fen": "7k/Q7/5K2/8/8/8/8/8", "side": "w",
        "solution": [((1, 0), (1, 6))], "title": "Queen Mate",
        "desc": "White to move: deliver checkmate in one.",
    },
    {
        "fen": "q3k3/8/8/8/8/N7/8/R6K", "side": "w",
        "solution": [((5, 0), (3, 1))], "title": "Discovered Attack",
        "desc": "White to move: uncover an attack on the queen.",
    },
]


def elo_to_params(elo):
    """Map Elo to search depth, blunder chance, and tolerance."""
    elo = max(MIN_ELO, min(MAX_ELO, elo))
    t = (elo - MIN_ELO) / (MAX_ELO - MIN_ELO)
    if elo < 800:
        depth = 1
    elif elo < 1400:
        depth = 2
    elif elo < 2100:
        depth = 3
    else:
        depth = 4
    return depth, 0.45 - 0.44 * t, 200 - 190 * t


def in_bounds(row, col):
    return 0 <= row < 8 and 0 <= col < 8


def is_white_piece(piece):
    return piece is not None and piece.isupper()


def same_color(piece1, piece2):
    return (piece1 is not None and piece2 is not None
            and is_white_piece(piece1) == is_white_piece(piece2))


def fen_to_board(fen_placement):
    board = []
    for row_string in fen_placement.split("/"):
        row = []
        for char in row_string:
            row.extend([None] * int(char) if char.isdigit() else [char])
        board.append(row)
    return board


class ChessGame:
    def __init__(self, root):
        self.root = root
        self.root.title("WASD Chess")
        self.root.resizable(False, False)
        self.canvas = None
        self.control_frame = None
        self.menu_frame = None
        self.dark_mode = False
        self.theme = LIGHT_THEME
        self.ai_vs_ai = False
        self.puzzle_mode = False
        self.bot_color = None
        self.bot_elo = DEFAULT_ELO
        self.white_elo = DEFAULT_ELO
        self.black_elo = DEFAULT_ELO
        self.ai_paused = False
        self.puzzle_index = 0
        self.puzzle_solution_moves = []
        self.puzzle_solved = False
        self.puzzle_attempts = 0
        self.elo_var = tk.IntVar(value=DEFAULT_ELO)
        self.white_elo_var = tk.IntVar(value=DEFAULT_ELO)
        self.black_elo_var = tk.IntVar(value=DEFAULT_ELO)
        self.root.configure(bg=self.theme["bg"])
        self.build_menu()

    def apply_widget_theme(self, widget):
        for option, value in (("bg", self.theme["panel_bg"]), ("fg", self.theme["fg"])):
            try:
                widget.configure(**{option: value})
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self.apply_widget_theme(child)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.theme = DARK_THEME if self.dark_mode else LIGHT_THEME
        self.root.configure(bg=self.theme["bg"])
        if self.canvas is not None:
            self.canvas.configure(bg=self.theme["canvas_bg"])
            self.draw()
        if self.control_frame is not None:
            self.apply_widget_theme(self.control_frame)
        if self.menu_frame is not None:
            self.apply_widget_theme(self.menu_frame)

    def build_menu(self):
        self.menu_frame = tk.Frame(self.root, padx=30, pady=20)
        self.menu_frame.pack()
        tk.Label(self.menu_frame, text="WASD Chess", font=("Arial", 22, "bold")).pack(pady=(0, 6))
        tk.Label(self.menu_frame, text="Move with WASD + Space, or just click with the mouse", font=("Arial", 10)).pack(pady=(0, 14))
        tk.Button(self.menu_frame, text="Two Player (Human vs Human)", width=34, command=self.start_two_player).pack(pady=4)
        tk.Frame(self.menu_frame, height=1, bg="#999999").pack(fill="x", pady=12)
        self.elo_label = tk.Label(self.menu_frame, text=f"Bot strength: {DEFAULT_ELO} Elo", font=("Arial", 11, "bold"))
        self.elo_label.pack()
        tk.Scale(self.menu_frame, from_=MIN_ELO, to=MAX_ELO, resolution=50, orient="horizontal", length=320, variable=self.elo_var, showvalue=False, command=self.on_elo_change).pack(pady=(2, 4))
        tk.Label(self.menu_frame, text="(weaker, shakier)   (stronger, more precise)", font=("Arial", 8)).pack(pady=(0, 10))
        tk.Button(self.menu_frame, text="Play vs Bot - I play White", width=34, command=lambda: self.start_vs_bot("w")).pack(pady=4)
        tk.Button(self.menu_frame, text="Play vs Bot - I play Black", width=34, command=lambda: self.start_vs_bot("b")).pack(pady=4)
        tk.Frame(self.menu_frame, height=1, bg="#999999").pack(fill="x", pady=12)
        tk.Label(self.menu_frame, text="AI vs AI - watch two bots play", font=("Arial", 11, "bold")).pack()
        self.white_elo_label = tk.Label(self.menu_frame, text=f"White bot: {DEFAULT_ELO} Elo", font=("Arial", 10))
        self.white_elo_label.pack(pady=(6, 0))
        tk.Scale(self.menu_frame, from_=MIN_ELO, to=MAX_ELO, resolution=50, orient="horizontal", length=320, variable=self.white_elo_var, showvalue=False, command=self.on_white_elo_change).pack()
        self.black_elo_label = tk.Label(self.menu_frame, text=f"Black bot: {DEFAULT_ELO} Elo", font=("Arial", 10))
        self.black_elo_label.pack(pady=(6, 0))
        tk.Scale(self.menu_frame, from_=MIN_ELO, to=MAX_ELO, resolution=50, orient="horizontal", length=320, variable=self.black_elo_var, showvalue=False, command=self.on_black_elo_change).pack(pady=(2, 8))
        tk.Button(self.menu_frame, text="Watch AI vs AI", width=34, command=self.start_ai_vs_ai).pack(pady=4)
        tk.Frame(self.menu_frame, height=1, bg="#999999").pack(fill="x", pady=12)
        tk.Button(self.menu_frame, text="Puzzle Mode", width=34, command=self.start_puzzle_mode).pack(pady=4)
        tk.Frame(self.menu_frame, height=1, bg="#999999").pack(fill="x", pady=12)
        tk.Button(self.menu_frame, text="Toggle Dark Mode (T)", width=34, command=self.toggle_dark_mode).pack(pady=(0, 2))
        self.root.bind("<KeyPress>", self.on_menu_key)
        self.apply_widget_theme(self.menu_frame)

    def on_menu_key(self, event):
        if event.keysym.lower() == "t":
            self.toggle_dark_mode()

    def on_elo_change(self, _value):
        self.elo_label.config(text=f"Bot strength: {self.elo_var.get()} Elo")

    def on_white_elo_change(self, _value):
        self.white_elo_label.config(text=f"White bot: {self.white_elo_var.get()} Elo")

    def on_black_elo_change(self, _value):
        self.black_elo_label.config(text=f"Black bot: {self.black_elo_var.get()} Elo")

    def start_two_player(self):
        self.ai_vs_ai = False
        self.puzzle_mode = False
        self.bot_color = None
        self._build_play_widgets()
        self.reset_game()
        self.draw()

    def start_vs_bot(self, human_color):
        self.ai_vs_ai = False
        self.puzzle_mode = False
        self.bot_color = "b" if human_color == "w" else "w"
        self.bot_elo = self.elo_var.get()
        self._build_play_widgets()
        self.reset_game()
        self.draw()
        self.maybe_bot_move()

    def start_ai_vs_ai(self):
        self.ai_vs_ai = True
        self.puzzle_mode = False
        self.bot_color = None
        self.white_elo = self.white_elo_var.get()
        self.black_elo = self.black_elo_var.get()
        self.ai_paused = False
        self._build_play_widgets()
        self.reset_game()
        self.draw()
        self.maybe_bot_move()

    def start_puzzle_mode(self):
        self.ai_vs_ai = False
        self.puzzle_mode = True
        self.bot_color = None
        self._build_play_widgets()
        self.load_puzzle(0)
        self.draw()

    def _build_play_widgets(self):
        if self.menu_frame is not None:
            self.menu_frame.destroy()
            self.menu_frame = None
        self.canvas = tk.Canvas(self.root, width=BOARD_PIXELS, height=BOARD_PIXELS + STATUS_HEIGHT, bg=self.theme["canvas_bg"], highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<ButtonPress-3>", self.on_right_press)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_release)
        self.control_frame = tk.Frame(self.root, pady=8)
        self.control_frame.pack()
        if self.puzzle_mode:
            buttons = [("Prev Puzzle (P)", 13, self.prev_puzzle), ("Next Puzzle (N)", 13, self.next_puzzle), ("Show Solution (S)", 15, self.show_puzzle_solution)]
        elif self.ai_vs_ai:
            buttons = [("Pause/Resume (P)", 16, self.toggle_pause), ("Step (N)", 8, self.step_once), ("Game Review (V)", 15, self.show_review)]
        else:
            buttons = [("Undo (U)", 9, self.on_undo_button), ("Hint (H)", 9, self.toggle_hint), ("Game Review (V)", 15, self.show_review)]
        for text, width, command in buttons:
            tk.Button(self.control_frame, text=text, width=width, command=command).pack(side="left", padx=3)
        tk.Button(self.control_frame, text="Menu (R)", width=9, command=self.return_to_menu).pack(side="left", padx=3)
        if not self.puzzle_mode and not self.ai_vs_ai:
            tk.Button(self.control_frame, text="Dark Mode (T)", width=15, command=self.toggle_dark_mode).pack(side="left", padx=3)
        self.root.bind("<KeyPress>", self.on_key)
        self.root.focus_set()
        self.apply_widget_theme(self.control_frame)

    def return_to_menu(self):
        if self.canvas is not None:
            self.canvas.destroy()
            self.canvas = None
        if self.control_frame is not None:
            self.control_frame.destroy()
            self.control_frame = None
        self.build_menu()

    def _init_shared_state(self):
        self.cursor = [7, 4]
        self.selected = None
        self.legal_targets = []
        self.bot_thinking = False
        self.history = []
        self.move_log = []
        self.arrows = []
        self.highlighted_squares = set()
        self.right_press_square = None
        self.hint_move = None

    def reset_game(self):
        self._init_shared_state()
        self.board = self.initial_board()
        self.turn = "w"
        self.game_over = False
        self.message = "White's turn"
        self.castling_rights = {key: False for key in (
            "w_king_moved", "w_rook_a_moved", "w_rook_h_moved",
            "b_king_moved", "b_rook_a_moved", "b_rook_h_moved")}
        self.en_passant_target = None

    def load_puzzle(self, idx):
        self._init_shared_state()
        puzzle = PUZZLES[idx]
        self.puzzle_index = idx
        self.board = fen_to_board(puzzle["fen"])
        self.turn = puzzle["side"]
        self.puzzle_solution_moves = puzzle["solution"]
        self.puzzle_solved = False
        self.puzzle_attempts = 0
        self.game_over = False
        self.castling_rights = {key: True for key in (
            "w_king_moved", "w_rook_a_moved", "w_rook_h_moved",
            "b_king_moved", "b_rook_a_moved", "b_rook_h_moved")}
        self.en_passant_target = None
        self.message = f"Puzzle {idx + 1}/{len(PUZZLES)}: {puzzle['title']} - {puzzle['desc']}"

    def initial_board(self):
        board = [[None] * 8 for _ in range(8)]
        back = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for col in range(8):
            board[0][col] = back[col].lower()
            board[1][col] = "p"
            board[6][col] = "P"
            board[7][col] = back[col]
        return board

    def get_next_en_passant_target(self, board, row, col, next_row, next_col, piece=None):
        piece = board[row][col] if piece is None else piece
        if piece is None or piece.upper() != "P" or col != next_col or abs(next_row - row) != 2:
            return None
        return ((row + next_row) // 2, col)

    def is_en_passant_move(self, board, row, col, next_row, next_col, en_passant_target=None):
        target = self.en_passant_target if en_passant_target is None else en_passant_target
        piece = board[row][col]
        if piece is None or piece.upper() != "P" or (next_row, next_col) != target or board[next_row][next_col] is not None or col == next_col:
            return False
        direction = -1 if is_white_piece(piece) else 1
        captured_row = next_row - direction
        if next_row - row != direction or not in_bounds(captured_row, next_col):
            return False
        captured = board[captured_row][next_col]
        return captured is not None and captured.upper() == "P" and is_white_piece(captured) != is_white_piece(piece)

    def pseudo_moves(self, board, row, col, en_passant_target=None):
        piece = board[row][col]
        if piece is None:
            return []
        target = self.en_passant_target if en_passant_target is None else en_passant_target
        kind = piece.upper()
        white = is_white_piece(piece)
        moves = []
        if kind == "P":
            direction = -1 if white else 1
            start_row = 6 if white else 1
            next_row = row + direction
            if in_bounds(next_row, col) and board[next_row][col] is None:
                moves.append((next_row, col))
                next_two = row + direction * 2
                if row == start_row and board[next_two][col] is None:
                    moves.append((next_two, col))
            for delta_col in (-1, 1):
                next_col = col + delta_col
                if not in_bounds(next_row, next_col):
                    continue
                target_piece = board[next_row][next_col]
                if target_piece is not None and not same_color(piece, target_piece):
                    moves.append((next_row, next_col))
                elif self.is_en_passant_move(board, row, col, next_row, next_col, target):
                    moves.append((next_row, next_col))
        elif kind == "N":
            for delta_row, delta_col in KNIGHT_OFFSETS:
                next_row, next_col = row + delta_row, col + delta_col
                if in_bounds(next_row, next_col) and not same_color(piece, board[next_row][next_col]):
                    moves.append((next_row, next_col))
        elif kind == "K":
            for delta_row, delta_col in KING_OFFSETS:
                next_row, next_col = row + delta_row, col + delta_col
                if in_bounds(next_row, next_col) and not same_color(piece, board[next_row][next_col]):
                    moves.append((next_row, next_col))
            moves.extend(self.castling_moves(board, row, col, white))
        else:
            directions = []
            if kind in ("R", "Q"):
                directions += ROOK_DIRS
            if kind in ("B", "Q"):
                directions += BISHOP_DIRS
            for delta_row, delta_col in directions:
                next_row, next_col = row + delta_row, col + delta_col
                while in_bounds(next_row, next_col):
                    if board[next_row][next_col] is None:
                        moves.append((next_row, next_col))
                    else:
                        if not same_color(piece, board[next_row][next_col]):
                            moves.append((next_row, next_col))
                        break
                    next_row += delta_row
                    next_col += delta_col
        return moves

    def castling_moves(self, board, row, col, white):
        if row != (7 if white else 0) or col != 4:
            return []
        expected = "K" if white else "k"
        if board[row][4] != expected:
            return []
        king_key = "w_king_moved" if white else "b_king_moved"
        if self.castling_rights[king_key] or self.is_square_attacked(board, row, 4, not white):
            return []
        rook = "R" if white else "r"
        moves = []
        rook_key = "w_rook_h_moved" if white else "b_rook_h_moved"
        if not self.castling_rights[rook_key] and board[row][7] == rook and board[row][5] is None and board[row][6] is None and not self.is_square_attacked(board, row, 5, not white) and not self.is_square_attacked(board, row, 6, not white):
            moves.append((row, 6))
        rook_key = "w_rook_a_moved" if white else "b_rook_a_moved"
        if not self.castling_rights[rook_key] and board[row][0] == rook and board[row][1] is None and board[row][2] is None and board[row][3] is None and not self.is_square_attacked(board, row, 3, not white) and not self.is_square_attacked(board, row, 2, not white):
            moves.append((row, 2))
        return moves

    def find_king(self, board, white):
        king = "K" if white else "k"
        for row in range(8):
            for col in range(8):
                if board[row][col] == king:
                    return row, col
        return None

    def is_square_attacked(self, board, row, col, by_white):
        direction = 1 if by_white else -1
        for delta_col in (-1, 1):
            pawn_row, pawn_col = row + direction, col + delta_col
            if in_bounds(pawn_row, pawn_col):
                piece = board[pawn_row][pawn_col]
                if piece is not None and piece.upper() == "P" and is_white_piece(piece) == by_white:
                    return True
        for delta_row, delta_col in KNIGHT_OFFSETS + KING_OFFSETS:
            attack_row, attack_col = row + delta_row, col + delta_col
            if in_bounds(attack_row, attack_col):
                piece = board[attack_row][attack_col]
                if piece is not None and is_white_piece(piece) == by_white:
                    if (abs(delta_row), abs(delta_col)) in ((1, 2), (2, 1)) and piece.upper() == "N":
                        return True
                    if max(abs(delta_row), abs(delta_col)) == 1 and piece.upper() == "K":
                        return True
        for directions, pieces in ((ROOK_DIRS, ("R", "Q")), (BISHOP_DIRS, ("B", "Q"))):
            for delta_row, delta_col in directions:
                attack_row, attack_col = row + delta_row, col + delta_col
                while in_bounds(attack_row, attack_col):
                    piece = board[attack_row][attack_col]
                    if piece is not None:
                        if is_white_piece(piece) == by_white and piece.upper() in pieces:
                            return True
                        break
                    attack_row += delta_row
                    attack_col += delta_col
        return False

    def apply_move_copy(self, board, row, col, next_row, next_col, en_passant_target=None):
        target = self.en_passant_target if en_passant_target is None else en_passant_target
        new_board = [current[:] for current in board]
        piece = new_board[row][col]
        if self.is_en_passant_move(board, row, col, next_row, next_col, target):
            direction = -1 if is_white_piece(piece) else 1
            new_board[next_row - direction][next_col] = None
        new_board[next_row][next_col] = piece
        new_board[row][col] = None
        if piece.upper() == "K" and abs(next_col - col) == 2:
            rook_col, new_rook_col = (7, 5) if next_col == 6 else (0, 3)
            new_board[row][new_rook_col] = new_board[row][rook_col]
            new_board[row][rook_col] = None
        if piece == "P" and next_row == 0:
            new_board[next_row][next_col] = "Q"
        elif piece == "p" and next_row == 7:
            new_board[next_row][next_col] = "q"
        return new_board

    def legal_moves(self, board, row, col, en_passant_target=None):
        piece = board[row][col]
        if piece is None:
            return []
        target = self.en_passant_target if en_passant_target is None else en_passant_target
        result = []
        for next_row, next_col in self.pseudo_moves(board, row, col, target):
            new_board = self.apply_move_copy(board, row, col, next_row, next_col, target)
            king = self.find_king(new_board, is_white_piece(piece))
            if king is None or not self.is_square_attacked(new_board, king[0], king[1], not is_white_piece(piece)):
                result.append((next_row, next_col))
        return result

    def all_legal_moves(self, board, white, en_passant_target=None):
        target = self.en_passant_target if en_passant_target is None else en_passant_target
        return [((row, col), move) for row in range(8) for col in range(8)
                if board[row][col] is not None and is_white_piece(board[row][col]) == white
                for move in self.legal_moves(board, row, col, target)]

    def order_moves(self, board, moves):
        def priority(move):
            (row, col), (next_row, next_col) = move
            target = board[next_row][next_col]
            score = PIECE_VALUES[target.upper()] if target else 0
            piece = board[row][col]
            if piece and piece.upper() == "P" and target is None and col != next_col:
                score += PIECE_VALUES["P"]
            return -score
        return sorted(moves, key=priority)

    def update_castling_rights(self, row, col, next_row, next_col, piece):
        if piece == "K":
            self.castling_rights["w_king_moved"] = True
        elif piece == "k":
            self.castling_rights["b_king_moved"] = True
        corners = {(7, 0): "w_rook_a_moved", (7, 7): "w_rook_h_moved", (0, 0): "b_rook_a_moved", (0, 7): "b_rook_h_moved"}
        if (row, col) in corners:
            self.castling_rights[corners[(row, col)]] = True
        if (next_row, next_col) in corners:
            self.castling_rights[corners[(next_row, next_col)]] = True

    def make_move(self, row, col, next_row, next_col):
        piece = self.board[row][col]
        if piece is None:
            return
        old_target = self.en_passant_target
        self.history.append({"board": [line[:] for line in self.board], "turn": self.turn, "castling": dict(self.castling_rights), "en_passant_target": old_target})
        self.move_log.append({"color": "w" if is_white_piece(piece) else "b", "board_before": [line[:] for line in self.board], "from": (row, col), "to": (next_row, next_col)})
        self.update_castling_rights(row, col, next_row, next_col, piece)
        self.board = self.apply_move_copy(self.board, row, col, next_row, next_col, old_target)
        self.en_passant_target = self.get_next_en_passant_target(self.move_log[-1]["board_before"], row, col, next_row, next_col, piece)
        self.turn = "b" if self.turn == "w" else "w"
        self.selected = None
        self.legal_targets = []
        self.arrows = []
        self.highlighted_squares = set()
        self.hint_move = None
        self.check_game_state()

    def check_game_state(self):
        white = self.turn == "w"
        king = self.find_king(self.board, white)
        in_check = king is not None and self.is_square_attacked(self.board, king[0], king[1], not white)
        moves = self.all_legal_moves(self.board, white, self.en_passant_target)
        who = "White" if white else "Black"
        if not moves:
            self.game_over = True
            self.message = (f"Checkmate! {'Black' if white else 'White'} wins. Press V for review, R for menu." if in_check else "Stalemate! Draw. Press V for review, R for menu.")
        else:
            self.game_over = False
            self.message = f"{who} is in CHECK - {who}'s turn" if in_check else f"{who}'s turn"

    def undo_move(self):
        if not self.history:
            return
        steps = 2 if self.bot_color is not None and len(self.history) >= 2 else 1
        target = self.history[-steps]
        self.board = [line[:] for line in target["board"]]
        self.turn = target["turn"]
        self.castling_rights = dict(target["castling"])
        self.en_passant_target = target["en_passant_target"]
        del self.history[-steps:]
        del self.move_log[-steps:]
        self.selected = None
        self.legal_targets = []
        self.game_over = False
        self.check_game_state()

    def on_undo_button(self):
        if not self.bot_thinking:
            self.undo_move()
            self.draw()

    def attempt_puzzle_move(self, row, col, next_row, next_col):
        if ((row, col), (next_row, next_col)) in self.puzzle_solution_moves:
            self.make_move(row, col, next_row, next_col)
            self.puzzle_solved = True
            self.message = f'Correct! "{PUZZLES[self.puzzle_index]["title"]}" solved. Press N for the next puzzle.'
        else:
            self.selected = None
            self.legal_targets = []
            self.puzzle_attempts += 1
            self.message = f"Not quite - try again. (attempt {self.puzzle_attempts})"

    def next_puzzle(self):
        if self.puzzle_index < len(PUZZLES) - 1:
            self.load_puzzle(self.puzzle_index + 1)
        else:
            self.message = "You've completed all the puzzles! Press R for the menu."
        self.draw()

    def prev_puzzle(self):
        if self.puzzle_index > 0:
            self.load_puzzle(self.puzzle_index - 1)
        self.draw()

    def show_puzzle_solution(self):
        files = "abcdefgh"
        (row, col), (next_row, next_col) = self.puzzle_solution_moves[0]
        self.message = f"Solution: {files[col]}{8 - row}{files[next_col]}{8 - next_row}. Press N for the next puzzle."
        self.draw()

    def toggle_hint(self):
        self.hint_move = None if self.hint_move else self.compute_hint()
        self.draw()

    def compute_hint(self):
        if not self.human_can_act():
            return None
        moves = self.order_moves(self.board, self.all_legal_moves(self.board, self.turn == "w", self.en_passant_target))
        if not moves:
            return None
        return moves[0]

    def evaluate(self, board):
        score = 0
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece is None:
                    continue
                value = PIECE_VALUES[piece.upper()]
                if piece.upper() == "P":
                    value += PAWN_TABLE[row if piece.isupper() else 7 - row][col]
                elif piece.upper() == "N":
                    value += KNIGHT_TABLE[row if piece.isupper() else 7 - row][col]
                score += value if piece.isupper() else -value
        return score

    def choose_bot_move(self, color, elo):
        moves = self.all_legal_moves(self.board, color == "w", self.en_passant_target)
        if not moves:
            return None
        if random.random() < elo_to_params(elo)[1]:
            return random.choice(moves)
        return self.order_moves(self.board, moves)[0]

    def maybe_bot_move(self):
        if self.game_over or (self.ai_vs_ai and self.ai_paused):
            return
        if self.ai_vs_ai:
            elo = self.white_elo if self.turn == "w" else self.black_elo
            self.bot_thinking = True
            self.root.after(400, lambda: self.bot_move(self.turn, elo))
        elif self.bot_color == self.turn:
            self.bot_thinking = True
            self.root.after(250, lambda: self.bot_move(self.bot_color, self.bot_elo))

    def bot_move(self, color, elo):
        if self.game_over or (not self.ai_vs_ai and self.bot_color != color) or self.turn != color:
            self.bot_thinking = False
            return
        move = self.choose_bot_move(color, elo)
        if move:
            (row, col), (next_row, next_col) = move
            self.make_move(row, col, next_row, next_col)
        self.bot_thinking = False
        self.draw()
        self.maybe_bot_move()

    def toggle_pause(self):
        self.ai_paused = not self.ai_paused
        if not self.ai_paused:
            self.maybe_bot_move()
        self.draw()

    def step_once(self):
        if not self.game_over and self.ai_vs_ai:
            move = self.choose_bot_move(self.turn, self.white_elo if self.turn == "w" else self.black_elo)
            if move:
                (row, col), (next_row, next_col) = move
                self.make_move(row, col, next_row, next_col)
            self.draw()

    def show_review(self):
        messagebox.showinfo("Game Review", f"Moves played: {len(self.move_log)}")

    def human_can_act(self):
        return not self.ai_vs_ai and not self.game_over and not self.bot_thinking and self.turn != self.bot_color

    def on_key(self, event):
        key = event.keysym.lower()
        if key == "t":
            self.toggle_dark_mode()
        elif self.ai_vs_ai and key == "p":
            self.toggle_pause()
        elif self.ai_vs_ai and key == "n":
            self.step_once()
        elif self.puzzle_mode and key == "p":
            self.prev_puzzle()
        elif self.puzzle_mode and key == "n":
            self.next_puzzle()
        elif self.puzzle_mode and key == "s":
            self.show_puzzle_solution()
        elif key == "v":
            self.show_review()
        elif key == "u" and not self.ai_vs_ai and not self.puzzle_mode:
            self.undo_move()
            self.draw()
        elif key == "h" and not self.ai_vs_ai and not self.puzzle_mode:
            self.toggle_hint()
        elif key == "r":
            self.return_to_menu()
        elif self.human_can_act():
            row, col = self.cursor
            if key == "w": self.cursor[0] = max(0, row - 1)
            elif key == "s": self.cursor[0] = min(7, row + 1)
            elif key == "a": self.cursor[1] = max(0, col - 1)
            elif key == "d": self.cursor[1] = min(7, col + 1)
            elif key == "space": self.handle_select()
            elif key == "escape": self.selected = None; self.legal_targets = []
            self.draw()
            self.maybe_bot_move()

    def on_click(self, event):
        if not self.human_can_act() or not (0 <= event.x < BOARD_PIXELS and 0 <= event.y < BOARD_PIXELS):
            return
        self.cursor = [event.y // SIZE, event.x // SIZE]
        self.handle_select()
        self.draw()
        self.maybe_bot_move()

    def handle_select(self):
        row, col = self.cursor
        piece = self.board[row][col]
        if self.selected is None:
            if piece is not None and is_white_piece(piece) == (self.turn == "w"):
                self.selected = (row, col)
                self.legal_targets = self.legal_moves(self.board, row, col, self.en_passant_target)
            return
        start_row, start_col = self.selected
        if (row, col) in self.legal_targets:
            if self.puzzle_mode:
                self.attempt_puzzle_move(start_row, start_col, row, col)
            else:
                self.make_move(start_row, start_col, row, col)
        elif piece is not None and is_white_piece(piece) == (self.turn == "w"):
            self.selected = (row, col)
            self.legal_targets = self.legal_moves(self.board, row, col, self.en_passant_target)
        else:
            self.selected = None
            self.legal_targets = []

    def on_right_press(self, event):
        if 0 <= event.x < BOARD_PIXELS and 0 <= event.y < BOARD_PIXELS:
            self.right_press_square = (event.y // SIZE, event.x // SIZE)
        else:
            self.right_press_square = None

    def on_right_release(self, event):
        start = self.right_press_square
        self.right_press_square = None
        if start is None or not (0 <= event.x < BOARD_PIXELS and 0 <= event.y < BOARD_PIXELS):
            return
        end = (event.y // SIZE, event.x // SIZE)
        if start == end:
            if start in self.highlighted_squares:
                self.highlighted_squares.remove(start)
            else:
                self.highlighted_squares.add(start)
        else:
            arrow = (start, end)
            if arrow in self.arrows:
                self.arrows.remove(arrow)
            else:
                self.arrows.append(arrow)
        self.draw()

    def draw_piece(self, x, y, piece):
        symbol = UNICODE_BY_TYPE[piece.upper()]
        white = is_white_piece(piece)
        main_fill = "#FFFFFF" if white else "#101010"
        outline_fill = "#101010" if white else "#FFFFFF"
        for delta_x, delta_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.canvas.create_text(x + delta_x, y + delta_y, text=symbol, font=("Arial", SIZE - 20), fill=outline_fill)
        self.canvas.create_text(x, y, text=symbol, font=("Arial", SIZE - 20), fill=main_fill)

    def square_center(self, row, col):
        return col * SIZE + SIZE // 2, row * SIZE + SIZE // 2

    def draw_arrow(self, start, end, color, dashed=False):
        x1, y1 = self.square_center(*start)
        x2, y2 = self.square_center(*end)
        options = {"fill": color, "width": 6, "arrow": "last", "arrowshape": (16, 20, 7), "capstyle": "round"}
        if dashed:
            options["dash"] = (8, 5)
        self.canvas.create_line(x1, y1, x2, y2, **options)

    def draw(self):
        if self.canvas is None:
            return
        theme = self.theme
        self.canvas.delete("all")
        for row in range(8):
            for col in range(8):
                x0, y0 = col * SIZE, row * SIZE
                color = theme["board_light"] if (row + col) % 2 == 0 else theme["board_dark"]
                self.canvas.create_rectangle(x0, y0, x0 + SIZE, y0 + SIZE, fill=color, outline="")
                if (row, col) in self.highlighted_squares:
                    self.canvas.create_rectangle(x0, y0, x0 + SIZE, y0 + SIZE, fill=theme["highlight"], stipple="gray50", outline="")
                if self.selected == (row, col):
                    self.canvas.create_rectangle(x0 + 3, y0 + 3, x0 + SIZE - 3, y0 + SIZE - 3, outline=theme["select"], width=4)
                if (row, col) in self.legal_targets:
                    center_x, center_y = self.square_center(row, col)
                    self.canvas.create_oval(center_x - 12, center_y - 12, center_x + 12, center_y + 12, fill=theme["move_dot"], outline="")
                if self.board[row][col]:
                    self.draw_piece(x0 + SIZE // 2, y0 + SIZE // 2, self.board[row][col])
        for start, end in self.arrows:
            self.draw_arrow(start, end, theme["arrow"])
        if self.hint_move:
            self.draw_arrow(self.hint_move[0], self.hint_move[1], theme["hint"], dashed=True)
        row, col = self.cursor
        self.canvas.create_rectangle(col * SIZE + 2, row * SIZE + 2, col * SIZE + SIZE - 2, row * SIZE + SIZE - 2, outline=theme["cursor"], width=4)
        self.canvas.create_rectangle(0, BOARD_PIXELS, BOARD_PIXELS, BOARD_PIXELS + STATUS_HEIGHT, fill=theme["status_bg"], outline="")
        self.canvas.create_text(10, BOARD_PIXELS + STATUS_HEIGHT // 2, anchor="w", text=self.message, fill=theme["status_fg"], font=("Arial", 13, "bold"))
        self.canvas.update_idletasks()


def main():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        if "no display name" in str(error) or "DISPLAY" in str(error):
            raise SystemExit(
                "WASD Chess needs a graphical display. Run it on your desktop "
                "Python installation, or set DISPLAY before launching it."
            ) from None
        raise
    ChessGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
