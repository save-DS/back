"""
시점 전환 API.

- POST /api/view/turn     : 좌/우 시점 전환 (left ↔ center ↔ right)
- GET  /api/view/current  : 현재 시점 + 보이는 오브젝트
- POST /api/view/back     : 상세 뷰에서 직전 화면으로 복귀 (스택 pop)
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from utils.data_loader import get_data


view_bp = Blueprint("view", __name__, url_prefix="/api/view")


# 시점 전환 규칙: 선형(linear) — left ↔ center ↔ right
_TURN_TABLE = {
    ("center", "left"):  "left",
    ("center", "right"): "right",
    ("left",   "right"): "center",
    ("right",  "left"):  "center",
}


def _get_view_objects(room_id: str, view: str) -> list[dict]:
    """해당 방의 해당 시점에 보이는 오브젝트 목록을 반환."""
    rooms = get_data()["rooms"]
    objects = get_data()["objects"]

    object_ids = rooms.get(room_id, {}).get("views", {}).get(view, {}).get("objects", [])
    return [objects[oid] for oid in object_ids if oid in objects]


@view_bp.route("/turn", methods=["POST"])
def turn_view():
    """좌/우 시점 전환."""
    body = request.get_json(silent=True) or {}
    direction = body.get("direction")

    if direction not in ("left", "right"):
        return error(
            ErrorCode.INVALID_REQUEST,
            "direction은 'left' 또는 'right'여야 합니다.",
        )

    if game_state.mode != "first_person":
        return error(
            ErrorCode.INVALID_STATE,
            "1인칭 모드에서만 시점 전환이 가능합니다.",
        )

    next_view = _TURN_TABLE.get((game_state.current_view, direction))
    if next_view is None:
        return error(
            ErrorCode.INVALID_STATE,
            f"'{game_state.current_view}'에서 '{direction}'으로 더 회전할 수 없습니다.",
        )

    game_state.current_view = next_view
    return success(
        data={
            "current_view": next_view,
            "objects": _get_view_objects(game_state.current_room, next_view),
        },
        state_changed={"current_view": next_view},
    )


@view_bp.route("/current", methods=["GET"])
def get_current_view():
    """현재 시점 + 보이는 오브젝트."""
    return success(data={
        "current_view": game_state.current_view,
        "objects": _get_view_objects(game_state.current_room, game_state.current_view),
    })


@view_bp.route("/back", methods=["POST"])
def go_back():
    """상세 뷰에서 직전 화면으로 복귀 (view_stack pop)."""
    if game_state.view_stack.is_empty():
        return error(
            ErrorCode.INVALID_STATE,
            "되돌아갈 화면이 없습니다.",
        )

    previous = game_state.view_stack.pop()
    return success(
        data={"previous_view": previous},
        state_changed={"view_stack": game_state.view_stack.to_list()},
    )
