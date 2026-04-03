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
PROJECT_ID = os.getenv("PROJECT_ID", "default")  # ID del proyecto que maneja este daemon
POLL_INTERVAL = 2  # segundos
LOG_FILE = f"/tmp/cc-daemon-v3-{PROJECT_ID}.log"

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
            'ANTHROPIC_MODEL': env.get('ANTHROPIC_MODEL', 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0'),
            'AWS_PROFILE': env.get('AWS_PROFILE', 'hc-qa-admin'),
            'AWS_REGION': 'eu-central-1',
            'NODE_TLS_REJECT_UNAUTHORIZED': '0',
            'TERM': 'xterm-256color'
        })

        try:
            # Iniciar Claude en modo INTERACTIVO (sin --print)
            self.process = pexpect.spawn(
                'bash',
                ['-c', f'cd {self.working_dir} && TERM=dumb claude'],
                env=env,
                encoding='utf-8',
                timeout=300,
                maxread=50000,
                dimensions=(100, 200)
            )

            # Desabilitar raw mode para evitar códigos ANSI problemáticos
            self.process.setecho(False)

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

                # CRÍTICO: Dar MUCHO más tiempo a Claude para procesar
                # Claude puede tardar 5-15 segundos en generar respuestas
                log("   ⏰ Esperando que Claude procese (10s)...")
                time.sleep(10)

                response_lines = []
                start_time = time.time()
                timeout = 120  # 2 minutos

                # Estrategia: leer hasta silencio prolongado
                silence_threshold = 8  # 8 segundos de silencio
                last_read_time = time.time()
                total_read = 0

                while True:
                    try:
                        # Leer con timeout más largo
                        chunk = self.process.read_nonblocking(size=4000, timeout=1.5)

                        if chunk:
                            response_lines.append(chunk)
                            last_read_time = time.time()
                            total_read += len(chunk)

                            # Solo loguear cada 2000 chars para no spam
                            if total_read % 2000 < 100:
                                log(f"   📥 Capturando... {total_read} chars")

                        # Si llevamos más de silence_threshold sin leer Y ya tenemos contenido, terminamos
                        if time.time() - last_read_time > silence_threshold and total_read > 100:
                            log(f"✅ Respuesta completa ({total_read} chars total)")
                            break

                        # Timeout general
                        if time.time() - start_time > timeout:
                            log("⚠️  Timeout general alcanzado")
                            break

                    except pexpect.TIMEOUT:
                        # Timeout del read_nonblocking
                        if total_read > 100 and time.time() - last_read_time > silence_threshold:
                            log(f"✅ Fin por timeout con contenido ({total_read} chars)")
                            break
                        # Si no hay contenido sustancial aún, seguir esperando
                        continue

                    except pexpect.EOF:
                        log("⚠️  EOF detectado - sesión terminó", "WARNING")
                        self.running = False
                        break

                response = "".join(response_lines).strip()

                # Limpiar códigos ANSI agresivamente
                import re
                response = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', response)      # CSI sequences
                response = re.sub(r'\x1b\][^\x07]*\x07', '', response)          # OSC sequences
                response = re.sub(r'\[\?[0-9]+[hl]', '', response)              # Bracketed paste mode
                response = re.sub(r'\x1b\[[;?]*[0-9;?]*[a-zA-Z]', '', response) # Más CSI
                response = re.sub(r'[\[\?0-9]+[hl]', '', response)              # Bracket sequences

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
                    "project_id": PROJECT_ID,
                    "type": msg_type,
                    "content": message,
                    "is_approval": False
                },
                timeout=10
            )
            if response.status_code == 200:
                log(f"✅ Mensaje enviado al servidor ({len(message)} chars)")
                return True
            else:
                log(f"⚠️  Servidor respondió con {response.status_code}: {response.text[:100]}", "WARNING")
                return False
        except Exception as e:
            log(f"⚠️  Error enviando al servidor: {e}", "WARNING")
            return False

    def poll_commands(self):
        """Consulta servidor por comandos pendientes"""
        try:
            response = requests.get(
                f"{SERVER_URL}/api/poll_command",
                params={"project_id": PROJECT_ID},
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
        log(f"Proyecto: {PROJECT_ID}")
        log(f"Working dir: {self.working_dir}")
        log(f"Poll interval: {POLL_INTERVAL}s")
        log("")

        # Iniciar sesión PERSISTENTE de Claude
        if not self.claude.start():
            log("❌ No se pudo iniciar Claude Code. Abortando.", "ERROR")
            return

        self.send_to_server(f"🤖 Daemon v3 conectado - Proyecto: {PROJECT_ID} - Sesión persistente en: {self.working_dir}", "system")
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
    parser.add_argument('--project-id', type=str, default=os.getenv('PROJECT_ID', 'default'),
                        help='Project ID for this daemon (default: PROJECT_ID env var or "default")')
    args = parser.parse_args()

    # Override PROJECT_ID if provided via CLI
    if args.project_id and args.project_id != 'default':
        os.environ['PROJECT_ID'] = args.project_id
        globals()['PROJECT_ID'] = args.project_id

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
