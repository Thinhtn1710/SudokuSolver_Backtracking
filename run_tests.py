import os
import time
from sudoku_solver import solve_sudoku
from sudoku_utils import read_board_from_file, write_board_to_file

# Thư mục input/output
input_dir = "input"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Puzzle bình thường
puzzles = [f"puzzle{i}.txt" for i in range(2, 7)]
# Puzzle lỗi
error_puzzles = [
    "puzzle_error_missing_line.txt",
    "puzzle_error_wrong_char.txt",
    "puzzle_error_duplicate.txt"
]

report_lines = ["# Report Test Case Sudoku Solver\n"]
report_lines.append("| Puzzle | Số ô trống ban đầu | Giải được không | Thời gian giải (ms) |")
report_lines.append("|--------|------------------|----------------|--------------------|")

# Chạy puzzle bình thường
for puzzle_file in puzzles:
    input_path = os.path.join(input_dir, puzzle_file)
    output_file = f"solved{puzzle_file[6:]}"
    output_path = os.path.join(output_dir, output_file)

    try:
        board = read_board_from_file(input_path)
        empty_count = sum(row.count(0) for row in board)

        start = time.time()
        solved = solve_sudoku(board)
        end = time.time()
        elapsed_ms = (end - start) * 1000

        if solved:
            write_board_to_file(board, output_path)
            solved_status = "✅"
        else:
            solved_status = "❌"

        report_lines.append(f"| {puzzle_file} | {empty_count} | {solved_status} | {elapsed_ms:.2f} |")
        print(f"{puzzle_file}: solved={solved_status}, time={elapsed_ms:.2f} ms")

    except Exception as e:
        report_lines.append(f"| {puzzle_file} | ERROR | ❌ | 0 |")
        print(f"Lỗi đọc file {puzzle_file}: {e}")

# Kiểm thử file lỗi
for puzzle_file in error_puzzles:
    input_path = os.path.join(input_dir, puzzle_file)
    output_path = os.path.join(output_dir, f"error_{puzzle_file}")

    try:
        board = read_board_from_file(input_path)
        empty_count = sum(row.count(0) for row in board)

        start = time.time()
        solved = solve_sudoku(board)
        end = time.time()
        elapsed_ms = (end - start) * 1000

        solved_status = "✅" if solved else "❌"
        report_lines.append(f"| {puzzle_file} | {empty_count} | {solved_status} | {elapsed_ms:.2f} |")
        print(f"{puzzle_file}: solved={solved_status}, time={elapsed_ms:.2f} ms")

    except Exception as e:
        report_lines.append(f"| {puzzle_file} | ERROR | ❌ | 0 |")
        print(f"Lỗi đọc file {puzzle_file}: {e}")

# Ghi report
with open("report_testcase.md", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print("Đã tạo report_testcase.md")

