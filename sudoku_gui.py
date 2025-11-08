# sudoku_gui.py

import tkinter as tk
from tkinter import messagebox

from sudoku_utils import Board, is_valid
from sudoku_solver import solve_sudoku


class SudokuGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sudoku Solver - Backtracking")

        self.entries = [[None for _ in range(9)] for _ in range(9)]

        self._build_grid()
        self._build_buttons()

    def _build_grid(self) -> None:
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack()

        for r in range(9):
            for c in range(9):
                # Độ dày viền để phân tách 3x3
                border_top = 2 if r in (0, 3, 6) else 1
                border_left = 2 if c in (0, 3, 6) else 1

                e = tk.Entry(
                    frame,
                    width=2,
                    font=("Arial", 18),
                    justify="center",
                    relief="solid",
                    bd=1,
                )
                e.grid(row=r, column=c, padx=(border_left, 1), pady=(border_top, 1))

                self.entries[r][c] = e

    def _build_buttons(self) -> None:
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()

        solve_btn = tk.Button(btn_frame, text="Solve", width=10, command=self.on_solve)
        solve_btn.grid(row=0, column=0, padx=5)

        clear_btn = tk.Button(btn_frame, text="Clear", width=10, command=self.on_clear)
        clear_btn.grid(row=0, column=1, padx=5)

        sample_btn = tk.Button(
            btn_frame, text="Load Sample", width=12, command=self.load_sample
        )
        sample_btn.grid(row=0, column=2, padx=5)

    def get_board_from_entries(self) -> Board:
        board: Board = []

        for r in range(9):
            row = []
            for c in range(9):
                val = self.entries[r][c].get().strip()

                if val == "":
                    row.append(0)
                elif val.isdigit() and 1 <= int(val) <= 9:
                    row.append(int(val))
                else:
                    raise ValueError(
                        f"Giá trị không hợp lệ tại ô ({r+1}, {c+1}). "
                        f"Chỉ được nhập số 1-9 hoặc để trống."
                    )
            board.append(row)

        return board

    def fill_entries_from_board(self, board: Board) -> None:
        for r in range(9):
            for c in range(9):
                self.entries[r][c].delete(0, tk.END)
                if board[r][c] != 0:
                    self.entries[r][c].insert(0, str(board[r][c]))

    def on_solve(self) -> None:
        # Đọc dữ liệu từ GUI
        try:
            board = self.get_board_from_entries()
        except ValueError as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))
            return

        # Kiểm tra trạng thái ban đầu hợp lệ (không mâu thuẫn)
        for r in range(9):
            for c in range(9):
                num = board[r][c]
                if num != 0:
                    board[r][c] = 0
                    if not is_valid(board, r, c, num):
                        messagebox.showerror(
                            "Lỗi Sudoku",
                            f"Giá trị ban đầu không hợp lệ tại ô ({r+1}, {c+1}).",
                        )
                        return
                    board[r][c] = num

        # Gọi solve_sudoku từ sudoku_solver.py
        if solve_sudoku(board):
            self.fill_entries_from_board(board)
            messagebox.showinfo(
                "Thành công", "Đã giải xong Sudoku bằng thuật toán Backtracking."
            )
        else:
            messagebox.showwarning(
                "Không có lời giải", "Không tìm được lời giải hợp lệ cho Sudoku này."
            )

    def on_clear(self) -> None:
        for r in range(9):
            for c in range(9):
                self.entries[r][c].delete(0, tk.END)

    def load_sample(self) -> None:
        """
        Load một đề mẫu vào GUI (trùng với puzzle1.txt).
        Bạn có thể thay bằng đề khác nếu muốn.
        """
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


if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()
