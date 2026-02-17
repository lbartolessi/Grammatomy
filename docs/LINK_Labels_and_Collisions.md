# LINK Labels and Collision Avoidance

## Overview

To prevent collisions in `LINK-<label>` naming across multiple trees and nested reabsorptions, the codebase now generates unique identifiers (UIDs) for each link created during fragmentation and detach operations.

## Format

Modern LINK nodes follow this format:

```
LINK-<base_label>-<uid>
```

Where:
- **base_label**: Single character from A-Z or Z0, Z1, etc. (e.g., `A`, `B`, `Q`, `R`)
- **uid**: 8-character hexadecimal suffix generated via `uuid.uuid4().hex[:8]`

### Example

```
LINK-A-d74b945d
LINK-B-52f8aab3
LINK-R-7ee98ebb
```

## Backward Compatibility

The implementation supports both:

1. **Old format** (no UID): `LINK-A` 
2. **New format** (with UID): `LINK-A-d74b945d`
3. **Tolerant fallback** (for hand-crafted or legacy PTBs)

The matching logic in `MutationEngine.reabsorb()` searches for:
- Exact match on `LINK-<label>` (old format)
- Prefix match on `LINK-<label>-` (new format with any UID)

If multiple candidates are found, an error is raised to prevent silent corruption.

## Files Updated

### Core Engines

- **`src/core/grammatomy/mutation.py`**
  - `MutationEngine.detach()`: Generates unique `LINK-<label>-<uid>` for both forward and back links
  - `MutationEngine.reabsorb()`: Accepts both old and new formats; matches by base label

- **`src/core/grammatomy/fragmentation.py`**
  - `FragmentationEngine.fragment()`: Generates unique `LINK-<label>-<uid>` for all extracted subtrees
  - Uses the same matching strategy as reabsorb

### API

- **`src/api/app/routers/mutation.py`**
  - Passes `link_label` (base label only) to `MutationEngine.reabsorb()`
  - No API-level changes needed—backward compatible

### Frontend

- **`src/web/src/grammatomy-app.ts`**
  - Continues to pass `subtree.label` (single character) to `/api/mutation/reabsorb`
  - Fully compatible with both old and new link formats
  - No UI changes needed

## No More Collisions

With UUID-based suffixes:

✓ All LINK labels are globally unique  
✓ Multiple projects can use the same labels (A, B, C...) without interference  
✓ Nested reabsorptions are safe  
✓ Legacy PTBs with old format still work  

## Testing

Run the validation snippets in `/pruebas PTB` to verify:

```bash
# Detach from a tree (creates new unique links)
# Reabsorb the fragment back (matches by base label)
# Verify no collisions across multiple trees
```

## Impact Assessment

- **Backward compatible**: Yes (old format still recognized)
- **Breaking changes**: None (all endpoints remain the same)
- **Performance**: Negligible (UUID generation on detach only)
- **Storage**: Slightly larger PTB strings (~8 chars per link)
