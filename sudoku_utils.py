# sudoku_utils.py

from typing import List, Tuple, Optional

Board = List[List[int]]  # Kiểu dữ liệu bảng Sudoku


def read_board_from_file(path: str) -> Board:
    """
    Đọc Sudoku từ file text.
    - Ký tự '0' hoặc '.' được hiểu là ô trống.
    - Bỏ qua dòng rỗng.
    """
    board: Board = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            row: List[int] = []
            for ch in line:
                if ch in ("0", "."):
                    row.append(0)
                elif ch.isdigit():
                    row.append(int(ch))

            if len(row) == 9:
                board.append(row)

    if len(board) != 9:
        raise ValueError("Dữ liệu Sudoku không hợp lệ: cần đúng 9 dòng hợp lệ.")

    return board


def write_board_to_file(board: Board, path: str) -> None:
    """
    Ghi Sudoku ra file, mỗi dòng 9 số.
    """
    with open(path, "w", encoding="utf-8") as f:
        for row in board:
            line = "".join(str(num) for num in row)
            f.write(line + "\n")


def print_board(board: Board) -> None:
    """
    In Sudoku ra console với định dạng dễ nhìn.
    Ô trống (0) sẽ in là '.'.
    """
    for r in range(9):
        if r != 0 and r % 3 == 0:
            print("-" * 21)

        row_vals = []
        for c in range(9):
            if c != 0 and c % 3 == 0:
                row_vals.append("|")

            val = board[r][c]
            row_vals.append(str(val) if val != 0 else ".")
        print(" ".join(row_vals))


def find_empty(board: Board) -> Optional[Tuple[int, int]]:
    """
    Tìm ô trống tiếp theo (giá trị 0).
    Trả về (row, col) hoặc None nếu không còn ô trống.
    """
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def is_valid(board: Board, row: int, col: int, num: int) -> bool:
    """
    Kiểm tra num có thể đặt tại (row, col) hay không.
    - Không trùng trong hàng
    - Không trùng trong cột
    - Không trùng trong ô 3x3
    Giả sử tại (row, col) hiện đang là 0 khi dùng trong backtracking.
    """

    # Kiểm tra hàng
    for c in range(9):
        if board[row][c] == num:
            return False

    # Kiểm tra cột
    for r in range(9):
        if board[r][col] == num:
            return False

    # Kiểm tra ô 3x3
    start_row = (row // 3) * 3
    start_col = (col // 3) * 3

    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if board[r][c] == num:
                return False

    return True
