import unittest
from typing import List

from anytree import RenderTree

from core.grammatomy import get_syntax_tree
from core.grammatomy.essential_validator import EssentialStructureValidator

# Frases de anidamiento central creciente (sin puntuación)
SENTENCES = [
    "El informe fue aprobado",
    "El informe que el comité evaluó fue aprobado",
    "El informe que el comité que el ministerio creó evaluó fue aprobado",
    "El informe que el comité que el ministerio que asumió la reforma creó evaluó fue aprobado",  # pylint: disable=line-too-long
    "El informe que el comité que el ministerio que el gobierno que llegó al poder asumió creó evaluó fue aprobado",  # pylint: disable=line-too-long
    "El informe que el comité que el ministerio que el gobierno que los votantes eligieron asumió creó evaluó fue aprobado",  # pylint: disable=line-too-long
    "El informe que el comité que el ministerio que el gobierno que los votantes que participaron en las elecciones eligieron asumió creó evaluó fue aprobado",  # pylint: disable=line-too-long
]


class TestDeepRecursionStress(unittest.TestCase):
    def setUp(self):
        self.validator = EssentialStructureValidator()
        # Usamos Stanza con el modelo 'default' (o 'combined') que suele ser robusto
        self.params = {
            "engine": "stanza",
            "lang": "es",
            "model_package": "default",
            "use_gpu": False,
        }

    def extract_tags(self, node) -> List[str]:
        """Extrae las etiquetas de los hijos inmediatos."""
        return [child.name for child in node.children]

    def test_recursion_levels(self):
        print("\n" + "=" * 80)
        print("PRUEBA DE ESTRÉS: RECURSIVIDAD PROFUNDA (SIN PUNTUACIÓN)")
        print("Objetivo: Verificar si el modelo mantiene la jerarquía o colapsa.")
        print("=" * 80)

        for i, text in enumerate(SENTENCES, 1):
            print(f'\nNivel {i}: "{text}"')

            try:
                self._process_sentence(text)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"❌ Error de ejecución en Nivel {i}: {e}")

    def _process_sentence(self, text):
        # 1. Parsing Real
        root = get_syntax_tree(text, self.params)

        if not root:
            print("❌ FALLO: El parser no devolvió ningún árbol.")
            return

        # Ajuste para Stanza que devuelve ROOT -> S
        s_node = root.children[0] if root.children and root.name == "ROOT" else root

        # 2. Validación Esencial
        children_tags = self.extract_tags(s_node)
        is_valid, missing = self.validator.validate_node("S", children_tags)

        status_icon = "✅" if is_valid else "❌"
        missing_info = f" [Missing: {missing}]" if missing else ""
        print(
            f"  Validación Esencial (S): {status_icon} (Hijos: {children_tags}){missing_info}"  # pylint: disable=line-too-long
        )

        # 2.1 Validación Recursiva de Hijos (Deep Scan)
        self._validate_children(s_node)

        # 3. Diagnóstico de Estructura
        self._diagnose_structure(children_tags)

        # 4. Visualización Compacta (Solo hasta profundidad 4 para no saturar)
        print("  Traza del Árbol (Top 4 niveles):")
        for pre, _, node in RenderTree(root):
            if node.depth > 4:
                continue
            # Mostrar solo el nombre del nodo para brevedad
            print(f"    {pre}{node.name}")

    def _validate_children(self, s_node):
        # Verificamos si los hijos directos (sn, grup.verb, etc.) están aplanados internamente
        for child in s_node.children:
            # Solo validamos nodos que sean grupos sintácticos conocidos
            if child.name in [
                "sn",
                "grup.verb",
                "sp",
                "grup.nom",
                "grup.a",
                "grup.adv",
                "spec",
            ]:
                grandchild_tags = self.extract_tags(child)
                c_valid, c_missing = self.validator.validate_node(child.name, grandchild_tags)

                if c_missing:  # Solo reportamos si hay algo interesante (missing o error)
                    c_status = "✅" if c_valid else "❌"
                    print(
                        f"    ↳ Sub-nodo '{child.name}': {c_status} [Missing: {c_missing}] "
                        f"-> Hijos: {grandchild_tags}"
                    )
                elif not c_valid:
                    print(f"    ↳ Sub-nodo '{child.name}': ❌ INVALIDO -> Hijos: {grandchild_tags}")

    def _diagnose_structure(self, children_tags):
        # Buscamos si existen constituyentes complejos (NP, VP)
        # o si hay aplanamiento (muchos tokens planos)
        # Actualizado para incluir etiquetas AnCora en la lista blanca
        phrasal_tags = [
            "NP",
            "VP",
            "S",
            "PP",
            "sn",
            "grup.verb",
            "grup.nom",
            "sp",
            "grup.a",
        ]
        has_phrasal = any(tag in phrasal_tags for tag in children_tags)
        flat_tokens = sum(1 for tag in children_tags if tag not in phrasal_tags)

        if has_phrasal and flat_tokens < 3:
            struct_diag = "Jerárquica (Correcta)"
        elif has_phrasal:
            struct_diag = "Híbrida (Parcialmente Aplanada)"
        else:
            struct_diag = "PLANA (Colapso Total)"

        print(f"  Diagnóstico Estructural: {struct_diag}")


if __name__ == "__main__":
    unittest.main()
