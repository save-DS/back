"""
인벤토리 API.

- GET  /api/inventory      : 보유 아이템 목록
- POST /api/inventory/use  : 아이템을 다른 아이템/오브젝트에 사용

[사용 케이스]
1. 아이템 + 아이템 조합 (예: battery + flashlight → uv_flashlight)
2. 아이템 → 오브젝트 사용 (예: scope on microscope → 단서 해독)
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from utils.data_loader import get_data


inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


@inventory_bp.route("", methods=["GET"])
def get_inventory():
    """보유 아이템 목록 (아이템 메타데이터 포함)."""
    items_data = get_data()["items"]
    inventory_ids = game_state.inventory.to_list()
    items = [items_data[iid] for iid in inventory_ids if iid in items_data]
    return success(data={"items": items})


@inventory_bp.route("/use", methods=["POST"])
def use_item():
    """아이템 사용/조합 처리."""
    body = request.get_json(silent=True) or {}
    item_id = body.get("item_id")
    target_id = body.get("target_id")

    if not item_id or not target_id:
        return error(ErrorCode.INVALID_REQUEST, "item_id와 target_id가 필요합니다.")

    if not game_state.inventory.has(item_id):
        return error(ErrorCode.INVALID_ITEM, f"'{item_id}'을(를) 보유하고 있지 않습니다.")

    items_data = get_data()["items"]
    objects_data = get_data()["objects"]
    item = items_data.get(item_id)
    if item is None:
        return error(ErrorCode.NOT_FOUND, f"'{item_id}' 아이템을 찾을 수 없습니다.")

    # --- (1) 아이템 + 아이템 조합 ---
    if target_id in items_data:
        return _combine_items(item, items_data[target_id])

    # --- (2) 아이템 → 오브젝트 사용 ---
    if target_id in objects_data:
        return _use_on_object(item, objects_data[target_id])

    return error(ErrorCode.INVALID_TARGET, f"'{target_id}'은(는) 사용 대상이 아닙니다.")


def _combine_items(item: dict, target_item: dict):
    """두 아이템 조합."""
    if not game_state.inventory.has(target_item["id"]):
        return error(
            ErrorCode.INVALID_TARGET,
            f"'{target_item['id']}'을(를) 보유하고 있지 않습니다.",
        )

    combine_result = item.get("combine_result")
    if not combine_result or target_item["id"] not in item.get("combinable_with", []):
        return error(
            ErrorCode.INVALID_TARGET,
            f"이 두 아이템은 조합할 수 없습니다.",
        )

    # 재료 두 개 제거 후 결과 아이템 추가
    game_state.inventory.remove(item["id"])
    game_state.inventory.remove(target_item["id"])
    game_state.inventory.add(combine_result)

    return success(
        data={
            "result_text": f"{item['name']}와(과) {target_item['name']}을(를) 합쳐 새 아이템을 만들었다.",
            "effect": "combine",
            "result_item": combine_result,
        },
        state_changed={"inventory": game_state.inventory.to_list()},
    )


def _use_on_object(item: dict, target: dict):
    """아이템을 오브젝트에 사용."""
    if target.get("required_item") != item["id"]:
        return error(
            ErrorCode.INVALID_TARGET,
            f"{item['name']}을(를) 여기에 쓸 수 없다.",
        )

    state_changed: dict = {}
    result_text: str

    # 단서 해독 (현미경에 스코프, 화이트보드에 UV 등)
    clue_id = target.get("gives_clue_on_use")
    if clue_id:
        # 같은 단서를 또 발견하면 중복 push 방지
        if clue_id not in set(game_state.found_clues.to_list()):
            game_state.found_clues.push(clue_id)
            state_changed["found_clues"] = game_state.found_clues.to_list_newest_first()

        # 시각적 결과 텍스트
        if item["id"] == "microscope_scope":
            result_text = target.get("narration_with_scope", "단서가 드러났다.")
        elif item["id"] == "uv_flashlight":
            result_text = target.get("narration_with_uv", "단서가 드러났다.")
        else:
            result_text = "단서가 드러났다."

        return success(
            data={
                "result_text": result_text,
                "effect": "reveal_clue",
                "found_clue": clue_id,
            },
            state_changed=state_changed,
        )

    # 탈출문 → 보안장치 해제 (탈출키 사용)
    if target["id"] == "escape_door" and item["id"] == "escape_key":
        return success(data={
            "result_text": target.get("narration_unlocked", "잠금이 풀렸다."),
            "effect": "unlock_keypad",
        })

    return success(data={
        "result_text": f"{item['name']}을(를) 사용했다.",
        "effect": "generic_use",
    })
