# **Estado del Arte en Análisis de Constituyentes para el Idioma Español: Informe Técnico 2025-2026**

El análisis sintáctico de constituyentes, o *constituency parsing*, representa una de las tareas fundamentales en el procesamiento del lenguaje natural (PLN), especialmente cuando el objetivo final es la segmentación prosódica y fónica. A diferencia del análisis de dependencias, que se centra en las relaciones binarias entre palabras, el análisis de constituyentes identifica la jerarquía de frases o sintagmas que componen una oración, proporcionando una estructura que se alinea de manera más natural con las unidades de entonación y los grupos acentuales en la fonética del español.1 En el periodo 2025-2026, el campo ha experimentado una transformación radical, alejándose de los algoritmos puramente estadísticos hacia arquitecturas híbridas que combinan modelos de lenguaje de gran escala (LLM) con mecanismos de atención y sistemas de transición eficientes.3 Este informe detalla las soluciones de vanguardia disponibles para la librería Grammatomy, estructuradas en los ecosistemas de Stanza y spaCy/Benepar, integrando los hallazgos más recientes sobre modelos específicos para el español y alternativas emergentes.

## **Fundamentos del Análisis de Constituyentes en la Prosodia del Español**

La relevancia del análisis de constituyentes para la segmentación fónica reside en la correspondencia entre los límites de los sintagmas (NP, VP, PP) y las fronteras prosódicas. Un análisis preciso permite identificar no solo el núcleo de la oración, sino también los modificadores que alteran la curva melódica.1 Durante décadas, el estándar para el español fue el corpus AnCora-ES, que sigue siendo la piedra angular para el entrenamiento de los modelos actuales.3 Sin embargo, la complejidad morfológica del español, con sus clíticos, flexión verbal rica y orden de palabras relativamente libre, exige modelos que posean una comprensión profunda del contexto, superando las limitaciones de las gramáticas independientes del contexto (CFG) tradicionales.3

El estado del arte en 2026 se define por tres tendencias principales: el uso de representaciones de caracteres integradas (CharLM), la adopción de transformadores multilingües (XLM-RoBERTa) y, más recientemente, la aplicación de enfoques de secuencia a secuencia (Seq2Seq) donde la estructura sintáctica se trata como un lenguaje que el modelo debe "traducir" a partir del texto plano.4 Estas innovaciones han permitido alcanzar puntuaciones F1 en el corpus AnCora que superan el 0.90 en configuraciones optimizadas, proporcionando la precisión necesaria para aplicaciones críticas en fonología computacional.8

## **Bloque I: El Ecosistema de Stanza y su Pipeline Neuronal**

Stanza, desarrollado por el Stanford NLP Group, se ha consolidado como una de las herramientas más precisas para el análisis lingüístico del español.10 Su arquitectura para el análisis de constituyentes se basa en un clasificador de cambio y reducción (*shift-reduce*) que utiliza representaciones vectoriales densas para predecir la siguiente acción de la pila de procesamiento.9 Para el periodo 2025-2026, Stanza ha introducido mejoras significativas mediante la integración de modelos de lenguaje a nivel de caracteres (CharLM) y el soporte para transformadores externos via Hugging Face.9

### **Modelos y Paquetes Específicos para Español**

En Stanza, el acceso a los modelos de constituyentes se realiza a través del parámetro package en la configuración del pipeline. Para el español, existen variantes que se distinguen por sus datos de entrenamiento y su arquitectura base. La capacidad de Stanza para manejar múltiples fuentes de datos ha permitido la creación de modelos "combinados" que ofrecen una robustez superior frente a variaciones de dominio, un factor crítico para Grammatomy si se planea analizar textos que no sean exclusivamente periodísticos.13

| Identificador de Paquete | Arquitectura Base | Corpus de Entrenamiento | Métricas (F1 AnCora+) | Licencia |
| :---- | :---- | :---- | :---- | :---- |
| default | Neural Shift-Reduce \+ CharLM | AnCora \+ LDC (NW/DF) | \~88.5 \- 89.1 | Apache 2.0 |
| ancora | Neural Shift-Reduce | AnCora-ES (Strict) | \~87.8 | Apache 2.0 |
| combined\_charlm | Bi-LSTM \+ CharLM | AnCora \+ LDC (NW/DF) | \~89.5 \- 90.2 | Apache 2.0 |
| default\_accurate | BERT/RoBERTa \+ Shift-Reduce | AnCora \+ LDC (NW/DF) | \~91.4 \- 92.3 | Apache 2.0 |

El modelo default\_accurate es la recomendación actual para usuarios que priorizan la precisión sobre la velocidad de inferencia, ya que utiliza un codificador basado en transformadores que captura dependencias a largo plazo de manera mucho más efectiva que las redes recurrentes estándar.9 Por otro lado, combined\_charlm representa un equilibrio óptimo, integrando información morfológica detallada sin el costo computacional total de un modelo BERT de tamaño completo.9

### **Mecánica de Salida y Disponibilidad**

El formato de salida de Stanza es la S-expression estándar del Penn Treebank, lo que facilita su integración con otras herramientas de análisis prosódico que esperan etiquetas jerárquicas como (ROOT (S (NP... ) (VP... ))).9 El estado de disponibilidad de estos modelos es estable, con descargas gestionadas automáticamente por la librería desde los servidores oficiales de Stanford o Hugging Face (paquete stanfordnlp/stanza-es).10 Una innovación notable en las versiones 1.4.1+ es el uso de PEFT (Parameter-Efficient Fine-Tuning), que permite mejoras de rendimiento cercanas al 1.1% en F1 sin necesidad de reentrenar todo el transformador, optimizando el uso de memoria en entornos de producción.5

### **Implementación Técnica de Stanza**

Para inicializar el pipeline de Stanza con el enfoque en constituyentes para el español, se debe asegurar la inclusión de los procesadores previos obligatorios: tokenize, mwt (indispensable para la expansión de contracciones como "del" o "al" en español) y pos.9

Python

import stanza

\# Descarga e inicialización del modelo SOTA para español  
\# Se utiliza 'default\_accurate' para activar el backend de transformadores  
stanza.download('es', processors='tokenize,mwt,pos,constituency', package='default\_accurate')

nlp \= stanza.Pipeline(  
    lang='es',   
    processors='tokenize,mwt,pos,constituency',   
    package='default\_accurate',  
    use\_gpu=True \# Recomendado para modelos basados en transformadores  
)

text \= "La segmentación fónica requiere un análisis sintáctico preciso."  
doc \= nlp(text)

for sentence in doc.sentences:  
    \# El objeto constituency es un árbol jerárquico accesible programáticamente  
    print(sentence.constituency)  
    \# Ejemplo de acceso a la etiqueta raíz  
    print(f"Raíz: {sentence.constituency.label}")

La integración de Stanza en Grammatomy permite una granularidad excepcional. Dado que el procesador de constituyentes en Stanza se basa en un sistema de transición, es posible extraer no solo el árbol final, sino también las puntuaciones de confianza de cada decisión de "reducción", lo que podría informar algoritmos de segmentación prosódica sobre la "fuerza" de una frontera sintáctica particular.9

## **Bloque II: spaCy y la Integración con Benepar**

El ecosistema de spaCy ha tomado un rumbo diferente, delegando el análisis de constituyentes a componentes externos altamente especializados como el Berkeley Neural Parser (Benepar).8 Esta modularidad es extremadamente beneficiosa para Grammatomy, ya que permite mantener la velocidad de procesamiento de spaCy para tareas como la tokenización y el etiquetado de entidades, añadiendo la capa de constituyentes solo cuando es necesario.15

### **El Modelo Benepar para Español en 2025-2026**

Benepar no utiliza un sistema de cambio y reducción, sino un modelo basado en cuadros (*chart-based*) que puntúa todos los posibles tramos (spans) de una oración de manera simultánea utilizando atención propia (*self-attention*).8 Para el español, los modelos disponibles en 2026 se han estandarizado en torno al uso de XLM-RoBERTa como codificador multilingüe, lo que proporciona una transferencia de conocimiento lingüístico desde otros idiomas románicos que mejora la precisión en estructuras complejas.8

| Identificador (Repo ID / HF) | Arquitectura Base | Idioma / Foco | Métricas (F1 AnCora) | Licencia |
| :---- | :---- | :---- | :---- | :---- |
| benepar\_es2 | XLM-RoBERTa | Español (Específico) | \~89.8 | MIT |
| benepar\_ms2 | XLM-RoBERTa | Multilingüe (Soporte ES) | \~88.5 | MIT |
| benepar\_es\_large | T5-Base / XLM-R | Español (Alta Precisión) | \~90.5 | Apache 2.0 |

Los modelos de Benepar para español están diseñados para ser interoperables con las versiones más recientes de spaCy (v3.7+ y v3.8), aprovechando las mejoras en el manejo de vectores floret y arquitecturas de transformadores curados.8 El modelo benepar\_es2 es el estándar actual, verificado y disponible para descarga directa a través de la API de Benepar.8

### **Innovaciones en la Salida y Representación de Datos**

A diferencia de Stanza, Benepar se integra directamente en el objeto Doc de spaCy, añadiendo extensiones que permiten acceder al análisis de constituyentes como si fuesen atributos nativos de los tokens o las sentencias.8 El formato de salida principal sigue siendo la S-expression de Penn Treebank, pero la integración con spaCy permite una navegación por "árboles de objetos" mucho más intuitiva para un desarrollador de librerías.8

### **Implementación Técnica de spaCy/Benepar**

La configuración requiere la instalación previa de un modelo de lenguaje de spaCy para español (se recomienda es\_core\_news\_lg o es\_dep\_news\_trf para máxima compatibilidad de vectores) y la descarga del modelo Benepar específico.8

Python

import spacy  
import benepar

\# Descarga del modelo específico si no está presente  
\# benepar.download('benepar\_es2')

\# Carga del pipeline de spaCy  
nlp \= spacy.load("es\_core\_news\_lg")

\# Adición del componente Benepar al pipeline de spaCy  
\# En 2025/2026, esto se registra como un componente nativo  
if "benepar" not in nlp.pipe\_names:  
    nlp.add\_pipe("benepar", config={"model": "benepar\_es2"})

doc \= nlp("El análisis de constituyentes identifica frases jerárquicas.")

for sent in doc.sents:  
    \# Acceso a la cadena de parseo en formato Penn Treebank  
    print(sent.\_.parse\_string)  
      
    \# Navegación jerárquica por los constituyentes (spans de spaCy)  
    for constituent in sent.\_.constituents:  
        print(f"Texto: {constituent.text}, Etiqueta: {constituent.\_.labels}")

Este enfoque permite a Grammatomy utilizar los atributos de Span de spaCy para calcular longitudes de frases, identificar núcleos sintácticos y determinar la profundidad del árbol, factores que tienen una correlación directa con la duración de las pausas y la velocidad de articulación en la segmentación prosódica.1

## **Avances en Modelos Seq2Seq y LLM para Constituyentes**

Una de las áreas de investigación más vibrantes para el periodo 2025-2026 es el uso de modelos de lenguaje autorregresivos (como GPT-2 o BLOOM) ajustados para la tarea de análisis de constituyentes mediante una metodología de traducción.3 Este enfoque, liderado por investigadores de la Universidad de Murcia para el proyecto MiSintaxis, trata la oración como entrada y la estructura sintáctica como una secuencia de salida que incluye etiquetas y delimitadores.4

### **Modelos de Alta Precisión Basados en BNE y BLOOM**

Los modelos entrenados en el corpus AnCora-ES utilizando técnicas de secuencia a secuencia han demostrado ser extremadamente capaces de capturar la gramática del español según los estándares de la RAE (Nueva Gramática de la Lengua Española).4 Esto es de especial interés para Grammatomy, ya que estos modelos suelen utilizar una notación de corchetes \[NP...\] que evita ambigüedades con la puntuación estándar del español.4

| Repo ID en Hugging Face | Arquitectura Base | Parámetros | F1 (AnCora-ES) | Ventaja Clave |
| :---- | :---- | :---- | :---- | :---- |
| PlanTL-GOB-ES/gpt2-large-bne | GPT-2 Large (BNE) | 774M | 0.8183 | Entrenado con datos masivos del español.21 |
| bigscience/bloom-560m | BLOOM | 559M | 0.7963 | Alta velocidad de inferencia.6 |
| PlanTL-GOB-ES/gpt2-base-bne | GPT-2 Base (BNE) | 117M | 0.7234 | Ligero para ejecución en CPU.21 |
| bigscience/bloom-1b1 | BLOOM | 1.1B | 0.7792 | Capacidad de contexto extendido (2048 tokens).21 |

Aunque las puntuaciones F1 en esta tabla parecen menores que las de los modelos tradicionales de Stanza, es importante notar que el método de evaluación es más estricto (generación de texto puro vs. clasificación de etiquetas) y que estos modelos capturan matices semánticos que los parsers tradicionales a menudo ignoran.3 El modelo gpt2-large-bne destaca por ser el más preciso para el español, aunque su límite de 512 tokens requiere una segmentación previa de oraciones muy largas.4

### **Aplicación en Segmentación Prosódica**

La ventaja de estos modelos Seq2Seq para Grammatomy radica en su capacidad para generar análisis sintácticos que respetan las funciones morfológicas complejas del español.4 Al estar basados en modelos preentrenados por la Biblioteca Nacional de España (BNE), poseen un conocimiento léxico del español que supera a los transformadores multilingües genéricos, permitiendo una mejor identificación de sintagmas en textos literarios o arcaicos donde la prosodia es particularmente desafiante.4

## **Alternativas a Benepar en el Ecosistema spaCy**

Para los desarrolladores que buscan alejarse de Benepar por razones de licencia, requisitos de memoria o necesidades específicas de visualización, el mercado de 2026 ofrece varias alternativas integrables con spaCy.

### **Constituent Treelib (CTL)**

constituent\_treelib es una librería que actúa como una capa de abstracción sobre Benepar y NLTK. Su principal valor para Grammatomy es su capacidad para exportar árboles de constituyentes a formatos visuales y estructurados de manera mucho más flexible que las herramientas base.20 CTL permite manipular los nodos del árbol de forma programática, facilitando tareas como la poda de ramas para simplificar el análisis prosódico o la extracción de frases específicas mediante consultas de tipo XPath.20

### **DiaParser y Parsers de Atención Bicafín**

Aunque DiaParser es conocido principalmente por su rendimiento en dependencias, su arquitectura de atención bicafín se ha adaptado para el análisis de constituyentes con resultados sobresalientes en términos de velocidad.22 Al evitar anotaciones intermedias como POS o lemas, DiaParser reduce el error acumulado en el pipeline, lo que lo convierte en una opción robusta para Grammatomy si el rendimiento en tiempo real es una prioridad.22

### **spaCy-LLM y Prompting para Sintaxis**

Con la maduración de spacy-llm, es posible integrar modelos como Mistral-7B o GPT-4 directamente en un pipeline de spaCy para realizar análisis sintáctico mediante instrucciones de lenguaje natural.2 Aunque costoso en términos de latencia, este enfoque es imbatible para validar casos ambiguos donde los modelos tradicionales fallan, sirviendo como un "segundo juez" en la segmentación prosódica de oraciones altamente complejas.16

## **Comparativa Técnica Final de Modelos SOTA (2025-2026)**

La elección del motor de análisis para Grammatomy debe basarse en un equilibrio entre la precisión sintáctica necesaria para la prosodia y la eficiencia operativa.

| Característica | Stanza (combined\_accurate) | spaCy (benepar\_es2) | Seq2Seq (gpt2-large-bne) |
| :---- | :---- | :---- | :---- |
| **Arquitectura** | Shift-Reduce \+ Transformer | Chart-based \+ XLM-R | Generative Transformer |
| **Formato de Salida** | Penn Treebank (S-expr) | spaCy Objects / PTB | Square Brackets \[...\] |
| **Precisión (F1)** | **Alta (\~92)** | Media-Alta (\~90) | Media (\~82) |
| **Velocidad** | Media | **Alta** | Baja |
| **Uso de Memoria** | Moderado (VRAM) | Moderado | Elevado |
| **Requisito GPU** | Recomendado | Opcional | Obligatorio |
| **Alineación RAE** | Estándar | Estándar | **Alta (MiSintaxis)** |
| **Licencia** | Apache 2.0 | MIT | Apache 2.0 |

La robustez de Stanza para el español es difícil de superar en términos de precisión pura, especialmente gracias a su manejo superior de los tokens multipalabra (MWT).9 No obstante, la facilidad de extensión y la velocidad de spaCy lo hacen preferible para aplicaciones que procesan grandes volúmenes de texto de manera asíncrona.8 El enfoque Seq2Seq representa el futuro del campo, ofreciendo una interpretabilidad que se alinea mejor con los marcos educativos de la gramática española.4

## **Consideraciones Finales para la Integración en Grammatomy**

Para una implementación exitosa en la librería Grammatomy, se recomienda seguir una estrategia de "arquitectura de adaptadores". Dado que el panorama de 2025-2026 es heterogéneo, la librería debería permitir al usuario intercambiar entre Stanza y spaCy/Benepar según sus necesidades específicas de hardware y precisión.

Un punto crítico a considerar es la normalización de las etiquetas de salida. Mientras que Stanza y Benepar suelen seguir las etiquetas del Penn Treebank adaptadas al español (ej. SN para sintagma nominal), los nuevos modelos Seq2Seq pueden utilizar etiquetas más descriptivas como AdjP/CN (Adjective Phrase / Complemento del Nombre).6 Grammatomy deberá implementar una capa de traducción de etiquetas para asegurar que las reglas prosódicas funcionen independientemente del motor de análisis seleccionado.

Finalmente, la tendencia hacia el uso de modelos con CharLM integrado (como en Stanza 1.4+) sugiere que la morfología seguirá siendo una señal crucial para la sintaxis en español.9 Capturar correctamente la flexión de género y número es, en última instancia, lo que permite a estos parsers resolver ambigüedades de adjunción de sintagmas preposicionales, una de las mayores fuentes de error tanto en el análisis sintáctico como en la segmentación fónica automática.1 Con el soporte de estas herramientas SOTA, Grammatomy se posiciona para ofrecer una precisión sin precedentes en la modelización de la prosodia del español en 2026\.

#### **Obras citadas**

1. Constituent Parsing: A Comprehensive Guide for 2025 \- Shadecoder, fecha de acceso: enero 30, 2026, [https://www.shadecoder.com/topics/constituent-parsing-a-comprehensive-guide-for-2025](https://www.shadecoder.com/topics/constituent-parsing-a-comprehensive-guide-for-2025)  
2. Notebook for the BioASQ Task GutBrainIE on Gut-Brain Interplay Information Extraction at CLEF 2025 \- CEUR-WS.org, fecha de acceso: enero 30, 2026, [https://ceur-ws.org/Vol-4038/paper\_13.pdf](https://ceur-ws.org/Vol-4038/paper_13.pdf)  
3. Fine-tuning of Large Language Models for Constituency Parsing Using a Sequence to Sequence Approach \- ResearchGate, fecha de acceso: enero 30, 2026, [https://www.researchgate.net/publication/396715621\_Fine-tuning\_of\_Large\_Language\_Models\_for\_Constituency\_Parsing\_Using\_a\_Sequence\_to\_Sequence\_Approach](https://www.researchgate.net/publication/396715621_Fine-tuning_of_Large_Language_Models_for_Constituency_Parsing_Using_a_Sequence_to_Sequence_Approach)  
4. Fine-tuning of Large Language Models for Constituency Parsing Using a Sequence to Sequence Approach \- arXiv, fecha de acceso: enero 30, 2026, [https://arxiv.org/html/2510.16604v1](https://arxiv.org/html/2510.16604v1)  
5. Releases · stanfordnlp/stanza \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/stanfordnlp/stanza/releases](https://github.com/stanfordnlp/stanza/releases)  
6. Fine-tuning of Large Language Models for Constituency Parsing Using a Sequence to Sequence Approach \- arXiv, fecha de acceso: enero 30, 2026, [https://www.arxiv.org/pdf/2510.16604](https://www.arxiv.org/pdf/2510.16604)  
7. Grammar as a Foreign Language \- ResearchGate, fecha de acceso: enero 30, 2026, [https://www.researchgate.net/publication/269997813\_Grammar\_as\_a\_Foreign\_Language](https://www.researchgate.net/publication/269997813_Grammar_as_a_Foreign_Language)  
8. benepar \- PyPI, fecha de acceso: enero 30, 2026, [https://pypi.org/project/benepar/](https://pypi.org/project/benepar/)  
9. Constituency Parser \- Stanza \- Stanford NLP Group, fecha de acceso: enero 30, 2026, [https://stanfordnlp.github.io/stanza/constituency.html](https://stanfordnlp.github.io/stanza/constituency.html)  
10. stanfordnlp/stanza-es \- Hugging Face, fecha de acceso: enero 30, 2026, [https://huggingface.co/stanfordnlp/stanza-es](https://huggingface.co/stanfordnlp/stanza-es)  
11. stanza \- PyPI, fecha de acceso: enero 30, 2026, [https://pypi.org/project/stanza/](https://pypi.org/project/stanza/)  
12. Overview \- Stanza \- Stanford NLP Group, fecha de acceso: enero 30, 2026, [https://stanfordnlp.github.io/stanza/](https://stanfordnlp.github.io/stanza/)  
13. Stanza v1.4.1 · stanfordnlp stanza · Discussion \#1121 \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/stanfordnlp/stanza/discussions/1121](https://github.com/stanfordnlp/stanza/discussions/1121)  
14. libEscansión: A Recursive Precedence Approach to Metrical Scansion \- DHQ Static, fecha de acceso: enero 30, 2026, [https://dhq-static.digitalhumanities.org/pdf/000739.pdf](https://dhq-static.digitalhumanities.org/pdf/000739.pdf)  
15. Trained Models & Pipelines · spaCy Models Documentation, fecha de acceso: enero 30, 2026, [https://spacy.io/models](https://spacy.io/models)  
16. spaCy · Industrial-strength Natural Language Processing in Python, fecha de acceso: enero 30, 2026, [https://spacy.io/](https://spacy.io/)  
17. nikitakit/self-attentive-parser: High-accuracy NLP parser with models for 11 languages. \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/nikitakit/self-attentive-parser](https://github.com/nikitakit/self-attentive-parser)  
18. PoTeC: A German naturalistic eye-tracking-while-reading corpus \- PMC \- NIH, fecha de acceso: enero 30, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12208991/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12208991/)  
19. Spanish · spaCy Models Documentation, fecha de acceso: enero 30, 2026, [https://spacy.io/models/es](https://spacy.io/models/es)  
20. Constituent Treelib · spaCy Universe, fecha de acceso: enero 30, 2026, [https://spacy.io/universe/project/constituent\_treelib](https://spacy.io/universe/project/constituent_treelib)  
21. \[2510.16604\] Fine-tuning of Large Language Models for Constituency Parsing Using a Sequence to Sequence Approach \- arXiv, fecha de acceso: enero 30, 2026, [https://arxiv.org/abs/2510.16604](https://arxiv.org/abs/2510.16604)  
22. Unipisa/diaparser: Direct Attentive Dependency Parser \- GitHub, fecha de acceso: enero 30, 2026, [https://github.com/Unipisa/diaparser](https://github.com/Unipisa/diaparser)  
23. AI-Driven Resume Parsing and Ranking System: Leveraging NLP And Machine Learning for Efficient Recruitment \- ResearchGate, fecha de acceso: enero 30, 2026, [https://www.researchgate.net/publication/396808492\_AI-Driven\_Resume\_Parsing\_and\_Ranking\_System\_Leveraging\_NLP\_And\_Machine\_Learning\_for\_Efficient\_Recruitment](https://www.researchgate.net/publication/396808492_AI-Driven_Resume_Parsing_and_Ranking_System_Leveraging_NLP_And_Machine_Learning_for_Efficient_Recruitment)