"""
퍼즐 API.

- POST /api/puzzle/submit   : 비밀번호/단어 입력형 퍼즐 정답 제출
- POST /api/puzzle/combine  : 단서 조합형 퍼즐 (필요 단서를 모두 가지고 있는지 검증)
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from utils.data_loader import get_data


puzzle_bp = Blueprint("puzzle", __name__, url_prefix="/api/puzzle")


@puzzle_bp.route("/submit", methods=["POST"])
def submit_puzzle():
    """입력형 퍼즐 정답 제출."""
    body = request.get_json(silent=True) or {}
    puzzle_id = body.get("puzzle_id")
    answer = body.get("answer")

    if not puzzle_id or answer is None:
        return error(ErrorCode.INVALID_REQUEST, "puzzle_id와 answer가 필요합니다.")

    puzzles = get_data()["puzzles"]
    puzzle = puzzles.get(puzzle_id)
    if puzzle is None:
        return error(ErrorCode.NOT_FOUND, f"'{puzzle_id}' 퍼즐을 찾을 수 없습니다.")

    # 이미 푼 퍼즐
    if puzzle_id in game_state.solved_puzzles:
        return success(data={
            "correct": True,
            "result_text": "이미 해결한 퍼즐입니다.",
            "reward": None,
        })

    # 선행 아이템 요구 (예: 탈출문 키패드는 탈출키 필요)
    required_item = puzzle.get("required_item")
    if required_item and not game_state.inventory.has(required_item):
        return error(
            ErrorCode.MISSING_REQUIREMENT,
            f"선행 아이템 '{required_item}'이(가) 필요합니다.",
        )

    # 정답 비교 (대소문자 무시 + 공백 정리)
    user_answer = str(answer).strip().lower()
    correct_answer = str(puzzle["answer"]).strip().lower()
    if user_answer != correct_answer:
        return error(ErrorCode.WRONG_ANSWER, "정답이 아닙니다.")

    # --- 정답 처리 ---
    game_state.solved_puzzles.add(puzzle_id)
    state_changed: dict = {"solved_puzzles": list(game_state.solved_puzzles)}
    reward: dict = {}

    # 아이템 보상 (잠긴 상자 → 탈출키 등)
    reward_item = puzzle.get("reward_item")
    if reward_item and game_state.inventory.add(reward_item):
        reward["item"] = reward_item
        state_changed["inventory"] = game_state.inventory.to_list()

    # 단서 보상 (컴퓨터 로그인 → 연구일지)
    reward_clue = puzzle.get("reward_clue")
    if reward_clue:
        game_state.found_clues.push(reward_clue)
        reward["clue"] = reward_clue
        state_changed["found_clues"] = game_state.found_clues.to_list_newest_first()

    # 클리어 트리거 (탈출문 키패드)
    if puzzle.get("triggers_clear"):
        game_state.mark_cleared()
        state_changed["status"] = game_state.status

    return success(
        data={
            "correct": True,
            "result_text": "정답입니다!",
            "reward": reward,
        },
        state_changed=state_changed,
    )


@puzzle_bp.route("/combine", methods=["POST"])
def combine_clues():
    """단서 조합 검증 (제출된 단서 목록이 퍼즐의 필요 단서와 일치하는지)."""
    body = request.get_json(silent=True) or {}
    puzzle_id = body.get("puzzle_id")
    clue_ids = body.get("clue_ids", [])

    if not puzzle_id or not isinstance(clue_ids, list):
        return error(ErrorCode.INVALID_REQUEST, "puzzle_id와 clue_ids[]가 필요합니다.")

    puzzles = get_data()["puzzles"]
    puzzle = puzzles.get(puzzle_id)
    if puzzle is None:
        return error(ErrorCode.NOT_FOUND, f"'{puzzle_id}' 퍼즐을 찾을 수 없습니다.")

    required = set(puzzle.get("required_clues", []))
    provided = set(clue_ids)

    if required == provided:
        return success(data={
            "correct": True,
            "result_text": "필요한 단서가 모두 모였습니다.",
        })

    missing = required - provided
    return success(data={
        "correct": False,
        "result_text": f"단서가 부족하거나 잘못되었습니다. (부족: {len(missing)}개)",
    })
