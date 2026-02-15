"""
Mutation Engine for Grammatomy.
Handles structural surgery (Detach/Reabsorb) using object-based tree manipulation.
"""

from anytree import Node, PreOrderIter, RenderTree

from core.grammatomy.exporters.ptb_exporter import PtbExporter
from core.grammatomy.parsers.lisp_parser import LispParser


class MutationEngine:
    """
    Encapsulates logic for grafting and pruning syntax trees.
    """

    @staticmethod
    def reabsorb(main_ptb: str, fragment_ptb: str, link_label: str) -> dict:
        """
        Replaces a LINK node in the main tree with the content of the fragment.
        """
        parser = LispParser()
        exporter = PtbExporter()

        # 1. Parse both trees into objects
        main_tree = parser.to_anytree(main_ptb)
        fragment_tree = parser.to_anytree(fragment_ptb)

        # 2. Find the Target Link Node in Main Tree
        # We look for LINK-{label} or just LINK if label is generic
        target_link = None
        target_name = f"LINK-{link_label}"

        for node in PreOrderIter(main_tree):
            # Check for exact match or if the node label starts with LINK- and matches
            # Robustness: Match "LINK-A", "LINK-A_1", "LINK-A " to handle parser artifacts
            if (
                node.name == target_name
                or node.name.startswith(f"{target_name}_")
                or node.name.startswith(f"{target_name} ")
            ):
                target_link = node
                break

        if not target_link:
            raise ValueError(
                f"No se encontró el nodo de enlace 'LINK-{link_label}' en el árbol principal."
            )

        # 3. Extract Content from Fragment
        # The fragment usually comes as (ROOT (LINK-X ...) (RealContent...))
        # or (ROOT (RealContent...)). We want the children of the ROOT.

        # Strategy A: Content is sibling of LINK (Flat structure - Legacy)
        # (ROOT (LINK) (Content...))
        content_nodes = []
        for child in fragment_tree.children:
            if not child.name.startswith("LINK"):
                content_nodes.append(child)

        # Strategy B: Content is child of LINK (Nested structure - New Standard)
        # (ROOT (LINK (Content...)))
        if not content_nodes:
            link_node = next((c for c in fragment_tree.children if c.name.startswith("LINK")), None)
            if link_node:
                content_nodes = list(link_node.children)

        # 4. Grafting (Cirugía)
        parent = target_link.parent
        if parent:
            # Heuristic: Prevent S -> S duplication (Redundant Wrapper)
            # If the fragment contains a single node that matches the parent's label,
            # we unwrap it to avoid nesting the same category.
            if len(content_nodes) == 1 and content_nodes[0].name == parent.name:
                wrapper = content_nodes[0]
                # Use the children of the wrapper as the actual content
                content_nodes = list(wrapper.children)

            # Get current children as a list to modify
            siblings = list(parent.children)
            try:
                link_index = siblings.index(target_link)

                # Remove the LINK node
                siblings.pop(link_index)

                # Detach content nodes from fragment first to be clean
                for node in content_nodes:
                    node.parent = None

                # Insert into the list
                for i, node in enumerate(content_nodes):
                    siblings.insert(link_index + i, node)

                # Commit changes to parent
                parent.children = tuple(siblings)

                # Explicitly detach the link node to be sure
                target_link.parent = None

            except ValueError:
                pass  # Link not in children? Should not happen if found via search.
        else:
            # Target is ROOT (No parent). Replace the entire tree content.
            if content_nodes:
                # If multiple nodes, we might need a dummy ROOT, but usually fragments have one top node.
                # We take the first node as the new root.
                new_root = content_nodes[0]
                new_root.parent = None
                # If there were siblings in content_nodes, they are lost unless wrapped.
                # Assuming standard (ROOT ...) structure where content_nodes=[S].
                main_tree = new_root

        # 5. Calculate Focus Index (DFS/PreOrder index of the first inserted node)
        focus_index = -1
        if content_nodes:
            first_inserted = content_nodes[0]
            for i, node in enumerate(PreOrderIter(main_tree)):
                if node is first_inserted:
                    focus_index = i
                    break

        # 6. Export back to PTB string
        return {"ptb": exporter.export(main_tree), "focus_index": focus_index}

    @staticmethod
    def detach(
        main_ptb: str, node_index: int, fragment_label: str, parent_context_label: str = "Main"
    ) -> dict:
        """
        Detaches the children of a specific node (identified by PreOrder index)
        into a new fragment, leaving a LINK node in its place.
        """
        parser = LispParser()
        exporter = PtbExporter()

        # 1. Parse Main Tree
        main_tree = parser.to_anytree(main_ptb)
        if not main_tree:
            raise ValueError("Invalid PTB")

        # 2. Locate Target Node by Index (PreOrder / DFS)
        # We assume the frontend calculates index based on the same traversal order.
        target_node = None
        for i, node in enumerate(PreOrderIter(main_tree)):
            if i == node_index:
                target_node = node
                break

        if not target_node:
            raise ValueError(f"Node at index {node_index} not found.")

        if target_node.is_leaf:
            raise ValueError("Cannot detach a leaf node.")

        # 3. Extract Children (The Content)
        children_to_move = list(target_node.children)

        # 4. Create Fragment Tree
        # Structure: (ROOT (LINK-{ParentContext} (Container (Child1) (Child2)...)))
        fragment_root = Node("ROOT")
        link_back = Node(f"LINK-{parent_context_label}", parent=fragment_root)

        # Duplicate the container node as a child of the LINK (The "Triangle")
        container_node = Node(target_node.name, parent=link_back)

        for child in children_to_move:
            child.parent = container_node

        # 5. Modify Main Tree (Surgery)
        # Replace children with LINK-{FragmentLabel}
        link_forward = Node(f"LINK-{fragment_label}")
        target_node.children = [link_forward]

        return {
            "main_ptb": exporter.export(main_tree),
            "fragment_ptb": exporter.export(fragment_root),
        }
