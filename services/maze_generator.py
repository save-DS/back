"""
미로 랜덤 생성 모듈.

[알고리즘]
1) DFS 백트래킹으로 미로 생성 (스택 사용)
2) BFS로 시작점에서 가장 먼 칸을 출구로 선정 (큐 사용)
3) 함정 N개 배치 (셋 + BFS 도달 가능성 검증)

[그리드 표현]
- 2차원 리스트, 0=길, 1=벽
- 외곽은 항상 벽
- 길이 되는 셀은 홀수 좌표 (1,1), (1,3), (3,1) ...
- 셀 사이 벽은 짝수 좌표 - DFS가 이를 뚫으며 통로 생성

[크기 규칙]
- 홀수만 허용 (짝수면 +1)
- 기본값 15x9 (이미지 사이즈)
"""
import random
from collections import deque


# 4방향 이웃 (DFS는 2칸 단위, BFS는 1칸 단위)
DIRECTIONS_BFS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIRECTIONS_DFS = [(-2, 0), (2, 0), (0, -2), (0, 2)]


# ----------------------------------------------------------------------
# 1. 미로 생성 (스택 기반 DFS 백트래킹)
# ----------------------------------------------------------------------
def generate_maze(width: int = 15, height: int = 9) -> list[list[int]]:
    """DFS 백트래킹으로 미로 생성.

    Args:
        width:  가로 크기 (홀수, 짝수면 +1)
        height: 세로 크기 (홀수, 짝수면 +1)

    Returns:
        2차원 리스트 (0=길, 1=벽)
    """
    if width % 2 == 0:
        width += 1
    if height % 2 == 0:
        height += 1

    # 전부 벽으로 초기화
    grid = [[1] * width for _ in range(height)]

    start = (1, 1)
    grid[start[0]][start[1]] = 0
    stack = [start]   # ★ 자료구조: 스택

    while stack:
        r, c = stack[-1]

        # 2칸 떨어진 이웃 중 아직 벽인 곳 (방문 안 한 곳)
        unvisited = []
        for dr, dc in DIRECTIONS_DFS:
            nr, nc = r + dr, c + dc
            if 1 <= nr < height - 1 and 1 <= nc < width - 1 and grid[nr][nc] == 1:
                unvisited.append((nr, nc))

        if unvisited:
            nr, nc = random.choice(unvisited)
            # 현재 칸과 선택된 칸 사이의 벽을 뚫는다
            grid[(r + nr) // 2][(c + nc) // 2] = 0
            grid[nr][nc] = 0
            stack.append((nr, nc))
        else:
            stack.pop()   # ★ 백트래킹

    return grid


# ----------------------------------------------------------------------
# 2. 출구 선정 (BFS로 시작점에서 가장 먼 칸)
# ----------------------------------------------------------------------
def pick_exit(grid: list[list[int]], start: tuple[int, int]) -> tuple[int, int]:
    """시작점에서 BFS 거리 최대인 칸을 출구로 선정.

    랜덤성을 보장하면서도 출구가 시작점과 충분히 떨어진 위치에 오도록 한다.
    """
    height = len(grid)
    width = len(grid[0])

    distances: dict[tuple[int, int], int] = {start: 0}
    queue: deque = deque([start])    # ★ 자료구조: 큐
    max_dist = 0
    exit_pos = start

    while queue:
        r, c = queue.popleft()
        if distances[(r, c)] > max_dist:
            max_dist = distances[(r, c)]
            exit_pos = (r, c)

        for dr, dc in DIRECTIONS_BFS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < height and 0 <= nc < width
                    and grid[nr][nc] == 0
                    and (nr, nc) not in distances):
                distances[(nr, nc)] = distances[(r, c)] + 1
                queue.append((nr, nc))

    return exit_pos


# ----------------------------------------------------------------------
# 3. 함정 배치 (셋 + BFS 도달 가능성 검증)
# ----------------------------------------------------------------------
def place_traps(
    grid: list[list[int]],
    start: tuple[int, int],
    exit_pos: tuple[int, int],
    n: int = 5,
) -> set[tuple[int, int]]:
    """함정 N개를 길 위에 배치. 단, 시작→출구 도달 가능성을 유지.

    Returns:
        함정 좌표들의 셋
    """
    height = len(grid)
    width = len(grid[0])

    # 시작/출구 제외한 모든 길 칸을 후보로
    candidates: list[tuple[int, int]] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 and (r, c) != start and (r, c) != exit_pos:
                candidates.append((r, c))

    random.shuffle(candidates)
    traps: set[tuple[int, int]] = set()    # ★ 자료구조: 셋

    for cand in candidates:
        if len(traps) >= n:
            break
        # 임시로 함정 추가 → 도달 가능한지 검증
        traps.add(cand)
        if not has_path_avoiding(grid, start, exit_pos, traps):
            traps.discard(cand)   # 막혀버리면 이 칸은 함정 불가

    return traps


def has_path_avoiding(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    avoid: set[tuple[int, int]],
) -> bool:
    """BFS로 start→goal 도달 가능성 검사. avoid 칸은 통과 불가."""
    if start in avoid or goal in avoid:
        return False

    height = len(grid)
    width = len(grid[0])
    visited = {start}
    queue: deque = deque([start])

    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            return True
        for dr, dc in DIRECTIONS_BFS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < height and 0 <= nc < width
                    and grid[nr][nc] == 0
                    and (nr, nc) not in visited
                    and (nr, nc) not in avoid):
                visited.add((nr, nc))
                queue.append((nr, nc))

    return False


# ----------------------------------------------------------------------
# 4. 한 번에 모든 요소 생성
# ----------------------------------------------------------------------
def generate_full_maze(
    width: int = 15,
    height: int = 9,
    trap_count: int = 5,
) -> dict:
    """미로 + 시작/출구/함정 한 번에 생성.

    Returns:
        {
            "grid":   2D list,
            "start":  (row, col),
            "exit":   (row, col),
            "traps":  set of (row, col),
            "dimensions": {"width": w, "height": h},
        }
    """
    grid = generate_maze(width, height)
    start = (1, 1)
    exit_pos = pick_exit(grid, start)
    traps = place_traps(grid, start, exit_pos, trap_count)

    return {
        "grid": grid,
        "start": start,
        "exit": exit_pos,
        "traps": traps,
        "dimensions": {"width": len(grid[0]), "height": len(grid)},
    }


# ----------------------------------------------------------------------
# 단독 실행 테스트 (미로를 텍스트로 시각화)
# ----------------------------------------------------------------------
def _render(grid, start, exit_pos, traps):
    """디버깅용 텍스트 렌더링: S=시작, E=출구, T=함정, #=벽, ' '=길."""
    rows = []
    for r, row in enumerate(grid):
        chars = []
        for c, val in enumerate(row):
            pos = (r, c)
            if pos == start:
                chars.append("S")
            elif pos == exit_pos:
                chars.append("E")
            elif pos in traps:
                chars.append("T")
            elif val == 1:
                chars.append("#")
            else:
                chars.append(" ")
        rows.append("".join(chars))
    return "\n".join(rows)


if __name__ == "__main__":
    random.seed(42)  # 재현 가능한 결과
    maze = generate_full_maze(width=15, height=9, trap_count=5)
    print("===== 15x9 미로 (S=시작, E=출구, T=함정, #=벽) =====")
    print(_render(maze["grid"], maze["start"], maze["exit"], maze["traps"]))
    print(f"\n시작: {maze['start']}")
    print(f"출구: {maze['exit']}")
    print(f"함정 ({len(maze['traps'])}개): {sorted(maze['traps'])}")

    print("\n===== 다른 시드로 한 번 더 =====")
    random.seed(2024)
    maze2 = generate_full_maze(width=15, height=9, trap_count=5)
    print(_render(maze2["grid"], maze2["start"], maze2["exit"], maze2["traps"]))
