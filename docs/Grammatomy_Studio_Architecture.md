# Grammatomy Studio: System Architecture & User Workflows

## Executive Summary

Grammatomy Studio is an interactive visual editor for **syntactic parse trees** built around the principles of linguistic rigor and computational pragmatism. It enables users to:

1. **Decompose** complex sentences into manageable subtrees (using AnCora `S` tags as cut points)
2. **Edit** individual trees under strict grammatical constraints (enforced by `hybrid_rules.yaml`)
3. **Recompose** subtrees back into unified structures
4. **Annotate** trees at multiple levels with Markdown documentation
5. **Export** in multiple formats for downstream consumption

The system is architected as a **Platonic Dualism**: a rigorous backend (anytree realm) communicating with a pragmatic frontend (web visualization layer) via REST JSON API, using Penn Treebank S-expression format for serialization.

---

## 1. User Journey & Core Workflow

### 1.1 Project Genesis

```
User uploads text (sonnet, article, speech, etc.)
    ↓
System identifies sentence boundaries (primarily `.` delimiters)
    ↓
For each sentence:
    - Stanza/Benepar generates parse tree
    - Tree is traversed and decomposed at AnCora `S` tag boundaries
    ↓
User views decomposed tree forest in editor
```

### 1.2 Tree Decomposition Strategy

**Why `S` (Sentence) tags?**

The `S` tag is chosen as the decomposition boundary because it represents:
- **Linguistic Naturalness**: `S` nodes inherently represent clausal constituents (main clauses, subordinate clauses, relative clauses)
- **Plug & Play Semantics**: Clauses can be naturally embedded or referenced without structural corruption
- **Preservation of Meaning**: Extracting an `S` subtree preserves its semantic and syntactic completeness
- **Multi-Language Applicability**: This strategy applies uniformly across AnCora (Spanish), Penn Treebank (English), VIT (Italian), CINTIL (Portuguese)

**Example Decomposition**:

Input tree:
```
(S (sn (NOUN María))
   (grup.verb (VERB vio)
              (sp (ADP en)
                  (S (sn (NOUN parque))
                     (grup.verb (VERB estaba))))))
```

Decomposition at `S` boundaries:
- **Main Tree**: `(S (sn (NOUN María)) (grup.verb (VERB vio) (LINK→TreeA)))`
- **Tree A**: `(S (sn (NOUN parque)) (grup.verb (VERB estaba)))`

### 1.3 Tree Linking Mechanism

When a subtree is extracted at an `S` node:

1. **Child Tree**:
   - Retains a replica of the `S` root node
   - Adds a **triangular node** (LINK) pointing back to parent tree
   - LINK label = parent tree name (e.g., "MainTree")

2. **Parent Tree**:
   - Original `S` node replaced with **triangular node** (LINK)
   - LINK label = child tree name (e.g., "TreeA")
   - Connection is bidirectional via named references

3. **Tree Naming Convention**:
   - Root tree containing `ROOT` token: `"MainTree"` (fixed)
   - Extracted subtrees: `"TreeA"`, `"TreeB"`, `"TreeC"`, etc. (sequential alphabetic suffix)

**Bidirectional Navigation**:
- User can click a LINK node in the parent → jumps to child tree editor
- User can click the back-reference LINK in the child → returns to parent context
- Visual indication: triangular/hollow nodes distinguish links from regular constituents

---

## 2. Tree Structure & Node Operations

### 2.1 Node Taxonomy

| Category | Examples | Properties |
|----------|----------|-----------|
| **Phrasal Nodes** | `sn`, `sp`, `grup.nom`, `grup.verb`, `sentence` | Interior nodes; subject to production rules |
| **POS Tags** | `NOUN`, `VERB`, `ADP`, `DET`, `ADJ`, `PUNCT`, `PROPN` | Pre-terminal; yield lexical tokens |
| **Leaf Tokens** | `"María"`, `"vio"`, `"en"` | Terminal symbols; text content |
| **Structural Links** | LINK nodes (triangular) | Special nodes for inter-tree references; not subject to validation rules |
| **Special Roots** | `ROOT`, `S`, `sentence` | Root-level constituents; appear at tree tops |

### 2.2 Permitted Edit Operations

All edit operations are subject to grammatical constraints enforced by `ValidationEngine`:

| Operation | Scope | Constraint Check |
|-----------|-------|-------------------|
| **Insert Node** | After any interior node | `can_add_child()`: new child tag in parent's `allowed_children` set |
| **Create Node** | At any position | New node type must have valid parent in current context |
| **Delete Node** | Immediate child only | `can_delete_child()`: deletion doesn't violate parent's `mandatory_children` |
| **Rename Node** | Any interior node | `get_valid_substitutions()`: new tag compatible with parent + siblings |
| **Copy/Paste** | Subtree operation | Pasted root must be valid child of target parent |
| **Move Node** | Between sibling positions | Tree shape remains valid; no cycles introduced |

### 2.3 Real-Time Validation

Post-Operation Behavior:

```
User makes edit (insert, delete, rename, move)
    ↓
Backend ValidationEngine runs:
    - Strict validation on modified node (pattern matching)
    - Lax validation on parent (yield presence check)
    - Propagation check up the tree to root
    ↓
Result:
    ✓ Valid   → Tree updates; UI shows green checkmark
    ✗ Invalid → Revert operation; show error message (rule violated)
```

**Two Validation Strategies** (see attached `validation_and_reconstruction.md`):

- **Strict Mode**: Children sequence must exactly match a production rule pattern
- **Lax Mode**: Essential content (mandatory yield) must exist somewhere in subtree (used for raw parser output)

---

## 3. Decomposition & Recomposition Operations

### 3.1 Automatic Decomposition

**Trigger**: Project creation (when Stanza parses input text)

**Algorithm**:
1. Traverse tree in post-order (bottom-up)
2. At each `S` node, check if it is a child of `sentence` or another `S`
3. If yes, extract it as a new subtree
4. Replace with LINK node in parent
5. Create new tree entry with sequential name (A, B, C...)
6. Maintain bidirectional reference links

**Example Output**:
- Input: One raw parse tree
- Output: Forest of 1–N trees (MainTree + A, B, C...)

### 3.2 Manual Decomposition (User-Initiated Split)

**Interaction**:
```
User right-clicks any interior node N with subtree content
    ↓
Menu option: "Extract as subtree"
    ↓
System checks: Is N a natural cleavage point?
    (User chose to split here; system doesn't restrict by S-tag in manual mode)
    ↓
Extraction performed (same as automatic, but at user-chosen node)
    ↓
New subtree created with LINK references established
```

**Design Note**: Manual extraction at non-`S` nodes is permitted because:
- Users may identify linguistically meaningful splits not marked by parser
- Advanced linguistic analysis may require granular decomposition
- System trusts user expertise while enforcing grammar rules post-split

### 3.3 Recomposition (Reabsorption)

**Interaction**:
```
User views subtree editor (TreeA)
    ↓
User clicks "Reabsorb" button (or "Merge with Parent")
    ↓
System performs inverse of decomposition:
    1. Remove LINK→Parent node from child tree
    2. Replace LINK node in parent with original subtree content
    3. Delete child tree entry
    4. Update naming (remaining trees: shift labels if needed)
    ↓
Result: Unified tree in MainTree; TreeA entry removed from project
```

**Atomicity**: Reabsorption is an atomic operation. Entire subtree (with all descendants) is seamlessly folded back.

**Limitations & Known Issues** (from user report):

> _User observation: "Creo que Gemini metio cosas en el web... en el tema de las reabsorciones y desgajamientos que no acaban de funcionar bien."_

**Hypothesis for Investigation**:
- Some state management for tree linking may reside in frontend component (Vue/Lit logic)
- Bidirectional reference updates may not always propagate correctly
- Possible race conditions if backend and frontend decomposition logic diverge
- **Recommendation**: Audit `src/web/` components for tree mutation logic; ensure all decomposition/recomposition operations delegate to backend

---

## 4. Project & Tree Metadata

### 4.1 Hierarchical Documentation

Every scope level can contain variable-length Markdown documentation:

```
Project
├── Project-level notes (scope: entire project context)
│
├── MainTree
│   ├── Tree-level notes (scope: MainTree semantics, overall analysis)
│   │
│   └── Node-level notes
│       ├── Node A: "This subtree encodes a relative clause modifying [...]"
│       ├── Node B: "Etymology note: preposition 'en' can mean 'in' or 'at'"
│       └── ...
│
├── TreeA
│   ├── Tree-level notes
│   └── Node-level notes
│
└── TreeB
    ├── Tree-level notes
    └── Node-level notes
```

### 4.2 Persistent Annotation

- Markdown documents are stored with tree metadata (not serialized in Penn Treebank format)
- Survives round-trip export/import cycles
- User-facing editor provides inline Markdown editor alongside tree visualization
- Comments can reference specific nodes by ID for precise linguistic annotation

---

## 5. System Architecture: Platonic Dualism

### 5.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Web Browser)                        │
│                  ┌──────────────────────────────┐                │
│                  │  Lit Web Components          │                │
│                  │  - Tree Visualizer           │                │
│                  │  - Node Editor (forms)       │                │
│                  │  - Cytoscape Graph           │                │
│                  │  - Markdown Editor           │                │
│                  │  - Split/Reabsorb UI         │                │
│                  └──────────────────────────────┘                │
│                           ↕ (REST JSON API)                      │
├─────────────────────────────────────────────────────────────────┤
│                     REST API Gateway                             │
│                   (Flask: src/api/app/)                          │
├─────────────────────────────────────────────────────────────────┤
│                    Backend (Python anytree)                      │
│                  ┌──────────────────────────────┐                │
│                  │  Core Logic Layer            │                │
│                  │                              │                │
│                  │  - LispParser                │                │
│                  │  - ValidationEngine          │                │
│                  │  - EdgeBasedReconstructor    │                │
│                  │  - TreeManipulator           │                │
│                  │  - ProjectManager            │                │
│                  │  - DecompositionEngine       │                │
│                  │                              │                │
│                  │  Data: anytree.NodeMixin     │                │
│                  │  Grammar: hybrid_rules.yaml  │                │
│                  └──────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 The Frontend: "The Cave" 🗝️

**Responsibilities**:
- **Rendering**: Display anytree structures as interactive graphs (Cytoscape)
- **Interaction Handling**: User clicks, drags, form submissions
- **Optimistic UI**: Show pending changes while request is in-flight
- **Visualization Customization**: Colors, node shapes, layout algorithms
- **Local State**: Scroll position, zoom level, selected node highlighting

**Key Components**:
- `TreeVisualizer`: Cytoscape-based renderer
- `NodeEditor`: Form-based property editor (drag-and-drop fields)
- `SplitUI`: Controls for tree decomposition/reabsorption
- `MarkdownPanel`: Annotation editor

**Constraints**:
- ❌ **DO NOT** perform tree mutations directly
- ❌ **DO NOT** validate rules locally (rule changes require backend updates)
- ✅ **DO** delegate all edits to backend via API calls
- ✅ **DO** cache trees locally for performance but treat as stale after every mutation

### 5.3 The Backend: "The Platonic Realm" 🏛️

**Responsibilities**:
- **Tree Storage**: anytree in-memory or database persistence
- **Business Logic**: All node operations (insert, delete, rename, move, copy)
- **Validation**: Rule enforcement via `ValidationEngine` and `hybrid_rules.yaml`
- **Reconstruction**: Rehydrating flattened trees via `EdgeBasedReconstructor`
- **Serialization**: Converting between anytree ↔ Penn Treebank format
- **Decomposition**: Splitting trees at `S` boundaries; managing LINK nodes

**Key Modules**:
- `LispParser`: PTB S-expression → anytree deserialization
- `ValidationEngine`: Post-hoc and preventive grammar checking
- `EdgeBasedReconstructor`: Tree repair algorithm
- `DecompositionEngine`: Tree splitting/merging logic
- `ProjectManager`: Metadata and tree forest management

**Guarantees**:
- ✅ All mutations maintain grammatical validity
- ✅ All trees in project are internally consistent
- ✅ LINK references are always bidirectional and resolvable
- ✅ No cycles; forest structure is DAG-safe

### 5.4 Communication Protocol: REST JSON API

**Serialization Format**: Penn Treebank S-expressions

```json
{
  "operation": "get_tree",
  "tree_id": "MainTree",
  "response": {
    "ptb": "(S (sn (NOUN María)) (grup.verb (VERB vio)))",
    "tree_hash": "abc123def456",
    "validation_status": "valid",
    "metadata": {
      "notes": "Main clause describing action",
      "created_at": "2025-02-15T10:30:00Z",
      "modifications": 3
    }
  }
}
```

**Typical Flow**:

```
User action (e.g., rename node)
    ↓
Frontend: POST /api/trees/{tree_id}/nodes/{node_id}
          Body: { "operation": "rename", "new_label": "sp" }
    ↓
Backend: Locate node, validate new label with ValidationEngine
         If valid: update anytree, return success
         If invalid: return 400 with error reason
    ↓
Frontend: Update local visualization from response PTB
```

---

## 6. Data Serialization: Penn Treebank Format

### 6.1 Serialization Strategy

**Why Penn Treebank?**

1. **Human-Readable**: S-expressions are self-documenting; easy to debug
2. **Lossless**: Encodes complete tree structure without ambiguity
3. **Linguistic Standard**: Industry standard for syntactic trees
4. **Compact**: Significantly smaller than JSON representation
5. **LISP Compatibility**: Close to Lisp syntax; facilitates symbolic manipulation

### 6.2 Format Specification

**Basic Structure**:
```
(Label Child₁ Child₂ ... Childₙ)
```

**Terminal Rule**:
```
LexicalNode → (PreTerminal Leaf)
Example: (NOUN "gato")
```

**Interior Node**:
```
InteriorNode → (Label Interior₁ Interior₂ ... Leafₙ)
Example: (sn (DET "el") (NOUN "gato"))
```

**LINK Nodes** (Special):
```
(LINK "TreeA")    ← Reference to subtree named TreeA
(LINK→MainTree)   ← Alternative notation with directional arrow
```

### 6.3 Round-Trip Guarantees

```
anytree Tree
    ↓
Serialization (LispParser.tree_to_ptb)
    ↓
PTB S-expression string
    ↓
API transmission (JSON wire format)
    ↓
Deserialization (LispParser.ptb_to_tree)
    ↓
anytree Tree
    
Invariant: Tree₀ ≡ Tree₁ (structure-preserving)
```

---

## 7. Validation & Reconstruction Pipeline

**See attached documentation**:
- [validation_and_reconstruction.md](validation_and_reconstruction.md)
- [algorithm_overview.md](algorithm_overview.md)
- [algorithm_deep_dive.md](algorithm_deep_dive.md)

### 7.1 Quick Reference

| Phase | Actor | Input | Algorithm | Output |
|-------|-------|-------|-----------|--------|
| **Parsing** | Stanza/Benepar | Raw text | Dependency/Constituency | Tree (possibly flattened) |
| **Lax Validation** | `ValidationEngine` | Tree | Yield presence check | Pass/Fail (indicates if repair needed) |
| **Reconstruction** | `EdgeBasedReconstructor` | Tree | Pattern-based node insertion | Canonical tree |
| **Strict Validation** | `ValidationEngine` | Tree | Exact pattern matching | Pass/Fail (final verification) |
| **Decomposition** | `DecompositionEngine` | Tree | S-tag boundary detection | Forest of subtrees with LINKs |

---

## 8. Exports & Downstream Consumption

### 8.1 Export Formats (Planned/Implemented)

| Format | Use Case | File Extension |
|--------|----------|---|
| **Penn Treebank** | Symbolic processing, NLP pipelines | `.ptb`, `.txt` |
| **JSON**         | API consumption, downstream tools | `.json` |
| **CoNLL-U**      | Dependency conversion, UD compatibility | `.conllu` |
| **LaTeX/TikZ**   | Academic papers, linguistic publications | `.tex` |
| **SVG/PNG**      | Web embedding, documentation | `.svg`, `.png` |
| **Markdown**     | Documentation + annotations | `.md` |
| **XML**          | XSLT processing, transformations | `.xml` |
| **SQL**          | Database ingestion, linguistic corpora | `.sql` |

### 8.2 Round-Trip Fidelity

**Preservation by Format**:
- **Penn Treebank**: ✓ Full (100%) - structure + labels
- **JSON**: ✓ Full with metadata - structure + labels + annotations
- **SVG/PNG**: ✗ Visual only - structure but no editability
- **Markdown**: ✓ Partial - annotations + human-readable summary
- **CoNLL-U**: ✓ Converted - dependency view; round-trip requires constituency→dependency mapping

---

## 9. Current Known Issues & Investigation Points

### 9.1 Frontend Decomposition Logic

**Issue Report** (User):
> "Creo que Gemini metio cosas en el web... en el tema de las reabsorciones y desgajamientos que no acaban de funcionar bien."

**Analysis**:

1. **Hypothesis**: Frontend components (`src/web/`) may contain business logic for tree mutations (decomposition/reabsorption) instead of delegating entirely to backend.

2. **Red Flags to Check**:
   - Presence of tree structure mutation code in Vue/Lit component lifecycle hooks
   - Local state updates for LINK nodes without backend confirmation
   - Missing `await` statements for API calls (suggesting optimistic updates gone awry)
   - Duplicated validation logic (frontend rules ≠ backend rules in `hybrid_rules.yaml`)

3. **Recommended Audit**:
   ```bash
   # Find suspect code patterns in frontend
   grep -r "decompose\|split\|reabsorb\|LINK" src/web/ --include="*.js" --include="*.ts" --include="*.vue"
   grep -r "NodeMixin\|anytree\|mutation" src/web/ --include="*.js" --include="*.ts"
   ```

4. **Corrective Actions**:
   - ✅ Ensure all decomposition API calls await backend response
   - ✅ Remove local tree structure mutations from frontend
   - ✅ Add request/response logging to debug state divergence
   - ✅ Implement optimistic locking for concurrent edits

### 9.2 Bidirectional Reference Consistency

**Risk**: After multiple decomposition/reabsorption cycles, LINK nodes may become stale or refer to non-existent trees.

**Mitigation**:
- Backend maintains referential integrity checks (`DecompositionEngine._validate_links()`)
- On each mutation, perform transitive closure check: ensure all reachable references are resolvable
- API response includes tree forest state (list of valid tree IDs) for client-side validation

---

## 10. Architectural Observations & Recommendations

### 10.1 Observed Strengths

1. **Clear Separation of Concerns**: Backend = computation; Frontend = visualization
2. **Grammar-Centric Design**: `hybrid_rules.yaml` is single source of truth
3. **Composable Components**: Web visualizer can be imported into other apps
4. **Linguistic Rigor**: Two-level validation (lax for pragmatism, strict for accuracy)
5. **Multilingual Foundation**: Architecture supports Spanish + future language plugins

### 10.2 Architectural Debt & Risks

1. **Frontend Logic Leak**: Unconfirmed but suspected business logic in web components
2. **No Concurrency Control**: What happens if two users edit the same project simultaneously?
3. **Unspecified Persistence Layer**: How are projects stored? (Memory? SQLite? PostgreSQL?)
4. **Missing Error Recovery**: What happens if an API call fails mid-operation?
5. **Incomplete Export Coverage**: Some advertised formats may not be fully implemented

### 10.3 Recommendations

| Priority | Area | Action |
|----------|------|--------|
| HIGH | Frontend Audit | Verify no business logic in web components; all mutations → API |
| HIGH | API Contract | Document all endpoints, request/response schemas, error codes |
| MEDIUM | Testing | Add integration tests for decomposition/reabsorption cycles |
| MEDIUM | Concurrency | Implement optimistic locking or conflict resolution strategy |
| MEDIUM | Observability | Add logging/tracing for tree mutations; audit bidirectional references |
| LOW | Performance | LispParser may be slow for large trees; consider caching or indexing |

---

## 11. Implementation Checklist for Key Features

### 11.1 Core MVP Features (Required)

- [x] Parse text into sentences
- [x] Generate trees with Stanza/Benepar
- [x] Decompose trees at `S` boundaries
- [x] Display trees in Cytoscape visualizer
- [x] Validate trees against `hybrid_rules.yaml`
- [ ] Edit operations (insert, delete, rename, move)
- [ ] Reabsorb subtrees back into parents
- [ ] Markdown annotations at all levels

### 11.2 Advanced Features (Future)

- [ ] Multi-user concurrent editing
- [ ] Real-time collaboration (WebSocket sync)
- [ ] Advanced export formats (LaTeX, SQL)
- [ ] Tree diffing & version history
- [ ] Batch operations on multiple trees
- [ ] Language plugin system for non-Spanish grammars

---

## Appendix: Terminology Reference

| Term | Definition |
|------|-----------|
| **Decomposition** | Process of splitting a tree at `S` nodes into subtrees + LINK references |
| **Reabsorption** | Inverse of decomposition; merging a subtree back into parent |
| **LINK Node** | Triangular placeholder node indicating reference to another tree |
| **Tree Forest** | Collection of related trees (MainTree + A, B, C...) forming a project |
| **Platonic Dualism** | Architectural pattern: backend as "world of ideas" (anytree) + frontend as "cave" (visualization) |
| **Strict Validation** | Grammar check requiring exact pattern match of children |
| **Lax Validation** | Grammar check requiring only mandatory content presence in descendants |
| **Yield** | Set of terminal symbols (leaves) contained in a node's subtree |
| **Reconstruction** | Process of inserting omitted intermediate nodes back into flattened tree |
| **PTB** | Penn Treebank; standard format for syntactic trees using S-expressions |

---

## Related Documentation

- [validation_and_reconstruction.md](validation_and_reconstruction.md) — Grammar enforcement engine
- [algorithm_overview.md](algorithm_overview.md) — High-level algorithm flow
- [algorithm_deep_dive.md](algorithm_deep_dive.md) — Detailed implementation logic
- [Design_Guidelines.md](Design_Guidelines.md) — Front-end component patterns
- [Frontend_Architecture.md](Frontend_Architecture.md) — Web stack details

---

*Last Updated: 2025-02-15*  
*Author: Grammatomy Design Team + AI Assistant*
