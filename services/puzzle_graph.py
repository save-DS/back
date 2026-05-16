"""
PuzzleGraph - 퍼즐/아이템/단서/오브젝트 사이의 관계를 표현하는 그래프.

[자료구조]
- 인접 관계를 딕셔너리(인덱스)들로 표현
- 그래프 탐색을 통해 "지금 풀 수 있는 퍼즐", "이 단서 어디서 구하나",
  "이 아이템 어디 쓰나" 등을 자동 추론

[게임 내 사용처]
- /api/hint/puzzle    : 부족한 단서 자동 안내
- /api/hint/progress  : 풀 수 있는 퍼즐 추천
- /api/hint/item-use  : 아이템 활용 추천
- 추후 AI 힌트 컨텍스트로도 같이 전달
"""


class PuzzleGraph:
    """퍼즐/아이템/단서/오브젝트 사이의 관계 그래프."""

    def __init__(self, puzzles: dict, items: dict, objects: dict):
        self.puzzles = puzzles
        self.items = items
        self.objects = objects
        # 역인덱스: clue_id → [그 단서를 얻는 방법들]
        self._clue_sources: dict[str, list[dict]] = {}
        self._build_indexes()

    # ------------------------------------------------------------------
    # 인덱스 구성
    # ------------------------------------------------------------------
    def _build_indexes(self) -> None:
        """오브젝트/퍼즐 데이터를 훑어서 단서 출처를 역인덱싱."""
        for obj_id, obj in self.objects.items():
            # 단순 조사로 얻는 단서
            cid = obj.get("gives_clue_on_investigate")
            if cid:
                self._add_source(cid, {
                    "method": "investigate",
                    "object_id": obj_id,
                    "hint": f"'{obj['name']}'을(를) 조사하세요.",
                })

            # 아이템을 써야 얻는 단서
            cid = obj.get("gives_clue_on_use")
            if cid:
                req_item_id = obj.get("required_item")
                req_item_name = self.items.get(req_item_id, {}).get("name", req_item_id)
                self._add_source(cid, {
                    "method": "use_item",
                    "object_id": obj_id,
                    "required_item": req_item_id,
                    "hint": f"'{obj['name']}'에 '{req_item_name}'을(를) 사용하세요.",
                })

            # 퍼즐을 풀어야 얻는 단서
            cid = obj.get("gives_clue_on_solve")
            if cid:
                puzzle_id = obj.get("puzzle")
                self._add_source(cid, {
                    "method": "solve_puzzle",
                    "object_id": obj_id,
                    "puzzle_id": puzzle_id,
                    "hint": f"'{obj['name']}'의 퍼즐을 해결하세요.",
                })

        # 퍼즐 자체 보상으로 단서가 나오는 경우 (예: 컴퓨터 → research_doc)
        for puzzle_id, puzzle in self.puzzles.items():
            cid = puzzle.get("reward_clue")
            if cid:
                self._add_source(cid, {
                    "method": "solve_puzzle",
                    "puzzle_id": puzzle_id,
                    "hint": f"'{puzzle_id}' 퍼즐을 해결하면 얻을 수 있습니다.",
                })

    def _add_source(self, clue_id: str, source: dict) -> None:
        self._clue_sources.setdefault(clue_id, []).append(source)

    # ------------------------------------------------------------------
    # 조회 - 단서가 어디서 나오는가
    # ------------------------------------------------------------------
    def sources_of(self, clue_id: str) -> list[dict]:
        """이 단서를 얻을 수 있는 방법들."""
        return list(self._clue_sources.get(clue_id, []))

    # ------------------------------------------------------------------
    # 조회 - 지금 풀 수 있는 퍼즐
    # ------------------------------------------------------------------
    def next_solvable_puzzles(self, state) -> list[dict]:
        """현재 상태로 풀 수 있는 퍼즐 목록 (이미 푼 건 제외)."""
        result = []
        found = set(state.found_clues.to_list())
        for pid, puzzle in self.puzzles.items():
            if pid in state.solved_puzzles:
                continue
            if self._is_solvable(puzzle, state, found):
                result.append({
                    "puzzle_id": pid,
                    "type": puzzle.get("type"),
                    "hint": puzzle.get("hint"),
                })
        return result

    @staticmethod
    def _is_solvable(puzzle: dict, state, found_clues: set) -> bool:
        # 필요 단서가 다 있는가
        required = set(puzzle.get("required_clues", []))
        if not required.issubset(found_clues):
            return False
        # 필요 아이템이 있는가
        req_item = puzzle.get("required_item")
        if req_item and not state.inventory.has(req_item):
            return False
        return True

    # ------------------------------------------------------------------
    # 조회 - 특정 퍼즐의 부족분
    # ------------------------------------------------------------------
    def missing_for(self, puzzle_id: str, state) -> dict | None:
        """특정 퍼즐을 풀기 위해 부족한 단서/아이템 + 조달 방법."""
        puzzle = self.puzzles.get(puzzle_id)
        if not puzzle:
            return None

        found = set(state.found_clues.to_list())
        required = set(puzzle.get("required_clues", []))
        missing_clues = sorted(required - found)

        req_item = puzzle.get("required_item")
        missing_item = req_item if req_item and not state.inventory.has(req_item) else None

        # 부족한 단서마다 조달 방법 추천
        suggestions = []
        for cid in missing_clues:
            suggestions.append({
                "clue_id": cid,
                "where_to_find": self.sources_of(cid),
            })

        return {
            "puzzle_id": puzzle_id,
            "missing_clues": missing_clues,
            "missing_item": missing_item,
            "suggestions": suggestions,
        }

    # ------------------------------------------------------------------
    # 조회 - 이 아이템 어디 쓰나
    # ------------------------------------------------------------------
    def where_to_use(self, item_id: str) -> dict | None:
        """주어진 아이템이 사용될 수 있는 모든 곳."""
        item = self.items.get(item_id)
        if not item:
            return None

        suggestions = []

        # 아이템 + 아이템 조합
        for other_id in item.get("combinable_with", []):
            other = self.items.get(other_id, {})
            suggestions.append({
                "method": "combine",
                "with": other_id,
                "with_name": other.get("name", other_id),
                "result": item.get("combine_result"),
                "hint": f"'{other.get('name', other_id)}'와(과) 조합할 수 있습니다.",
            })

        # 오브젝트에 사용
        for obj_id in item.get("usable_with", []):
            obj = self.objects.get(obj_id, {})
            suggestions.append({
                "method": "use_on_object",
                "target": obj_id,
                "target_name": obj.get("name", obj_id),
                "hint": f"'{obj.get('name', obj_id)}'에 사용할 수 있습니다.",
            })

        # 퍼즐의 선행 아이템
        for pid, puzzle in self.puzzles.items():
            if puzzle.get("required_item") == item_id:
                suggestions.append({
                    "method": "required_for_puzzle",
                    "puzzle_id": pid,
                    "hint": f"'{pid}' 퍼즐을 풀 때 필요합니다.",
                })

        return {
            "item_id": item_id,
            "item_name": item.get("name"),
            "suggestions": suggestions,
        }


# ----------------------------------------------------------------------
# 싱글톤 접근자
# ----------------------------------------------------------------------
_graph_cache: PuzzleGraph | None = None


def get_puzzle_graph() -> PuzzleGraph:
    """게임 데이터에서 PuzzleGraph 인스턴스를 만들어 캐싱."""
    global _graph_cache
    if _graph_cache is None:
        from utils.data_loader import get_data
        data = get_data()
        _graph_cache = PuzzleGraph(
            puzzles=data["puzzles"],
            items=data["items"],
            objects=data["objects"],
        )
    return _graph_cache


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    from utils.data_loader import get_data

    data = get_data()
    g = PuzzleGraph(data["puzzles"], data["items"], data["objects"])

    print("===== clue_3 출처 =====")
    for src in g.sources_of("clue_3"):
        print(" ", src)

    print("\n===== clue_9 출처 =====")
    for src in g.sources_of("clue_9"):
        print(" ", src)

    print("\n===== research_doc 출처 =====")
    for src in g.sources_of("research_doc"):
        print(" ", src)

    print("\n===== battery 활용처 =====")
    for s in g.where_to_use("battery")["suggestions"]:
        print(" ", s)

    print("\n===== escape_key 활용처 =====")
    for s in g.where_to_use("escape_key")["suggestions"]:
        print(" ", s)

    # 가상 GameState 시나리오
    from services.game_state import GameState
    gs = GameState()
    gs.reset()

    print("\n===== [초기 상태] 지금 풀 수 있는 퍼즐 =====")
    print(g.next_solvable_puzzles(gs))

    print("\n===== [초기 상태] cabinet_password 부족분 =====")
    print(g.missing_for("cabinet_password", gs))

    # 단서 다 모으기
    for cid in ["clue_3", "clue_9", "clue_6", "clue_2"]:
        gs.found_clues.push(cid)

    print("\n===== [단서 4개 보유] 지금 풀 수 있는 퍼즐 =====")
    print(g.next_solvable_puzzles(gs))
