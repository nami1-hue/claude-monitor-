#!/usr/bin/env python3
"""
Claude Code Monitor Client - Connects to Railway server
"""

import sys
import subprocess
import threading
import re
import time
import os
import signal
import requests

# Server URL - Will be set after Railway deployment
SERVER_URL = os.environ.get('CLAUDE_MONITOR_URL', 'http://localhost:5000')

# Global state
subprocess_proc = None
output_buffer = []
last_send_time = time.time()


def send_to_server(message: str, is_approval: bool = False):
    """Send message to Railway server"""
    try:
        response = requests.post(
            f"{SERVER_URL}/api/message",
            json={
                'type': 'claude',
                'content': message,
                'is_approval': is_approval
            },
            timeout=5
        )
        if response.status_code != 200:
            print(f"Warning: Server returned {response.status_code}", file=sys.stderr)
    except requests.exceptions.Timeout:
        print(f"Warning: Timeout sending to server", file=sys.stderr)
    except requests.exceptions.ConnectionError:
        print(f"Warning: Could not connect to server", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Error sending to server: {e}", file=sys.stderr)


def is_approval_prompt(text: str) -> bool:
    """Check if text contains an approval prompt"""
    patterns = [
        r"Do you want to (?:proceed|continue)",
        r"Would you like (?:me )?to",
        r"Should I",
        r"Continue\?",
        r"Proceed\?",
        r"\(y/n\)",
        r"\[y/n\]",
        r"yes/no",
        r"approve",
    ]
    text_lower = text.lower()
    return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns)


def wait_for_approval_response(timeout=300):
    """Poll server for approval response"""
    print("⏳ Waiting for approval from web interface...", flush=True)

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{SERVER_URL}/api/poll_approval",
                timeout=2
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'approval' in data:
                    approval = data['approval']
                    resp = approval.get('response', 'n')
                    print(f"✅ Response received: {resp}", flush=True)
                    return resp + '\n'
        except Exception as e:
            print(f"Error polling approval: {e}", file=sys.stderr)

        time.sleep(1)

    print("⏰ Timeout waiting for approval", flush=True)
    return None


def output_reader(pipe, pipe_name):
    """Read output from subprocess and handle it"""
    global output_buffer, last_send_time

    buffer = ""

    try:
        for line in iter(pipe.readline, ''):
            if not line:
                break

            # Always print to console immediately
            print(line, end='', flush=True)

            buffer += line
            output_buffer.append(line)

            # Send to server periodically or on important events
            current_time = time.time()
            should_send = False

            # Send if buffer is large enough
            if len(buffer) > 800:
                should_send = True
            # Send if enough time has passed
            elif current_time - last_send_time > 3:
                should_send = True
            # Send if it looks like an approval prompt
            elif is_approval_prompt(buffer):
                should_send = True

            if should_send and buffer.strip():
                is_approval = is_approval_prompt(buffer)
                send_to_server(buffer, is_approval=is_approval)
                buffer = ""
                last_send_time = current_time

    except Exception as e:
        print(f"Error in output reader: {e}", file=sys.stderr)


def input_handler():
    """Handle input and check for approval prompts"""
    global subprocess_proc

    try:
        while subprocess_proc and subprocess_proc.poll() is None:
            try:
                # Check if we're waiting for approval
                recent_output = ''.join(output_buffer[-20:])
                if is_approval_prompt(recent_output):
                    # Wait for response from web interface
                    response = wait_for_approval_response(timeout=300)
                    if response:
                        subprocess_proc.stdin.write(response)
                        subprocess_proc.stdin.flush()
                        output_buffer.clear()
                        continue

                # Read user input from terminal
                user_input = input()
                if subprocess_proc and subprocess_proc.poll() is None:
                    subprocess_proc.stdin.write(user_input + '\n')
                    subprocess_proc.stdin.flush()

            except EOFError:
                break
            except Exception as e:
                print(f"Error in input handler: {e}", file=sys.stderr)
                break

    except Exception as e:
        print(f"Input handler error: {e}", file=sys.stderr)


def run_claude_code(args):
    """Run Claude Code with monitoring"""
    global subprocess_proc

    # Verify server is accessible
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"⚠️  Warning: Server health check failed (status {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("")
        print("=" * 60)
        print(" ❌ ERROR: Cannot connect to monitoring server!")
        print("=" * 60)
        print("")
        print(f"Server URL: {SERVER_URL}")
        print("")
        print("Make sure the Railway server is running and accessible.")
        print("Set the correct URL with:")
        print('  export CLAUDE_MONITOR_URL="https://your-app.up.railway.app"')
        print("")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Warning: Could not verify server: {e}")

    # Build command
    cmd = ['cc'] + args

    print(f"🚀 Starting Claude Code with monitoring...")
    print(f"🌐 Web interface: {SERVER_URL}")
    print(f"Command: {' '.join(cmd)}\n")

    # Send startup message
    send_to_server(f"🚀 Claude Code started\nCommand: {' '.join(cmd)}")

    # Run Claude Code
    try:
        subprocess_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Start output reader thread
        output_thread = threading.Thread(
            target=output_reader,
            args=(subprocess_proc.stdout, "stdout"),
            daemon=True
        )
        output_thread.start()

        # Start input handler thread
        input_thread = threading.Thread(target=input_handler, daemon=True)
        input_thread.start()

        # Wait for process to complete
        returncode = subprocess_proc.wait()

        # Send completion message
        status = "✅ completed successfully" if returncode == 0 else f"⚠️ exited with code {returncode}"
        send_to_server(f"Claude Code {status}")

        return returncode

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        if subprocess_proc:
            subprocess_proc.terminate()
            subprocess_proc.wait()
        send_to_server("⚠️ Claude Code interrupted by user")
        return 130

    except Exception as e:
        print(f"❌ Error running Claude Code: {e}")
        send_to_server(f"❌ Error: {e}")
        return 1


def signal_handler(signum, frame):
    """Handle termination signals"""
    print("\n🛑 Shutting down...")
    if subprocess_proc:
        subprocess_proc.terminate()
    sys.exit(0)


def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get arguments
    args = sys.argv[1:]

    # Run Claude Code with monitoring
    returncode = run_claude_code(args)
    sys.exit(returncode)


if __name__ == '__main__':
    main()
