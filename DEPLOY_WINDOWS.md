# 🪟 Qubot Deployment Guide for Windows

Guía completa para desplegar Qubot en Windows usando Docker Desktop.

---

## 📋 Prerequisites

### 1. Docker Desktop

**Descargar e instalar:**
```
https://docs.docker.com/desktop/install/windows-install/
```

**Requisitos:**
- Windows 10/11 (64-bit)
- WSL2 backend (recomendado) o Hyper-V
- Mínimo 4GB RAM (8GB recomendado)
- ~10GB espacio libre en disco

**Durante la instalación:**
1. ✅ Marca "Use WSL 2 instead of Hyper-V" (recomendado)
2. ✅ Marca "Add shortcut to desktop"
3. Reinicia tu computadora cuando lo pida

---

## 🚀 Quick Start (3 Pasos)

### Paso 1: Iniciar Docker Desktop

1. Presiona la tecla **Windows**
2. Escribe **"Docker Desktop"**
3. Haz clic para abrirlo
4. **Espera** hasta que el ícono de la ballena deje de animarse (30-60 segundos)

> ⚠️ **IMPORTANTE**: No continues hasta que Docker Desktop muestre "Engine running" en verde

### Paso 2: Abrir Git Bash

1. Presiona la tecla **Windows**
2. Escribe **"Git Bash"**
3. Haz clic para abrirlo

### Paso 3: Ejecutar el Deploy

```bash
# Navegar al proyecto
cd c:/Users/TuUsuario/Desktop/Qubot

# Ejecutar el script de despliegue
./scripts/deploy-local.sh
```

---

## 🔍 Verificar el Despliegue

### Método 1: Script de Diagnóstico (Recomendado)

```bash
# En Git Bash o PowerShell
./scripts/check-deployment.ps1
```

### Método 2: Comandos Docker

```bash
# Ver contenedores corriendo
docker ps

# Ver logs
docker compose -f docker-compose.local.yml logs -f

# Ver estado de todos los servicios
docker compose -f docker-compose.local.yml ps
```

### Método 3: Navegador

Abre tu navegador y visita:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

---

## ❌ Solución de Problemas

### Error: "Docker no está corriendo"

**Síntoma:**
```
ERROR: Docker daemon is not running
```

**Solución:**
1. Abre Docker Desktop desde el menú de inicio
2. Espera 30-60 segundos hasta que diga "Engine running"
3. Intenta de nuevo

---

### Error: "Port already in use"

**Síntoma:**
```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**Causa:** PostgreSQL o Redis ya están corriendo localmente en Windows

**Solución 1 - Detener servicios de Windows:**
```powershell
# En PowerShell como Administrador
Stop-Service postgresql-x64-15
Stop-Service redis
```

**Solución 2 - Usar el script de fix:**
```bash
./scripts/fix-deployment.sh
```

---

### Error: "Cannot connect to the Docker daemon"

**Síntoma:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solución:**
1. Cierra Git Bash
2. Abre Docker Desktop
3. Espera a que cargue completamente
4. Abre Git Bash nuevamente

---

### Error: "No such file or directory"

**Síntoma:**
```
bash: ./scripts/deploy-local.sh: No such file or directory
```

**Solución:**
```bash
# Asegúrate de estar en el directorio correcto
cd /c/Users/TuUsuario/Desktop/Qubot

# O usa la ruta completa
cd c:/Users/TuUsuario/Desktop/Qubot
```

---

### Los contenedores no aparecen en Docker Desktop

**Pasos:**

1. **Verifica que Docker Desktop esté corriendo:**
   ```bash
   docker info
   ```

2. **Verifica el estado de los contenedores:**
   ```bash
   docker ps -a
   ```

3. **Si no aparecen, ejecuta el despliegue:**
   ```bash
   ./scripts/deploy-local.sh
   ```

4. **Si hay errores de build, limpia y reconstruye:**
   ```bash
   ./scripts/fix-deployment.sh
   ```

---

## 🛠️ Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `deploy-local.sh` | Despliegue completo con verificaciones |
| `check-deployment.ps1` | Diagnóstico del estado actual |
| `check-deployment.sh` | Diagnóstico (Linux/Mac/Git Bash) |
| `fix-deployment.sh` | Limpia y reconstruye todo |

---

## 📁 Estructura de Puertos

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 8000 | API | Backend FastAPI |
| 3000 | Frontend | Next.js |
| 5432 | PostgreSQL | Base de datos |
| 6379 | Redis | Cache y colas |

---

## 🔄 Comandos Útiles

```bash
# Iniciar servicios
docker compose -f docker-compose.local.yml up -d

# Ver logs en tiempo real
docker compose -f docker-compose.local.yml logs -f

# Ver logs de un servicio específico
docker compose -f docker-compose.local.yml logs -f api

# Detener servicios
docker compose -f docker-compose.local.yml down

# Detener y eliminar volúmenes (limpieza completa)
docker compose -f docker-compose.local.yml down -v

# Reconstruir imágenes
docker compose -f docker-compose.local.yml up --build -d

# Reiniciar un servicio específico
docker compose -f docker-compose.local.yml restart api
```

---

## 🆘 Obtener Ayuda

Si nada funciona, ejecuta este comando y comparte la salida:

```bash
# En PowerShell
.\scripts\check-deployment.ps1

# En Git Bash
./scripts/check-deployment.sh
```

Luego revisa los logs:
```bash
docker compose -f docker-compose.local.yml logs > qubot-logs.txt 2>&1
```

---

## ✅ Checklist Pre-Deploy

- [ ] Docker Desktop instalado
- [ ] Docker Desktop iniciado y "Engine running"
- [ ] Git Bash instalado
- [ ] Puerto 5432 libre (no hay PostgreSQL local corriendo)
- [ ] Puerto 6379 libre (no hay Redis local corriendo)
- [ ] Estás en el directorio correcto del proyecto
- [ ] Archivo `.env` existe (se creará automáticamente de `.env.example`)

---

**¿Problemas persistentes?** Revisa la guía completa en `DEPLOY.md`
