from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request
import json
import os
from flask_socketio import SocketIO, emit
import socket

app = Flask(__name__)
app.secret_key = 'dev_secret_key_1234567890'
socketio = SocketIO(app, async_mode="gevent")

MESSAGE_FILE = 'messages.json'

def load_messages():
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_messages(messages):
    with open(MESSAGE_FILE, 'w') as f:
        json.dump(messages, f)

@app.route('/')
def index():
    return render_template('chat.html', messages=load_messages())

@socketio.on('send_message')
def handle_send_message(data):
    username = data.get('username', 'Anonymous')
    message = data.get('message', '')
    messages = load_messages()
    msg_obj = {'username': username, 'text': message}
    messages.append(msg_obj)
    save_messages(messages)
    emit('receive_message', msg_obj, broadcast=True)

@socketio.on('request_messages')
def handle_request_messages():
    emit('load_messages', load_messages())

if __name__ == '__main__':
    # Print local IP for easy access
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Access the chat on this device: http://localhost:8001")
    print(f"Access the chat from other devices: http://{local_ip}:8001")
    socketio.run(app, port=8001, host='0.0.0.0', debug=True)