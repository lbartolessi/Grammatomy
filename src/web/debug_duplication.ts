// Run this with: npx ts-node src/web/debug_duplication.ts

import { parsePtbToCytoscape } from './src/utils/ptb-utils';

const testCases = [
    "(PRON Estas)",
    "(PRON Estas Estas)",
    "(PRON (Estas))",
    "(ROOT (sentence (grup.nom (grup.nom (PRON Estas) (S (relatiu (PRON que)) (sn (grup.nom (PRON me))) (grup.verb (VERB dictó)))) (PUNCT ,))))"
];

function runTest() {
    console.log("Running frontend duplication diagnostics...");

    for (const ptb of testCases) {
        console.log(`\n--- Testing: ${ptb} ---`);
        try {
            const elements = parsePtbToCytoscape(ptb);
            printTree(elements);
        } catch (e) {
            console.error("Error parsing:", e);
        }
    }
}

function printTree(elements: any[]) {
    const nodeMap = new Map<string, any>();
    const edges: any[] = [];

    // Separate nodes and edges
    elements.forEach(el => {
        // Cytoscape elements can be { data: { source, target } } for edges
        if (el.data.source && el.data.target) {
            edges.push(el.data);
        } else {
            nodeMap.set(el.data.id, { ...el.data, children: [] });
        }
    });

    // Build hierarchy
    edges.forEach(edge => {
        const parent = nodeMap.get(edge.source);
        const child = nodeMap.get(edge.target);
        if (parent && child) {
            parent.children.push(child);
        }
    });

    // Find roots (nodes with no incoming edges)
    const roots = Array.from(nodeMap.values()).filter(n => 
        !edges.some(e => e.target === n.id)
    );

    // Render
    renderTree(roots);
}

function renderTree(nodes: any[]) {
    const print = (node: any, prefix: string, isTail: boolean) => {
        console.log(`${prefix}${isTail ? "└── " : "├── "}${node.label} (children=${node.children.length})`);
        for (let i = 0; i < node.children.length - 1; i++) {
            print(node.children[i], prefix + (isTail ? "    " : "│   "), false);
        }
        if (node.children.length > 0) {
            print(node.children[node.children.length - 1], prefix + (isTail ? "    " : "│   "), true);
        }
    };

    nodes.forEach(root => {
        console.log(`${root.label} (children=${root.children.length})`);
        if (root.children.length > 0) {
            // Print children
            for (let i = 0; i < root.children.length - 1; i++) {
                print(root.children[i], "", false);
            }
            print(root.children[root.children.length - 1], "", true);
        }
    });
}

runTest();