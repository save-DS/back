"""
미로 API.

- GET  /api/maze/map         : 미로 그리드 + 시작/출구/현재위치 (※ 함정 제외)
- POST /api/maze/move        : 4방향 한 칸 이동
  - 벽/경계 → COLLISION
  - 함정 → trap_hit, 시작점 리셋
  - 출구 → reached_exit, 게임 클리어
- POST /api/maze/regenerate  : 미로 즉시 새로 생성
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from services.maze_generator import generate_full_maze


maze_bp = Blueprint("maze", __name__, url_prefix="/api/maze")


_DIRECTION_DELTA = {
    "up":    (-1, 0),
    "down":  (1, 0),
    "left":  (0, -1),
    "right": (0, 1),
}


def _require_maze_mode():
    if game_state.mode != "maze":
        return error(ErrorCode.INVALID_STATE, "미로 모드가 아닙니다.")
    if not game_state.maze_grid:
        return error(ErrorCode.INVALID_STATE, "미로가 아직 생성되지 않았습니다.")
    return None


@maze_bp.route("/map", methods=["GET"])
def get_map():
    err = _require_maze_mode()
    if err:
        return err

    return success(data={
        "grid": game_state.maze_grid,
        "start": list(game_state.maze_start),
        "exit": list(game_state.maze_exit),
        "current_position": list(game_state.maze_position),
        "dimensions": {
            "width": len(game_state.maze_grid[0]),
            "height": len(game_state.maze_grid),
        },
    })


@maze_bp.route("/move", methods=["POST"])
def move():
    err = _require_maze_mode()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    direction = body.get("direction")
    if direction not in _DIRECTION_DELTA:
        return error(
            ErrorCode.INVALID_REQUEST,
            "direction은 up/down/left/right 중 하나여야 합니다.",
        )

    dr, dc = _DIRECTION_DELTA[direction]
    cur_r, cur_c = game_state.maze_position
    nr, nc = cur_r + dr, cur_c + dc

    height = len(game_state.maze_grid)
    width = len(game_state.maze_grid[0])

    # 경계/벽 충돌
    if nr < 0 or nr >= height or nc < 0 or nc >= width:
        return error(ErrorCode.COLLISION, "맵 바깥으로 나갈 수 없습니다.")
    if game_state.maze_grid[nr][nc] == 1:
        return error(ErrorCode.COLLISION, "벽으로 이동할 수 없습니다.")

    # 이동 성공
    game_state.maze_position = (nr, nc)
    game_state.maze_steps += 1

    state_changed: dict = {
        "maze_position": [nr, nc],
        "maze_steps": game_state.maze_steps,
    }
    data: dict = {
        "new_position": [nr, nc],
        "steps": game_state.maze_steps,
        "trap_hit": False,
        "reset_to_start": False,
        "reached_exit": False,
    }

    # 함정 적중 → 시작점 리셋
    if (nr, nc) in game_state.maze_traps:
        start = game_state.maze_start
        game_state.maze_position = start
        game_state.maze_trap_hits += 1
        data.update({
            "new_position": list(start),
            "trap_hit": True,
            "reset_to_start": True,
            "result_text": "함정에 걸렸다! 시작점으로 돌아갑니다.",
        })
        state_changed["maze_position"] = list(start)
        state_changed["maze_trap_hits"] = game_state.maze_trap_hits
        return success(data=data, state_changed=state_changed)

    # 출구 도달 → 클리어
    if (nr, nc) == game_state.maze_exit:
        game_state.maze_reached_exit = True
        game_state.mark_cleared()
        data.update({
            "reached_exit": True,
            "result_text": "탈출 성공!",
        })
        state_changed["maze_reached_exit"] = True
        state_changed["status"] = game_state.status
        return success(data=data, state_changed=state_changed)

    return success(data=data, state_changed=state_changed)


@maze_bp.route("/regenerate", methods=["POST"])
def regenerate():
    """미로를 강제로 새로 생성 (포기/디버깅용)."""
    err = _require_maze_mode()
    if err:
        return err

    maze = generate_full_maze(width=20, height=14, trap_count=5)
    game_state.maze_grid = maze["grid"]
    game_state.maze_start = maze["start"]
    game_state.maze_exit = maze["exit"]
    game_state.maze_traps = maze["traps"]
    game_state.maze_position = maze["start"]
    game_state.maze_steps = 0
    game_state.maze_trap_hits = 0
    game_state.maze_reached_exit = False

    return success(
        data={
            "grid": maze["grid"],
            "start": list(maze["start"]),
            "exit": list(maze["exit"]),
            "current_position": list(maze["start"]),
            "dimensions": {
                "width": len(maze["grid"][0]),
                "height": len(maze["grid"]),
            },
        },
        state_changed={
            "maze_position": list(maze["start"]),
            "maze_steps": 0,
            "maze_trap_hits": 0,
            "maze_reached_exit": False,
        },
    )
