# sudoku_gui.py
# Sudoku Solver GUI - Fullscreen, rich layout, big play area
# - Auto full screen (maximized), không cho thu nhỏ
# - Khu chơi: card riêng (tiêu đề + grid + numpad + thông tin lời giải)
# - Bên phải: 2 card Hướng dẫn & Thuật toán Backtracking
# - Dùng solve_sudoku() từ sudoku_solver.py
# - Dùng read_board_from_file, is_valid từ sudoku_utils.py

import os
import time
import tkinter as tk
from tkinter import messagebox

from sudoku_utils import Board, is_valid, read_board_from_file
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

CELL_BG = "#ffffff"          # Ô trắng nổi bật
CELL_FG = "#111827"
CELL_BORDER = "#d1d5db"
CELL_HL = "#fee2e2"          # Ô đang chọn highlight hồng nhạt

STATUS_OK = "#22c55e"
STATUS_ERR = "#f97316"
STATUS_NORMAL = "#6b7280"


class SudokuGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sudoku Solver - Backtracking")

        self._init_window()
        self.root.configure(bg=BG_MAIN)

        self.entries: list[list[tk.Entry]] = [[None for _ in range(9)] for _ in range(9)]
        self.selected_cell: tuple[int, int] | None = None
        self.solve_info_label: tk.Label | None = None

        self._build_header()
        self._build_main()
        self._build_toolbar()
        self._build_status()

    # ========= WINDOW SETUP =========
    def _init_window(self) -> None:
        w, h = 1366, 768
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = int((sw - w) / 2)
        y = int((sh - h) / 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        try:
            self.root.state("zoomed")  # full trên Windows
        except Exception:
            pass

        self.root.resizable(False, False)

    # ========= UI BUILDERS =========

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=BG_MAIN)
        header.pack(fill="x", padx=32, pady=(18, 6))

        grad = tk.Frame(header, bg=ACCENT, height=3)
        grad.pack(fill="x", side="top", pady=(0, 10))

        title_row = tk.Frame(header, bg=BG_MAIN)
        title_row.pack(fill="x")

        title = tk.Label(
            title_row,
            text="Sudoku Solver",
            font=("Segoe UI", 26, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        )
        title.pack(side="left")

        badge = tk.Label(
            title_row,
            text="Backtracking",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_LIGHT,
            bg=BG_MAIN,
            padx=10,
            pady=3,
            bd=0,
        )
        badge.pack(side="left", padx=(10, 0))

        subtitle = tk.Label(
            header,
            text="Nhập đề, load từ file hoặc dùng mẫu • Thuật toán quay lui (Backtracking) • Giải & hiển thị trực quan",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_MAIN,
        )
        subtitle.pack(anchor="w", pady=(4, 0))

    def _build_main(self) -> None:
        wrapper = tk.Frame(self.root, bg=BG_MAIN)
        wrapper.pack(fill="both", expand=True, padx=32, pady=(4, 8))

        # ===== LEFT: PLAY AREA CARD =====
        play_card = tk.Frame(
            wrapper,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
        )
        play_card.pack(side="left", fill="both", expand=True, padx=(0, 18))
        play_card.pack_propagate(False)

        # Play card header
        play_header = tk.Frame(play_card, bg=CARD_BG)
        play_header.pack(fill="x", pady=(10, 4), padx=14)

        play_title = tk.Label(
            play_header,
            text="Bảng Sudoku 9×9",
            font=("Segoe UI", 14, "bold"),
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        play_title.pack(side="left")

        play_hint = tk.Label(
            play_header,
            text="Nhập đề hoặc load, sau đó nhấn Solve",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        play_hint.pack(side="left", padx=(10, 0))

        # Grid container (centered)
        self.grid_container = tk.Frame(play_card, bg=CARD_BG)
        self.grid_container.pack(pady=(6, 4))
        self._build_grid(self.grid_container)

        # Numpad + info
        self._build_numpad(play_card)
        self._build_play_info(play_card)

        # ===== RIGHT: INFO PANEL =====
        side_panel = tk.Frame(wrapper, bg=BG_MAIN, width=380)
        side_panel.pack(side="right", fill="y")
        side_panel.pack_propagate(False)

        self._build_help_cards(side_panel)

    def _build_grid(self, parent: tk.Frame) -> None:
        grid_frame = tk.Frame(parent, bg=CARD_BG)
        grid_frame.pack()

        for r in range(9):
            for c in range(9):
                pad_left = 3 if c in (0, 3, 6) else 1
                pad_top = 3 if r in (0, 3, 6) else 1
                pad_right = 3 if c == 8 else 1
                pad_bottom = 3 if r == 8 else 1

                e = tk.Entry(
                    grid_frame,
                    width=3,
                    justify="center",
                    font=("Segoe UI", 20, "bold"),
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
                    ipady=6,
                )
                e.bind("<FocusIn>", lambda ev, rr=r, cc=c: self._on_cell_focus(rr, cc))
                self.entries[r][c] = e

    def _build_numpad(self, parent: tk.Frame) -> None:
        pad_frame = tk.Frame(parent, bg=CARD_BG)
        pad_frame.pack(pady=(10, 2))

        info = tk.Label(
            pad_frame,
            text="Chọn ô rồi click số để nhập nhanh",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        info.pack(anchor="center", pady=(0, 4))

        row = tk.Frame(pad_frame, bg=CARD_BG)
        row.pack()

        def make_num_btn(text, cmd):
            return tk.Button(
                row,
                text=text,
                command=cmd,
                font=("Segoe UI", 10, "bold"),
                fg=TEXT_PRIMARY,
                bg="#111827",
                activebackground=ACCENT,
                activeforeground=TEXT_PRIMARY,
                bd=0,
                relief="flat",
                padx=12,
                pady=6,
                cursor="hand2",
            )

        for n in range(1, 10):
            btn = make_num_btn(str(n), lambda v=n: self._input_number(v))
            btn.pack(side="left", padx=3)

        erase_btn = tk.Button(
            pad_frame,
            text="Erase",
            command=self._erase_selected,
            font=("Segoe UI", 9),
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
            activebackground=ACCENT_DARK,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        erase_btn.pack(pady=(4, 0))

    def _build_play_info(self, parent: tk.Frame) -> None:
        info_frame = tk.Frame(parent, bg=CARD_BG)
        info_frame.pack(fill="x", pady=(6, 10), padx=14)

        label = tk.Label(
            info_frame,
            text="Thông tin lời giải:",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        label.pack(anchor="w")

        self.solve_info_label = tk.Label(
            info_frame,
            text="• Chưa giải. Nhập đề hoặc load puzzle1.txt rồi nhấn Solve.",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            justify="left",
            anchor="w",
        )
        self.solve_info_label.pack(anchor="w")

    def _build_help_cards(self, parent: tk.Frame) -> None:
        # Card 1: Hướng dẫn nhanh
        guide_card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
        )
        guide_card.pack(fill="x", pady=(4, 10))
        guide_inner = tk.Frame(guide_card, bg=CARD_BG)
        guide_inner.pack(padx=14, pady=14, fill="both")

        title = tk.Label(
            guide_inner,
            text="Hướng dẫn nhanh",
            font=("Segoe UI", 12, "bold"),
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        title.pack(anchor="w", pady=(0, 6))

        def add(text, bold=False, color=TEXT_MUTED, top=0, bottom=1):
            lbl = tk.Label(
                guide_inner,
                text=text,
                font=("Segoe UI", 9 if not bold else 10, "bold" if bold else "normal"),
                fg=color,
                bg=CARD_BG,
                justify="left",
                anchor="w",
            )
            lbl.pack(anchor="w", pady=(top, bottom))

        add("• Bảng 9×9, điền số 1–9, không trùng hàng / cột / khối 3×3.", bottom=3)
        add("Nhập đề:", bold=True, color=ACCENT_LIGHT, top=4)
        add("• Click ô rồi gõ số 1–9 hoặc dùng numpad.")
        add("• Để trống hoặc nhập 0 / '.' = ô chưa điền.", bottom=3)

        add("Load puzzle1.txt:", bold=True, color=ACCENT_LIGHT, top=4)
        add("• Đường dẫn: input/puzzle1.txt.")
        add("• 9 dòng, mỗi dòng 9 ký tự [0–9] hoặc '.', '0' / '.' = trống.", bottom=3)

        add("Solve:", bold=True, color=ACCENT_LIGHT, top=4)
        add("• Kiểm tra hợp lệ đề ban đầu, sau đó giải bằng Backtracking.")
        add("• Nếu có nghiệm → điền đầy bảng + info thời gian giải.", bottom=3)

        add("Clear & Exit:", bold=True, color=ACCENT_LIGHT, top=4)
        add("• Clear: xoá toàn bộ lưới để nhập đề mới.")
        add("• Exit: thoát chương trình.", bottom=0)

        # Card 2: Thuật toán Backtracking
        algo_card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
        )
        algo_card.pack(fill="both", pady=(0, 4), expand=True)
        algo_inner = tk.Frame(algo_card, bg=CARD_BG)
        algo_inner.pack(padx=14, pady=14, fill="both")

        t2 = tk.Label(
            algo_inner,
            text="Thuật toán Backtracking",
            font=("Segoe UI", 12, "bold"),
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        t2.pack(anchor="w", pady=(0, 6))

        def add_algo(text, bold=False, color=TEXT_MUTED, top=0, bottom=1):
            lbl = tk.Label(
                algo_inner,
                text=text,
                font=("Segoe UI", 9 if not bold else 10, "bold" if bold else "normal"),
                fg=color,
                bg=CARD_BG,
                justify="left",
                anchor="w",
            )
            lbl.pack(anchor="w", pady=(top, bottom))

        add_algo("Ý tưởng:", bold=True, color=TEXT_PRIMARY, bottom=1)
        add_algo("• Chọn ô trống tiếp theo, thử các số 1–9.")
        add_algo("• Nếu hợp lệ → đi tiếp ô sau.")
        add_algo("• Nếu bế tắc → quay lui, thử số khác.", bottom=4)

        add_algo("Giả mã solve_sudoku:", bold=True, color=ACCENT_LIGHT, bottom=1)
        add_algo("1. find_empty() → không còn ô trống → return True.")
        add_algo("2. Với ô (row, col) còn trống:")
        add_algo("   for num in 1..9:")
        add_algo("      if is_valid(board, row, col, num):")
        add_algo("         đặt num, gọi đệ quy solve_sudoku(board);")
        add_algo("         nếu True → lan truyền True.")
        add_algo("   không số nào phù hợp → đặt lại 0, return False.", bottom=4)

        add_algo("Độ phức tạp:", bold=True, color=ACCENT_LIGHT, bottom=1)
        add_algo("• Lý thuyết xấu: O(9^n) (n = số ô trống).")
        add_algo("• Thực tế Sudoku chuẩn: nhiều ràng buộc → cắt nhánh mạnh → chạy nhanh.", bottom=4)

        add_algo("Trong dự án này:", bold=True, color=TEXT_PRIMARY, bottom=1)
        add_algo("• solve_sudoku(board): định nghĩa trong sudoku_solver.py.")
        add_algo("• find_empty(), is_valid(): trong sudoku_utils.py.")
        add_algo("• GUI chỉ là lớp tương tác gọi thuật toán & hiển thị kết quả.")

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self.root, bg=BG_MAIN)
        bar.pack(fill="x", padx=32, pady=(0, 4))

        def make_btn(text, cmd, primary=False):
            return tk.Button(
                bar,
                text=text,
                command=cmd,
                font=("Segoe UI", 9, "bold"),
                fg=TEXT_PRIMARY if primary else TEXT_MUTED,
                bg=ACCENT if primary else "#111827",
                activebackground=ACCENT_DARK if primary else "#1f2937",
                activeforeground=TEXT_PRIMARY,
                bd=0,
                padx=18,
                pady=8,
                relief="flat",
                cursor="hand2",
            )

        btn_load_file = make_btn("Load puzzle1.txt", self.load_from_file)
        btn_sample = make_btn("Load Sample", self.load_sample)
        btn_clear = make_btn("Clear", self.on_clear)
        btn_solve = make_btn("Solve", self.on_solve, primary=True)
        btn_exit = make_btn("Exit", self.root.destroy)

        btn_load_file.pack(side="left", padx=(0, 6), pady=6)
        btn_sample.pack(side="left", padx=6, pady=6)
        btn_clear.pack(side="left", padx=6, pady=6)
        btn_solve.pack(side="left", padx=14, pady=6)
        btn_exit.pack(side="right", padx=(6, 0), pady=6)

    def _build_status(self) -> None:
        self.status_bar = tk.Label(
            self.root,
            text="Sẵn sàng.",
            font=("Segoe UI", 9),
            fg=STATUS_NORMAL,
            bg=BG_MAIN,
            anchor="w",
            padx=32,
            pady=4,
        )
        self.status_bar.pack(fill="x", side="bottom")

    # ========= HELPERS =========

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
        e.config(
            bg=CELL_HL,
            fg=ACCENT_DARK,
            highlightbackground=ACCENT,
        )
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
                        f"Giá trị không hợp lệ tại ô ({r+1}, {c+1}). "
                        "Chỉ nhập 1–9, 0 hoặc để trống."
                    )
            board.append(row)
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
        original_x = self.grid_container.winfo_x()

        def move(offsets):
            if not offsets:
                self.grid_container.place_forget()
                self.grid_container.pack(pady=(6, 4))
                return
            dx = offsets[0]
            self.grid_container.place(
                x=original_x + dx, y=self.grid_container.winfo_y()
            )
            self.root.after(25, move, offsets[1:])

        self.grid_container.pack_forget()
        self.grid_container.place(x=original_x, y=self.grid_container.winfo_y())
        seq = [0, -8, 8, -6, 6, -3, 3, 0]
        move(seq)

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
            txt = f"Đã giải xong Sudoku. Thời gian: {elapsed_ms:.3f} ms."
            self._set_status("Đã giải xong Sudoku.", STATUS_OK)
            self._set_solve_info(txt, STATUS_OK)
            self._flash_board("#bbf7d0", CELL_BG, 4)
            messagebox.showinfo("Thành công", txt)
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
        self._set_status("Đã xoá toàn bộ lưới.", STATUS_NORMAL)
        self._set_solve_info(
            "• Đã xoá lưới. Nhập đề mới hoặc load puzzle1.txt / Sample.",
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
        self._set_status("Đã load đề mẫu.", STATUS_NORMAL)
        self._set_solve_info(
            "Đã load đề mẫu kinh điển. Nhấn Solve để xem Backtracking hoạt động.",
            TEXT_MUTED,
        )

    def load_from_file(self) -> None:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, "input", "puzzle1.txt")
            board = read_board_from_file(path)
            self.fill_entries_from_board(board)
            self._set_status(f"Đã load từ {path}", STATUS_NORMAL)
            self._set_solve_info(
                f"Đã load đề từ {path}. Kiểm tra lại rồi nhấn Solve.",
                TEXT_MUTED,
            )
        except Exception as e:
            msg = f"Không đọc được puzzle1.txt:\n{e}"
            messagebox.showerror("Lỗi", msg)
            self._set_status("Lỗi khi load puzzle1.txt.", STATUS_ERR)
            self._set_solve_info("Lỗi load puzzle1.txt. Kiểm tra đường dẫn & nội dung.", STATUS_ERR)
            self._flash_board("#ffe4e6", CELL_BG, 4)
            self._shake_grid()


if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()
