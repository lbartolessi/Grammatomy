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
