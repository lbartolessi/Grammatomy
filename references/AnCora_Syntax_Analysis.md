# Análisis de Sintaxis AnCora (Basado en Guías Oficiales)

Este documento resume las reglas sintácticas extraídas de la documentación oficial de AnCora ("Guia sintaxi.txt", "3LB-WP 03-02") para informar la lógica de validación de Grammatomy.

## 1. Estructura de Constituyentes (Nivel de Frase)

AnCora sigue un formalismo **X-Barra** modificado. Esto implica una jerarquía de tres niveles que los modelos neuronales modernos a menudo aplanan.

### Sintagma Nominal (`sn`)
*   **Estructura Canónica:** `sn` -> `(spec)` + `grup.nom`
*   **Grupo Nominal (`grup.nom`):** Contiene el núcleo y sus complementos.
    *   `grup.nom` -> `(nucleo)` + `(complementos)`
*   **Implicación para Grammatomy:**
    *   **Validación Estricta:** Debe exigir la presencia de `grup.nom`. Un `sn` no puede contener directamente un `noun`.
    *   **Validación Laxa:** Debe permitir `sn` -> `noun` (colapso de niveles).

### Grupo Verbal (`grup.verb`)
*   **Definición:** Contiene solo las formas verbales conjugadas (simples o compuestas) y perífrasis.
*   **Nota:** No incluye el sujeto ni los complementos del verbo (estos cuelgan de `S`, no de `grup.verb`).
*   **Implicación:** A diferencia del `VP` del inglés (que incluye el objeto), el `grup.verb` es solo el núcleo complejo del predicado.

## 2. Fenómenos Especiales

### Sujetos Elípticos
*   **AnCora:** Inserta un nodo `sn` vacío con el atributo `elliptic="yes"`.
*   **Modelos SOTA:** Omiten el nodo.
*   **Política:** El modo estricto podría advertir sobre la falta de sujeto explícito o elíptico, mientras que el modo laxo lo ignora.

### Coordinación
*   **Estructura:** Los elementos coordinados y la conjunción son **hermanos** (sisters). No hay jerarquía entre ellos.
*   **Etiqueta:** El nodo padre de una coordinación toma la categoría de los elementos coordinados (ej. `sn` coordinado con `sn` resulta en un padre `sn` con atributo `coord="yes"`).

## 3. Mapeo de Categorías (Hibridación)

Dado que Grammatomy utiliza etiquetas UD (Universal Dependencies) para las hojas, se establece la siguiente equivalencia para la validación:

| Categoría AnCora | Categoría UD (Grammatomy) | Contexto |
| :--- | :--- | :--- |
| `n` (nombre) | `NOUN`, `PROPN` | Núcleo de `grup.nom` |
| `v` (verbo) | `VERB`, `AUX` | Núcleo de `grup.verb` |
| `a` (adjetivo) | `ADJ` | Núcleo de `grup.a` |
| `d` (determinante)| `DET` | Hijo de `spec` |

## 4. Criterios de Validación Diferenciada

### Perfil Estricto (Academic)
*   Requiere `grup.nom` dentro de `sn`.
*   Requiere `grup.verb` dentro de `S` (salvo oraciones nominales marcadas).
*   No permite mezcla de categorías incompatibles (ej. `DET` como núcleo de `grup.nom` sin nominalización).

### Perfil Laxo (Pragmatic)
*   Permite colapso de proyección (ej. `sn` -> `NOUN`).
*   Permite `S` -> `VERB` directo (estilo VIT italiano).
*   Valida por "intención": si hay un núcleo nominal, se acepta como `sn` válido aunque falte la estructura intermedia.