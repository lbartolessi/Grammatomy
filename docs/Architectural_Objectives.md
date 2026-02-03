# Objetivos Arquitectónicos y Estrategia de Simplificación

> **Fase:** Definición y Simplificación
> **Objetivo:** Establecer los pilares para un producto instalable, interoperable y modular.

## 1. Objetivos de Alto Nivel

1. **Facilidad de Operación:** El producto debe poder instalarse y operarse con facilidad en cualquier entorno (Windows, Linux) por usuarios sin conocimientos técnicos.
2. **Interoperabilidad:** Debe ser interoperable con otros productos de la suite y con elementos externos no previstos.
3. **Modularidad Estratificada:** Debe poder compartirse a varios niveles (librería, componentes gráficos, aplicación final) sin forzar la instalación del conjunto completo.
4. **No Duplicación (DRY):** Evitar la duplicación de procesos. Los cambios en el núcleo o la UI deben realizarse en un solo sitio.
5. **Automatización:** La pluralidad de opciones de distribución debe ser fácilmente automatizable.

## 2. Pilares Técnicos

### A. Accesibilidad Universal (Zero-Config Runtime)

- **Concepto:** Empaquetado "Frozen Binary" que incluye el intérprete de Python y dependencias críticas.
- **Requisito:** El usuario final no interactúa con `pip`, `venv` o la consola. La aplicación es autocontenida.

### B. Interoperabilidad Agnóstica

- **Concepto:** Adopción estricta de Estándares de Intercambio de Datos (JSON Schema, YAML, S-Expressions) como contrato público.
- **Requisito:** La lógica de negocio no depende de estructuras de memoria internas de Python, sino de formatos serializables universales.

### C. Arquitectura Estratificada (Layered Modularity)

- **Diseño "Core-First":**
  - **Nivel 0:** `grammatomy-lib` (Lógica pura, dependencia de Python).
  - **Nivel 1:** `grammatomy-cli` / `api` (Interfaces de texto/red).
  - **Nivel 2:** `grammatomy-studio` (GUI, componentes Qt/Web).
- **Implicación:** Los niveles superiores importan a los inferiores. Un usuario de la librería no descarga Qt; un usuario del Studio descarga todo empaquetado.

### D. Single Source of Truth (SSOT) Estructural

- **Concepto:** La lógica de validación, renderizado y parsing reside exclusivamente en el _Core_.
- **Requisito:** GUI y API son consumidores. Si mejora el parser en el Core, el Studio y la API se actualizan automáticamente al recompilar.

### E. Orquestación de Build (CI/CD Matrix)

- **Concepto:** Pipeline de construcción parametrizado.
- **Requisito:** Un mismo repositorio genera wheel, Docker y ejecutables (.exe/AppImage) mediante scripts automatizados.

## 3. Matices Críticos

### Gestión de Activos Pesados (Model Sovereignty vs. Ease of Use)

- **Desafío:** Modelos neuronales (Stanza, Benepar) de gran tamaño.
- **Solución:** **Gestor de Recursos Integrado**. El sistema detecta faltantes al inicio, descarga y configura sin intervención del usuario.

### Estabilidad de la API Pública (Versioning)

- **Desafío:** Sincronización entre librería, API y Studio.
- **Solución:** **Versionado Semántico Estricto (SemVer)**. Interfaces públicas como contratos inmutables entre versiones menores.
