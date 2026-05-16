"""
MazeBFS - 미로에서 최단 경로를 찾는 BFS 알고리즘.

[자료구조]
- 큐 (collections.deque) : BFS의 핵심
- 셋 (visited)          : 이미 방문한 좌표 (중복 탐색 방지)
- 딕셔너리 (came_from)  : 경로 복원용 (각 노드의 이전 노드 기록)

[입력 형식]
미로는 2차원 리스트:
    0 = 이동 가능한 길
    1 = 벽 (이동 불가)

좌표는 (row, col) 튜플.

[게임 내 사용처]
- /api/hint/maze : 플레이어 위치 → 출구까지 최단 경로 다음 방향 안내
- AI 힌트에 "다음 한 칸 어디로 가야 함" 컨텍스트로 제공
"""
from collections import deque


# 4방향 이동 (위/아래/왼쪽/오른쪽)
DIRECTIONS = [
    (-1, 0, "up"),
    (1, 0, "down"),
    (0, -1, "left"),
    (0, 1, "right"),
]


def _is_walkable(maze: list[list[int]], row: int, col: int) -> bool:
    """좌표가 미로 안에 있고 벽이 아니면 True."""
    if row < 0 or row >= len(maze):
        return False
    if col < 0 or col >= len(maze[0]):
        return False
    return maze[row][col] == 0


def find_shortest_path(
    maze: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    avoid: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]] | None:
    """start에서 goal까지의 최단 경로를 좌표 리스트로 반환.

    Args:
        avoid: 피해야 할 좌표들의 셋 (예: 미로의 함정 위치)

    경로가 없으면 None.
    경로에는 start와 goal이 모두 포함된다.
    """
    if avoid is None:
        avoid = set()
    if not _is_walkable(maze, *start) or not _is_walkable(maze, *goal):
        return None
    if start in avoid or goal in avoid:
        return None
    if start == goal:
        return [start]

    visited: set[tuple[int, int]] = {start}
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    queue: deque[tuple[int, int]] = deque([start])

    while queue:
        current = queue.popleft()
        for dr, dc, _ in DIRECTIONS:
            next_pos = (current[0] + dr, current[1] + dc)
            if next_pos in visited or not _is_walkable(maze, *next_pos):
                continue
            if next_pos in avoid:
                continue
            visited.add(next_pos)
            came_from[next_pos] = current
            if next_pos == goal:
                return _reconstruct_path(came_from, start, goal)
            queue.append(next_pos)

    return None  # 경로 없음


def _reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """came_from 딕셔너리로부터 start→goal 경로 복원."""
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def next_step(
    maze: list[list[int]],
    current: tuple[int, int],
    goal: tuple[int, int],
    avoid: set[tuple[int, int]] | None = None,
) -> dict | None:
    """현재 위치에서 goal까지 최단 경로 상의 "다음 한 칸" 정보 반환.

    Args:
        avoid: 피해야 할 좌표들의 셋 (함정 등)

    Returns:
        {
            "direction": "up" | "down" | "left" | "right",
            "next_position": (row, col),
            "remaining_steps": int,
            "path": [(row, col), ...]   # 전체 경로 (힌트 시각화용)
        }
        경로 없으면 None.
    """
    path = find_shortest_path(maze, current, goal, avoid=avoid)
    if path is None or len(path) < 2:
        return None

    next_pos = path[1]
    dr = next_pos[0] - current[0]
    dc = next_pos[1] - current[1]
    direction = next(d[2] for d in DIRECTIONS if (d[0], d[1]) == (dr, dc))
    return {
        "direction": direction,
        "next_position": next_pos,
        "remaining_steps": len(path) - 1,
        "path": path,
    }


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 0 = 길, 1 = 벽
    # S = 시작(0,0), E = 출구(4,4)
    test_maze = [
        [0, 0, 1, 0, 0],
        [1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    start = (0, 0)
    goal = (4, 4)

    print("===== 미로 BFS 테스트 =====")
    print("미로 (0=길, 1=벽):")
    for row in test_maze:
        print("  ", row)
    print(f"\n시작: {start}, 출구: {goal}")

    path = find_shortest_path(test_maze, start, goal)
    print(f"\n최단 경로 ({len(path)}칸):")
    for step in path:
        print(f"  {step}")

    print("\n===== 다음 한 칸 안내 (힌트용) =====")
    hint = next_step(test_maze, current=(0, 0), goal=goal)
    print(hint)

    print("\n===== 경로 없는 경우 =====")
    blocked_maze = [
        [0, 1],
        [1, 0],
    ]
    print("막힌 미로:", find_shortest_path(blocked_maze, (0, 0), (1, 1)))
