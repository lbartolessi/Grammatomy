# Diseño de Arquitectura de Aplicación

> **Objetivo:** Definir la estructura técnica para la transición de Demo (Streamlit) a Producto (Studio & API).

## 1. Visión General

Grammatomy evoluciona hacia una arquitectura desacoplada **Cliente-Servidor**. Esto permite que el motor de análisis (pesado, Python/Torch) funcione independientemente de la interfaz de usuario (ligera, Web/JS), facilitando despliegues tanto locales como remotos.

---

## 2. Componentes del Sistema

### 2.1. Backend (Core & API)
*   **Tecnología:** Python 3.11+, FastAPI.
*   **Responsabilidad:**
    *   Carga y gestión de modelos neuronales (Stanza/spaCy).
    *   Procesamiento de texto a árboles (Parsing).
    *   Validación estructural (Lógica de negocio).
    *   Persistencia local de configuración (`config.yaml`).
*   **Diseño:** Stateless (sin estado). Cada petición `/parse` es atómica.

### 2.2. Frontend (Web Client)
*   **Tecnología:** Lit (Web Components), TypeScript, Vite.
*   **Filosofía:** "Standard-Based". Uso de estándares web nativos sobre frameworks monolíticos.
*   **Componentes Clave:**
    *   `<grammatomy-editor>`: Lienzo interactivo para manipular árboles (SVG/Canvas).
    *   `<grammatomy-tree-view>`: Visualizador de solo lectura.
    *   `<grammatomy-console>`: Panel de control y logs.
*   **Styling:** Light DOM para máxima compatibilidad con CSS global.

### 2.3. Grammatomy Studio (Desktop Wrapper)
*   **Tecnología:** Python (PySide6 / Qt6) + QWebEngineView.
*   **Función:**
    *   Actúa como un navegador dedicado que carga el Frontend.
    *   Gestiona el ciclo de vida del servidor FastAPI en segundo plano (invisible para el usuario).
    *   Proporciona acceso al sistema de archivos nativo (Abrir/Guardar proyectos).

---

## 3. Flujo de Datos

1.  **Input:** El usuario introduce texto en el Cliente (Web/Studio).
2.  **Request:** El Cliente envía `POST /parse { text: "...", config: {...} }` al Backend.
3.  **Processing:**
    *   El Backend selecciona el motor según `config.yaml`.
    *   Genera el árbol sintáctico.
    *   Aplica reglas de validación (`src.core.grammatomy.validation`).
4.  **Response:** Devuelve JSON con la estructura del árbol y metadatos de validación.
5.  **Rendering:** El componente `<grammatomy-editor>` dibuja el árbol y permite la edición visual (Drag & Drop).

---

## 4. Principios de Diseño

*   **Model Sovereignty:** La configuración de modelos reside en el disco del usuario, no en la nube. El Backend es la autoridad sobre qué modelos están disponibles.
*   **Zero-Config Deployment:** La aplicación de escritorio (Studio) debe incluir el runtime de Python y los modelos mínimos necesarios para arrancar sin configuración externa.
*   **Interoperabilidad:** El formato de intercambio es JSON estándar, permitiendo que otros clientes consuman la API.
