import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yaml
from anytree import Node, PreOrderIter

from .glossary import TAG_MAP

# Standard Constituents Rules (Penn Treebank / AnCora approximation)
# Mapping: Parent Tag -> List of Allowed Child Tags
# If a parent is not listed, the system will default to permissive mode (allow all).

logger = logging.getLogger(__name__)


def load_grammar_rules(lang: str = "es") -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """
    Loads grammar rules from the YAML configuration file.
    Returns a tuple containing:
    1. A flattened dictionary {Parent: [Allowed Children]} for validation.
    2. A dictionary {NodeID: Description} for UI tooltips.
    """
    rules = {}
    descriptions = {}

    # Determine path relative to this file
    base_path = Path(__file__).parent / "assets" / "rules"
    # Unified rules file (Hybrid)
    file_path = base_path / "hybrid_rules.yaml"

    if not file_path.exists():
        logger.warning(
            "Grammar rules file not found at %s. Using empty rules.", file_path
        )
        return {}, {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Handle new dictionary structure: rules: { TAG: { allowed: [...] } }
        raw_nodes = data.get("nodes", [])
        for node in raw_nodes:
            tag = node["id"]
            children_config = node.get("allowed_children", {})
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
GRAMMAR_RULES, NODE_DESCRIPTIONS = load_grammar_rules("es")

# --- LEAF & PUNCTUATION VALIDATION ---

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

# Tags that strictly denote punctuation (AnCora + Penn)
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

# Hook for external lexicon validation (e.g., dictionary lookup)
# Signature: (word, pos_tag, lang) -> (is_valid, error_message)
LexiconCallback = Callable[[str, str, str], Tuple[bool, str]]
LEXICON_HOOK: Optional[LexiconCallback] = None


def validate_leaf_consistency(
    text: str, pos_tag: str, lang: str = "es"
) -> Tuple[bool, str]:
    """
    Validates the consistency between a leaf text and its POS tag.
    Enforces rules for words vs. punctuation.
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
    Filters a list of tags based on the grammar rules for the given parent.

    Args:
        parent_tag: The tag of the parent node (e.g., "NP").
        all_tags: The list of candidate tags (e.g., all POS tags).

    Returns:
        List[str]: A filtered list of valid tags. If parent is unknown, returns all_tags.
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
    """Checks a single node against grammar rules."""
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
    Audits the entire tree against the loaded grammar rules.
    Returns a dictionary mapping invalid nodes to their error messages.
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
    Main entry point for parsing. Facade for different engines.
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
        if self.engine == "stanza":
            from .engines.stanza_engine import StanzaEngine

            return StanzaEngine.get_tree(
                text, lang=self.lang, model_package=self.model, use_gpu=self.use_gpu
            )
        elif self.engine == "spacy":
            from .engines.spacy_engine import SpacyEngine

            return SpacyEngine.get_tree(
                text, lang=self.lang, model_package=self.model, use_gpu=self.use_gpu
            )
        else:
            raise ValueError(f"Unsupported engine: {self.engine}")


def get_syntax_tree(
    text: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Node]:
    if params is None:
        params = {}

    engine = params.get("engine", "stanza")
    lang = params.get("lang", "es")
    model_package = params.get("model_package", "default")
    use_gpu = params.get("use_gpu", False)

    grammar = Grammar(engine=engine, lang=lang, model=model_package, use_gpu=use_gpu)
    return grammar.parse(text)
