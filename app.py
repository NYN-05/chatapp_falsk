from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, send_from_directory, url_for
import json
import os
from flask_socketio import SocketIO, emit
import socket
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'dev_secret_key_1234567890'
socketio = SocketIO(app, async_mode="gevent")

MESSAGE_FILE = 'messages.json'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'mov', 'avi'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        file_url = url_for('uploaded_file', filename=filename)
        return {'url': file_url}, 200
    return {'error': 'Invalid file type'}, 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@socketio.on('send_message')
def handle_send_message(data):
    username = data.get('username', 'Anonymous')
    message = data.get('message', '')
    file_url = data.get('file_url', None)
    messages = load_messages()
    msg_obj = {'username': username, 'text': message}
    if file_url:
        msg_obj['file_url'] = file_url
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