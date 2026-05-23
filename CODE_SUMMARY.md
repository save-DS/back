# 폐연구실 탈출 게임 - 백엔드 코드 정리 (PPT용)

> 발표/PPT 작성을 위한 모듈별 핵심 정리.
> 각 모듈을 슬라이드 하나로 만들 수 있도록 구성.

---

## 1. 전체 개요

- **스택**: Python 3.13 + Flask 3.0 + flask-cors
- **구조**: Flask Blueprint 패턴으로 시스템별 모듈 분리
- **저장**: 정적 데이터는 JSON, 게임 상태는 메모리 싱글톤(GameState)
- **API**: 총 24개 엔드포인트 (게임 3 + 모드 1 + 1인칭 9 + 미로 3 + 힌트 5 + UI 2 + 이벤트 1)
- **자료구조 7종**: 리스트/딕셔너리/셋/스택/큐/그래프/BFS 모두 실제 코드에 적용
- **AI 힌트**: 1인칭 HINT 버튼은 Google Gemini API로 자유 질문 응답
  (그래프(PuzzleGraph) 분석 결과를 컨텍스트로 함께 넘기는 하이브리드)

---

## 2. 폴더 구조

```
back/
├── app.py                    # Flask 진입점, 블루프린트 등록
├── requirements.txt
├── data/                     # 정적 JSON 데이터
│   ├── rooms.json
│   ├── items.json
│   ├── objects.json
│   └── puzzles.json
├── services/                 # 게임 로직 + 자료구조 모듈
│   ├── game_state.py         # 단일 진실의 원천 (싱글톤)
│   ├── inventory.py          # 인벤토리 (리스트+셋)
│   ├── clue_stack.py         # Stack 클래스
│   ├── event_queue.py        # Queue 클래스
│   ├── room_graph.py         # 방 연결 그래프
│   ├── maze_bfs.py           # 미로 BFS 최단경로
│   ├── maze_generator.py     # 미로 랜덤 생성 (DFS)
│   ├── puzzle_graph.py       # 퍼즐 의존성 그래프
│   └── ai_hint.py            # AI 힌트 (Gemini API + PuzzleGraph 하이브리드)
├── api/                      # Flask Blueprint들
│   ├── __init__.py           # 응답 헬퍼 + 에러 코드
│   ├── game.py               # 게임 라이프사이클
│   ├── view.py               # 시점 전환
│   ├── investigate.py        # 오브젝트 조사
│   ├── inventory.py          # 인벤토리 조회/사용
│   ├── puzzle.py             # 퍼즐 정답/조합
│   ├── move.py               # 방 이동
│   ├── mode.py               # 모드 전환
│   ├── maze.py               # 미로 맵/이동/재생성
│   ├── hint.py               # 힌트 (미로 BFS / 룰베이스 / AI 자유질문)
│   ├── ui.py                 # 단서창/미니맵
│   └── events.py             # 이벤트 폴링
├── utils/
│   └── data_loader.py        # JSON 캐시 로더
└── .env.example              # GEMINI_API_KEY 템플릿 (.env는 gitignore)
```

---

## 3. 진행 단계 (Issue 단위)

| Phase | 이슈 | 핵심 결과물 |
|-------|------|------------|
| 1 | #1 Foundation | 폴더 구조 + JSON 데이터 4개 + GameState 싱글톤 |
| 2 | #2 자료구조 모듈 | Inventory/Stack/Queue/Graph/BFS 5개 클래스 |
| 3 | #3 1인칭 API | 게임 시작·시점·조사·인벤토리·퍼즐·이동 (12 엔드포인트) |
| 4 | #4 미로 + BFS | 랜덤 미로 생성 + 함정 + BFS 힌트 (5 엔드포인트) |
| 5 | #5 룰베이스 힌트 + UI | 퍼즐 그래프 + 6 엔드포인트 |
| 6 | #6 코드 노트 재설계 | 코드 노트를 컴퓨터에 사용 → bang 단서 해독 흐름 |
| 7 | #7 AI 힌트 (완료) | Google Gemini API 자유 질문 + PuzzleGraph 하이브리드 |

---

# 모듈별 PPT 슬라이드

## 📄 슬라이드 1 — GameState (단일 진실의 원천)

**파일**: `services/game_state.py`

**역할**: 게임의 모든 상태(인벤토리, 해결한 퍼즐, 현재 위치, 모드 등)를 보관하는 중앙 객체. 모든 시스템이 이 객체를 통해 상태를 읽고 쓴다.

**자료구조**: 딕셔너리(전체) + 리스트/셋/스택/큐 조합

**핵심 포인트**
- **싱글톤 패턴**: 어디서 import해도 같은 인스턴스 반환 → 상태 동기화 보장
- **단일 진실의 원천(SSoT)**: Redux/Zustand와 같은 컨셉
- **JSON 직렬화**: `to_dict()`에서 set/커스텀클래스를 list로 변환
- **보안 결정**: `maze_traps`는 to_dict()에서 제외 (함정 위치 노출 방지)

**핵심 코드**
```python
class GameState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def init_state(self):
        self.mode = "first_person"
        self.inventory = Inventory(max_size=8)
        self.solved_puzzles = set()
        self.found_clues = Stack()
        self.view_stack = Stack()
        self.event_queue = Queue()
        ...
```

---

## 📄 슬라이드 2 — Inventory (리스트 + 셋 조합)

**파일**: `services/inventory.py`

**역할**: 플레이어 인벤토리. 획득 순서 보존 + 중복 획득 방지를 동시에.

**자료구조**: **리스트(순서) + 셋(O(1) 검색)** ← 두 자료구조 동시 활용이 핵심

**핵심 포인트**
- 리스트만 쓰면 `has()` 검사가 O(n) → 느림
- 셋만 쓰면 순서가 사라짐 → 인벤토리 슬롯 표시 불가
- **두 자료구조를 같이 써서 양쪽 장점**

**핵심 코드**
```python
class Inventory:
    def __init__(self, max_size: int = 8):
        self._items: list[str] = []      # 획득 순서
        self._lookup: set[str] = set()    # 빠른 검색

    def add(self, item_id: str) -> bool:
        if item_id in self._lookup:        # O(1) 중복 검사
            return False
        if self.is_full():
            return False
        self._items.append(item_id)
        self._lookup.add(item_id)
        return True

    def has(self, item_id: str) -> bool:
        return item_id in self._lookup     # O(1)
```

---

## 📄 슬라이드 3 — Stack (스택, LIFO)

**파일**: `services/clue_stack.py`

**역할**: 단서 발견 기록(최신순 표시) + 화면 히스토리(뒤로가기) 모두에 사용.

**자료구조**: 스택 (LIFO)

**핵심 포인트**
- **하나의 범용 Stack 클래스를 두 용도로 재사용** (found_clues, view_stack)
- 파이썬 `list.append/pop`은 양 끝 연산이 O(1) → 스택에 적합
- 화면 뒤로가기 = `view_stack.pop()`으로 직전 화면 복원

**핵심 코드**
```python
class Stack:
    def __init__(self):
        self._items: list = []

    def push(self, item) -> None:
        self._items.append(item)

    def pop(self):
        if self.is_empty(): return None
        return self._items.pop()

    def to_list_newest_first(self) -> list:
        return list(reversed(self._items))
```

---

## 📄 슬라이드 4 — Queue (큐, FIFO)

**파일**: `services/event_queue.py`

**역할**: 이벤트/알림/대화 순서 처리. 정전, 경고 메시지, 시간 기반 이벤트 등.

**자료구조**: 큐 (FIFO) — `collections.deque` 기반

**핵심 포인트**
- 파이썬 `list`로 큐를 만들면 `pop(0)`이 O(n) → 느림
- **`collections.deque`는 양쪽 끝 연산 모두 O(1)**
- 이벤트 폴링 API(`/api/events/pending`)와 직접 연결

**핵심 코드**
```python
from collections import deque

class Queue:
    def __init__(self):
        self._items: deque = deque()

    def enqueue(self, item) -> None:
        self._items.append(item)

    def dequeue(self):
        if self.is_empty(): return None
        return self._items.popleft()    # O(1)
```

---

## 📄 슬라이드 5 — RoomGraph (그래프, 인접 리스트)

**파일**: `services/room_graph.py`

**역할**: 방과 방 사이 연결 관계. 미니맵 + 방 이동 가능성 판정에 사용.

**자료구조**: 그래프 (무방향, 인접 리스트 `dict[str, list[str]]`)

**핵심 포인트**
- **인접 리스트** 방식 → 노드 수가 많고 엣지가 적을 때 효율적
- `has_path(a, b)`: BFS로 두 방 사이 도달 가능성 검사
- `from_rooms_data()`: JSON 데이터에서 자동 그래프 구성

**핵심 코드**
```python
class RoomGraph:
    def __init__(self):
        self._adjacency: dict[str, list[str]] = {}

    def add_edge(self, a: str, b: str) -> None:
        self.add_room(a); self.add_room(b)
        if b not in self._adjacency[a]:
            self._adjacency[a].append(b)
        if a not in self._adjacency[b]:
            self._adjacency[b].append(a)

    def has_path(self, start, goal) -> bool:
        """BFS로 도달 가능성 검사"""
        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in self._adjacency[current]:
                if neighbor == goal: return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False
```

---

## 📄 슬라이드 6 — MazeBFS (BFS 최단 경로)

**파일**: `services/maze_bfs.py`

**역할**: 미로에서 시작점→출구 최단 경로를 찾아 힌트로 제공. 함정 회피 옵션 포함.

**자료구조**: 큐(BFS) + 셋(visited) + 딕셔너리(came_from으로 경로 복원)

**핵심 포인트**
- **BFS는 가중치 없는 그래프의 최단 경로를 보장**
- `avoid` 파라미터로 함정 좌표 회피 가능 → 안전한 경로만 추천
- `came_from` 딕셔너리로 역추적해 전체 경로 복원
- 4방향 이동 (상/하/좌/우)

**핵심 코드**
```python
def find_shortest_path(maze, start, goal, avoid=None):
    visited = {start}
    came_from = {}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        for dr, dc, _ in DIRECTIONS:
            next_pos = (current[0]+dr, current[1]+dc)
            if next_pos in visited or not _is_walkable(maze, *next_pos):
                continue
            if next_pos in avoid:                  # 함정 회피
                continue
            visited.add(next_pos)
            came_from[next_pos] = current
            if next_pos == goal:
                return _reconstruct_path(came_from, start, goal)
            queue.append(next_pos)
    return None
```

---

## 📄 슬라이드 7 — MazeGenerator (DFS 백트래킹 미로 생성)

**파일**: `services/maze_generator.py`

**역할**: 매 게임마다 다른 미로를 랜덤 생성 + 함정 5개 배치 + 출구 위치 자동 선정.

**자료구조**: **스택(DFS 백트래킹)** + 큐(출구 선정 BFS) + 셋(함정 좌표/visited)

**핵심 포인트**
- **DFS 백트래킹**: 이웃 중 안 방문한 곳으로 진행, 막히면 스택 pop으로 백트래킹
- **출구는 BFS로 시작점에서 가장 먼 칸을 선정** → 게임 난이도 보장
- **함정 배치 시 BFS로 도달 가능성 검증** → 풀 수 없는 미로 방지

**핵심 코드 (DFS 부분)**
```python
def generate_maze(width=15, height=9):
    grid = [[1] * width for _ in range(height)]   # 전부 벽
    start = (1, 1)
    grid[1][1] = 0
    stack = [start]                                # ★ 스택

    while stack:
        r, c = stack[-1]
        unvisited = [(r+dr, c+dc) for dr, dc in DIRECTIONS_DFS
                     if 1 <= r+dr < height-1 and 1 <= c+dc < width-1
                     and grid[r+dr][c+dc] == 1]
        if unvisited:
            nr, nc = random.choice(unvisited)
            grid[(r+nr)//2][(c+nc)//2] = 0         # 벽 뚫기
            grid[nr][nc] = 0
            stack.append((nr, nc))
        else:
            stack.pop()                            # 백트래킹
    return grid
```

---

## 📄 슬라이드 8 — PuzzleGraph (퍼즐 의존성 그래프)

**파일**: `services/puzzle_graph.py`

**역할**: 퍼즐/아이템/단서/오브젝트 사이 관계를 그래프로 표현 → 자동 힌트 생성.

**자료구조**: 그래프 + 역인덱스 딕셔너리(`_clue_sources`)

**핵심 포인트**
- 노드: 퍼즐, 아이템, 단서, 오브젝트
- 엣지: "이 단서가 있어야 퍼즐 풀린다" "이 아이템은 저기 사용한다"
- **역인덱스로 "단서 → 출처 목록" 자동 구성** → "어디 가서 어떻게 얻어"를 자동 안내
- 진행 분석에서 "지금 풀 수 있는 퍼즐 / 가장 가까운 미해결 퍼즐" 자동 추천

**핵심 코드**
```python
def missing_for(self, puzzle_id, state):
    """특정 퍼즐을 풀려면 부족한 단서/아이템 + 조달 방법"""
    puzzle = self.puzzles[puzzle_id]
    found = set(state.found_clues.to_list())
    required = set(puzzle.get("required_clues", []))
    missing_clues = sorted(required - found)        # ← 셋 차집합

    suggestions = []
    for cid in missing_clues:
        suggestions.append({
            "clue_id": cid,
            "where_to_find": self.sources_of(cid),  # 역인덱스 조회
        })
    return {
        "missing_clues": missing_clues,
        "suggestions": suggestions,
    }
```

---

## 📄 슬라이드 9 — API 공통 응답 형식

**파일**: `api/__init__.py`

**역할**: 모든 API가 동일한 응답 구조를 갖도록 헬퍼 제공.

**핵심 포인트**
- **성공/실패 응답 형식 표준화**
- **`state_changed` 필드**: 변경된 필드만 전송 → 네트워크 효율 + 프론트 리렌더 최소화
- **9종 에러 코드**: INVALID_REQUEST, NOT_FOUND, INVALID_STATE, ALREADY_DONE, MISSING_REQUIREMENT, WRONG_ANSWER, COLLISION, INVALID_ITEM, INVALID_TARGET

**응답 예**
```json
// 성공
{
  "success": true,
  "data": { ... },
  "state_changed": { "current_view": "left" },
  "pending_events": [ ... ]
}

// 실패
{
  "success": false,
  "error_code": "WRONG_ANSWER",
  "message": "정답이 아닙니다."
}
```

---

## 📄 슬라이드 10 — 시점 전환 API (스택 활용)

**파일**: `api/view.py`

**역할**: 1인칭 모드의 좌/중/우 시점 전환 + 상세 뷰 뒤로가기.

**핵심 포인트**
- 시점 전환은 **선형(linear)**: left ↔ center ↔ right
- 끝에서 더 회전 시 `INVALID_STATE` 에러
- **뒤로가기 = `view_stack.pop()`** → 스택 자료구조 정확히 활용

**엔드포인트 3개**
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | /api/view/turn | 좌/우 시점 전환 |
| GET | /api/view/current | 현재 시점 조회 |
| POST | /api/view/back | 직전 화면 복귀 (스택 pop) |

---

## 📄 슬라이드 11 — 조사 API (셋 + 스택 활용)

**파일**: `api/investigate.py`

**역할**: 오브젝트 클릭 시 내레이션 + 아이템/단서 자동 지급.

**핵심 포인트**
- **셋으로 중복 보상 방지**: `investigated_objects` 셋에 추가 → 두 번째 조사 시 보상 안 줌
- **상태 기반 내레이션**: 퍼즐 해결 여부에 따라 다른 텍스트
- **view_stack에 push** → 뒤로가기 동작 가능

**핵심 코드**
```python
@investigate_bp.route("/investigate", methods=["POST"])
def investigate():
    is_first_time = object_id not in game_state.investigated_objects
    if is_first_time:
        game_state.investigated_objects.add(object_id)       # 셋
        # 아이템/단서 자동 지급
        for item_id in obj.get("initial_items", []):
            if game_state.inventory.add(item_id):
                found_items.append(item_id)
    game_state.view_stack.push({...})                        # 스택
```

---

## 📄 슬라이드 12 — 인벤토리 사용 API (조합/사용 분기)

**파일**: `api/inventory.py`

**역할**: 아이템 + 아이템 조합 (배터리+손전등 → UV램프), 또는 아이템 → 오브젝트 사용 (UV램프 → 화이트보드).

**핵심 포인트**
- **하나의 엔드포인트(`/api/inventory/use`)가 두 가지 사용 케이스를 처리**
- target_id가 아이템인지 오브젝트인지 자동 분기
- 조합 시 두 재료 제거 + 결과 아이템 추가

**예시 요청**
```bash
# 조합
POST /api/inventory/use { "item_id": "battery", "target_id": "flashlight" }
# → battery, flashlight 제거 → uv_flashlight 획득

# 오브젝트 사용
POST /api/inventory/use { "item_id": "uv_flashlight", "target_id": "whiteboard" }
# → clue_3 단서 발견
```

---

## 📄 슬라이드 13 — 미로 API (충돌/함정/출구 처리)

**파일**: `api/maze.py`

**역할**: 미로 4방향 이동 + 벽 충돌 + 함정 적중 + 출구 도달 처리.

**핵심 포인트**
- 벽/경계 → `COLLISION` 에러
- 함정 적중 → `trap_hit: true`, 시작점 리셋 (단, 함정 위치는 백엔드만 알고 있음)
- 출구 도달 → `reached_exit: true`, `status: cleared`
- **함정 정보는 응답에 절대 노출 안 됨** (`to_dict()`에서도 제외)

**핵심 코드**
```python
# 함정 적중
if (nr, nc) in game_state.maze_traps:           # 셋 검사 O(1)
    game_state.maze_position = game_state.maze_start  # 리셋
    game_state.maze_trap_hits += 1
    return success(data={"trap_hit": True, "reset_to_start": True, ...})

# 출구 도달
if (nr, nc) == game_state.maze_exit:
    game_state.maze_reached_exit = True
    game_state.mark_cleared()
    return success(data={"reached_exit": True, ...})
```

---

## 📄 슬라이드 14 — 힌트 시스템 (미로 BFS / 룰베이스 / AI)

**파일**: `api/hint.py`, `services/ai_hint.py`

| 엔드포인트 | 자료구조/기술 | 동작 | 현재 사용처 |
|-----------|--------------|------|------------|
| GET /api/hint/maze | BFS | 미로 함정 회피 최단 경로 | 미로 HINT 버튼 (1회 제한) |
| GET /api/hint/puzzle | 그래프 (PuzzleGraph) | 특정 퍼즐의 부족 단서 분석 | 룰베이스(자료구조 시연/폴백) |
| GET /api/hint/progress | 그래프 + 셋 | 진행 요약 + 가장 가까운 미해결 퍼즐 | 〃 |
| GET /api/hint/item-use | 그래프 | 보유 아이템 활용 추천 | 〃 |
| **POST /api/hint/ask** | **Gemini API + 그래프** | **자유 질문 → 다음 단계 안내** | **1인칭 HINT 버튼** |

**미로 힌트(BFS) 예시 응답**
```json
{ "next_direction": "right", "remaining_steps": 14,
  "path": [[3,5],[3,6],...], "hint_text": "right으로 이동하세요. (출구까지 14칸)" }
```

> 미로 힌트는 BFS 경로를 프론트에서 2초간 표시(미로당 1회).
> 1인칭 힌트는 AI(`/ask`)가 담당하며, 룰베이스 4종은 그래프 자료구조 시연 +
> AI 키 없을 때의 폴백으로 남겨둠.

---

## 📄 슬라이드 15 — 자료구조 활용 매트릭스 (수업 평가 핵심)

| 자료구조 | 구현 클래스/모듈 | 게임 내 역할 | 핵심 연산 복잡도 |
|---------|-----------------|-------------|----------------|
| **리스트** | `Inventory._items` | 인벤토리 순서 보존 | append O(1), remove O(n) |
| **딕셔너리** | JSON 데이터, `GameState`, `state_changed` 응답 | 데이터 키 조회 | get/set O(1) |
| **셋** | `Inventory._lookup`, `solved_puzzles`, `investigated_objects`, `maze_traps` | 중복 방지 + O(1) 검사 | add/has O(1) |
| **스택** | `Stack` (clue_stack.py) — `found_clues`, `view_stack` | 단서 최신순, 화면 뒤로가기, 미로 생성 DFS | push/pop O(1) |
| **큐** | `Queue` (event_queue.py) — `event_queue` | 이벤트 순차 처리, BFS | enqueue/dequeue O(1) |
| **그래프** | `RoomGraph` (방), `PuzzleGraph` (퍼즐 의존성) | 방 이동 / 힌트 자동 추론 | get_neighbors O(1) |
| **BFS** | `maze_bfs.py`, `RoomGraph.has_path` | 미로 최단 경로 / 도달 가능성 | O(V+E) |

---

## 📄 슬라이드 16 — API 엔드포인트 전체 목록

### 게임 관리 (3)
- POST /api/game/init
- GET  /api/game/state
- POST /api/game/reset

### 모드 전환 (1)
- POST /api/mode/switch

### 1인칭 (8)
- POST /api/view/turn
- GET  /api/view/current
- POST /api/view/back
- POST /api/investigate
- GET  /api/inventory
- POST /api/inventory/use
- POST /api/puzzle/submit
- POST /api/puzzle/combine
- POST /api/move/room

### 미로 (3)
- GET  /api/maze/map
- POST /api/maze/move
- POST /api/maze/regenerate

### 힌트 (5)
- GET  /api/hint/maze
- GET  /api/hint/puzzle?puzzle_id=
- GET  /api/hint/progress
- GET  /api/hint/item-use
- POST /api/hint/ask  (AI 자유 질문, Gemini)

### UI 보조 (3)
- GET /api/ui/clues
- GET /api/ui/minimap
- GET /api/events/pending

**합계: 24개**

---

## 📄 슬라이드 17 — 게임 플레이 시나리오 (검증 완료)

curl로 풀 클리어까지 검증:

```
[1인칭 - 캐비닛 비번 3962 만들기]
1. POST /api/game/init                                       → 게임 시작
2. POST /api/investigate {object_id:"cabinet"}              → 건전지 획득
3. POST /api/investigate {object_id:"desk_drawer"}          → 손전등 획득
4. POST /api/inventory/use {battery+flashlight}             → UV램프 조합
5. POST /api/inventory/use {uv_flashlight+whiteboard}       → clue_3
6. POST /api/investigate {object_id:"shelf_book"}           → 현미경 스코프
7. POST /api/inventory/use {scope+microscope}               → clue_9
8. POST /api/investigate {object_id:"newspaper_pile"}       → clue_6
9. POST /api/investigate {object_id:"rug"}                  → clue_2
10. POST /api/puzzle/submit {cabinet_password, "3962"}      → 탈출키 획득

[1인칭 - bang 단어 해독]
11. POST /api/investigate {object_id:"code_note"}           → 코드 노트 획득
12. POST /api/puzzle/submit {computer_login, "0418"}        → 연구일지(research_doc)
13. POST /api/inventory/use {code_note+computer}            → word_bang 해독
14. POST /api/puzzle/submit {escape_door_keypad, "bang"}    → 탈출문 열림 → 미로 진입

[미로 - 암기 + 탈출]
15. POST /api/mode/switch {"maze"}                          → 미로 진입 (15×9, 함정 5)
    (프론트: 3초간 길 보여준 뒤 벽을 길 색으로 덮어 안 보이게 함)
16. GET  /api/hint/maze                                     → BFS 경로 + 다음 방향 (1회)
17. POST /api/maze/move {direction}                         → 한 칸씩 이동
18. (출구 도달)                                              → status: cleared
```

> 코드 노트는 컴퓨터 로그인(0418) 후에만 사용 가능 (use_requires_puzzle).
> escape_door_keypad의 정답 "bang"은 word_bang 단서로 해독해서 알아냄.

---

## 📄 슬라이드 18 — 설계 결정 포인트 (PPT 부록)

### 1. 왜 싱글톤 GameState?
- 모든 API가 동일한 상태에 접근해야 함
- DB 없이도 일관성 보장
- 테스트/리셋 용이

### 2. 왜 함정을 백엔드가 숨기는가?
- 프론트에 노출하면 console.log로 위치 알 수 있음
- 백엔드가 단순 boolean(`trap_hit`)만 전달 → 보안

### 3. 왜 미로를 매번 생성?
- 재플레이 가치 (매번 다른 미로)
- DFS 백트래킹 알고리즘이 미로 풀이 가능성을 자체 보장
- 함정 배치 후 BFS로 도달 가능성 재검증

### 4. 왜 RoomGraph + PuzzleGraph 두 그래프인가?
- RoomGraph: 공간 구조 (어디서 어디로 갈 수 있나)
- PuzzleGraph: 논리적 의존성 (어떤 단서가 어떤 퍼즐에 쓰이나)
- 둘 다 그래프지만 표현하는 관계가 완전히 다름

### 5. 왜 응답에 `state_changed`가 있는가?
- 전체 GameState 매번 보내면 느림
- 변경된 필드만 보내서 프론트가 부분 업데이트 가능 (React/Vue 친화적)

---

## 📄 슬라이드 19 — 개발 워크플로우

- **Git 전략**: `main ← develop ← feat/N-설명`
- **이슈 단위**: 각 Phase가 GitHub Issue 하나에 매핑
- **커밋 컨벤션**: `feat: 한글 설명` (Conventional + Korean)
- **PR**: 각 이슈마다 develop으로 PR → 머지 후 브랜치 삭제
- **검증**: 각 모듈 단독 실행 (`python -m services.모듈명`) + curl 통합 테스트

---

## 📄 슬라이드 20 — 다음 단계 (Issue #6 예정)

**AI 힌트 시스템 (Claude API)**
- `POST /api/hint/ask`: 사용자가 자유롭게 질문
- 백엔드가 현재 GameState + 게임 세계 데이터를 시스템 프롬프트로 구성
- Claude가 상황에 맞는 자연스러운 한국어 힌트 응답
- **알고리즘(BFS/PuzzleGraph) 결과를 컨텍스트로 함께 전달**
- → "BFS + LLM 하이브리드 힌트 시스템"으로 어필 가능
