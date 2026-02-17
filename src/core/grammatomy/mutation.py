"""
Mutation Engine for Grammatomy.
Handles structural surgery (Detach/Reabsorb) using object-based tree manipulation.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from anytree import PreOrderIter

from core.grammatomy.config import config
from core.grammatomy.exporters.ptb_exporter import PtbExporter
from core.grammatomy.logger import setup_logging
from core.grammatomy.parsers.lisp_parser import LispParser, SyntaxNode
from core.grammatomy.tree_comparator import TreeComparator

logger = setup_logging(__name__)


class MutationEngine:
    """
    Encapsulates logic for grafting and pruning syntax trees.
    """

    @classmethod
    def reabsorb(cls, main_ptb: str, fragment_ptb: str, link_label: str) -> Dict[str, Any]:
        """
        Replaces a LINK node in the main tree with the content of the fragment.
        """
        parser = LispParser()
        exporter = PtbExporter()

        # 1. Parse trees
        main_tree, fragment_tree = cls._parse_trees(parser, main_ptb, fragment_ptb)

        # 2. Find Target Link
        target_link = cls._find_target_link(main_tree, link_label)

        # 3. Extract Content
        content_nodes = cls._extract_content_nodes(fragment_tree)

        # 4. Grafting
        cls._graft_content(target_link, content_nodes)

        # 5. Calculate Focus Index
        focus_index = cls._calculate_focus_index(main_tree, content_nodes)

        # 6. Export
        new_ptb = " ".join([exporter.export(c) for c in main_tree.children])
        return {"ptb": new_ptb, "focus_index": focus_index}

    @staticmethod
    def _parse_trees(
        parser: LispParser, main_ptb: str, fragment_ptb: str
    ) -> Tuple[SyntaxNode, SyntaxNode]:
        wrapped_main = f"(VIRTUAL_ROOT {main_ptb})"
        main_tree = parser.to_anytree(wrapped_main)
        fragment_tree = parser.to_anytree(fragment_ptb)

        if not main_tree:
            raise ValueError("Invalid Main PTB")
        if not fragment_tree:
            raise ValueError("Invalid Fragment PTB")

        if main_tree.name != "VIRTUAL_ROOT":
            virtual_root = SyntaxNode("VIRTUAL_ROOT")
            main_tree.parent = virtual_root
            main_tree = virtual_root

        return main_tree, fragment_tree

    @staticmethod
    def _find_target_link(main_tree: SyntaxNode, link_label: str) -> SyntaxNode:
        base_name = f"LINK-{link_label}"
        matches = [
            n
            for n in PreOrderIter(main_tree)
            if getattr(n, "name", "") == base_name
            or getattr(n, "name", "").startswith(f"{base_name}-")
        ]

        if len(matches) == 1:
            target_link = matches[0]
            # Diagnostic trace
            path_names = [n.name for n in target_link.path]
            logger.debug("target_link='%s' path=%s", target_link.name, path_names)
            return target_link

        if len(matches) > 1:
            raise ValueError(f"Ambiguous reabsorption: multiple matches for '{base_name}' found.")

        # No match found
        all_links = [
            n.name for n in PreOrderIter(main_tree) if getattr(n, "name", "").startswith("LINK-")
        ]
        diag_msg = f"No se encontró el nodo de enlace '{base_name}' en el árbol principal."
        if all_links:
            diag_msg += f" Nodos LINK disponibles: {all_links[:5]}"
        else:
            diag_msg += " (No LINK nodes found at all in tree)"
        logger.error(diag_msg)
        raise ValueError(diag_msg)

    @staticmethod
    def _extract_content_nodes(fragment_tree: SyntaxNode) -> List[SyntaxNode]:
        content_nodes: List[SyntaxNode] = []

        # Strategy C: Root IS the LINK
        if fragment_tree.name.startswith("LINK-"):
            content_nodes = list(fragment_tree.children)
        else:
            # Strategy A: Content is sibling of LINK
            for child in fragment_tree.children:
                if not child.name.startswith("LINK"):
                    content_nodes.append(child)

            # Strategy B: Content is child of LINK
            if not content_nodes:
                link_node = next(
                    (c for c in fragment_tree.children if c.name.startswith("LINK-")), None
                )
                if link_node:
                    content_nodes = list(link_node.children)
        return content_nodes

    @staticmethod
    def _graft_content(target_link: SyntaxNode, content_nodes: List[SyntaxNode]) -> None:
        parent = target_link.parent
        if not parent:
            return

        # Redundancy Check
        if len(content_nodes) == 1 and content_nodes[0].name == parent.name:
            logger.info(
                "Detected %s->%s redundancy. Unwrapping child node.",
                parent.name,
                content_nodes[0].name,
            )
            wrapper = content_nodes[0]
            content_nodes = list(wrapper.children)

        logger.info(
            "parent='%s' will receive %d node(s): %s",
            parent.name,
            len(content_nodes),
            [n.name for n in content_nodes],
        )

        siblings = list(parent.children)
        try:
            link_index = siblings.index(target_link)
            siblings.pop(link_index)

            for node in content_nodes:
                node.parent = None

            for i, node in enumerate(content_nodes):
                siblings.insert(link_index + i, node)

            parent.children = tuple(siblings)
            target_link.parent = None
        except ValueError:
            pass

    @staticmethod
    def _calculate_focus_index(main_tree: SyntaxNode, content_nodes: List[SyntaxNode]) -> int:
        if not content_nodes:
            return -1
        first_inserted = content_nodes[0]
        counter = 0
        for root_child in main_tree.children:
            for node in PreOrderIter(root_child):
                if node is first_inserted:
                    return counter
                counter += 1
        return -1

    @classmethod
    def detach(
        cls,
        main_ptb: str,
        node_path: List[int],
        fragment_label: str,
        parent_context_label: str = "Main",
        target_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detaches the children of a specific node (identified by Path from Root)
        into a new fragment, leaving a LINK node in its place.
        """
        parser = LispParser()
        exporter = PtbExporter()

        # 1. Parse Main Tree
        main_tree = cls._parse_main_tree_for_detach(parser, main_ptb)

        # 2. Locate Target Node
        target_node = cls._locate_node_by_path(main_tree, node_path, target_label)

        if target_node.is_leaf:
            raise ValueError("Cannot detach a leaf node.")

        # 3. Create Fragment
        children_to_move = list(target_node.children)
        logger.info(
            "Moving %d children from '%s' to fragment.",
            len(children_to_move),
            target_node.name,
        )

        uid = uuid.uuid4().hex[:8]
        fragment_ptb_str = cls._create_fragment(
            children_to_move, target_node.name, parent_context_label, uid, exporter
        )

        # 4. Modify Main Tree
        link_forward = SyntaxNode(f"LINK-{fragment_label}-{uid}")
        target_node.children = [link_forward]

        new_main_ptb = " ".join([exporter.export(c) for c in main_tree.children])

        # 5. Integrity Check
        integrity_info = cls._check_integrity(
            main_ptb, new_main_ptb, fragment_ptb_str, fragment_label
        )

        return {
            "main_ptb": new_main_ptb,
            "fragment_ptb": fragment_ptb_str,
            "integrity_check": integrity_info,
        }

    @staticmethod
    def _parse_main_tree_for_detach(parser: LispParser, main_ptb: str) -> SyntaxNode:
        wrapped_ptb = f"(VIRTUAL_ROOT {main_ptb})"
        main_tree = parser.to_anytree(wrapped_ptb)
        if not main_tree:
            raise ValueError("Invalid PTB")

        if main_tree.name != "VIRTUAL_ROOT":
            virtual_root = SyntaxNode("VIRTUAL_ROOT")
            main_tree.parent = virtual_root
            main_tree = virtual_root
        return main_tree

    @staticmethod
    def _locate_node_by_path(
        main_tree: SyntaxNode, node_path: List[int], target_label: Optional[str]
    ) -> SyntaxNode:
        current_node = main_tree
        try:
            for idx in node_path:
                current_node = current_node.children[idx]
            target_node = current_node
        except (IndexError, AttributeError) as exc:
            raise ValueError(f"Node at path {node_path} not found.") from exc

        logger.debug(
            "Found Node: '%s' (Children: %s)",
            target_node.name,
            [c.name for c in target_node.children],
        )

        if target_label and target_node.name != target_label:
            raise ValueError(
                f"Target node mismatch: Expected '{target_label}', "
                f"found '{target_node.name}' at path {node_path}."
            )
        return target_node

    @staticmethod
    def _create_fragment(
        children: List[SyntaxNode],
        container_name: str,
        parent_context: str,
        uid: str,
        exporter: PtbExporter,
    ) -> str:
        link_back_name = f"LINK-{parent_context}-{uid}"
        fragment_root = SyntaxNode(link_back_name)
        container_node = SyntaxNode(container_name, parent=fragment_root)

        for child in children:
            child.parent = container_node

        return exporter.export(fragment_root)

    @staticmethod
    def _check_integrity(
        original_ptb: str, new_main: str, fragment_ptb: str, fragment_label: str
    ) -> Dict[str, Any]:
        if not config.debug:
            return {"status": "skipped", "diffs": []}

        try:
            reabsorbed = MutationEngine.reabsorb(new_main, fragment_ptb, fragment_label)
            diffs = TreeComparator.compare_ptb(original_ptb, reabsorbed["ptb"])
            if diffs:
                logger.warning("Integrity Check Failed! %d differences found.", len(diffs))
                for d in diffs[:5]:
                    logger.warning("  - %s", d)
                return {"status": "failed", "diffs": diffs}

            logger.info("Integrity Check Passed: Detach is reversible.")
            return {"status": "passed", "diffs": []}
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Integrity Check Crashed: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def delete_node(main_ptb: str, node_index: int) -> Dict[str, str]:
        """
        Deletes a node (and its subtree) from the tree.
        - If a terminal word is deleted, its parent POS tag is deleted.
        - If a parent becomes empty, a Ghost node is spawned.
        - ROOT cannot be deleted.
        """
        parser = LispParser()
        exporter = PtbExporter()

        root = parser.to_anytree(main_ptb)
        if not root:
            raise ValueError("Invalid PTB")

        target_node = None
        for i, node in enumerate(PreOrderIter(root)):
            if i == node_index:
                target_node = node
                break

        if not target_node:
            raise ValueError(f"Node at index {node_index} not found.")

        if target_node.is_root:
            raise ValueError("Cannot delete ROOT node.")

        # Logic: If leaf (and not ghost), delete parent (POS tag)
        node_to_delete = target_node
        is_ghost = "👻" in target_node.name
        if target_node.is_leaf and not is_ghost:
            if target_node.parent and not target_node.parent.is_root:
                node_to_delete = target_node.parent

        parent = node_to_delete.parent
        node_to_delete.parent = None  # Detach from tree

        # If parent became empty, spawn a ghost to preserve structure
        if parent and not parent.children:
            SyntaxNode("👻", parent=parent)

        return {"ptb": exporter.export(root)}
