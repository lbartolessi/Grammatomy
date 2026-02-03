#!/usr/bin/env python3
"""
Batch Validation Tool for Grammatomy.

This script runs a stress test on the configured parsers (Stanza/Benepar)
using complex sentences from multiple languages. It applies the current
metasyntactic rules and generates a consolidated report of warnings.

Usage:
    python tools/batch_validation.py
"""

import logging
import os
import sys

# Ensure src is in path to import grammatomy modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from grammatomy import get_syntax_tree
from grammatomy.validation import validate_structure

# Configure logging to console only, clean format
logging.basicConfig(format="%(message)s", level=logging.INFO)

# --- STRESS CORPUS ---
# A collection of sentences designed to trigger complex syntactic structures.
CORPUS = [
    {
        "lang": "es",
        "engine": "stanza",
        "desc": "Spanish Complex (Subordination & Coordination)",
        "text": (
            "Mientras el comité deliberaba sobre la conveniencia de aceptar un plan que "
            "prometía simplificar los procedimientos, algunos miembros optaron por aplazar "
            "una votación que revelaba tensiones latentes."
        ),
    },
    {
        "lang": "es",
        "engine": "stanza",
        "desc": "Spanish Mixed (Direct Object & Prepositions)",
        "text": "El veloz murciélago hindú comía feliz cardillo y kiwi en la cueva.",
    },
    {
        "lang": "en",
        "engine": "spacy",  # Uses Benepar
        "desc": "English Standard (PTB)",
        "text": "The scientist confirmed that the results significantly contradict the previous theories.",
    },
    {
        "lang": "pt",
        "engine": "stanza",
        "desc": "Portuguese (CINTIL / CharLM)",
        "text": "As armas e os barões assinalados, que da ocidental praia lusitana, por mares nunca de antes navegados, passaram ainda além da Taprobana.",
    },
    {
        "lang": "it",
        "engine": "stanza",
        "desc": "Italian (VIT / CharLM)",
        "text": "Nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura, ché la diritta via era smarrita.",
    },
]


def run_batch_validation():
    print("=" * 60)
    print(" 🕵️  GRAMMATOMY BATCH VALIDATION REPORT")
    print("=" * 60 + "\n")

    total_warnings = 0

    for item in CORPUS:
        lang = item["lang"]
        engine = item["engine"]
        desc = item["desc"]
        text = item["text"]

        print(f"🔹 [{lang.upper()}] {desc} (Engine: {engine})")
        print(f'   Input: "{text[:70]}..."')

        try:
            # 1. Parse
            # Note: We suppress internal logs to keep the report clean
            root = get_syntax_tree(text, params={"lang": lang, "engine": engine})

            if not root:
                print("   ❌ Parsing Failed: No tree returned.")
                continue

            # 2. Validate
            warnings = validate_structure(root)

            if not warnings:
                print("   ✅ Structure OK (Compliant with current rules)")
            else:
                print(f"   ⚠️  {len(warnings)} Metasyntax Warnings:")
                for w in warnings.values():
                    print(f"      - {w}")
                total_warnings += len(warnings)

        except Exception as e:
            print(f"   ❌ Execution Error: {e}")

        print("-" * 60)

    print(
        f"\nSUMMARY: {total_warnings} warnings detected across {len(CORPUS)} test cases."
    )
    print("=" * 60)


if __name__ == "__main__":
    run_batch_validation()
