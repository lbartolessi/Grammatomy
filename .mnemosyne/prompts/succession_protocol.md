# SUCCESSION PROTOCOL (N+1 Eromena)

This protocol triggers when a Chapter reaches its capacity (~800 lines).

1. ANALYZE: Review the current chapter.
2. SUMMARIZE: Write a "Wayfarer's Summary" (5-10 lines) of key progress and pending blockers.
3. SYNC: Check if 'itinerary.md' or 'methodology.md' need a final update before closing the chapter.
4. CALCULATE N+1:
   - Current is Chapter N (e.g., 001).
   - Target is N+1 (e.g., 002).
5. SPAWN: Create `.mnemosyne/chronicles/chapter_[N+1].md`.
6. CARRY OVER: Start the new chapter with:
   "CONTINUED FROM CHAPTER [N].
   SUMMARY: [Insert Wayfarer's Summary here]
   NEXT IMMEDIATE STEP: [The very next task from Itinerary]"
7. ARCHIVE: Close the previous chapter file. Do not write in it again.

8. **LABELING & TAXONOMY (Suggested Style):**
   When summarizing or creating the "Wayfarer's Summary", use bold labels to categorize information. You are free to create new labels, but consider these established patterns:
   - **[NATURE OF WORK]**: Use labels like **Refactoring**, **Fix**, **Feature**, or **Cleanup** to define the action.
   - **[STRATEGIC WEIGHT]**: Use **Architectural Decision**, **Milestone**, or **Strategic Pivot** for high-impact changes.
   - **[RATIONALE]**: Always include a **Reasoning**, **Root Cause**, or **Impact** tag to explain why a decision was made.
   - **[STATE]**: Clearly mark **Pending**, **Blocked**, or **Stable** status.

   *Note: These labels are suggestions based on successful past iterations. Adapt, merge, or invent new ones if the current "Path" requires a different vocabulary.*
