#!/usr/bin/env python3
"""
Claude Code Remote Daemon - v2
Control remoto de Claude Code con sesión persistente
"""
import pexpect
import requests
import time
import sys
import os
import signal
from datetime import datetime

# ══════════════════════════════════════════════
# Configuración
# ══════════════════════════════════════════════

SERVER_URL = os.getenv("CLAUDE_MONITOR_URL", "https://eloquent-quietude-production.up.railway.app")
POLL_INTERVAL = 2  # segundos
LOG_FILE = "/tmp/cc-daemon-v2.log"

# ══════════════════════════════════════════════
# Logging
# ══════════════════════════════════════════════

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

# ══════════════════════════════════════════════
# Claude Code Session Manager
# ══════════════════════════════════════════════

class ClaudeSession:
    def __init__(self, working_dir=None):
        self.env = None
        self.running = False
        self.working_dir = working_dir or os.getcwd()

    def start(self):
        """Prepara el entorno para ejecutar Claude Code"""
        log(f"Preparando entorno de Claude Code en: {self.working_dir}")

        self.env = os.environ.copy()
        self.env.update({
            'ANTHROPIC_MODEL_PROVIDER': 'bedrock',
            'ANTHROPIC_MODEL': 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0',
            'AWS_PROFILE': 'AWSAdministratorAccess-754689903878',
            'AWS_REGION': 'eu-central-1',
            'NODE_TLS_REJECT_UNAUTHORIZED': '0',
            'TERM': 'xterm-256color'
        })

        self.running = True
        log("✅ Entorno de Claude listo", "SUCCESS")
        return True

    def send_message(self, message):
        """Ejecuta Claude con el mensaje y captura respuesta"""
        if not self.running:
            log("⚠️  Sesión no está activa", "WARNING")
            return None

        try:
            log(f"📤 Ejecutando comando: {message[:80]}...")

            # Usar bash con pipe (método confiable)
            bash_cmd = f'cd {self.working_dir} && cat <<EOF | claude --print\n{message}\nEOF'

            process = pexpect.spawn(
                'bash',
                ['-c', bash_cmd],
                env=self.env,
                encoding='utf-8',
                timeout=120  # 2 minutos timeout
            )

            # Capturar toda la salida
            output = []
            while True:
                try:
                    line = process.readline()
                    if not line:
                        break
                    output.append(line)
                except pexpect.EOF:
                    break
                except pexpect.TIMEOUT:
                    log("⚠️  Timeout esperando respuesta", "WARNING")
                    break

            # Esperar que termine
            process.close()

            response = "".join(output).strip()
            log(f"📥 Respuesta recibida ({len(response)} chars)", "SUCCESS")
            return response

        except Exception as e:
            log(f"❌ Error ejecutando comando: {e}", "ERROR")
            import traceback
            log(traceback.format_exc(), "ERROR")
            return None

    def stop(self):
        """Limpia recursos"""
        self.running = False
        log("✅ Sesión detenida", "SUCCESS")

# ══════════════════════════════════════════════
# Daemon Principal
# ══════════════════════════════════════════════

class ClaudeDaemon:
    def __init__(self, working_dir=None):
        self.working_dir = working_dir or os.getcwd()
        self.claude = ClaudeSession(working_dir=self.working_dir)
        self.running = False

    def send_to_server(self, message, msg_type="system"):
        """Envía mensaje al servidor web"""
        try:
            response = requests.post(
                f"{SERVER_URL}/api/message",
                json={
                    "type": msg_type,
                    "content": message,
                    "is_approval": False
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            log(f"⚠️  Error enviando al servidor: {e}", "WARNING")
            return False

    def poll_commands(self):
        """Consulta servidor por comandos pendientes"""
        try:
            response = requests.get(
                f"{SERVER_URL}/api/poll_command",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                command_data = data.get("command")
                if command_data:
                    # Extraer el texto del comando (puede ser dict o string)
                    if isinstance(command_data, dict):
                        command_text = command_data.get("command", "")
                    else:
                        command_text = command_data

                    if command_text:
                        log(f"📨 Comando recibido: {command_text}")
                        return command_text
            return None
        except Exception as e:
            log(f"⚠️  Error consultando comandos: {e}", "WARNING")
            return None

    def run(self):
        """Loop principal del daemon"""
        log("=" * 60)
        log("🚀 Claude Code Remote Daemon v2 - INICIANDO")
        log("=" * 60)
        log(f"Servidor: {SERVER_URL}")
        log(f"Working dir: {self.working_dir}")
        log(f"Poll interval: {POLL_INTERVAL}s")
        log("")

        # Iniciar sesión de Claude
        if not self.claude.start():
            log("❌ No se pudo iniciar Claude Code. Abortando.", "ERROR")
            return

        self.send_to_server(f"🤖 Daemon v2 conectado - Directorio: {self.working_dir}", "system")
        self.running = True

        # Loop principal
        try:
            while self.running:
                # Consultar por comandos
                command = self.poll_commands()

                if command:
                    # Enviar notificación
                    self.send_to_server(f"🚀 Ejecutando comando: {command}", "system")

                    # Enviar a Claude y capturar respuesta
                    response = self.claude.send_message(command)

                    if response:
                        # Enviar respuesta al servidor con tipo "claude"
                        self.send_to_server(response, "claude")
                    else:
                        self.send_to_server("❌ Error: No se pudo obtener respuesta", "system")

                # Esperar antes de siguiente poll
                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            log("\n⚠️  Interrupción recibida (Ctrl+C)")
        finally:
            self.stop()

    def stop(self):
        """Detiene el daemon limpiamente"""
        log("\n🛑 Deteniendo daemon...")
        self.running = False
        self.claude.stop()
        self.send_to_server("👋 Daemon stopped", "system")
        log("✅ Daemon detenido correctamente")

# ══════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════

def signal_handler(signum, frame):
    """Handler para señales de sistema"""
    log(f"\n⚠️  Señal {signum} recibida", "WARNING")
    daemon.stop()
    sys.exit(0)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Claude Code Remote Daemon v2')
    parser.add_argument('--dir', type=str, help='Working directory for Claude session')
    args = parser.parse_args()

    working_dir = args.dir if args.dir else os.getcwd()

    # Registrar signal handlers
    daemon = ClaudeDaemon(working_dir=working_dir)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Limpiar log anterior
    with open(LOG_FILE, "w") as f:
        f.write("")

    # Iniciar daemon
    daemon.run()
