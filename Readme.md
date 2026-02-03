---
title: Grammatomy
emoji: 🩻
colorFrom: gray
colorTo: blue
sdk: docker
pinned: false
app_port: 8501
short_description: Universal Constituent Parser for Spanish Prosody
---

# 🩻 **Grammatomy**: _Universal Constituent Parser_ (AnyTree Wrapper)

## 1. Visión General y Objetivo

**Grammatomy** es una librería de "disección sintáctica" independiente. Su objetivo es extraer el **Análisis de Constituyentes (Full Parsing)** de oraciones en múltiples idiomas y normalizar la salida en una estructura jerárquica de **`anytree`**.

Esta librería es agnóstica a la fonética; su responsabilidad termina al entregar un árbol sintáctico limpio, recursivo y tipado que otros proyectos (como **G2Puri**) consumirán para análisis prosódico.

## 2. Motores y Estrategias de Carga (Engines)

### A. Stanza (Stanford NLP)

- **Carga:** Automática a través del sistema de modelos de Stanza.
- **Configuración:** `stanza.download(lang, processors='tokenize,pos,constituency')`.

### B. spaCy + Benepar

Para idiomas distintos al inglés, no usaremos `benepar.download()`. En su lugar, cargaremos modelos de **Hugging Face** o locales directamente en el pipeline de spaCy.

- **Workflow:**
  1. Cargar modelo base de spaCy (ej. `es_core_news_lg`).
  2. Añadir el componente `benepar` al pipeline.
  3. Cargar el modelo de constituyentes específico desde un archivo o identificador de HF.

## 3. Catálogo de Modelos por Idioma (Open Source)

| Idioma        | Código | Motor Stanza (Package)              | Modelo Benepar / Hugging Face (Recomendado)                         |
| :------------ | :----- | :---------------------------------- | :------------------------------------------------------------------ |
| **Español**   | `es`   | `default_accurate` (Bertin-RoBERTa) | _No disponible en Benepar_. Usar Stanza o modelos Seq2Seq (PlanTL). |
| **Portugués** | `pt`   | `cintil_charlm`                     | _Soporte nativo en Stanza_.                                         |
| **Italiano**  | `it`   | `vit_charlm`                        | _Soporte nativo en Stanza_.                                         |
| **Alemán**    | `de`   | `spmrl_charlm`                      | _Soporte nativo en Stanza_.                                         |
| **Inglés**    | `en`   | `gum` (o `wsj`)                     | `benepar_en3` (Official Berkeley)                                   |
| **Francés**   | `fr`   | _No soportado_                      | _Incompatible con transformers >= 4.30 (WIP)_                       |

## 4. Estructura de la Interfaz Pública

La librería debe exponer un único punto de entrada:

```python
def get_syntax_tree(text: str, params: dict) -> Node:
    """
    params: {
        'lang': 'es',
        'engine': 'stanza' | 'spacy',
        'model_path': str (opcional, para modelos locales de Benepar),
        'low_resource': bool (para usar modelos más ligeros)
    }
    Retorna: Un objeto Node de anytree con atributos: label, pos, word.
    """
```

## 5. Instrucciones de Implementación

### Conversión de Formato Penn Treebank (LISP)

Ambos motores devuelven el árbol en formato de paréntesis: `(S (SN (NP Juan)) (VP (V vino)))`.
Implementar `LispParser.to_anytree(lisp_str)` siguiendo estos pasos:

1. Eliminar saltos de línea y normalizar espacios.
2. Usar una pila (stack) para gestionar la recursividad de los paréntesis.
3. El primer elemento tras un `(` es la `label` (ej: SN).
4. Si el elemento es un terminal (hoja), asignarlo al atributo `word` del nodo actual.
5. Incluir en cada nodo hoja toda la información morfológica (tagging) que el motor proporcione.

```text
S
├── SN
│   └── NP
│       └── Juan
└── VP
    └── V
        └── vino
```

### Lógica de Carga para spaCy-Benepar (Alternativa)

Si el motor es `spacy`, utiliza este patrón:

```python
import spacy
from benepar.spacy_plugin import BeneparComponent

nlp = spacy.load("es_core_news_lg")
# Carga manual del modelo descargado de Hugging Face
nlp.add_pipe("benepar", config={"model": "nombre_del_modelo_en_hf_o_ruta_local"})
doc = nlp(text)
sent = list(doc.sents)[0]
lisp_tree = sent._.parse_string

```

## 6. Hoja de Ruta (Roadmap)

1. **Project setup**: Preparar el entorno de desarrollo, environment.yml para entorno Conda, project.toml, estructura de directorios (src, test, etc...)
2. **Parser LISP**: Convertidor universal independiente del motor.
3. **Bridge Stanza**: Integración del pipeline de Stanford.
4. **Bridge spaCy**: Integración de Benepar con soporte para modelos externos.
5. **AnyTree Exporter**: Utilidad para visualizar el árbol en consola o exportar a JSON/dict.
6. **Interactive Web Demo**: Prototipado rápido en Streamlit/Gradio para validación de conceptos.
7. **Grammatomy API (REST)**: Servicio centralizado (FastAPI) para desacoplar el motor de la interfaz.
8. **Grammatomy Studio (Desktop/Qt)**: Aplicación nativa (PySide6) capaz de operar en modo híbrido:
   - _Local_: Motor integrado para privacidad y potencia.
   - _Remoto_: Cliente ligero consumiendo la API (Escenario "Gaming PC" -> Tablet).
9. **Distribution & Deployment Ecosystem**: Estrategia de empaquetado universal para "ocultar" Python al usuario final:
   - _Contenerización_: Docker (Solo para despliegue en Servidor/API).
   - _Linux_: AppImage.
   - _Windows_: Instalador nativo "Invisible Python" (MSI/EXE vía PyInstaller/Nuitka).
   - _Cloud_: Hugging Face Spaces.
10. **Performance Benchmark Suite**: Desarrollo de scripts para comparar latencia CPU/GPU, medir tiempos de arranque (cold/warm start) y validar modelos multilingües con oraciones complejas estandarizadas.

## 7. Ejecución de la Demo Interactiva

### Modo Público (Por defecto)

Muestra una interfaz simplificada, ocultando opciones técnicas (CPU/GPU, selección de motor) y forzando los modelos recomendados (BERT para español).

```bash
streamlit run src/grammatomy/demo/app.py
```

### Modo Desarrollador (`--dev`)

Habilita todos los controles: selección manual de motor (Stanza/spaCy), dispositivo de hardware y variantes de modelos.

```bash
streamlit run src/grammatomy/demo/app.py -- --dev
```
