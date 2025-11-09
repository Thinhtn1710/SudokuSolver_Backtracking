import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

from sudoku_utils import (
    Board,
    is_valid,
    read_board_from_file,
    write_board_to_file,
    find_empty,
)
from sudoku_solver import solve_sudoku

# ===== THEME =====
BG_MAIN = "#020817"

ACCENT = "#e11d48"
ACCENT_LIGHT = "#f472b6"
ACCENT_DARK = "#9f1239"

TEXT_PRIMARY = "#f9fafb"
TEXT_MUTED = "#9ca3af"

CARD_BG = "#020817"
CARD_BORDER = "#111827"

CELL_BG = "#ffffff"
CELL_FG = "#111827"
CELL_BORDER = "#d1d5db"
CELL_HL = "#fee2e2"

STATUS_OK = "#22c55e"
STATUS_ERR = "#f97316"
STATUS_NORMAL = "#6b7280"


class SudokuGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sudoku Solver - Backtracking")

        # scale + fullscreen linh hoạt
        self._init_window_and_scale()
        self.root.configure(bg=BG_MAIN)

        # core state
        self.entries: list[list[tk.Entry]] = [[None for _ in range(9)] for _ in range(9)]
        self.selected_cell: tuple[int, int] | None = None
        self.solve_info_label: tk.Label | None = None

        # file state
        self.current_input_file: str | None = None
        self.original_board: Board | None = None  # để Reload puzzle gốc

        # dropdown data
        self.input_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value="")
        self.input_files: list[str] = []
        self.output_files: list[str] = []

        # step-by-step state
        self.step_solver_running: bool = False
        self.step_gen = None
        self.step_delay_ms: int = 80  # tốc độ mô phỏng Backtracking

        self._build_header()
        self._build_main()
        self._build_toolbar()
        self._build_status()

        self.refresh_file_lists()

    # ========= WINDOW + SCALE =========
    def _init_window_and_scale(self) -> None:
        """
        Full màn hình theo độ phân giải hiện tại.
        Dùng hệ số scale S để mọi thứ cân trên 14", 16", FHD, 2K,...
        Baseline: 1600x900.
        """
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        try:
            self.root.state("zoomed")
            self.root.geometry(f"{sw}x{sh}+0+0")
        except tk.TclError:
            self.root.geometry(f"{sw}x{sh}+0+0")

        self.root.resizable(True, True)

        s = min(sw / 1600.0, sh / 900.0)
        self.S = max(0.8, min(s, 1.35))

        # Fonts
        self.F_TITLE = ("Segoe UI", int(26 * self.S), "bold")
        self.F_SUB = ("Segoe UI", int(9 * self.S))
        self.F_CARD_TITLE = ("Segoe UI", int(14 * self.S), "bold")
        self.F_TEXT = ("Segoe UI", int(9 * self.S))
        self.F_TEXT_B = ("Segoe UI", int(10 * self.S), "bold")
        self.F_NUMPAD = ("Segoe UI", int(10 * self.S), "bold")
        self.F_CELL = ("Segoe UI", int(20 * self.S), "bold")

        # Layout
        self.WRAP_SIDE = int(340 * self.S)
        self.WRAP_INFO = int(520 * self.S)
        self.PX = int(32 * self.S)
        self.SIDE_W = int(360 * self.S)

        # Grid metrics
        self.CELL_IPADX = int(8 * self.S)
        self.CELL_IPADY = int(6 * self.S)
        self.CELL_PAD_THIN = max(1, int(1 * self.S))
        self.CELL_PAD_THICK = max(3, int(3 * self.S))

    # ========= UI BUILDERS =========

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=BG_MAIN)
        header.pack(
            fill="x",
            padx=self.PX,
            pady=(int(18 * self.S), int(6 * self.S)),
        )

        grad = tk.Frame(header, bg=ACCENT, height=max(2, int(3 * self.S)))
        grad.pack(fill="x", side="top", pady=(0, int(10 * self.S)))

        title_row = tk.Frame(header, bg=BG_MAIN)
        title_row.pack(fill="x")

        title = tk.Label(
            title_row,
            text="Sudoku Solver",
            font=self.F_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        )
        title.pack(side="left")

        badge = tk.Label(
            title_row,
            text="Backtracking • Visual • Study Mode",
            font=("Segoe UI", int(9 * self.S), "bold"),
            fg=ACCENT_LIGHT,
            bg=BG_MAIN,
            padx=int(10 * self.S),
            pady=max(2, int(3 * self.S)),
        )
        badge.pack(side="left", padx=(int(12 * self.S), 0))

        subtitle = tk.Label(
            header,
            text="Bàn chơi Sudoku tối ưu hiển thị • Hỗ trợ file input/output • Mô phỏng Backtracking từng bước.",
            font=self.F_SUB,
            fg=TEXT_MUTED,
            bg=BG_MAIN,
        )
        subtitle.pack(anchor="w", pady=(int(4 * self.S), 0))

    def _build_main(self) -> None:
        wrapper = tk.Frame(self.root, bg=BG_MAIN)
        wrapper.pack(
            fill="both",
            expand=True,
            padx=self.PX,
            pady=(int(4 * self.S), int(8 * self.S)),
        )

        # LEFT: Play area
        play_card = tk.Frame(
            wrapper,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
        )
        play_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, int(18 * self.S)),
        )
        play_card.pack_propagate(False)

        play_header = tk.Frame(play_card, bg=CARD_BG)
        play_header.pack(
            fill="x",
            pady=(int(10 * self.S), int(4 * self.S)),
            padx=int(14 * self.S),
        )

        play_title = tk.Label(
            play_header,
            text="Bảng Sudoku 9×9",
            font=self.F_CARD_TITLE,
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        play_title.pack(side="left")

        play_hint = tk.Label(
            play_header,
            text="Tập trung chơi: nhập đề, dùng file, Solve hoặc Step-by-step.",
            font=self.F_SUB,
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        play_hint.pack(side="left", padx=(int(10 * self.S), 0))

        # Grid center
        self.grid_container = tk.Frame(play_card, bg=CARD_BG)
        self.grid_container.pack(pady=(int(6 * self.S), int(4 * self.S)))
        self._build_grid(self.grid_container)

        # Numpad + info
        self._build_numpad(play_card)
        self._build_play_info(play_card)

        # RIGHT: Help + Stats
        side_panel = tk.Frame(
            wrapper,
            bg=BG_MAIN,
            width=self.SIDE_W,
        )
        side_panel.pack(side="right", fill="y")
        side_panel.pack_propagate(False)

        self._build_help_panel(side_panel)

    def _build_grid(self, parent: tk.Frame) -> None:
        grid_frame = tk.Frame(parent, bg=CARD_BG)
        grid_frame.pack()

        for r in range(9):
            for c in range(9):
                pad_left = self.CELL_PAD_THICK if c in (0, 3, 6) else self.CELL_PAD_THIN
                pad_top = self.CELL_PAD_THICK if r in (0, 3, 6) else self.CELL_PAD_THIN
                pad_right = self.CELL_PAD_THICK if c == 8 else self.CELL_PAD_THIN
                pad_bottom = self.CELL_PAD_THICK if r == 8 else self.CELL_PAD_THIN

                e = tk.Entry(
                    grid_frame,
                    width=2,
                    justify="center",
                    font=self.F_CELL,
                    bg=CELL_BG,
                    fg=CELL_FG,
                    bd=0,
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=CELL_BORDER,
                    insertbackground=ACCENT,
                )
                e.grid(
                    row=r,
                    column=c,
                    padx=(pad_left, pad_right),
                    pady=(pad_top, pad_bottom),
                    ipadx=self.CELL_IPADX,
                    ipady=self.CELL_IPADY,
                )

                e.bind("<FocusIn>", lambda ev, rr=r, cc=c: self._on_cell_focus(rr, cc))
                self._bind_cell_navigation(e, r, c)
                e.bind(
                    "<KeyRelease>",
                    lambda ev, rr=r, cc=c: self._on_cell_key(ev, rr, cc),
                )

                self.entries[r][c] = e

    def _bind_cell_navigation(self, e: tk.Entry, r: int, c: int) -> None:
        def go(dr: int, dc: int):
            nr, nc = r + dr, c + dc
            nr = max(0, min(8, nr))
            nc = max(0, min(8, nc))
            self._focus_cell(nr, nc)
            return "break"

        e.bind("<Up>", lambda ev: go(-1, 0))
        e.bind("<Down>", lambda ev: go(1, 0))
        e.bind("<Left>", lambda ev: go(0, -1))
        e.bind("<Right>", lambda ev: go(0, 1))

    def _on_cell_key(self, event: tk.Event, r: int, c: int) -> None:
        """
        Giới hạn input: rỗng / 0 / '.' / 1-9. Khác -> xoá.
        Giữ mỗi ô chỉ 1 ký tự hợp lệ => UI sạch, tránh lỗi vặt.
        """
        e = self.entries[r][c]
        val = e.get().strip()

        if val == "":
            return

        if len(val) > 1:
            val = val[-1]

        if val in ("0", "."):
            e.delete(0, tk.END)
            return

        if not val.isdigit() or not (1 <= int(val) <= 9):
            e.delete(0, tk.END)
            return

        e.delete(0, tk.END)
        e.insert(0, val)

    def _build_numpad(self, parent: tk.Frame) -> None:
        pad_frame = tk.Frame(parent, bg=CARD_BG)
        pad_frame.pack(pady=(int(10 * self.S), int(2 * self.S)))

        info = tk.Label(
            pad_frame,
            text="Chọn ô rồi click số để nhập nhanh",
            font=self.F_SUB,
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        info.pack(anchor="center", pady=(0, int(4 * self.S)))

        row = tk.Frame(pad_frame, bg=CARD_BG)
        row.pack()

        def make_btn(text, cmd):
            return tk.Button(
                row,
                text=text,
                command=cmd,
                font=self.F_NUMPAD,
                fg=TEXT_PRIMARY,
                bg="#111827",
                activebackground=ACCENT,
                activeforeground=TEXT_PRIMARY,
                bd=0,
                relief="flat",
                padx=int(12 * self.S),
                pady=int(6 * self.S),
                cursor="hand2",
            )

        for n in range(1, 10):
            b = make_btn(str(n), lambda v=n: self._input_number(v))
            b.pack(side="left", padx=int(3 * self.S))

        erase_btn = tk.Button(
            pad_frame,
            text="Erase",
            command=self._erase_selected,
            font=self.F_SUB,
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
            activebackground=ACCENT_DARK,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=int(10 * self.S),
            pady=int(4 * self.S),
            relief="flat",
            cursor="hand2",
        )
        erase_btn.pack(pady=(int(4 * self.S), 0))

    def _build_play_info(self, parent: tk.Frame) -> None:
        info_frame = tk.Frame(parent, bg=CARD_BG)
        info_frame.pack(
            fill="x",
            pady=(int(6 * self.S), int(10 * self.S)),
            padx=int(14 * self.S),
        )

        label = tk.Label(
            info_frame,
            text="Thông tin lời giải:",
            font=self.F_TEXT_B,
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        label.pack(anchor="w")

        self.solve_info_label = tk.Label(
            info_frame,
            text="• Chưa giải. Nhập đề hoặc chọn file Input, sau đó nhấn Validate / Solve / Step.",
            font=self.F_TEXT,
            fg=TEXT_MUTED,
            bg=CARD_BG,
            justify="left",
            anchor="w",
            wraplength=self.WRAP_INFO,
        )
        self.solve_info_label.pack(anchor="w")

    def _build_help_panel(self, parent: tk.Frame) -> None:
        guide_card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
        )
        guide_card.pack(
            fill="both",
            pady=(int(4 * self.S), int(4 * self.S)),
            expand=True,
        )

        guide_inner = tk.Frame(guide_card, bg=CARD_BG)
        guide_inner.pack(
            padx=int(14 * self.S),
            pady=int(14 * self.S),
            fill="both",
            expand=True,
        )

        title = tk.Label(
            guide_inner,
            text="Hướng dẫn nhanh",
            font=self.F_CARD_TITLE,
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        title.pack(anchor="w", pady=(0, int(6 * self.S)))

        def add(text, bold=False, color=TEXT_MUTED, top=0, bottom=2):
            lbl = tk.Label(
                guide_inner,
                text=text,
                font=self.F_TEXT_B if bold else self.F_TEXT,
                fg=color,
                bg=CARD_BG,
                justify="left",
                anchor="w",
                wraplength=self.WRAP_SIDE,
            )
            lbl.pack(
                anchor="w",
                pady=(int(top * self.S), int(bottom * self.S)),
            )

        add("• Điền số 1–9, không trùng hàng / cột / khối 3×3.", bottom=3)
        add("• Validate: kiểm tra chi tiết lỗi trùng, tô đỏ ô sai.", bottom=3)
        add("• Solve: giải nhanh bằng Backtracking chuẩn.", bottom=2)
        add("• Step: mô phỏng Backtracking từng bước ngay trên lưới.", bottom=3)
        add("• Input/Output: chọn file .txt để chơi và xem kết quả.", bottom=6)

        btn_algo = tk.Button(
            guide_inner,
            text="Xem thuật toán Backtracking",
            command=self.show_backtracking_info,
            font=self.F_TEXT_B,
            fg=ACCENT_LIGHT,
            bg="#111827",
            activebackground=ACCENT,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=int(10 * self.S),
            pady=int(6 * self.S),
            relief="flat",
            cursor="hand2",
        )
        btn_algo.pack(anchor="w", pady=(0, int(8 * self.S)))

        self.stats_label = tk.Label(
            guide_inner,
            text="Stats: dùng GUI này để demo & luyện Sudoku.",
            font=self.F_TEXT,
            fg="#6b7280",
            bg=CARD_BG,
            justify="left",
            anchor="w",
            wraplength=self.WRAP_SIDE,
        )
        self.stats_label.pack(anchor="w", pady=(int(4 * self.S), 0))

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self.root, bg=BG_MAIN)
        bar.pack(fill="x", padx=self.PX, pady=(0, int(4 * self.S)))

        # Input
        tk.Label(
            bar,
            text="Input:",
            font=self.F_TEXT_B,
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        ).pack(side="left", padx=(0, int(6 * self.S)))

        self.input_menu = ttk.Combobox(
            bar,
            textvariable=self.input_var,
            state="readonly",
            width=int(20 * self.S),
        )
        self.input_menu.pack(side="left", padx=(0, int(4 * self.S)))

        tk.Button(
            bar,
            text="Load",
            command=self.load_from_selected_input,
            font=self.F_TEXT_B,
            fg=TEXT_PRIMARY,
            bg=ACCENT,
            activebackground=ACCENT_DARK,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=int(10 * self.S),
            pady=int(6 * self.S),
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(0, int(10 * self.S)), pady=int(6 * self.S))

        # Output
        tk.Label(
            bar,
            text="Output:",
            font=self.F_TEXT_B,
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        ).pack(side="left", padx=(0, int(6 * self.S)))

        self.output_menu = ttk.Combobox(
            bar,
            textvariable=self.output_var,
            state="readonly",
            width=int(20 * self.S),
        )
        self.output_menu.pack(side="left", padx=(0, int(4 * self.S)))

        tk.Button(
            bar,
            text="View",
            command=self.view_selected_output,
            font=self.F_TEXT_B,
            fg=TEXT_PRIMARY,
            bg="#111827",
            activebackground=ACCENT,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=int(8 * self.S),
            pady=int(6 * self.S),
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S))

        tk.Button(
            bar,
            text="Load to Grid",
            command=self.load_selected_output_to_grid,
            font=self.F_TEXT_B,
            fg=TEXT_PRIMARY,
            bg="#111827",
            activebackground=ACCENT,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=int(8 * self.S),
            pady=int(6 * self.S),
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(0, int(14 * self.S)), pady=int(6 * self.S))

        # Helper tạo nút nhỏ
        def small_btn(text, cmd, primary=False):
            return tk.Button(
                bar,
                text=text,
                command=cmd,
                font=self.F_TEXT_B,
                fg=TEXT_PRIMARY if primary else TEXT_MUTED,
                bg=ACCENT if primary else "#111827",
                activebackground=ACCENT_DARK if primary else "#1f2937",
                activeforeground=TEXT_PRIMARY,
                bd=0,
                padx=int(10 * self.S),
                pady=int(6 * self.S),
                relief="flat",
                cursor="hand2",
            )

        # Validate + Step + Reload puzzle
        small_btn("Validate", self.on_validate).pack(
            side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Step", self.on_step_solve).pack(
            side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Reload puzzle", self.reload_original_puzzle).pack(
            side="left", padx=(0, int(10 * self.S)), pady=int(6 * self.S)
        )

        # Open folders
        small_btn("Open input", self.open_input_folder).pack(
            side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Open output", self.open_output_folder).pack(
            side="left", padx=(0, int(12 * self.S)), pady=int(6 * self.S)
        )

        # Gameplay controls
        small_btn("Load Sample", self.load_sample).pack(
            side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Clear", self.on_clear).pack(
            side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Solve", self.on_solve, primary=True).pack(
            side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Exit", self.root.destroy).pack(
            side="right", padx=(int(6 * self.S), 0), pady=int(6 * self.S)
        )

    def _build_status(self) -> None:
        self.status_bar = tk.Label(
            self.root,
            text="Sẵn sàng.",
            font=self.F_TEXT,
            fg=STATUS_NORMAL,
            bg=BG_MAIN,
            anchor="w",
            padx=self.PX,
            pady=int(4 * self.S),
        )
        self.status_bar.pack(fill="x", side="bottom")

    # ========= BASIC HELPERS =========

    def _set_status(self, text: str, color: str = STATUS_NORMAL) -> None:
        self.status_bar.config(text=text, fg=color)

    def _set_solve_info(self, text: str, color: str = TEXT_MUTED) -> None:
        if self.solve_info_label is not None:
            self.solve_info_label.config(text=text, fg=color)

    def _reset_cell_colors(self) -> None:
        for r in range(9):
            for c in range(9):
                self.entries[r][c].config(
                    bg=CELL_BG,
                    fg=CELL_FG,
                    highlightbackground=CELL_BORDER,
                )

    def _focus_cell(self, r: int, c: int) -> None:
        r = max(0, min(8, r))
        c = max(0, min(8, c))
        e = self.entries[r][c]
        e.focus_set()
        self._on_cell_focus(r, c)

    def _on_cell_focus(self, r: int, c: int) -> None:
        self._reset_cell_colors()
        e = self.entries[r][c]
        e.config(bg=CELL_HL, fg=ACCENT_DARK, highlightbackground=ACCENT)
        self.selected_cell = (r, c)

    def _input_number(self, num: int) -> None:
        if self.selected_cell is None:
            return
        r, c = self.selected_cell
        e = self.entries[r][c]
        e.delete(0, tk.END)
        e.insert(0, str(num))

    def _erase_selected(self) -> None:
        if self.selected_cell is None:
            return
        r, c = self.selected_cell
        self.entries[r][c].delete(0, tk.END)

    # ========= BOARD DATA =========

    def get_board_from_entries(self) -> Board:
        board: Board = []
        for r in range(9):
            row = []
            for c in range(9):
                val = self.entries[r][c].get().strip()
                if val in ("", "0", "."):
                    row.append(0)
                elif val.isdigit() and 1 <= int(val) <= 9:
                    row.append(int(val))
                else:
                    raise ValueError(
                        f"Giá trị không hợp lệ tại ô ({r+1}, {c+1}). Chỉ nhập 1–9, 0 hoặc để trống."
                    )
            if len(row) != 9:
                raise ValueError("Mỗi hàng Sudoku phải có đúng 9 ô.")
            board.append(row)
        if len(board) != 9:
            raise ValueError("Bảng Sudoku phải có đúng 9 hàng.")
        return board

    def fill_entries_from_board(self, board: Board) -> None:
        self._reset_cell_colors()
        for r in range(9):
            for c in range(9):
                e = self.entries[r][c]
                e.delete(0, tk.END)
                if board[r][c] != 0:
                    e.insert(0, str(board[r][c]))

    # ========= VALIDATION =========

    def _check_initial_valid(self, board: Board, announce: bool = True) -> bool:
        """
        Kiểm tra đề ban đầu có vi phạm luật Sudoku không.
        Dùng chung cho Solve & Step.
        """
        for r in range(9):
            for c in range(9):
                num = board[r][c]
                if num != 0:
                    board[r][c] = 0
                    if not is_valid(board, r, c, num):
                        board[r][c] = num
                        if announce:
                            msg = f"Giá trị ban đầu không hợp lệ tại ô ({r+1}, {c+1})."
                            messagebox.showerror("Lỗi Sudoku", msg)
                            self._set_status("Sudoku ban đầu không hợp lệ.", STATUS_ERR)
                            self._set_solve_info(msg, STATUS_ERR)
                            self._mark_single_error(r, c)
                        return False
                    board[r][c] = num
        return True

    def _mark_single_error(self, r: int, c: int) -> None:
        self._reset_cell_colors()
        self.entries[r][c].config(
            bg="#fee2e2",
            fg=ACCENT_DARK,
            highlightbackground=ACCENT,
        )
        self._flash_board("#ffe4e6", CELL_BG, 4)
        self._shake_grid()

    def _collect_violations(self, board: Board):
        """
        Thu thập chi tiết lỗi: trùng hàng, cột, ô 3x3.
        Trả về (list_message, set_cells_invalid).
        """
        errors = []
        bad = set()

        # hàng
        for r in range(9):
            seen = {}
            for c in range(9):
                v = board[r][c]
                if v == 0:
                    continue
                if v in seen:
                    c2 = seen[v]
                    errors.append(
                        f"Trùng số {v} trên hàng {r+1} (cột {c2+1} và {c+1})."
                    )
                    bad.add((r, c))
                    bad.add((r, c2))
                else:
                    seen[v] = c

        # cột
        for c in range(9):
            seen = {}
            for r in range(9):
                v = board[r][c]
                if v == 0:
                    continue
                if v in seen:
                    r2 = seen[v]
                    errors.append(
                        f"Trùng số {v} trên cột {c+1} (hàng {r2+1} và {r+1})."
                    )
                    bad.add((r, c))
                    bad.add((r2, c))
                else:
                    seen[v] = r

        # box
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                seen = {}
                for dr in range(3):
                    for dc in range(3):
                        r = br + dr
                        c = bc + dc
                        v = board[r][c]
                        if v == 0:
                            continue
                        if v in seen:
                            r2, c2 = seen[v]
                            errors.append(
                                f"Trùng số {v} trong khối 3x3 tại hàng {br+1}-{br+3}, cột {bc+1}-{bc+3} "
                                f"({r2+1},{c2+1}) và ({r+1},{c+1})."
                            )
                            bad.add((r, c))
                            bad.add((r2, c2))
                        else:
                            seen[v] = (r, c)

        return errors, bad

    def on_validate(self) -> None:
        try:
            board = self.get_board_from_entries()
        except ValueError as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))
            self._set_status("Lỗi dữ liệu đầu vào.", STATUS_ERR)
            self._set_solve_info("Lỗi dữ liệu: kiểm tra lại các ô nhập.", STATUS_ERR)
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()
            return

        self._reset_cell_colors()
        errors, bad = self._collect_violations(board)

        if not errors:
            self._set_status("Board hiện tại hợp lệ theo luật Sudoku.", STATUS_OK)
            self._set_solve_info(
                "Board không vi phạm trùng hàng/cột/khối. Có thể nhấn Solve hoặc Step.",
                STATUS_OK,
            )
            messagebox.showinfo("Hợp lệ", "Board hiện tại hợp lệ theo luật Sudoku.")
        else:
            for (r, c) in bad:
                self.entries[r][c].config(
                    bg="#fee2e2",
                    fg=ACCENT_DARK,
                    highlightbackground=ACCENT,
                )
            msg = "Phát hiện một số lỗi:\n\n" + "\n".join(errors)
            messagebox.showerror("Board có lỗi", msg)
            self._set_status("Board có lỗi. Các ô đỏ vi phạm luật Sudoku.", STATUS_ERR)
            self._set_solve_info(
                "Board có lỗi. Xem thông báo & các ô đỏ để chỉnh lại.",
                STATUS_ERR,
            )
            self._shake_grid()

    # ========= STEP-BY-STEP BACKTRACKING =========

    def _generate_backtracking_steps(self, board: Board):
        """
        Generator mô phỏng Backtracking.
        Yield:
          ("place", r, c, num, board_snapshot)
          ("remove", r, c, 0, board_snapshot)
          ("solved", board_snapshot)
          ("nosolution", board_snapshot)
        """
        work = [row[:] for row in board]

        def backtrack():
            pos = find_empty(work)
            if pos is None:
                yield ("solved", [row[:] for row in work])
                return True
            r, c = pos
            for num in range(1, 10):
                if is_valid(work, r, c, num):
                    work[r][c] = num
                    yield ("place", r, c, num, [row[:] for row in work])
                    res = yield from backtrack()
                    if res:
                        return True
                    work[r][c] = 0
                    yield ("remove", r, c, 0, [row[:] for row in work])
            return False

        solved = yield from backtrack()
        if not solved:
            yield ("nosolution", [row[:] for row in work])

    def on_step_solve(self) -> None:
        if self.step_solver_running:
            messagebox.showinfo(
                "Đang mô phỏng",
                "Đang mô phỏng Backtracking. Vui lòng đợi hoàn tất.",
            )
            return
        try:
            board = self.get_board_from_entries()
        except ValueError as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))
            self._set_status("Lỗi dữ liệu đầu vào.", STATUS_ERR)
            self._set_solve_info(
                "Lỗi dữ liệu: chỉ nhập 1–9, 0 hoặc để trống.",
                STATUS_ERR,
            )
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()
            return

        if not self._check_initial_valid(board, announce=True):
            return

        self.step_gen = self._generate_backtracking_steps(board)
        self.step_solver_running = True

        self._set_status("Mô phỏng Backtracking từng bước...", ACCENT)
        self._set_solve_info(
            "Đang mô phỏng Backtracking: quan sát các ô thay đổi theo thời gian.",
            ACCENT,
        )

        self._run_step_visual()

    def _run_step_visual(self) -> None:
        if not self.step_solver_running or self.step_gen is None:
            return
        try:
            step = next(self.step_gen)
        except StopIteration:
            self.step_solver_running = False
            self.step_gen = None
            return

        kind = step[0]

        if kind == "place":
            _, r, c, num, board_snapshot = step
            self.fill_entries_from_board(board_snapshot)
            self.entries[r][c].config(
                bg="#fef9c3",
                fg=ACCENT_DARK,
                highlightbackground=ACCENT,
            )
        elif kind == "remove":
            _, r, c, _, board_snapshot = step
            self.fill_entries_from_board(board_snapshot)
            self.entries[r][c].config(
                bg="#fee2e2",
                fg=ACCENT_DARK,
                highlightbackground=ACCENT,
            )
        elif kind == "solved":
            _, board_snapshot = step
            self.fill_entries_from_board(board_snapshot)
            self._set_status("Backtracking: đã tìm thấy lời giải.", STATUS_OK)
            self._set_solve_info(
                "Mô phỏng Backtracking hoàn tất: đã tìm thấy lời giải.",
                STATUS_OK,
            )
            self._flash_board("#bbf7d0", CELL_BG, 4)
            self.step_solver_running = False
            self.step_gen = None
            return
        elif kind == "nosolution":
            _, board_snapshot = step
            self.fill_entries_from_board(board_snapshot)
            self._set_status(
                "Backtracking: không tìm được lời giải cho board này.",
                STATUS_ERR,
            )
            self._set_solve_info(
                "Mô phỏng Backtracking chạy hết mà không tìm thấy lời giải.",
                STATUS_ERR,
            )
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()
            self.step_solver_running = False
            self.step_gen = None
            return

        self.root.after(self.step_delay_ms, self._run_step_visual)

    # ========= ANIMATIONS =========

    def _flash_board(self, color1: str, color2: str, times: int = 4) -> None:
        def step(n: int):
            if n <= 0:
                self._reset_cell_colors()
                return
            bg = color1 if n % 2 == 0 else color2
            for r in range(9):
                for c in range(9):
                    self.entries[r][c].config(bg=bg)
            self.root.after(80, step, n - 1)

        step(times)

    def _shake_grid(self) -> None:
        self.root.update_idletasks()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        offsets = [0, -12, 12, -9, 9, -5, 5, 0]

        def move(i: int = 0):
            if i >= len(offsets):
                self.root.geometry(f"+{x}+{y}")
                return
            dx = offsets[i]
            self.root.geometry(f"+{x + dx}+{y}")
            self.root.after(25, move, i + 1)

        move()

    # ========= FILE LISTS & FOLDERS =========

    def refresh_file_lists(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        in_dir = os.path.join(base, "input")
        out_dir = os.path.join(base, "output")

        try:
            self.input_files = sorted(
                f for f in os.listdir(in_dir) if f.lower().endswith(".txt")
            )
        except Exception:
            self.input_files = []
        self.input_menu["values"] = self.input_files
        if self.input_files and self.input_var.get() not in self.input_files:
            self.input_var.set(self.input_files[0])

        try:
            self.output_files = sorted(
                f for f in os.listdir(out_dir) if f.lower().endswith(".txt")
            )
        except Exception:
            self.output_files = []
        self.output_menu["values"] = self.output_files
        if self.output_files and self.output_var.get() not in self.output_files:
            self.output_var.set(self.output_files[0])

    def _open_folder(self, path: str) -> None:
        if not os.path.exists(path):
            messagebox.showinfo("Không tìm thấy", f"Không tồn tại: {path}")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror(
                "Lỗi",
                f"Không mở được thư mục:\n{path}\n{e}",
            )

    def open_input_folder(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        self._open_folder(os.path.join(base, "input"))

    def open_output_folder(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        self._open_folder(os.path.join(base, "output"))

    # ========= BUTTON HANDLERS: I/O =========

    def load_from_selected_input(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        in_dir = os.path.join(base, "input")
        fname = self.input_var.get()
        if not fname:
            messagebox.showwarning(
                "Chưa chọn file",
                "Hãy chọn một file trong dropdown Input.",
            )
            return
        path = os.path.join(in_dir, fname)
        try:
            board = read_board_from_file(path)
            self.fill_entries_from_board(board)
            self.current_input_file = fname
            self.original_board = [row[:] for row in board]
            self._set_status(f"Đã load từ input/{fname}", STATUS_NORMAL)
            self._set_solve_info(
                f"Đã load đề từ input/{fname}. Kiểm tra rồi nhấn Validate / Solve / Step.",
                TEXT_MUTED,
            )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được {path}:\n{e}")
            self._set_status("Lỗi khi load input.", STATUS_ERR)
            self._set_solve_info(
                "Lỗi load input. Kiểm tra đường dẫn & nội dung.",
                STATUS_ERR,
            )
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()

    def reload_original_puzzle(self) -> None:
        if self.original_board is None:
            messagebox.showinfo(
                "Không có puzzle gốc",
                "Chưa có đề nào được load từ input để reload.",
            )
            return
        self.fill_entries_from_board(self.original_board)
        self._set_status("Đã reload puzzle gốc.", STATUS_NORMAL)
        self._set_solve_info(
            "Đã tải lại đề gốc từ file input. Sẵn sàng Solve / Step.",
            TEXT_MUTED,
        )

    def view_selected_output(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(base, "output")
        fname = self.output_var.get()
        if not fname:
            messagebox.showwarning(
                "Chưa chọn file",
                "Chọn một file trong dropdown Output.",
            )
            return
        path = os.path.join(out_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            top = tk.Toplevel(self.root)
            top.title(f"Xem output/{fname}")
            top.configure(bg=BG_MAIN)

            w = int(420 * self.S)
            h = int(420 * self.S)
            x = self.root.winfo_x() + int(80 * self.S)
            y = self.root.winfo_y() + int(80 * self.S)
            top.geometry(f"{w}x{h}+{x}+{y}")

            txt = tk.Text(
                top,
                wrap="none",
                font=self.F_TEXT,
                bg="#020817",
                fg=TEXT_PRIMARY,
                relief="flat",
            )
            txt.pack(
                fill="both",
                expand=True,
                padx=int(12 * self.S),
                pady=int(12 * self.S),
            )
            txt.insert("1.0", content)
            txt.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được {path}:\n{e}")

    def load_selected_output_to_grid(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(base, "output")
        fname = self.output_var.get()
        if not fname:
            messagebox.showwarning(
                "Chưa chọn file",
                "Chọn một file trong dropdown Output.",
            )
            return
        path = os.path.join(out_dir, fname)
        try:
            board = read_board_from_file(path)
            self.fill_entries_from_board(board)
            self.current_input_file = None
            self.original_board = [row[:] for row in board]
            self._set_status(f"Đã load từ output/{fname}", STATUS_NORMAL)
            self._set_solve_info(
                f"Đang hiển thị lưới từ output/{fname}.",
                TEXT_MUTED,
            )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được {path}:\n{e}")
            self._set_status("Lỗi khi load output.", STATUS_ERR)

    # ========= BUTTON HANDLERS: GAMEPLAY =========

    def on_solve(self) -> None:
        if self.step_solver_running:
            messagebox.showinfo(
                "Đang mô phỏng",
                "Đang chạy Step-by-step. Đợi xong hoặc Clear rồi Solve lại.",
            )
            return
        try:
            board = self.get_board_from_entries()
        except ValueError as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))
            self._set_status("Lỗi dữ liệu đầu vào.", STATUS_ERR)
            self._set_solve_info(
                "Lỗi dữ liệu: chỉ nhập 1–9, 0 hoặc để trống.",
                STATUS_ERR,
            )
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()
            return

        if not self._check_initial_valid(board, announce=True):
            return

        self._set_status("Đang giải bằng Backtracking...", ACCENT)
        self._set_solve_info("Đang giải...", ACCENT)
        self.root.update_idletasks()

        start = time.perf_counter()
        solved = solve_sudoku(board)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if solved:
            self.fill_entries_from_board(board)

            base = os.path.dirname(os.path.abspath(__file__))
            out_dir = os.path.join(base, "output")
            os.makedirs(out_dir, exist_ok=True)

            # Nếu load từ input → solved_<tên>.txt
            # Nếu tự nhập / sample → Puzzle_Play.txt (ghi đè)
            if self.current_input_file:
                stem = os.path.splitext(os.path.basename(self.current_input_file))[0]
                fname = f"solved_{stem}.txt"
            else:
                fname = "Puzzle_Play.txt"

            out_path = os.path.join(out_dir, fname)
            write_board_to_file(board, out_path)

            self._set_status("Đã giải xong Sudoku.", STATUS_OK)
            self._set_solve_info(
                f"Đã giải. Thời gian: {elapsed_ms:.3f} ms • Đã lưu: output/{fname}",
                STATUS_OK,
            )
            self._flash_board("#bbf7d0", CELL_BG, 4)
            messagebox.showinfo(
                "Thành công",
                f"Đã giải xong.\nThời gian: {elapsed_ms:.3f} ms\nĐã lưu: {out_path}",
            )

            self.refresh_file_lists()
            if fname in self.output_files:
                self.output_var.set(fname)
        else:
            txt = "Không tìm được lời giải hợp lệ cho Sudoku này."
            self._set_status("Không tìm được lời giải.", STATUS_ERR)
            self._set_solve_info(txt, STATUS_ERR)
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()
            messagebox.showwarning("Không có lời giải", txt)

    def on_clear(self) -> None:
        if self.step_solver_running:
            self.step_solver_running = False
            self.step_gen = None
        for r in range(9):
            for c in range(9):
                self.entries[r][c].delete(0, tk.END)
        self._reset_cell_colors()
        self.selected_cell = None
        self.current_input_file = None
        self.original_board = None
        self._set_status("Đã xoá toàn bộ lưới.", STATUS_NORMAL)
        self._set_solve_info(
            "• Đã xoá lưới. Nhập đề mới hoặc chọn file Input rồi Solve / Step.",
            TEXT_MUTED,
        )

    def load_sample(self) -> None:
        sample: Board = [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ]
        self.fill_entries_from_board(sample)
        self.current_input_file = None
        self.original_board = [row[:] for row in sample]
        self._set_status("Đã load đề mẫu.", STATUS_NORMAL)
        self._set_solve_info(
            "Đã load đề mẫu. Có thể Validate, Solve hoặc Step để xem Backtracking.",
            TEXT_MUTED,
        )

    # ========= BACKTRACKING POPUP =========

    def show_backtracking_info(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("Thuật toán Backtracking - Mô tả")
        top.configure(bg=BG_MAIN)
        top.transient(self.root)

        w = int(520 * self.S)
        h = int(520 * self.S)
        x = self.root.winfo_x() + int(40 * self.S)
        y = self.root.winfo_y() + int(40 * self.S)
        top.geometry(f"{w}x{h}+{x}+{y}")

        title = tk.Label(
            top,
            text="Thuật toán Backtracking cho Sudoku",
            font=self.F_CARD_TITLE,
            fg=ACCENT_LIGHT,
            bg=BG_MAIN,
        )
        title.pack(
            anchor="w",
            padx=int(16 * self.S),
            pady=(int(14 * self.S), int(4 * self.S)),
        )

        subtitle = tk.Label(
            top,
            text=(
                "Backtracking thử từng khả năng một cách có kiểm soát.\n"
                "Nút Step trong GUI mô phỏng trực tiếp các bước dưới đây."
            ),
            font=self.F_TEXT,
            fg=TEXT_MUTED,
            bg=BG_MAIN,
            wraplength=w - int(32 * self.S),
            justify="left",
        )
        subtitle.pack(
            anchor="w",
            padx=int(16 * self.S),
            pady=(0, int(8 * self.S)),
        )

        txt = tk.Text(
            top,
            wrap="word",
            font=self.F_TEXT,
            bg="#020817",
            fg=TEXT_PRIMARY,
            relief="flat",
            padx=int(16 * self.S),
            pady=int(8 * self.S),
        )
        txt.pack(
            fill="both",
            expand=True,
            padx=int(8 * self.S),
            pady=(0, int(8 * self.S)),
        )

        content = (
            "Ý tưởng:\n"
            "• Luôn chọn một ô trống tiếp theo (theo thứ tự).\n"
            "• Thử lần lượt các số 1–9.\n"
            "• Nếu số đang thử không vi phạm luật Sudoku → đi tiếp ô sau.\n"
            "• Nếu không còn số hợp lệ → quay lui (backtrack), trả ô về 0 và thử số khác.\n"
            "• Khi không còn ô trống → bảng hiện tại là lời giải.\n\n"
            "Giả mã solve_sudoku(board):\n"
            "1. Tìm ô trống bằng find_empty(). Nếu không có → return True.\n"
            "2. Với ô (row, col):\n"
            "     for num in 1..9:\n"
            "         if is_valid(board, row, col, num):\n"
            "             đặt board[row][col] = num\n"
            "             nếu solve_sudoku(board) trả True → return True\n"
            "     đặt lại board[row][col] = 0 và return False.\n\n"
            "Trong GUI này:\n"
            "• Nút Solve: chạy nhanh toàn bộ Backtracking.\n"
            "• Nút Step: chạy Backtracking từng bước và hiển thị trực tiếp trên lưới.\n"
            "   - Ô vàng: đang thử một giá trị.\n"
            "   - Ô đỏ nhạt: bước quay lui (thu hồi giá trị thử sai).\n"
            "• Nhờ đó bạn vừa chơi Sudoku, vừa quan sát được thuật toán hoạt động."
        )

        txt.insert("1.0", content)
        txt.config(state="disabled")

        tk.Button(
            top,
            text="Đóng",
            command=top.destroy,
            font=self.F_TEXT_B,
            fg=TEXT_MUTED,
            bg="#111827",
            activebackground=ACCENT,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=int(12 * self.S),
            pady=int(6 * self.S),
            relief="flat",
            cursor="hand2",
        ).pack(pady=(0, int(10 * self.S)))


if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()
