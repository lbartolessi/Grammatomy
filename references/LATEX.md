Para que una herramienta de creación de publicaciones lingüísticas sea realmente efectiva, el usuario debe proporcionar una estructura de metadatos que no solo ayude a la organización interna, sino que también facilite la **indexación académica** y la **interoperabilidad** (que otros sistemas entiendan de qué trata el paper).

Aquí tienes los metadatos básicos categorizados por su función:

---

## 1. Metadatos de Identificación y Autoría

Son los pilares para que el trabajo sea citado correctamente.

* **Título y Subtítulo:** El nombre completo de la investigación.
* **Autor(es):** Nombre completo y, crucialmente, el **ORCID** (Open Researcher and Contributor ID) para evitar ambigüedades.
* **Afiliación Institucional:** Universidad o centro de investigación al que pertenecen los autores.
* **Palabras Clave (Keywords):** Entre 3 y 6 términos técnicos (ej. *sociolingüística*, *morfosintaxis*, *procesamiento de lenguaje natural*).

## 2. Metadatos Específicos de Lingüística

Aquí es donde el proyecto aporta valor real al área académica. Sin estos datos, un paper lingüístico pierde contexto científico.

* **Lengua(s) Objeto de Estudio:** El idioma o variedad lingüística analizada (utilizando códigos estándar como el **ISO 639-3**, ej: `spa` para español, `que` para quechua).
* **Área de la Lingüística:** Clasificación temática (Fonética, Semántica, Pragmática, etc.).
* **Metodología:** Indicar si el enfoque es cualitativo, cuantitativo, basado en corpus o experimental.

## 3. Metadatos de Fuentes y Corpus

En lingüística, la procedencia de los datos es vital para la replicabilidad.

* **Descripción del Corpus:** Nombre del corpus utilizado, tamaño (número de palabras/tokens) y procedencia.
* **Licencia de Datos:** Si los datos son abiertos (Creative Commons) o restringidos.
* **Herramientas de Software:** Versiones de programas usados para el análisis (ej. *AntConc*, *ELAN*, *Praat*, o librerías de Python como *spaCy*).

---

## Resumen de Estructura Recomendada

| Categoría | Campo sugerido | ¿Por qué es importante? |
| --- | --- | --- |
| **Básicos** | Título, Resumen (Abstract) | Resumen del contenido para buscadores. |
| **Técnicos** | ISO Language Code | Permite que otros lingüistas encuentren el estudio por idioma. |
| **Legales** | Declaración de Ética | Fundamental en estudios con informantes humanos. |
| **Referenciales** | Bibliografía (BibTeX/RIS) | Asegura que las citas sigan el formato APA o MLA. |

---

> **Nota sobre estándares:** Si quieres que tu proyecto sea profesional, te sugiero que los metadatos sigan el esquema del **Dublin Core** o de la **OLAC** (Open Language Archives Community), que es el estándar de oro para recursos lingüísticos.

---

¡Excelente decisión! Una guía de **Instrucciones para Autores** bien estructurada no solo profesionaliza tu plataforma, sino que también garantiza que los papers generados tengan una calidad técnica apta para ser aceptados en revistas de alto impacto.

Aquí tienes una propuesta de guía que puedes integrar en tu proyecto, diseñada para ser clara, directa y muy funcional:

---

# ⚠️ Guía de Preparación de Metadatos y Manuscrito

Bienvenido al asistente de creación lingüística. Para asegurar la integridad académica y la visibilidad de su investigación, por favor complete la información siguiendo estos estándares:

## 1. Información de Identificación (Front Matter)

Esta sección es vital para la indexación en bases de datos como Scopus o Web of Science.

* **Título:** Debe ser informativo y contener las variables principales del estudio. Evite abreviaturas.
* **Resumen (Abstract):** Un solo párrafo (máx. 250 palabras) que incluya: objetivo, metodología, resultados principales y conclusión.
* **ORCID ID:** Proporcione su identificador de investigador de 16 dígitos. Si no lo tiene, puede obtenerlo en [orcid.org](https://orcid.org).
* **Palabras Clave:** Proporcione de 3 a 5 términos. Se recomienda usar tesauros especializados en lingüística.

## 2. Especificaciones Lingüísticas (Obligatorio)

Para que su trabajo sea categorizado correctamente en archivos digitales (como OLAC), debe definir:

* **Lengua Objeto:** Identifique el idioma estudiado mediante el estándar **ISO 639-3** (ej. *spa* para español, *eng* para inglés, *nah* para náhuatl).
* **Variedad Dialectal:** Si aplica, especifique la zona geográfica o social (ej. español rioplatense, inglés jurídico).
* **Nivel de Análisis:** Seleccione una o más categorías:
* Fonética/Fonología
* Morfosintaxis
* Semántica/Pragmática
* Lingüística de Corpus / Computacional
* Análisis del Discurso



## 3. Gestión de Datos y Ética

La transparencia es la base de la ciencia moderna.

* **Fuentes de Datos:** Especifique si los datos provienen de un corpus existente, entrevistas, encuestas o experimentos de laboratorio.
* **Declaración Ética:** Si trabajó con informantes humanos, confirme que cuenta con el consentimiento informado y la aprobación de un comité de ética.
* **Disponibilidad de Datos:** Indique si el corpus o los datos brutos estarán disponibles para otros investigadores (Open Data).

## 4. Estilo y Referencias

* **Citas:** El sistema utiliza por defecto el formato **APA 7ma Edición**, a menos que se especifique lo contrario (ej. MLA o Chicago).
* **Ejemplos Lingüísticos:** Todos los ejemplos deben estar numerados y, de ser necesario, seguir las **Reglas de Glosado de Leipzig** para morfología.

---

### Ejemplo de cómo debería verse su ficha de metadatos:

| Campo | Entrada del Usuario (Ejemplo) |
| --- | --- |
| **Título** | *Análisis de los marcadores discursivos en el habla urbana de Madrid* |
| **Idioma (ISO)** | `spa` |
| **Metodología** | Cuantitativa, basada en el corpus PRESEEA. |
| **Software** | R (Librería tidyverse), AntConc 4.0. |

---

Perfecto, vamos con el **Punto 1: El Formulario Técnico**.

Para que tu software no abrume al usuario, lo ideal es dividir el formulario en **cuatro bloques lógicos**. Esto permite que el investigador avance desde lo general (autoría) hacia lo ultra-específico (datos lingüísticos).

Aquí tienes la propuesta de campos y el tipo de dato que cada uno debería recolectar:

---

## 📋 Estructura del Formulario de Entrada

### Bloque A: Identificación General (The Basics)

*Este bloque genera la portada y los metadatos de búsqueda.*

1. **Título del Proyecto:** (Texto libre - Máx. 200 caracteres).
2. **Título Corto (Running Head):** (Texto libre - Para encabezados de página).
3. **Autor(es):** (Nombre, Apellido, Afiliación, Correo electrónico).
4. **ORCID:** (Validación de formato: `0000-0000-0000-0000`).
5. **Abstract / Resumen:** (Área de texto - Sugerido 150-250 palabras).

### Bloque B: Especificaciones del Lenguaje (The Core)

*Aquí es donde tu herramienta se diferencia de un editor de texto genérico.*

6. **Lengua(s) de Estudio:** (Selector con búsqueda por código **ISO 639-3**).
* *Ejemplo:* Al escribir "Español", el sistema guarda `spa`.


7. **Variedad Lingüística:** (Texto libre - Ej: *Español andino*, *Alemán de Suiza*).
8. **Nivel de Análisis:** (Checklist múltiple):
* [ ] Fonética / Fonología
* [ ] Morfología
* [ ] Sintaxis
* [ ] Semántica / Pragmática
* [ ] Sociolingüística / Psicolingüística
* [ ] Otros.



### Bloque C: Datos y Metodología (The Evidence)

*Crucial para la sección de "Metodología" del paper.*

9. **Tipo de Datos:** (Menú desplegable):
* Corpus pre-existente (ej. CREA, COCA).
* Trabajo de campo (entrevistas, encuestas).
* Experimentación (laboratorio, *eye-tracking*).
* Datos de redes sociales / Web scraping.


10. **Herramientas de Análisis:** (Texto o etiquetas - Ej: *R, ELAN, Praat, Python*).
11. **Glosado:** (Switch Sí/No): "¿El proyecto requiere glosas interlineales (Reglas de Leipzig)?".

### Bloque D: Gestión de Referencias

12. **Estilo de Cita:** (Menú desplegable: APA 7, MLA 9, Chicago, LSA).
13. **Carga de Archivo Bibliográfico:** (Botón de carga para archivos `.bib` o `.ris`).

---

## 🛠️ Sugerencia de Interfaz (UX)

Para que el formulario sea "inteligente", podrías añadir **Validación Contextual**:

> **Ejemplo:** Si el usuario selecciona "Fonética" en el Bloque B, el formulario podría desplegar una pregunta opcional en el Bloque C: *¿Desea incluir espectrogramas o archivos de audio vinculados?*

---

Para publicaciones lingüísticas en LaTeX, no existe una plantilla "única", pero sí un estándar de facto: el uso de paquetes específicos que manejan la complejidad de la disciplina (glosas, árboles y alfabetos fonéticos).

Aquí te presento tres enfoques o "sabores" de plantillas que tu proyecto debería ofrecer:

---

## 1. La Plantilla "Estándar de Oro" (Generic Linguistics Paper)

Esta es la más versátil. Utiliza la clase `article` pero cargando la "trinidad" de la lingüística en LaTeX.

* **Paquetes clave:**
* `gb4e` o `langsci-gb4e`: Para ejemplos numerados y glosas interlineales.
* `forest`: Para árboles sintácticos (con la librería `linguistics`).
* `tipa`: Para el Alfabeto Fonético Internacional (IPA).
* `biblatex` (estilo APA): Para las referencias.



**Estructura sugerida de metadatos en el preámbulo:**

```latex
\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{libertine} % Fuente muy usada en lingüística por su soporte de glifos
\usepackage[linguistics]{forest}
\usepackage{gb4e} % ¡Importante! Debe ser el último paquete cargado

\title{Título del Paper}
\author{Nombre del Autor \thanks{ORCID: 0000-0000-0000-0000}}
\date{\today}

```

---

## 2. La Plantilla "Language Science Press"

Si tu usuario busca publicar un libro o un capítulo de alta calidad técnica, el formato de **Language Science Press (LangSci)** es el estándar de referencia en la comunidad de acceso abierto.

* **Características:**
* Diseño extremadamente limpio y moderno.
* Uso de fuentes específicas (**Libertinus**) que soportan caracteres especiales de lenguas indígenas o minoritarias.
* Gestión avanzada de metadatos (ISO de lenguas, áreas temáticas).


* **Ideal para:** Proyectos de tesis o monografías lingüísticas complejas.

---

## 3. La Plantilla de la LSA (Linguistic Society of America)

Muchos journals siguen las directrices de la revista *Language*. Es una plantilla más sobria, con márgenes específicos y un sistema de citas muy riguroso.

* **Punto clave:** El estilo de bibliografía `sp.bst` (o `biblatex-sp-okls`) que formatea las referencias según las normas de la LSA.

---

## Comparativa de Herramientas Visuales

| Elemento | Paquete Recomendado | Ejemplo de Uso |
| --- | --- | --- |
| **Árboles** | `forest` | Muy superior a `qtree`; permite nodos automáticos y mayor control estético. |
| **Glosas** | `gb4e` o `expex` | `gb4e` es más simple; `expex` es para casos de glosas muy complejos (múltiples líneas). |
| **Fonética** | `tipa` | Permite escribir símbolos IPA usando códigos ASCII. |
| **Tablas** | `booktabs` | Para crear tablas académicas sin líneas verticales (estilo profesional). |

### Ejemplo de código para un árbol sintáctico (Forest):

Para que tu software lo genere automáticamente, el usuario solo debería definir la estructura y tú envolverla en este código:

---

Tienes toda la razón. En el mundo académico, y especialmente en lingüística, el valor de una herramienta no está solo en "escribir", sino en **eliminar la fricción del formato técnico**. Si tu aplicación genera un código LaTeX limpio, compilable y que respeta las normas de la LSA o APA, los investigadores la adoptarán por puro ahorro de tiempo.

Aquí tienes el **Skeleton Snippet** que tu aplicación debería generar. Está diseñado para ser la "salida estándar" que procese los metadatos del formulario que definimos antes.

---

## 📄 Estructura del Snippet Maestro (LaTeX)

Este código utiliza los paquetes más robustos y modernos. Está comentado para que tu lógica de programación sepa dónde inyectar cada variable del formulario.

```latex
% --- PREÁMBULO ---
\documentclass[11pt,a4paper]{article}

% Codificación y Fuentes (Soporte para caracteres especiales lingüísticos)
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{libertinus} % Excelente soporte para IPA y glifos raros

% Paquetes de Lingüística Esenciales
\usepackage[linguistics]{forest} % Para árboles sintácticos
\usepackage{tipa}                % Para Alfabeto Fonético (IPA)
\usepackage{vowel}               % Para diagramas de trapecios vocálicos
\usepackage{leipzig}             % Para manejar abreviaturas de glosado
\usepackage{gb4e}                % Para ejemplos numerados y glosas (Cargar al final)

% Bibliografía (Ajustable según el selector del formulario)
\usepackage[style=apa, backend=biber]{biblatex}
\addbibresource{bibliografia.bib} 

% --- METADATOS INYECTADOS ---
\title{[[TITULO_DEL_FORMULARIO]]}
\author{[[NOMBRE_AUTOR]] \thanks{[[AFILIACION]] --- ORCID: [[ORCID]]}}
\date{\today}

% --- CUERPO DEL DOCUMENTO ---
\begin{document}

\maketitle

\begin{abstract}
[[ABSTRACT_DEL_FORMULARIO]]
\par\vspace{1em}
\noindent \textbf{Keywords:} [[KEYWORDS_DEL_FORMULARIO]] \\
\noindent \textbf{Language(s):} [[ISO_CODE]] ([[VARIEDAD]])
\end{abstract}

\section{Introducción}
% Aquí empieza el contenido generado...

\section{Análisis de Datos}
% Ejemplo de cómo el software debería renderizar un ejemplo glosado:
\begin{exe}
\ex
\begin{tabular}[t]{llll}
    [[LENGUA_ORIGINAL_1]] & [[LENGUA_ORIGINAL_2]] & [[LENGUA_ORIGINAL_3]] \\
    \textit{el} & \textit{niño} & \textit{duerme} \\
    DET.M.SG & N.M.SG & V.3.SG.PRES \\
    \end{tabular}
\glt `El niño duerme.'
\end{exe}

\section{Estructura Sintáctica}
% Renderizado automático de árboles desde el formulario
\begin{center}
\begin{forest}
  [[ESTRUCTURA_SINTACTICA_BRUTA]]
\end{forest}
\end{center}



\printbibliography

\end{document}

```

---

## 💡 Puntos clave para tu lógica de exportación

1. **El conflicto de `gb4e`:** Este paquete es el estándar para numerar ejemplos, pero es famoso por entrar en conflicto con otros. **Regla de oro:** Siempre debe ser el último paquete cargado en el preámbulo.
2. **Manejo de Glosas:** Si el usuario introduce una oración y su traducción, tu software debe alinear las palabras. En LaTeX, esto se hace con entornos como `\begin{tabular}` o comandos de `gb4e`.
3. **Diagramas Vocálicos:** Si el usuario marca "Fonética" en el formulario, sería un gran valor añadido que tu software permita generar trapecios vocálicos usando el paquete `vowel`.

## ¿Qué sigue para tu MVP?

Para que Gemini Code Assist trabaje mejor, podrías pedirle que:

* **Cree un "Parser" de texto a Forest:** Un script que convierta una estructura simple de corchetes del usuario (ej: `[S [NP El niño] [VP duerme]]`) al código LaTeX exacto de `forest`.
* **Validador de BibTeX:** Una función que verifique que el archivo `.bib` subido por el usuario no tiene errores antes de intentar compilar.

¿Quieres que te ayude a definir la **lógica de conversión de esos corchetes simples a código de árbol LaTeX**? Es la parte que más suele frustrar a los lingüistas.

---

Excelente enfoque. Conocer estas revistas no solo te sirve para el estilo de la plantilla, sino para entender el **modelo de datos** que exigen. Si tu software puede exportar un archivo que cumpla con los requisitos de estas "Big Four", tus usuarios estarán a un clic de enviar su manuscrito a la élite académica.

Aquí tienes las 4 referencias clave, su enfoque y por qué son importantes para tu proyecto:

---

## 1. *Language* (Journal of the Linguistic Society of America)

Es la revista de lingüística más prestigiosa a nivel mundial.

* **Importancia para tu software:** Tienen un "Style Sheet" extremadamente estricto. Si tu salida de LaTeX cumple con los márgenes, el sistema de citas (LSA Style) y el formato de ejemplos de *Language*, tu herramienta será validada instantáneamente por la comunidad.
* **Dato técnico:** Requieren que las notas al pie sean mínimas y que las referencias bibliográficas sigan un formato muy limpio (sin abreviaturas de nombres de revistas).

## 2. *Natural Language & Linguistic Theory* (NLLT)

El referente para la **lingüística teórica** (Sintaxis, Semántica, Morfología).

* **Importancia para tu software:** Aquí es donde los **árboles sintácticos** (`forest`) son los protagonistas. La precisión en el glosado interlineal es innegociable.
* **Dato técnico:** Suelen preferir el estilo de citas de Springer, pero con las adaptaciones lingüísticas estándar (Reglas de Leipzig).

## 3. *Journal of Phonetics* (Elsevier)

El estándar para la **lingüística experimental** y de laboratorio.

* **Importancia para tu software:** A diferencia de las anteriores, aquí los metadatos de **metodología** y **análisis estadístico** son críticos.
* **Dato técnico:** Tu plantilla para esta revista debería priorizar la inserción de gráficos de alta resolución (vectoriales, `.pdf` o `.eps`) y tablas de datos complejas (`booktabs`).

## 4. *Glossa: a journal of general linguistics*

Líder en el movimiento de **Acceso Abierto (Open Access)**.

* **Importancia para tu software:** Es una revista moderna y digital. Utilizan un sistema de metadatos muy robusto para que los papers sean "maquinables".
* **Dato técnico:** Es la oportunidad perfecta para que tu software brille exportando no solo el PDF, sino también el archivo `.tex` limpio y el archivo de bibliografía `.bib` perfectamente curado.

---

### Comparativa de Exigencias de Formato

| Revista | Estilo de Cita | Elemento Crítico | Nivel de "LaTeX-friendly" |
| --- | --- | --- | --- |
| **Language** | LSA Style | Glosas perfectas | Muy alto |
| **NLLT** | Springer/APA | Árboles complejos | Alto |
| **J. Phonetics** | APA | Gráficos y Tablas | Medio (aceptan Word, pero prefieren PDF) |
| **Glossa** | Ubiquity | Metadatos y Accesibilidad | Total (Open Source) |

---

### Un consejo de "insider" para tu proyecto:

Muchos autores sufren al pasar de una revista a otra porque los estilos de cita cambian ligeramente. Si tu aplicación permite cambiar entre **"Estilo LSA"** y **"Estilo APA 7"** con un solo selector en el formulario, habrás resuelto el mayor dolor de cabeza del investigador.

---

Efectivamente, en Europa el ecosistema tiene matices importantes. Aunque la lingüística es una disciplina globalizada, las tradiciones académicas europeas (especialmente la británica, la alemana y la francesa) introducen variaciones en el **estilo de citación** y en la **jerarquía de los metadatos**.

Para que tu aplicación sea competitiva en el mercado europeo, debes considerar estos tres pilares:

---

## 1. El Estándar Unificado: *The Unified Style Sheet for Linguistics*

En 2007, un grupo de editores de las revistas europeas más importantes (incluyendo las de la asociación **LAGB** en Reino Unido y varios institutos **Max Planck** en Alemania) acordaron un "estilo unificado".

* **Diferencia con APA:** Es más minimalista. Por ejemplo, no usa "pág." o "p." para las páginas, sino solo dos puntos (Ej: *Chomsky 1965: 24*).
* **Impacto en tu software:** Deberías incluir una opción de exportación llamada **"Unified Linguistics Style"**. Es el estándar de facto para revistas como *Journal of Linguistics* (Cambridge University Press).

---

## 2. Revistas Europeas de Referencia (The Euro-List)

Si un usuario en Europa usa tu plataforma, probablemente apunte a estas publicaciones:

### *Journal of Linguistics* (Reino Unido - Cambridge)

* **Perfil:** La revista de la *Linguistics Association of Great Britain*.
* **Exigencia:** Muy rigurosa con la **micro-tipografía**. Prefieren el uso de comillas simples para significados (ej: *casa* 'house') y dobles para citas textuales. Tu generador de LaTeX debería automatizar este cambio.

### *Lingua* / *Lingua Open* (Países Bajos - Elsevier/Open Access)

* **Perfil:** Una de las más antiguas y respetadas en Europa continental.
* **Exigencia:** Siguen un estilo muy cercano al de la LSA pero con adaptaciones métricas (A4 en lugar de Letter) y una preferencia por bibliografías extremadamente detalladas.

### *Zeitschrift für Sprachwissenschaft* (Alemania)

* **Perfil:** Referente en la lingüística germánica y teórica.
* **Exigencia:** Aquí los metadatos de **categorización de la lengua** (ISO codes) son sagrados. A menudo requieren resúmenes en dos idiomas (inglés y alemán/lengua objeto).

---

## 3. Variaciones Técnicas en el Layout (Europa vs. USA)

Al configurar tu plantilla LaTeX con Gemini Code Assist, asegúrate de que el usuario pueda alternar estos "detalles europeos":

| Característica | Estándar USA (LSA/APA) | Estándar Europeo (LAGB/Unified) |
| --- | --- | --- |
| **Tamaño de Papel** | `letterpaper` (8.5" x 11") | `a4paper` (210mm x 297mm) |
| **Comillas de significado** | Suelen usar dobles o simples indistintamente. | **Obligatorio:** simples para glosas/significados. |
| **Citas Bibliográficas** | (Author, Year, p. 00) | (Author Year: 00) — *Sin coma tras el autor.* |
| **Glosas (Leipzig)** | A menudo abreviadas en Small Caps. | Estricto seguimiento de las *Leipzig Glossing Rules*. |

---

## 🛠️ Ajuste para tu código LaTeX (Soporte Europeo)

Para que tu preámbulo sea "Euro-compatible", te sugiero añadir el paquete `babel` con soporte multi-idioma y configurar `biblatex` con el estilo `authoryear-comp`, que es el que más se acerca al estándar unificado europeo:

```latex
% Soporte para idiomas y tipografía europea
\usepackage[spanish,german,french,british]{babel} 
\usepackage[style=authoryear-comp, backend=biber, indexing=cite]{biblatex}

% Configuración de comillas según tradición europea (csquotes)
\usepackage{csquotes}
\DeclareQuoteAlias{british}{linguistics} 

```

---

### ¿Cómo proceder ahora?

Para que tu MVP sea realmente "internacional", podrías implementar un **"Toggle de Región"** en la configuración del proyecto:

* **Modo Atlantic:** Papel *Letter*, citas APA 7, fuente *Times New Roman*.
* **Modo Continental/Euro:** Papel *A4*, *Unified Style Sheet*, fuente *Libertinus* o *Computer Modern*.

---

Esta es una excelente idea para la lógica de tu aplicación. Implementar **Presets de Estilo** permitirá que el usuario pase de un formato a otro sin tocar una sola línea de código LaTeX, algo que los lingüistas te agradecerán eternamente.

Respecto a **España y Portugal**, sí hay particularidades culturales y académicas que deberías programar como "reglas de negocio" en tu herramienta.

---

## 🇪spaña y 🇵ortugal: Particularidades Críticas

1. **El Sistema de Apellidos:** En ambos países, el uso de dos apellidos (o más) es la norma.
* **Problema en LaTeX:** BibTeX a menudo confunde el primer apellido con un segundo nombre.
* **Solución en tu software:** Tu formulario debe capturar los apellidos en un campo único y exportarlos entre llaves en el `.bib`: `author = {{García Martínez}, Juan}`.


2. **Citas con "Apud":** En la tradición ibérica (especialmente en filología), todavía es común ver la cita de una cita mediante *apud* (ej. *Chomsky 1957 apud Lyons 1970*). Tu sistema de bibliografía debería estar preparado para manejar el campo `related` en BibLaTeX.
3. **Abreviaturas Gramaticales:** Mientras que en inglés se usa `3SG` (3rd Person Singular), en España es frecuente ver `3ªsg` o `3.ªsg.`. Tu motor de glosado debería permitir "Diccionarios de Etiquetas" locales.
4. **Normas de la RAE/CPLP:** En España, las normas de la RAE dictan que los signos de puntuación van **fuera** de las comillas de cierre (a diferencia del estándar americano). Tu paquete `csquotes` debe estar configurado como `style=spanish`.

---

## 🛠️ JSON de Configuración de Presets

Aquí tienes la estructura de datos que Gemini Code Assist puede usar para "alimentar" el generador de plantillas según la región:

```json
{
  "presets": {
    "north_america": {
      "display_name": "Standard (LSA/APA)",
      "latex_class": "article",
      "paper_size": "letterpaper",
      "font_size": "12pt",
      "bib_style": "apa",
      "citation_format": "parentheses",
      "quotes_style": "american",
      "required_packages": ["babel[english]", "gb4e"]
    },
    "europe_unified": {
      "display_name": "Unified Style (Euro)",
      "latex_class": "article",
      "paper_size": "a4paper",
      "font_size": "11pt",
      "bib_style": "authoryear-comp",
      "citation_format": "unified_points", 
      "quotes_style": "british",
      "required_packages": ["babel[british]", "csquotes", "langsci-gb4e"]
    },
    "iberian_standard": {
      "display_name": "Ibérico (RAE/CPLP Focus)",
      "latex_class": "article",
      "paper_size": "a4paper",
      "font_size": "11pt",
      "bib_style": "iso-authortitle",
      "citation_format": "apud_supported",
      "quotes_style": "spanish",
      "required_packages": ["babel[spanish,portuguese]", "csquotes", "gb4e"],
      "specific_rules": {
        "double_surname_protection": true,
        "interlinear_gloss_lang": "local"
      }
    }
  }
}

```

---

## 🚀 Cómo aplicar esto en tu flujo de trabajo

Cuando el usuario elija **"Ibérico"** en tu UI, el motor de exportación debería realizar estos tres cambios automáticos en el archivo `.tex`:

1. **Configuración de `csquotes`:** `\DeclareQuoteAlias{spanish}{manual}` para asegurar que las comillas angulares (« ») o las dobles se comporten según la norma local.
2. **Traducción de términos fijos:** Cambiar "References" por "Bibliografía" o "Referências" automáticamente vía `babel`.
3. **Tratamiento de las Glosas:** Si el paper es sobre una lengua indígena o minoritaria analizada desde una universidad española, el glosado suele estar en español (ej. `DET.FEM.PL` en lugar de `DET.F.PL`). Puedes ofrecer un "Mapper" de etiquetas.

---


