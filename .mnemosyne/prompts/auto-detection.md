# AUTO-DETECTION RULES

> **Purpose:** Define how Copilot automatically detects patterns and triggers MNEMOSYNE workflows.

## 1. TASK DETECTION

**Trigger Phrases** (watch for these in user messages or code comments):
- "Esto debería ser modular"
- "Hay que refactorizar..."
- "Falta documentar..."
- "Necesitamos optimizar..."
- "Este patrón debería reutilizarse"
- "La performance de [X] es baja"
- "Deberíamos agregar pruebas para..."
- "Hay código duplicado en..."

**Action:**
1. Propose a CANDIDATE entry for `itinerary.md`:
   ```
   - [ ] [CANDIDATE] [Domain] Task Description [Detected in Session-YYYY-MM-DD]
   ```
2. Explain why in 1-2 lines
3. Ask: "¿Agregamos esto al itinerary?"
4. On approval, add to itinerary.md and log to chronicle

---

## 2. CHRONICLE LOGGING TRIGGERS

**Significant Action Types** (auto-detect these):

### Code Changes
- **[Feature]** — New capability added
  - Trigger: User implements a new endpoint, function, or module
  - Example: "Implementé la API de mutación"
- **[Fix]** — Bug resolved
  - Trigger: Test suite changes from failing to passing
  - Example: "Corregí el bug de duplicación de hojas"
- **[Refactoring]** — Code restructured (no new features)
  - Trigger: Codebase reorganized, but tests still pass
  - Example: "Moví la lógica de validación al núcleo"

### Infrastructure & Process
- **[Cleanup]** — Files removed, dependencies consolidated
  - Trigger: Deleted files, removed unused imports
- **[Documentation]** — Added/updated docs
  - Trigger: User writes technical guides or API docs
- **[Infrastructure]** — DevOps, CI/CD, tooling
  - Trigger: Docker config, GitHub Actions, test setup

### High-Level Decisions
- **[Architectural Decision]** — Major design choice
  - Trigger: "Decidimos que..." or "Vamos a usar..."
  - Example: "Mutation logic moves to backend (anytree)"
- **[Strategic Pivot]** — Change in project direction
  - Trigger: Abandoning a planned feature or changing approach
  - Example: "Frontend no longer handles complex PTB parse operations"
- **[Milestone]** — Significant achievement
  - Trigger: "100% test pass", "Production-ready", "Completed Phase X"

### Assessment & Analysis
- **[Analysis]** — Investigation without immediate action
  - Trigger: "Investigué [X]..." or "Encontré que..."
  - Example: "Discovered 3 XFAIL tests in ValidationEngine"
- **[Plan]** — Forward-looking strategy
  - Trigger: "Prioritizado...", "Próximas pasos..."

---

## 3. SUCCESSION AUTO-ALERT TRIGGER

**Condition:** Current chapter contains > 25 `[Date]` entries

**Action:**
1. Display: **⚠️ Chapter 008 has 28 entries. Consider SUCCESSION soon.**
2. Link to `.mnemosyne/prompts/succession_protocol.md`
3. Ask: "¿Ejecutamos SUCCESSION?" (user decides, not automatic)

**Why 25?** Average of 2-3 major entries per day × 10-day cycle gives a natural "chapter weight" that indicates closure readiness.

---

## 4. METHODOLOGY UPDATE TRIGGERS

**Pattern Detection:**

When Copilot identifies a new or clarified architectural pattern:

**Examples:**
- "Mutation Engine Architecture: All structural changes now live in Python backend"
- "Validation Asymmetry: Visualization uses Lax logic, Editing uses Strict logic"
- "Session Persistence: Application backend is stateless; persistence via local file I/O"

**Action:**
1. Propose update to `methodology.md`:
   ```
   - **[New Pattern Name]:** [Description]
   ```
2. Explain why (1-2 lines: "This pattern emerged because...")
3. Ask: "Add this to methodology.md?"
4. On approval: Append and log to chronicle

---

## 5. ITINERARY SMART-MARK TRIGGERS

**Condition:** Task appears complete when:
- All relevant tests **PASS** (from test output)
- Code is **committed** or ready for commit
- No **blockers** remain
- User **confirms completion** (optional prompt)

**Action:**
1. Detect task from context: "We just finished [Task X]"
2. Propose: "✅ Mark `[x] Standard Logging Implementation` as DONE in itinerary.md?"
3. On approval: Update itinerary.md and log to chronicle with test output evidence

---

## 6. SESSION RECAP AUTO-TRIGGER

**Condition:** Session ending (user says "goodbye", "bye", "close session", "hasta luego", etc.)

**Action:**
1. Auto-generate recap with:
   - Duration (estimated from timestamps)
   - Chapter and phase
   - Tasks touched (with progress deltas)
   - Blockers (if any)
   - Next session recommendation
   - Files modified
2. Display and ask: "Save this recap to quick-sync.md?"
3. On approval: Append to `quick-sync.md` and update `live-state.json`

---

## 7. WATCHER AUTO-DETECT TRIGGER

**Condition:** Start of each session (AUTO-STARTUP)

**Action:**
1. Scan `.mnemosyne/` for recent file modifications (git timestamps or manual edits)
2. If changes detected:
   - Incorporate them into context
   - Notify user: **"✅ Synced: 2 tasks marked DONE, Chronicle has 27 entries, Methodology updated"**
3. No user action needed (silent background operation)

---

## 8. LIVE-STATE SYNC TRIGGER

**Condition:** Continuous throughout session

**Action:**
1. Track:
   - Current working task (from conversation context)
   - Progress percentage (if task has estimable scope)
   - Last significant action (timestamp + description)
   - Any emergent blockers
2. Update `.mnemosyne/live-state.json` silently (no user notification)
3. Critical blockers: **Notify user immediately**

---

## 9. CONTEXT INTEGRITY CHECK

**Condition:** AUTO-STARTUP 0b (Every session)

**Files to verify:**
- `.mnemosyne/manifesto.md` ✓
- `.mnemosyne/itinerary.md` ✓
- `.mnemosyne/methodology.md` ✓
- `.mnemosyne/chronicles/chapter_[N].md` ✓

**Action on Missing:**
- **STOP** execution
- List missing files
- Ask user: "Restore these files or recreate them?"

---

## 10. AUTO-DETECTION DISABLE (Optional)

User can disable auto-detection by saying:
- "Desactiva auto-detection"
- "Solo manual triggers"
- "Mnemosyne: quiet mode"

Then Copilot:
1. Remains fully synced (AUTO-STARTUP still runs)
2. But **suppresses all proposals** (Smart-Mark, Task Detection, etc.)
3. Only responds to explicit manual triggers (e.g., "Ejecuta SUCCESSION")

To re-enable: "Activa auto-detection"

---

## Notes for Implementation

- All detection should be **soft-touch**: Propose, don't force
- If uncertain whether to trigger: **Ask rather than act**
- Priority: Avoid interrupting user workflow with excessive suggestions
- Log all auto-detected actions to `live-state.json` for transparency
