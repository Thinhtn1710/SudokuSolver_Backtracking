# sudoku_gui.py
# Sudoku Solver GUI - Responsive fullscreen, dropdown input/output, optimized layout
# - UI scale theo màn hình, grid & numpad nổi bật
# - Right panel: chỉ "Hướng dẫn nhanh" + nút xem "Thuật toán Backtracking" (popup riêng)
# - Dropdown chọn file từ input/, dropdown xem / load file từ output/
# - Solve -> ghi kết quả vào output/ và refresh dropdown
# - Không phá layout khi báo lỗi (rung cửa sổ thay vì di chuyển grid)

import os
import time
import datetime as dt
import tkinter as tk
from tkinter import messagebox, ttk

from sudoku_utils import Board, is_valid, read_board_from_file, write_board_to_file
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

        # scale & fullscreen
        self._init_window_and_scale()
        self.root.configure(bg=BG_MAIN)

        self.entries: list[list[tk.Entry]] = [[None for _ in range(9)] for _ in range(9)]
        self.selected_cell: tuple[int, int] | None = None
        self.solve_info_label: tk.Label | None = None

        self.current_input_file: str | None = None

        # dropdown data
        self.input_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value="")
        self.input_files: list[str] = []
        self.output_files: list[str] = []

        self._build_header()
        self._build_main()
        self._build_toolbar()
        self._build_status()

        self.refresh_file_lists()

    # ========= WINDOW + SCALE =========
    def _init_window_and_scale(self) -> None:
        """
        Full màn hình + hệ số scale S để UI cân trên mọi độ phân giải.
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

        # Cho phép resize, layout tự co giãn theo pack/grid
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
        header.pack(fill="x", padx=self.PX, pady=(int(18 * self.S), int(6 * self.S)))

        grad = tk.Frame(header, bg=ACCENT, height=max(2, int(3 * self.S)))
        grad.pack(fill="x", side="top", pady=(0, int(10 * self.S)))

        title_row = tk.Frame(header, bg=BG_MAIN)
        title_row.pack(fill="x")

        title = tk.Label(title_row, text="Sudoku Solver", font=self.F_TITLE, fg=TEXT_PRIMARY, bg=BG_MAIN)
        title.pack(side="left")

        badge = tk.Label(
            title_row,
            text="Backtracking",
            font=("Segoe UI", int(9 * self.S), "bold"),
            fg=ACCENT_LIGHT,
            bg=BG_MAIN,
            padx=int(10 * self.S),
            pady=max(2, int(3 * self.S)),
        )
        badge.pack(side="left", padx=(int(10 * self.S), 0))

        subtitle = tk.Label(
            header,
            text="Nhập đề hoặc chọn file • Giải bằng thuật toán quay lui • Trải nghiệm như một board game số.",
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

        # ===== LEFT: PLAY AREA =====
        play_card = tk.Frame(
            wrapper,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
        )
        play_card.pack(side="left", fill="both", expand=True, padx=(0, int(18 * self.S)))
        play_card.pack_propagate(False)

        play_header = tk.Frame(play_card, bg=CARD_BG)
        play_header.pack(fill="x", pady=(int(10 * self.S), int(4 * self.S)), padx=int(14 * self.S))

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
            text="Tập trung chơi: nhập đề, Solve, xem kết quả.",
            font=self.F_SUB,
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        play_hint.pack(side="left", padx=(int(10 * self.S), 0))

        # Grid (centered)
        self.grid_container = tk.Frame(play_card, bg=CARD_BG)
        self.grid_container.pack(pady=(int(6 * self.S), int(4 * self.S)))
        self._build_grid(self.grid_container)

        # Numpad + solve info
        self._build_numpad(play_card)
        self._build_play_info(play_card)

        # ===== RIGHT: INFO PANEL =====
        side_panel = tk.Frame(wrapper, bg=BG_MAIN, width=self.SIDE_W)
        side_panel.pack(side="right", fill="y")
        side_panel.pack_propagate(False)

        self._build_help_card(side_panel)

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
                self.entries[r][c] = e

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

        def make_btn(text, cmd, primary=False):
            return tk.Button(
                row,
                text=text,
                command=cmd,
                font=self.F_NUMPAD,
                fg=TEXT_PRIMARY,
                bg=ACCENT if primary else "#111827",
                activebackground=ACCENT_DARK if primary else ACCENT,
                activeforeground=TEXT_PRIMARY,
                bd=0,
                relief="flat",
                padx=int(12 * self.S),
                pady=int(6 * self.S),
                cursor="hand2",
            )

        for n in range(1, 9 + 1):
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
            text="• Chưa giải. Nhập đề hoặc chọn file Input, sau đó nhấn Solve.",
            font=self.F_TEXT,
            fg=TEXT_MUTED,
            bg=CARD_BG,
            justify="left",
            anchor="w",
            wraplength=self.WRAP_INFO,
        )
        self.solve_info_label.pack(anchor="w")

    def _build_help_card(self, parent: tk.Frame) -> None:
        """
        Panel phải: chỉ một card Hướng dẫn nhanh + nút mở popup Thuật toán Backtracking.
        Layout gọn để không phá cảm giác chơi.
        """
        guide_card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
        )
        guide_card.pack(fill="both", pady=(int(4 * self.S), int(4 * self.S)), expand=True)

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

        def add(text, bold=False, color=TEXT_MUTED, top=0, bottom=1):
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

        # Rút gọn, đủ dùng cho gameplay
        add("• Bảng 9×9, điền số 1–9, không trùng hàng / cột / khối 3×3.", bottom=3)
        add("Nhập:", bold=True, color=ACCENT_LIGHT, top=2)
        add("• Click ô rồi gõ số (1–9) hoặc dùng numpad.")
        add("• Để trống / 0 / '.' = ô chưa điền.", bottom=3)

        add("Input:", bold=True, color=ACCENT_LIGHT, top=2)
        add("• Chọn file .txt trong dropdown Input rồi nhấn Load.", bottom=3)

        add("Solve:", bold=True, color=ACCENT_LIGHT, top=2)
        add("• Tự kiểm tra hợp lệ, giải bằng Backtracking.")
        add("• Có nghiệm → điền lưới + lưu vào output/.", bottom=3)

        add("Output:", bold=True, color=ACCENT_LIGHT, top=2)
        add("• Chọn file trong dropdown Output để xem hoặc load lên lưới.", bottom=3)

        add("Clear/Exit:", bold=True, color=ACCENT_LIGHT, top=2)
        add("• Clear để nhập đề mới, Exit để thoát.", bottom=6)

        # Nút xem thuật toán (mở popup riêng)
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
            padx=int(12 * self.S),
            pady=int(8 * self.S),
            relief="flat",
            cursor="hand2",
        )
        btn_algo.pack(anchor="w", pady=(0, 0))

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self.root, bg=BG_MAIN)
        bar.pack(fill="x", padx=self.PX, pady=(0, int(4 * self.S)))

        # Input dropdown
        tk.Label(bar, text="Input:", font=self.F_TEXT_B, fg=TEXT_PRIMARY, bg=BG_MAIN).pack(
            side="left", padx=(0, int(6 * self.S))
        )
        self.input_menu = ttk.Combobox(
            bar,
            textvariable=self.input_var,
            state="readonly",
            width=int(22 * self.S),
        )
        self.input_menu.pack(side="left", padx=(0, int(6 * self.S)))

        btn_load_in = tk.Button(
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
        )
        btn_load_in.pack(side="left", padx=(0, int(14 * self.S)), pady=int(6 * self.S))

        # Output dropdown
        tk.Label(bar, text="Output:", font=self.F_TEXT_B, fg=TEXT_PRIMARY, bg=BG_MAIN).pack(
            side="left", padx=(0, int(6 * self.S))
        )
        self.output_menu = ttk.Combobox(
            bar,
            textvariable=self.output_var,
            state="readonly",
            width=int(22 * self.S),
        )
        self.output_menu.pack(side="left", padx=(0, int(6 * self.S)))

        btn_view_out = tk.Button(
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
        )
        btn_view_out.pack(side="left", padx=(0, int(4 * self.S)), pady=int(6 * self.S))

        btn_load_out = tk.Button(
            bar,
            text="Load to Grid",
            command=self.load_selected_output_to_grid,
            font=self.F_TEXT_B,
            fg=TEXT_PRIMARY,
            bg="#111827",
            activebackground=ACCENT,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=int(10 * self.S),
            pady=int(6 * self.S),
            relief="flat",
            cursor="hand2",
        )
        btn_load_out.pack(side="left", padx=(0, int(14 * self.S)), pady=int(6 * self.S))

        # Sample / Clear / Solve / Exit
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
                padx=int(12 * self.S),
                pady=int(7 * self.S),
                relief="flat",
                cursor="hand2",
            )

        small_btn("Load Sample", self.load_sample).pack(
            side="left", padx=(0, int(6 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Clear", self.on_clear).pack(
            side="left", padx=(0, int(6 * self.S)), pady=int(6 * self.S)
        )
        small_btn("Solve", self.on_solve, primary=True).pack(
            side="left", padx=(0, int(6 * self.S)), pady=int(6 * self.S)
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

    # ========= QUICK HELP POPUP =========

    def show_backtracking_info(self) -> None:
        """
        Popup riêng giải thích thuật toán Backtracking.
        Không chiếm chỗ panel phải, chỉ mở khi người chơi muốn đọc.
        """
        top = tk.Toplevel(self.root)
        top.title("Thuật toán Backtracking - Sudoku Solver")
        top.configure(bg=BG_MAIN)
        top.transient(self.root)

        # kích thước / vị trí
        w = int(520 * self.S)
        h = int(520 * self.S)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = self.root.winfo_x() + int(40 * self.S)
        y = self.root.winfo_y() + int(40 * self.S)
        if x + w > sw:
            x = max(0, sw - w - 20)
        if y + h > sh:
            y = max(0, sh - h - 20)
        top.geometry(f"{w}x{h}+{x}+{y}")

        title = tk.Label(
            top,
            text="Thuật toán Backtracking",
            font=self.F_CARD_TITLE,
            fg=ACCENT_LIGHT,
            bg=BG_MAIN,
        )
        title.pack(anchor="w", padx=int(16 * self.S), pady=(int(14 * self.S), int(4 * self.S)))

        subtitle = tk.Label(
            top,
            text="Ý tưởng duyệt thử từng khả năng một cách có kiểm soát, sai thì quay lui. Dưới đây là mô tả áp dụng cho Sudoku.",
            font=self.F_TEXT,
            fg=TEXT_MUTED,
            bg=BG_MAIN,
            wraplength=w - int(32 * self.S),
            justify="left",
        )
        subtitle.pack(anchor="w", padx=int(16 * self.S), pady=(0, int(8 * self.S)))

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
        txt.pack(fill="both", expand=True, padx=int(8 * self.S), pady=(0, int(8 * self.S)))

        content = (
            "Ý tưởng chính:\n"
            "• Luôn chọn một ô trống tiếp theo.\n"
            "• Thử các giá trị 1–9; chỉ giữ những giá trị không phá vỡ luật Sudoku.\n"
            "• Nếu đi tiếp dẫn đến bế tắc → quay lui (backtrack), thử giá trị khác.\n"
            "• Nếu không còn ô trống → bảng hiện tại là lời giải.\n\n"
            "Giả mã (pseudocode):\n"
            "1. find_empty(board):\n"
            "      tìm ô còn 0; nếu không có → return True (đã giải).\n"
            "2. Với ô (row, col) vừa tìm được:\n"
            "      for num in 1..9:\n"
            "          if is_valid(board, row, col, num):\n"
            "              đặt board[row][col] = num\n"
            "              nếu solve_sudoku(board) trả True → lan truyền True\n"
            "      không số nào phù hợp → đặt lại 0, return False.\n\n"
            "Trong chương trình:\n"
            "• solve_sudoku(board): cài đặt trong sudoku_solver.py.\n"
            "• is_valid(), find_empty(): trong sudoku_utils.py.\n"
            "• GUI chỉ gọi solve_sudoku(board) với đề đã hợp lệ, sau đó hiển thị kết quả.\n"
        )

        txt.insert("1.0", content)
        txt.config(state="disabled")

        btn_close = tk.Button(
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
        )
        btn_close.pack(pady=(0, int(10 * self.S)))

    # ========= STATE HELPERS =========

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
        # Rung nhẹ cửa sổ, không động vào layout grid
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

    # ========= FILE LISTS =========

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

    # ========= BUTTON HANDLERS =========

    def on_solve(self) -> None:
        try:
            board = self.get_board_from_entries()
        except ValueError as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))
            self._set_status("Lỗi dữ liệu đầu vào.", STATUS_ERR)
            self._set_solve_info("Lỗi dữ liệu: kiểm tra lại các ô nhập.", STATUS_ERR)
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()
            return

        # kiểm tra hợp lệ ban đầu
        for r in range(9):
            for c in range(9):
                num = board[r][c]
                if num != 0:
                    board[r][c] = 0
                    if not is_valid(board, r, c, num):
                        msg = f"Giá trị ban đầu không hợp lệ tại ô ({r+1}, {c+1})."
                        messagebox.showerror("Lỗi Sudoku", msg)
                        self._set_status("Sudoku ban đầu không hợp lệ.", STATUS_ERR)
                        self._set_solve_info(msg, STATUS_ERR)
                        self._flash_board("#ffe4e6", CELL_BG, 4)
                        self._shake_grid()
                        return
                    board[r][c] = num

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
        for r in range(9):
            for c in range(9):
                self.entries[r][c].delete(0, tk.END)
        self._reset_cell_colors()
        self.selected_cell = None
        self.current_input_file = None
        self._set_status("Đã xoá toàn bộ lưới.", STATUS_NORMAL)
        self._set_solve_info(
            "• Đã xoá lưới. Nhập đề mới hoặc chọn file Input rồi Solve.",
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
        self._set_status("Đã load đề mẫu.", STATUS_NORMAL)
        self._set_solve_info("Đã load đề mẫu. Nhấn Solve để xem lời giải.", TEXT_MUTED)

    def load_from_selected_input(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        in_dir = os.path.join(base, "input")
        fname = self.input_var.get()
        if not fname:
            messagebox.showwarning("Chưa chọn file", "Hãy chọn một file trong dropdown Input.")
            return
        path = os.path.join(in_dir, fname)
        try:
            board = read_board_from_file(path)
            self.fill_entries_from_board(board)
            self.current_input_file = fname
            self._set_status(f"Đã load từ input/{fname}", STATUS_NORMAL)
            self._set_solve_info(
                f"Đã load đề từ input/{fname}. Kiểm tra rồi nhấn Solve.",
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

    def view_selected_output(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(base, "output")
        fname = self.output_var.get()
        if not fname:
            messagebox.showwarning("Chưa chọn file", "Chọn một file trong dropdown Output.")
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
            txt.pack(fill="both", expand=True, padx=int(12 * self.S), pady=int(12 * self.S))
            txt.insert("1.0", content)
            txt.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được {path}:\n{e}")

    def load_selected_output_to_grid(self) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(base, "output")
        fname = self.output_var.get()
        if not fname:
            messagebox.showwarning("Chưa chọn file", "Chọn một file trong dropdown Output.")
            return
        path = os.path.join(out_dir, fname)
        try:
            board = read_board_from_file(path)
            self.fill_entries_from_board(board)
            self.current_input_file = None
            self._set_status(f"Đã load từ output/{fname}", STATUS_NORMAL)
            self._set_solve_info(
                f"Đang hiển thị lưới từ output/{fname}.",
                TEXT_MUTED,
            )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được {path}:\n{e}")
            self._set_status("Lỗi khi load output.", STATUS_ERR)

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()
