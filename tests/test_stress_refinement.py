import unittest
from copy import deepcopy

from anytree import PreOrderIter, RenderTree

from src.core.grammatomy import get_syntax_tree
from src.core.grammatomy.edge_reconstructor import EdgeBasedReconstructor
from src.core.grammatomy.validation_engine import ValidationEngine


# ANSI color codes for console output.
class Colors:
    """Terminal color codes for better visualization."""

    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"


# Banco de pruebas de estrés, extraído de la consulta a Gemini.
STRESS_SENTENCES = {
    "Anidamiento Profundo": [
        "La idea de que el hombre que conociste sea el director es increíble.",
        # "Dijo que pensaba que creía que no vendrías a la fiesta.",  # pylint: disable=line-too-long
        "El informe que mencionaste que debíamos revisar antes de que llegara el comité resultó incompleto.",  # pylint: disable=line-too-long
        # "La persona que dijo que conocía al autor que ganó el premio no apareció en la conferencia.",  # pylint: disable=line-too-long
        "El coche que el mecánico que trabaja al lado reparó se vendió por un precio alto.",  # pylint: disable=line-too-long
        "El informe que la directora que renunció la semana pasada escribió fue publicado en el periódico.",  # pylint: disable=line-too-long
    ],
    # "Ambigüedad de Adjunción (SP)": [
    #     "Vieron al sospechoso con el telescopio desde la colina.",
    #     "Depositó el dinero en el banco que estaba en la esquina.",
    #     "El hombre observó al perro con el telescopio.",
    #     "La investigadora analizó los datos del experimento con cautela.",
    #     "El niño encontró el libro de su hermana en el jardín.",
    #     "La niña observó al pájaro con un telescopio.",
    #     "Los biólogos estudiaron la muestra con un microscopio.",
    #     "Visitaron la catedral con un guía.",
    # ],
    "Estructuras con 'se'": [
        "Se venden apartamentos de lujo en la costa.",
        "Se avisó a los delegados de la cancelación del evento.",
        "Se necesitan voluntarios para el proyecto.",
        "Se necesita a voluntarios para el proyecto.",
        # Agramatical, pero útil para pruebas de robustez.
        "Se vende a casas con vistas al mar.",
        "Se contratan empleados con experiencia.",
        "Se busca a voluntarios para el evento.",
    ],
    # "Orden No Canónico (Garden Path)": [
    #     "Al presidente lo criticaron duramente sus propios ministros.",
    #     "Ayer me entregó el paquete que faltaba el mensajero de la empresa.",
    #     "A Laura la felicitó su jefe durante la ceremonia.",
    #     "Mientras los estudiantes estudiaban el examen fue retirado de la mesa.",
    #     "A Pedro lo vio su amiga desde la ventana del tren.",
    #     "A María la llamó su hermano por la tarde.",
    #     "A los invitados los saludó el alcalde con una sonrisa.",
    #     "Después del diluvio apareció un arcoíris sobre el horizonte.",
    # ],
    "Coordinación con Elipsis (Gapping)": [
        "El Gobierno aprobó la ley de educación y la oposición, la de sanidad.",
        "Unos prefieren viajar en tren y otros, en avión por la mañana.",
        "María preparó café y su hermano, té verde.",
        "El director aprobó el presupuesto y la junta, las modificaciones.",
        "Compraron libros antiguos y sus amigos, revistas.",
        "Marta pidió vino tinto y su amigo, cerveza.",
        # "Elena preparó paella y su esposo, fideuá.",
        "Juan compró helados para todos y María, bebidas para acompañar.",
    ],
    "Ambigüedad de Adjunción (RC)": [
        # "Entrevistaron la hija de la embajadora que fue premiada en París.",
        "Leí el capítulo del libro que publicaron ayer por la tarde.",
        "Vi al hijo del profesor que llegó tarde a la reunión.",
        "Entregaron el informe del departamento que había sido auditado el mes pasado.",
        "Conocí a la hermana del médico que trabaja en el hospital central.",
        "Encontré a la amiga del profesor que llegó tarde.",
        "Compramos la casa del primo que tiene el jardín más grande.",
        # "Vi al profesor de la universidad que ganó el premio Nobel.",
    ],
}


class TestStressRefinement(unittest.TestCase):
    """
    Prueba el algoritmo de refinamiento contra un banco de frases complejas
    diseñadas para causar aplanamiento y errores estructurales en parsers neuronales.
    """

    def setUp(self):
        # Clear the singleton cache to ensure rules are reloaded for each test run,
        # which is crucial when iteratively modifying the YAML file.
        ValidationEngine._instances = {}  # pylint: disable=protected-access
        self.reconstructor = EdgeBasedReconstructor()
        self.params = {
            "engine": "stanza",
            "lang": "es",
            "model_package": "default",
            "use_gpu": False,
        }

    def print_tree(self, node, title, modified_nodes=None):
        print(f"\n--- {title} ---")
        if not node:
            print("    Árbol Nulo")
            return
        if modified_nodes is None:
            modified_nodes = set()

        for pre, _, n in RenderTree(node):
            if n in modified_nodes:
                print(f"    {pre}{Colors.YELLOW}{n.name}{Colors.ENDC}")
            elif n.is_leaf:
                print(f"    {pre}{Colors.CYAN}{n.name}{Colors.ENDC}")
            else:
                print(f"    {pre}{n.name}")

    def validate_tree_strict(self, root):
        """Verifica si el árbol completo cumple las reglas estrictas."""
        for node in PreOrderIter(root):
            if not node.children:
                continue
            children_tags = [child.name for child in node.children]
            is_valid, errors, _ = self.reconstructor.engine.validate_node(
                node.name, children_tags, strategy="strict"
            )
            if not is_valid:
                # DEBUG: Print loaded patterns for this node to diagnose mismatch
                patterns = self.reconstructor.engine.patterns.get(node.name, [])
                error_msg = (
                    f"Nodo '{node.name}' falló validación: {children_tags}. Errors: {errors}"
                )
                print(f"\n[DEBUG] Validation Failed for '{node.name}'")
                print(f"  - Children found: {children_tags}")
                print(f"  - Patterns loaded: {patterns}")
                return False, error_msg

        return True, "OK"

    def test_stress_cases(self):
        """
        Itera sobre el banco de pruebas, parsea, refina y muestra los resultados
        para una evaluación visual.
        """
        results = {
            "untouched": 0,
            "refined": 0,
            "failed": 0,
            "valid_final": 0,
            "invalid_final": 0,
        }

        for category, sentences in STRESS_SENTENCES.items():
            print("\n" + "=" * 80)
            print(f"CATEGORÍA DE ESTRÉS: {category}")
            print("=" * 80)
            for i, text in enumerate(sentences, 1):
                self._process_sentence(i, text, results)

        # 5. Imprimir tabla de resumen
        print("\n" + "=" * 80)
        print("RESUMEN DE LA EJECUCIÓN DEL REFINADOR")
        print("-" * 80)
        print(f"  Árboles sin modificar (Untouched):      {results['untouched']}")
        print(f"  Árboles refinados (Refined):            {results['refined']}")
        print(f"  Fallos de parseo inicial:               {results['failed']}")
        print("-" * 80)
        print(f"  TOTAL VÁLIDOS (Strict Mode):            {results['valid_final']}")
        print(f"  TOTAL INVÁLIDOS:                        {results['invalid_final']}")
        print("=" * 80)

        # Assert final success for regression testing
        self.assertEqual(
            results["invalid_final"],
            0,  # pylint: disable=line-too-long
            f"Regression: Found {results['invalid_final']} invalid trees.",  # pylint: disable=line-too-long
        )

    def _process_sentence(self, index: int, text: str, results: dict):
        print(f"\n--- FRASE {index}: '{text}' ---")

        # 1. Parseo original
        original_root = get_syntax_tree(text, self.params)
        self.print_tree(original_root, "Árbol Original (Stanza)")

        if not original_root:
            self.fail(f"El parser falló para la frase: {text}")
            results["failed"] += 1
            return

        # 2. Refinamiento
        # Hacemos una copia para no modificar el original
        tree_to_refine = deepcopy(original_root)
        total_created_nodes = set()
        passes_made = 0
        refined_root = tree_to_refine  # Initialize to avoid unbound variable

        # Iterative Refinement (up to 3 passes to catch cascading changes)
        for _ in range(1, 4):
            refined_root, pass_created = self.reconstructor.refine(tree_to_refine)
            if not pass_created:
                break
            passes_made += 1
            total_created_nodes.update(pass_created)
            # If changes occurred, we loop again to see if new structures enable further refinement
            tree_to_refine = refined_root

        print(f"  (Refinamiento completado en {passes_made} pasada(s) efectivas)")
        self.print_tree(refined_root, "Árbol Refinado", modified_nodes=total_created_nodes)

        # 3.5 Validación Estricta Final
        is_valid, reason = self.validate_tree_strict(refined_root)
        validity_icon = "✅" if is_valid else "❌"
        print(f"  Validación Estricta: {validity_icon} ({reason})")

        if is_valid:
            results["valid_final"] += 1
        else:
            results["invalid_final"] += 1

        # 3. Verificación básica
        self.assertIsNotNone(refined_root, "El refinamiento devolvió un árbol nulo.")
        self.assertEqual(original_root.name, refined_root.name, "El nodo raíz fue alterado.")

        # 4. Actualizar estadísticas
        if total_created_nodes:
            results["refined"] += 1
        else:
            results["untouched"] += 1


if __name__ == "__main__":
    unittest.main()
