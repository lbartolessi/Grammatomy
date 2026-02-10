# **Auditoría de integridad estructural en modelos de análisis de constituyentes para el español basados en el corpus AnCora**

El desarrollo de herramientas de validación sintáctica estricta, como Grammatomy, exige una comprensión profunda de las discrepancias entre la teoría lingüística formal y las implementaciones prácticas de los modelos de procesamiento de lenguaje natural (PLN) de última generación. En el contexto del español, la transición de los esquemas de anotación manuales, como los del corpus AnCora, hacia modelos neuronales entrenados en arquitecturas de transformadores ha introducido una serie de transformaciones estructurales que a menudo se perciben como inconsistencias o errores. Sin embargo, un análisis técnico exhaustivo de los artefactos bajo estudio —Stanza (Stanford NLP) y Benepar (Berkeley Neural Parser)— revela que estas "laxitudes" estructurales son, en gran medida, decisiones de diseño orientadas a la optimización estadística y la convergencia de los modelos.

## **La arquitectura del corpus AnCora y su transformación hacia estándares neuronales**

Para auditar la integridad estructural de los modelos actuales, es imperativo remontarse a la fuente de sus datos de entrenamiento: el corpus AnCora. AnCora representa el esfuerzo más significativo en la creación de un recurso multilingüe (español y catalán) con anotaciones en múltiples niveles, incluyendo morfología, sintaxis y semántica.1 Originalmente, las anotaciones de AnCora se realizaron de forma manual o semiautomática siguiendo una jerarquía de constituyentes muy rica, donde, por ejemplo, los sintagmas nominales no eran unidades atómicas, sino que se descomponían en niveles intermedios como el grupo nominal (grup.nom) para capturar la recursividad y la estructura interna del nombre y sus complementos.1

La jerarquía nativa de AnCora fue diseñada para ser lingüísticamente exhaustiva, permitiendo etiquetas funcionales sufijadas (como sn-suj para sintagma nominal sujeto) que vinculaban la estructura de constituyentes con las funciones gramaticales.3 No obstante, los modelos neuronales contemporáneos, especialmente aquellos basados en el estándar del Penn Treebank (PTB), requieren una simplificación de este espacio de etiquetas para evitar el problema de la dispersión de datos (_sparse data_). La política de reducción de etiquetas es un proceso documentado en la historia del análisis sintáctico, donde se sacrifica la granularidad teórica en favor de una mayor precisión estadística y velocidad de procesamiento.4

## **Análisis de la política de colapso de etiquetas y eliminación de cadenas unarias**

La primera preocupación de la auditoría se centra en si los scripts de preprocesamiento eliminan deliberadamente nodos unarios o proyecciones intermedias. La evidencia técnica en los repositorios de Stanford y Berkeley confirma que esta práctica es un estándar de facto en el entrenamiento de modelos de constituyentes.

### **El mecanismo de poda en Stanza y CoreNLP**

En el ecosistema de Stanford, el preprocesamiento de treebanks para el entrenamiento de modelos neuronales incluye clases específicas como RemoveGFSubcategoryStripper, cuya función es eliminar las subcategorizaciones de los nodos de categoría y etiquetas de funciones gramaticales.6 Este proceso transforma una estructura compleja como (SN-SUJ (GRUP.NOM (NC profesor))) en una versión más simple (NP (NN profesor)). La razón de este colapso es que el mantenimiento de etiquetas de funciones gramaticales (GF) multiplica exponencialmente el número de etiquetas que el clasificador debe predecir. En un modelo de _Shift-Reduce_ como el de Stanza, cada etiqueta adicional representa una acción de reducción posible en la pila, lo que complica el aprendizaje de la política de transición.7

Además, la simplificación de NP \-\> NML \-\> N a NP \-\> N es una respuesta a la necesidad de binarización de reglas, necesaria para obtener tiempos de ejecución cúbicos en algoritmos de tipo CKY o para optimizar la secuencia de transiciones en modelos de desplazamiento-reducción.9 Los scripts de Stanford para el español, entrenados con el paquete default_accurate sobre AnCora y datos de LDC, aplican estas transformaciones para unificar los diversos estilos de anotación de las fuentes, lo que resulta en la pérdida de niveles intermedios que Grammatomy identifica como ausentes.7

### **La gestión de cadenas unarias en Benepar**

El Berkeley Neural Parser (Benepar) aborda la jerarquía desde una perspectiva basada en gráficos y atención propia (_self-attention_). Aunque su arquitectura es teóricamente capaz de manejar cadenas unarias, el sistema a menudo las colapsa durante el entrenamiento para mejorar la métrica F1.12 En Benepar, un tramo de texto (_span_) puede tener múltiples etiquetas cuando existen cadenas unarias, representadas internamente como una tupla de etiquetas para ese nodo.12 Sin embargo, si el script de entrenamiento detecta que ciertos niveles intermedios (como el grup.nom de AnCora) no aportan valor discriminativo para predecir la estructura global, estos se eliminan mediante heurísticas de simplificación.

La tabla a continuación resume las transformaciones típicas observadas durante la conversión de AnCora a los formatos compatibles con estos modelos:

| Estructura Original AnCora      | Estructura en Modelo Neuronal | Justificación Técnica                                                      |
| :------------------------------ | :---------------------------- | :------------------------------------------------------------------------- |
| sn-suj                          | NP                            | Eliminación de etiquetas funcionales para reducir el espacio de búsqueda.3 |
| grup.nom                        | Colapsado en NP               | Reducción de profundidad del árbol para optimizar la convergencia.4        |
| grup.verb                       | VP                            | Estandarización hacia el formato Penn Treebank.8                           |
| Cadenas unarias X \-\> Y \-\> Z | X-Y \-\> Z o X \-\> Z         | Minimización de pasos de reducción en modelos Shift-Reduce.10              |
| Puntuación anidada              | Puntuación en ROOT/S          | Heurística de pseudo-proyectividad para evitar cruces de arcos.16          |

Este colapso no es un error de los modelos, sino una característica de diseño necesaria para que los analizadores funcionen con la eficiencia requerida en entornos de producción. La estructura "laxa" es, por tanto, el estándar operativo de estos artefactos.

## **Tratamiento del nodo ROOT y la topología de la puntuación**

El segundo punto crítico de la auditoría es la ubicación de los signos de puntuación como hijos directos del nodo ROOT. Este comportamiento, detectado en stanza-es, genera árboles que parecen violar la jerarquía donde la puntuación debería estar contenida dentro de la oración (S).

### **Convenciones de pseudo-proyectividad y segmentación**

La investigación documental indica que permitir que la puntuación cuelgue de ROOT es una convención de anotación que facilita la gestión de estructuras no proyectivas, especialmente en lenguas con orden de palabras relativamente libre como el español.16 En muchos esquemas de conversión, especialmente aquellos que buscan compatibilidad con Universal Dependencies (UD), la puntuación se trata como un elemento periférico que no pertenece estrictamente a la estructura sintáctica del predicado principal.18

En el modelo Shift-Reduce de Stanza, la decisión de adjuntar la puntuación al nodo superior a menudo ocurre al final de la secuencia de transiciones. Si el modelo ha cerrado el constituyente principal S y el siguiente token es un punto final, la acción más conservadora y menos propensa a errores de "cruzado de paréntesis" (_cross-bracketing_) es adjuntar dicho punto al nodo ROOT.8 Esta práctica evita que la puntuación "rompa" constituyentes internos si el modelo tiene dudas sobre su anidamiento exacto.

Además, el corpus AnCora original presentaba desafíos en la representación de la puntuación debido a su origen en XML, donde las etiquetas de puntuación a menudo delimitaban oraciones completas de manera externa.1 Al convertir estos datos para el entrenamiento de Stanza, los scripts mantienen esta separación de nivel superior. Por lo tanto, no se trata de un error de segmentación, sino de una política de adjunción deliberada para mantener la robustez del modelo frente a oraciones largas y complejas donde el anidamiento de la puntuación podría degradar la precisión del resto de la estructura.17

## **Hibridación de etiquetas UD en árboles de constituyentes**

El tercer hallazgo de la auditoría confirma la inyección de etiquetas de Universal Dependencies (UPOS), como NOUN, DET y PROPN, en lugar de las etiquetas tradicionales de constituyentes como NN o DT.

### **La integración del pipeline de Stanza**

Stanza está diseñado como un sistema modular donde el procesador de constituyentes depende de las salidas de los procesadores previos (tokenización y POS).7 Dado que los modelos de POS para español en Stanza están armonizados con el estándar de Universal Dependencies v2, el etiquetador produce etiquetas UPOS.19 El analizador de constituyentes hereda estas etiquetas y las utiliza como nodos pre-terminales.

Esta hibridación está documentada oficialmente en la descripción de los modelos de Stanza, donde se menciona que los modelos de constituyentes para idiomas distintos al inglés a menudo se entrenan utilizando el conjunto de etiquetas UPOS para garantizar la consistencia en el ecosistema multilingüe de la herramienta.7 En el caso de benepar_es2, cuando se utiliza a través de la integración con spaCy, el comportamiento es similar: el componente Benepar hereda las etiquetas POS asignadas por el modelo base de spaCy, que para el español suele ser un modelo entrenado también sobre AnCora-UD.12

| Componente                  | Origen de la Etiqueta   | Estándar Utilizado |
| :-------------------------- | :---------------------- | :----------------- |
| Pre-terminal (Sustantivo)   | POS Tagger (UD)         | NOUN               |
| Pre-terminal (Determinante) | POS Tagger (UD)         | DET                |
| Nodo intermedio             | Preprocesamiento AnCora | NP, VP, PP         |
| Nodo raíz                   | Convención PTB          | ROOT               |

Este uso de etiquetas UPOS en árboles de constituyentes se considera una salida estándar válida para estos modelos específicos. La documentación de Stanza subraya que sus modelos de constituyentes pueden soportar cualquier conjunto de etiquetas siempre que existan datos de entrenamiento, y para el español, la decisión estratégica fue alinear los pre-terminales con UD para facilitar las tareas de transferencia de aprendizaje y la consistencia entre los modos de análisis de dependencias y constituyentes.7

## **Implicaciones para la validación estructural en Grammatomy**

La auditoría revela una divergencia fundamental entre el "rigor lingüístico" y el "estándar de facto" del software de PLN actual. Si Grammatomy mantiene reglas de validación basadas estrictamente en la jerarquía teórica de AnCora, marcará como erróneos prácticamente todos los resultados generados por los modelos SOTA actuales.

### **El dilema de la relajación de reglas**

El análisis de los scripts de preprocesamiento de Stanza y Benepar demuestra que la estructura laxa no es un accidente, sino el resultado de procesos de normalización y limpieza destinados a maximizar la utilidad estadística del modelo.4 La eliminación de nodos intermedios y el colapso de etiquetas son técnicas estándar para reducir la complejidad del problema de aprendizaje. En particular:

1. La ausencia de grup.nom responde a la necesidad de aplanar el árbol para que las puntuaciones de los tramos (_span scores_) en modelos como Benepar sean más robustas y menos propensas a errores en niveles de granularidad fina que no afectan la interpretación semántica global.21
2. La posición de la puntuación en ROOT es una estrategia de seguridad para evitar violaciones de proyectividad que invalidarían el árbol de constituyentes completo.16
3. La presencia de etiquetas UD es una consecuencia de la modularidad y la búsqueda de un "lenguaje universal" de etiquetas que trascienda los treebanks individuales.22

Por tanto, Grammatomy debería considerar la implementación de perfiles de validación diferenciados. Un "perfil de rigor lingüístico" sería útil para la corrección manual de corpus, pero un "perfil de validación de modelos neuronales" debe necesariamente relajar sus reglas para aceptar estas convenciones como válidas. Tratar estos comportamientos como errores del modelo ignoraría la realidad de cómo se construyen y optimizan estos artefactos en la actualidad.

## **Consideraciones sobre la métrica y la fidelidad estructural**

Un punto adicional a considerar es cómo se evalúan estos modelos. La métrica F1 calculada mediante evalb ignora frecuentemente la puntuación y las etiquetas de nivel superior, centrándose en el emparejamiento de paréntesis etiquetados para el contenido léxico.7 Esto ha permitido que los modelos evolucionen hacia estructuras más planas sin sufrir penalizaciones en las tablas de clasificación de precisión (_leaderboards_).

### **Evaluación de la pérdida de información**

Aunque el colapso de etiquetas mejora la convergencia, existe una pérdida de información estructural innegable. La desaparición de la cadena NP \-\> NML \-\> N implica que el modelo ya no distingue explícitamente entre un nombre que actúa como núcleo y una estructura nominal compleja anidada, a menos que esta última tenga un tramo mayor que una sola palabra.4 Para Grammatomy, esto significa que la validación no solo debe ser una comprobación de "presencia/ausencia", sino una evaluación de si la estructura resultante permite una reconstrucción semántica coherente.

| Fenómeno            | Efecto en la Validación | Recomendación para Grammatomy                           |
| :------------------ | :---------------------- | :------------------------------------------------------ |
| Puntuación en ROOT  | Desajuste jerárquico    | Permitir como excepción si el nodo hermano es S o FRAG. |
| Falta de grup.nom   | Árbol plano             | Aceptar NP \-\> NOUN como estructura mínima legal.      |
| Etiquetas UD        | Conflicto de tagset     | Mapear NOUN a N, DET a D en las reglas de validación.   |
| Clíticos fusionados | Fragmentación léxica    | Validar la consistencia de la tokenización previa.30    |

## **Conclusiones de la auditoría técnica**

Tras el análisis de los artefactos Stanza y Benepar, junto con la documentación de preprocesamiento de AnCora, se concluye que:

El colapso de etiquetas y la simplificación de jerarquías en sintagmas nominales son características de diseño (_features_) intencionales, integradas en los scripts de entrenamiento para optimizar la precisión y la velocidad de los modelos neuronales. La inyección de etiquetas UD es una salida estándar documentada en Stanza y una consecuencia de la arquitectura de pipeline de spaCy para Benepar. La ubicación de la puntuación en el nodo ROOT responde a convenciones de robustez y pseudo-proyectividad.

Mantener el rigor extremo en Grammatomy llevaría a un rechazo sistemático de las herramientas SOTA. Se recomienda encarecidamente la relajación de las reglas de validación para alinearlas con los estándares de facto del procesamiento neuronal moderno, tratando la estructura laxa no como un error, sino como la representación canónica del análisis sintáctico computacional contemporáneo para el español. La integridad estructural del modelo no está rota; ha sido transformada por las exigencias de la eficiencia estadística.

Este informe sirve como base para ajustar las expectativas de las herramientas de validación sintáctica frente a la realidad tecnológica de los transformadores y los sistemas de análisis basados en transiciones, asegurando que la auditoría de modelos se realice bajo criterios de viabilidad técnica y no solo bajo idealismos gramaticales.

### **Obras citadas**

1. DRAFT VERSION AnCora: Multilingual and Multilevel Annotated Corpora \- Universitat de Barcelona, fecha de acceso: febrero 4, 2026, [https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf](https://clic.ub.edu/corpus/sites/default/files/inline-files/ancora-corpus.pdf)
2. Iarg-AnCora: Spanish corpus annotated with implicit arguments, fecha de acceso: febrero 4, 2026, [https://diposit.ub.edu/dspace/bitstream/2445/171322/1/669157.pdf](https://diposit.ub.edu/dspace/bitstream/2445/171322/1/669157.pdf)
3. Towards a Machine-Learning Architecture for Lexical Functional Grammar Parsing Grzegorz Chrupa la, fecha de acceso: febrero 4, 2026, [https://doras.dcu.ie/550/1/GrzegorzPhDFinal.pdf](https://doras.dcu.ie/550/1/GrzegorzPhDFinal.pdf)
4. Building a large annotated corpus of English: the Penn Treebank \- LDC Catalog, fecha de acceso: febrero 4, 2026, [https://catalog.ldc.upenn.edu/docs/LDC95T7/cl93.html](https://catalog.ldc.upenn.edu/docs/LDC95T7/cl93.html)
5. Penn Treebank (Phrase Structure Treebank), fecha de acceso: febrero 4, 2026, [https://standards.clarin.eu/sis/views/view-spec.xq?id=SpecPennTB](https://standards.clarin.eu/sis/views/view-spec.xq?id=SpecPennTB)
6. Index (Stanford CoreNLP API), fecha de acceso: febrero 4, 2026, [https://nlp.stanford.edu/nlp/javadoc/javanlp-3.5.0/index-all.html](https://nlp.stanford.edu/nlp/javadoc/javanlp-3.5.0/index-all.html)
7. Constituency Parser \- Stanza \- Stanford NLP Group, fecha de acceso: febrero 4, 2026, [https://stanfordnlp.github.io/stanza/constituency.html](https://stanfordnlp.github.io/stanza/constituency.html)
8. CoreNLP/doc/lexparser/README.txt at main \- GitHub, fecha de acceso: febrero 4, 2026, [https://github.com/stanfordnlp/CoreNLP/blob/main/doc/lexparser/README.txt](https://github.com/stanfordnlp/CoreNLP/blob/main/doc/lexparser/README.txt)
9. Constituency Parsing \- Stanford University, fecha de acceso: febrero 4, 2026, [https://web.stanford.edu/\~jurafsky/slp3/old_sep21/13.pdf](https://web.stanford.edu/~jurafsky/slp3/old_sep21/13.pdf)
10. HOLISTIC LANGUAGE PROCESSING: JOINT MODELS OF LINGUISTIC STRUCTURE A DISSERTATION SUBMITTED TO THE DEPARTMENT OF COMPUTER SCIENC \- Stanford NLP Group, fecha de acceso: febrero 4, 2026, [https://nlp.stanford.edu/\~manning/dissertations/Finkel-Jenny-thesis-augmented.pdf](https://nlp.stanford.edu/~manning/dissertations/Finkel-Jenny-thesis-augmented.pdf)
11. Stanza v1.4.1 · stanfordnlp stanza · Discussion \#1121 \- GitHub, fecha de acceso: febrero 4, 2026, [https://github.com/stanfordnlp/stanza/discussions/1121](https://github.com/stanfordnlp/stanza/discussions/1121)
12. nikitakit/self-attentive-parser: High-accuracy NLP parser ... \- GitHub, fecha de acceso: febrero 4, 2026, [https://github.com/nikitakit/self-attentive-parser](https://github.com/nikitakit/self-attentive-parser)
13. mrdrozdov/self-attentive-parser-with-extra-features: High-accuracy NLP parser with models for 11 languages. \- GitHub, fecha de acceso: febrero 4, 2026, [https://github.com/mrdrozdov/self-attentive-parser-with-extra-features](https://github.com/mrdrozdov/self-attentive-parser-with-extra-features)
14. Syntax Parsing of Morphologically Rich Languages and Its Application \- SZTE Doktori Repozitórium, fecha de acceso: febrero 4, 2026, [https://doktori.bibl.u-szeged.hu/12207/3/thesis_szzs_online.pdf](https://doktori.bibl.u-szeged.hu/12207/3/thesis_szzs_online.pdf)
15. DKPro Core™ Tagset Reference, fecha de acceso: febrero 4, 2026, [https://dkpro.github.io/dkpro-core/releases/1.8.0/docs/tagset-reference.html](https://dkpro.github.io/dkpro-core/releases/1.8.0/docs/tagset-reference.html)
16. Parsing as Reduction \- ACL Anthology, fecha de acceso: febrero 4, 2026, [https://aclanthology.org/P15-1147.pdf](https://aclanthology.org/P15-1147.pdf)
17. Transformation and Combination in Data-Driven Dependency Parsing \- Diva-portal.org, fecha de acceso: febrero 4, 2026, [http://www.diva-portal.org/smash/get/diva2:287405/FULLTEXT01.pdf](http://www.diva-portal.org/smash/get/diva2:287405/FULLTEXT01.pdf)
18. UniversalDependencies/UD_Spanish-AnCora: Spanish data from the AnCora corpus. \- GitHub, fecha de acceso: febrero 4, 2026, [https://github.com/UniversalDependencies/UD_Spanish-AnCora](https://github.com/UniversalDependencies/UD_Spanish-AnCora)
19. UD_Spanish-AnCora \- Universal Dependencies, fecha de acceso: febrero 4, 2026, [https://universaldependencies.org/treebanks/es_ancora/index.html](https://universaldependencies.org/treebanks/es_ancora/index.html)
20. The Dirty Little Secret of Constituency Parser Evaluation \- Grammarly Engineering Blog, fecha de acceso: febrero 4, 2026, [https://www.grammarly.com/blog/engineering/the-dirty-little-secret-of-constituency-parser-evaluation/](https://www.grammarly.com/blog/engineering/the-dirty-little-secret-of-constituency-parser-evaluation/)
21. Improving Constituency Parsing with Span Attention \- ACL Anthology, fecha de acceso: febrero 4, 2026, [https://aclanthology.org/2020.findings-emnlp.153.pdf](https://aclanthology.org/2020.findings-emnlp.153.pdf)
22. A syntax-injected approach for faster and more accurate sentiment analysis \- PeerJ, fecha de acceso: febrero 4, 2026, [https://peerj.com/articles/cs-3519/](https://peerj.com/articles/cs-3519/)
23. A Universal Dependencies Conversion Pipeline for a Penn-format Constituency Treebank, fecha de acceso: febrero 4, 2026, [https://www.researchgate.net/publication/352657231_A_Universal_Dependencies_Conversion_Pipeline_for_a_Penn-format_Constituency_Treebank](https://www.researchgate.net/publication/352657231_A_Universal_Dependencies_Conversion_Pipeline_for_a_Penn-format_Constituency_Treebank)
24. Proceedings of the Ancient Language Processing Workshop (ALP 2023\) associated with RANLP'2023, fecha de acceso: febrero 4, 2026, [https://www.ancientnlp.com/alp2023/accepted_papers/ALP2023pro.pdf](https://www.ancientnlp.com/alp2023/accepted_papers/ALP2023pro.pdf)
25. A survey on narrative extraction from textual data, fecha de acceso: febrero 4, 2026, [https://d-nb.info/1283544660/34](https://d-nb.info/1283544660/34)
26. Proceedings of the Third Workshop on Quantitative Syntax (QUASY, SyntaxFest 2025\) \- ACL Anthology, fecha de acceso: febrero 4, 2026, [https://aclanthology.org/2025.quasy-1.pdf](https://aclanthology.org/2025.quasy-1.pdf)
27. Head-driven Phrase Structure Parsing in O(n ) Time Complexity \- arXiv, fecha de acceso: febrero 4, 2026, [https://arxiv.org/pdf/2105.09835](https://arxiv.org/pdf/2105.09835)
28. Divisible Transition Systems and Multiplanar Dependency Parsing \- MIT Press Direct, fecha de acceso: febrero 4, 2026, [https://direct.mit.edu/coli/article/39/4/799/1459/Divisible-Transition-Systems-and-Multiplanar](https://direct.mit.edu/coli/article/39/4/799/1459/Divisible-Transition-Systems-and-Multiplanar)
29. Proceedings of the 16th International Conference on Parsing Technologies and the IWPT 2020 Shared Task on Parsing into Enhanced \- ACL Anthology, fecha de acceso: febrero 4, 2026, [https://aclanthology.org/2020.iwpt-1.pdf](https://aclanthology.org/2020.iwpt-1.pdf)
30. Incorrect Spanish verb decomposition · Issue \#1395 · stanfordnlp/stanza \- GitHub, fecha de acceso: febrero 4, 2026, [https://github.com/stanfordnlp/stanza/issues/1395](https://github.com/stanfordnlp/stanza/issues/1395)
