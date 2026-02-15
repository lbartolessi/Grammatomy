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

const RESERVED_TAGS = new Set([
    // Sentence / Clause
    "ROOT", "S", "SQ", "SINV", "SBAR", "FRAG", "INC", "CONJP", "INTJ", "LST", "NAC", "NX", "PRN", "PRT", "QP", "RRC", "UCP", "WHADJP", "WHAVP", "WHNP", "WHPP", "X", "sentence",
    // AnCora Groups
    "grup.nom", "sn", "grup.verb", "grup.a", "s.a", "grup.adv", "sadv", "sp", "prep", "morfema.pronominal", "morfema.verbal", "relatiu", "neg", "gerundi", "participi", "infinitiu", "spec", "conj", "coord", "inc", "interjeccio",
    // Universal Dependencies POS
    "NOUN", "PROPN", "VERB", "AUX", "ADJ", "DET", "PRON", "ADV", "ADP", "CCONJ", "SCONJ", "NUM", "PART", "SYM", "INTJ", "PUNCT",
    // Legacy AnCora POS
    "n", "v", "a", "d", "r", "p", "c", "s", "w", "z", "f", "i",
    "nc", "np", "aq", "rg", "rn",
    // Punctuation & Symbols
    ".", ",", ":", ";", "!", "?", "...", "-", "–", "—", "(", ")", "[", "]", "{", "}", "\"", "'", "«", "»", "¿", "¡",
    "``", "''", "-LRB-", "-RRB-", "$", "#",
    "fp", "fc", "fs", "fd", "fe", "fg", "fz", "fx", "ft", "fat", "fpt", "fit", "fia",
    // Link Nodes
    "LINK"
]);

export function parsePtbToCytoscape(ptb: string): (GraphNode | GraphEdge)[] {
    const elements: (GraphNode | GraphEdge)[] = [];
    let idCounter = 0;
    const childCounts = new Map<string, number>();

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
            const label = tokens[i + 1]; // Next token is the label
            
            const isReserved = RESERVED_TAGS.has(label) || label.startsWith('LINK-');

            if (isReserved) {
                // Structural Node (e.g. (NP ...))
                const nodeId = `n${idCounter++}`;
                let idx = 0;

                if (currentParentId) {
                    idx = childCounts.get(currentParentId) || 0;
                    childCounts.set(currentParentId, idx + 1);
                    elements.push({ data: { source: currentParentId, target: nodeId } });
                }

                elements.push({ data: { id: nodeId, label: label, index: idx } });

                if (currentParentId) stack.push(currentParentId);
                currentParentId = nodeId;
                i += 2; // Skip '(' and label
            } else {
                // Leaf Node wrapped in parens (e.g. (gato))
                if (currentParentId) {
                    // A POS node can only have ONE child.
                    const hasChild = elements.some(el => 'source' in el.data && el.data.source === currentParentId);
                    if (!hasChild) {
                        const wordId = `n${idCounter++}`;
                        const idx = childCounts.get(currentParentId) || 0;
                        childCounts.set(currentParentId, idx + 1);
                        elements.push({ data: { id: wordId, label: label, index: idx } });
                        elements.push({ data: { source: currentParentId, target: wordId } });
                    }
                }
                i += 2; // Skip '(' and label
                if (tokens[i] === ')') i++; // Consume closing ')'
            }
        } else if (token === ')') {
            // End of current node, pop back up
            if (stack.length > 0) {
                currentParentId = stack.pop() || null;
            } else {
                currentParentId = null; // Reached the end of the root
            }
            i++;
        } else {
            // It's a leaf word (e.g. "The") inside a node like (DT The)
            if (currentParentId) {
                // A POS node can only have ONE child (the terminal word).
                const hasChild = elements.some(el => 'source' in el.data && el.data.source === currentParentId);
                if (!hasChild) {
                    const wordId = `n${idCounter++}`;
                    const idx = childCounts.get(currentParentId) || 0;
                    childCounts.set(currentParentId, idx + 1);
                    elements.push({ data: { id: wordId, label: token, index: idx } });
                    elements.push({ data: { source: currentParentId, target: wordId } });
                }
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
            // This is a leaf. If its parent is a POS tag, it's a terminal word.
            // Otherwise, it could be an empty phrasal node.
            return label;
        }
        
        const childrenStr = children.map((child: any) => traverse(child)).join(' ');
        return `(${label} ${childrenStr})`;
    };

    return roots.map((r: any) => traverse(r)).join('\n');
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