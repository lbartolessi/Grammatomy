# Policy: Node Editing, Validation, and Transformation

> **Status:** Active | **Version:** 1.0 | **Scope:** Grammatomy Studio

This document formalizes the "Decalogue" of rules governing the structural manipulation of syntax trees within the editor. These principles prioritize user freedom and informative feedback over restrictive prevention.

## The Decalogue

1.  **Mandatory Descendant Validation:** When validating a node for mandatory children, the *entire descendant tree* (children, grandchildren, etc.) must be traversed until at least one of the required tags is found. If none are found after a full search, the node is marked as invalid. The logic assumes an "OR" condition (at least one of the list).

2.  **Exhaustive Validation:** The system performs a complete validation of the entire tree structure. No pruning optimization is applied based on invalid states; every node is evaluated to provide comprehensive feedback.

3.  **Ghost on Last Child Deletion:** When a node is deleted, if it was the last child of its parent, a new ghost node must be automatically added to the parent. Subsequently, the entire ancestor line must be re-validated, as a required descendant may have been removed.

4.  **Permissive Deletion:** The system will **never** prevent the user from deleting a mandatory node. Instead, it will rely on the validation mechanism (Rule #3) to correctly mark the ancestor as invalid, informing the user of the structural error without blocking the action.

5.  **Move-to-Ghost as Replacement:** When a node is moved onto a ghost node, it **replaces** the ghost node. It does not become a child of the ghost. The moved node is attached to the ghost's original parent.

6.  **Upwards Validation Cascade:** After any state-changing operation (moving a node, changing a tag, resolving a ghost), the entire ancestor line of the affected nodes must be re-validated to check if any previously invalid nodes have now become valid.

7.  **Future-Proofing for Copy/Paste:** These rules will apply equally to future Copy, Cut, and Paste operations.

8.  **Immediate Visual Feedback:** Any change to a node's state (e.g., becoming invalid) must be reflected instantly in its visual representation in the UI.

9.  **Structural Primacy:** These rules are of paramount structural importance and must always be applied in a safe and stable manner.

10. **Unalterable Priority:** No performance or other consideration takes precedence over the strict application of these rules.