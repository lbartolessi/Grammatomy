/**
 * PTB Utilities for Client-Side Parsing/Serialization.
 * Converts between S-expressions and Cytoscape Elements.
 */

export interface GraphNode {
    data: {
        id: string;
        label: string;
        parent?: string;
        index?: number; // Added index support
    };
}

export interface GraphEdge {
    data: {
        source: string;
        target: string;
    };
}

export function parsePtbToCytoscape(ptb: string): (GraphNode | GraphEdge)[] {
    const elements: (GraphNode | GraphEdge)[] = [];
    let idCounter = 0;

    // Tokenize: Add spaces around parens to split easily
    const tokens = ptb
        .replace(/\(/g, ' ( ')
        .replace(/\)/g, ' ) ')
        .trim()
        .split(/\s+/)
        .filter(t => t.length > 0);

    let currentParentId: string | null = null;
    const stack: string[] = []; // Stack of parent IDs

    let i = 0;
    while (i < tokens.length) {
        const token = tokens[i];

        if (token === '(') {
            // Start of a new node
            const label = tokens[i + 1]; // Next token is the label
            const nodeId = `n${idCounter++}`;
            
            // Create Node
            elements.push({ data: { id: nodeId, label: label } });

            // Create Edge from parent
            if (currentParentId) {
                elements.push({ data: { source: currentParentId, target: nodeId } });
            }

            // Push current parent to stack and descend
            if (currentParentId) stack.push(currentParentId);
            currentParentId = nodeId;
            
            i += 2; // Skip '(' and label
        } else if (token === ')') {
            // End of current node, pop back up
            currentParentId = stack.pop() || null;
            i++;
        } else {
            // It's a leaf word (e.g. "The") inside a node like (DT The)
            const wordId = `n${idCounter++}`;
            elements.push({ data: { id: wordId, label: token } });
            if (currentParentId) {
                elements.push({ data: { source: currentParentId, target: wordId } });
            }
            i++;
        }
    }

    return elements;
}

export function serializeCytoscapeToPtb(cy: any): string {
    // Find Root (node with no incoming edges)
    const roots = cy.nodes().filter((n: any) => n.incomers().length === 0);
    if (roots.length === 0) return "";

    // Sort roots by index if multiple (forest)
    roots.sort((a: any, b: any) => (a.data('index') || 0) - (b.data('index') || 0));

    const traverse = (node: any): string => {
        // CRITICAL: Sort children by index to preserve structural order
        const children = node.outgoers().nodes().sort((a: any, b: any) => {
            return (a.data('index') || 0) - (b.data('index') || 0);
        });

        const label = node.data('label');
        
        if (children.length === 0) {
            return label; // Leaf word
        }
        
        const childrenStr = children.map((child: any) => traverse(child)).join(' ');
        return `(${label} ${childrenStr})`;
    };

    return traverse(roots[0]);
}

export function serializeNodeToPtb(node: any): string {
    const traverse = (n: any): string => {
        const children = n.outgoers().nodes().sort((a: any, b: any) => {
            return (a.data('index') || 0) - (b.data('index') || 0);
        });

        const label = n.data('label');
        if (children.length === 0) return label;
        
        const childrenStr = children.map((child: any) => traverse(child)).join(' ');
        return `(${label} ${childrenStr})`;
    };
    return traverse(node);
}
