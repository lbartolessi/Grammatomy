#!/usr/bin/env python3
"""
Grammatomy Probe: Multilingual Tagset Inspector.
Diagnoses the raw output of constituency parsers to determine the native tagset.
"""
import logging

import spacy
import stanza

# Configure logging
logging.getLogger("stanza").setLevel(logging.WARNING)


def _traverse_stanza_tree(node):
    """
    Traverses Stanza tree to find leaves and their parents.
    Format: (Parent -> Leaf)
    """
    if node.is_leaf():
        return
    if all(child.is_leaf() for child in node.children):
        # This is a Pre-Terminal (POS tag) -> Terminal (Word)
        print(f"  Word: '{node.children[0].label:15}' | Tag: '{node.label}'")
    else:
        for child in node.children:
            _traverse_stanza_tree(child)


def probe_stanza_es():
    print("\n--- 🇪🇸 PROBE: Stanza (Spanish / AnCora) ---")

    sentences = [
        "El gato rápido come pescado.",
        "tengo 200 buenas razones para no necesitar 1346 argumentos el 98,9% de las veces "
        "si trabajo con la versión 2.0 que cuesta 300$ y corre en una GPU de 4Gb.",
    ]

    try:
        # Download minimal requirements if needed
        stanza.download(
            "es",
            processors="tokenize,pos,constituency",
            package="default_accurate",
            verbose=False,
        )

        nlp = stanza.Pipeline(
            "es",
            processors="tokenize,pos,constituency",
            package="default_accurate",
            verbose=False,
            use_gpu=True,
        )

        for i, text in enumerate(sentences):
            print(f'\n[{i+1}] Analyzing: "{text[:60]}..."')
            doc = nlp(text)

            tree = doc.sentences[0].constituency  # type: ignore
            print(f"Raw Tree String: {tree}")

            print("\nLeaf Tag Analysis:")
            _traverse_stanza_tree(tree)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Probe Failed: {e}")


def probe_spacy_benepar_en():
    print("\n--- 🇺🇸 PROBE: Benepar (English / PTB) ---")
    try:
        # Assuming benepar_en3 is installed via our manage_models.py
        import benepar  # pylint: disable=unused-import, import-outside-toplevel, reimported

        if not spacy.util.is_package("en_core_web_md"):
            spacy.cli.download("en_core_web_md")  # type: ignore

        nlp = spacy.load("en_core_web_md")
        if "benepar" not in nlp.pipe_names:
            nlp.add_pipe("benepar", config={"model": "benepar_en3"})

        doc = nlp("The quick cat eats fish.")
        sent = list(doc.sents)[0]

        print(f"Raw Parse String: {sent._.parse_string}")
        print("\nLeaf Tag Analysis:")
        for token in sent:
            # Benepar injects labels into the tree, but let's see what the leaves correspond to
            # We look at the parent of the leaf in the parse tree
            parent = token._.parent
            if parent:
                print(f"  Word: '{token.text:10}' | Tag: '{parent._.labels}'")

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Probe Failed: {e}")
        print("Note: Ensure 'benepar_en3' is downloaded via tools/manage_models.py")


if __name__ == "__main__":
    print("🔍 Initiating Tagset Probe...")
    probe_stanza_es()
    # probe_spacy_benepar_en() # Optional comparison
    print("\nProbe Complete.")
