"""
폐연구실 탈출 게임 - 백엔드 진입점.
Flask 서버를 실행하는 메인 파일.
"""
from dotenv import load_dotenv
load_dotenv()  # .env의 ANTHROPIC_API_KEY 등을 환경변수로 로딩 (import보다 먼저)

from flask import Flask, jsonify
from flask_cors import CORS

from api.game import game_bp
from api.view import view_bp
from api.investigate import investigate_bp
from api.inventory import inventory_bp
from api.puzzle import puzzle_bp
from api.move import move_bp
from api.mode import mode_bp
from api.maze import maze_bp
from api.hint import hint_bp
from api.ui import ui_bp
from api.events import events_bp


# Flask 앱 생성
app = Flask(__name__)
# 한글 응답을 유니코드 이스케이프 없이 그대로 내보내도록 설정
app.json.ensure_ascii = False
# 프론트엔드(다른 포트)에서도 호출할 수 있도록 CORS 허용
CORS(app)


# ----------------------------------------------------------------------
# 블루프린트 등록
# ----------------------------------------------------------------------
app.register_blueprint(game_bp)
app.register_blueprint(view_bp)
app.register_blueprint(investigate_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(puzzle_bp)
app.register_blueprint(move_bp)
app.register_blueprint(mode_bp)
app.register_blueprint(maze_bp)
app.register_blueprint(hint_bp)
app.register_blueprint(ui_bp)
app.register_blueprint(events_bp)


# ----------------------------------------------------------------------
# 헬스체크
# ----------------------------------------------------------------------
@app.route("/")
def health():
    """헬스체크 - 서버가 살아있는지 확인하는 엔드포인트."""
    return jsonify({
        "success": True,
        "message": "폐연구실 탈출 게임 백엔드 정상 작동 중",
    })


if __name__ == "__main__":
    # debug=True : 코드 수정 시 서버 자동 재시작
    # host="0.0.0.0" : 같은 네트워크 다른 기기에서도 접근 가능
    # 참고: Mac은 5000번 포트를 AirPlay가 사용하므로 5050으로 설정
    app.run(host="0.0.0.0", port=5050, debug=True)
