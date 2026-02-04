# Política de Preservación de Etiquetas Nativas

> **Principio:** Fidelidad Lingüística sobre Interoperabilidad Artificial
> **Ámbito:** Interfaz de Usuario y Representación de Datos

## 1. Declaración de Principios

Grammatomy adopta una postura de **No-Intervención** respecto a la nomenclatura gramatical generada por los modelos subyacentes. Exponemos las etiquetas "crudas" (*raw tags*) tal como las define el corpus de entrenamiento de cada idioma (AnCora para español, Penn Treebank para inglés, VIT para italiano, etc.), rechazando explícitamente cualquier intento de normalización, traducción o mapeo a un "meta-lenguaje" universal.

## 2. Justificación Científica y Técnica

Esta decisión se fundamenta en cuatro pilares críticos para el rigor académico:

### 2.1. Anclaje en la Tradición Académica
Las notaciones utilizadas por cada modelo (ej. `sn` en AnCora vs `NP` en PTB) no son arbitrarias; son los estándares extendidos y utilizados por los lingüistas que trabajan en ese idioma específico. Están ancladas en una tradición cultural y científica propia. Intentar unificarlas alienaría al usuario experto, obligándole a aprender una tercera notación artificial inventada por la herramienta.

### 2.2. Semántica Estructural Relativa
Los términos gramaticales no tienen un valor absoluto universal. Una etiqueta como `S` (*Sentence*) o `VP` (*Verb Phrase*) tiene matices estructurales muy diferentes en un árbol de constituyentes del inglés (jerárquico) frente a uno del italiano (plano). Traducir etiquetas basándose en similitudes superficiales destruiría la información sobre la "armonía estructural" del conjunto.

### 2.3. Intraducibilidad de Sistemas Teóricos
No existe una correspondencia biyectiva entre los sistemas. Fenómenos como los subniveles de la teoría X-Barra (marcados con apóstrofes o etiquetas como `NX`) no tienen equivalentes directos en sistemas como AnCora o VIT. Cualquier traducción implicaría una pérdida de datos o una simplificación inaceptable (*lossy compression*).

### 2.4. Foco Monolingüe del Usuario
Grammatomy no es una herramienta de traducción automática, sino de análisis profundo. El usuario que utiliza esta herramienta para preparar un corpus, ilustrar ejercicios o deducir segmentación fónica, trabaja inmerso en un idioma concreto. Se asume que el usuario debe adaptarse a la notación del modelo estándar de su lengua de estudio, en lugar de esperar que la lengua se adapte a una convención de software.

## 3. Implicaciones para el Usuario Final

*   **Curva de Aprendizaje:** El usuario debe familiarizarse con el *tagset* específico del modelo que está utilizando (disponible en el Glosario de la aplicación).
*   **Veracidad de Datos:** Lo que el usuario ve en la pantalla es exactamente lo que el modelo ha predicho, sin capas de ofuscación. Esto garantiza que la herramienta sea válida para la investigación científica reproducible.