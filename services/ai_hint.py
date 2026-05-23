"""
AI 힌트 서비스 (Google Gemini API - 무료 티어).

사용자가 자유롭게 질문하면("지금 뭐 해야 해?") 현재 게임 상황을 읽고
다음 단계를 자연스럽게 안내한다.

[왜 Gemini?]
- 무료 티어(카드 등록 불필요)로 학생 프로젝트/발표에 충분
- aistudio.google.com/apikey 에서 키 발급

[설계]
- 정적 게임 세계 데이터(방/아이템/퍼즐/오브젝트)는 system_instruction으로 전달
- 현재 GameState + PuzzleGraph 분석 결과 + 사용자 질문은 contents(user)로 전달
- PuzzleGraph(룰베이스)가 계산한 "지금 풀 수 있는 퍼즐 / 부족 단서"를
  컨텍스트로 함께 줘서 환각을 막고 정확한 다음 단계를 안내 (그래프 + LLM 하이브리드)

[API 키]
환경변수 GEMINI_API_KEY 필요 (.env 파일). 없으면 RuntimeError.
"""
import os
import json

from google import genai
from google.genai import types

from utils.data_loader import get_data
from services.puzzle_graph import get_puzzle_graph


# 게임 힌트용 모델. gemini-2.5-flash = 무료 티어 + 빠름.
# (2.5-flash는 기본 thinking이 켜져 출력 토큰을 잡아먹으므로 아래에서 thinking을 끈다)
MODEL = "gemini-2.5-flash"
MAX_TOKENS = 400

_client = None


def get_client() -> genai.Client:
    """Gemini 클라이언트 (지연 생성). API 키 없으면 RuntimeError."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    global _client
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


def _build_system_prompt() -> str:
    """정적 게임 세계 데이터로 시스템 프롬프트 구성."""
    data = get_data()
    return f"""당신은 '폐연구실 탈출' 방탈출 게임의 친절한 힌트 도우미입니다.
플레이어가 막혔을 때 다음에 무엇을 하면 좋을지 안내합니다.

[게임 개요]
- 1인칭으로 연구실을 좌/중/우 시점으로 탐색하며 단서와 아이템을 모아 퍼즐을 풀고,
  탈출문을 열어 미로로 진입한 뒤 미로를 빠져나오면 클리어.

[방/시점 데이터]
{json.dumps(data["rooms"], ensure_ascii=False)}

[아이템 데이터]
{json.dumps(data["items"], ensure_ascii=False)}

[오브젝트 데이터]
{json.dumps(data["objects"], ensure_ascii=False)}

[퍼즐 데이터]
{json.dumps(data["puzzles"], ensure_ascii=False)}

[답변 규칙]
1. 정답(비밀번호, 단어 등)을 절대 직접 말하지 말 것. 방향과 다음 행동만 안내.
2. 한 번에 '다음 한 단계'만 알려줄 것. 전체 공략을 늘어놓지 말 것.
3. 2~3문장으로 짧고 친근하게.
4. 아래 [현재 상황]과 [시스템 분석]을 근거로 답할 것. 데이터에 없는 내용은 지어내지 말 것.
5. 이미 한 일은 다시 시키지 말 것 (해결한 퍼즐/보유 아이템/발견 단서 참고).
"""


def _build_user_content(question: str, state) -> str:
    """현재 상태 + PuzzleGraph 분석 + 질문으로 user 메시지 구성."""
    graph = get_puzzle_graph()
    solvable = graph.next_solvable_puzzles(state)

    # 가장 가까운 미해결 퍼즐의 부족 단서/조달 방법
    puzzles = get_data()["puzzles"]
    closest = None
    for pid in puzzles:
        if pid in state.solved_puzzles:
            continue
        info = graph.missing_for(pid, state)
        if closest is None or len(info["missing_clues"]) < len(closest["missing_clues"]):
            closest = info

    analysis = {
        "지금_풀_수_있는_퍼즐": solvable,
        "가장_가까운_미해결_퍼즐": closest,
    }

    return f"""[현재 상황]
- 모드: {state.mode}
- 현재 위치: {state.current_room} / 시점: {state.current_view}
- 보유 아이템: {state.inventory.to_list()}
- 발견한 단서: {state.found_clues.to_list_newest_first()}
- 해결한 퍼즐: {list(state.solved_puzzles)}
- 조사한 오브젝트: {list(state.investigated_objects)}

[시스템 분석 (룰베이스 계산 결과 — 참고용)]
{json.dumps(analysis, ensure_ascii=False)}

[플레이어 질문]
{question}
"""


def ask_hint(question: str, state) -> str:
    """질문 + 현재 상태 → Gemini 힌트 텍스트 반환."""
    client = get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=_build_user_content(question, state),
        config=types.GenerateContentConfig(
            system_instruction=_build_system_prompt(),
            max_output_tokens=MAX_TOKENS,
            # thinking을 꺼서 출력 토큰이 thinking에 소모되지 않게 함 (응답 빔 방지)
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    return (response.text or "").strip()
