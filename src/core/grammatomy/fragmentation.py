"""
Fragmentation Engine.

Handles the recursive splitting of syntax trees into manageable subtrees (Góngora Mode)
and their reconstruction (Defragmentation).
"""

from typing import Dict, List, Optional, Tuple

from anytree import Node, PreOrderIter, RenderTree

from core.grammatomy.exporters.ptb_exporter import PtbExporter
from core.grammatomy.parsers.lisp_parser import LispParser


class FragmentationEngine:
    def __init__(self):
        self.parser = LispParser()
        self.exporter = PtbExporter()

    def fragment(self, ptb: str) -> Tuple[str, List[Dict]]:
        """
        Recursively fragments a tree at 'S' nodes.
        Returns (main_ptb, list_of_subtrees).
        """
        root = self.parser.to_anytree(ptb)
        if not root:
            return ptb, []

        subtrees = []
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        counter = 0

        # 1. Identify S nodes to extract (Bottom-Up to handle nesting)
        # We skip the main sentence node usually (child of ROOT)

        # Helper to find S nodes
        s_nodes = []
        for node in PreOrderIter(root):
            if node.name == "S" and node.parent and node.parent.name != "ROOT":
                # We verify it's not the main sentence if the structure is (ROOT (S ...))
                # Actually, we want to fragment sub-clauses.
                # Let's collect all S nodes that are NOT direct children of ROOT.
                s_nodes.append(node)

        # Sort by depth descending (deepest first)
        s_nodes.sort(key=lambda n: n.depth, reverse=True)

        # Map node instances to labels
        node_labels = {}

        for s_node in s_nodes:
            # Generate Label
            if counter < len(alphabet):
                label = alphabet[counter]
            else:
                label = f"Z{counter}"
            counter += 1

            node_labels[s_node] = label

            # Determine Parent Label (for navigation)
            parent_label = "0"
            # Check if any ancestor is also being extracted
            curr = s_node.parent
            while curr:
                if curr in node_labels:
                    parent_label = node_labels[curr]
                    break
                curr = curr.parent

            # Serialize the subtree content
            # Note: If this node contains children that were already replaced by LINKs,
            # the serialization will include those LINKs, which is correct.
            content_ptb = self.exporter.export(s_node)

            # Wrap in LINK-Parent structure for the subtree view
            # The subtree view root should be a LINK back to parent, containing the S node
            # But wait, the S node IS the content.
            # Visual requirement: LINK-0 -> S ...

            # Create a temporary root for the subtree view
            link_root = Node(f"LINK-{parent_label}")
            # We need to clone s_node to attach it to link_root without detaching from original yet?
            # No, we export s_node, so we have the string.

            # Store subtree data
            subtrees.append(
                {
                    "id": f"st_{label}",
                    "label": label,
                    "root_node_id": str(id(s_node)),  # Internal ref
                    "ptb": f"(LINK-{parent_label} {content_ptb})",
                    "notes": f"Extracted from {parent_label}",
                }
            )

            # Modify the main tree: Replace S node children with a LINK node
            # We don't remove S, we remove its children and add a LINK child.
            # Spec: "En las S del arbol ROOT añadimos un nodo hijo... que diga (A...)"
            s_node.children = [Node(f"LINK-{label}")]

        main_ptb = self.exporter.export(root)
        return main_ptb, subtrees

    def defragment(self, main_ptb: str, subtrees: List[Dict]) -> str:
        """
        Merges subtrees back into the main tree.
        """
        root = self.parser.to_anytree(main_ptb)
        if not root:
            return main_ptb

        # Map label -> subtree ptb
        subtree_map = {st["label"]: st["ptb"] for st in subtrees}

        # Find LINK nodes in main tree
        # We need to iterate and replace. Since we might have nested links,
        # we might need multiple passes or recursive resolution.
        # But since we have the full map, we can resolve on the fly?
        # Actually, the main tree contains LINK-A. Subtree A contains LINK-B.
        # If we replace LINK-A with Subtree A content, we then need to find LINK-B in that content.

        # Strategy: Resolve recursively.

        def resolve_node(node):
            # Check if node is a LINK (e.g. "LINK-A")
            if node.name.startswith("LINK-") and node.name.split("-")[1] in subtree_map:
                label = node.name.split("-")[1]
                subtree_ptb = subtree_map[label]

                # Parse subtree
                st_root = self.parser.to_anytree(subtree_ptb)
                # st_root is "LINK-Parent". Its child is the "S" node we want.
                if st_root and st_root.children:
                    real_content = st_root.children[0]  # The S node

                    # The parent of the LINK node in the main tree is the S node that was emptied.
                    # We want to replace the LINK node with the *children* of the restored S node.
                    # Wait, in fragment() we did: s_node.children = [Node(f"LINK-{label}")]
                    # So node.parent is the S node.
                    # We want to set node.parent.children = real_content.children

                    # Recursively resolve children of the restored content first
                    for child in real_content.children:
                        resolve_node(child)

                    return real_content.children

            # Standard recursion
            new_children = []
            for child in node.children:
                resolved = resolve_node(child)
                if isinstance(resolved, (list, tuple)):
                    new_children.extend(resolved)
                else:
                    # If it returned None or similar (shouldn't happen logic-wise here), keep child
                    # But resolve_node returns list of children if replacement happens
                    # Wait, if it's not a link, we just recurse.
                    # The recursion above modifies the tree in place? No, AnyTree structure is mutable.
                    # But if we replace children, we need to assign them.
                    pass

            # This recursion logic is tricky with AnyTree iterators.
            # Better: Find all LINK nodes, replace them. Repeat until no LINKs found.
            return None

        # Iterative replacement approach (safer)
        iterations = 0
        while iterations < 10:  # Safety break
            found_link = False
            for node in PreOrderIter(root):
                if node.name.startswith("LINK-") and len(node.name.split("-")) > 1:
                    label = node.name.split("-")[1]
                    if label in subtree_map:
                        # Found a link to resolve
                        subtree_ptb = subtree_map[label]
                        st_root = self.parser.to_anytree(subtree_ptb)

                        if st_root and st_root.children:
                            real_content = st_root.children[0]  # The S node

                            # Parent of LINK is the S node container
                            parent = node.parent
                            if parent:
                                # Replace LINK with the children of the restored S
                                # We must detach LINK and attach new children
                                # AnyTree: parent.children is a tuple.

                                # We want to preserve order? LINK is usually the only child.
                                new_kids = list(parent.children)
                                idx = new_kids.index(node)

                                # Insert real content children at index
                                replacement_kids = real_content.children
                                new_kids[idx : idx + 1] = replacement_kids

                                parent.children = new_kids
                                found_link = True
                                # Break to restart iteration (tree changed)
                                break

            if not found_link:
                break
            iterations += 1

        return self.exporter.export(root)
