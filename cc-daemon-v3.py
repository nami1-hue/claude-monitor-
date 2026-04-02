#!/usr/bin/env python3
"""
Claude Code Remote Daemon - v3
Sesión persistente de Claude Code con contexto mantenido
"""
import pexpect
import requests
import time
import sys
import os
import signal
import threading
from datetime import datetime

# ══════════════════════════════════════════════
# Configuración
# ══════════════════════════════════════════════

SERVER_URL = os.getenv("CLAUDE_MONITOR_URL", "https://eloquent-quietude-production.up.railway.app")
POLL_INTERVAL = 2  # segundos
LOG_FILE = "/tmp/cc-daemon-v3.log"

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
# Claude Code Persistent Session Manager
# ══════════════════════════════════════════════

class ClaudePersistentSession:
    def __init__(self, working_dir=None):
        self.process = None
        self.running = False
        self.working_dir = working_dir or os.getcwd()
        self.lock = threading.Lock()
        self.last_output = []

    def start(self):
        """Inicia sesión PERSISTENTE de Claude Code"""
        log(f"Iniciando sesión persistente de Claude Code en: {self.working_dir}")

        env = os.environ.copy()
        env.update({
            'ANTHROPIC_MODEL_PROVIDER': 'bedrock',
            'ANTHROPIC_MODEL': 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0',
            'AWS_PROFILE': 'AWSAdministratorAccess-754689903878',
            'AWS_REGION': 'eu-central-1',
            'NODE_TLS_REJECT_UNAUTHORIZED': '0',
            'TERM': 'xterm-256color'
        })

        try:
            # Iniciar Claude en modo INTERACTIVO (sin --print)
            self.process = pexpect.spawn(
                'bash',
                ['-c', f'cd {self.working_dir} && claude'],
                env=env,
                encoding='utf-8',
                timeout=300,
                maxread=50000,
                dimensions=(100, 200)
            )

            log("⏳ Esperando prompt inicial de Claude...")

            # Esperar el prompt de seguridad "Yes, I trust this folder"
            try:
                index = self.process.expect([
                    r'Yes.*trust.*folder',
                    r'ready',
                    pexpect.TIMEOUT
                ], timeout=10)

                if index == 0:
                    log("🔐 Detectado prompt de seguridad - Auto-aprobando...")
                    # Enviar tecla de flecha abajo y Enter para seleccionar "Yes"
                    self.process.send('\x1b[B')  # Arrow down (por si acaso)
                    time.sleep(0.3)
                    self.process.sendline('')  # Enter
                    time.sleep(2)

            except pexpect.TIMEOUT:
                log("⚠️  No se detectó prompt de seguridad (puede que ya esté aprobado)")

            self.running = True
            log("✅ Sesión de Claude Code iniciada y lista", "SUCCESS")
            return True

        except Exception as e:
            log(f"❌ Error iniciando Claude: {e}", "ERROR")
            import traceback
            log(traceback.format_exc(), "ERROR")
            return False

    def send_message(self, message):
        """Envía mensaje a la sesión PERSISTENTE de Claude"""
        if not self.running or not self.process:
            log("⚠️  Sesión no está activa", "WARNING")
            return None

        with self.lock:
            try:
                log(f"📤 Enviando a sesión persistente: {message[:80]}...")

                # Limpiar buffer antes de enviar
                try:
                    self.process.read_nonblocking(size=10000, timeout=0.1)
                except:
                    pass

                # Enviar mensaje
                self.process.sendline(message)

                # Esperar y capturar respuesta
                log("⏳ Capturando respuesta...")

                # Dar tiempo a que Claude empiece a procesar (importante!)
                time.sleep(2)

                response_lines = []
                start_time = time.time()
                timeout = 120  # 2 minutos

                # Estrategia mejorada: leer hasta silencio prolongado
                silence_threshold = 5  # 5 segundos de silencio (aumentado)
                last_read_time = time.time()
                total_read = 0

                while True:
                    try:
                        # Intentar leer con timeout más largo
                        chunk = self.process.read_nonblocking(size=2000, timeout=1.0)

                        if chunk:
                            response_lines.append(chunk)
                            last_read_time = time.time()
                            total_read += len(chunk)
                            log(f"   📥 Leídos {total_read} chars hasta ahora...")

                        # Si llevamos más de silence_threshold sin leer Y ya tenemos contenido, terminamos
                        if time.time() - last_read_time > silence_threshold and total_read > 0:
                            log(f"✅ Respuesta completa ({total_read} chars total)")
                            break

                        # Timeout general
                        if time.time() - start_time > timeout:
                            log("⚠️  Timeout general alcanzado")
                            break

                    except pexpect.TIMEOUT:
                        # Timeout del read_nonblocking
                        if total_read > 0 and time.time() - last_read_time > silence_threshold:
                            log(f"✅ Fin por timeout con contenido ({total_read} chars)")
                            break
                        # Si no hay contenido aún, seguir esperando
                        continue

                    except pexpect.EOF:
                        log("⚠️  EOF detectado - sesión terminó", "WARNING")
                        self.running = False
                        break

                response = "".join(response_lines).strip()

                # Limpiar códigos ANSI
                import re
                response = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', response)
                response = re.sub(r'\x1b\][^\x07]*\x07', '', response)

                log(f"📥 Respuesta capturada ({len(response)} chars)", "SUCCESS")
                return response

            except Exception as e:
                log(f"❌ Error enviando mensaje: {e}", "ERROR")
                import traceback
                log(traceback.format_exc(), "ERROR")
                return None

    def stop(self):
        """Detiene la sesión de Claude"""
        if self.process:
            log("🛑 Cerrando sesión de Claude...")
            try:
                self.process.sendcontrol('c')
                time.sleep(0.5)
                self.process.sendcontrol('d')
                time.sleep(0.5)
                self.process.terminate(force=True)
            except:
                pass
            self.running = False
            log("✅ Sesión cerrada", "SUCCESS")

# ══════════════════════════════════════════════
# Daemon Principal
# ══════════════════════════════════════════════

class ClaudeDaemon:
    def __init__(self, working_dir=None):
        self.working_dir = working_dir or os.getcwd()
        self.claude = ClaudePersistentSession(working_dir=self.working_dir)
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
                    # Extraer el texto del comando
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
        log("🚀 Claude Code Remote Daemon v3 - SESIÓN PERSISTENTE")
        log("=" * 60)
        log(f"Servidor: {SERVER_URL}")
        log(f"Working dir: {self.working_dir}")
        log(f"Poll interval: {POLL_INTERVAL}s")
        log("")

        # Iniciar sesión PERSISTENTE de Claude
        if not self.claude.start():
            log("❌ No se pudo iniciar Claude Code. Abortando.", "ERROR")
            return

        self.send_to_server(f"🤖 Daemon v3 conectado - Sesión persistente en: {self.working_dir}", "system")
        self.running = True

        # Loop principal
        try:
            while self.running:
                # Consultar por comandos
                command = self.poll_commands()

                if command:
                    # Enviar notificación
                    self.send_to_server(f"⏳ Procesando: {command}", "system")

                    # Enviar a sesión PERSISTENTE de Claude
                    response = self.claude.send_message(command)

                    if response:
                        # Enviar respuesta al servidor
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
        self.send_to_server("👋 Daemon v3 stopped", "system")
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

    parser = argparse.ArgumentParser(description='Claude Code Remote Daemon v3')
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
