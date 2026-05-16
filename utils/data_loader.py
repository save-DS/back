"""
JSON 데이터 로딩 유틸.
data/ 폴더의 정적 JSON 파일을 읽어와 딕셔너리로 반환한다.
"""
import json
from pathlib import Path


# 현재 파일 위치 기준으로 data/ 폴더 경로 계산
# __file__ : 이 파일(data_loader.py)의 절대 경로
# .resolve().parent.parent : 두 단계 위(back/)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str) -> dict:
    """data/ 폴더에서 JSON 파일 하나를 읽어 딕셔너리로 반환."""
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_data() -> dict:
    """게임에 필요한 모든 정적 데이터를 한 번에 로딩.

    반환 예:
        {
            "rooms":   {...},
            "items":   {...},
            "objects": {...},
            "puzzles": {...}
        }
    """
    return {
        "rooms":   load_json("rooms.json"),
        "items":   load_json("items.json"),
        "objects": load_json("objects.json"),
        "puzzles": load_json("puzzles.json"),
    }


if __name__ == "__main__":
    # 간단한 로딩 테스트 — 직접 실행하면 데이터 잘 읽히는지 확인
    data = load_all_data()
    for key, value in data.items():
        print(f"[{key}] {len(value)}개 로딩 완료")
