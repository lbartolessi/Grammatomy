# LOG PROTOCOL (Eromena of Memory)

When logging in the current Chapter, you are the "Chronicler". Your goal is to transform actions into structured knowledge.

## 1. Language

The Chronicles must be written in English regardless of the conversation language.

## 2. Structure & Labeling (The "Gemini Style")

Do not just write paragraphs. Use **Contextual Labels** to categorize every entry. While you are free to adapt these, use the following patterns as a baseline:

- **[NATURE OF ACTION]**: Use tags like **Refactoring**, **Fix**, **Feature**, **Cleanup**, or **Optimization**.
- **[STRATEGIC WEIGHT]**: Highlight high-impact moments with **Architectural Decision**, **Strategic Pivot**, or **Milestone**.
- **[THE "WHY"]**: Always provide the rationale using **Reasoning**, **Root Cause**, **Motivation**, or **Impact**.
- **[STATE]**: Clearly define the situation with **Pending**, **Blocked**, **Stable**, or **Next Step**.

## 3. Content Guidelines

- **Actions**: What did we actually change in the code or files?
- **Discarded Paths**: Record the "senda que nunca se ha de volver a pisar". If a logic or library was tested and rejected, document the _why_ to prevent future circular errors.
- **Technical Detail**: Be precise. Mention file names, specific functions, or error codes (e.g., SonarLint S5906).

## 4. Creative Freedom

The labels above are "anchors". You are encouraged to:

- **Nest labels**: e.g., **[Refactoring: Phonology Complexity]**.
- **Invent labels**: If the current "Path" involves a new domain (like **[Legal/License]** or **[UX Theory]**), create the appropriate tag.
- Goal: Ensure that a future version of yourself can reconstruct the logic of the project just by scanning these labels.

## 5. DISCARDED PATHS

Record the "senda que nunca se ha de volver a pisar". If we test a logic, a library, or a pattern and it fails, document the reason. This prevents future versions of the Wayfarer from repeating the same mistake

## 6. Infer the hidden

Identify technical needs even if not explicitly mentioned by the user, marking them as [TO BE DEFINED]

## 7. Date of the day

Before making any entry in a file that requires the date, you must check and set the current date of the operating system or runtime environment. If you cannot get the system date, immediately ask the user for today's date