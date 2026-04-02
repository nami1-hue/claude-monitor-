#!/usr/bin/env python3
"""
Claude Code Monitor - Railway Deployment
Web interface accessible from anywhere
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Authentication
MONITOR_PASSWORD = os.environ.get('MONITOR_PASSWORD', 'changeme123')

# Global state
message_history = []
pending_approval = None
pending_commands = []  # Queue of commands from web to daemon
MAX_HISTORY = 200


def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def requires_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Serve the main monitoring page or login"""
    if not session.get('authenticated'):
        return render_template('login.html')
    return render_template('monitor.html')


@app.route('/api/login', methods=['POST'])
def login():
    """Handle login"""
    try:
        data = request.json
        password = data.get('password', '')

        if password == MONITOR_PASSWORD:
            session['authenticated'] = True
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid password'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle logout"""
    session.clear()
    return jsonify({'status': 'ok'})


@app.route('/api/messages')
@requires_auth
def get_messages():
    """Get message history"""
    return jsonify(message_history)


@app.route('/api/message', methods=['POST'])
def receive_message():
    """Receive message from ccmon"""
    try:
        data = request.json
        msg_type = data.get('type', 'claude')
        content = data.get('content', '')
        is_approval = data.get('is_approval', False)

        # Create message
        timestamp = datetime.now().strftime('%H:%M:%S')
        msg = {
            'type': msg_type,
            'content': content,
            'timestamp': timestamp,
            'is_approval': is_approval
        }

        # Add to history
        message_history.append(msg)

        # Keep only last MAX_HISTORY messages
        if len(message_history) > MAX_HISTORY:
            message_history[:] = message_history[-MAX_HISTORY:]

        # Set pending approval if needed
        global pending_approval
        if is_approval:
            pending_approval = msg.copy()
            pending_approval['resolved'] = False

        # Broadcast to all connected clients
        socketio.emit('new_message', msg)

        return jsonify({'status': 'ok'})

    except Exception as e:
        print(f"Error receiving message: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/approve', methods=['POST'])
@requires_auth
def approve_action():
    """Handle approval/rejection from web interface"""
    global pending_approval

    try:
        data = request.json
        response = data.get('response', 'n')

        # Store response for ccmon to poll
        approval_response = {
            'response': response,
            'timestamp': datetime.now().isoformat()
        }

        # In Railway, we'll use a simple in-memory store
        # ccmon will poll this endpoint
        app.config['APPROVAL_RESPONSE'] = approval_response

        # Clear pending approval
        if pending_approval:
            pending_approval['resolved'] = True
            pending_approval['response'] = 'approved' if response == 'y' else 'rejected'

        # Notify all clients
        socketio.emit('approval_resolved', {
            'response': response,
            'status': 'approved' if response == 'y' else 'rejected'
        })

        return jsonify({'status': 'ok', 'response': response})

    except Exception as e:
        print(f"Error handling approval: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/poll_approval', methods=['GET'])
def poll_approval():
    """Endpoint for ccmon to poll for approval response"""
    approval = app.config.get('APPROVAL_RESPONSE')
    if approval:
        # Clear after reading
        app.config['APPROVAL_RESPONSE'] = None
        return jsonify({'status': 'ok', 'approval': approval})
    else:
        return jsonify({'status': 'waiting'})


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'messages': len(message_history),
        'pending_approval': pending_approval is not None
    })


@app.route('/api/send_command', methods=['POST'])
@requires_auth
def send_command():
    """Receive command from web interface to execute on daemon"""
    try:
        data = request.json
        command = data.get('command', '').strip()

        if not command:
            return jsonify({'status': 'error', 'message': 'Empty command'}), 400

        # Add to pending commands queue
        cmd_id = len(pending_commands) + 1
        cmd_obj = {
            'id': cmd_id,
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        pending_commands.append(cmd_obj)

        # Notify daemon via socketio
        socketio.emit('new_command', cmd_obj)

        return jsonify({'status': 'ok', 'command_id': cmd_id})

    except Exception as e:
        print(f"Error sending command: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/poll_command', methods=['GET'])
def poll_command():
    """Daemon polls for pending commands"""
    if pending_commands:
        # Get first pending command
        cmd = pending_commands.pop(0)
        cmd['status'] = 'executing'
        return jsonify({'status': 'ok', 'command': cmd})
    else:
        return jsonify({'status': 'no_commands'})


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'ready'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    print(f"Client disconnected: {request.sid}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Claude Monitor on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
