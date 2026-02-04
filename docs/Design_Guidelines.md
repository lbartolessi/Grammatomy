# 📘 Linguistic Suite: Design System & Style Guide

This document defines the visual and functional standards for the linguistic application suite. The system is inspired by **Bauhaus functionalism**, prioritizing clarity, accessibility, and scientific rigor.

---

## 1. Core Philosophy

- **Accessibility First:** Guaranteed legibility for users with color vision deficiencies (CVD).
- **Typography as Structure:** Meaning is conveyed through weight, scale, and hierarchy rather than decorative elements.
- **Minimalist Aesthetic:** Use of 1px lines, generous white space (breathing room), and a "paper-like" interface.

---

## 2. Color Palette & Accessibility

We employ two specific palettes to ensure universal accessibility. Check contrast ratios at [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/).

### 2.1 Base Tones (Ergonomics)

- **Level 1 (Primary):**
  - **Light:** `#F4F4F4` (Bone White). This is the **maximum brightness** allowed. Pure white (`#FFFFFF`) is forbidden to prevent eye strain.
  - **Dark:** `#161616` (Carbon Black). Deep neutral background.
- **Level 2 (Secondary/Structural):**
  - **Light:** `#E6E6E6`. Slightly darker for borders and secondary backgrounds.
  - **Dark:** `#1C1E26`. Slightly lighter with a **cool blue tint** to distinguish surface layers.
- **Usage Note:** These neutrals are distinct within both functional palettes and may be used as additional data colors if the primary palette is exhausted.

### 2.2 Functional Palettes

| **CRITICAL RULE:** Do not mix palettes. Distinction is guaranteed only within a single palette. |
| Purpose | Source | Colors |
| --- | --- | --- |
| **UI & Interaction** | IBM Design Language | Blue `#648FFF`, Purple `#785EF0`, Pink `#DC267F`, Orange `#FE6100`, Yellow `#FFB000` |
| **Data & Charts** | Bang Wong Palette | Orange `#E69F00`, Sky `#56B4E9`, Green `#009E73`, Blue `#0072B2`, Vermilion `#D55E00` |

---

## 3. Typography Strategy

We use a "Triad of Precision" to distinguish between interface, data, and phonetics.

### 3.1 Font Families

1. **[Roboto](https://fonts.google.com/specimen/Roboto):** Main UI font.

- _Weights:_ 300 (Light) for body text, 900 (Black) for headers.
- **Deployment:** Served locally from `/public/fonts/` (No Google Fonts CDN).

2. **[Charis SIL](https://software.sil.org/charis/):** Specialized for **IPA (Phonetic)** transcriptions.

- _Role:_ Ensures diacritics and rare phonetic glyphs are rendered with academic accuracy.

3. **[Roboto Mono](https://fonts.google.com/specimen/Roboto+Mono):** For technical data and audio-to-text alignment.

---

## 4. Iconography

We use **[Material Symbols (Outlined)](https://fonts.google.com/icons?icon.set=Material+Symbols)** for their neutral, non-distracting style.

- **Configuration:** \* Weight: `200` (Thin lines to match the Bauhaus aesthetic).
- Optical Size: `24px`.

- **Integration:** Served locally as a variable font (`MaterialSymbolsOutlined.ttf`).
- **Usage:** `<span class="material-symbols-outlined">search</span>`

---

## 5. Implementation & Theme Strategy

### 5.1 Dark Mode Policy

- **Priority:** Light Mode is the default. Dark Mode can cause halation for users with astigmatism and is generally more fatiguing for this user base.
- **Control:** A toggle switch (slider or icon) must always be available in the top title bar.

### 5.2 Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  darkMode: "class", // Manual toggle for Day/Night mode
  theme: {
    extend: {
      colors: {
        // Base Neutrals (High Contrast in both palettes)
        base: {
          dark: "#161616", // Level 1
          "dark-dim": "#1C1E26", // Level 2 (Blue tint)
          light: "#F4F4F4", // Level 1 (Max Brightness)
          "light-dim": "#E6E6E6", // Level 2
        },
        // IBM Palette (UI Elements Only)
        ibm: {
          blue: "#648FFF",
          purple: "#785EF0",
          pink: "#DC267F",
          orange: "#FE6100",
          yellow: "#FFB000",
        },
        // Bang Wong Palette (Data Visualization Only)
        wong: {
          orange: "#E69F00",
          sky: "#56B4E9",
          green: "#009E73",
          blue: "#0072B2",
          vermilion: "#D55E00",
        },
      },
      fontFamily: {
        sans: ["Roboto", "sans-serif"],
        serif: ["Charis SIL", "serif"],
        mono: ["Roboto Mono", "monospace"],
      },
    },
  },
};
```

---

## 6. Layout Components

### 6.1 Linguistic Interlinear Glossing

- **Structure:** Vertical stacks of Category (labels) and Tokens (text).
- **Rule:** Labels in `font-black text-[10px] text-ibm-blue`. Tokens in `font-light`.

### 6.2 Data Comparison Tables

- **Style:** No background fills. 1px borders (`border-base-dark/10`).
- **Highlight:** Use `bg-wong-orange/20` for phonetic divergences.

---

## 7. Useful Resources

- **CVD Simulator:** Use Chrome DevTools (`Ctrl+Shift+P` -> "Emulate vision deficiency").
- **Font Helper:** [Google Webfonts Helper](https://www.google.com/search?q=https://google-webfonts-helper.herokuapp.com/) (For WOFF2 local downloads).
- **IPA Standards:** [International Phonetic Association](https://www.internationalphoneticassociation.org/content/ipa-chart).
