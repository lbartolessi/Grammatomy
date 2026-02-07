from typing import Optional

from anytree import Node
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QPainter,
    QPen,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneContextMenuEvent,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QInputDialog,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core.grammatomy import to_ptb
from core.grammatomy.glossary import TAG_MAP
from core.grammatomy.grammar import (
    GRAMMAR_RULES,
    NODE_DESCRIPTIONS,
    PUNCTUATION_INVENTORY,
    PUNCTUATION_TAGS,
    get_suggestions,
    validate_leaf_consistency,
)
from core.grammatomy.grammar import validate_structure

# --- CONFIGURATION ---
# Colorblind-friendly palette (Wong)
COLORS = {
    "PHRASAL": "#E69F00",  # Orange
    "POS": "#56B4E9",  # Sky Blue
    "WORD": "#009E73",  # Bluish Green
    "PUNCT": "#999999",  # Grey
    "DEFAULT": "#F0E442",  # Yellow (Fallback)
    "ERROR": "#D55E00",  # Vermilion (Wong Palette - High Contrast)
}

LABEL_PROMPT = "Etiqueta:"
FONT_FAMILY = "Segoe UI"


class ZoomView(QGraphicsView):
    """Custom View with Zoom support."""

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event:
            zoom_in = event.angleDelta().y() > 0
            scale_factor = 1.15 if zoom_in else 1 / 1.15
            self.scale(scale_factor, scale_factor)
        else:
            super().wheelEvent(event)


class SyntaxNodeItem(QGraphicsRectItem):
    """A draggable graphical representation of a syntax node."""

    def __init__(
        self,
        node: Node,
        x: float,
        y: float,
        editor_ref,
        error_msg: Optional[str] = None,
    ):
        super().__init__(0, 0, 0, 0)  # Rect initialized later
        self.node_ref = node
        self.editor_ref = editor_ref  # Reference to SyntaxEditor widget
        self.error_msg = error_msg

        self.edges_in = []
        self.edges_out = []

        self.setZValue(1)

        # Determine Color
        if node.is_leaf:
            color_code = COLORS["WORD"]
        elif any(child.is_leaf for child in node.children):
            if node.name in PUNCTUATION_TAGS or (
                len(node.name) > 0 and node.name.startswith("f") and node.name[0] == "f"
            ):
                color_code = COLORS["PUNCT"]
            else:
                color_code = COLORS["POS"]
        else:
            color_code = COLORS["PHRASAL"]

        self.setBrush(QBrush(QColor(color_code)))

        # Tooltip Logic
        description = NODE_DESCRIPTIONS.get(node.name)
        if not description:
            # Fallback to Glossary
            description = TAG_MAP["Phrasal"].get(node.name) or TAG_MAP["POS"].get(node.name)

        tooltip_parts = []
        if description:
            tooltip_parts.append(f"<b>{node.name}</b>: {description}")

        if self.error_msg:
            self.setPen(QPen(QColor(COLORS["ERROR"]), 4))
            tooltip_parts.append(f"⚠️ <b>Error:</b> {self.error_msg}")
        else:
            self.setPen(QPen(Qt.GlobalColor.white, 1))

        if tooltip_parts:
            self.setToolTip("<br>".join(tooltip_parts))

        self.text_item = QGraphicsSimpleTextItem(node.name, self)
        self.text_item.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        self.text_item.setBrush(QBrush(Qt.GlobalColor.white))

        padding = 10
        brect = self.text_item.boundingRect()
        self.setRect(0, 0, brect.width() + padding * 2, brect.height() + padding)
        self.text_item.setPos(padding, padding / 2)

        flags = (
            QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        if node.name != "👻":
            flags |= QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
        self.setFlags(flags)
        self.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            self.editor_ref.update_edges(self)
        return super().itemChange(change, value)

    def set_highlight(self, active: bool):
        if active:
            pen = QPen(QColor("#76FF03"))
            pen.setWidth(3)
            self.setPen(pen)
        else:
            self.setPen(QPen(Qt.GlobalColor.white, 1))

    def _validate_orphan_rule(self, node_to_move, target_node):
        """Checks if moving the node leaves a parent group empty."""
        current_parent = node_to_move.parent
        if current_parent == target_node:
            return False, None, None

        if current_parent and len(current_parent.children) <= 1:
            return (
                False,
                "Acción Inválida",
                "Regla de Orfandad:\nNo se puede dejar un Grupo sin hijos.",
            )
        return True, None, None

    def _validate_grammar_rule(self, node_to_move, target_node):
        """Checks if the target node allows the moving node as a child."""
        if target_node.name in GRAMMAR_RULES:
            allowed = GRAMMAR_RULES[target_node.name]
            if allowed and node_to_move.name not in allowed:
                return (
                    False,
                    "Violación Gramatical",
                    f"El nodo '{target_node.name}' no admite hijos de tipo '{node_to_move.name}'.",
                )
        return True, None, None

    def validate_move(self, target_item):
        target_node = target_item.node_ref
        source_node = self.node_ref

        # 1. Basic structural checks
        if (
            target_node.is_leaf
            or self._is_pos(target_node)
            or target_node in source_node.descendants
            or target_node == source_node
        ):
            return False, None, None, None

        node_to_move = source_node
        if source_node.is_leaf and source_node.parent and self._is_pos(source_node.parent):
            node_to_move = source_node.parent
        elif source_node.is_leaf:
            return False, None, None, None

        # 2. Rule checks
        ok, title, msg = self._validate_orphan_rule(node_to_move, target_node)
        if not ok:
            return False, None, title, msg

        ok, title, msg = self._validate_grammar_rule(node_to_move, target_node)
        if not ok:
            return False, None, title, msg

        return True, node_to_move, None, None

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene = self.editor_ref
        colliding = self.collidingItems()
        best_target = None
        for item in colliding:
            if isinstance(item, SyntaxNodeItem) and item != self:
                best_target = item
                break

        if scene.hovered_item and scene.hovered_item != best_target:
            scene.hovered_item.set_highlight(False)
            scene.hovered_item = None

        if best_target:
            is_valid, _, _, _ = self.validate_move(best_target)
            if is_valid:
                best_target.set_highlight(True)
                scene.hovered_item = best_target

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.editor_ref.hovered_item:
            self.editor_ref.hovered_item.set_highlight(False)
            self.editor_ref.hovered_item = None

        colliding = self.collidingItems()
        target_item = None
        for item in colliding:
            if isinstance(item, SyntaxNodeItem) and item != self:
                target_item = item
                break

        if not target_item:
            self.editor_ref.render_tree()
            return

        is_valid, node_to_move, err_title, err_msg = self.validate_move(target_item)

        if not is_valid:
            if err_title and err_msg:
                QMessageBox.warning(self.editor_ref, err_title, err_msg)
            self.editor_ref.render_tree()
            return

        if node_to_move:
            node_to_move.parent = target_item.node_ref

        self.editor_ref.commit_action()

    def _is_pos(self, node):
        if node.name in TAG_MAP["POS"]:
            return True
        if node.name in PUNCTUATION_TAGS:
            return True
        if node.name not in TAG_MAP["Phrasal"] and len(node.name) <= 5:
            return True
        return False

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        menu = QMenu()
        edit_action = menu.addAction("Editar Etiqueta ✏️")
        menu.addSeparator()
        add_group = menu.addAction("Añadir Grupo (NP, VP...) 📂")
        add_pos = menu.addAction("Añadir Categoría (N, V...) 🏷️")
        add_leaf = menu.addAction("Añadir Hoja (Texto) 🍃")
        add_punct = menu.addAction("Añadir Puntuación (.,;) ❞")
        menu.addSeparator()
        delete_action = menu.addAction("Borrar Nodo 🗑️")

        is_pos_node = self._is_pos(self.node_ref)
        is_word_node = self.node_ref.parent and self._is_pos(self.node_ref.parent)
        is_ghost = self.node_ref.name == "👻"

        # The setEnabled calls can be ignored by the type checker as addAction is reliable
        if is_ghost or is_word_node:  # type: ignore
            add_group.setEnabled(False)  # type: ignore
            add_pos.setEnabled(False)  # type: ignore
            add_leaf.setEnabled(False)  # type: ignore
            add_punct.setEnabled(False)  # type: ignore
        elif is_pos_node:  # type: ignore
            add_group.setEnabled(False)  # type: ignore
            add_pos.setEnabled(False)  # type: ignore
            add_punct.setEnabled(False)  # type: ignore
            add_leaf.setEnabled(len(self.node_ref.children) == 0)  # type: ignore
        else:  # type: ignore
            add_group.setEnabled(True)  # type: ignore
            add_pos.setEnabled(True)  # type: ignore
            add_leaf.setEnabled(False)  # type: ignore
            add_punct.setEnabled(True)  # type: ignore

        if self.error_msg:
            add_group.setEnabled(False)  # type: ignore
            add_pos.setEnabled(False)  # type: ignore
            add_leaf.setEnabled(False)  # type: ignore
            add_punct.setEnabled(False)  # type: ignore
            menu.insertSection(edit_action, "⚠️ Nodo Inválido")

        action = menu.exec(event.screenPos())

        if action == edit_action:
            self.edit_label()
        elif action == add_group:  # type: ignore
            self.add_group_child()
        elif action == add_pos:  # type: ignore
            self.add_pos_child()
        elif action == add_leaf:  # type: ignore
            self.add_leaf_child()
        elif action == add_punct:  # type: ignore
            self.add_punct_child()
        elif action == delete_action:
            self.delete_node()

    def _get_edit_options(self) -> tuple[list[str], str]:
        current_name = self.node_ref.name
        phrasal_tags = sorted(TAG_MAP["Phrasal"].keys())
        pos_tags = sorted(TAG_MAP["POS"].keys())
        punct_tags = sorted(PUNCTUATION_TAGS)

        if current_name in PUNCTUATION_TAGS:
            return punct_tags, "Editar Puntuación"
        if self._is_pos(self.node_ref):
            return pos_tags, "Editar Categoría (POS)"
        if current_name in TAG_MAP["Phrasal"]:
            return phrasal_tags, "Editar Sintagma (Phrasal)"

        return sorted(phrasal_tags + pos_tags + punct_tags), "Editar Etiqueta"

    def edit_label(self):
        current_name = self.node_ref.name
        is_leaf = self.node_ref.is_leaf

        if is_leaf:
            new_text, ok = QInputDialog.getText(
                self.editor_ref, "Editar Hoja", "Palabra:", text=current_name
            )
        else:
            items, title = self._get_edit_options()
            current_index = items.index(current_name) if current_name in items else 0
            new_text, ok = QInputDialog.getItem(
                self.editor_ref,
                title,
                LABEL_PROMPT,
                items,
                current=current_index,
                editable=True,
            )

        if ok and new_text:
            if is_leaf:
                pos_tag = self.node_ref.parent.name if self.node_ref.parent else "UNK"
                is_valid, err = validate_leaf_consistency(new_text, pos_tag)
                if not is_valid:
                    QMessageBox.warning(self.editor_ref, "Error de Validación", err)
                    return
            self.node_ref.name = new_text
            self.editor_ref.commit_action()

    def add_group_child(self):
        items = get_suggestions(self.node_ref.name, sorted(TAG_MAP["Phrasal"].keys()))
        tag, ok = QInputDialog.getItem(
            self.editor_ref,
            "Añadir Grupo",
            LABEL_PROMPT,
            items,
            current=0,
            editable=True,
        )
        if ok and tag:
            group = Node(tag, parent=self.node_ref)
            ghost_pos = Node("👻", parent=group)
            Node("👻", parent=ghost_pos)
            self.editor_ref.commit_action()

    def add_pos_child(self):
        items = get_suggestions(self.node_ref.name, sorted(TAG_MAP["POS"].keys()))
        tag, ok = QInputDialog.getItem(
            self.editor_ref,
            "Añadir Categoría",
            LABEL_PROMPT,
            items,
            current=0,
            editable=True,
        )
        if ok and tag:
            pos = Node(tag, parent=self.node_ref)
            Node("👻", parent=pos)
            self.editor_ref.commit_action()

    def add_leaf_child(self):
        text, ok = QInputDialog.getText(self.editor_ref, "Añadir Hoja", "Palabra:")
        if ok and text:
            is_valid, err = validate_leaf_consistency(text, self.node_ref.name)
            if not is_valid:
                QMessageBox.warning(self.editor_ref, "Error de Validación", err)
                return
            Node(text, parent=self.node_ref)
            self.editor_ref.commit_action()

    def add_punct_child(self):
        all_punct = sorted(set().union(*PUNCTUATION_INVENTORY.values()))
        symbol, ok = QInputDialog.getItem(
            self.editor_ref,
            "Añadir Puntuación",
            "Signo:",
            all_punct,
            current=0,
            editable=True,
        )
        if not ok or not symbol:
            return
        tag, ok = QInputDialog.getItem(
            self.editor_ref,
            "Etiqueta",
            "Tag:",  # "Tag" is more technical and appropriate here
            sorted(PUNCTUATION_TAGS),
            current=0,
            editable=True,
        )
        if ok and tag:
            punct = Node(tag, parent=self.node_ref)
            Node(symbol, parent=punct)
            self.editor_ref.commit_action()

    def delete_node(self):
        if self.node_ref.is_root:
            self.editor_ref.clear()
            return
        node_to_delete = self.node_ref
        if self.node_ref.parent and self._is_pos(self.node_ref.parent):
            node_to_delete = self.node_ref.parent
        parent = node_to_delete.parent
        if parent and len(parent.children) <= 1:
            QMessageBox.warning(
                self.editor_ref,
                "Acción Inválida",
                "Regla de Orfandad: No se puede borrar el único hijo.",
            )
            return
        node_to_delete.parent = None
        self.editor_ref.commit_action()


class SyntaxEditor(QWidget):
    """
    Reusable Qt6 Component for Visual Syntax Tree Editing.
    Can be embedded in any QMainWindow or QDialog.
    """

    treeChanged = pyqtSignal(str)  # Emits PTB string on change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)

        self.scene = QGraphicsScene()
        self.view = ZoomView(self.scene)
        self._main_layout.addWidget(self.view)

        self.root: Optional[Node] = None
        self.node_items = {}
        self.hovered_item = None

        self._calculate_subtree_width = None
        self._violations = {}

        # History
        self.history = []
        self.history_index = -1

    def load_tree(self, root: Node):
        """Loads a new tree into the editor."""
        self.root = root
        self.push_state()
        self.render_tree()

    def get_tree(self) -> Optional[Node]:
        return self.root

    def get_ptb(self) -> str:
        return to_ptb(self.root) if self.root else ""

    def clear(self):
        self.root = None
        self.scene.clear()
        self.node_items.clear()
        self.commit_action()

    def update_edges(self, moving_item: SyntaxNodeItem):
        for line, parent_item in moving_item.edges_in:
            line.setLine(
                parent_item.scenePos().x() + parent_item.rect().width() / 2,
                parent_item.scenePos().y() + parent_item.rect().height(),
                moving_item.scenePos().x() + moving_item.rect().width() / 2,
                moving_item.scenePos().y(),
            )
        for line, child_item in moving_item.edges_out:
            line.setLine(
                moving_item.scenePos().x() + moving_item.rect().width() / 2,
                moving_item.scenePos().y() + moving_item.rect().height(),
                child_item.scenePos().x() + child_item.rect().width() / 2,
                child_item.scenePos().y(),
            )

    def _draw_node_recursive(self, node, x, y, node_gap, level_height, parent_item=None):
        error = self._violations.get(node)
        item = SyntaxNodeItem(node, x, y, self, error_msg=error)
        self.scene.addItem(item)
        self.node_items[node] = item

        # pylint: disable=protected-access
        actual_x = x + (node._width - item.rect().width()) / 2
        item.setPos(actual_x, y)

        if parent_item:
            line = QGraphicsLineItem()
            line.setPen(QPen(QColor("#90A4AE"), 2))
            line.setZValue(0)
            self.scene.addItem(line)
            item.edges_in.append((line, parent_item))
            parent_item.edges_out.append((line, item))
            self.update_edges(item)

        # pylint: disable=protected-access
        total_children_width = sum(c._width for c in node.children) + node_gap * (
            len(node.children) - 1
        )
        current_x = x + (node._width / 2) - (total_children_width / 2)

        for child in node.children:
            self._draw_node_recursive(
                child, current_x, y + level_height, node_gap, level_height, item
            )
            # pylint: disable=protected-access
            current_x += child._width + node_gap

    def _render_tree_legacy(self):
        # Kept for reference if needed, but logic moved to _draw_node_recursive
        pass

    def render_tree(self):
        self.scene.clear()
        self.node_items.clear()
        if not self.root:
            return

        # pylint: disable=invalid-name
        font_metrics = QFontMetrics(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        NODE_GAP = 20
        LEVEL_HEIGHT = 100
        # pylint: enable=invalid-name

        def calculate_subtree_width(node):
            text_width = font_metrics.horizontalAdvance(node.name) + 30
            if not node.children:
                node._width = text_width  # pylint: disable=protected-access
                return text_width
            children_width = sum(calculate_subtree_width(c) for c in node.children)
            children_width += NODE_GAP * (len(node.children) - 1)
            # pylint: disable=protected-access
            node._width = max(text_width, children_width)
            return node._width

        calculate_subtree_width(self.root)
        self._violations = validate_structure(self.root)
        self._draw_node_recursive(self.root, 0, 0, NODE_GAP, LEVEL_HEIGHT)

        if self.root in self.node_items:
            self.view.centerOn(self.node_items[self.root])

    def commit_action(self):
        self.push_state()
        self.render_tree()
        self.treeChanged.emit(self.get_ptb())

    def push_state(self):
        ptb = self.get_ptb()
        if self.history and self.history_index >= 0 and self.history[self.history_index] == ptb:
            return
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]
        self.history.append(ptb)
        self.history_index += 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            # Logic to restore from PTB string would require parsing here or in app
            # For self-containment, we assume we can't parse inside unless we import parser
            # But we can emit signal requesting restore?
            # Better: SyntaxEditor should be able to parse PTB for restore.
            from core.grammatomy import from_ptb  # pylint: disable=import-outside-toplevel

            self.root = from_ptb(self.history[self.history_index])
            self.render_tree()
            self.treeChanged.emit(self.get_ptb())

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            from core.grammatomy import from_ptb  # pylint: disable=import-outside-toplevel

            self.root = from_ptb(self.history[self.history_index])
            self.render_tree()
            self.treeChanged.emit(self.get_ptb())

    def save_image(self, path):
        self.scene.clearSelection()
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        image = QImage(self.scene.sceneRect().size().toSize(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()
        image.save(path)
