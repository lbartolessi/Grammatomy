import unittest

from anytree import PreOrderIter, RenderTree

from src.core.grammatomy import get_syntax_tree
from src.core.grammatomy.edge_reconstructor import EdgeBasedReconstructor
from src.core.grammatomy.validation_engine import ValidationEngine


# ANSI color codes for console output
class Colors:
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"


# Banco de pruebas de validación ciega (Generado por DeepSeek)
DEEPSEEK_TEST_SENTENCES = {
    "Categoría 1: Ambigüedad de Adjunción de Cláusula Relativa": [
        "La propuesta de la delegación que generó más polémica fue retirada.",
        "Criticaron el discurso del presidente que se volvió viral en las redes.",
        "Finalmente localizaron al hermano de la testigo que llevaba una gabardina azul.",
    ],
    "Categoría 2: Construcciones Ambiguas con 'se'": [
        "Se contratarán desarrolladores antes del lanzamiento.",
        "En esta empresa se valora a los desarrolladores por sus ideas.",
        "Se premió a los ganadores con una standing ovation.",
    ],
    "Categoría 3: Orden de Palabras No Canónico (Garden Path)": [
        "Al director general lo despidió sorpresivamente la junta accionista.",
        "Mientras revisaba los datos el servidor se colapsó por completo.",
        "Con tanto esfuerzo la meta finalmente fue alcanzada por el equipo.",
    ],
    "Categoría 4: Coordinación con Elipsis (Gapping)": [
        "La streamer comenzó su directo a las ocho, y sus seguidores, a las diez.",
        "Nuestra arquitecta propuso un diseño vanguardista, y la cliente, uno más conservador.",
        "El primer equipo anotó dos goles en el primer tiempo, y el rival, tres.",
    ],
    "Categoría 5: Anidamiento Profundo de Subordinadas": [
        "El informe que sugeriste que encargáramos al consultor externo que recomendaste ha llegado.",
        (
            "Me pregunto si la persona a quien le confiaste la copia de la llave "
            "que guardábamos en la oficina será de fiar."
        ),
        (
            "La teoría de que el hecho de que los datos fueran públicos "
            "influyó en la decisión es controvertida."
        ),
    ],
    "Categoría 6: Ambigüedad de Adjunción de Sintagmas Preposicionales": [
        "El técnico revisó el servidor con los nuevos parches de seguridad.",
        "Encontramos al explorador cerca del río con un equipo de geolocalización avanzado.",
        "La periodista entrevistó al ministro con una actitud desafiante.",
    ],
}

# Banco de pruebas de validación ciega (Generado por Claude)
CLAUDE_TEST_SENTENCES = {
    "Categoría 1: Ambigüedad de Adjunción de Cláusula Relativa": [
        "Encontré la carta del abogado que mencionaba el testamento perdido.",
        "Revisé el informe del consultor que criticaba las nuevas políticas.",
        "Conocí al sobrino del escritor que publicó tres novelas este año.",
        "Observé la fotografía del artista que ganó el concurso internacional.",
    ],
    "Categoría 2: Construcciones Ambiguas con 'se'": [
        "Se necesitan traductores con dominio del mandarín.",
        "Se necesita a traductores con dominio del mandarín.",
        "Se contrata diseñadores gráficos para proyectos urgentes.",
        "Se entrevista a candidatos todos los viernes por la mañana.",
        "Se evalúan propuestas hasta el próximo mes.",
    ],
    "Categoría 3: Orden de Palabras No Canónico (Garden Path)": [
        "Al gerente lo convenció el cliente con argumentos sólidos.",
        "A los estudiantes los sorprendió la profesora con un examen inesperado.",
        "Mientras el técnico reparaba la máquina se descompuso completamente.",
        "Cuando los periodistas investigaban el escándalo estalló públicamente.",
        "Al amanecer los pescadores regresaron con las redes vacías.",
    ],
    "Categoría 4: Coordinación con Elipsis (Gapping)": [
        "El arquitecto diseñó la fachada principal y su asistente, los planos internos.",
        "Carolina eligió el vestido azul y su hermana, los zapatos plateados.",
        "El chef preparó la entrada y su ayudante, el postre especial.",
        "Los inversores compraron acciones tecnológicas y los especuladores, bonos del estado.",
    ],
    "Categoría 5: Anidamiento Profundo de Subordinadas": [
        "El proyecto que me asignaron que desarrollara resultó ser el que más recursos consumió.",
        "La película que me dijiste que viera resultó ser la que todos comentaban.",
        "El candidato que propusiste que entrevistáramos resultó ser quien mejor encajaba.",
        "La estrategia que sugeriste que implementáramos demostró ser la que mayor impacto tuvo.",
    ],
    "Categoría 6: Ambigüedad de Adjunción de Sintagmas Preposicionales": [
        "La enfermera examinó al paciente con el estetoscopio nuevo.",
        "El detective siguió al sospechoso con la gabardina gris.",
        "El fotógrafo retrató a la modelo con la cámara profesional.",
        "El veterinario vacunó al perro con la jeringa desechable.",
        "El arqueólogo estudió los restos con el microscopio especializado.",
    ],
}

# Banco de pruebas de validación ciega (Generado por Mistral)
MISTRAL_TEST_SENTENCES = {
    "Categoría 1: Ambigüedad de Adjunción de Cláusula Relativa": [
        "El informe del comité que incluye los datos actualizados fue revisado por la auditora.",
        "La propuesta de la consultora que presenta las recomendaciones clave aún no se ha aprobado.",
        "El análisis del grupo que contiene los resultados preliminares será discutido en la reunión.",
        "El documento del departamento que detalla los procedimientos está en revisión.",
        "La investigación del equipo que aborda los temas clave fue publicada recientemente.",
    ],
    "Categoría 2: Construcciones Ambiguas con 'se'": [
        "Se solicitan especialistas con experiencia en desarrollo de software para el proyecto.",
        "Se contrató a voluntarios con experiencia en logística para el evento.",
        "Se requieren técnicos con certificación en seguridad antes del viernes.",
        "Se necesita a ingenieros con conocimientos en inteligencia artificial para la vacante.",
    ],
    "Categoría 3: Orden de Palabras No Canónico (Garden Path)": [
        "A los inversores los convenció el proyecto innovador durante la presentación.",
        ("Cuando el informe se revisó, desaparecieron los archivos importantes de la carpeta."),
        "A los estudiantes los sorprendió la noticia del cambio de horario.",
        "Durante la reunión, el informe se discutió y se tomaron decisiones importantes.",
    ],
    "Categoría 4: Coordinación con Elipsis (Gapping)": [
        "La chef preparó sopa de mariscos y el comensal, ensalada César.",
        "El arquitecto diseñó la fachada y su equipo, los interiores.",
        "El profesor explicó el tema y los alumnos, las dudas.",
        "La empresa lanzó un nuevo producto y su competencia, una campaña publicitaria.",
    ],
    "Categoría 5: Anidamiento Profundo de Subordinadas": [
        "La película que el crítico dijo que el director había modificado sin avisar resultó ser un fracaso.",
        "El libro que el profesor recomendó que los estudiantes leyeran fue un éxito de ventas.",
        "El proyecto que el gerente anunció que el equipo había completado antes de tiempo fue premiado.",
    ],
    "Categoría 6: Ambigüedad de Adjunción de Sintagmas Preposicionales": [
        "El guardabosques avistó al oso con el telescopio.",
        "La profesora corrigió los exámenes con las respuestas detalladas.",
        "El investigador analizó los datos con el software especializado.",
        "El mecánico reparó el coche con las herramientas nuevas.",
    ],
}


class TestBlindValidation(unittest.TestCase):
    """
    Ejecuta una validación ciega sobre frases nuevas para verificar la generalización
    de las reglas gramaticales y el algoritmo de refinamiento.
    """

    def setUp(self):
        # Limpiar caché para asegurar recarga de reglas
        ValidationEngine._instances = {}  # pylint: disable=protected-access
        self.reconstructor = EdgeBasedReconstructor()  # pylint: disable=protected-access
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
                error_msg = (
                    f"Nodo '{node.name}' falló validación: {children_tags}. Errors: {errors}"
                )
                return False, error_msg
        return True, "OK"

    def test_blind_cases(self):
        results = {
            "untouched": 0,
            "refined": 0,
            "failed": 0,
            "valid_final": 0,
            "invalid_final": 0,
        }

        # Combinar ambos bancos de pruebas para el reporte
        test_suites = [
            ("DEEPSEEK", DEEPSEEK_TEST_SENTENCES),
            ("CLAUDE", CLAUDE_TEST_SENTENCES),
            ("MISTRAL", MISTRAL_TEST_SENTENCES),
        ]

        for source_name, suite in test_suites:
            print(f"\n>>> EJECUTANDO SUITE: {source_name} <<<")
            self._process_suite(suite, results)

        print("\n" + "=" * 80)
        print("RESUMEN BLIND TEST")
        print("-" * 80)
        total_sentences = sum(len(v) for _, s in test_suites for v in s.values())
        print(f"  Total Frases: {total_sentences}")
        print(f"  Válidos:      {results['valid_final']}")
        print(f"  Inválidos:    {results['invalid_final']}")
        print("=" * 80)

        # Assert final success for regression testing
        self.assertEqual(
            results["invalid_final"],
            0,
            f"Regression: Found {results['invalid_final']} invalid trees in Blind Test.",
        )

    def _process_suite(self, suite, results):
        for category, sentences in suite.items():
            print("\n" + "=" * 80)
            print(f"{category}")
            print("=" * 80)
            for i, text in enumerate(sentences, 1):
                self._process_sentence(i, text, results)

    def _process_sentence(self, index: int, text: str, results: dict):
        print(f"\n--- FRASE {index}: '{text}' ---")

        original_root = get_syntax_tree(text, self.params)
        if not original_root:
            print(f"❌ El parser falló para la frase: {text}")
            results["failed"] += 1
            return

        # Refinamiento
        refined_root, created_nodes = self.reconstructor.refine(original_root)

        if created_nodes:
            print(f"  (Refinado: {len(created_nodes)} nodos creados)")
            self.print_tree(refined_root, "Árbol Refinado", modified_nodes=created_nodes)
            results["refined"] += 1
        else:
            print("  (Sin cambios estructurales)")
            results["untouched"] += 1

        # Validación
        is_valid, reason = self.validate_tree_strict(refined_root)
        validity_icon = "✅" if is_valid else "❌"
        print(f"  Validación Estricta: {validity_icon} ({reason})")

        if is_valid:
            results["valid_final"] += 1
        else:
            results["invalid_final"] += 1


if __name__ == "__main__":
    unittest.main()
