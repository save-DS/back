"""
힌트 API.

- GET  /api/hint/maze     : 미로 BFS 최단 경로 (미로 모드 전용, 그대로 유지)
- GET  /api/hint/puzzle   : 특정 퍼즐의 텍스트 힌트 + 부족 단서 안내 (룰베이스)
- GET  /api/hint/progress : 진행 분석 + 다음 목표 추천 (룰베이스)
- GET  /api/hint/item-use : 보유 아이템 활용 추천 (룰베이스)
- POST /api/hint/ask      : AI 자유 질문 (1인칭 HINT 버튼이 사용. Claude API)

룰베이스 힌트(puzzle/progress/item-use)는 AI 힌트의 내부 컨텍스트로도 쓰이고,
API 키가 없을 때의 폴백으로도 활용 가능하도록 남겨둔다.
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from services.maze_bfs import next_step
from services.puzzle_graph import get_puzzle_graph
from services.ai_hint import ask_hint
from utils.data_loader import get_data


hint_bp = Blueprint("hint", __name__, url_prefix="/api/hint")


# ----------------------------------------------------------------------
# 미로 BFS (Issue #4)
# ----------------------------------------------------------------------
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

    path_as_list = [list(p) for p in result["path"]]
    return success(data={
        "next_direction": result["direction"],
        "remaining_steps": result["remaining_steps"],
        "path": path_as_list,
        "hint_text": f"{result['direction']}으로 이동하세요. (출구까지 {result['remaining_steps']}칸)",
    })


# ----------------------------------------------------------------------
# 1인칭 - 특정 퍼즐 힌트
# ----------------------------------------------------------------------
@hint_bp.route("/puzzle", methods=["GET"])
def puzzle_hint():
    puzzle_id = request.args.get("puzzle_id")
    if not puzzle_id:
        return error(ErrorCode.INVALID_REQUEST, "puzzle_id 쿼리 파라미터가 필요합니다.")

    puzzles = get_data()["puzzles"]
    puzzle = puzzles.get(puzzle_id)
    if puzzle is None:
        return error(ErrorCode.NOT_FOUND, f"'{puzzle_id}' 퍼즐을 찾을 수 없습니다.")

    if puzzle_id in game_state.solved_puzzles:
        return success(data={
            "puzzle_id": puzzle_id,
            "hint_text": "이미 해결한 퍼즐입니다.",
            "already_solved": True,
        })

    # 텍스트 힌트 + 부족분 분석
    graph = get_puzzle_graph()
    missing = graph.missing_for(puzzle_id, game_state)

    return success(data={
        "puzzle_id": puzzle_id,
        "hint_text": puzzle.get("hint"),
        "already_solved": False,
        "missing_clues": missing["missing_clues"],
        "missing_item": missing["missing_item"],
        "suggestions": missing["suggestions"],
    })


# ----------------------------------------------------------------------
# 1인칭 - 진행 분석
# ----------------------------------------------------------------------
@hint_bp.route("/progress", methods=["GET"])
def progress_hint():
    graph = get_puzzle_graph()
    puzzles_data = get_data()["puzzles"]

    # 진행 요약
    summary = {
        "solved_puzzles": len(game_state.solved_puzzles),
        "total_puzzles": len(puzzles_data),
        "items_collected": game_state.inventory.count(),
        "clues_found": game_state.found_clues.size(),
        "investigated_objects": len(game_state.investigated_objects),
        "status": game_state.status,
    }

    solvable = graph.next_solvable_puzzles(game_state)

    # 가장 가까운 미해결 퍼즐 (부족 단서 가장 적은 것)
    closest = None
    for pid in puzzles_data:
        if pid in game_state.solved_puzzles:
            continue
        info = graph.missing_for(pid, game_state)
        missing_count = len(info["missing_clues"])
        if closest is None or missing_count < closest["missing_count"]:
            closest = {
                "puzzle_id": pid,
                "missing_count": missing_count,
                "missing_clues": info["missing_clues"],
                "suggestions": info["suggestions"],
            }

    # 현재 목표 문구
    if game_state.status == "cleared":
        current_goal = "게임을 클리어했습니다."
    elif solvable:
        names = ", ".join(p["puzzle_id"] for p in solvable)
        current_goal = f"퍼즐을 풀 수 있습니다: {names}"
    elif closest and closest["missing_count"] > 0:
        current_goal = (
            f"퍼즐 '{closest['puzzle_id']}'을(를) 풀려면 "
            f"단서 {closest['missing_count']}개가 더 필요합니다."
        )
    else:
        current_goal = "주변을 더 조사해보세요."

    return success(data={
        "summary": summary,
        "current_goal": current_goal,
        "solvable_now": solvable,
        "closest_puzzle": closest,
    })


# ----------------------------------------------------------------------
# 1인칭 - 아이템 사용 추천
# ----------------------------------------------------------------------
@hint_bp.route("/item-use", methods=["GET"])
def item_use_hint():
    graph = get_puzzle_graph()
    items_data = get_data()["items"]

    suggestions = []
    for item_id in game_state.inventory.to_list():
        info = graph.where_to_use(item_id)
        if info and info["suggestions"]:
            suggestions.append({
                "item_id": item_id,
                "item_name": items_data.get(item_id, {}).get("name", item_id),
                "suggestions": info["suggestions"],
            })

    return success(data={"suggestions": suggestions})


# ----------------------------------------------------------------------
# 1인칭 - AI 자유 질문 (Claude API)
# ----------------------------------------------------------------------
@hint_bp.route("/ask", methods=["POST"])
def ask_ai_hint():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return error(ErrorCode.INVALID_REQUEST, "질문을 입력해주세요.")

    # 미로 모드에서는 AI 자유 질문 대신 미로 힌트(BFS)를 쓰도록 유도
    if game_state.mode != "first_person":
        return error(
            ErrorCode.INVALID_STATE,
            "AI 힌트는 1인칭 탐색 모드에서만 사용할 수 있습니다.",
        )

    game_state.ai_query_count += 1

    try:
        answer = ask_hint(question, game_state)
    except RuntimeError as e:
        # API 키 미설정 등 설정 문제
        return error(ErrorCode.INVALID_STATE, str(e))
    except Exception:
        return error(
            ErrorCode.INVALID_STATE,
            "AI 힌트 생성에 실패했습니다. 잠시 후 다시 시도해주세요.",
        )

    return success(
        data={"question": question, "answer": answer},
        state_changed={"ai_query_count": game_state.ai_query_count},
    )
