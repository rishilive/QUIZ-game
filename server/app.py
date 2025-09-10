from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- Room & Player Management ----------------
rooms = {}  # {room_code: {"players": {name: score}, "theme": theme}}

def generate_room_code(length=5):
    """Generate a unique room code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if code not in rooms:
            return code

# ---------------- Socket.IO Events ----------------
@socketio.on("create_room")
def handle_create_room(data):
    name = data.get("name")
    room_code = generate_room_code()
    rooms[room_code] = {"players": {name: 0}, "theme": "General"}
    join_room(room_code)
    emit("join_success", {"room_code": room_code, "theme": "General"}, to=request.sid)
    emit("server_msg", {"text": f"{name} created and joined room {room_code}"}, room=room_code)
    emit("leaderboard", {"items": [{"name": name, "score": 0}]}, room=room_code)
    emit("room_created", {"room_code": room_code}, to=request.sid)
    print(f"[INFO] Room {room_code} created by {name}")

@socketio.on("join_room")
def handle_join_room(data):
    room_code = data.get("room_code")
    name = data.get("name")
    if room_code in rooms:
        rooms[room_code]["players"][name] = 0
        join_room(room_code)
        emit("join_success", {"room_code": room_code, "theme": rooms[room_code]["theme"]}, to=request.sid)
        emit("server_msg", {"text": f"{name} joined room {room_code}"}, room=room_code)
        leaderboard_items = [{"name": n, "score": s} for n, s in rooms[room_code]["players"].items()]
        emit("leaderboard", {"items": leaderboard_items}, room=room_code)
        print(f"[INFO] {name} joined room {room_code}")
    else:
        emit("join_failed", {"text": "Room not found"}, to=request.sid)
        print(f"[WARN] Failed join attempt by {name} to non-existent room {room_code}")

@socketio.on("set_theme")
def handle_set_theme(data):
    room_code = data.get("room_code")
    theme = data.get("theme", "General")
    if room_code in rooms:
        rooms[room_code]["theme"] = theme
        emit("server_msg", {"text": f"Theme set to {theme}"}, room=room_code)
        print(f"[INFO] Theme for room {room_code} set to {theme}")

@socketio.on("update_score")
def handle_update_score(data):
    room_code = data.get("room_code")
    name = data.get("name")
    score = data.get("score", 0)
    if room_code in rooms and name in rooms[room_code]["players"]:
        rooms[room_code]["players"][name] = score
        leaderboard_items = [{"name": n, "score": s} for n, s in rooms[room_code]["players"].items()]
        emit("leaderboard", {"items": leaderboard_items}, room=room_code)
        print(f"[INFO] Score updated: {name} -> {score} in room {room_code}")

@socketio.on("disconnect")
def handle_disconnect():
    print("❌ A client disconnected")

# ---------------- Run Server ----------------
if __name__ == "__main__":
    print("Starting QuizMaster server on :5000")
    socketio.run(app, host="0.0.0.0", port=5000)
