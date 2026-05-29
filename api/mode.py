"""
모드 전환 API.

- POST /api/mode/switch : 1인칭 ↔ 미로 전환
  - 미로 진입 시 처음이면 새 미로 자동 생성
  - 같은 게임 세션에서 다시 미로로 와도 같은 미로 유지
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from services.maze_generator import generate_full_maze


mode_bp = Blueprint("mode", __name__, url_prefix="/api/mode")


def _ensure_maze_exists() -> dict:
    """미로가 아직 없으면 새로 생성. 있으면 기존 것 반환."""
    if not game_state.maze_grid:
        maze = generate_full_maze(width=20, height=14, trap_count=5)
        game_state.maze_grid = maze["grid"]
        game_state.maze_start = maze["start"]
        game_state.maze_exit = maze["exit"]
        game_state.maze_traps = maze["traps"]
        game_state.maze_position = maze["start"]
        game_state.maze_steps = 0
        game_state.maze_trap_hits = 0
        game_state.maze_reached_exit = False

    return {
        "grid": game_state.maze_grid,
        "start": list(game_state.maze_start),
        "exit": list(game_state.maze_exit),
        "current_position": list(game_state.maze_position),
        "dimensions": {
            "width": len(game_state.maze_grid[0]),
            "height": len(game_state.maze_grid),
        },
    }


@mode_bp.route("/switch", methods=["POST"])
def switch_mode():
    body = request.get_json(silent=True) or {}
    target = body.get("target_mode")

    if target not in ("first_person", "maze"):
        return error(
            ErrorCode.INVALID_REQUEST,
            "target_mode는 'first_person' 또는 'maze'여야 합니다.",
        )

    if game_state.mode == target:
        return error(
            ErrorCode.INVALID_STATE,
            f"이미 '{target}' 모드입니다.",
        )

    state_changed: dict = {"mode": target}
    init_data: dict = {}

    if target == "maze":
        init_data = _ensure_maze_exists()
        state_changed["maze_position"] = list(game_state.maze_position)

    game_state.switch_mode(target)

    return success(
        data={"mode": target, "init_data": init_data},
        state_changed=state_changed,
    )
