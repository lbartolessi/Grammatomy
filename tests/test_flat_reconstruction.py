import unittest

from anytree import Node, RenderTree

from core.grammatomy import get_syntax_tree
from core.grammatomy.edge_reconstructor import EdgeBasedReconstructor
from core.grammatomy.essential_validator import EssentialStructureValidator

# Frases de anidamiento central creciente (sin puntuación)
SENTENCES = [
    "El informe que el comité evaluó fue aprobado",
]

# Lista negra de nodos estructurales que deben ser eliminados para el aplanamiento
PHRASAL_NODES = {
    "ROOT",
    "S",
    "sentence",  # Stanza wrapper
    "NP",
    "VP",
    "PP",
    "ADVP",
    "ADJP",
    "sn",
    "grup.nom",
    "grup.verb",
    "sp",
    "spec",
    "grup.a",
    "grup.adv",
    "s.a",
    "s.adv",
    "SBAR",
    "relatiu",
    "coord",
    "conj",
    "neg",
    "morfema.pronominal",
    "morfema.verbal",
    "ao",  # Aposición
}


class TestFlatReconstruction(unittest.TestCase):
    def setUp(self):
        self.reconstructor = EdgeBasedReconstructor()
        self.validator = EssentialStructureValidator()
        self.params = {
            "engine": "stanza",
            "lang": "es",
            "model_package": "default",
            "use_gpu": False,
        }

    def flatten_tree(self, root: Node) -> Node:
        """
        Aplana completamente el árbol.
        Crea un nuevo ROOT y le asigna como hijos directos todos los nodos POS (pre-terminales) del árbol original.
        """
        print("\n  [Flattening Debug]")
        flat_children = []
        # Normalizamos el nombre para la comprobación
        # (strip y lower por si acaso, aunque mantenemos casing original)

        def collect_leaves(n):
            name_clean = n.name.strip()

            # Si es un nodo estructural conocido, profundizamos
            if name_clean in PHRASAL_NODES:
                for child in n.children:
                    collect_leaves(child)
            else:
                # Es un nodo de contenido (POS o palabra)
                # print(f"    + Collecting leaf/POS: {name_clean}")
                flat_children.append(n)

        collect_leaves(root)

        # Crear nuevo ROOT
        new_root = Node("ROOT")
        for child in flat_children:
            # Re-parenting (AnyTree mueve el nodo, lo desconecta del padre anterior)
            child.parent = new_root

        return new_root

    def test_reconstruct_from_flat(self):
        print("\n" + "=" * 80)
        print("PRUEBA: RECONSTRUCCIÓN DESDE APLANAMIENTO TOTAL")
        print("=" * 80)

        for i, text in enumerate(SENTENCES, 1):
            self._process_sentence(i, text)

    def _process_sentence(self, index: int, text: str):
        print(f'\nFrase {index}: "{text}"')

        # 1. Obtener árbol original
        original_root = get_syntax_tree(text, self.params)
        if not original_root:
            print("  ❌ Fallo al parsear.")
            return

        print("  Árbol Original (Stanza):")
        for pre, _, node in RenderTree(original_root):
            print(f"    {pre}{node.name}")

        # 2. Aplanar
        flat_root = self.flatten_tree(original_root)
        print("  Árbol Aplanado (ROOT -> POS):")
        for pre, _, node in RenderTree(flat_root):
            if node.depth <= 1:  # Solo mostrar hijos directos de ROOT
                print(f"    {pre}{node.name}")

        # Verificar que no se nos ha colado un nodo 'sentence' o 'S'
        direct_children_names = [c.name for c in flat_root.children]
        if "sentence" in direct_children_names or "S" in direct_children_names:
            print("  ❌ ERROR CRÍTICO: El aplanamiento falló. 'sentence' o 'S' sigue presente.")
            return

        # 3. Reconstruir
        print("  ... Reconstruyendo ...")

        # Note: EdgeBasedReconstructor uses 'refine', not 'reconstruct'
        reconstructed_root, _ = self.reconstructor.refine(flat_root)

        # 4. Visualizar resultado
        print("\n  Árbol Reconstruido Final:")
        for pre, _, node in RenderTree(reconstructed_root):
            print(f"    {pre}{node.name}")

        self._validate_reconstruction(reconstructed_root)

    def _validate_reconstruction(self, reconstructed_root: Node):
        # 5. Validar estructura básica
        # Esperamos que ROOT tenga un hijo S
        # Nota: El reconstructor crea nodos con nombres canónicos (sentence, sn, grup.verb)
        # definidos en las reglas.
        s_nodes = [c for c in reconstructed_root.children if c.name == "sentence"]

        if s_nodes:
            print("  ✅ ROOT contiene sentence.")
            s_node = s_nodes[0]
            # Esperamos que sentence tenga un hijo grup.verb
            vp_nodes = [c for c in s_node.children if c.name == "grup.verb"]
            if vp_nodes:
                print("  ✅ sentence contiene grup.verb.")
            else:
                print(
                    f"  ⚠️ sentence NO contiene grup.verb. Hijos: {[c.name for c in s_node.children]}"  # pylint: disable=line-too-long # noqa: E501
                )

            # Esperamos que sentence tenga un hijo sn (sujeto)
            np_nodes = [c for c in s_node.children if c.name == "sn"]
            if np_nodes:
                print("  ✅ sentence contiene sn (Sujeto).")
        else:
            print(
                f"  ❌ ROOT NO contiene sentence. Hijos de ROOT: {[c.name for c in reconstructed_root.children]}"
            )


if __name__ == "__main__":
    unittest.main()
