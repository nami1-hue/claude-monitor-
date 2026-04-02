#!/usr/bin/env python3
"""
Claude Code Daemon - Executes commands from web interface
Runs in background on your local machine
"""

import sys
import os
import subprocess
import threading
import requests
import time
import re
import json
from datetime import datetime

# Server configuration
SERVER_URL = os.environ.get('CLAUDE_MONITOR_URL', 'http://localhost:5000')
POLL_INTERVAL = 2  # seconds

# State
current_process = None
waiting_for_approval = False


def send_message(msg_type, content, is_approval=False):
    """Send message to server"""
    try:
        data = {
            'type': msg_type,
            'content': content,
            'is_approval': is_approval
        }
        requests.post(f"{SERVER_URL}/api/message", json=data, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")


def poll_approval_response():
    """Poll server for approval response from web"""
    try:
        response = requests.get(f"{SERVER_URL}/api/poll_approval", timeout=5)
        data = response.json()
        if data.get('status') == 'ok' and data.get('approval'):
            return data['approval']['response']
    except Exception as e:
        print(f"Error polling approval: {e}")
    return None


def execute_command(command):
    """Execute Claude Code command and stream output"""
    global current_process, waiting_for_approval

    # Replace 'cc' with 'claude' if command starts with 'cc '
    if command.startswith('cc '):
        command = 'claude ' + command[3:]
    elif command == 'cc':
        command = 'claude'

    # Fix quotes: if command has ask/chat followed by unquoted text, quote it
    import shlex
    try:
        parts = shlex.split(command)
        if len(parts) >= 2 and parts[0] == 'claude':
            # Add --print flag for non-interactive mode
            if parts[1] in ['ask', 'chat']:
                # Rebuild: claude --print ask "rest of text"
                if len(parts) > 2:
                    rest = ' '.join(parts[2:])
                    command = f'claude --print {parts[1]} "{rest}"'
                else:
                    command = f'claude --print {parts[1]}'
    except ValueError:
        # If shlex fails, leave command as-is
        pass

    print(f"📋 Executing: {command}")
    send_message('system', f'🚀 Executing command: {command}')

    try:
        # Execute command
        current_process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Stream output
        output_buffer = []

        while True:
            line = current_process.stdout.readline()

            if not line:
                break

            line = line.rstrip()
            output_buffer.append(line)

            # Send to web interface
            send_message('claude', line)

            # Detect approval requests
            if 'approve' in line.lower() or 'proceed' in line.lower() or '(y/n)' in line.lower():
                print(f"⚠️  Approval needed: {line}")
                send_message('approval', line, is_approval=True)
                waiting_for_approval = True

                # Wait for approval from web
                print("⏳ Waiting for approval from web interface...")
                approval_timeout = 300  # 5 minutes
                start_time = time.time()

                while waiting_for_approval:
                    if time.time() - start_time > approval_timeout:
                        print("❌ Approval timeout")
                        send_message('system', '❌ Approval timeout (5 minutes)')
                        current_process.kill()
                        return

                    # Check for approval response
                    approval = poll_approval_response()
                    if approval:
                        print(f"✅ Approval received: {approval}")
                        send_message('system', f'✅ Approval: {approval}')

                        # Send response to Claude Code
                        current_process.stdin.write(f"{approval}\n")
                        current_process.stdin.flush()
                        waiting_for_approval = False
                        break

                    time.sleep(0.5)

        # Wait for process to complete
        return_code = current_process.wait()

        if return_code == 0:
            send_message('system', f'✅ Command completed successfully')
        else:
            send_message('system', f'⚠️  Command exited with code {return_code}')

    except Exception as e:
        error_msg = f"❌ Error executing command: {e}"
        print(error_msg)
        send_message('system', error_msg)

    finally:
        current_process = None
        waiting_for_approval = False


def poll_commands():
    """Poll server for new commands"""
    print(f"🔄 Polling for commands from {SERVER_URL}")

    while True:
        try:
            response = requests.get(f"{SERVER_URL}/api/poll_command", timeout=5)
            data = response.json()

            if data.get('status') == 'ok' and data.get('command'):
                cmd = data['command']
                command_str = cmd.get('command')
                print(f"\n📨 New command received: {command_str}")

                # Execute command
                execute_command(command_str)

        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to {SERVER_URL}")
            print("   Make sure the server is running")
            time.sleep(10)
        except Exception as e:
            print(f"Error polling: {e}")

        time.sleep(POLL_INTERVAL)


def main():
    """Main daemon loop"""
    print("=" * 60)
    print("🤖 Claude Code Daemon")
    print("=" * 60)
    print(f"Server: {SERVER_URL}")
    print(f"Polling every {POLL_INTERVAL} seconds")
    print()
    print("📱 Open web interface to send commands:")
    print(f"   {SERVER_URL}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Send startup message
    send_message('system', '🤖 Daemon started - Ready to receive commands')

    try:
        poll_commands()
    except KeyboardInterrupt:
        print("\n\n👋 Daemon stopped")
        send_message('system', '👋 Daemon stopped')


if __name__ == '__main__':
    main()
