"""
힌트 API.

이번 이슈에서는 미로 힌트만 구현. 나머지 힌트(퍼즐/진행/아이템/AI)는 Issue #5.

- GET /api/hint/maze : 현재 위치 → 출구까지 BFS 최단 경로 반환 (함정 회피)
                      프론트가 받은 path를 2초간 시각화.
"""
from flask import Blueprint

from api import success, error, ErrorCode
from services.game_state import game_state
from services.maze_bfs import next_step


hint_bp = Blueprint("hint", __name__, url_prefix="/api/hint")


@hint_bp.route("/maze", methods=["GET"])
def maze_hint():
    if game_state.mode != "maze":
        return error(ErrorCode.INVALID_STATE, "미로 모드에서만 사용 가능합니다.")
    if not game_state.maze_grid:
        return error(ErrorCode.INVALID_STATE, "미로가 생성되지 않았습니다.")

    result = next_step(
        maze=game_state.maze_grid,
        current=game_state.maze_position,
        goal=game_state.maze_exit,
        avoid=game_state.maze_traps,
    )

    if result is None:
        return error(
            ErrorCode.INVALID_STATE,
            "경로를 찾을 수 없습니다 (이미 출구이거나 막힘).",
        )

    # path는 [(r,c), ...] 튜플 리스트 → JSON 호환 [[r,c],...]로 변환
    path_as_list = [list(p) for p in result["path"]]

    return success(data={
        "next_direction": result["direction"],
        "remaining_steps": result["remaining_steps"],
        "path": path_as_list,
        "hint_text": f"{result['direction']}으로 이동하세요. (출구까지 {result['remaining_steps']}칸)",
    })
