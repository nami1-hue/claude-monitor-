# 📚 Documentación - Claude Monitor

## 🚀 Para empezar

### 👉 **EMPEZAR AQUÍ:**
- **[QUICKSTART.md](QUICKSTART.md)** - Setup en 5 minutos (para apurados)
- **[README.md](README.md)** - Overview del proyecto

---

## 📖 Documentación completa

### 🎮 **Multi-Proyecto** (NEW!)
- **[MULTI_PROJECT_SETUP.md](MULTI_PROJECT_SETUP.md)** - Guía completa
  - Configuración en Railway
  - Instalación de múltiples daemons
  - Uso de la interfaz web
  - API endpoints
  - Troubleshooting
  - Variables de entorno

### 🔐 **Seguridad**
- **[SECURITY_SETUP.md](SECURITY_SETUP.md)** - Seguridad y autenticación
  - Contraseña
  - HTTPS
  - Validación de endpoints

### 📝 **Histórico de cambios**
- **[CHANGELOG.md](CHANGELOG.md)** - Historial de versiones
  - v2.0.0 - Multi-proyecto (actual)
  - v1.0.0 - Release inicial

---

## 🛠️ Archivos y scripts

### Archivos de configuración
| Archivo | Descripción |
|---------|------------|
| `PROJECTS_EXAMPLE.json` | Ejemplo de configuración de proyectos |
| `railway.json` | Configuración de Railway |
| `Procfile` | Entry point para Railway |

### Scripts de utilidad
| Script | Descripción |
|--------|------------|
| `install-daemon.sh` | Instala daemon para un proyecto (interactivo) |
| `test-setup.sh` | Verifica que todo está configurado |

### Código
| Archivo | Descripción |
|---------|------------|
| `server.py` | Servidor Flask con soporte multi-proyecto |
| `cc-daemon-v3.py` | Daemon persistente de Claude Code |
| `templates/monitor.html` | Interfaz web con selector de proyecto |
| `templates/login.html` | Página de login |
| `requirements.txt` | Dependencias Python |

---

## 🎯 Flujos de trabajo típicos

### Primer setup
```
1. Lee: QUICKSTART.md (5 min)
2. Configura: PROJECTS en Railway
3. Corre: ./install-daemon.sh
4. Prueba: ./test-setup.sh
5. Abre: https://tuurl.railway.app
```

### Agregar nuevo proyecto
```
1. Lee: MULTI_PROJECT_SETUP.md → "Configuración en Railway"
2. Edita: Variable PROJECTS en Railway
3. Corre: ./install-daemon.sh nuevo-proyecto ~/ruta
4. Verifica: En web ves el nuevo proyecto
```

### Troubleshooting
```
1. Corre: ./test-setup.sh
2. Lee: MULTI_PROJECT_SETUP.md → "Troubleshooting"
3. Revisa: Logs del daemon (journalctl -u cc-daemon-*)
4. Verifica: Variables de entorno (PROJECT_ID, MONITOR_URL, etc)
```

### Deploy en Railway
```
1. Lee: README.md → "Deploy en Railway"
2. Copia: archivos a tu repo
3. Vincula: GitHub a Railway
4. Configura: PROJECTS y MONITOR_PASSWORD
5. Deploy automático ✅
```

---

## 📊 Mapa de conceptos

```
┌─────────────────────────────────────────────────────────────┐
│                   Claude Monitor v2.0                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Server (Railway)                                            │
│  ├─ server.py                                               │
│  ├─ Multi-proyecto support                                  │
│  ├─ API endpoints                                           │
│  └─ Web interface                                           │
│                                                              │
│  Daemons (Local machines)                                   │
│  ├─ cc-daemon-v3.py                                         │
│  ├─ PROJECT_ID #1 → phd-research                           │
│  ├─ PROJECT_ID #2 → hc-acop                                │
│  ├─ PROJECT_ID #3 → other-project                          │
│  └─ PROJECT_ID #4 → ...                                    │
│                                                              │
│  Frontend (Browser)                                         │
│  ├─ monitor.html                                            │
│  ├─ Project selector                                       │
│  ├─ Message feed                                            │
│  ├─ Command input                                           │
│  └─ Approval buttons                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📞 Referencia rápida

### Instalar daemon
```bash
./install-daemon.sh PROJECT_ID ~/ruta/proyecto
```

### Verificar setup
```bash
./test-setup.sh
```

### Ver estado
```bash
sudo systemctl status cc-daemon-PROJECT_ID
```

### Ver logs
```bash
journalctl -u cc-daemon-PROJECT_ID -f
```

### URL del monitor
```
https://eloquent-quietude-production.up.railway.app
```

---

## 🔗 Enlaces importantes

- **Railway Dashboard:** https://railway.app/dashboard
- **GitHub:** https://github.com/nami1-hue/claude-monitor-
- **Este repositorio:** ~/claude-monitor-railway/

---

## ✅ Checklist de setup

- [ ] Leí QUICKSTART.md
- [ ] Configuré PROJECTS en Railway
- [ ] Ejecuté `./install-daemon.sh` para mis proyectos
- [ ] Ejecuté `./test-setup.sh` y pasó
- [ ] Abro el monitor en navegador
- [ ] Selecciono proyecto y veo mensajes
- [ ] Envío un comando de prueba
- [ ] ¡Funciona! 🎉

---

## 🐛 Necesitas ayuda?

1. **Setup:** QUICKSTART.md + test-setup.sh
2. **Configuración:** MULTI_PROJECT_SETUP.md
3. **Problemas:** MULTI_PROJECT_SETUP.md → Troubleshooting
4. **Seguridad:** SECURITY_SETUP.md

---

**Documentación actualizada:** 2026-04-02
**Versión:** 2.0.0 (Multi-Project)
