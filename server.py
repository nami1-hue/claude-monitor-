#!/usr/bin/env python3
"""
Claude Code Monitor - Railway Deployment
Web interface accessible from anywhere
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'claude-monitor-secret-key-change-this')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
message_history = []
pending_approval = None
MAX_HISTORY = 200


@app.route('/')
def index():
    """Serve the main monitoring page"""
    return render_template('monitor.html')


@app.route('/api/messages')
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
