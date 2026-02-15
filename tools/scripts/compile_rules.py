#!/usr/bin/env python3
"""
Compilador de Reglas Gramaticales.

Transforma 'ancora_canonical.yaml' (reglas puras) en 'hybrid_rules.yaml' (reglas de producción),
inyectando compatibilidad con Universal Dependencies (UD) y Stanza.
"""

import itertools
import logging
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RuleCompiler")

# Mapeo de Transparencia: AnCora -> UD
# Se inyectarán estas etiquetas en los patrones que contengan la clave.
UD_INJECTION_MAP = {
    "n": ["NOUN", "PROPN"],
    "v": ["VERB", "AUX"],
    "a": ["ADJ"],
    "d": ["DET"],
    "r": ["ADV"],
    "p": ["PRON"],
    "s": ["ADP"],
    "c": ["CCONJ", "SCONJ"],
    "z": ["NUM"],
    "w": ["NOUN", "NUM"],  # Fechas a veces son NOUN o NUM
    "f": ["PUNCT", "SYM"],
    "i": ["INTJ"],
}

BASE_PATH = Path(__file__).resolve().parents[2] / "src" / "core" / "grammatomy" / "assets" / "rules"
INPUT_FILE = BASE_PATH / "ancora_canonical.yaml"
OUTPUT_FILE = BASE_PATH / "hybrid_rules.yaml"


def compile_rules():
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    canonical_nodes = data.get("nodes", [])
    hybrid_nodes = []

    # 1. Procesar Nodos Estructurales
    for node in canonical_nodes:
        new_node = node.copy()

        # Expandir Allowed Children
        if "allowed_children" in new_node:
            # Normalize list to dict structure for processing
            if isinstance(new_node["allowed_children"], list):
                new_node["allowed_children"] = {"optional": list(new_node["allowed_children"])}

            for category in ["mandatory", "optional"]:
                if category in new_node["allowed_children"]:
                    original_list = new_node["allowed_children"][category]
                    expanded_list = []
                    for tag in original_list:
                        if tag in UD_INJECTION_MAP:
                            expanded_list.extend(UD_INJECTION_MAP[tag])
                        else:
                            expanded_list.append(tag)
                    new_node["allowed_children"][category] = sorted(list(set(expanded_list)))

        # Expandir Patrones
        if "patterns" in new_node:
            new_patterns = []
            for pattern in new_node["patterns"]:
                # Generar todas las combinaciones posibles (Producto Cartesiano)
                # Si el patrón es [n, s.a], y n->[NOUN, PROPN], generamos:
                # [NOUN, s.a] y [PROPN, s.a]
                slot_options = []
                for item in pattern:
                    if item in UD_INJECTION_MAP:
                        slot_options.append(UD_INJECTION_MAP[item])
                    else:
                        slot_options.append([item])

                for p in itertools.product(*slot_options):
                    new_patterns.append(list(p))

            new_node["patterns"] = new_patterns

        hybrid_nodes.append(new_node)

    # 2. Añadir definiciones de Hojas UD explícitas
    # Para que el validador sepa que NOUN es una hoja válida
    ud_leaves = set()
    for tags in UD_INJECTION_MAP.values():
        ud_leaves.update(tags)

    for leaf_tag in sorted(list(ud_leaves)):
        # Evitar duplicados si ya existen en el canónico (raro)
        if not any(n["id"] == leaf_tag for n in hybrid_nodes):
            hybrid_nodes.append({"id": leaf_tag, "type": "leaf"})

    # Guardar
    output_data = {
        "tree_config": {
            "language": "es",
            "description": "Hybrid AnCora + UD Rules (Auto-compiled)",
            "version": "2.3-auto",
        },
        "nodes": hybrid_nodes,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(output_data, f, sort_keys=False, allow_unicode=True)

    logger.info(f"Successfully compiled hybrid rules to: {OUTPUT_FILE}")


if __name__ == "__main__":
    compile_rules()
