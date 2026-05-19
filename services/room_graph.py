"""
RoomGraph - 방 사이의 연결 관계를 표현하는 무방향 그래프.

[자료구조]
- 인접 리스트(dict[str, list[str]])
  예: {"main_lab": ["hallway", "lab_b"], "hallway": ["main_lab"]}

[게임 내 사용처]
- 방 이동 가능 여부 확인 (현재 방 → 옆 방으로 갈 수 있나?)
- 특정 방까지 도달 가능한지 확인 (그래프 탐색)
- AI 힌트에서 "다음에 갈 방" 추천

[설계 노트]
- 무방향 그래프 (양방향 이동 가능)
- 향후 확장: 엣지에 조건 (특정 아이템/퍼즐 해결 필요) 추가 가능
"""
from collections import deque


class RoomGraph:
    """방 연결 관계를 관리하는 그래프."""

    def __init__(self):
        # adjacency list: room_id → 연결된 room_id 리스트
        self._adjacency: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # 구성
    # ------------------------------------------------------------------
    def add_room(self, room_id: str) -> None:
        """노드 추가 (중복 추가는 무시)."""
        if room_id not in self._adjacency:
            self._adjacency[room_id] = []

    def add_edge(self, a: str, b: str) -> None:
        """양방향 연결 추가.

        a, b 노드가 없으면 자동으로 만든다.
        이미 연결돼있으면 중복 추가하지 않는다.
        """
        self.add_room(a)
        self.add_room(b)
        if b not in self._adjacency[a]:
            self._adjacency[a].append(b)
        if a not in self._adjacency[b]:
            self._adjacency[b].append(a)

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------
    def get_neighbors(self, room_id: str) -> list[str]:
        """해당 방과 직접 연결된 방 목록."""
        return list(self._adjacency.get(room_id, []))

    def is_connected(self, a: str, b: str) -> bool:
        """a 방에서 b 방으로 한 번에 이동 가능한가?"""
        return b in self._adjacency.get(a, [])

    def has_path(self, start: str, goal: str) -> bool:
        """start에서 goal까지 도달 가능한가? (BFS)"""
        if start not in self._adjacency or goal not in self._adjacency:
            return False
        if start == goal:
            return True

        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in self._adjacency[current]:
                if neighbor == goal:
                    return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def all_rooms(self) -> list[str]:
        """등록된 모든 방 ID."""
        return list(self._adjacency.keys())

    # ------------------------------------------------------------------
    # 데이터에서 구성
    # ------------------------------------------------------------------
    @classmethod
    def from_rooms_data(cls, rooms_data: dict) -> "RoomGraph":
        """data/rooms.json 형식에서 그래프 생성.

        rooms_data 예:
            {
                "main_lab": {"id": ..., "connected_rooms": ["hallway"]},
                "hallway":  {"id": ..., "connected_rooms": ["main_lab", "lab_b"]}
            }
        """
        graph = cls()
        for room_id, room_info in rooms_data.items():
            graph.add_room(room_id)
            for neighbor in room_info.get("connected_rooms", []):
                graph.add_edge(room_id, neighbor)
        return graph

    def to_dict(self) -> dict:
        """JSON 직렬화용."""
        return {k: list(v) for k, v in self._adjacency.items()}

    def __repr__(self) -> str:
        return f"RoomGraph({self._adjacency})"


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 가상의 방 구조 (현재 게임은 main_lab 1개지만 확장성 테스트)
    print("===== 시나리오: 4개의 방 연결 =====")
    g = RoomGraph()
    g.add_edge("main_lab", "hallway")
    g.add_edge("hallway", "lab_b")
    g.add_edge("hallway", "storage")
    print("전체 방:", g.all_rooms())
    print("hallway 이웃:", g.get_neighbors("hallway"))
    print("main_lab과 hallway 연결?:", g.is_connected("main_lab", "hallway"))
    print("main_lab과 lab_b 직접 연결?:", g.is_connected("main_lab", "lab_b"))
    print("main_lab → lab_b 도달 가능? (BFS):", g.has_path("main_lab", "lab_b"))
    print("main_lab → secret_room 도달 가능?:", g.has_path("main_lab", "secret_room"))

    print("\n===== 시나리오: JSON 데이터에서 생성 =====")
    from utils.data_loader import load_json
    rooms_data = load_json("rooms.json")
    g2 = RoomGraph.from_rooms_data(rooms_data)
    print("로딩된 방:", g2.all_rooms())
    print("to_dict():", g2.to_dict())
