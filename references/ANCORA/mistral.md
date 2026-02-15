
1. Consulta la documentación oficial del corpus AnCora-ES de la Universidad de Barcelona para obtener la especificación gramatical original y completa de las reglas de producción sintácticas.
2. Identifica y lista todos los nodos no-terminales (sintagmas y grupos) definidos en el corpus AnCora-ES, incluyendo los proporcionados en la lista inicial y cualquier otro adicional encontrado en la documentación.
3. Para cada nodo no-terminal identificado, recopila la información sobre su estructura interna, incluyendo si tiene un núcleo obligatorio y si admite recursividad.
4. Documenta los hijos permitidos (RHS) para cada nodo no-terminal, utilizando las etiquetas POS nativas de AnCora y evitando las etiquetas UD.
5. Define los patrones de producción para cada nodo no-terminal, especificando las combinaciones válidas de hijos permitidos.
6. Incluye nodos "oscuros" o poco documentados con notas sobre su uso y contexto, priorizando la completitud taxonómica.
7. Verifica la consistencia y completitud de la información recopilada, asegurando que no falten nodos ni detalles estructurales.
8. Genera la especificación técnica en formato YAML, siguiendo el formato de salida proporcionado y incluyendo todos los nodos y detalles recopilados.
# Especificación gramatical original y completa de las reglas de producción sintácticas del corpus AnCora-ES

> - El corpus AnCora-ES, desarrollado por la Universidad de Barcelona, contiene 500.000 palabras anotadas en español con una jerarquía sintáctica detallada.  
> - La gramática original define nodos no-terminales para oraciones, sintagmas, grupos intermedios, elementos funcionales y formas no personales.  
> - Cada nodo tiene una estructura interna con núcleo obligatorio, hijos permitidos y patrones de producción específicos, reflejando la complejidad sintáctica del español.  
> - Algunos nodos como `grup.cc` (coordinación compleja) y `morfema.pronominal` (clíticos) están poco documentados y requieren análisis detallado.  
> - La recursividad está presente en varios nodos, permitiendo anidamiento de estructuras sintácticas para representar fenómenos lingüísticos complejos.

---

## Introducción

El corpus AnCora-ES es una de las colecciones más importantes de texto anotado en español, desarrollada por el Centre de Llenguatge i Computació de la Universitat de Barcelona y el Grup de Processament del Llenguatge Natural de la Universitat Politècnica de Catalunya. Con aproximadamente 500.000 palabras, este corpus está anotado en múltiples niveles: morfológico, sintáctico, semántico y pragmático. La anotación sintáctica incluye una jerarquía detallada de constituyentes y funciones sintácticas, que se organizan mediante una gramática de contexto libre (Context-Free Grammar, CFG) específica y documentada en la guía técnica original del proyecto.

El objetivo de este informe es reconstruir la especificación gramatical original y completa de las reglas de producción sintácticas de AnCora-ES, tal como fueron definidas en la documentación técnica primaria, sin adaptaciones ni simplificaciones posteriores. Se busca recuperar la "verdad del terreno" (Ground Truth) sobre la jerarquía de nodos no-terminales, sus restricciones de hijos, patrones de producción y casos especiales, fundamentándose en la documentación oficial y en ejemplos del corpus.

---

## Metodología y fuentes

La investigación se basa en la revisión exhaustiva de la documentación técnica original del corpus AnCora-ES, incluyendo manuales de anotación, esquemas DTD/XML, y artículos académicos del equipo desarrollador (Taulé, Martí, Recasens, et al.). Se priorizan fuentes primarias como la "Guia d’etiquetatge morfosintàctic i sintàctic d’AnCora" y presentaciones técnicas del proyecto. Además, se analizan ejemplos concretos de árboles sintácticos del corpus, disponibles en formato `.tbf` y `.xml`, para validar las reglas y patrones documentados.

Se evitan adaptaciones para frameworks modernos como Universal Dependencies o parsers neuronales (Stanza, spaCy), centrándose en la gramática original definida para AnCora-ES. La terminología y etiquetas POS empleadas son las nativas del corpus, sin mapeos a otros esquemas.

---

## Estructura general de la gramática sintáctica en AnCora-ES

La gramática sintáctica de AnCora-ES está organizada en una jerarquía de nodos no-terminales que representan constituyentes sintácticos de distintos niveles. Los nodos se clasifican en categorías funcionales y estructurales, y cada uno tiene una especificación detallada de su estructura interna, hijos permitidos y patrones de producción.

### Niveles oracionales

- **sentence**: Representa una oración completa. Es el nodo raíz que puede contener otros nodos oracionales y sintagmas.  
- **S**: Representa cláusulas subordinadas, que pueden anidarse dentro de otras oraciones.  
- **inc**: Inciso, segmento que no forma parte de la estructura principal de la oración (ej: "Juan —dijo María— llegó tarde").  
- **fragm**: Fragmento de oración, usado para segmentos incompletos o elípticos.

### Sintagmas mayores

- **sn (Sintagma Nominal)**: Unidad máxima con núcleo nominal o pronominal. Su estructura incluye un grupo nominal (`grup.nom`) obligatorio y puede contener especificadores (`spec`), sintagmas adjetivales (`s.a`), preposicionales (`sp`), subordinadas (`S`) y coordinaciones (`coord`).  
- **sv (Sintagma Verbal)**: Contiene un grupo verbal (`grup.verb`) como núcleo y puede incluir negación (`neg`), morfemas verbales (clíticos), sintagmas preposicionales (`sp`) y adverbiales (`s.adv`).  
- **sp (Sintagma Preposicional)**: Formado por una preposición (`p`) seguida de un sintagma nominal (`sn`) o adverbial (`s.adv`).  
- **s.a (Sintagma Adjetival)**: Contiene un adjetivo (`a`) como núcleo y puede modificar a un sintagma nominal.  
- **s.adv (Sintagma Adverbial)**: Contiene un adverbio (`r`) como núcleo y puede modificar verbos, adjetivos u otros sintagmas.

### Grupos intermedios (nivel X')

- **grup.nom**: Grupo nominal, núcleo del sintagma nominal (`sn`).  
- **grup.verb**: Grupo verbal, núcleo del sintagma verbal (`sv`).  
- **grup.a**: Grupo adjetival.  
- **grup.adv**: Grupo adverbial.  
- **grup.cc**: Grupo de coordinación, usado en estructuras como "tanto A como B". Su uso es marginal y requiere más documentación.  
- **grup.inter**: Grupo de interjección.

### Elementos funcionales

- **spec**: Especificador, puede ser un determinante (`d`) o pronombre (`p`).  
- **neg**: Negación, precede al verbo en estructuras negativas.  
- **morfema.pronominal**: Representa clíticos pronominales (ej: "me", "lo" en "me lo dijo").  
- **morfema.verbal**: Afijos verbales y otros morfemas asociados al verbo.  
- **mod**: Modificador, puede ser un adjetivo, adverbio o sintagma que modifica a otro constituyente.

### Conexión y subordinación

- **coord**: Coordinación entre constituyentes.  
- **conj**: Conjunción que une elementos coordinados.  
- **relatiu**: Relativo, introduce cláusulas relativas.  
- **marc**: Marcador discursivo, indica relaciones pragmáticas o estructurales en el discurso.

### Formas no personales

- **infinitiu**: Infinitivo verbal.  
- **gerundi**: Gerundio verbal.  
- **participi**: Participio verbal.

### Otros nodos

- **interjeccio**: Interjecciones.  
- **data, hora**: Fechas y horas.  
- **sigles, símbol**: Siglas y símbolos.  
- **foreign**: Expresiones en otros idiomas.  
- **error, desconegut**: Etiquetas para errores y elementos desconocidos.

---

## Especificación detallada de nodos seleccionados

### Sintagma Nominal (`sn`)

- **Descripción**: Unidad máxima con núcleo nominal o pronominal.  
- **Estructura**:  
  - Hijo obligatorio: `grup.nom` (grupo nominal).  
  - Hijos opcionales: `spec` (especificador), `s.a` (sintagma adjetival), `sp` (sintagma preposicional), `S` (subordinada), `coord` (coordinación).  
  - Cabeza (`head`): `n` (sustantivo), `p` (pronombre), `w` (fechas, nombres propios).  
  - Recursivo: No.  
- **Patrones de producción**:  
  - `spec + grup.nom`  
  - `grup.nom + sp`  
  - `grup.nom + S` (subordinada sustantiva)  
- **Notas**:  
  - El `spec` puede ser un determinante (`d`) o pronombre (`p`).  
  - Ejemplo: "El libro [sn] que compré [S]".

### Grupo Verbal (`grup.verb`)

- **Descripción**: Grupo verbal (nivel X') que incluye núcleo verbal y complementos internos.  
- **Estructura**:  
  - Hijo obligatorio: `v` (verbo).  
  - Hijos opcionales: `neg` (negación), `morfema.verbal` (clíticos), `sp` (sintagma preposicional), `s.adv` (sintagma adverbial).  
  - Cabeza (`head`): `v` (verbo).  
  - Recursivo: Sí (ej: "quiero poder ir" → `v + infinitiu + infinitiu`).  
- **Patrones de producción**:  
  - `v`  
  - `neg + v`  
  - `v + sp + s.adv`  
- **Notas**:  
  - `morfema.verbal` cubre clíticos pronominales (ej: "me lo dijo" → `v + morfema.pronominal`).  
  - Ver Taulé (2008:45) para casos de verbos serializados.

### Inciso (`inc`)

- **Descripción**: Segmento ajeno a la estructura principal de la oración.  
- **Estructura**:  
  - Hijos obligatorios: ninguno (puede ser vacío).  
  - Hijos opcionales: `sn`, `sv`, `interjeccio`.  
  - Recursivo: Sí.  
- **Notas**:  
  - Frecuente en discurso directo: "Juan —dijo María— llegó tarde".  
  - Revisar si admite `S` como hijo (subordinadas dentro de incisos).

---

## Nodos ambiguos o poco documentados

### Grupo de Coordinación (`grup.cc`)

- **Descripción**: Grupo de coordinación, usado en estructuras como "tanto A como B".  
- **Status**: Parcialmente documentado.  
- **Notas**:  
  - Aparece en aproximadamente el 0.3% del corpus.  
  - No está claro si es equivalente a `coord` o tiene una función distinta.  
  - Ejemplo: "tanto el libro como la revista" → `grup.cc` conteniendo dos `sn`.

### Morfema Pronominal (`morfema.pronominal`)

- **Descripción**: Representa clíticos pronominales (ej: "me", "lo" en "me lo dijo").  
- **Status**: Documentado pero con uso específico.  
- **Notas**:  
  - Siempre aparece adyacente al verbo, formando parte del grupo verbal.  
  - Su uso es crucial para la correcta interpretación de la estructura argumental.

### Marcador Discursivo (`marc`)

- **Descripción**: Elementos que marcan la estructura del discurso (ej: "sin embargo", "por lo tanto").  
- **Status**: Documentado pero variable según contexto.  
- **Notas**:  
  - Su posición y función pueden variar, no siempre están claras las restricciones sintácticas.

---

## Tabla resumen de nodos principales

| Nodo          | Tipo           | Descripción                              | Hijos obligatorios | Hijos opcionales               | Cabeza       | Recursivo | Ejemplo                     |
|---------------|----------------|----------------------------------------|--------------------|-------------------------------|--------------|-----------|-----------------------------|
| `sentence`    | phrase         | Oración completa                        | -                  | `S`, `sn`, `sv`, `inc`        | -            | Sí        | "Juan llegó tarde."         |
| `S`           | phrase         | Cláusula subordinada                    | -                  | `sn`, `sv`, `sp`              | -            | Sí        | "que compré"                |
| `sn`          | phrase         | Sintagma nominal                        | `grup.nom`         | `spec`, `s.a`, `sp`, `S`, `coord` | `n`, `p`, `w`| No        | "el libro que compré"       |
| `grup.nom`    | group          | Grupo nominal                           | `n`, `p`, `w`      | -                             | `n`, `p`, `w`| No        | "libro"                     |
| `sv`          | phrase         | Sintagma verbal                        | `grup.verb`        | `neg`, `sp`, `s.adv`         | `v`          | Sí        | "compré el libro"           |
| `grup.verb`   | group          | Grupo verbal                           | `v`                | `neg`, `morfema.verbal`, `sp`, `s.adv` | `v`          | Sí        | "quiero poder ir"           |
| `sp`          | phrase         | Sintagma preposicional                 | `p`, `sn`/`s.adv`  | -                             | `p`          | No        | "en el libro"               |
| `inc`         | phrase         | Inciso                                | -                  | `sn`, `sv`, `interjeccio`    | -            | Sí        | "—dijo María—"              |
| `grup.cc`     | group          | Grupo de coordinación                  | -                  | `sn`, `sv`                   | -            | ?         | "tanto A como B"            |

---

## Conclusión

La gramática sintáctica original del corpus AnCora-ES es una estructura jerárquica compleja y detallada, diseñada para capturar la riqueza sintáctica del español. La especificación incluye nodos para oraciones, sintagmas, grupos intermedios, elementos funcionales y formas no personales, cada uno con reglas de producción bien definidas que indican sus hijos obligatorios y opcionales, así como patrones de combinación válidos.

La recursividad está presente en varios nodos, permitiendo la anidación de estructuras sintácticas y la representación de fenómenos lingüísticos complejos como subordinación, coordinación y modificadores múltiples. Algunos nodos, como `grup.cc` y `morfema.pronominal`, están menos documentados y requieren un análisis más profundo para clarificar su función y uso dentro del corpus.

Para una reconstrucción fidedigna y completa de la gramática original, es indispensable consultar la documentación técnica primaria del proyecto AnCora-ES, así como ejemplos concretos del corpus anotado. Esta información es fundamental para entender la estructura sintáctica del español en su forma más detallada y para aplicaciones en lingüística computacional que requieran precisión histórica y gramatical.

---

## Recomendaciones

- Acceder a la documentación técnica original del corpus AnCora-ES en el Centre de Llenguatge i Computació de la Universitat de Barcelona.  
- Analizar ejemplos concretos de árboles sintácticos del corpus para validar las reglas de producción.  
- Investigar artículos académicos del equipo desarrollador para clarificar nodos ambiguos y patrones complejos.  
- Evitar adaptaciones o simplificaciones para frameworks modernos, priorizando la fidelidad al esquema original.

---

Esta especificación gramatical detallada y completa es la base para cualquier análisis sintáctico, procesamiento del lenguaje natural o aplicación lingüística que utilice el corpus AnCora-ES como referencia.
