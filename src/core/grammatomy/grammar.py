"""
Módulo de Gramática y Parsing (Grammar).

Este módulo actúa como fachada principal para las operaciones de análisis sintáctico
y validación gramatical. Coordina los motores de parsing (Stanza, SpaCy), carga
las reglas de validación desde archivos YAML y proporciona utilidades para
verificar la consistencia de hojas y estructura.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yaml
from anytree import Node, PreOrderIter

from .glossary import TAG_MAP

#: Logger del módulo.
logger = logging.getLogger(__name__)


def load_grammar_rules() -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """
    Carga las reglas gramaticales desde el archivo de configuración YAML.

    El archivo de reglas define la estructura permitida (padre -> hijos) y
    metadatos para la interfaz de usuario.

    Returns:
        Una tupla conteniendo:
        1. Diccionario aplanado {Padre: [Hijos Permitidos]} para validación rápida.
        2. Diccionario {NodeID: Descripción} para tooltips en la UI.
    """
    rules = {}
    descriptions = {}

    # Determine path relative to this file
    base_path = Path(__file__).parent / "assets" / "rules"

    # Archivo de reglas unificado (Híbrido AnCora/Universal Dependencies)
    file_path = base_path / "hybrid_rules.yaml"

    if not file_path.exists():
        logger.warning("Grammar rules file not found at %s. Using empty rules.", file_path)
        return {}, {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Handle new dictionary structure: rules: { TAG: { allowed: [...] } }
        raw_nodes = data.get("nodes", [])
        for node in raw_nodes:
            tag = node["id"]
            children_config = node.get("allowed_children", {})

            if isinstance(children_config, list):
                allowed = children_config
            else:
                allowed = (children_config.get("mandatory", []) or []) + (
                    children_config.get("optional", []) or []
                )
            rules[tag] = allowed
            if "description" in node:
                descriptions[tag] = node["description"]

    except (OSError, yaml.YAMLError) as e:
        logger.error("Error loading grammar rules: %s", e)
        return {}, {}

    return rules, descriptions


# Initialize rules
GRAMMAR_RULES, NODE_DESCRIPTIONS = load_grammar_rules()

# --- LEAF & PUNCTUATION VALIDATION ---

#: Inventario de signos de puntuación válidos por idioma.
PUNCTUATION_INVENTORY: Dict[str, Set[str]] = {
    "es": {
        ".",
        ",",
        ";",
        ":",
        "...",
        "¡",
        "!",
        "¿",
        "?",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        '"',
        "'",
        "-",
        "–",
        "—",
        "«",
        "»",
        "%",
        "/",
    },
    "en": {
        ".",
        ",",
        ";",
        ":",
        "...",
        "!",
        "?",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        '"',
        "'",
        "-",
        "–",
        "—",
        "`",
        "``",
        "''",
        "%",
        "/",
    },
    "ca": {
        ".",
        ",",
        ";",
        ":",
        "...",
        "¡",
        "!",
        "¿",
        "?",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        '"',
        "'",
        "-",
        "–",
        "—",
        "«",
        "»",
        "·",
        "%",
        "/",
    },
}

#: Etiquetas que denotan estrictamente puntuación (AnCora + Penn).
PUNCTUATION_TAGS: Set[str] = {
    # Penn
    ".",
    ",",
    ":",
    "``",
    "''",
    "-LRB-",
    "-RRB-",
    "SYM",
    "$",
    "#",
    "PUNCT",  # Universal Dependencies
    # AnCora (starts with f)
    "fp",
    "fc",
    "fs",
    "fd",
    "fe",
    "fg",
    "fz",
    "fx",
    "ft",
    "fat",
    "fpt",
    "fit",
    "fia",
}

#: Tipo para el callback de validación de léxico.
LexiconCallback = Callable[[str, str, str], Tuple[bool, str]]

#: Hook para validación externa de léxico (ej. búsqueda en diccionario).
LEXICON_HOOK: Optional[LexiconCallback] = None


def validate_leaf_consistency(text: str, pos_tag: str, lang: str = "es") -> Tuple[bool, str]:
    """
    Valida la consistencia entre el texto de una hoja y su etiqueta POS.
    Aplica reglas estrictas para distinguir palabras de signos de puntuación.

    Args:
        text: El texto del nodo hoja.
        pos_tag: La etiqueta gramatical asignada.
        lang: Código de idioma.

    Returns:
        Tupla (Es válido, Mensaje de error).
    """
    # 1. External Hook (Future Proofing)
    if LEXICON_HOOK:
        valid, msg = LEXICON_HOOK(text, pos_tag, lang)  # pylint: disable=not-callable
        if not valid:
            return False, msg

    # 2. Punctuation Validation
    # AnCora tags starting with 'f' are punctuation
    is_punct_tag = pos_tag in PUNCTUATION_TAGS or (
        len(pos_tag) > 0 and pos_tag.startswith("f") and pos_tag[0] == "f"
    )

    allowed_punct = PUNCTUATION_INVENTORY.get(lang, PUNCTUATION_INVENTORY["es"])

    if is_punct_tag:
        if text not in allowed_punct:
            return (
                False,
                (
                    f"'{text}' is not a valid punctuation mark for '{lang}' "
                    f"or does not match the tag '{pos_tag}'."
                ),
            )
        return True, ""

    # 3. Word Validation
    if text in allowed_punct:
        return (
            False,
            f"Text '{text}' is punctuation, but tag '{pos_tag}' expects a word.",
        )

    if " " in text:
        return (
            False,
            "Words cannot contain spaces (use hyphens for compounds).",
        )

    return True, ""


def get_suggestions(parent_tag: str, all_tags: List[str]) -> List[str]:
    """
    Filtra una lista de etiquetas basándose en las reglas gramaticales para un padre dado.

    Args:
        parent_tag: La etiqueta del nodo padre (ej. "sn").
        all_tags: Lista completa de etiquetas candidatas.

    Returns:
        Lista filtrada y ordenada de etiquetas válidas.
    """
    if parent_tag not in GRAMMAR_RULES:
        return sorted(all_tags)

    allowed = set(GRAMMAR_RULES[parent_tag])
    # Filter tags that are in the allowed set
    valid = [tag for tag in all_tags if tag in allowed]

    # If strict filtering leaves us with nothing (e.g. hybrid tags), fallback to permissive
    if not valid:
        return sorted(all_tags)

    return sorted(valid)


def _check_node_validity(
    node: Node, known_tags: Set[str], rules: Dict[str, List[str]]
) -> Optional[str]:
    """Verifica un único nodo contra las reglas gramaticales."""
    # 0. Ghost Node Check (Intrinsic Invalidity)
    if node.name == "👻":
        return "Nodo Fantasma: Estructura temporal. Edite la etiqueta."

    if node.is_root or not node.parent:
        return None

    parent_tag = node.parent.name
    if parent_tag not in rules:
        return None

    child_tag = node.name
    allowed_children = rules[parent_tag]
    if allowed_children:
        if child_tag not in allowed_children and child_tag != "👻":
            return f"Estructural: '{parent_tag}' no admite hijo '{child_tag}'."
    elif child_tag in known_tags:
        return f"Terminal: '{parent_tag}' no puede contener estructura '{child_tag}'."

    return None


def validate_structure(root: Node) -> Dict[Node, str]:
    """
    Audita el árbol completo contra las reglas gramaticales cargadas.

    Returns:
        Un diccionario mapeando nodos inválidos a sus mensajes de error.
        {Node: "Mensaje de error"}
    """
    violations = {}

    # Build a set of all known structural tags to distinguish them from raw text
    known_tags = set()
    if "Phrasal" in TAG_MAP:
        known_tags.update(TAG_MAP["Phrasal"].keys())
    if "POS" in TAG_MAP:
        known_tags.update(TAG_MAP["POS"].keys())
    known_tags.update(PUNCTUATION_TAGS)

    for node in PreOrderIter(root):
        error = _check_node_validity(node, known_tags, GRAMMAR_RULES)
        if error:
            violations[node] = error

    return violations


class Grammar:
    """
    Fachada principal para el análisis sintáctico.

    Abstrae la complejidad de los diferentes motores subyacentes (Stanza, SpaCy)
    proporcionando una interfaz unificada para obtener árboles sintácticos.

    Attributes:
        engine (str): Nombre del motor ('stanza' o 'spacy').
        lang (str): Idioma objetivo.
        model (str): Paquete de modelo específico.
    """

    def __init__(
        self,
        engine: str = "stanza",
        lang: str = "es",
        model: str = "default",
        use_gpu: bool = False,
    ):
        self.engine = engine
        self.lang = lang
        self.model = model
        self.use_gpu = use_gpu

    def parse(self, text: str) -> Optional[Node]:
        """
        Analiza el texto y retorna un árbol sintáctico.

        Args:
            text: La oración o texto a analizar.

        Returns:
            El nodo raíz del árbol generado o None si falla.
        """
        root = None
        if self.engine == "stanza":
            from .engines.stanza_engine import StanzaEngine

            root = StanzaEngine.get_tree(
                text, lang=self.lang, model_package=self.model, use_gpu=self.use_gpu
            )
        elif self.engine == "spacy":
            from .engines.spacy_engine import SpacyEngine

            root = SpacyEngine.get_tree(
                text, lang=self.lang, model_package=self.model, use_gpu=self.use_gpu
            )
        else:
            raise ValueError(f"Unsupported engine: {self.engine}")

        return root


def get_syntax_tree(text: str, params: Optional[Dict[str, Any]] = None) -> Optional[Node]:
    """
    Función utilitaria (helper) para obtener un árbol sintáctico rápidamente.

    Args:
        text: Texto a analizar.
        params: Diccionario de configuración (engine, lang, model_package, use_gpu).

    Returns:
        Nodo raíz del árbol sintáctico.
    """
    if params is None:
        params = {}

    engine = params.get("engine", "stanza")
    lang = params.get("lang", "es")
    model_package = params.get("model_package", "default")
    use_gpu = params.get("use_gpu", False)

    grammar = Grammar(engine=engine, lang=lang, model=model_package, use_gpu=use_gpu)
    return grammar.parse(text)
