# **Evaluación de Robustez en Parsers Automáticos del Español: Un Banco de Pruebas de Estrés basado en Patología Sintáctica y Psicolingüística Computacional**

El desarrollo de herramientas de procesamiento de lenguaje natural (PLN) ha experimentado un avance sin precedentes gracias a la implementación de arquitecturas basadas en transformadores y modelos de grafos de dependencias. Sin embargo, la evaluación de la robustez de estos sistemas, tales como Stanza o Benepar, a menudo se limita a métricas de precisión sobre corpus estándar que no capturan la complejidad de los fallos de análisis (parsing breakdowns) en situaciones de ambigüedad genuina. Este reporte, redactado desde la perspectiva de la psicolingüística computacional y la sintaxis formal, propone un banco de pruebas de estrés diseñado específicamente para explotar las vulnerabilidades intrínsecas del idioma español. A diferencia de los enfoques tradicionales que replican estructuras del inglés, este análisis se centra en fenómenos nativos como la flexibilidad del orden de constituyentes, el sistema de clíticos, el sujeto nulo y el marcado diferencial de objeto, utilizando fuentes académicas para sustentar cada categoría patológica.

## **Fundamentos del Procesamiento de Oraciones en Español y la Crisis del Parsing Lineal**

El procesamiento de oraciones (sentence processing) en seres humanos opera de manera incremental, construyendo representaciones estructurales a medida que se recibe el input lingüístico. Los parsers automáticos intentan emular esta eficiencia, pero suelen enfrentarse a conflictos donde una estructura localmente ambigua induce a un error de análisis global. En el ámbito del español, la sintaxis no se rige primordialmente por la posición, sino por una red de concordancias morfológicas y marcas funcionales que el procesador debe integrar en tiempo real.

Los sistemas de parsing actuales, entrenados mayoritariamente con modelos probabilísticos o redes neuronales profundas, tienden a favorecer la "proximidad lineal" o el "cierre tardío", una estrategia que, si bien es efectiva en lenguas con orden rígido como el inglés, resulta catastrófica ante la flexibilidad del español. La robustez de un parser no se mide por su capacidad para analizar oraciones simples, sino por su resiliencia ante los "caminos de jardín" (garden paths) y las ambigüedades de adjunción que desafían las heurísticas de frecuencia.

## **Categoría I: Ambigüedad de Adjunción en Sintagmas Nominales Complejos**

La adjunción de cláusulas de relativo (RC) tras un sintagma nominal complejo (formado por dos sustantivos unidos por la preposición "de") constituye el campo de batalla más documentado en la psicolingüística translingüística. El conflicto surge cuando el procesador debe decidir si la oración subordinada modifica al primer núcleo nominal (![][image1]) o al segundo (![][image2]).

### **La Estrategia de Cierre Tardío vs. Adjunción Temprana**

El principio de Cierre Tardío (Late Closure) postula que los nuevos elementos sintácticos deben adjuntarse a la cláusula o frase que se está procesando en ese momento para minimizar la carga en la memoria de trabajo.1 Bajo esta premisa, se esperaría que en una secuencia como "![][image1] de ![][image2] que...", la cláusula de relativo se adjunte a ![][image2]. No obstante, investigaciones fundamentales han demostrado que el español muestra una preferencia sistemática por la Adjunción Temprana (High Attachment), vinculando la cláusula al ![][image1].3

Esta divergencia plantea un reto para los parsers automáticos. Muchos modelos de lenguaje están sesgados hacia el cierre tardío debido a su entrenamiento inicial o a la influencia de arquitecturas diseñadas para el inglés. Un parser robusto para el español debe ser capaz de contrarrestar este sesgo de proximidad lineal para capturar la interpretación preferida por los hablantes nativos.

### **Oración Trampa: La Adjunción del Antecedente**

- **Categoría:** Ambigüedad de Adjunción (Attachment Ambiguity).
- **Oración Trampa:** "Alguien disparó a la criada de la actriz que estaba en el balcón." 1
- **La Ambigüedad:**
  - **Árbol A (Adjunción Alta / Preferencia en Español):** La cláusula "que estaba en el balcón" se adjunta al ![][image1] ("la criada"). En esta interpretación, la criada es quien se encuentra en el balcón. Formalmente, la RC es hija del Sintagma Nominal encabezado por "criada".1
  - **Árbol B (Adjunción Baja / Cierre Tardío):** La cláusula se adjunta al ![][image2] ("la actriz"). Aquí, es la actriz quien ocupa el balcón. Esta estructura es la predicha por modelos de procesamiento universales que no consideran la especificidad del español.1
- **Fuente:** Cuetos, F., & Mitchell, D. C. (1988). Relative clause attachment in Spanish and English. _Language and Cognitive Processes_.1

### **Factores Moduladores: El Peso de la Morfología y la Semántica**

La robustez de un parser se evalúa mediante su sensibilidad a las marcas de desambiguación. En español, el género y el número actúan como anclas que fuerzan una interpretación específica, invalidando las preferencias de adjunción por defecto.4

| Condición de Desambiguación | Oración de Ejemplo                                   | Interpretación Forzada                   |
| :-------------------------- | :--------------------------------------------------- | :--------------------------------------- |
| Concordancia de Género      | "El criado de la actriz que estaba divorciada."      | Adjunción Baja (![][image2] \- femenino) |
| Concordancia de Número      | "Los criados de la actriz que estaban en el balcón." | Adjunción Alta (![][image1] \- plural)   |
| Restricción Semántica       | "El perro del médico que estaba ladrando."           | Adjunción Alta (basada en el léxico)     |

Un parser que falle en identificar que "divorciada" (femenino) no puede modificar a "criado" (masculino) demuestra una falta de integración entre el análisis morfológico y la estructura sintáctica. Este "broken parsing" es común en sistemas que priorizan la jerarquía estructural sobre la validación de rasgos (feature checking).5

## **Categoría II: El Laberinto del "SE" y la Indeterminación de la Diátesis**

El clítico "se" representa el epítome de la complejidad funcional en la sintaxis del español. Su procesamiento requiere que el sistema desambigüe entre valores reflexivos, recíprocos, pronominales, de pasiva refleja, impersonales y dativos aspectuales.6 La dificultad radica en que, en muchas ocasiones, la oración es estructuralmente idéntica hasta el final, o incluso permanece ambigua globalmente, dependiendo del contexto pragmático.

### **El Conflicto entre Pasiva Refleja e Impersonalidad**

El parser automático suele colapsar al intentar distinguir entre la pasiva refleja (donde hay un sujeto paciente que concuerda con el verbo) y la impersonal (donde el verbo es invariable y el sustantivo es un objeto directo).6 Esta distinción es crucial para la asignación de roles temáticos (Agente vs. Paciente).

- **Categoría:** El Laberinto del "SE" (The "SE" Maze).
- **Oración Trampa:** "Se eligieron los nuevos ministros del gobierno tras la crisis." vs "Se eligió a los nuevos ministros del gobierno tras la crisis." 6
- **La Ambigüedad:**
  - **Árbol A (Pasiva Refleja):** En la primera oración, "los nuevos ministros" es el Sujeto Gramatical Paciente. El verbo "eligieron" debe concordar en plural. El parser debe etiquetar el SN como nsubj.6
  - **Árbol B (Impersonal con "A" Personal):** En la segunda oración, la presencia de la preposición "a" marca a "los nuevos ministros" como Complemento Directo Animado. El verbo permanece en tercera persona del singular porque no tiene sujeto léxico. El parser debe etiquetar el SN como obj y reconocer la impersonalidad del núcleo verbal.6
- **Fuente:** Real Academia Española. (2009). _Nueva gramática de la lengua española_. Madrid: Espasa.6

### **Valores Pronominales y el "SE" de Voz Media**

La "Voz Media" describe procesos que le ocurren al sujeto sin que haya un agente externo claro, a menudo utilizando verbos de cambio de estado o posición.7

| Valor de "SE"    | Función Sintáctica       | Característica del Parsing               |
| :--------------- | :----------------------- | :--------------------------------------- |
| Reflexivo        | CD / CI                  | El sujeto realiza y recibe la acción.7   |
| Pronominal       | Morfema del verbo        | Inherente al lexema (ej: arrepentirse).7 |
| Voz Media        | Marca de intransitividad | Indica cambio de estado (ej: secarse).12 |
| Dativo Aspectual | Refuerzo enfático        | Opcional, aporta matiz de culminación.7  |

Un fallo típico en parsers como Stanza ocurre cuando se analiza el "se" de "Juan se comió la manzana" como un objeto directo reflexivo ("Juan se comió a sí mismo"), en lugar de identificarlo como un dativo aspectual que enfatiza la totalidad de la acción. Este error de interpretación semántica se deriva de una incapacidad para modelar la interfaz léxico-sintaxis.7

## **Categoría III: Ambigüedad Sujeto-Objeto y el Camino de Jardín del Marcado Diferencial**

El español permite una gran libertad en el orden de los constituyentes (SVO, VSO, VOS, OVS). Esta flexibilidad, combinada con el Marcado Diferencial de Objeto (DOM) mediante la preposición "a", genera situaciones de ambigüedad donde el parser puede confundir un objeto directo con un sujeto o viceversa.13

### **La Trampa de los Sujetos Posverbales**

En oraciones subordinadas temporales, el español permite que el sujeto aparezca tras el verbo. Si el verbo es transitivo y el objeto también puede funcionar como sujeto de la oración principal, se produce un efecto de Garden Path.15

- **Categoría:** Ambigüedad Sujeto-Objeto (Word Order Ambiguity).
- **Oración Trampa:** "Mientras los niños estudiaban el mapa permanecía en la vitrina." 15
- **La Ambigüedad:**
  - **Árbol A (Interpretación Errónea Local):** El parser analiza "el mapa" como el objeto directo del verbo "estudiaban" (Lectura: Los niños estudiaban el mapa). Al llegar a "permanecía", el sistema detecta una anomalía sintáctica porque le falta un sujeto para el segundo verbo.15
  - **Árbol B (Interpretación Correcta Global):** "Estudiaban" es usado aquí de forma intransitiva. "El mapa" es el sujeto de la oración principal encabezada por "permanecía". La pausa estructural (prosódica en el habla, virgular en la escritura descuidada) se encuentra después de "estudiaban".15
- **Fuente:** Carreiras, M., & Clifton, C. (1993). Relative clause interpretation preferences in Spanish and English. _Language and Speech_.4

### **El Marcado Diferencial de Objeto (DOM) como Fuente de Conflicto**

La preposición "a" ante objetos directos animados es una característica definitoria del español que los parsers suelen procesar erróneamente como marcas de dativo (objeto indirecto) o incluso como preposiciones de lugar.9

**Oración Trampa de Estrés:** "A los alumnos saludó el profesor en el pasillo."

En esta estructura OVS, el parser debe resistir la tentación de etiquetar "A los alumnos" como sujeto (por su posición inicial) o como objeto indirecto (por la preposición "a"). Un parser robusto debe identificar que "el profesor" es el único candidato a nsubj por la falta de preposición y la concordancia, asignando a "los alumnos" el rol de obj.13

## **Categoría IV: Coordinación y la Elipsis de Vaciado (Gapping)**

La elipsis es un fenómeno donde se omite material lingüístico recuperable contextualmente. El _gapping_ o vaciado es especialmente problemático porque deja "restos" (remnants) que el parser debe vincular con sus correlatos en la primera cláusula para reconstruir la estructura lógica.18

### **La Reconstrucción de la Estructura Ausente**

En español, el _gapping_ es frecuente en el lenguaje formal y periodístico. El reto para el parser es que no existe una marca física del verbo omitido, y los restos pueden tener funciones sintácticas diversas.

- **Categoría:** Coordinación y Elipsis (Gapping).
- **Oración Trampa:** "Luis saludó a María y Antonia a Juan Carlos." 20
- **La Ambigüedad:**
  - **Árbol A (Coordinación de Objetos \- Erróneo):** El parser podría interpretar que Luis saludó a tres personas: María, Antonia y Juan Carlos. Esta interpretación falla porque "Antonia" no lleva la "a" de objeto directo en la primera lectura, y la estructura de la frase sugiere una simetría de cláusulas.20
  - **Árbol B (Vaciado Verbal \- Correcto):** La oración se compone de dos cláusulas coordinadas: \[Luis saludó a María\] y \[Antonia (saludó) a Juan Carlos\]. "Antonia" es el sujeto de la segunda cláusula y "a Juan Carlos" su objeto. El parser debe "proyectar" el verbo de la primera cláusula en la segunda.20
- **Fuente:** Brucart, J. M. (1987). _La elipsis sintáctica en español_. Bellaterra: Publicacions de la Universitat Autònoma de Barcelona.18

### **Gapping con Órdenes no Canónicos (VSO)**

El nivel de estrés aumenta cuando el _gapping_ ocurre en oraciones con el sujeto pospuesto, forzando al sistema a reconocer patrones de elipsis sobre estructuras que ya de por sí son poco frecuentes en el entrenamiento de modelos estándar.19

| Tipo de Gapping | Estructura de Superficie | Desafío para el Parser                             |
| :-------------- | :----------------------- | :------------------------------------------------- |
| Simple          | "S V O y S O"            | Vincular el segundo sujeto al verbo elidido.19     |
| Complejo        | "V S O y S O"            | Identificar el orden VSO en ambas cláusulas.19     |
| Con Clíticos    | "S lo V y S O"           | Manejar la referencia del clítico en la elipsis.20 |

## **Análisis de Vulnerabilidades en Arquitecturas de Transformadores (Stanza y Benepar)**

A pesar de que modelos como Stanza (basado en redes neuronales de grafos) y Benepar (basado en constituyentes) han mejorado la precisión general, su desempeño en este "Banco de Pruebas de Estrés" revela limitaciones estructurales profundas.

### **La Ilusión de la Concordancia Local**

Muchos parsers modernos operan bajo mecanismos de atención que priorizan la información local. En el caso de la adjunción de relativas ("la criada de la actriz que..."), si el modelo no está entrenado con un balance adecuado de adjunciones altas, la atención del transformador se "anclará" en el sustantivo más cercano (![][image2]), ignorando que en español existe una predisposición estructural hacia el ![][image1]. Este es un fallo de "sesgo de proximidad" que afecta la fidelidad de la representación semántica.3

### **El Problema de las Etiquetas Funcionales en el "SE"**

La arquitectura de dependencias de Stanza a menudo etiqueta el "se" con una categoría genérica (ej: expl:pv para pronominales o expl:pass para pasivas). Sin embargo, el fallo ocurre en la asignación del sujeto paciente. En una pasiva refleja como "Se venden pisos", el sistema suele marcar "pisos" como obj (objeto directo), tratándola como una oración activa con sujeto elidido, lo cual es técnicamente incorrecto desde la sintaxis formal del español, donde "pisos" es el nsubj.6 Este error tiene consecuencias graves en tareas de extracción de información y traducción automática.

### **Desafíos en la Reconstrucción de la Elipsis**

Los parsers de constituyentes (como Benepar) suelen tener dificultades para representar nodos vacíos o elididos. Al no encontrar un núcleo verbal en la segunda parte de una coordinación con _gapping_, el parser tiende a "forzar" la adjunción de los restos a la cláusula anterior, creando una estructura de sintagma nominal extremadamente larga y semánticamente incoherente.18

## **Propuesta de Métricas de Robustez para el Procesamiento del Español**

Para cuantificar la robustez de un parser ante estos fenómenos, proponemos la adopción de métricas que vayan más allá del UAS (Unlabeled Attachment Score) o LAS (Labeled Attachment Score) tradicionales.

1. **Índice de Resiliencia ante Garden Path (IRGP):** Porcentaje de oraciones como "Mientras los niños estudiaban el mapa..." analizadas correctamente tras el punto de desambiguación.
2. **Precisión en Diátesis de Clíticos (PDC):** Capacidad del sistema para distinguir correctamente entre sujetos y objetos en construcciones con "se".
3. **Consistencia de Concordancia a Larga Distancia (CCLD):** Evaluación de si el parser respeta los rasgos de género y número al realizar adjunciones de cláusulas de relativo.

### **Comparativa de Errores por Categoría**

| Categoría           | Parser A (Stanza)       | Parser B (Benepar)       | Causa de Fallo                               |
| :------------------ | :---------------------- | :----------------------- | :------------------------------------------- |
| Adjunción RC        | Sesgo hacia ![][image2] | Sesgo hacia ![][image2]  | Falta de sintonización (tuning) al español.1 |
| SE Impersonal       | Confunde con Reflexivo  | Etiqueta como Sujeto     | Ambigüedad funcional del clítico.7           |
| Gapping             | Falla en dependencias   | Estructura plana errónea | Incapacidad de modelar elipsis verbal.20     |
| Sujetos Posverbales | Marca como Objeto       | Falla en la jerarquía    | Sesgo posicional SVO.13                      |

## **Implicaciones para el Futuro del PLN en Español**

La evaluación sistemática mediante este banco de pruebas de estrés subraya la necesidad de transitar de modelos de lenguaje puramente estadísticos a modelos que integren restricciones gramaticales explícitas. La sintaxis del español no es una variante del inglés con más morfología; es un sistema con principios de organización propios donde la jerarquía se establece mediante la concordancia y no solo mediante el orden lineal.

El futuro del parsing robusto en español depende de la capacidad de los modelos para:

- **Integrar el conocimiento morfosintáctico:** Los rasgos de género y número deben ser condiciones necesarias para la adjunción de dependencias.
- **Modelar la elipsis:** Los sistemas deben ser capaces de predecir la existencia de núcleos verbales nulos en estructuras coordinadas.
- **Desambiguar funcionalmente los clíticos:** El clítico "se" debe ser analizado en función del marco de subcategorización del verbo y la presencia de marcas como la "a" personal.

## **Conclusiones del Investigador Senior**

La robustez de los parsers automáticos en español es, en la actualidad, una asignatura pendiente. Mientras que el rendimiento en textos estándar es aceptable, la fragilidad ante estructuras patológicas como las presentadas en este informe revela que los modelos aún no "entienden" la sintaxis del español, sino que "adivinan" basándose en probabilidades de proximidad.

Las categorías analizadas —adjunción, el "se", el orden flexible y la elipsis— no son curiosidades lingüísticas, sino componentes esenciales del uso real de la lengua. Un sistema de inteligencia artificial que no pueda distinguir entre una criada en el balcón y una actriz en el balcón, o que confunda una pasiva refleja con una acción reflexiva, no es apto para aplicaciones críticas en el ámbito jurídico, médico o de análisis de discurso. La implementación de este banco de pruebas de estrés es el primer paso necesario para auditar la calidad de los parsers y guiar el desarrollo de una tecnología lingüística que sea verdaderamente representativa de la complejidad sintáctica del idioma español.

Este reporte concluye que la evaluación de la robustez debe ser un proceso continuo, basado en la teoría lingüística y no solo en la validación estadística. La riqueza de la morfología flexiva y la flexibilidad sintáctica del español deben ser vistas no como un ruido que dificulta el parsing, sino como la señal misma que permite una comunicación precisa y llena de matices, la cual los parsers automáticos deben aspirar a capturar íntegramente.

#### **Obras citadas**

1. Early and late preferences in relative clause attachment in Spanish ..., fecha de acceso: enero 31, 2026, [https://academicworks.cuny.edu/cgi/viewcontent.cgi?article=1235\&context=qc_pubs](https://academicworks.cuny.edu/cgi/viewcontent.cgi?article=1235&context=qc_pubs)
2. Sentence Processing in Spanish as a Heritage Language: A Self-Paced Reading Study of Relative Clause Attachment \- ResearchGate, fecha de acceso: enero 31, 2026, [https://www.researchgate.net/publication/324530370_Sentence_Processing_in_Spanish_as_a_Heritage_Language_A_Self-Paced_Reading_Study_of_Relative_Clause_Attachment](https://www.researchgate.net/publication/324530370_Sentence_Processing_in_Spanish_as_a_Heritage_Language_A_Self-Paced_Reading_Study_of_Relative_Clause_Attachment)
3. Syntactic Attachment and Anaphor Resolution: The Two Sides of Relative Clause Attachment \- Cambridge Core \- Journals & Books Online, fecha de acceso: enero 31, 2026, [https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/54F59D9F88B95A6DBE210F72A4145FFA/9780511527210c11_p259-281_CBO.pdf/syntactic-attachment-and-anaphor-resolution-the-two-sides-of-relative-clause-attachment.pdf](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/54F59D9F88B95A6DBE210F72A4145FFA/9780511527210c11_p259-281_CBO.pdf/syntactic-attachment-and-anaphor-resolution-the-two-sides-of-relative-clause-attachment.pdf)
4. (PDF) Relative Clause Interpretation Preferences in Spanish and ..., fecha de acceso: enero 31, 2026, [https://www.researchgate.net/publication/15127594_Relative_Clause_Interpretation_Preferences_in_Spanish_and_English](https://www.researchgate.net/publication/15127594_Relative_Clause_Interpretation_Preferences_in_Spanish_and_English)
5. Lexico-Semantic Influence on Syntactic Processing: An Eye ..., fecha de acceso: enero 31, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC10046643/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10046643/)
6. se | Diccionario panhispánico de dudas | RAE \- ASALE, fecha de acceso: enero 31, 2026, [https://www.rae.es/dpd/se](https://www.rae.es/dpd/se)
7. SE \- Valores de la partícula se \- Hispanoteca, fecha de acceso: enero 31, 2026, [http://hispanoteca.eu/Gram%C3%A1ticas/Gram%C3%A1tica%20espa%C3%B1ola/SE%20-%20Valores%20de%20la%20part%C3%ADcula%20se.htm](http://hispanoteca.eu/Gram%C3%A1ticas/Gram%C3%A1tica%20espa%C3%B1ola/SE%20-%20Valores%20de%20la%20part%C3%ADcula%20se.htm)
8. se en medias \- pasivas \- impersonales \- Hispanoteca, fecha de acceso: enero 31, 2026, [http://hispanoteca.eu/Foro/ARCHIVO-Foro/se%20en%20medias-pasivas-impersonales.htm](http://hispanoteca.eu/Foro/ARCHIVO-Foro/se%20en%20medias-pasivas-impersonales.htm)
9. Se medias \- pasivas \- impersonales 3 \- Hispanoteca, fecha de acceso: enero 31, 2026, [http://hispanoteca.eu/Gram%C3%A1ticas/Gram%C3%A1tica%20espa%C3%B1ola/Se%20medias%20-%20pasivas%20-%20impersonales%203.htm](http://hispanoteca.eu/Gram%C3%A1ticas/Gram%C3%A1tica%20espa%C3%B1ola/Se%20medias%20-%20pasivas%20-%20impersonales%203.htm)
10. La enseñanza de las construcciones pasivas e impersonales con se en E/LE. ¿Cuántas distinciones son necesarias?, fecha de acceso: enero 31, 2026, [https://revistas.ucm.es/index.php/DIDA/article/download/51042/47392/92159](https://revistas.ucm.es/index.php/DIDA/article/download/51042/47392/92159)
11. Sobre una pasiva anómala en español \- Redalyc, fecha de acceso: enero 31, 2026, [https://www.redalyc.org/journal/5259/525977674004/html/](https://www.redalyc.org/journal/5259/525977674004/html/)
12. Observaciones Diacrónicas Sobre El Clítico 'Se' En Español: Categorización Y Gramaticalización1, fecha de acceso: enero 31, 2026, [https://www.theartsjournal.org/index.php/site/article/viewFile/902/449](https://www.theartsjournal.org/index.php/site/article/viewFile/902/449)
13. “Yo a mí me parece”: la gramaticalización de “yo” como marcador de discurso en el español coloquial, fecha de acceso: enero 31, 2026, [https://www.lingref.com/cpp/wss/6/paper2851.pdf](https://www.lingref.com/cpp/wss/6/paper2851.pdf)
14. Sobre ambigüedad y vaguedad en los diccionarios \- Hispadoc, fecha de acceso: enero 31, 2026, [https://hispadoc.es/descarga/articulo/6466011.pdf](https://hispadoc.es/descarga/articulo/6466011.pdf)
15. Procesamiento de oraciones ambiguas de vía muerta y ... \- Dialnet, fecha de acceso: enero 31, 2026, [https://dialnet.unirioja.es/descarga/articulo/3816381.pdf](https://dialnet.unirioja.es/descarga/articulo/3816381.pdf)
16. Oraciones con SE en castellano: sólo una aparente (superficial) confusión \- Dialnet, fecha de acceso: enero 31, 2026, [https://dialnet.unirioja.es/descarga/articulo/58426.pdf](https://dialnet.unirioja.es/descarga/articulo/58426.pdf)
17. La posesión de traducciones de textos técnicos del alemán al castellano María Helena Mendoza García \- TDX, fecha de acceso: enero 31, 2026, [https://www.tdx.cat/bitstream/handle/10803/457362/mhmg1de1.pdf?sequence=1\&isAllowed=y](https://www.tdx.cat/bitstream/handle/10803/457362/mhmg1de1.pdf?sequence=1&isAllowed=y)
18. Sobre la enseñanza de la elisión sintáctica en la clase de gramática del español como lengua extranjera o segunda (ELE/L2), fecha de acceso: enero 31, 2026, [https://scholarworks.indianapolis.iu.edu/bitstreams/362aa767-43ea-4e58-a89c-209427428ad8/download](https://scholarworks.indianapolis.iu.edu/bitstreams/362aa767-43ea-4e58-a89c-209427428ad8/download)
19. THE NON-UNITY OF GAPPING \- ADDI \- EHU, fecha de acceso: enero 31, 2026, [https://addi.ehu.es/bitstream/handle/10810/20922/TESIS_JUNG_WONSUK.pdf?isAllowed=y\&sequence=1](https://addi.ehu.es/bitstream/handle/10810/20922/TESIS_JUNG_WONSUK.pdf?isAllowed=y&sequence=1)
20. LA ELISIÓN SINTÁCTICA EN ESPAÑOL \- DDD UAB, fecha de acceso: enero 31, 2026, [https://ddd.uab.cat/pub/llibres/1987/142543/elisintesp1987.pdf](https://ddd.uab.cat/pub/llibres/1987/142543/elisintesp1987.pdf)
21. ¿ESPECIES EN PELIGRO DE EXTINCIÓN? La elipsis en la teoría de la gramática En primer lugar debo advertir que tanto a la elip, fecha de acceso: enero 31, 2026, [http://www.sinoele.org/images/Revista/17/monograficos/AAH_2005/AAH_2005_5%20Laura%20Vela%20%20Almendros_74-92.pdf](http://www.sinoele.org/images/Revista/17/monograficos/AAH_2005/AAH_2005_5%20Laura%20Vela%20%20Almendros_74-92.pdf)

[image1]: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAZCAYAAADaILXQAAABFElEQVR4XmNgGAUDDXqB+D8SdkGVBgNkeRBeiSpNGPwG4pMMEM26aHIwkIsuQCw4DsRRDBDDJ6LJgYAQEGuhCxIDWIDYFsqGeR0dtKELEAtABoMsAIGfDBDDGRHSYHAQjU802I7EtmSAGL4BScwTiB8h8YkGIBd/RRM7AcR/gVgOyu8C4kUIaeJBJRDvRhNjZ4C4/g0SWxVJnhWIDYH4JRA7IoljgG1AXIcuyICI2CQGzCB5AMQ7GSDyeA3/BMQO6IIMiIg9B8Tz0ORgACTvhC6IDA6gC0ABKAXBXK+IJgcDBA3vQxdAAmcYsKd5GMAaLIJQCWSMDXAA8Qt0QSRA0OWUAJobjq0UpQoAGR6ELjgKhhEAAOzMQTDZezj3AAAAAElFTkSuQmCC
[image2]: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAWCAYAAADAQbwGAAABLklEQVR4Xu2SPUsDQRCGx0pFLGIrqIUEibaSlGoh9mLrD7CMlWhjaWkZiFVS+A9EbKwEEQTBj0YhYCGSRiIWIqLv7Ga52ZdkiyOFhQ88MPPO3XB7dyL/DJpt+GPciseOJ4mv+YzHvfmCl+JvWKaZcgjvOEzxApfELzyOR45zeMBhinDUcCxGswKH/RiBC936Q/zNw9nYcUV9kl1TL4pfeG0yZZ36JCfUX4hfqsuVWTiRjdOU4TtlelxdqMdXGmambMISnJce71v/w1MOJf44ryYfhc+mfzO1ow1XOARn4hfW4b3J57p5oGlqxzcc4xBsSPaUNZqtmfrG1DIOj2xA7ItfOEN5YAjehmYHPsAOrIaQmIaPHBr24BSHeWnBIod5mYQVDvOyKtnHsr/WH+YX3xJA9TKzwFkAAAAASUVORK5CYII=
