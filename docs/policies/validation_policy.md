# Política de Validación de Árboles Sintácticos

> **Estado:** Activo | **Versión:** 1.0 | **Ámbito:** Core & Studio

## 1. Principios Fundamentales

Grammatomy adopta un enfoque pragmático y científicamente riguroso para la validación de árboles sintácticos, reconociendo la naturaleza híbrida de los modelos de procesamiento de lenguaje natural (NLP) modernos.

### 1.1. Integridad Estructural (Metasintaxis)
Para evitar la degeneración de los datos, todo árbol debe cumplir estrictamente con la siguiente topología:

1.  **Nodos de Grupo (Phrasal Nodes):** (e.g., `NP`, `VP`, `S`)
    *   *Contenido:* Solo pueden contener otros Grupos o Categorías Gramaticales (POS).
    *   *Restricción:* Nunca pueden contener texto (hojas) directamente.
2.  **Categorías Gramaticales (POS Nodes):** (e.g., `NOUN`, `VERB`, `n`)
    *   *Contenido:* Deben contener exactamente una Hoja (terminal).
    *   *Restricción:* No pueden tener hijos de Grupo.
3.  **Hojas (Terminals):**
    *   *Contenido:* Texto plano.
    *   *Restricción:* No pueden tener hijos.

### 1.2. Realidad Híbrida (Hybrid Reality)
Reconocemos y validamos la coexistencia de dos estándares en un mismo árbol, producto de los modelos SOTA (Stanza/Benepar):
*   **Estructura Superior:** Sigue las convenciones de **Constituyentes** (AnCora para ES, Penn Treebank para EN).
*   **Hojas (POS):** Sigue preferentemente el estándar **Universal Dependencies (UD)** (`NOUN`, `VERB`, `DET`) para maximizar la interoperabilidad, aunque se toleran etiquetas legacy (`n`, `v`, `d`) mediante una capa de transparencia.

---

## 2. Reglas Específicas por Idioma

El validador aplicará perfiles de reglas dinámicos según el idioma detectado.

### Español (Perfil: AnCora-Hybrid)
*   **Recursividad Nominal:** Se permite y valida que un `grup.nom` contenga oraciones subordinadas (`S`) o sintagmas preposicionales (`sp`) anidados, reflejando la estructura profunda de AnCora.
*   **Expansión de Contracciones:** Tokens como "del" deben expandirse estructuralmente en `sp (prep: de) + sn (det: el)`.
*   **Sujeto Nulo:** Se permite la ausencia de un nodo `sn` (sujeto) explícito bajo `S`, dado el carácter pro-drop del español.

### Inglés (Perfil: PTB-Standard)
*   **Jerarquía Estricta:** Se requiere la presencia de `VP` (Verb Phrase) bajo `S`.
*   **Etiquetas Funcionales:** Se validan etiquetas extendidas como `NP-SBJ` o `ADVP-TMP`.

### Italiano (Perfil: VIT-Flat)
*   **Estructura Plana:** Se permite que el nodo `S` contenga directamente al verbo y sus complementos sin un `VP` intermedio, siguiendo el Venice Italian Treebank.

---

## 3. Mecanismo de Edición y "Nodos Fantasma"

Para facilitar la edición humana en *Grammatomy Studio* sin romper la validación en tiempo real:

1.  **Ghost Nodes (👻):** Son hojas terminales temporales. Pueden ser hijos de cualquier nodo, pero **nunca pueden tener hijos**.
2.  **Validación Estricta de Mutación:** Un nodo fantasma solo puede transformarse (cambiar su etiqueta) a un tipo permitido explícitamente por su nodo padre. No se permiten saltos lógicos ni inferencias.
3.  **Crecimiento Determinista:** Si un fantasma muta a un nodo de Grupo (No-Terminal), el sistema genera automáticamente un único hijo fantasma debajo para mantener el árbol cerrado. Si muta a Terminal, el proceso concluye.
4.  **Borrado Recursivo:** La eliminación de un nodo implica la eliminación inmediata e irreversible de todo su subárbol descendente.
5.  **Estado de Plantilla:** Un árbol con fantasmas es sintácticamente válido (no viola reglas de paternidad) pero semánticamente incompleto.

---

## 4. Validación Léxica

*   **Puntuación:** Los signos de puntuación deben validarse contra el inventario del idioma. No pueden etiquetarse como palabras de contenido (e.g., una coma no puede ser un `NOUN`).
*   **Espacios:** Las hojas no pueden contener espacios (salvo MWEs tratados como unidad).

---

## 5. Política de Integridad y Gestión de Anomalías

La maduración del proyecto ha permitido transitar de un enfoque reactivo —donde las reglas se relajaban para acomodar las idiosincrasias de los modelos— a uno prescriptivo, donde la especificación YAML constituye el axioma de corrección estructural.

### 5.1. El Modelo de Restricción Asimétrica
Se establece una distinción fundamental en el tratamiento de las violaciones de reglas según su origen:

1.  **Violaciones de Modelo (Nodos "Enfermos"):**
    *   **Diagnóstico:** Si un modelo genera una estructura que incumple las restricciones (ej. omisión de un nivel jerárquico intermedio), el sistema identifica y marca visualmente el nodo como "enfermo" o anómalo.
    *   **Acción:** No se bloquea ni se descarta el árbol. Se prioriza la fidelidad al *output* del modelo, delegando en el experto humano la decisión final de corregir la anomalía o aceptarla como una limitación del motor.

2.  **Violaciones de Usuario (Prevención Activa):**
    *   **Diagnóstico:** Cualquier intento de modificación manual se evalúa *a priori* contra el conjunto de reglas.
    *   **Acción:** El sistema impide físicamente la creación de estados inválidos. Las operaciones que resultarían en una violación (ej. adjuntar un nodo a un padre prohibido) se bloquean en la interfaz (deshabilitación de menús, rechazo de *drag-and-drop*).
    *   **Corolario:** El usuario no puede introducir errores sintácticos; su interacción se limita estrictamente a la curación y perfeccionamiento del árbol dentro de los límites de la gramática definida.