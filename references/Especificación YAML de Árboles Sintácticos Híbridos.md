# **Arquitectura de validación metasintáctica para el editor Grammatomy: Análisis de hibridación y especificación técnica de reglas jerárquicas en modelos SOTA**

La evolución de la lingüística computacional en la última década ha transitado desde sistemas basados puramente en reglas hacia arquitecturas neuronales de alto rendimiento, como Stanza y Benepar, que priorizan la precisión estadística sobre la ortodoxia gramatical académica. En el marco del proyecto Grammatomy, el desarrollo de un editor y validador de árboles sintácticos exige una reconciliación entre las estructuras de constituyentes tradicionales y las representaciones pragmáticas generadas por estos modelos de última generación (SOTA). Las pruebas de estrés realizadas revelan que los modelos no operan en un vacío teórico, sino que heredan y transforman las convenciones de los corpus con los que fueron entrenados, como AnCora para el español, el Penn Treebank (PTB) para el inglés, el Venice Italian Treebank (VIT) para el italiano y CINTIL para el portugués.1

La problemática central radica en que los modelos SOTA a menudo generan estructuras híbridas que mezclan etiquetas de constituyentes con categorías de Universal Dependencies (UD), o adoptan jerarquías planas donde la teoría de la X-Barra dictaría una estructura ramificada.4 Para que el validador de Grammatomy sea efectivo, no debe limitarse a señalar desviaciones de los manuales de la RAE o la gramática de Quirk; debe legalizar estas hibridaciones siempre que mantengan la coherencia interna del modelo de procesamiento. Este informe detalla las reglas metasintácticas necesarias para supervisar estas relaciones jerárquicas, integrando conocimientos empíricos sobre recursividad, estructuras mixtas y etiquetas especializadas.

## **Paradigmas de representación y la brecha pragmática en modelos SOTA**

Los parsers contemporáneos, especialmente aquellos basados en arquitecturas de transición (shift-reduce) o esquemas de atención de transformadores, han demostrado que la representación interna de la sintaxis es más fluida de lo que sugieren los libros de texto.2 Mientras que la lingüística académica se enfoca en la competencia, los modelos SOTA se centran en la actuación y la manejabilidad de los datos. Esto resulta en una "brecha pragmática" donde, por ejemplo, el modelo Stanza para el italiano prescinde totalmente del nivel de frase verbal (VP), posicionando al núcleo verbal directamente bajo el nodo oracional (S).4

Para un arquitecto de software de NLP, esta variabilidad no debe ser tratada como un error, sino como una especificación de diseño del modelo. El validador de Grammatomy debe implementar un motor de reglas que sea sensible al contexto del idioma y al corpus de referencia. La arquitectura propuesta se basa en una especificación YAML que permite definir restricciones de paternidad, cardinalidad y contexto, integrando de forma nativa la hibridación de etiquetas.

### **Comparativa de filosofías de anotación por corpus de referencia**

| Corpus | Idioma | Filosofía Estructural | Nivel de VP | Manejo de MWE |
| :---- | :---- | :---- | :---- | :---- |
| **AnCora** | Español | CFG enriquecida con funciones 8 | Presente como grup.verb 9 | Expansión con guion bajo 9 |
| **PTB II** | Inglés | Jerarquía de constituyentes pura 10 | Presente y jerárquico 11 | Etiquetas funcionales (-TMP, \-ADV) 10 |
| **VIT** | Italiano | X-Barra simplificada y plana 4 | Ausente por defecto en nivel S 7 | Etiquetas especializadas (spd, sa) 4 |
| **CINTIL** | Portugués | Basado en gramática profunda (HPSG) 6 | Profundo y recursivo 7 | Adherencia a X-Barra estándar 3 |

## **El modelo español: Recursividad en AnCora y expansión de MWE**

El análisis del español en Grammatomy se fundamenta en el corpus AnCora, cuya estructura de constituyentes es significativamente más compleja que los modelos escolares. Un hallazgo crítico en las pruebas de estrés es la recursividad del nodo S (cláusula) dentro del grup.nom (grupo nominal).8 En la gramática tradicional, una oración de relativo se consideraría un adjunto al sintagma nominal, pero en AnCora, el grup.nom actúa como un contenedor donde pueden coexistir sustantivos (n), adjetivos (s.a), sintagmas preposicionales (sp) y otras cláusulas S de forma recursiva.9

Esta estructura permite capturar nominalizaciones complejas y subordinadas adjetivas sin necesidad de proyecciones intermedias de X-Barra, lo que simplifica el procesamiento computacional pero complica la validación si se espera una estructura purista. Además, el manejo de las expresiones multi-palabra (MWE) en los modelos SOTA para el español introduce etiquetas como grup.cc (grupo de conjunción coordinante) o grup.prep (grupo preposicional) para agrupar tokens que originalmente estaban unidos por guiones bajos, como *no\_obstante* o *a\_pesar\_de*.9

### **Dinámicas del grupo nominal y clausal en español**

En AnCora, el nodo sn (sintagma nominal) actúa como el padre de un spec (especificador) y un grup.nom. Sin embargo, es en el grup.nom donde se observa la mayor densidad de información. El validador debe permitir que un grup.nom sea padre de otro grup.nom en casos de aposición o coordinación, y que un S sea hijo de un grup.nom en casos de subordinación relativa.8

| Padre | Hijo Permitido | Rol Sintáctico | Restricción de Contexto |
| :---- | :---- | :---- | :---- |
| **sn** | spec | Especificador | Opcional, suele preceder al núcleo 9 |
| **grup.nom** | n / NOUN | Núcleo nominal | Obligatorio, puede ser múltiple en aposiciones 9 |
| **grup.nom** | S | Cláusula subordinada | Relativas o completivas de nombre 8 |
| **S** | grup.verb | Núcleo verbal | Obligatorio en cláusulas finitas 9 |

La expansión de contracciones (ej. *del* a *de el*) y clíticos (ej. *dárselo* a *dar se lo*) también impacta en la jerarquía del árbol. En estos casos, el validador debe asegurar que los nuevos tokens generados se adjunten a los constituyentes correctos (sp para la preposición y sn para el artículo), manteniendo la integridad semántica de la frase original.9

## **Estructuras X-Barra y gramáticas profundas en el portugués**

El portugués, procesado a través del corpus CINTIL, ofrece una perspectiva diferente debido a su origen en la gramática LXGram y su alineación con los principios de la Teoría de la X-Barra y HPSG.3 A diferencia de los modelos planos, CINTIL mantiene una jerarquía más estricta donde los nodos intermediarios (![][image1], ![][image2], ![][image3]) son fundamentales para determinar el alcance de los adjuntos y complementos.13

Un aspecto empírico esencial para Grammatomy es que, en portugués, el núcleo verbal puede estar anidado bajo múltiples niveles de VP dependiendo de la cantidad de verbos auxiliares o modales que precedan al verbo principal.4 Esto contrasta con el modelo italiano, donde los auxiliares se mantienen en el mismo nivel que el verbo tensed.7

### **El esquema X-Barra mixto en CINTIL**

La hibridación en el modelo portugués se manifiesta cuando las etiquetas de X-Barra (como N-BAR o V-BAR) conviven con etiquetas de UD (como nsubj o obj). El validador debe ser capaz de procesar estas proyecciones intermedias, asegurando que cada frase (XP) tenga un núcleo (X) y que los adjuntos se unan correctamente a los niveles de "barra".14

| Nivel X-Barra | Componentes | Regla de Paternidad | Implicación de Software |
| :---- | :---- | :---- | :---- |
| **XP (Maximal)** | Spec \+ X' | Puede ser raíz o hijo de otro X' | Punto de entrada para validación de sintagma 14 |
| **X' (Intermediate)** | X \+ Complemento | Siempre hijo de XP o X' | Permite recursividad de adjuntos 15 |
| **X0 (Head)** | Lexema / UPOS | Hijo obligatorio de X' | Núcleo de la proyección 14 |

La conversión de CINTIL a Universal Dependencies ha generado un banco de dependencias (CINTIL-UDep) que mantiene la riqueza de la anotación original pero adaptada a la simplicidad de UD.6 Grammatomy debe permitir que las etiquetas XPOS (específicas de CINTIL) se utilicen para validar la estructura de constituyentes, mientras que las UPOS se utilicen para la validación cruzada de categorías léxicas universales.6

## **La arquitectura plana y etiquetas especializadas del italiano (VIT)**

El Venice Italian Treebank (VIT) representa un caso de estudio único para la arquitectura de Grammatomy debido a su renuncia deliberada al nivel de VP.4 En VIT, la oración (S) se analiza de forma plana: el sujeto, el grupo verbal y los complementos cuelgan directamente del mismo nodo superior.7 Esta decisión, tomada originalmente para facilitar la creación de parsers de habla, ha persistido en las versiones modernas del corpus.4

Además, VIT introduce etiquetas altamente especializadas para tipos específicos de sintagmas preposicionales y adverbiales. Por ejemplo, en lugar de una etiqueta genérica de PP o sp, VIT utiliza spd para frases preposicionales introducidas por *di* y sa para aquellas introducidas por *a*.4

### **Componentes de la oración en VIT**

En lugar de un VP, VIT utiliza nodos específicos para el núcleo verbal: IBAR para verbos en tiempos finitos y IR\_INFL para verbos en futuro, condicional o subjuntivo (denominados verbos "irreales").4

| Nodo | Descripción | Hijos Permitidos | Relación Jerárquica |
| :---- | :---- | :---- | :---- |
| **S** | Oración | NP-SUBJ, IBAR, spd, sa, complementos | Estructura plana, todos al mismo nivel 4 |
| **IBAR** | Grupo Verbal Tensed | vt (verbo transitivo), vi (intransitivo) | Núcleo oracional para oraciones afirmativas 17 |
| **IR\_INFL** | Grupo Verbal Irreal | v (verbo en modo subj/cond) | Usado para marcar modalidad gramatical 16 |
| **spd** | Frase con "di" | partd, sn | Especialización funcional de la preposición 17 |

Esta "flatness" requiere que el validador de Grammatomy sea excepcionalmente flexible con la cardinalidad de los hijos del nodo S. En inglés o español, una sobrepoblación de hijos bajo S podría indicar una falla en la segmentación de frases, pero en italiano es la norma estructural.7

## **El estándar PTB II y las etiquetas funcionales en inglés**

Para el inglés, el validador debe adherirse a las convenciones del Penn Treebank II, que es la base de la mayoría de los parsers de constituyentes modernos, incluido Benepar.2 El PTB II no solo define categorías básicas como NP o VP, sino que utiliza un sistema complejo de "Function Tags" para marcar roles gramaticales y semánticos, como \-ADV (adverbial), \-TMP (temporal), o \-LGS (sujeto lógico).10

Una característica distintiva de los modelos SOTA para inglés es la introducción de la etiqueta NML (Noun Modifier Label) en revisiones recientes del PTB para marcar sintagmas adjetivos basados en nombres dentro de un NP.2 El validador de Grammatomy debe tratar estas etiquetas extendidas como ciudadanos de primera clase en su esquema de validación.

### **Jerarquía y etiquetas especiales en PTB II**

| Etiqueta | Descripción | Restricciones de Paternidad | Notas Empíricas |
| :---- | :---- | :---- | :---- |
| **SBAR** | Cláusula subordinada | Hijo de NP, VP o S | Introducida por un complementizador o palabra-WH 11 |
| **NAC** | Not a Constituent | Principalmente dentro de un NP | Indica el alcance de modificadores pre-nominales 10 |
| **NX** | Núcleo de NP complejo | Hijo de un NP | Corresponde vagamente al nivel N-barra 10 |
| **QP** | Quantifier Phrase | Hijo de NP | Para medidas y cantidades complejas 11 |

El PTB II también impone restricciones negativas interesantes que el validador debe codificar. Por ejemplo, la etiqueta de función \-LOC (locativo) no debe aplicarse nunca a un nodo SBAR, y en casos de aposición con SBAR, no se debe usar la etiqueta \-TMP.10 Estas "prohibiciones de contexto" son vitales para mantener la fidelidad al corpus de entrenamiento del modelo.

## **Integración de UD y Constituyentes: La hibridación legalizada**

El desafío técnico más prominente en Grammatomy es la convivencia de dos paradigmas sintácticos en un solo árbol. Los modelos de Stanza, por ejemplo, realizan una predicción de UPOS (Universal POS tags) antes de generar la estructura de dependencias o constituyentes.18 Esto a menudo resulta en árboles donde las hojas no son etiquetas léxicas del corpus original (como nc en AnCora), sino etiquetas universales como NOUN o PROPN.19

### **Estrategia de validación híbrida**

El arquitecto de software debe definir un "mapeo de transparencia" donde etiquetas de diferentes taxonomías se consideren equivalentes para fines de cumplimiento de reglas jerárquicas. Por ejemplo, una regla que exige un sustantivo como núcleo de un grup.nom debe ser satisfecha tanto por una etiqueta n (AnCora) como por una etiqueta NOUN (UD).5

| Categoría Universal (UD) | Categorías Equivalentes (Constituyentes) | Roles de Dependencia Permitidos |
| :---- | :---- | :---- |
| **NOUN** | n, npro, NN, NNS, n-común | nsubj, obj, obl, nmod 19 |
| **VERB** | v, vt, vi, VB, VBD, VBG | root, xcomp, ccomp 21 |
| **AUX** | aux, IBAR, IR\_INFL, MD | aux, aux:pass 19 |
| **PRON** | p, npro, PRP, PRP$ | nsubj, obj, expl 19 |

Esta hibridación no solo es necesaria para validar la salida de los modelos SOTA, sino que permite al usuario de Grammatomy enriquecer sus árboles con información de dependencias sin romper la estructura de constituyentes subyacente.3

## **Especificación Técnica de Reglas Metasintácticas (YAML)**

La siguiente especificación YAML consolida las reglas para los cuatro idiomas analizados. Este bloque único está diseñado para ser cargado directamente en el motor de validación de Grammatomy, permitiendo una supervisión exhaustiva de la jerarquía del árbol.

YAML

\# Grammatomy Meta-Syntactic Rules Specification  
\# Idiomas: ES, EN, IT, PT  
\# Versión: 2.0.4 (Stress-Tested for Stanza/Benepar)

rules:  
  \# \--- SECCIÓN ESPAÑOL (ANCORA HYBRID) \---  
  \- id: ES\_SN\_VALIDATOR  
    descripcion: Validación de Sintagma Nominal con soporte para MWE y UD.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios: \[grup.nom\]  
      opcionales:  
    restricciones:  
      cardinalidad: { grup.nom: "1..\*" }  
      orden: \[spec, grup.nom\]  
    prohibiciones:

  \- id: ES\_GRUP\_NOM\_RECURSION  
    descripcion: Soporte para recursividad de S y estructuras complejas AnCora.  
    padres\_permitidos: \[sn, grup.nom\]  
    hijos\_permitidos:  
      obligatorios:  
      opcionales:  
    restricciones:  
      recursividad: true \# Legaliza S dentro de grup.nom   
      contexto: "S en grup.nom debe ser subordinada (relativa/completiva)"  
    prohibiciones: \[spec\]

  \- id: ES\_GRUP\_VERB\_HYBRID  
    descripcion: Grupo verbal con soporte para expansión de clíticos y UPOS.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales: \[sn, sp, sadv, neg, morfema.pronominal, morfema.verbal, f\]  
    restricciones:  
      cardinalidad: { v: "1", VERB: "1" }  
      orden: \[neg, aux, v\]  
    prohibiciones: \[grup.nom\]

  \# \--- SECCIÓN INGLÉS (PTB II \+ NML) \---  
  \- id: EN\_NP\_PTB\_STANDARD  
    descripcion: Noun Phrase del Penn Treebank con soporte para NML y NX.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales:  
    restricciones:  
      cardinalidad: { NN: "1..\*", NOUN: "1..\*" }  
    prohibiciones:

  \- id: EN\_VP\_HIERARCHICAL  
    descripcion: Verb Phrase jerárquico para modelos Benepar/Stanza.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales:  
    restricciones:  
      recursividad: true \# Soporte para auxiliares encadenados  
    prohibiciones:

  \- id: EN\_SBAR\_CONSTRAINTS  
    descripcion: Cláusulas subordinadas con restricciones de etiquetas funcionales.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales:  
    restricciones:  
      prohibiciones\_contexto: \# Basado en PTB II   
    prohibiciones: \[VP, grup.verb\]

  \# \--- SECCIÓN ITALIANO (VIT FLAT) \---  
  \- id: IT\_S\_FLAT\_STRUCTURE  
    descripcion: Oración plana de VIT sin nodo VP.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales:  
    restricciones:  
      estructura: "plana"  
      cardinalidad: { IBAR: "0..1", IR\_INFL: "0..1" }  
    prohibiciones: \[VP\]

  \- id: IT\_IBAR\_CORE  
    descripcion: Núcleo verbal tensed de VIT.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales: \[neg, pron, aux, morf\]  
    restricciones:  
      orden: "núcleo debe ser pre-terminal"  
    prohibiciones: \[sn, sp, NP\]

  \- id: IT\_SPD\_SPECIALIZED  
    descripcion: Frase preposicional específica de VIT para "di".  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales:  
    restricciones:  
      contexto: "especialización léxica requerida para preposición 'di'"  
    prohibiciones: \[v, vt\]

  \# \--- SECCIÓN PORTUGUÉS (CINTIL X-BAR) \---  
  \- id: PT\_XBAR\_PROJECTION  
    descripcion: Proyecciones de la X-Barra para CINTIL-UDep.  
    padres\_permitidos: \[NP, VP, PP, AdjP\]  
    hijos\_permitidos:  
      obligatorios:  
      opcionales:  
    restricciones:  
      jerarquia: "binaria"  
      adherencia: "X-Bar Theory"  
    prohibiciones:

  \- id: PT\_VP\_DEEP\_CHAIN  
    descripcion: VP profundo con soporte para múltiples auxiliares.  
    padres\_permitidos:  
    hijos\_permitidos:  
      obligatorios:  
      opcionales: \[VP, NP, PP, AdvP, Clit, f\]  
    restricciones:  
      cardinalidad: { V: "1", VERB: "1" }  
    prohibiciones: \[N, sn\]

\# Mapeo de Transparencia de Etiquetas (Hibridación UD-Constituents)  
label\_transparency:  
  \- id: NOUN\_EQUIV  
    tags:  
  \- id: VERB\_EQUIV  
    tags:  
  \- id: AUX\_EQUIV  
    tags:

## **Análisis de impacto en la arquitectura de software de Grammatomy**

La implementación de estas reglas en un motor de validación requiere un enfoque de "Constraint Satisfaction Problem" (CSP). El validador no solo debe realizar una búsqueda en profundidad (DFS) sobre el árbol para verificar etiquetas individuales, sino que debe evaluar la "salud estructural" de cada nodo basándose en su entorno multilingüe.

### **Mecanismos de validación recomendados**

1. **Validación Sensible al Idioma**: El sistema debe cargar perfiles de reglas dinámicamente. Si un árbol es detectado como IT, el validador debe suspender la regla de "Existencia Obligatoria de VP" que es estándar en EN y PT.7  
2. **Manejo de Recursividad Infinita**: Especialmente para el español (grup.nom) e inglés (VP), el validador debe implementar límites de profundidad o detectores de ciclos para evitar desbordamientos en la validación de estructuras recursivas complejas.8  
3. **Normalización de Pre-terminales**: Antes de aplicar las reglas de YAML, Grammatomy debe normalizar los pre-terminales (tags de POS). Si el parser utiliza UPOS (como NOUN), el sistema debe consultar la tabla de label\_transparency para verificar si cumple los requisitos de un núcleo nominal en el corpus original.5

### **Gestión de nulidades y trazas estructurales**

Un punto avanzado identificado en las investigaciones es el manejo de elementos nulos o vacíos (ej. sujetos elípticos en español o italiano). Mientras que muchos parsers SOTA los omiten, modelos entrenados en VIT o AnCora pueden incluirlos como nodos hoja con etiquetas como 0 o \*.23 La especificación YAML permite estos hijos opcionales para evitar que el validador marque erróneamente una oración como "sin sujeto" cuando el modelo ha detectado correctamente un sujeto nulo.4

## **Conclusiones sobre la normalización de la hibridación sintáctica**

La creación de Grammatomy como una herramienta de referencia para la comunidad de NLP depende de su capacidad para abrazar la naturaleza híbrida y pragmática de los modelos SOTA actuales. La especificación técnica presentada no es simplemente una lista de reglas; es un marco de trabajo que reconoce que la sintaxis computacional es una disciplina de compromiso entre la teoría pura y la manejabilidad estadística.

La legalización de la hibridación de etiquetas (Constituyentes \+ UD) y el reconocimiento de las peculiaridades de cada corpus (como la recursividad en AnCora o la planitud en VIT) transforman al validador de un censor rígido en un asistente inteligente. Este enfoque garantiza que Grammatomy pueda ser utilizado tanto para depurar modelos de producción como para realizar investigación lingüística avanzada, proporcionando una visión clara de cómo los modelos realmente "entienden" y estructuran el lenguaje humano en la práctica.

#### **Obras citadas**

1. Adding a new Constituency model \- Stanza, fecha de acceso: febrero 3, 2026, [https://stanfordnlp.github.io/stanza/new\_language\_constituency.html](https://stanfordnlp.github.io/stanza/new_language_constituency.html)  
2. Constituency Parser \- Stanza \- Stanford NLP Group, fecha de acceso: febrero 3, 2026, [https://stanfordnlp.github.io/stanza/constituency.html](https://stanfordnlp.github.io/stanza/constituency.html)  
3. Out-of-the-Box Robust Parsing of Portuguese \- PORTULAN CLARIN, fecha de acceso: febrero 3, 2026, [https://portulanclarin.net/static/docs/lxparser/2010SilvaBrancoCastroEtAl.pdf](https://portulanclarin.net/static/docs/lxparser/2010SilvaBrancoCastroEtAl.pdf)  
4. VIT – Venice Italian Treebank: Syntactic and Quantitative ... \- DSpace, fecha de acceso: febrero 3, 2026, [https://dspace.ut.ee/bitstreams/c216431f-9791-47c1-8283-d2ff073d8988/download](https://dspace.ut.ee/bitstreams/c216431f-9791-47c1-8283-d2ff073d8988/download)  
5. UniversalDependencies/UD\_Spanish-AnCora: Spanish data from the AnCora corpus. \- GitHub, fecha de acceso: febrero 3, 2026, [https://github.com/UniversalDependencies/UD\_Spanish-AnCora](https://github.com/UniversalDependencies/UD_Spanish-AnCora)  
6. UniversalDependencies/UD\_Portuguese-CINTIL \- GitHub, fecha de acceso: febrero 3, 2026, [https://github.com/UniversalDependencies/UD\_Portuguese-CINTIL](https://github.com/UniversalDependencies/UD_Portuguese-CINTIL)  
7. VIT – Venice Italian Treebank: Syntactic and Quantitative Features \- ResearchGate, fecha de acceso: febrero 3, 2026, [https://www.researchgate.net/publication/28584827\_VIT\_-\_Venice\_Italian\_Treebank\_Syntactic\_and\_Quantitative\_Features](https://www.researchgate.net/publication/28584827_VIT_-_Venice_Italian_Treebank_Syntactic_and_Quantitative_Features)  
8. DRAFT VERSION AnCora: Multilingual and Multilevel Annotated ..., fecha de acceso: febrero 3, 2026, [https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)  
9. Spanish FAQ for Stanford CoreNLP, parser, POS tagger, and NER, fecha de acceso: febrero 3, 2026, [https://nlp.stanford.edu/software/spanish-faq.shtml](https://nlp.stanford.edu/software/spanish-faq.shtml)  
10. Penn Treebank Constituent Tags, fecha de acceso: febrero 3, 2026, [https://surdeanu.cs.arizona.edu/mihai/teaching/ista555-fall13/readings/PennTreebankConstituents.html](https://surdeanu.cs.arizona.edu/mihai/teaching/ista555-fall13/readings/PennTreebankConstituents.html)  
11. Penn Treebank — HanLP Documentation, fecha de acceso: febrero 3, 2026, [https://hanlp.hankcs.com/docs/annotations/constituency/ptb.html](https://hanlp.hankcs.com/docs/annotations/constituency/ptb.html)  
12. Nominalizaciones deverbales: Denotación y estructura argumental \- TDX, fecha de acceso: febrero 3, 2026, [https://www.tdx.cat/bitstream/10803/81499/1/APM\_TESIS.pdf](https://www.tdx.cat/bitstream/10803/81499/1/APM_TESIS.pdf)  
13. 6.14 Trees: Introducing X-bar theory – ENG 200 \- NOVA Open Publishing, fecha de acceso: febrero 3, 2026, [https://pressbooks.nvcc.edu/eng200h5p/chapter/x-bar-theory-introduction/](https://pressbooks.nvcc.edu/eng200h5p/chapter/x-bar-theory-introduction/)  
14. X-bar theory \- Wikipedia, fecha de acceso: febrero 3, 2026, [https://en.wikipedia.org/wiki/X-bar\_theory](https://en.wikipedia.org/wiki/X-bar_theory)  
15. 6\. X-bar syntax, fecha de acceso: febrero 3, 2026, [https://opentext.ku.edu/syntax/chapter/chapter-6-x-bar-syntax/](https://opentext.ku.edu/syntax/chapter/chapter-6-x-bar-syntax/)  
16. (PDF) VIT Venice Italian Treebank: Syntactic and quantitative features \- Academia.edu, fecha de acceso: febrero 3, 2026, [https://www.academia.edu/36917150/VIT\_Venice\_Italian\_Treebank\_Syntactic\_and\_quantitative\_features](https://www.academia.edu/36917150/VIT_Venice_Italian_Treebank_Syntactic_and_quantitative_features)  
17. Enriching the Venice Italian Treebank with dependency and ... \- LREC, fecha de acceso: febrero 3, 2026, [http://www.lrec-conf.org/proceedings/lrec2008/pdf/490\_paper.pdf](http://www.lrec-conf.org/proceedings/lrec2008/pdf/490_paper.pdf)  
18. Step-by-step Instructions and a Simple Tabular Output Format Improve the Dependency Parsing Accuracy of LLMs \- arXiv, fecha de acceso: febrero 3, 2026, [https://arxiv.org/html/2506.09983v2](https://arxiv.org/html/2506.09983v2)  
19. UD\_Spanish-AnCora \- Universal Dependencies, fecha de acceso: febrero 3, 2026, [https://universaldependencies.org/treebanks/es\_ancora/index.html](https://universaldependencies.org/treebanks/es_ancora/index.html)  
20. PlanTL-GOB-ES/UD\_Spanish-AnCora · Datasets at Hugging Face, fecha de acceso: febrero 3, 2026, [https://huggingface.co/datasets/PlanTL-GOB-ES/UD\_Spanish-AnCora](https://huggingface.co/datasets/PlanTL-GOB-ES/UD_Spanish-AnCora)  
21. UD\_Spanish-GSD \- Universal Dependencies, fecha de acceso: febrero 3, 2026, [https://universaldependencies.org/treebanks/es\_gsd/index.html](https://universaldependencies.org/treebanks/es_gsd/index.html)  
22. Software \> Stanford Parser, fecha de acceso: febrero 3, 2026, [https://nlp.stanford.edu/software/lex-parser.shtml](https://nlp.stanford.edu/software/lex-parser.shtml)  
23. Harmonization and Development of Resources and Tools for Italian Natural Language Processing within the PARLI Project, fecha de acceso: febrero 3, 2026, [http://ndl.ethernet.edu.et/bitstream/123456789/66475/1/313.pdf](http://ndl.ethernet.edu.et/bitstream/123456789/66475/1/313.pdf)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAZCAYAAAA14t7uAAABC0lEQVR4XmNgGAU0Av+B+CO6IAhUMkAkYTgLVRoMnjOgqvmJJAfiL0biYwCQguNQOhJNDgQmA/FuNDF5IL6BJoYBngGxGQPE4D1ociBwBIjL0cSigLgaTQwDxEJpmHfRwXsgZkQTO4PGxwDKQCwBZT9mgBgshJAGg/VofE4g/o0mhgHmIbFFgPgbED8AYhaoGDcQG8AUQAEXENuhiWGAJ2j8WQwQV4dB+R4MmMFAEKQC8WV0QQbUsD6NLEEsWMQASUroAGawAJQmGdwH4lB0QSC4yQAxsIABEqEkg2voAlDAD8SfGCCGJ6HJEQXwZcdJDBCDldAlcAGQa2BhCMOwpIUOZqALjIJRMJwBAF0EO5Vv+ylgAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAZCAYAAAAxFw7TAAAAyElEQVR4XmNgGAVkgv9A/BFdAB0XIisAgs1IciC8HkkOxF+MxIcDkMRzdEEkAJJ3QROTB+IbaGJwALMdF5iELgAEUUBcjS4IA7gMVGZACyMkcAZdABngMvAwEM9DFwQCTiD+jS6IDLAZKAXEIWhiMMAFxHbogsgAm4Gr0PgkgcsMEANBNoPAYyBOQkiTDrYwQAzUgPJ3IsmRBaYxQAx0B2IHBkgaowhEMEAM/ArER9HkyALWDIiIMUGTIxs8A2J2dMFRMAqGEgAAf00w2/DVM8cAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAYCAYAAAD6S912AAAAyklEQVR4XmNgGAVkAHUg/g/EFugSIJDJAJHEhS8CcQVcNQQkAfF9IGZEE0cBvxkgBqADCSD+BMT7kcRuArEUEh8rgLkIGzjOAJFzBuIwKJsgACn6gC4IBEwMEBeC5PWBuA+Iv6KowAL8GCAa6tAlgGA+A0QuGMr/CcTGCGnsAGQrSJMrugQDRPwXEt8diY0ViDFgxiwMX4HKkwRCGSCa1wKxAxIGhRdZ4CoDxEB+dAlyAcx7VANUM9ABiP0ZEAaC+CpI8qNgFAwpAADGUTamsw+NLAAAAABJRU5ErkJggg==>