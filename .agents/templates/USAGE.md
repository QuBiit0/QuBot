# Guía de Uso de Templates LMAgent

Los templates ubicados en esta carpeta están diseñados para ser puntos de partida listos para usar para nuevos componentes de tu sistema.

## Flujo de Trabajo General

1. **Elegir**: Selecciona el template adecuado para tu tarea.
2. **Copiar**: Duplica la carpeta del template a tu destino.
3. **Personalizar**: Ajusta la configuración y nombres.
4. **Instalar**: Instala las dependencias y corre.

---

## 🐍 Backend Python (FastAPI)

Ideal para microservicios robustos, APIs de datos o lógica de negocio compleja.

**Pasos:**

1. Copia el template:
   ```bash
   cp -r templates/backend-python servicios/mi-nuevo-servicio
   ```

2. Navega al directorio:
   ```bash
   cd servicios/mi-nuevo-servicio
   ```

3. Crea tu entorno virtual e instala dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # o venv\Scripts\activate en Windows
   pip install -r requirements.txt
   ```

4. Configura el entorno:
   ```bash
   cp .env.example .env  # (Si existe, sino crea uno basado en config.py)
   ```

5. Ejecuta:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🟢 Backend Node (Express + TS)

Ideal para servicios ligeros, webhooks, o adaptadores de integración.

**Pasos:**

1. Copia el template:
   ```bash
   cp -r templates/backend-node servicios/mi-adaptador
   ```

2. Instala dependencias:
   ```bash
   cd servicios/mi-adaptador
   npm install
   ```

3. Ejecuta en desarrollo:
   ```bash
   npm run dev
   ```

---

## ⚡ Automation n8n

Para flujos de automatización visual.

**Pasos:**

1. Abre n8n en tu navegador.
2. Crea un nuevo workflow.
3. Copia el contenido de `templates/automation-n8n/webhook-handler.json`.
4. Pega (Ctrl+V) directamente en el canvas de n8n.
5. Ajusta los nodos a tu necesidad.

---

## 🤖 Agent Python

Para crear agentes autónomos especializados.

**Pasos:**

1. Copia `templates/agent-python` a tu carpeta de agentes.
2. Define el `system.md` en la carpeta `prompts`.
3. Configura las herramientas disponibles en `config.yaml`.
