"""
Fragmentation Engine.

Handles the recursive splitting of syntax trees into manageable subtrees (Góngora Mode)
and their reconstruction (Defragmentation).
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from anytree import Node, PreOrderIter

from core.grammatomy.config import config
from core.grammatomy.exporters.ptb_exporter import PtbExporter
from core.grammatomy.grammar import PUNCTUATION_TAGS
from core.grammatomy.logger import setup_logging
from core.grammatomy.parsers.lisp_parser import LispParser
from core.grammatomy.tree_comparator import TreeComparator

logger = setup_logging(__name__)


class FragmentationEngine:
    def __init__(self):
        self.parser = LispParser()
        self.exporter = PtbExporter()

    def _parse_and_normalize(self, ptb: str) -> Optional[Node]:
        wrapped_ptb = f"(VIRTUAL_ROOT {ptb})"
        root = self.parser.to_anytree(wrapped_ptb)
        if not root:
            return None
        if root.name != "VIRTUAL_ROOT":
            virtual_root = Node("VIRTUAL_ROOT")
            root.parent = virtual_root
            root = virtual_root
        return root

    def _identify_s_nodes(self, root: Node) -> List[Node]:
        def count_real_words(n):
            return sum(
                1 for leaf in n.leaves if leaf.parent and leaf.parent.name not in PUNCTUATION_TAGS
            )

        candidates = []
        for node in PreOrderIter(root):
            if (
                node.name == "S"
                and node.parent
                and node.parent.name not in ("ROOT", "VIRTUAL_ROOT")
            ):
                # Filter: Only extract if it has > 2 real words (punctuation excluded)
                if count_real_words(node) > 2:
                    candidates.append(node)
        return candidates

    def _assign_labels(self, s_nodes_top_down: List[Node]) -> Dict[Node, str]:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        counter = 0
        labels = {}
        for s_node in s_nodes_top_down:
            if counter < len(alphabet):
                label = alphabet[counter]
            else:
                label = f"Z{counter}"
            counter += 1
            labels[s_node] = label
        return labels

    def _find_parent_label(self, node: Node, node_labels: Dict[Node, str]) -> str:
        curr = node.parent
        while curr:
            if curr in node_labels:
                return node_labels[curr]
            curr = curr.parent
        return "Main"

    def _extract_subtrees(self, s_nodes: List[Node], node_labels: Dict[Node, str]) -> List[Dict]:
        subtrees = []
        s_nodes_processing = sorted(s_nodes, key=lambda n: n.depth, reverse=True)

        for s_node in s_nodes_processing:
            label = node_labels[s_node]
            uid = uuid.uuid4().hex[:8]
            parent_label = self._find_parent_label(s_node, node_labels)
            content_ptb = self.exporter.export(s_node)
            link_root_name = f"LINK-{parent_label}-{uid}"
            subtrees.append(
                {
                    "id": f"st_{label}",
                    "label": label,
                    "root_node_id": str(id(s_node)),  # Internal ref
                    "ptb": f"({link_root_name} {content_ptb})",
                    "notes": f"Extracted from {parent_label}",
                }
            )
            s_node.children = [Node(f"LINK-{label}-{uid}")]
        return subtrees

    def fragment(self, ptb: str) -> Tuple[str, List[Dict], Optional[Dict[str, Any]]]:
        """
        Recursively fragments a tree at 'S' nodes.
        Returns (main_ptb, list_of_subtrees).
        """
        root = self._parse_and_normalize(ptb)
        if not root:
            return ptb, [], None

        s_nodes = self._identify_s_nodes(root)
        node_labels = self._assign_labels(s_nodes)
        subtrees = self._extract_subtrees(s_nodes, node_labels)

        # Unwrap VIRTUAL_ROOT for export
        main_ptb = " ".join([self.exporter.export(c) for c in root.children])

        # --- Integrity Check (Master Map Verification) ---
        integrity_info = self._verify_integrity(ptb, main_ptb, subtrees)
        return main_ptb, subtrees, integrity_info

    def _replace_link_node(self, link_node: Node, subtree_ptb: str):
        st_root = self.parser.to_anytree(subtree_ptb)
        if st_root and st_root.children:
            real_content = st_root.children[0]  # The S node
            parent = link_node.parent
            if parent:
                new_kids = list(parent.children)
                try:
                    idx = new_kids.index(link_node)
                    new_kids[idx : idx + 1] = real_content.children
                    parent.children = new_kids
                except ValueError:
                    pass

    def _resolve_links_pass(self, root: Node, subtree_map: Dict[str, str]) -> bool:
        for node in PreOrderIter(root):
            if node.name.startswith("LINK-") and len(node.name.split("-")) > 1:
                label = node.name.split("-")[1]
                if label in subtree_map:
                    self._replace_link_node(node, subtree_map[label])
                    return True
        return False

    def defragment(self, main_ptb: str, subtrees: List[Dict]) -> str:
        """
        Merges subtrees back into the main tree.
        """
        root = self._parse_and_normalize(main_ptb)
        if not root:
            return main_ptb

        # Map label -> subtree ptb
        subtree_map = {st["label"]: st["ptb"] for st in subtrees}

        # Iterative replacement approach (safer)
        # Dynamic limit: Ensure we have enough passes for all fragments + buffer
        max_iterations = max(50, len(subtrees) * 2)
        for _ in range(max_iterations):
            if not self._resolve_links_pass(root, subtree_map):
                break

        # Unwrap VIRTUAL_ROOT for export
        return " ".join([self.exporter.export(c) for c in root.children])

    def _verify_integrity(
        self, original_ptb: str, main_ptb: str, subtrees: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        if not config.debug:
            return None

        try:
            reconstructed_ptb = self.defragment(main_ptb, subtrees)
            diffs = TreeComparator.compare_ptb(original_ptb, reconstructed_ptb)
            if diffs:
                logger.warning("Integrity Check Failed! %d differences found.", len(diffs))
                for d in diffs[:5]:
                    logger.warning("  - %s", d)
                return {"status": "failed", "diffs": diffs}

            logger.info("Integrity Check Passed: Master Map reconstruction matches original.")
            return {"status": "passed", "diffs": []}
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Integrity Check Crashed: %s", e)
            return {"status": "error", "message": str(e)}
