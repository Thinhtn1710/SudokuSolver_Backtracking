def count_steps(board):
    """Đếm số bước đệ quy thực hiện khi giải Sudoku."""
    steps = 0

    def backtrack(b):
        nonlocal steps
        steps += 1
        # Tìm ô trống
        empty = None
        for i in range(9):
            for j in range(9):
                if b[i][j] == 0:
                    empty = (i, j)
                    break
            if empty:
                break
        if not empty:
            return True  # Đã giải xong

        row, col = empty
        for num in range(1, 10):
            if is_valid(b, row, col, num):
                b[row][col] = num
                if backtrack(b):
                    return True
                b[row][col] = 0
        return False

    # Tạo bản sao để không làm thay đổi board gốc
    import copy
    board_copy = copy.deepcopy(board)
    backtrack(board_copy)
    return steps
