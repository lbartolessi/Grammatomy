"""
Tests de Casos Límite y Resiliencia para Grammar.

Este módulo implementa la filosofía de "Regression Testing":
Verifica explícitamente el comportamiento del sistema ante fallos de I/O,
corrupción de datos y violaciones de integridad léxica.
"""

import unittest
from unittest.mock import mock_open, patch

from anytree import Node

from src.core.grammatomy.grammar import (
    load_grammar_rules,
    validate_leaf_consistency,
    validate_structure,
)


class TestGrammarResilience(unittest.TestCase):
    """Verifica la robustez del módulo Grammar ante condiciones adversas."""

    @patch("pathlib.Path.exists")
    def test_load_rules_missing_file(self, mock_exists):
        """Debe retornar diccionarios vacíos si el archivo YAML no existe."""
        mock_exists.return_value = False
        with self.assertLogs("src.core.grammatomy.grammar", level="WARNING") as cm:
            rules, descriptions = load_grammar_rules()
            self.assertEqual(rules, {})
            self.assertEqual(descriptions, {})
            self.assertIn("Grammar rules file not found", cm.output[0])

    @patch("builtins.open", new_callable=mock_open, read_data="invalid: [yaml: content")
    @patch("pathlib.Path.exists")
    def test_load_rules_corrupt_yaml(self, mock_exists, mock_file):
        """Debe manejar errores de parsing YAML silenciosamente y loguear el error."""
        mock_exists.return_value = True
        with self.assertLogs("src.core.grammatomy.grammar", level="ERROR") as cm:
            # Forzamos que yaml.safe_load falle (el mock de open entrega basura)
            rules, descriptions = load_grammar_rules()
            self.assertEqual(rules, {})
            self.assertEqual(descriptions, {})
            self.assertIn("Error loading grammar rules", cm.output[0])

    def test_leaf_consistency_edge_cases(self):
        """Verifica reglas estrictas de validación léxica."""
        # Caso 1: Palabra con espacios (debería ser un compuesto con guiones)
        valid, msg = validate_leaf_consistency("bad word", "NOUN")
        self.assertFalse(valid)
        self.assertIn("spaces", msg)

        # Caso 2: Puntuación etiquetada como palabra
        valid, msg = validate_leaf_consistency(".", "NOUN")
        self.assertFalse(valid)
        self.assertIn("punctuation", msg)

        # Caso 3: Palabra etiquetada como puntuación (AnCora 'fp' = punto final)
        valid, msg = validate_leaf_consistency("Hola", "fp")
        self.assertFalse(valid)
        self.assertIn("not a valid punctuation", msg)

        # Caso 4: Puntuación válida
        valid, _ = validate_leaf_consistency(".", "fp")
        self.assertTrue(valid)

    def test_validate_structure_ghosts(self):
        """Verifica que validate_structure detecte nodos fantasma."""
        root = Node("S")
        ghost = Node("👻", parent=root)

        violations = validate_structure(root)
        self.assertIn(ghost, violations)
        self.assertIn("Nodo Fantasma", violations[ghost])

    def test_validate_structure_unknown_parent(self):
        """Nodos con padres desconocidos en las reglas deben ser ignorados (o manejados)."""
        root = Node("UNKNOWN_TAG")
        child = Node("sn", parent=root)

        # Si el padre no está en las reglas, no se puede validar, no debería explotar.
        violations = validate_structure(root)
        self.assertEqual(violations, {})


if __name__ == "__main__":
    unittest.main()
