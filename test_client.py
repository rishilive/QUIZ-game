import socketio

# Enable debug logging
sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("✅ Connected to server")
    sio.emit("create_room", {"name": "Tester"})

@sio.on("room_created")
def room_created(data):
    print("🎮 Room created with code:", data["room_code"])

@sio.on("join_success")
def join_success(data):
    print("🙌 Joined room:", data)

@sio.on("server_msg")
def server_msg(data):
    print("📢", data["text"])

@sio.event
def disconnect():
    print("❌ Disconnected from server")

print("🔌 Connecting to http://localhost:5000 ...")
sio.connect("http://localhost:5000")
sio.wait()
