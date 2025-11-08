# sudoku_solver.py

import os
import sys
import time

from sudoku_utils import (
    Board,
    read_board_from_file,
    write_board_to_file,
    print_board,
    find_empty,
    is_valid,
)


def solve_sudoku(board: Board) -> bool:
    """
    Thuật toán giải Sudoku bằng quay lui (Backtracking).
    - Tìm ô trống.
    - Thử lần lượt các số 1..9, kiểm tra hợp lệ bằng is_valid.
    - Nếu hợp lệ thì đặt số đó và đệ quy giải tiếp.
    - Nếu nhánh đó không dẫn đến nghiệm -> backtrack (gán lại 0) và thử số khác.
    - Nếu không còn ô trống -> đã giải xong -> trả về True.
    """

    empty_pos = find_empty(board)
    if empty_pos is None:
        # Không còn ô trống => đã giải xong
        return True

    row, col = empty_pos

    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num  # đặt thử

            if solve_sudoku(board):
                return True  # nếu giải được thì propagate True lên

            # nếu không giải được, quay lui
            board[row][col] = 0

    # Thử hết 1..9 không được => không có nghiệm tại trạng thái này
    return False


def solve_file(input_path: str, output_path: str) -> None:
    """
    Hàm tiện ích:
    - Đọc Sudoku từ input_path
    - In đề
    - Giải + đo thời gian
    - In kết quả
    - Ghi lời giải ra output_path
    """
    board = read_board_from_file(input_path)

    print("===== SUDOKU BAN ĐẦU =====")
    print_board(board)

    start = time.time()
    solved = solve_sudoku(board)
    end = time.time()

    if solved:
        print("\n===== SUDOKU ĐÃ GIẢI =====")
        print_board(board)
        elapsed_ms = (end - start) * 1000
        print(f"\nThời gian giải: {elapsed_ms:.3f} ms")

        # Đảm bảo thư mục output tồn tại
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        write_board_to_file(board, output_path)
        print(f"Lời giải đã được ghi vào: {output_path}")
    else:
        elapsed_ms = (end - start) * 1000
        print("\nKhông tìm được lời giải cho Sudoku.")
        print(f"Thời gian chạy: {elapsed_ms:.3f} ms")


if __name__ == "__main__":
    # Cho phép truyền file qua command line, nếu không thì dùng mặc định
    base_dir = os.path.dirname(os.path.abspath(__file__))

    default_input = os.path.join(base_dir, "input", "puzzle1.txt")
    default_output = os.path.join(base_dir, "output", "solved1.txt")

    input_path = sys.argv[1] if len(sys.argv) >= 2 else default_input
    output_path = sys.argv[2] if len(sys.argv) >= 3 else default_output

    solve_file(input_path, output_path)
