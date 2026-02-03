# User Personas and Use Cases

> **Phase:** Definition & Simplification
> **Objective:** To define the target user profiles that will guide the project's architectural and usability decisions.

This document formalizes the four key user personas for the Grammatomy suite. Each architectural decision must be justified by its service to one or more of these personas.

---

## Persona 1: The Domain Expert (Non-Technical)

This persona represents professors, linguists, and enthusiasts with deep knowledge in grammar but minimal or even hostile attitudes towards technology.

- **Profile:**
  - **Technical Skill:** Low. Uses computers as appliances (e.g., Word with default settings).
  - **Psychology:** Wary of complexity, configuration, and error messages. Values simplicity and directness above all. Has a very high, implicit standard for usability.
  - **Environment:** Primarily Windows or macOS.

- **Core Need: "It Just Works"**
  - They require a zero-configuration, one-click installation process. Download an installer, run it, and find the application in their menu.

- **Architectural Implications:**
  - **Product:** `Grammatomy Studio` (the final desktop application).
  - **Delivery:** Must be a **"Frozen Binary"** (`.exe`, `.app`, `AppImage`). This validates our `Zero-Config Philosophy`.
  - **UI/UX:** The interface must be extremely intuitive, with minimal menus and no technical jargon.

---

## Persona 2: The Researcher

This persona represents academic or professional linguists who are not programmers but are proficient with a specific set of digital tools for their research (spreadsheets, statistical software, databases).

- **Profile:**
  - **Technical Skill:** Medium. Understands data formats and workflows.
  - **Knowledge:** Conceptually aware of NLP/AI technologies (LLMs, Transformers).
  - **Environment:** Works within an established ecosystem of research software.

- **Core Need: Interoperability**
  - They need to move data seamlessly between Grammatomy and their existing tools. The product must behave like a "Lego piece" that fits into their workflow.

- **Architectural Implications:**
  - **Product:** The `RESTful API` is their primary interface.
  - **Delivery:** The API must serve data in **standard, universal formats** (JSON, Penn Treebank strings, etc.). This validates our `Interoperability Agnóstica` principle.
  - **Future:** This persona justifies the future development of plugins for common research tools.

---

## Persona 3: The Application Integrator

This persona is a high-level developer building end-user applications (e.g., language learning platforms, chatbots) that require syntactic analysis capabilities.

- **Profile:**
  - **Technical Skill:** High (Web/Application Development).
  - **Goal:** To embed a functional, interactive syntax tree editor into their own product with minimal effort.

- **Core Need: High-Level, Embeddable Components**
  - They want to import a "black box" component that includes form, content, and functionality, and have it work immediately within their application's layout.

- **Architectural Implications:**
  - **Product:** A library of UI components.
  - **Delivery:** An **NPM package** containing reusable **Web Components**. This validates our decision to use `Lit` and the `Standard-Based & Style-Flexible UI` principle.
  - **Example:** `npm install @grammatomy/tree-editor` and then using `<g-tree-editor>` in their HTML.

---

## Persona 4: The System Developer

This persona is a low-level developer who needs specific, fine-grained pieces of our technology to build other NLP tools (e.g., a G2P converter, a metrics engine). This persona is essentially "us" developing other parts of the suite.

- **Profile:**
  - **Technical Skill:** Very High (Python/Library Development).
  - **Goal:** To access the core parsing logic, data structures, or rendering functions without the overhead of the full application stack.

- **Core Need: Fine-Grained, Modular Libraries**
  - They want to pick and choose the exact pieces they need.

- **Architectural Implications:**
  - **Product:** The core Python library.
  - **Delivery:** A **pip-installable Python package** (`grammatomy-lib`). This validates our `Core-First Layering` principle.
