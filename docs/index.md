# Welcome to Grammatomy

**Grammatomy** is an advanced constituency parsing engine designed to bridge the gap between formal linguistic theory and the pragmatic reality of modern NLP models.

It provides a robust framework for:

*   **Parsing**: Generating syntactic trees using SOTA models (Stanza, Benepar).
*   **Validation**: Auditing tree structures against hybrid grammar rules (AnCora + UD).
*   **Reconstruction**: Repairing flattened or degenerate trees using algorithmic refinement.
*   **Visualization**: Rendering trees in multiple formats (ASCII, Graphviz, JSON).

## Key Features

*   **Hybrid Grammar Support**: Natively handles trees that mix constituent labels (e.g., `sn`, `grup.nom`) with Universal Dependencies tags (e.g., `NOUN`, `DET`).
*   **Edge-Based Reconstruction**: A novel algorithm that "rehydrates" flattened structures by inferring missing intermediate nodes based on production patterns.
*   **Strict & Lax Validation**: Dual-mode validation to support both rigorous academic standards and flexible production pipelines.
*   **Model Sovereignty**: Designed to run locally with full control over model resources.

## Getting Started

If you are a developer or linguist looking to understand the internal mechanics of Grammatomy, we recommend starting with the **Technical Guides**:

1.  **Algorithm Overview**: A high-level visual guide to the core logic.
2.  **Validation & Reconstruction**: The theoretical foundation of our hybrid approach.
3.  **Algorithm Deep Dive**: A step-by-step analysis of the code.

## API Reference

For detailed documentation of the Python modules, classes, and functions, visit the **API Reference** section.

---

*Grammatomy is an open-source project developed by [Your Name/Organization].*

<div align="center">
  <small>"Caminante, no hay camino, se hace camino al andar."</small>
</div>