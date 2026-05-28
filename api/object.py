"""
오브젝트 인터랙션 API.

- POST /api/object/take : 상세 팝업 안의 아이템 영역을 클릭해서 아이템 획득

[디자인]
requires_explicit_pickup=true 인 오브젝트는 investigate로 자동지급되지 않고,
프론트가 상세 팝업의 핫스팟(DETAIL_HOTSPOTS) 클릭 시 이 엔드포인트를 호출한다.
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from utils.data_loader import get_data


object_bp = Blueprint("object", __name__, url_prefix="/api/object")


@object_bp.route("/take", methods=["POST"])
def take_item():
    body = request.get_json(silent=True) or {}
    object_id = body.get("object_id")
    item_id = body.get("item_id")

    if not object_id or not item_id:
        return error(ErrorCode.INVALID_REQUEST, "object_id와 item_id가 필요합니다.")

    objects = get_data()["objects"]
    obj = objects.get(object_id)
    if obj is None:
        return error(ErrorCode.NOT_FOUND, f"'{object_id}' 오브젝트를 찾을 수 없습니다.")

    # 이 오브젝트에서 얻을 수 있는 아이템 목록
    available: list[str] = []
    if obj.get("gives_item"):
        available.append(obj["gives_item"])
    available.extend(obj.get("initial_items", []))

    if item_id not in available:
        return error(
            ErrorCode.INVALID_TARGET,
            f"'{item_id}'은(는) 이 오브젝트에서 얻을 수 있는 아이템이 아닙니다.",
        )

    if game_state.inventory.has(item_id):
        return error(ErrorCode.ALREADY_DONE, "이미 가지고 있습니다.")

    if not game_state.inventory.add(item_id):
        return error(ErrorCode.INVALID_STATE, "인벤토리가 가득 찼습니다.")

    # 이 오브젝트에서 뭔가 꺼냈다는 표시 (상세 이미지가 바뀌도록 — 셋 자료구조)
    game_state.taken_from_objects.add(object_id)

    return success(
        data={"item_id": item_id, "object_id": object_id},
        state_changed={
            "inventory": game_state.inventory.to_list(),
            "taken_from_objects": list(game_state.taken_from_objects),
        },
    )
