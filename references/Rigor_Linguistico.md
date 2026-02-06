# Estándares de Rigor Lingüístico en Grammatomy

Grammatomy no es solo una herramienta de dibujo; es un entorno de edición sintáctica asistida que adhiere estrictamente a los estándares académicos más reconocidos para el análisis de constituyentes: **Penn Treebank II** (para estructuras generales) y **AnCora** (para especificidades del español).

Esta guía detalla las reglas de validación que el editor gráfico (`Grammatomy Studio`) impone para garantizar la consistencia de los corpus generados.

## 1. Integridad Estructural (Metasintaxis)

Para evitar la creación de árboles degenerados o lingüísticamente imposibles, el sistema impone las siguientes restricciones topológicas:

### A. Jerarquía de Derivación
El sistema distingue tres tipos de nodos y restringe sus relaciones parentales:

1.  **Nodos de Grupo (Phrasal Nodes):** (e.g., `NP`, `VP`, `S`)
    *   *Solo pueden contener:* Otros Grupos o Categorías Gramaticales (POS).
    *   *Prohibido:* No pueden contener Hojas (texto) directamente.
2.  **Categorías Gramaticales (POS Nodes):** (e.g., `NN`, `VBD`, `DT`)
    *   *Solo pueden contener:* Una única Hoja (palabra/terminal).
    *   *Prohibido:* No pueden tener hijos de Grupo ni múltiples palabras.
3.  **Hojas (Terminals):** (e.g., "gato", "come")
    *   *Prohibido:* No pueden tener hijos.

### B. Unidad Léxica (POS + Palabra)
En la edición visual, la jerarquía es estricta.
*   **Borrado en Cascada:** Al borrar un nodo, se elimina todo su subárbol. No existen nodos huérfanos flotantes.

### C. Prevención de Orfandad
*   No se permite eliminar o mover un nodo si es el **único hijo** de un Grupo. Esto evita la existencia de sintagmas vacíos (e.g., un `NP` sin núcleo ni determinantes) que romperían los parsers estándar.

---

## 2. Validación Gramatical (Valencias)

El editor consulta en tiempo real una gramática de transición (`grammatomy.grammar`) basada en los manuales de anotación de Penn y AnCora.

### Reglas Principales (Extracto)

#### Nivel Oracional (`S`, `ROOT`)
| Padre | Hijos Permitidos (Extracto) | Descripción |
| :--- | :--- | :--- |
| **S** | `NP`, `VP`, `PP`, `ADVP` | Estructura básica de cláusula. |
| **SQ** | `AUX`, `NP`, `VP` | Preguntas de sí/no invertidas. |

#### Nivel Sintagmático Nominal (`NP` / `sn`)
El sistema valida que los sintagmas nominales contengan elementos coherentes con la teoría de la X-barra:
*   **Determinantes:** `DT`, `CD`, `spec` (AnCora).
*   **Núcleos:** `NN`, `NNS`, `n` (AnCora), `PRP`.
*   **Modificadores:** `JJ` (Adjetivos), `PP` (Sintagmas Preposicionales), `SBAR` (Cláusulas relativas).

#### Nivel Sintagmático Verbal (`VP` / `grup.verb`)
Se restringe la adjunción a complementos verbales válidos:
*   **Formas Verbales:** `VB`, `VBD`, `v` (AnCora).
*   **Argumentos:** `NP` (Objeto Directo), `PP` (Complementos Circunstanciales/Régimen).
*   **Negación:** `neg`.

### Interoperabilidad Penn-AnCora
Grammatomy permite (y valida) estructuras híbridas necesarias para el procesamiento moderno del español, donde a menudo se mezclan etiquetas de alto nivel de Penn (`S`) con etiquetas morfológicas ricas de AnCora (`grup.nom`).

---

## 3. Referencias Académicas

La lógica de validación se ha extraído de las siguientes fuentes normativas:

1.  **Bies, A., et al. (1995).** *Bracketing Guidelines for Treebank II Style*. University of Pennsylvania.
    *   Define la estructura canónica para `NP`, `VP`, `SBAR`, etc.
2.  **Taulé, M., et al. (2008).** *AnCora: Multilevel Annotated Corpora for Catalan and Spanish*.
    *   Define las estructuras específicas del español como `grup.nom`, `morfema.pronominal`, etc.

---

## 4. Mecanismo de "Nodos Fantasma" (Ghost Nodes 👻)

Para facilitar la creación de estructuras complejas sin violar las reglas de validación momentáneamente, Grammatomy utiliza **Nodos Fantasma**.

*   **Naturaleza:** Hoja terminal estéril. No admite hijos.
*   **Mutación Estricta:** Solo acepta etiquetas validadas contra el padre inmediato.
*   **Expansión:** Al asignar una etiqueta no-terminal (e.g., `NP`) a un fantasma, este se solidifica y engendra automáticamente un hijo fantasma.
*   **Estado:** Un árbol con fantasmas es un "Árbol Abstracto" válido para guardar pero incompleto para procesar.

---

## 5. Tratamiento de la Puntuación

Aunque en la sintaxis formal los signos de puntuación a menudo se consideran elementos periféricos ("ciudadanos de segunda clase" sin proyección estructural), en Grammatomy son vitales para la segmentación prosódica.

*   **Adjunción:** No forman grupos propios. Se adjuntan como hermanos directos dentro del sintagma donde aparecen (e.g., una coma dentro de un `S` o un `NP`).
*   **Inventario Dual:** El sistema soporta y sugiere automáticamente tanto las etiquetas simbólicas de Penn (e.g., `,`, `.`) como las funcionales de AnCora (e.g., `fc`, `fp`).
*   **Asistencia:** Dado que estas etiquetas son difíciles de memorizar, el editor incluye un asistente dedicado ("Añadir Puntuación") que infiere la etiqueta correcta a partir del signo gráfico introducido.

---

## 6. Validación Léxica y Lexicón

Para garantizar la coherencia entre el texto terminal (Hoja) y su categoría gramatical (POS), el sistema implementa dos niveles de control:

1.  **Validación Formal (Nativa):**
    *   *Palabras:* No pueden contener espacios (salvo guiones de composición) ni caracteres reservados de puntuación.
    *   *Puntuación:* Debe pertenecer al inventario de signos válidos para el idioma configurado.
2.  **Validación Semántica (Lexicón):**
    *   La arquitectura dispone de un *hook* de validación (`LEXICON_HOOK`) diseñado para integrarse con diccionarios externos o bases de datos léxicas.
    *   Esto permite, en implementaciones avanzadas, rechazar asignaciones semánticamente inválidas (e.g., etiquetar "casa" como Verbo) consultando un lexicón real.

---

## 7. Realidad Híbrida y Redundancia de Etiquetas

Debido a la evolución de los corpus de entrenamiento (transición de estándares EAGLES/AnCora a Universal Dependencies), los modelos neuronales actuales (Stanza, Benepar) a menudo generan árboles con una mezcla heterogénea de etiquetas para las categorías gramaticales (POS).

Grammatomy adopta oficialmente el estándar **Universal Dependencies (UD)** para las hojas (POS) por su claridad y universalidad, manteniendo la estructura **AnCora** para los sintagmas superiores.

| Categoría | Etiqueta UD (Estándar) | Notas |
| :--- | :--- | :--- | :--- |
| **Sustantivo** | `NOUN`, `PROPN` | |
| **Verbo** | `VERB`, `AUX` | |
| **Adjetivo** | `ADJ` | |
| **Determinante** | `DET` | |
| **Pronombre** | `PRON` | |
| **Adverbio** | `ADV` | |
| **Preposición** | `ADP` | |
| **Conjunción** | `CCONJ`, `SCONJ` | |
| **Número** | `NUM` | |
| **Símbolo** | `SYM` | |

**Política de Validación:** Las etiquetas legacy de AnCora (`n`, `v`, `d`, etc.) se consideran obsoletas y el editor las marcará como inválidas para forzar la convergencia hacia UD.