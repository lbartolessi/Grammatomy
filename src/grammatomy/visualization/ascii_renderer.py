from anytree import RenderTree

def render_ascii_colored(root) -> str:
    """Generates HTML for a colored ASCII tree using standard CSS classes."""
    punct_tags = [".", ",", ":", ";", "!", "?", "...", "(", ")", "``", "''", "--", "-", "«", "»"]
    
    html_lines = []
    for pre, _, node in RenderTree(root):
        # Escape HTML characters in pre and node content
        safe_pre = pre.replace("<", "&lt;").replace(">", "&gt;")
        
        line_content = f"<span class='tree-connector'>{safe_pre}</span>"
        
        label = node.name
        
        # Determine style for the node label
        if hasattr(node, "word") and node.word:
            style_class = "style-punct" if label in punct_tags else "style-pos"
        else:
            style_class = "style-phrasal"
            
        line_content += f"<span class='{style_class}'>{label}</span>"
        
        if hasattr(node, "word") and node.word:
            line_content += f": <span class='style-word'>\"{node.word}\"</span>"
            
        html_lines.append(line_content)
    
    return "\n".join(html_lines)