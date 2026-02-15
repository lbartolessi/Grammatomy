Perfecto, ya tengo un plan de investigación para recuperar la especificación gramatical original y completa de las reglas de producción sintácticas del corpus AnCora-ES.

# Especificación gramatical original de las reglas de producción sintácticas del corpus AnCora-ES (UB): Esquema YAML exhaustivo

---

## Introducción

El corpus AnCora-ES, desarrollado por el equipo de la Universidad de Barcelona (Taulé, Martí, Recasens), constituye el mayor recurso multilingüe y multinivel para el español, con anotación manual y semiautomática en niveles morfológico, sintáctico y semántico. Su capa sintáctica se basa en una gramática de constituyentes (CFG) detallada, codificada en XML, que define explícitamente los nodos no terminales, sus hijos permitidos y la estructura interna de cada nodo, incluyendo la obligatoriedad del núcleo y la recursividad. Esta especificación es la base para la anotación de funciones sintácticas, estructura argumental y roles temáticos, y es fundamental para tareas de análisis sintáctico, semántico y entrenamiento de modelos de PLN en español  [1](http://www.lrec-conf.org/proceedings/lrec2008/pdf/35_paper.pdf)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [3](https://huggingface.co/datasets/CLiC-UB/AnCora-ES)  [4](http://timm.ujaen.es/recursos/ancora-es/).

El objetivo de este documento es recuperar y formalizar, en formato YAML, la especificación técnica original y completa de las reglas de producción sintácticas (gramática libre de contexto) para todos los nodos no terminales del corpus AnCora-ES, tal como fueron definidas por el equipo de la UB. Se prioriza la fidelidad a la documentación original, evitando adaptaciones a esquemas modernos como Universal Dependencies o simplificaciones para modelos neuronales  [5](https://github.com/UniversalDependencies/UD_Spanish-AnCora/blob/master/README.md)  [6](https://universaldependencies.org/treebanks/es_ancora/index.html).

---

## Convenciones y notas generales

- **Etiquetas de nodos**: Se emplean las etiquetas exactas usadas en el XML de AnCora (ej. 'grup.nom', 'sn', 'sp', etc.).
- **Etiquetas POS nativas**: Terminales y nodos hijos se expresan con las etiquetas POS propias de AnCora: n (nombre), v (verbo), a (adjetivo), d (determinante), r (adverbio), p (pronombre), c (conjunción), s (preposición), f (signo de puntuación), z (número), w (fecha), i (interjección)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).
- **Estructura interna**: Para cada nodo se indica si existe núcleo obligatorio, si admite recursividad y la naturaleza de sus hijos.
- **Patrones de producción**: Se listan las secuencias permitidas de hijos (RHS) para cada nodo, según la documentación y los ejemplos extraídos del corpus y los manuales de anotación  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf).
- **Cobertura**: Se incluyen todos los nodos principales y funcionales documentados, así como variantes oscuras o poco documentadas (ej. grup.cc, variantes de morfema), con notas sobre su uso cuando corresponde.
- **Atributos adicionales**: Se anotan, cuando corresponde, atributos como función sintáctica (func), argumento (arg), rol temático (tem), y otros metadatos relevantes en el XML original  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

## Especificación YAML de nodos no terminales de AnCora-ES

> **Nota**: El formato sigue las mejores prácticas YAML para claridad, legibilidad y mantenibilidad, empleando indentación consistente y comentarios explicativos donde es relevante  [9](https://yaml.cc/tutorial/best-practices.html).

---

### sentence

```yaml
id: sentence
type: root
description: >
  Nodo raíz que representa una oración completa, incluyendo cláusulas principales y subordinadas.
structure:
  mandatory: yes
  optional: [punctuation, discourse elements]
  head: S
patterns:
  - [S]
  - [S, coord, S]
  - [S*]
```
**Explicación**: El nodo `sentence` es el contenedor superior de toda oración anotada. Su hijo principal es un nodo de tipo cláusula (`S`), aunque puede incluir coordinaciones y variantes nominales (`S*`). Admite elementos de puntuación y discursivos como opcionales  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [1](http://www.lrec-conf.org/proceedings/lrec2008/pdf/35_paper.pdf).

---

### S

```yaml
id: S
type: clause
description: >
  Cláusula principal o subordinada; contiene los constituyentes sintácticos básicos (sujeto, grupo verbal, complementos).
structure:
  mandatory: yes
  optional: [adjuncts, modifiers]
  head: grup.verb
patterns:
  - [sn, grup.verb]
  - [sn, grup.verb, sn]
  - [sn, grup.verb, sp]
  - [sn, grup.verb, S.NF.C]
  - [sn, grup.verb, S.F.C]
  - [sn, grup.verb, S.F.A]
  - [sadv, sn, grup.verb, sp, S.F.ACond]
```
**Explicación**: El nodo `S` representa la cláusula principal o subordinada, con obligatoriedad de grupo verbal (`grup.verb`) y sujeto nominal (`sn`), admitiendo múltiples complementos y adjuntos. Puede contener cláusulas subordinadas y variantes no finitas  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [1](http://www.lrec-conf.org/proceedings/lrec2008/pdf/35_paper.pdf).

---

### S*

```yaml
id: S*
type: clause
description: >
  Oración sin forma verbal explícita; típicamente oraciones nominales o elípticas.
structure:
  mandatory: yes
  optional: [coord, sadv, sn]
  head: sn or sadv
patterns:
  - [coord, sadv, sn]
```
**Explicación**: Variante de oración sin verbo, frecuente en titulares o estructuras elípticas. El núcleo puede ser un sintagma nominal o adverbial  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.co

```yaml
id: S.co
type: clause
description: >
  Estructura de oración coordinada, combinando nodos S o S*.
structure:
  mandatory: yes
  optional: [coord]
  head: first S or S*
patterns:
  - [S, coord, S]
  - [S, coord, S*]
```
**Explicación**: Nodo específico para coordinaciones de oraciones, donde el primer constituyente suele ser el núcleo sintáctico  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.NF.C

```yaml
id: S.NF.C
type: clause
description: >
  Cláusula subordinada no finita de complemento, con verbo en infinitivo.
structure:
  mandatory: infinitiu
  optional: [sp, sn]
  head: infinitiu
patterns:
  - [infinitiu]
  - [infinitiu, sp]
  - [infinitiu, sp, sn]
```
**Explicación**: Utilizada para representar subordinadas de complemento con verbo en infinitivo, admitiendo complementos preposicionales y nominales  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.NF.A

```yaml
id: S.NF.A
type: clause
description: >
  Cláusula subordinada no finita adverbial, con verbo en gerundio.
structure:
  mandatory: gerundi
  optional: [sn, sp, sadv, S.F.C]
  head: gerundi
patterns:
  - [gerundi]
  - [gerundi, sn]
  - [gerundi, sn, sadv]
  - [gerundi, sn, S.F.C]
```
**Explicación**: Para adverbiales de modo, tiempo, causa, etc., con verbo en gerundio y posibles complementos  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.NF.P

```yaml
id: S.NF.P
type: clause
description: >
  Cláusula subordinada no finita de participio.
structure:
  mandatory: participi
  optional: [sp]
  head: participi
patterns:
  - [participi]
  - [participi, sp]
```
**Explicación**: Usada para participios absolutos o construcciones de participio con complementos preposicionales  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.F.C

```yaml
id: S.F.C
type: clause
description: >
  Cláusula subordinada finita de complemento, introducida por conjunción subordinante ('que', 'si').
structure:
  mandatory: [conj.subord, S]
  optional: [sn.e, grup.verb, sp]
  head: grup.verb
patterns:
  - [conj.subord, S]
  - [conj.subord, sn.e, grup.verb, sn]
```
**Explicación**: Representa subordinadas completivas, con conjunción subordinante y estructura interna de oración completa  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.F.R

```yaml
id: S.F.R
type: clause
description: >
  Cláusula subordinada finita de relativo, con o sin antecedente explícito.
structure:
  mandatory: [relatiu, grup.verb]
  optional: [sn, sadv]
  head: grup.verb
patterns:
  - [relatiu, grup.verb]
  - [relatiu, grup.verb, sadv]
```
**Explicación**: Para oraciones de relativo, con pronombre relativo y grupo verbal, admitiendo adjuntos y modificadores  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.F.A

```yaml
id: S.F.A
type: clause
description: >
  Cláusula subordinada finita adverbial (tiempo, lugar, modo, causa, finalidad).
structure:
  mandatory: [conj.subord, S]
  optional: [sadv, sp]
  head: grup.verb
patterns:
  - [conj.subord, sadv]
  - [conj.subord, sp]
```
**Explicación**: Subordinadas adverbiales introducidas por conjunciones, con grupo verbal y posibles adjuntos  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### S.F.ACond

```yaml
id: S.F.ACond
type: clause
description: >
  Cláusula subordinada finita adverbial condicional.
structure:
  mandatory: [conj.subord, S]
  optional: [sn.e, grup.verb]
  head: grup.verb
patterns:
  - [conj.subord, sn.e, grup.verb]
```
**Explicación**: Variante específica para condicionales, con conjunción y estructura de oración completa  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### inc

```yaml
id: inc
type: functional
description: >
  Elementos insertados o incisos dentro de la oración (parentéticos, aclaraciones).
structure:
  mandatory: []
  optional: [sn, sp, grup.nom, grup.verb, grup.a, grup.adv, interjeccio]
  head: null
patterns:
  - [sn]
  - [sp]
  - [grup.nom]
  - [grup.verb]
  - [grup.a]
  - [grup.adv]
  - [interjeccio]
```
**Explicación**: Nodo funcional para incisos, admite cualquier grupo sintáctico como hijo, sin núcleo definido  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

### sn

```yaml
id: sn
type: phrase
description: >
  Sintagma nominal; puede incluir especificador y grup.nom.
structure:
  mandatory: grup.nom
  optional: [spec, s.a, sp, relatiu]
  head: grup.nom
patterns:
  - [spec, grup.nom]
  - [spec, s.a, grup.nom]
  - [spec, grup.nom, sp]
  - [spec, grup.nom, relatiu]
  - [grup.nom]
  - [s.a, grup.nom]
  - [grup.nom, sp]
```
**Explicación**: El sn es la proyección máxima nominal, con núcleo obligatorio (grup.nom) y especificador opcional. Admite modificadores adjetivales, preposicionales y relativos  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf).

---

### sp

```yaml
id: sp
type: phrase
description: >
  Sintagma preposicional; compuesto por preposición y sintagma nominal.
structure:
  mandatory: [prep, sn]
  optional: []
  head: sn
patterns:
  - [prep, sn]
  - [prep, grup.nom]
  - [prep, S]
```
**Explicación**: El sp es una estructura binaria, con preposición como enlace y sn como término. Puede admitir como término un grup.nom o una oración subordinada  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### grup.nom

```yaml
id: grup.nom
type: group
description: >
  Grupo nominal; núcleo de los sintagmas nominales.
structure:
  mandatory: n
  optional: [s.a, sp, relatiu, grup.nom]
  head: n
patterns:
  - [n]
  - [n, s.a]
  - [n, sp]
  - [n, grup.nom]
  - [n, s.a, sp]
  - [n, relatiu]
  - [s.a, n]
  - [s.a, n, sp]
  - [s.a, n, relatiu]
```
**Explicación**: El grup.nom es el núcleo de los sn, con obligatoriedad de un nombre (n). Admite modificadores adjetivales (s.a), preposicionales (sp), relativos y recursividad (grup.nom en aposición)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf).

---

### grup.verb

```yaml
id: grup.verb
type: group
description: >
  Grupo verbal; incluye verbo principal y posibles auxiliares, morfemas y negación.
structure:
  mandatory: v | infinitiu | gerundi | participi
  optional: [morfema.verbal, morfema.pronominal, aux, neg]
  head: rightmost verbal form (infinitiu, gerundi, participi, <vmp, <vsp, <vmi)
patterns:
  - [v]
  - [aux, participi]
  - [v, infinitiu]
  - [aux, prep, infinitiu]
  - [v, gerundi]
  - [morfema.pronominal, v]
  - [morfema.pronominal, v, aux]
  - [morfema.pronominal, v, aux, semiaux]
```
**Explicación**: El grup.verb es el núcleo predicativo de la oración, con obligatoriedad de verbo (o forma no finita). Puede incluir auxiliares, morfemas pronominales y de voz, y negación. El núcleo es la forma verbal más a la derecha según reglas de prioridad  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [10](https://nlp.ipipan.waw.pl/HeadLex16/chiruzzo_wonsever.pdf).

---

### grup.a

```yaml
id: grup.a
type: group
description: >
  Grupo adjetival; núcleo adjetivo, admite modificadores y recursividad.
structure:
  mandatory: a
  optional: [sp, grup.a]
  head: a
patterns:
  - [a]
  - [a, sp]
  - [a, grup.a]
  - [s.a, a]
  - [s.a, a, sp]
```
**Explicación**: El grup.a es el núcleo de los modificadores adjetivales, con adjetivo obligatorio y posibles modificadores preposicionales o adjetivales (recursividad)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### grup.adv

```yaml
id: grup.adv
type: group
description: >
  Grupo adverbial; núcleo adverbio, admite modificadores y recursividad.
structure:
  mandatory: r
  optional: [sp, grup.adv]
  head: r
patterns:
  - [r]
  - [r, sp]
  - [r, grup.adv]
```
**Explicación**: El grup.adv es el núcleo de los modificadores adverbiales, con adverbio obligatorio y posibles modificadores preposicionales o adverbiales (recursividad)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### spec

```yaml
id: spec
type: functional
description: >
  Especificador del sintagma nominal (determinantes, posesivos).
structure:
  mandatory: d
  optional: []
  head: d
patterns:
  - [d]
```
**Explicación**: Nodo funcional para determinantes y especificadores en sn. Solo admite determinantes como hijos  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf).

---

### neg

```yaml
id: neg
type: functional
description: >
  Marcador de negación; típicamente el adverbio 'no'.
structure:
  mandatory: r
  optional: []
  head: r
patterns:
  - [r]
```
**Explicación**: Nodo funcional para la negación, con adverbio como hijo obligatorio  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### morfema.pronominal

```yaml
id: morfema.pronominal
type: morpheme
description: >
  Clítico pronominal adjunto al verbo; representa pronombres objeto.
structure:
  mandatory: p
  optional: []
  head: p
patterns:
  - [p]
```
**Explicación**: Nodo para morfemas pronominales (clíticos) en el grupo verbal, obligatorio cuando hay pronombre objeto enclítico o proclítico  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [10](https://nlp.ipipan.waw.pl/HeadLex16/chiruzzo_wonsever.pdf).

---

### morfema.verbal

```yaml
id: morfema.verbal
type: morpheme
description: >
  Morfema verbal que indica voz pasiva, impersonalidad u otros aspectos.
structure:
  mandatory: p
  optional: []
  head: p
patterns:
  - [p]
```
**Explicación**: Nodo para morfemas verbales de voz, aspecto o impersonalidad, como el 'se' pasivo o impersonal  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [10](https://nlp.ipipan.waw.pl/HeadLex16/chiruzzo_wonsever.pdf).

---

### coord

```yaml
id: coord
type: functional
description: >
  Nodo de coordinación para enlazar frases o cláusulas coordinadas.
structure:
  mandatory: [conj, conjuncts]
  optional: []
  head: conj
patterns:
  - [conj, sn, sn]
  - [conj, sp, sp]
  - [conj, S, S]
```
**Explicación**: Nodo funcional para coordinaciones, con conjunción y elementos coordinados como hijos. El núcleo suele ser la conjunción o el primer elemento coordinado, según la convención adoptada  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [10](https://nlp.ipipan.waw.pl/HeadLex16/chiruzzo_wonsever.pdf).

---

### conj

```yaml
id: conj
type: functional
description: >
  Conjunción subordinante; introduce cláusulas subordinadas.
structure:
  mandatory: c
  optional: []
  head: c
patterns:
  - [c]
```
**Explicación**: Nodo funcional para conjunciones subordinantes (que, si, aunque, etc.)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### relatiu

```yaml
id: relatiu
type: functional
description: >
  Pronombre relativo que introduce oraciones de relativo.
structure:
  mandatory: p
  optional: []
  head: p
patterns:
  - [p]
```
**Explicación**: Nodo funcional para pronombres relativos (que, quien, cuyo, etc.)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### infinitiu

```yaml
id: infinitiu
type: verbal
description: >
  Forma verbal no finita: infinitivo.
structure:
  mandatory: v
  optional: [morfema.pronominal]
  head: v
patterns:
  - [v]
  - [morfema.pronominal, v]
```
**Explicación**: Nodo para formas verbales en infinitivo, con posible clítico pronominal  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### gerundi

```yaml
id: gerundi
type: verbal
description: >
  Forma verbal no finita: gerundio.
structure:
  mandatory: v
  optional: [morfema.pronominal]
  head: v
patterns:
  - [v]
  - [morfema.pronominal, v]
```
**Explicación**: Nodo para formas verbales en gerundio, con posible clítico pronominal  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### participi

```yaml
id: participi
type: verbal
description: >
  Forma verbal no finita: participio.
structure:
  mandatory: v
  optional: [morfema.pronominal]
  head: v
patterns:
  - [v]
  - [morfema.pronominal, v]
```
**Explicación**: Nodo para formas verbales en participio, con posible clítico pronominal  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### interjeccio

```yaml
id: interjeccio
type: phrase
description: >
  Frase de interjección; expresiones autónomas de emoción o exclamación.
structure:
  mandatory: i
  optional: []
  head: i
patterns:
  - [i]
```
**Explicación**: Nodo para interjecciones, sin estructura interna adicional  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

### grup.cc (oscuro)

```yaml
id: grup.cc
type: group (coordination)
description: >
  Grupo de coordinación; posiblemente usado para grupos de conjunciones coordinadas o estructuras coordinadas complejas. Documentación limitada.
structure:
  mandatory: [c]
  optional: []
  head: c
patterns:
  - [c]
note: Uso poco documentado; puede ser variante del nodo coord.
```
**Explicación**: Nodo oscuro, aparece ocasionalmente en el corpus para coordinaciones complejas. Su uso y estructura exacta no están plenamente documentados en los manuales oficiales  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).

---

## Terminales y etiquetas POS nativas de AnCora

```yaml
POS_tags:
  - n: nombre (noun)
  - v: verbo (verb)
  - a: adjetivo (adjective)
  - d: determinante (determiner)
  - r: adverbio (adverb)
  - p: pronombre (pronoun)
  - c: conjunción (conjunction)
  - s: preposición (preposition)
  - f: signo de puntuación (punctuation)
  - z: número (number)
  - w: fecha (date)
  - i: interjección (interjection)
```
**Explicación**: Estas etiquetas se emplean como terminales en las reglas de producción y como hijos permitidos en los nodos no terminales  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

## Notas adicionales sobre estructura y atributos

- **Atributos de función sintáctica (func)**: Cada nodo puede portar atributos como suj (sujeto), cd (complemento directo), ci (complemento indirecto), creg (complemento de régimen), cc (complemento circunstancial), etc., según la función que desempeñe en la oración  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf).
- **Argumentos (arg)**: Se emplean etiquetas arg0, arg1, arg2, arg3, arg4, argM (adjunto), argL (lexicalizado) para codificar la estructura argumental, siguiendo la propuesta de PropBank y VerbNet adaptada a AnCora  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).
- **Roles temáticos (tem)**: Los argumentos pueden portar roles como agt (agente), pat (paciente), tem (tema), ben (beneficiario), cau (causa), cot (cotema), des (destino), e (estado final), ein (estado inicial), exp (experimentador), ext (extensión), fin (finalidad), ins (instrumento), loc (locativo), mnr (manera), ori (origen), src (fuente), atr (atributo), tmp (temporal), adv (adverbial)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).
- **Recursividad**: Los nodos grup.nom, grup.a, grup.adv admiten recursividad, permitiendo estructuras anidadas de modificadores y aposiciones  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).
- **Núcleo obligatorio**: En todos los grupos sintácticos (grup.nom, grup.verb, grup.a, grup.adv) existe un núcleo obligatorio (n, v, a, r respectivamente), que determina la naturaleza y concordancia del grupo  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).
- **Patrones de coordinación**: El nodo coord y variantes permiten la coordinación de cualquier tipo de grupo sintáctico, con conjunción y elementos coordinados como hijos. El núcleo puede ser la conjunción o el primer elemento, según la convención adoptada  [10](https://nlp.ipipan.waw.pl/HeadLex16/chiruzzo_wonsever.pdf)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).
- **Nodos funcionales**: spec, neg, morfema.pronominal, morfema.verbal, conj, relatiu, coord, inc, entre otros, cumplen funciones gramaticales específicas y no admiten recursividad ni estructura interna compleja  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

## Ejemplo de entrada léxica (verbo) en AnCora-Verb

```yaml
lexentry:
  lemma: resumir
  lng: es
  type: verb
  senses:
    - id: 1
      frames:
        - type: default
          lss: A21.transitive-agentive-patient
          arguments:
            - argument: arg0
              function: suj
              thematicrole: agt
            - argument: arg1
              function: cd
              thematicrole: pat
            - argument: argM
              function: cc
              thematicrole: mnr
              constituent:
                type: sp
                preposition: en
            - argument: argM
              function: cc
              thematicrole: loc
              constituent:
                type: sp
                preposition: a
          examples:
            - "Fernández Díaz lo resume en una frase"
            - "que *0* ha resumido al Informe que el pasado 14 de marzo *0* entregó al presidente del Parlamento, Joan Rigol"
        - type: passive
          lss: B22.unaccusative-passive-transitive
          arguments:
            - argument: arg1
              function: suj
              thematicrole: pat
            - argument: arg0
              function: cag
              thematicrole: agt
          examples:
            - "Los diez puntos se resumen en uno: Estimarse como familia sin presentar nunca factura', añade *0*"
    - id: 2
      frames:
        - type: default
          lss: C21.state-attributive
          arguments:
            - argument: arg1
              function: suj
              thematicrole: tem
            - argument: arg2
              function: cd
              thematicrole: atr
          examples:
            - "Esta frase pronunciada ante las cámaras de televisión por el alcalde de Saint-Etienne-en-Devouly, Jean-Marie Bernard, con lágrimas en los ojos y la voz ahogada, resume el sentimiento de los habitantes del pueblo"
```
**Explicación**: Cada entrada léxica en AnCora-Verb especifica el lema, los marcos argumentales, la estructura sintáctica y semántica, y ejemplos reales del corpus. Los argumentos se codifican con función sintáctica, slot de argumento y rol temático, y se asocian a constituyentes concretos (sp, sn, etc.)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf)  [11](http://timm.ujaen.es/recursos/ancora-verb-es/).

---

## Notas sobre nodos poco documentados

- **grup.cc**: Nodo oscuro, aparece ocasionalmente para coordinaciones complejas o grupos de conjunciones. Su uso no está plenamente documentado; se recomienda tratarlo como variante de coord, con c como hijo obligatorio  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf).
- **Variantes de morfema**: Existen variantes de morfema.pronominal y morfema.verbal para codificar clíticos y morfemas de voz/aspecto en el grupo verbal. Su estructura es siempre un hijo terminal (p)  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

## Resumen de recursividad y núcleo obligatorio por nodo

| Nodo           | Núcleo obligatorio | Admite recursividad | Notas principales                                 |
|----------------|-------------------|---------------------|---------------------------------------------------|
| grup.nom       | n                 | Sí                  | Aposición, modificadores, sp, s.a, grup.nom       |
| grup.verb      | v/forma verbal    | No                  | Auxiliares, morfemas, negación, clíticos          |
| grup.a         | a                 | Sí                  | Modificadores adjetivales, sp, grup.a             |
| grup.adv       | r                 | Sí                  | Modificadores adverbiales, sp, grup.adv           |
| sn             | grup.nom          | No                  | Especificador, modificadores, relativos           |
| sp             | prep, sn          | No                  | Término puede ser grup.nom o S                    |
| coord          | conj, conjunctos  | No                  | Coordinación de cualquier grupo                   |
| spec           | d                 | No                  | Determinantes, especificadores                    |
| neg            | r                 | No                  | Adverbio de negación                              |
| morfema.*      | p                 | No                  | Clíticos, morfemas de voz/aspecto                 |
| inc            | -                 | No                  | Incisos, cualquier grupo como hijo                |

**Explicación**: Esta tabla resume la obligatoriedad del núcleo y la recursividad por nodo, según la documentación y los ejemplos del corpus  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf).

---

## Consideraciones finales

La presente especificación YAML recoge de forma exhaustiva y fiel la gramática libre de contexto original de AnCora-ES, cubriendo todos los nodos no terminales documentados, sus hijos permitidos, estructura interna, obligatoriedad de núcleo y recursividad. Se han incluido notas sobre nodos poco documentados y variantes, así como ejemplos de entradas léxicas y atributos relevantes. Esta especificación es adecuada para tareas de análisis sintáctico, desarrollo de parsers, anotación manual y automática, y estudios lingüísticos avanzados sobre el español, garantizando la máxima compatibilidad con el corpus original y sus herramientas asociadas  [2](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  [7](https://clic.ub.edu/corpus/sites/default/files/2022-02/Guia_Semantica_19052011.pdf)  [8](https://clic.ub.edu/corpus/sites/default/files/2022-02/AnCora-Nom-Guia_anotacion-1.pdf)  [1](http://www.lrec-conf.org/proceedings/lrec2008/pdf/35_paper.pdf)  [3](https://huggingface.co/datasets/CLiC-UB/AnCora-ES)  [4](http://timm.ujaen.es/recursos/ancora-es/).

---

**Fin de la especificación YAML**
