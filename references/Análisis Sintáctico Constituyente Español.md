# **Motores de Análisis Sintáctico de Constituyentes para la Segmentación Fónica y Prosódica del Español: Evaluación de Modelos SOTA y Estrategias de Despliegue (2024-2026)**

El desarrollo de sistemas avanzados para la segmentación fónica y prosódica en español requiere una comprensión estructural que trascienda el análisis de dependencias superficiales. La prosodia, entendida como la organización jerárquica de la duración, la intensidad y el tono, se correlaciona estrechamente con la estructura sintagmática de la oración. Los límites de los constituyentes sintácticos suelen coincidir con las fronteras de los grupos fónicos, lo que convierte al *Constituent Parsing* (Análisis de Constituyentes) en una herramienta indispensable para el modelado lingüístico de precisión. A diferencia del *shallow parsing* o *chunking*, que se limita a identificar sintagmas aislados, el análisis de constituyentes recursivo proporciona una jerarquía completa de nodos anidados, permitiendo capturar la arquitectura profunda de la lengua española.

## **Fundamentos Lingüísticos y Necesidades Técnicas en el Análisis de Constituyentes**

El análisis de constituyentes se define como el proceso de descomponer una oración en sus unidades gramaticales constituyentes, organizadas jerárquicamente en un árbol de estructura de frase.1 Cada nodo no terminal en este árbol representa una categoría sintáctica (como SN para Sintagma Nominal o SV para Sintagma Verbal), mientras que los nodos terminales corresponden a los tokens individuales etiquetados con sus respectivas categorías de Part-of-Speech (POS).2 Para la segmentación prosódica, esta jerarquía es vital: permite identificar no solo el sujeto y el predicado, sino también las complejas estructuras de subordinación y adjunción donde se producen los fenómenos de declinación tonal y pausas respiratorias.

En el contexto del español, un idioma con una morfología rica y un orden de palabras relativamente flexible, el motor de análisis debe ser capaz de manejar la recursividad infinita de la gramática. Los requerimientos técnicos para una librería de segmentación fónica moderna incluyen la capacidad de ejecutarse en entornos locales (mediante contenedores Docker o instalaciones vía pip) para garantizar la soberanía de los datos y el procesamiento eficiente por lotes.3 Asimismo, la salida del sistema debe ser mapeable a estructuras de datos anidadas, como diccionarios JSON o árboles de la librería anytree, para facilitar su manipulación algorítmica.4

## **El Estado del Arte (SOTA): Modelos Neuronales y Arquitecturas de Atención**

Desde 2024, el panorama del procesamiento de lenguaje natural (PLN) para el español ha sido dominado por arquitecturas basadas en Transformers que han optimizado el análisis de constituyentes mediante mecanismos de auto-atención y decodificadores de tramos (*spans*).

### **La Arquitectura Berkeley Neural Parser (Benepar)**

El Berkeley Neural Parser representa uno de los hitos más significativos en el análisis sintáctico moderno. Su enfoque se basa en un codificador auto-atentivo que asigna puntuaciones a cada tramo posible de la oración, buscando la estructura que maximice la puntuación total del árbol.6 Matemáticamente, si una oración ![][image1] se compone de tokens ![][image2], el parser busca el árbol ![][image3] tal que:

![][image4]  
Donde ![][image5] es la puntuación asignada al tramo que comienza en la posición ![][image6], termina en ![][image7] y tiene la etiqueta sintáctica ![][image8].7 Este modelo evita las limitaciones de las gramáticas de contexto libre tradicionales al utilizar representaciones vectoriales densas extraídas de modelos como BERT o RoBERTa.3

Sin embargo, la implementación específica de Benepar para el español presenta matices importantes. Aunque la librería benepar es fácilmente instalable vía pip, los modelos pre-entrenados oficiales se han centrado históricamente en idiomas como el inglés, chino y alemán.10 Para el español, la estrategia predominante en el periodo 2024-2026 implica el uso de modelos multilingües (como XLM-RoBERTa) o el entrenamiento de modelos específicos utilizando el AnCora Treebank.7 Los modelos SOTA actuales en Hugging Face que utilizan esta arquitectura permiten obtener árboles con una profundidad jerárquica real, capturando sintagmas complejos de manera recursiva.8

### **Avances en Parsers de CRF Neuronal**

Otra línea de investigación SOTA involucra a los parsers de Campo Aleatorio Condicional (CRF) neuronal. Estos modelos logran un rendimiento excepcional mediante el uso de algoritmos de *inside-outside* batchificados en GPU, permitiendo procesar más de 1,000 oraciones por segundo con una precisión estructural cercana al 96% en benchmarks estándar.12 Para el desarrollador de una librería de segmentación fónica, estos modelos ofrecen una eficiencia crítica cuando se trabaja con grandes corpus de audio transcrito que requieren análisis sintáctico masivo.

## **Librerías Consolidadas: Stanza vs. spaCy**

La elección entre las dos librerías más importantes del ecosistema Python, Stanza y spaCy, depende fundamentalmente de la prioridad dada a la precisión lingüística frente a la velocidad de procesamiento.

### **Stanza: El Estándar de Oro en Profundidad Sintáctica**

Stanza, desarrollada por el grupo de PLN de Stanford, integra un motor de *Constituent Parsing* que es, posiblemente, el más completo para el español en una librería de fácil instalación.14 A diferencia de los modelos básicos de spaCy, que se centran en dependencias, Stanza incluye un ConstituencyProcessor basado en un parser de tipo *shift-reduce* neuronal.14

El pipeline de Stanza para español se configura de la siguiente manera:

1. **Tokenización y MWT:** Maneja la expansión de palabras multi-token (como "del" a "de el" o "dámelo" a "da me lo"), lo cual es esencial para el etiquetado POS correcto.14  
2. **Etiquetado POS:** Proporciona etiquetas detalladas (XPOS) basadas en el estándar del AnCora Treebank.15  
3. **Análisis de Constituyentes:** Genera un objeto de árbol recursivo que puede recorrerse programáticamente.14

La capacidad de Stanza para utilizar modelos "accurate" basados en Transformers (como BERT) eleva la precisión de los límites sintagmáticos, aunque incrementa el consumo de recursos.14 El árbol resultante sigue el formato del Penn Treebank, el cual es el estándar de facto para la representación de constituyentes en la investigación académica.14

### **spaCy y la Extensión spacy-benepar**

spaCy ha sido tradicionalmente criticado por su falta de un motor nativo de constituyentes. Para suplir esta carencia, la extensión spacy-benepar permite integrar la potencia de la arquitectura de Berkeley directamente en el flujo de trabajo de spaCy.6 Esta integración es particularmente útil si el resto del pipeline de segmentación (como la lematización o el reconocimiento de entidades) ya reside en spaCy.

No obstante, existe un inconveniente técnico: para el español, no hay un modelo de constituyentes "oficial" dentro del comando benepar.download().10 Los usuarios deben descargar modelos específicos de Hugging Face o entrenar uno propio sobre el AnCora Treebank para que la extensión funcione con nuestro idioma.3 Si se logra configurar, la salida se integra en el objeto Doc de spaCy, permitiendo acceder a los constituyentes mediante el atributo .\_.children.6

## **FreeLing y el Motor Txala: Análisis de Potencia Industrial**

FreeLing, desarrollado por la Universitat Politècnica de Catalunya (UPC), ha sido durante décadas el pilar de la lingüística computacional en español.19 Su motor de análisis sintáctico, Txala, es un parser que originalmente se basaba en dependencias pero que, en sus versiones completas (*Full Parsing*), genera una estructura jerárquica profunda que puede convertirse en árboles de constituyentes.20

### **Despliegue y Versiones**

Uno de los mayores desafíos de FreeLing ha sido históricamente su instalación, al estar escrito en C++ con múltiples dependencias. Sin embargo, en el periodo 2024-2026, la disponibilidad de imágenes de Docker pre-configuradas ha democratizado su uso.22 Estas imágenes permiten ejecutar FreeLing en modo servidor, eliminando las limitaciones de las versiones "light" y garantizando el acceso a todas las funcionalidades del motor Txala.23

| Atributo | FreeLing (Txala/Full Parser) |
| :---- | :---- |
| **Arquitectura** | Híbrida (Reglas \+ Estocástica) 21 |
| **Formatos de Salida** | JSON, XML, CoNLL, Texto indentado 24 |
| **Soporte de Docker** | Imágenes oficiales y comunitarias disponibles 22 |
| **Liderazgo Lingüístico** | Especialización extrema en fenómenos del español 19 |

La capacidad de FreeLing para manejar clíticos y ambigüedades morfológicas sigue siendo superior en muchos aspectos a los modelos puramente neuronales, especialmente en textos con estructuras gramaticales complejas o arcaicas.16

## **El AnCora Treebank: El Fundamento de la Investigación Académica**

Cualquier esfuerzo por desarrollar una herramienta de parsing en español debe remitirse al AnCora Treebank. Es el corpus anotado más grande para el español y el catalán, con más de 500,000 palabras.27 La importancia de AnCora para la segmentación fónica radica en su origen: aunque actualmente es muy conocido por su versión en Universal Dependencies (UD), su anotación original se realizó íntegramente en un marco de constituyentes.28

### **Herramientas y Distribución**

Existen herramientas académicas específicas diseñadas para trabajar con el formato XML original de AnCora, permitiendo extraer árboles de constituyentes con funciones sintácticas etiquetadas (como Sujeto, Objeto Directo, etc.).27 Para un desarrollador de librerías, acceder a la versión original de AnCora permite entrenar parsers que no solo identifiquen que un tramo es un "SN", sino que también identifiquen su función dentro de la jerarquía prosódica, algo que los parsers genéricos a veces omiten.27

## **Comparativa Técnica de Motores de Constituyentes (2024-2026)**

Para la toma de decisiones en el desarrollo de una librería de segmentación fónica, se presenta la siguiente tabla comparativa que evalúa los motores investigados bajo los requerimientos técnicos del usuario.

| Motor / Librería | Profundidad del Árbol | Etiquetado POS | Formato de Salida | Facilidad de Despliegue | Mapeo a anytree |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Stanza (Stanford)** | Recursividad Total 14 | Detallado (XPOS) 15 | Penn String / Dict 14 | Alta (pip) 17 | Directo vía dict 5 |
| **FreeLing (Docker)** | Muy Alta 20 | Muy Detallado (EAGLES) 19 | JSON / XML 24 | Media (Docker) 23 | Nativo vía JSON 5 |
| **Benepar (HF)** | Recursividad Total 9 | Depende del Taggeador 18 | Penn String 3 | Media (Modelos ES) 3 | Requiere Parser Penn |
| **spaCy \+ Extension** | Alta 6 | Estándar spaCy 32 | Atributos de Objeto 6 | Media (Modelos HF) | Vía recorrido de hijos |
| **AnCora Native** | Máxima (Gold Standard) | Lingüístico profundo | XML Original 29 | Baja (Uso Académico) | Vía XML Parser 33 |

## **Estrategias de Implementación y Mapeo a Estructuras Anidadas**

Una vez elegido el motor, el desafío técnico reside en convertir la salida (a menudo una cadena con paréntesis tipo LISP o un XML plano) en una estructura recursiva útil para Python.

### **De Penn Treebank a anytree**

La mayoría de los motores (Stanza, Benepar) devuelven el árbol en formato Penn Treebank: (ROOT (S (NP (DT El) (NN niño)) (VP (VB come)))).14

Para integrar esto en una librería de segmentación fónica, se recomienda utilizar un parser intermedio (como el de NLTK o uno basado en expresiones regulares) para transformar la cadena en un diccionario y, posteriormente, utilizar anytree.importer.DictImporter.5 Esto permite acceder a métodos de visualización y búsqueda de nodos críticos para el cálculo de pausas prosódicas.4

### **Procesamiento por Lotes y Servidor**

Para el procesamiento por lotes, tanto Stanza como FreeLing (en Docker) son extremadamente robustos. Stanza permite procesar listas de documentos de manera nativa utilizando GPU si está disponible, mientras que FreeLing puede escalarse horizontalmente mediante múltiples contenedores Docker que respondan a peticiones de un balanceador de carga.3

## **Implicaciones para la Prosodia y la Segmentación Fónica**

La calidad del análisis sintáctico tiene un impacto directo en la detección de los constituyentes mayores (como el límite entre sujeto y predicado) y menores (como la estructura interna de los sintagmas preposicionales). En el español, la entonación se organiza en torno a estos constituyentes:

1. **Fronteras de Constituyente:** Son los puntos más probables para la inserción de pausas silenciosas o el alargamiento de la sílaba final del grupo fónico.1  
2. **Etiquetado POS y Acento:** Las etiquetas POS detalladas permiten distinguir entre palabras funcionales (generalmente átonas) y palabras de contenido (tónicas), información crucial para los algoritmos de síntesis y análisis prosódico.2  
3. **Recursividad y Declinación:** La profundidad del árbol permite modelar cómo la declinación tonal (el descenso gradual de la frecuencia fundamental) se resetea o se mantiene a través de las diferentes capas de la estructura sintáctica.8

## **Conclusiones y Recomendaciones**

Tras la investigación de las opciones disponibles para el periodo 2024-2026, se concluye que:

1. **Stanza es la opción más equilibrada** para una librería en Python que busque facilidad de instalación y una profundidad jerárquica real. Su soporte nativo para el español basado en AnCora y su salida estructurada facilitan enormemente el mapeo a anytree.14  
2. **FreeLing (vía Docker) es la opción de potencia industrial**. Si la librería requiere un análisis lingüístico extremadamente detallado (especialmente para el manejo de clíticos y morfología compleja), FreeLing sigue siendo insuperable, siempre que el desarrollador pueda gestionar el entorno de contenedores.19  
3. **Benepar en Hugging Face es la ruta para la innovación SOTA**. Utilizar implementaciones de Berkeley adaptadas a español con modelos Transformers de última generación proporcionará la mayor precisión estructural, a costa de una mayor complejidad en la configuración inicial.7

El desarrollador debe priorizar motores que garanticen una salida JSON o XML jerárquica, ya que esto reduce la fricción técnica al integrar el análisis sintáctico con los módulos de análisis acústico y prosódico de la librería final.5 La combinación de Stanza para el análisis base y anytree para la gestión de la estructura jerárquica se perfila como la arquitectura de referencia para la segmentación fónica en español en los próximos años.

#### **Obras citadas**

1. Constituent Parsing: A Comprehensive Guide for 2025 \- Shadecoder, fecha de acceso: enero 30, 2026, [https://www.shadecoder.com/topics/constituent-parsing-a-comprehensive-guide-for-2025](https://www.shadecoder.com/topics/constituent-parsing-a-comprehensive-guide-for-2025)  
2. A Comprehensive Guide to Parsing: Constituency and Dependency Parsing \- Medium, fecha de acceso: enero 30, 2026, [https://medium.com/@vashwin22comp/a-comprehensive-guide-to-parsing-constituency-and-dependency-parsing-ad29bd932dc1](https://medium.com/@vashwin22comp/a-comprehensive-guide-to-parsing-constituency-and-dependency-parsing-ad29bd932dc1)  
3. benepar \- PyPI, fecha de acceso: enero 30, 2026, [https://pypi.org/project/benepar/](https://pypi.org/project/benepar/)  
4. Any Python Tree Data — anytree documentation, fecha de acceso: enero 30, 2026, [https://anytree.readthedocs.io/](https://anytree.readthedocs.io/)  
5. Dictionary Importer — anytree documentation \- Read the Docs, fecha de acceso: enero 30, 2026, [https://anytree.readthedocs.io/en/latest/importer/dictimporter.html](https://anytree.readthedocs.io/en/latest/importer/dictimporter.html)  
6. Berkeley Neural Parser · spaCy Universe, fecha de acceso: enero 30, 2026, [https://spacy.io/universe/project/self-attentive-parser](https://spacy.io/universe/project/self-attentive-parser)  
7. Multilingual Constituency Parsing with Self-Attention and Pre-Training \- The Berkeley NLP Group, fecha de acceso: enero 30, 2026, [https://nlp.cs.berkeley.edu/pubs/Kitaev-Cao-Klein\_2019\_MultilingualParsing\_paper.pdf](https://nlp.cs.berkeley.edu/pubs/Kitaev-Cao-Klein_2019_MultilingualParsing_paper.pdf)  
8. Improving Constituency Parsing with Span Attention \- ACL Anthology, fecha de acceso: enero 30, 2026, [https://aclanthology.org/2020.findings-emnlp.153.pdf](https://aclanthology.org/2020.findings-emnlp.153.pdf)  
9. Berkeley Neural Parser, fecha de acceso: enero 30, 2026, [https://parser.kitaev.io/](https://parser.kitaev.io/)  
10. nikitakit/self-attentive-parser: High-accuracy NLP parser ... \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/nikitakit/self-attentive-parser](https://github.com/nikitakit/self-attentive-parser)  
11. Assessment of Pre-Trained Models Across Languages and Grammars \- Hugging Face, fecha de acceso: enero 30, 2026, [https://huggingface.co/papers/2309.11165](https://huggingface.co/papers/2309.11165)  
12. Paper page \- Fast and Accurate Neural CRF Constituency Parsing \- Hugging Face, fecha de acceso: enero 30, 2026, [https://huggingface.co/papers/2008.03736](https://huggingface.co/papers/2008.03736)  
13. High-Accuracy Transition-Based Constituency Parsing \- ACL Anthology, fecha de acceso: enero 30, 2026, [https://aclanthology.org/2025.iwpt-1.4.pdf](https://aclanthology.org/2025.iwpt-1.4.pdf)  
14. Constituency Parser \- Stanza, fecha de acceso: enero 30, 2026, [https://stanfordnlp.github.io/stanza/constituency.html](https://stanfordnlp.github.io/stanza/constituency.html)  
15. Models \- Stanza \- Stanford NLP Group, fecha de acceso: enero 30, 2026, [https://stanfordnlp.github.io/stanza/models.html](https://stanfordnlp.github.io/stanza/models.html)  
16. PoetryLab as Infrastructure for the Analysis of Spanish Poetry \- Semantic Scholar, fecha de acceso: enero 30, 2026, [https://pdfs.semanticscholar.org/bca2/030c4eb3499d9ca408d135c0adc06981cd0f.pdf](https://pdfs.semanticscholar.org/bca2/030c4eb3499d9ca408d135c0adc06981cd0f.pdf)  
17. Stanford Stanza sometimes splits a sentence into two sentences \- Stack Overflow, fecha de acceso: enero 30, 2026, [https://stackoverflow.com/questions/77840651/stanford-stanza-sometimes-splits-a-sentence-into-two-sentences](https://stackoverflow.com/questions/77840651/stanford-stanza-sometimes-splits-a-sentence-into-two-sentences)  
18. Adding a new Constituency model \- Stanza \- Stanford NLP Group, fecha de acceso: enero 30, 2026, [https://stanfordnlp.github.io/stanza/new\_language\_constituency.html](https://stanfordnlp.github.io/stanza/new_language_constituency.html)  
19. Welcome | FreeLing Home Page \- TALP \- UPC, fecha de acceso: enero 30, 2026, [https://nlp.lsi.upc.edu/freeling/node/1](https://nlp.lsi.upc.edu/freeling/node/1)  
20. Student Research Workshop associated with RANLP 2011 \- ACL Anthology, fecha de acceso: enero 30, 2026, [https://aclanthology.org/R11-2.pdf](https://aclanthology.org/R11-2.pdf)  
21. Towards Robustness in Natural Language Understanding \- Jordi Atserias Batalla, fecha de acceso: enero 30, 2026, [https://jordi.atserias.cat/publications/2006/phd\_atserias\_300506.pdf](https://jordi.atserias.cat/publications/2006/phd_atserias_300506.pdf)  
22. malev/docker-freeling: Dockerfile for FreeLing 3.1 \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/malev/docker-freeling](https://github.com/malev/docker-freeling)  
23. d4n13lbc/docker-freeling \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/d4n13lbc/docker-freeling](https://github.com/d4n13lbc/docker-freeling)  
24. Using \`\`analyzer\`\` Program to Process Corpora \- FreeLing 4.1 User Manual, fecha de acceso: enero 30, 2026, [https://freeling-user-manual.readthedocs.io/en/v4.1/analyzer/](https://freeling-user-manual.readthedocs.io/en/v4.1/analyzer/)  
25. SAQL: Query Language for Corpora with morpho-syntactic annotation, fecha de acceso: enero 30, 2026, [https://repositorium.uminho.pt/bitstreams/a5cd57f4-1754-4c34-9d64-e02a1508c161/download](https://repositorium.uminho.pt/bitstreams/a5cd57f4-1754-4c34-9d64-e02a1508c161/download)  
26. Usage | FreeLing Home Page, fecha de acceso: enero 30, 2026, [https://nlp.lsi.upc.edu/freeling/taxonomy/term/3](https://nlp.lsi.upc.edu/freeling/taxonomy/term/3)  
27. AnCora: Multilevel Annotated Corpora for Catalan and Spanish. \- ResearchGate, fecha de acceso: enero 30, 2026, [https://www.researchgate.net/publication/220746393\_AnCora\_Multilevel\_Annotated\_Corpora\_for\_Catalan\_and\_Spanish](https://www.researchgate.net/publication/220746393_AnCora_Multilevel_Annotated_Corpora_for_Catalan_and_Spanish)  
28. UD\_Spanish-AnCora \- Universal Dependencies, fecha de acceso: enero 30, 2026, [https://universaldependencies.org/treebanks/es\_ancora/index.html](https://universaldependencies.org/treebanks/es_ancora/index.html)  
29. PlanTL-GOB-ES/UD\_Spanish-AnCora · Datasets at Hugging Face, fecha de acceso: enero 30, 2026, [https://huggingface.co/datasets/PlanTL-GOB-ES/UD\_Spanish-AnCora](https://huggingface.co/datasets/PlanTL-GOB-ES/UD_Spanish-AnCora)  
30. The IULA Spanish LSP Treebank \- SciSpace, fecha de acceso: enero 30, 2026, [https://scispace.com/pdf/the-iula-spanish-lsp-treebank-3ewl5fh1vn.pdf](https://scispace.com/pdf/the-iula-spanish-lsp-treebank-3ewl5fh1vn.pdf)  
31. UniversalDependencies/UD\_Spanish-AnCora: Spanish data from the AnCora corpus. \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/UniversalDependencies/UD\_Spanish-AnCora](https://github.com/UniversalDependencies/UD_Spanish-AnCora)  
32. Spanish · spaCy Models Documentation, fecha de acceso: enero 30, 2026, [https://spacy.io/models/es](https://spacy.io/models/es)  
33. Parsing XML with Python \- NetworkAcademy.IO, fecha de acceso: enero 30, 2026, [https://www.networkacademy.io/ccna-automation/data-formats/parsing-xml-with-python](https://www.networkacademy.io/ccna-automation/data-formats/parsing-xml-with-python)  
34. how could I use complete penn treebank dataset inside python/nltk \- Stack Overflow, fecha de acceso: enero 30, 2026, [https://stackoverflow.com/questions/36079383/how-could-i-use-complete-penn-treebank-dataset-inside-python-nltk](https://stackoverflow.com/questions/36079383/how-could-i-use-complete-penn-treebank-dataset-inside-python-nltk)  
35. Tree Rendering — anytree documentation \- Read the Docs, fecha de acceso: enero 30, 2026, [https://anytree.readthedocs.io/en/latest/api/anytree.render.html](https://anytree.readthedocs.io/en/latest/api/anytree.render.html)  
36. Notebook for the BioASQ Task GutBrainIE on Gut-Brain Interplay Information Extraction at CLEF 2025 \- CEUR-WS.org, fecha de acceso: enero 30, 2026, [https://ceur-ws.org/Vol-4038/paper\_13.pdf](https://ceur-ws.org/Vol-4038/paper_13.pdf)  
37. Working with JSON and XML files in Python (Elements of Computing II, S21, University of Notre Dame) \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/kwaldenphd/json-xml-python](https://github.com/kwaldenphd/json-xml-python)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAAYCAYAAAD3Va0xAAAAvElEQVR4XmNgGAWkAmsg/o8Fw8B3LHK8SPIYQIEBoug5ELMhiQsC8SMgFkMSIwj8GCCG7YbyWYB4JRAzw1UQCZgYEM5nBOKlDKiuIwnADLoFxBJociSBXQwQgwrRJUgFf4H4EwPEMD00OaKBKxCXA3ErA8SgKajSxIEnQFyJxEdPT0QBUBppQRMj2aC1QHwEXZAB4jqQQQvQxFEAKI1EA3EVA0TxWVRpBj4gXgiVA2WRcCAWRlExCkYBlQAAUD8s5y1xrpcAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFIAAAAZCAYAAACis3k0AAACK0lEQVR4Xu2XTUhVQRTHj2kEmpT4AeIiQUsLBAu/aKHYXnDhwp1BoQbtggxaBZGLFrZplyhSiEhRJAgKoQvdiLjrE2oRhqCLalHQpv5/zlzecJ5eP7qPWzI/+MHMOXPnvhnPm3mKBAKBQCAQCAQCgdQphSuwBjbAX/A+rITt8G5m6KHhCJyHzXAa/obvYSv8ABczQ/fOArzn9Tnpd3gCfoEvvdxhgcVx1LU7RNfc7fps/3DtfXHG9DnRFROLOA4fwp828R9RAlu8/iPRNSdKveiktTYBTsMt0WMg8RenyGfJwXr64ScbNIxJDl6cIlxLIuv5CJ/DY/Ab7PVyrMIqr0/iNrIMXrBBw21YbYMeffC6DXrwq3nTBg11kv25I87DZdHPSrgWHlcRb2GPa/PCfQO74BR8AQddLgtOtAavuvZFF+dh/Coa5DEqO28kPwQPah4R21Eu+izH7cRuFfJMNN9kE45Tor88XkvmQvGZFH2eG33WtW95+VXRW50MwwdwEza6WPRsFkuil0eb68+KViYvnPxokEdcRQ6JnjmPbcJRIPrsiE14bEj8rTkgOsdJm3DwHTNwXXSspQI+FT3vL4tWLzeXG8+Ni8iD50TneeLF+Ytmuz/QvonbSHIDTthgCvC44rfsb+Fa/aOG8ybCbhvJ6ubZkjbvbOCAfBWtcnIHFsNLmfTBYZnHbeS/UI2Fkkw1Ev8fknFYBOe8WE7otIGUuGYDgUAgEEiHP5OUbLW6bRhkAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAYCAYAAADKx8xXAAAAyklEQVR4XmNgwA84gHgjEDOiS+AD3ED8AIg1gPg/EPehyOIBe4BYAcqOA+KfCKmBBJUMEH9MBuJMIHYA4iqo2Akg9gLiBCDeARXjAmkCgZNAfBbGgYJYBoiiLCQxJgaIQXCwG5kDBaeB+CW6IBDMQ+ZkIHOAQIgBYtt6NHEQ2IcugAw6GSAaHdDECYJDDBCNoJRDEgBpAmGSAVkaWRggms6jSxACdgwQjVPRJQgBUBSANEqhSxACL4D4FrogLgALDGy4GkndKKApAABcmy020xGcYAAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,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>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD8AAAAZCAYAAACGqvb0AAACs0lEQVR4Xu2YS6hOURiGX/f7xFEMXGIoGYhSbhO55DJxKbkMMDAiIqWTQ5SkFGWAgYmiUFLkNhKFolAuMZMBBgZCKfG9/9rbv/Zrr7X/vfdJP/1PvZ193m9/a+2191rfWucAHTqUYbDpupptyjY16vLBNFbNNmWd6YuaVZlp2q5mLzPJdEjNAnpMt0wvTM8kdtfUT7zSzDH9VNNjP1x8uQZKchblB5/C/neI18f0Fm65VoYP9VVNj1mmm2r+RabCDX6aBuD83WqWgQ0cUbONuAT3gfJ4jfisLYTJLCDtCKf2J9NGDSRcRMHg35lOmUaYFpi6s+FG8mTxyBPTCdNHFHQQ4Y5pr2kxXBv9s+FCdiLe9x5E4qyGr+DeIDlmut0MN2DyGPHIZbg81oNgBwUcTX7OgGtjtBdrhauI970FkTiLBIP8iktME7LhxqDz9kt/C2F+j/d7q3R51xcQecgIzPmhpsdCRNrlNGMwlQ6U2wT9vuKnjIeLT9RASd4j8pARmHNfTY8VKGj3MNxBIX0BA7PhhjdKvBSuKebWJe27LMzh84fYhEC72iHX7zfTEM8jvGe6eCSdUun9/nY4CK6ItQrbOaOmsR7hduabvpuGmx6ZlmbDDQ4iMnhOt5R5iafQW6OmcRrN+6cgO/VPJrFVnhdiGNy9azWAPz+Qz2bT4+T6M9xupZxHIH+c6Thc4nPTsmz4N0x+qKYx0nQPLnerxLhl8mjJQ0YRrPihdcudhO2EeAD39YdqIIHPXmtZ3kC8ooaYbXqpZg5PTQfU9GA7VeHgV6tZFq6pAWoW8Aau2iob0Jzm55LrEOyT7VSBNYEHqNqsTFQGfvW8E9s+uNhcuIGnB508dqG12ZMHXyyLYa9wxXRNzQB5J8Iq8PhaBf7jZZGadWBR4fr/F6j1Z2yHDv8ZvwA/xJeATA2S1wAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAZCAYAAAD9jjQ4AAAAbUlEQVR4XmNgGOSAEYj/A/FmdAkY2AjECuiC5IHXQOwPxHlA3IcmxxAJpcuAeCWyhCiUtmGAuJQHSQ4OOhkgkhgA5L87DDgkFzBAJJqA2AyIXyBLfoVKagPxGiBuRJb0AuJ3QPwJiKWRJUYCAAD4kxPDsM77+gAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAaCAYAAABl03YlAAAAmElEQVR4XmNgGFpgFhCXoAuig/9A/AJdcABACxA/BeKPQKyAKgUBLEDcC8RcQOwFxAdQZIGAD4hfIfGzgfguEh8MOIHYAom/DIjnIPExgC4DJIzE0SWQQR4DRBFOwAzEHxgIKLJmgCj4jS6BDGoZIIqOoUsoArEUlP2LAaJIDyENAT8ZICENAiAFfUhycNDEAHHDGnSJIQ8AliAbhmDOcF0AAAAASUVORK5CYII=>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAYAAAAZCAYAAAASTF8GAAAAbUlEQVR4XmNgoB+QB+LdQHwYiJ+hyYHBfyD+hi4IAiCJ7eiCulAJY3SJXCB+DcSMyIIgDkgwCVkQBMwYIMbIoUtshUpggK8MOCRAgn/RBUEAJNEJxB5AfAFdIhyIl0IVwMF0IH4BxGHIgsMBAACJghglpd/dywAAAABJRU5ErkJggg==>