import socketio

# Enable debug logging
sio = socketio.Client(logger=True, engineio_logger=True)

ROOM_CODE = input("Enter room code to join: ")

@sio.event
def connect():
    print("✅ Connected to server")
    sio.emit("join_room", {"room_code": ROOM_CODE, "name": "Player2"})

@sio.on("join_success")
def join_success(data):
    print("🙌 Successfully joined room:", data)

@sio.on("join_failed")
def join_failed(data):
    print("❌ Failed to join room:", data)

@sio.on("server_msg")
def server_msg(data):
    print("📢", data["text"])

@sio.on("leaderboard")
def leaderboard(data):
    print("🏆 Leaderboard:", data["items"])

@sio.event
def disconnect():
    print("❌ Disconnected from server")


if __name__ == "__main__":
    print("🔌 Connecting to http://localhost:5000 ...")
    sio.connect("http://localhost:5000")
    sio.wait()
