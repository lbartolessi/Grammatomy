# Frontend Architecture and UI Technology Stack

> **Phase:** Definition & Simplification
> **Decision:** Adopt Lit for Web Components rendering in the Light DOM.

## 1. Core Decision

The user interface for Grammatomy will be a **custom web application** built with **TypeScript** and the **Lit** library. All components will be configured to render in the **Light DOM**, explicitly disabling the Shadow DOM to ensure global styling capabilities.

## 2. Rationale and Alternatives Considered

### A. Rejection of "Magic" Frameworks (Streamlit, Gradio)

While excellent for rapid prototyping, frameworks like Streamlit and Gradio impose a rigid execution model (e.g., full-page reloads) that severely limits the creation of a complex, professional-grade user experience. Our objective requires full control over the application's state and rendering lifecycle, which these tools do not provide.

### B. Rejection of Heavy Frameworks (React, Angular, Vue)

Large, monolithic frameworks introduce significant overhead and a steep learning curve. They often require a "virtual DOM" and a large runtime library to be shipped to the client, which contradicts our goal of a lightweight, standard-based, and simple architecture.

### C. Lit vs. Svelte

Both Lit and Svelte align with our philosophy of compiling to highly optimized, vanilla JavaScript.

- **Svelte:** A compiler that excels at building entire applications with minimal boilerplate. Its reactivity is implicit ("magic").
- **Lit:** A lightweight library for creating standard **Web Components**.

**Decision:** We chose **Lit** due to its unparalleled **interoperability**. A component built with Lit is a standard, reusable artifact that can be used in any future project or web context, perfectly aligning with our goal of a modular and extensible suite of tools. Since our application is a simple RESTful client, the advanced reactivity offered by Svelte is not required.

## 3. The Shadow DOM Dilemma and Solution

A critical point was raised regarding the **Shadow DOM**, the technology Web Components use for style encapsulation.

- **The Problem:** The Shadow DOM prevents global CSS frameworks (like Bootstrap, Tailwind, etc.) from styling the internal elements of a component. This would force us to write custom styles for every component, defeating the purpose of using a flexible CSS framework.

- **The Solution:** Lit allows us to disable the Shadow DOM on a per-component basis by overriding the `createRenderRoot` method. This causes the component's template to be rendered directly into the main document ("Light DOM").

```typescript
import { LitElement, html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("open-component")
export class OpenComponent extends LitElement {
  // This is the key: render in the Light DOM.
  protected createRenderRoot() {
    return this;
  }

  render() {
    // This button will now be styled by global CSS frameworks.
    return html`<button class="btn btn-primary">Styled Button</button>`;
  }
}
```

This approach gives us the best of both worlds: the **modularity** of Web Components and the **design flexibility** of global CSS. The trade-off is a loss of style encapsulation, a risk we can easily mitigate with careful CSS class naming conventions (e.g., BEM).
