from typing import List, Tuple, Optional

Board = List[List[int]]  # Kiểu dữ liệu bảng Sudoku


def read_board_from_file(path: str) -> Board:
    """
    Đọc Sudoku từ file text.
    - Mỗi dòng (không rỗng) phải có đúng 9 ký tự.
    - Ký tự '0' hoặc '.' được hiểu là ô trống.
    - Ký tự '1'..'9' là số hợp lệ.
    - Nếu gặp ký tự khác -> báo lỗi.
    - Nếu không đủ 9 dòng hợp lệ -> báo lỗi.
    - Sau khi đọc xong sẽ kiểm tra hợp lệ ban đầu (không trùng số trong hàng/cột/ô 3x3).
    """
    board: Board = []

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            # Bỏ qua dòng rỗng
            if not line:
                continue

            # Mỗi dòng dữ liệu Sudoku phải có đúng 9 ký tự
            if len(line) != 9:
                raise ValueError(
                    f"Dữ liệu Sudoku không hợp lệ tại dòng {line_num}: "
                    f"cần đúng 9 ký tự, nhận {len(line)}."
                )

            row: List[int] = []
            for ch in line:
                if ch in ("0", "."):
                    row.append(0)
                elif ch.isdigit():
                    # '1'..'9' là hợp lệ, '0' đã xử lý ở trên
                    digit = int(ch)
                    if 1 <= digit <= 9:
                        row.append(digit)
                    else:
                        # Trường hợp phòng thủ, gần như không xảy ra
                        raise ValueError(
                            f"Ký tự số không hợp lệ '{ch}' tại dòng {line_num}."
                        )
                else:
                    # Bắt được các ký tự sai như 'a', '#', ...
                    raise ValueError(
                        f"Ký tự không hợp lệ '{ch}' tại dòng {line_num}."
                    )

            board.append(row)

    # Phải có đúng 9 dòng dữ liệu
    if len(board) != 9:
        raise ValueError(
            "Dữ liệu Sudoku không hợp lệ: cần đúng 9 dòng hợp lệ."
        )

    # Kiểm tra hợp lệ trạng thái ban đầu:
    # - Không trùng số (1..9) trong cùng hàng
    # - Không trùng số (1..9) trong cùng cột
    # - Không trùng số (1..9) trong cùng ô 3x3
    _validate_initial_board(board)

    return board


def _validate_initial_board(board: Board) -> None:
    """
    Kiểm tra các ràng buộc Sudoku trên đề ban đầu.
    Cho phép số 0 (ô trống), nhưng:
    - Không cho phép trùng số 1..9 trong cùng hàng.
    - Không cho phép trùng số 1..9 trong cùng cột.
    - Không cho phép trùng số 1..9 trong cùng ô 3x3.
    Nếu vi phạm -> raise ValueError.
    """

    # Kiểm tra hàng
    for r in range(9):
        seen = set()
        for c in range(9):
            val = board[r][c]
            if val == 0:
                continue
            if val in seen:
                raise ValueError(
                    f"Dữ liệu không hợp lệ: trùng số {val} trên hàng {r + 1}."
                )
            seen.add(val)

    # Kiểm tra cột
    for c in range(9):
        seen = set()
        for r in range(9):
            val = board[r][c]
            if val == 0:
                continue
            if val in seen:
                raise ValueError(
                    f"Dữ liệu không hợp lệ: trùng số {val} trên cột {c + 1}."
                )
            seen.add(val)

    # Kiểm tra ô 3x3
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            seen = set()
            for r in range(box_row, box_row + 3):
                for c in range(box_col, box_col + 3):
                    val = board[r][c]
                    if val == 0:
                        continue
                    if val in seen:
                        raise ValueError(
                            "Dữ liệu không hợp lệ: trùng số "
                            f"{val} trong ô 3x3 bắt đầu tại "
                            f"hàng {box_row + 1}, cột {box_col + 1}."
                        )
                    seen.add(val)


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
