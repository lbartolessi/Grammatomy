/**
 * PTB Utilities for Client-Side Parsing/Serialization.
 * Converts between S-expressions and Cytoscape Elements.
 */

export interface GraphNode {
    data: {
        id: string;
        label: string;
        parent?: string;
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
    "grup.nom", "sn", "grup.verb", "grup.a", "s.a", "grup.adv", "sadv", "sp", "prep", "morfema.pronominal", "morfema.verbal", "relatiu", "neg", "gerundi", "participi", "infinitiu", "spec",
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
                elements.push({ data: { id: nodeId, label: label } });

                if (currentParentId) {
                    elements.push({ data: { source: currentParentId, target: nodeId } });
                }

                if (currentParentId) stack.push(currentParentId);
                currentParentId = nodeId;
                i += 2; // Skip '(' and label
            } else {
                // Leaf Node wrapped in parens (e.g. (gato))
                if (currentParentId) {
                    // Check for duplicates
                    const hasChild = elements.some(el => 'source' in el.data && el.data.source === currentParentId);
                    if (!hasChild) {
                        const wordId = `n${idCounter++}`;
                        elements.push({ data: { id: wordId, label: label } });
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
            }
            i++;
        } else {
            // It's a leaf word (e.g. "The") inside a node like (DT The)
            
            if (currentParentId) {
                // FINAL FIX: A POS node can only have ONE child (the terminal word).
                // Any subsequent tokens before the ')' are ignored.
                const hasChild = elements.some(el => 'source' in el.data && el.data.source === currentParentId);
                if (!hasChild) {
                    const wordId = `n${idCounter++}`;
                    elements.push({ data: { id: wordId, label: token } });
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

    const traverse = (node: any): string => {
        const children = node.outgoers().nodes();
        const label = node.data('label');
        
        if (children.length === 0) {
            return label; // Leaf word
        }
        
        const childrenStr = children.map((child: any) => traverse(child)).join(' ');
        return `(${label} ${childrenStr})`;
    };

    return traverse(roots[0]);
}