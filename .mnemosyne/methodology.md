# METHODOLOGY (Méthodos)

> INSTRUCTION: This file records our habits, technical standards, and craftsmanship style.
> UPDATE RULE: Update this file ONLY when:
>
> 1. A new architectural pattern is successfully implemented.
> 2. We explicitly decide to change a coding standard or technical preference.
> 3. A conflict between current methods and a new solution is resolved.
>    ACTION: Update below the tag. Keep it concise, focused on "how" we work.

## UPDATABLE CONTENT

- Initial status: Exploratory phase.
- **Model Sovereignty:** Critical models must be persisted locally. Runtime dependency on external repositories (Hugging Face, Stanford) is minimized to setup/maintenance phases, not production execution.
- **Qualitative Validation:** We prioritize linguistic accuracy on specific structural edge cases (ambiguity, recursion, ellipsis) over generic F1 scores. Model selection should be task-specific based on these qualitative behaviors.
- **Native Syntactic Testing:** Syntactic ambiguity tests must be constructed specifically for the target language's grammar (e.g., Spanish morphology), avoiding direct translation of foreign "garden path" sentences that may lose their ambiguity.
- **Core-First Layering:** Architecture follows a strict dependency hierarchy: Lib (Logic) -> API/CLI (Interface) -> Studio (GUI). Logic resides exclusively in the core (SSOT) and never leaks upwards.
- **Zero-Config Philosophy:** End-user deliverables must be self-contained (frozen binaries), requiring no knowledge of Python environments.
- **Automated Resource Management:** Heavy assets (models) are managed by an internal "Resource Manager" that handles detection, download, and configuration transparently.
- **Standard-Based & Style-Flexible UI:** The user interface will be built with standard Web Components (via Lit) rendering in the Light DOM. This prioritizes interoperability and component reusability while ensuring full compatibility with global CSS frameworks, avoiding both framework lock-in and Shadow DOM styling limitations.
- **Radical Usability (The Hostile User Test):** Every end-user-facing feature must be designed to be immediately understandable and usable by a non-technical, technology-averse domain expert. If a feature requires explanation, its design has failed.
- **Native Tagset Preservation:** We explicitly reject the normalization or translation of linguistic tags across languages. Each model's notation (AnCora, PTB, VIT, CINTIL) is rooted in a specific academic tradition and structural logic that cannot be mapped without loss of nuance. The tool exposes the raw, native nomenclature of the underlying model, requiring the user to adapt to the specific standard of the language being analyzed, rather than enforcing a synthetic universal interoperability.
