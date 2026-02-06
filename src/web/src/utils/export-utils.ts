import { parsePtbToCytoscape } from "./ptb-utils";

/**
 * Converts a PTB string into a LaTeX Forest code snippet.
 * Example: (S (NP John)) -> \begin{forest} [S [NP [John]]] \end{forest}
 */
export function ptbToLatexForest(ptb: string): string {
    // We reuse the parser logic to traverse the structure
    // But since we don't have the graph object here, we parse the string again
    // or we could implement a simple recursive string parser.
    
    // Simple recursive parser for PTB to Forest
    // Tokenizer from ptb-utils
    const tokens = ptb
        .replace(/\(/g, ' ( ')
        .replace(/\)/g, ' ) ')
        .trim()
        .split(/\s+/)
        .filter(t => t.length > 0);

    let output = "";
    
    const process = (index: number): number => {
        if (index >= tokens.length) return index;
        
        const token = tokens[index];
        
        if (token === '(') {
            const label = tokens[index + 1];
            output += `[${label} `;
            
            let current = index + 2;
            while (current < tokens.length && tokens[current] !== ')') {
                current = process(current);
            }
            output += "]";
            return current + 1; // Skip ')'
        } else if (token === ')') {
            return index + 1;
        } else {
            // Leaf word
            output += `[${token}] `;
            return index + 1;
        }
    };

    process(0);
    
    return `\\begin{forest}\n${output}\n\\end{forest}`;
}

export function downloadFile(filename: string, content: string, mimeType: string) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}