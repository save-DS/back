"""
오브젝트 조사 API.

- POST /api/investigate : 1인칭 모드에서 오브젝트 클릭 처리

[동작]
- 오브젝트 ID 검증
- 상태에 맞는 내레이션 생성 (퍼즐 해결 여부 등에 따라)
- 첫 조사라면: investigated_objects에 추가, 아이템/단서 보상 지급
- view_stack에 push (뒤로가기용)
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from utils.data_loader import get_data


investigate_bp = Blueprint("investigate", __name__, url_prefix="/api")


def _build_narration(obj: dict) -> str:
    """오브젝트와 현재 게임 상태를 보고 적절한 내레이션을 고른다."""
    # 퍼즐이 해결된 경우
    puzzle_id = obj.get("puzzle")
    if puzzle_id and puzzle_id in game_state.solved_puzzles:
        return obj.get("narration_solved", obj["narration_default"])

    return obj["narration_default"]


@investigate_bp.route("/investigate", methods=["POST"])
def investigate():
    body = request.get_json(silent=True) or {}
    object_id = body.get("object_id")

    if not object_id:
        return error(ErrorCode.INVALID_REQUEST, "object_id가 필요합니다.")

    if game_state.mode != "first_person":
        return error(
            ErrorCode.INVALID_STATE,
            "1인칭 모드에서만 조사할 수 있습니다.",
        )

    objects = get_data()["objects"]
    obj = objects.get(object_id)
    if obj is None:
        return error(ErrorCode.NOT_FOUND, f"'{object_id}' 오브젝트를 찾을 수 없습니다.")

    # 첫 조사인지 판정
    is_first_time = object_id not in game_state.investigated_objects

    found_items: list[str] = []
    found_clue: str | None = None
    state_changed: dict = {}

    if is_first_time:
        game_state.investigated_objects.add(object_id)
        state_changed["investigated_objects"] = list(game_state.investigated_objects)

        # requires_explicit_pickup이 true면 아이템 자동지급 안 함
        # (상세 팝업 안의 핫스팟을 직접 클릭해야 아이템 얻음 - /api/object/take 사용)
        if not obj.get("requires_explicit_pickup"):
            # 단일 아이템 자동 지급 (예: 코드 노트)
            single_item = obj.get("gives_item")
            if single_item and game_state.inventory.add(single_item):
                found_items.append(single_item)

            # 초기 아이템들 자동 지급
            for item_id in obj.get("initial_items", []):
                if game_state.inventory.add(item_id):
                    found_items.append(item_id)

            if found_items:
                state_changed["inventory"] = game_state.inventory.to_list()

        # 단서 자동 지급 (예: 달력의 0418, 러그 아래 숫자)
        clue_id = obj.get("gives_clue_on_investigate")
        if clue_id:
            game_state.found_clues.push(clue_id)
            found_clue = clue_id
            state_changed["found_clues"] = game_state.found_clues.to_list_newest_first()

    # 뒤로가기를 위해 현재 메인 뷰를 스택에 push
    game_state.view_stack.push({
        "type": "main_view",
        "view": game_state.current_view,
    })
    state_changed["view_stack"] = game_state.view_stack.to_list()

    return success(
        data={
            "object": obj,
            "result_text": _build_narration(obj),
            "found_items": found_items,
            "found_clue": found_clue,
        },
        state_changed=state_changed,
    )
