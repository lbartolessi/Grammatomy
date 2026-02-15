Entendido. Procedo a realizar la extracción arqueológica del esquema sintáctico de **AnCora-ES**, basándome estrictamente en los manuales de etiquetado del **CLiC-UB** (Centro de Lenguaje y Computación de la Universidad de Barcelona).

La arquitectura de AnCora es jerárquica y se distingue por el uso de puntos para denotar niveles de agrupación (como `grup.nom` vs `sn`). A continuación, presento la especificación técnica en YAML, respetando el sistema de etiquetas POS de una sola letra (Eagles/AnCora) y la estructura de constituyentes original.

```yaml
meta:
  source: "AnCora-ES Official Guidelines (CLiC-UB)"
  version: "Canonical Ground Truth"
  annotators: "Taulé, Martí, Recasens"

nodes:
  - id: "sentence"
    type: "root"
    description: "Oración principal o nodo raíz del árbol."
    structure:
      mandatory: ["S" | "sn" | "grup.verb"]
      optional: ["f", "inc", "coord"]
    patterns:
      - ["S", "f"]
      - ["sn", "grup.verb", "f"]
      - ["interjeccio", "f"]

  - id: "S"
    type: "clause"
    description: "Oración (subordinada o constituyente de sentence). Puede ser finita o no personal."
    structure:
      head: ["grup.verb"]
      optional: ["sn", "sp", "s.a", "sadv", "conj", "relatiu", "morfema.pronominal", "neg"]
    patterns:
      - ["conj", "sn", "grup.verb"] # Subordinada sustantiva/adverbial
      - ["relatiu", "grup.verb"] # Subordinada de relativo
      - ["morfema.pronominal", "grup.verb"] # Pasiva refleja o impersonal
      - ["infinitiu"] # Cláusula de infinitivo
      - ["gerundi"] # Cláusula de gerundio
      - ["participi"] # Cláusula de participio

  - id: "sn"
    type: "phrase"
    description: "Sintagma Nominal. Contiene obligatoriamente un grupo nominal."
    structure:
      mandatory: ["grup.nom"]
      optional: ["spec", "s.a", "sp", "S", "coord", "f"]
    patterns:
      - ["spec", "grup.nom"]
      - ["grup.nom"]
      - ["spec", "grup.nom", "s.a"]
      - ["spec", "grup.nom", "sp"]
      - ["spec", "grup.nom", "S"] # SN con subordinada de relativo

  - id: "grup.nom"
    type: "group"
    description: "Grupo Nominal (Núcleo del SN). Maneja la aposición y expansión adyacente."
    structure:
      head: ["n", "p", "w", "z"] # n=nombre, p=pronombre, w=fecha, z=número
      optional: ["s.a", "sp", "sn", "S", "f"]
    patterns:
      - ["n"]
      - ["p"]
      - ["n", "s.a"]
      - ["n", "sp"]
      - ["n", "sn"] # Aposición nominal
      - ["n", "f", "sn", "f"] # Aposición explicativa
      - ["z"] # Numerales como núcleo

  - id: "sp"
    type: "phrase"
    description: "Sintagma Preposicional."
    structure:
      head: ["s"] # s=preposición
      mandatory: ["sn" | "S" | "sadv" | "sp"] # sp recursivo para locuciones
    patterns:
      - ["s", "sn"]
      - ["s", "S"] # Prep + Oración (ej: 'para que...')
      - ["s", "sadv"] # ej: 'desde hoy'

  - id: "grup.verb"
    type: "group"
    description: "Grupo Verbal. Incluye formas simples, compuestas y perífrasis."
    structure:
      head: ["v"] # v=verbo
      optional: ["morfema.verbal", "morfema.pronominal", "neg"]
    patterns:
      - ["v"]
      - ["morfema.verbal", "v"] # Perífrasis con 'va' o auxiliares
      - ["neg", "v"]
      - ["morfema.pronominal", "v"] # Verbos pronominales

  - id: "s.a"
    type: "phrase"
    description: "Sintagma Adjetival."
    structure:
      head: ["grup.a"]
      optional: ["spec"] # spec suele ser un adverbio de grado (r)
    patterns:
      - ["grup.a"]
      - ["spec", "grup.a"]

  - id: "grup.a"
    type: "group"
    description: "Grupo Adjetival."
    structure:
      head: ["a"] # a=adjetivo
      optional: ["sp", "sadv", "S"]
    patterns:
      - ["a"]
      - ["a", "sp"] # ej: 'proclive a...'

  - id: "sadv"
    type: "phrase"
    description: "Sintagma Adverbial."
    structure:
      head: ["grup.adv"]
      optional: ["spec"]
    patterns:
      - ["grup.adv"]
      - ["spec", "grup.adv"]

  - id: "grup.adv"
    type: "group"
    description: "Grupo Adverbial."
    structure:
      head: ["r"] # r=adverbio
      optional: ["sp", "sadv"]
    patterns:
      - ["r"]
      - ["r", "sp"]

  - id: "spec"
    type: "functional"
    description: "Especificador. Generalmente determinantes o cuantificadores."
    structure:
      head: ["d", "r", "z"] # d=determinante, r=adverbio (grado), z=número
    patterns:
      - ["d"]
      - ["r"]
      - ["d", "d"] # ej: 'todos los'

  - id: "coord"
    type: "connection"
    description: "Estructura de coordinación."
    structure:
      mandatory: ["conj"] # c=conjunción
      elements: ["sn", "S", "grup.verb", "s.a", "sp", "sadv"]
    patterns:
      - ["sn", "conj", "sn"]
      - ["S", "f", "S", "conj", "S"]
      - ["conj", "S"] # Coordinación inicial

  - id: "morfema.pronominal"
    type: "functional"
    description: "Clítico con valor de SE (pasiva refleja, impersonal, pronominal)."
    structure:
      head: ["p"] # Generalmente 'p0000000' en AnCora

  - id: "morfema.verbal"
    type: "functional"
    description: "Auxiliares en perífrasis y tiempos compuestos."
    structure:
      head: ["v"]

  - id: "inc"
    type: "clause"
    description: "Inciso o elemento parentético."
    structure:
      head: ["S", "sn", "sp", "f"]
    note: "Se usa para marcar aposiciones extensas o comentarios del narrador entre comas o guiones."

  - id: "interjeccio"
    type: "other"
    description: "Interjección."
    structure:
      head: ["i"]

  - id: "grup.cc"
    type: "obscure"
    description: "Grupo de Complemento Circunstancial (poco frecuente)."
    note: "En versiones tardías de AnCora, se prefiere colapsar en 'sp' o 'sadv' con función CC, pero aparece en el corpus para locuciones adverbiales complejas."
    structure:
      head: ["r", "s"]

```

### Notas Técnicas del Arqueólogo:

1. **Recursividad:** El nodo `sn` es altamente recursivo a través de `sp` y `grup.nom` (aposiciones).
2. **Núcleos (Heads):** En AnCora, el núcleo no siempre es un terminal; por ejemplo, en un `sn`, el núcleo es un `grup.nom`, y dentro de este se encuentra el terminal `n` (nombre).
3. **Etiquetas POS:** He mantenido la nomenclatura de una sola letra original del sistema Eagles-AnCora: `d` (determinante), `n` (nombre), `v` (verbo), `a` (adjetivo), `r` (adverbio), `s` (preposición), `p` (pronombre), `c` (conjunción), `i` (interjección), `z` (numeral), `w` (fecha/moneda) y `f` (puntuación).

¿Deseas que profundice en la especificación de las etiquetas de **funciones sintácticas** (ej: `arg0-agt`, `creg`, `cd`) asociadas a estos nodos?
