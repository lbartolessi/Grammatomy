import unittest
from typing import List

from src.core.grammatomy.essential_validator import EssentialStructureValidator


class TestAnCoraRealCases(unittest.TestCase):
    """
    Test de estrés basado en la Sintaxis Nativa de AnCora (Stanza Output).
    Valida que el motor acepte la estructura canónica definida en hybrid_rules.yaml
    (sn, grup.nom, sentence) y rechace las estructuras corruptas.
    """

    def setUp(self):
        self.validator = EssentialStructureValidator()

    def check_validity(self, node_type: str, children: List[str], expected: bool, case_name: str):
        print(f"\n🔍 Case: {case_name}")
        print(f"   Structure: {node_type} -> {children}")
        result, missing = self.validator.validate_node(node_type, children)
        status = "✅ OK" if result == expected else "❌ FAIL"
        missing_str = f" (Missing: {missing})" if missing else ""
        print(f"   Result: {result}{missing_str} (Expected: {expected}) -> {status}")
        self.assertEqual(
            result, expected, f"Fallo en {case_name}: Esperado {expected}, obtenido {result}"
        )

    def test_sn_structure(self):
        """
        Cobertura para sn (Sintagma Nominal).
        Regla: Requiere grup.nom.
        """
        # 1. Canónico (sn -> grup.nom)
        self.check_validity("sn", ["grup.nom"], True, "sn Canónico")

        # 2. Complejo (sn -> spec + grup.nom)
        self.check_validity("sn", ["spec", "grup.nom"], True, "sn Complejo")

        # 3. Aplanado (sn -> NOUN) - Stanza a veces aplana grup.nom
        # El validador debe detectar que falta grup.nom pero aceptar NOUN
        self.check_validity("sn", ["NOUN"], True, "sn Aplanado (NOUN)")

        # 4. Inválido (Sin núcleo)
        self.check_validity("sn", ["spec"], False, "sn Inválido (Solo spec)")

    def test_sp_structure(self):
        """
        Cobertura para sp (Sintagma Preposicional).
        Regla: Requiere ADP (Preposición) Y Término (sn/grup.nom/S).
        """
        # 1. Canónico (sp -> ADP + sn)
        self.check_validity("sp", ["ADP", "sn"], True, "sp Canónico")

        # 2. Aplanado (sp -> ADP + NOUN)
        self.check_validity("sp", ["ADP", "NOUN"], True, "sp Aplanado (ADP+NOUN)")

        # 3. Inválido (Falta preposición)
        self.check_validity("sp", ["sn"], False, "sp Inválido (Sin ADP)")

    def test_grup_verb_structure(self):
        """
        Cobertura para grup.verb.
        Regla: Requiere VERB o AUX.
        """
        self.check_validity("grup.verb", ["VERB"], True, "grup.verb Simple")
        self.check_validity("grup.verb", ["AUX", "VERB"], True, "grup.verb Compuesto")
        self.check_validity("grup.verb", ["sn"], False, "grup.verb Inválido (Sin verbo)")

    def test_sentence_structure(self):
        """
        Cobertura para sentence (Oración).
        Regla: Requiere grup.verb.
        """
        self.check_validity("sentence", ["grup.verb"], True, "sentence Canónica")
        # sentence -> sn + VERB (Aplanado, grup.verb implícito)
        self.check_validity("sentence", ["sn", "VERB"], True, "sentence Aplanada (con VERB)")
        self.check_validity("sentence", ["sn"], False, "sentence Inválida (Sin verbo)")


if __name__ == "__main__":
    unittest.main()
