export interface GrammatomyProject {
  meta: {
    version: string;
    name: string;
    created_at: string;
    updated_at: string;
  };
  source_text: string;
  units: TreeUnit[];
  notes?: string; // Project-level notes
}

export interface TreeUnit {
  id: string;
  sentence: string;
  original_ptb: string;
  current_ptb: string;
  status: 'draft' | 'validated' | 'flagged';
  metadata: Record<string, any>;
  notes?: string; // Observaciones generales del usuario
  subtrees?: SubTree[]; // Lista de subárboles/fragmentos extraídos
}

export interface SubTree {
  id: string;
  label: string;        // Etiqueta de enlace (Ej: "1", "2", "A")
  root_node_id: string; // ID del nodo ancla en el árbol padre (o donde debería ir)
  parent_subtree_id?: string | null; // ID del subárbol padre. null = Main Tree.
  ptb: string;          // Estructura interna del subárbol
  notes?: string;       // Observaciones específicas de este fragmento
  metadata?: Record<string, any>;
}

export type ProjectAction = 'new' | 'load' | 'save' | 'export';