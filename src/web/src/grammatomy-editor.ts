import { LitElement, html, PropertyValueMap } from 'lit';
import { customElement, query, state, property } from 'lit/decorators.js';
import cytoscape from 'cytoscape';
import { parsePtbToCytoscape, serializeCytoscapeToPtb } from './utils/ptb-utils';
import dagre from 'cytoscape-dagre'; // <--- Importante
cytoscape.use(dagre);                // <--- Importante

@customElement('grammatomy-editor')
export class GrammatomyEditor extends LitElement {
  @query('#cy')
  private container!: HTMLElement;

  private cy!: cytoscape.Core;

  @property({ type: String })
  ptb: string = '';

  @state()
  private selectedNode: any = null;

  @state()
  private feedbackMsg: string = '';

  @state()
  private isMoveMode: boolean = false;

  // Replaces the monolithic 'rules' object
  @state()
  private availableTags: string[] = [];
  @state()
  private validConversionTags: string[] = [];
  @state()
  private validationErrors: string[] = [];
  @state()
  private selectedNodeRule: any = {};

  private resizeObserver: ResizeObserver | null = null;

  // Unified Layout Configuration (Single Source of Truth)
  // Compact spacing ensures nodes appear larger when fitted to screen
  private readonly layoutConfig: any = {
    name: 'dagre',
    rankDir: 'TB', // Top-to-Bottom layout
    spacingFactor: 1.1,
    animate: true,
    animationDuration: 400,
    fit: true
  };

  // Switch to Light DOM to use global Tailwind styles
  override createRenderRoot() {
    return this;
  }

  override connectedCallback() {
    super.connectedCallback();
    // Force the host component to fill the parent container (body)
    this.classList.add('block', 'h-full', 'w-full');
  }

  override firstUpdated() {
    this.initGraph();
    this.fetchTags();

    // Responsive: Auto-resize Cytoscape when container changes dimensions
    if (this.container) {
      this.resizeObserver = new ResizeObserver(() => {
        this.cy?.resize();
      });
      this.resizeObserver.observe(this.container);
    }
  }

  override updated(changedProperties: PropertyValueMap<any> | Map<PropertyKey, unknown>) {
    if (changedProperties.has('ptb') && this.ptb) {
      this.loadPtb(this.ptb);
    }
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    this.resizeObserver?.disconnect();
  }

  private async fetchTags() {
    try {
      const response = await fetch('/api/validation/tags');
      if (response.ok) {
        this.availableTags = await response.json();
      }
    } catch (e) {
      console.error("Failed to load tags:", e);
    }
  }

  private initGraph() {
    this.cy = cytoscape({
      container: this.container,
      elements: [], // Start empty

      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#E69F00', // Default: Phrasal (Bang Wong Orange)
            'border-width': 2,
            'border-color': 'rgba(0,0,0,0.1)', // Subtle border
            'label': 'data(label)',
            'color': '#161616', // Text Black (on Orange)
            'shape': 'round-rectangle', // Adapts better to text than ellipse
            'width': 'label',  // Required for dynamic sizing despite deprecation warning
            'height': 'label', // Required for dynamic sizing despite deprecation warning
            'padding': '8px',  // Breathing room
            'text-valign': 'center',
            'text-halign': 'center',
            'font-family': 'Roboto Mono',
            'font-size': '12px',
            'font-weight': 'bold'
          }
        },
        {
          selector: 'node.pos',
          style: {
            'background-color': '#56B4E9', // Bang Wong Sky
            'color': '#161616' // Text Black
          }
        },
        {
          selector: 'node.leaf',
          style: {
            'background-color': '#009E73', // Bang Wong Green
            'color': '#F4F4F4', // Text Bone White
            'border-width': 0 // Leaves look cleaner without border
          }
        },
        {
          selector: 'node.punctuation',
          style: {
            'background-color': '#0072B2', // Bang Wong Blue
            'color': '#F4F4F4', // Text Bone White
            'shape': 'tag' // Distinct shape for punctuation
          }
        },
        {
          selector: 'node.error',
          style: {
            'background-color': '#D55E00', // Bang Wong Vermilion
            'color': '#F4F4F4', // Text Bone White
            'shape': 'hexagon', // Standard shape to prevent rendering crashes
            'border-width': 3,
            'border-color': '#FFFFFF'
          }
        },
        {
          selector: '.ghost',
          style: {
            'background-opacity': 0.5,
            'border-style': 'dashed',
            'background-color': '#999999',
            'color': '#161616'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': '#A0A0A0',
            'target-arrow-color': '#A0A0A0',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier' // Dagre works better with smooth curves
          }
        },
        // State Styles
        {
          selector: ':selected',
          style: {
            'border-width': 4,
            'border-color': '#D55E00', // Bang Wong Vermilion (High Contrast)
          }
        },
        // Subtree Highlight (Negative/Inverted for Deep Structure Visualization)
        {
          selector: 'node.subtree-highlight',
          style: {
            'background-color': '#161616',
            'color': '#E69F00',
            'border-color': '#E69F00'
          }
        },
        {
          selector: 'node.pos.subtree-highlight',
          style: {
            'background-color': '#161616',
            'color': '#56B4E9',
            'border-color': '#56B4E9'
          }
        },
        {
          selector: 'node.leaf.subtree-highlight',
          style: {
            'background-color': '#161616', // Carbon Black background
            'color': '#F4F4F4',             // Bone White text
            'border-width': 2,
            'border-color': '#F4F4F4'      // Bone White border for contrast
          }
        },
        {
          selector: 'node.punctuation.subtree-highlight',
          style: {
            'background-color': '#F4F4F4',
            'color': '#0072B2',
            'border-width': 2,
            'border-color': '#0072B2'
          }
        }
      ],

      layout: this.layoutConfig
    });

    // Event Handling
    this.cy.on('tap', 'node', (evt) => {
      const node = evt.target;

      if (this.isMoveMode) {
        // Execute Move Operation
        this.handleMoveOperation(node);
      } else {
        // Select Node
        this.selectNode(node);
      }
    });

    this.cy.on('tap', (evt) => {
      if (evt.target === this.cy) {
        this.clearSelection();
      }
    });

    // Auto-layout on drag release to maintain tree structure
    this.cy.on('dragfree', 'node', () => {
      this.runLayout(false); // Preserve zoom/pan on interaction
    });
  }

  private async selectNode(node: any) {
    // Visual: Highlight subtree in negative to isolate structural units
    this.cy.elements().removeClass('subtree-highlight');
    node.successors().addClass('subtree-highlight');

    this.selectedNode = node.data();
    this.validationErrors = []; // Reset errors

    // Contextual Validation for Dropdown
    const nodeElement = this.cy.$id(this.selectedNode.id);
    const isLeaf = !nodeElement.isParent() && nodeElement.outgoers().length === 0;

    // LEAF NODE POLICY:
    // In the absence of a Lexicon Hook, all leaves (words) are considered valid content.
    if (isLeaf) {
        this.validConversionTags = []; 
        // Ensure leaf is not marked as error unless it was explicitly marked
        if (!this.selectedNode.label.includes('👻') && !this.selectedNode.label.includes('ERR')) {
            nodeElement.removeClass('error');
        }
    } else {
        // STRUCTURAL NODE POLICY
        const ancestorLabels = nodeElement.predecessors('node').map(n => n.data('label'));
        const childrenLabels = nodeElement.outgoers('node').map(n => n.data('label'));
        const descendantLabels = nodeElement.successors('node').map(n => n.data('label'));

        try {
            const response = await fetch('/api/validation/check/conversion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_tag: this.selectedNode.label,
                    ancestor_tags: ancestorLabels,
                    children_tags: childrenLabels
                })
            });
            if (response.ok) {
                this.validConversionTags = await response.json();
                const isContextValid = this.validConversionTags.includes(this.selectedNode.label);
                
                if (!isContextValid) {
                    this.validationErrors.push("Context Error: Tag not allowed by parent or incompatible with children.");
                }

                // Check 2: Internal Requirements (Mandatory Descendants)
                let isStructureValid = true;
                const reqResponse = await fetch('/api/validation/check/requirements', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tag: this.selectedNode.label,
                        descendant_tags: descendantLabels
                    })
                });
                if (reqResponse.ok) {
                    const reqResult = await reqResponse.json();
                    isStructureValid = reqResult.allowed;
                    if (!isStructureValid) {
                        this.validationErrors.push(reqResult.reason);
                    }
                }

                if (!isContextValid || !isStructureValid) {
                    nodeElement.addClass('error');
                } else {
                    if (!this.selectedNode.label.includes('👻') && !this.selectedNode.label.includes('ERR')) {
                        nodeElement.removeClass('error');
                    }
                }
            }
        } catch (e) {
            console.error("Failed to fetch conversion options", e);
            this.validConversionTags = [];
        }
    }
    
    // Fetch specific rules for this node (for Inspector info and local checks like mandatory children)
    try {
        const encodedLabel = encodeURIComponent(this.selectedNode.label);
        console.log(`Fetching rules for label: '${this.selectedNode.label}' -> URL: /api/validation/rules/`);
        const response = await fetch(`/api/validation/rules/`);

        if (response.ok) {
            this.selectedNodeRule = await response.json();
            console.log(`Rules for ${this.selectedNode.label}:`, this.selectedNodeRule);
        } else {
            this.selectedNodeRule = {};
        }
    } catch (e) {
        console.error("Failed to fetch node rules", e);
        this.selectedNodeRule = {};
    }

    this.isMoveMode = false; // Cancel move mode if selecting
    this.feedbackMsg = '';
    // Force update because Cytoscape internal state isn't tracked by Lit
    this.requestUpdate();
  }

  private clearSelection() {
    this.cy.elements().removeClass('subtree-highlight');
    this.selectedNode = null;
    this.selectedNodeRule = {};
    this.validConversionTags = [];
    this.validationErrors = [];
    this.isMoveMode = false;
    this.feedbackMsg = '';
    this.requestUpdate();
  }

  private handleLabelChange(e: Event) {
    const newLabel = (e.target as HTMLSelectElement).value;
    if (!this.selectedNode || newLabel === this.selectedNode.label) return;

    const node = this.cy.$id(this.selectedNode.id);
    node.data('label', newLabel);

    // Update the state for the inspector to re-render with the new label
    this.selectedNode = node.data();

    // Re-classify to apply new styles if the node type changed
    this.classifyNodes();

    this.feedbackMsg = `Node label changed to ''.`;
    // No layout change needed, just a UI update for the inspector
    this.requestUpdate();
  }

  private async handleMoveOperation(targetParent: any) {
    if (!this.selectedNode) return;
    
    // FIX: Revert selection change caused by the click on target
    // Ensure the visual selection stays on the source node
    this.cy.nodes().unselect();
    this.cy.$id(this.selectedNode.id).select();

    let nodeToMove = this.cy.$id(this.selectedNode.id);
    const newParent = targetParent;

    // 0. Atomic Unit Handling: Treat POS+Leaf or Punctuation+Sign as a single unit.
    // If selecting a leaf that belongs to a POS/Punctuation parent, move the parent.
    if (nodeToMove.outdegree(false) === 0) {
        const parent = nodeToMove.incomers('edge').source();
        if (parent.length > 0 && (parent.hasClass('pos') || parent.hasClass('punctuation'))) {
             nodeToMove = parent;
        }
    }

    // 0.0 ROOT Protection: ROOT cannot be moved.
    // It has no parent to detach from, so moving it would create a cycle or duplicate root.
    if (nodeToMove.data('label') === 'ROOT' || nodeToMove.incomers().length === 0) {
         this.feedbackMsg = "Operation cancelled: Cannot move the ROOT node.";
         this.isMoveMode = false;
         this.requestUpdate();
         return;
    }

    // 0.1 Orphan Prevention (Cannot leave old parent empty)
    const oldParent = nodeToMove.incomers('edge').source();
    if (oldParent.length > 0 && oldParent.outgoers('node').length === 1) {
         this.feedbackMsg = "Operation cancelled: Cannot move the only child (Parent would be empty).";
         this.isMoveMode = false;
         this.requestUpdate();
         return;
    }

    // 1. Integrity Checks (Topology)
    if (nodeToMove.id() === newParent.id()) {
        this.feedbackMsg = "Operation cancelled: Cannot move a node to itself.";
        this.isMoveMode = false;
        this.requestUpdate();
        return;
    }

    if (nodeToMove.successors().contains(newParent)) {
        this.feedbackMsg = "Operation cancelled: Cannot move a node into its own descendant (Cycle detected).";
        this.isMoveMode = false;
        this.requestUpdate();
        return;
    }

    // 2. Rule Validation (Metasyntax)
    const parentLabel = newParent.data('label');
    const childLabel = nodeToMove.data('label');
    
    // Server-side validation
    try {
        const response = await fetch('/api/validation/check/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ parent_tag: parentLabel, child_tag: childLabel })
        });
        const result = await response.json();
        if (!result.allowed) {
            this.feedbackMsg = `Validation Error: ${result.reason}`;
            this.isMoveMode = false;
            this.requestUpdate();
            return;
        }
    } catch (e) {
        console.error("Validation check failed", e);
        this.feedbackMsg = "Server error during validation.";
        return;
    }

    // Block moving into POS, Leaf, or Punctuation (Terminals/Atomic units)
    if (newParent.hasClass('pos') || newParent.hasClass('leaf') || newParent.hasClass('punctuation')) {
        this.feedbackMsg = `Validation Error: Cannot move nodes into '' (Terminal/POS).`;
        this.isMoveMode = false;
        this.requestUpdate();
        return;
    }
    
    // 3. Execution (Graph Mutation)
    this.cy.batch(() => {
        nodeToMove.incomers('edge').remove(); // Detach from old parent
        this.cy.add({ group: 'edges', data: { source: newParent.id(), target: nodeToMove.id() } }); // Attach to new
    });

    this.feedbackMsg = `Success: Moved '' to ''.`;
    this.isMoveMode = false;
    this.classifyNodes(); // Re-calculate styles (e.g. parent might become leaf)
    
    // Re-apply highlight to the moved subtree (classifyNodes wipes classes)
    if (this.selectedNode) {
       this.cy.$id(this.selectedNode.id).successors().addClass('subtree-highlight');
    }

    this.runLayout(false); // Update layout preserving zoom
    this.requestUpdate();
  }

  // --- Actions ---

  private startMoveMode() {
    this.isMoveMode = true;
    this.feedbackMsg = "Select the new parent node...";
  }

  private handleAddChild() {
    if (!this.selectedNode) return;

    const parentId = this.selectedNode.id;
    const parentLabel = this.selectedNode.label;
    const allowedChildren = this.selectedNodeRule.allowed || [];

    // Heuristic: Does this node allow POS tags directly?
    // We check if any allowed child is a known POS or if the list is empty (leaves only)
    // For this implementation, we assume if it allows 'NOUN', 'VERB', etc., it allows POS.
    // A simpler check: If it allows children that are NOT in the rules keys (terminals) or are standard POS.
    const commonPosTags = ['NOUN', 'VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'NUM', 'CONJ', 'PRT', 'n', 'v', 'a', 'd', 'p', 'r', 'c'];
    const admitsPosDirectly = allowedChildren.some((tag: string) => commonPosTags.includes(tag) || tag.toUpperCase() === tag);

    this.cy.batch(() => {
        const ghostWordId = `ghost_word_${Date.now()}`;
        const ghostPosId = `ghost_pos_${Date.now()}`;
        
        // Create the Leaf (Word) - Always needed
        this.cy.add({ group: 'nodes', data: { id: ghostWordId, label: '👻Word' }, classes: 'leaf ghost' });

        if (admitsPosDirectly) {
            // Scenario A: Parent -> 👻POS -> 👻Word
            this.cy.add({ group: 'nodes', data: { id: ghostPosId, label: '👻POS' }, classes: 'pos ghost' });
            this.cy.add({ group: 'edges', data: { source: parentId, target: ghostPosId } });
            this.cy.add({ group: 'edges', data: { source: ghostPosId, target: ghostWordId } });
        } else {
            // Scenario B: Parent -> 👻Node -> 👻POS -> 👻Word
            const ghostNodeId = `ghost_node_${Date.now()}`;
            this.cy.add({ group: 'nodes', data: { id: ghostNodeId, label: '👻Node' }, classes: 'ghost' });
            this.cy.add({ group: 'nodes', data: { id: ghostPosId, label: '👻POS' }, classes: 'pos ghost' });
            
            this.cy.add({ group: 'edges', data: { source: parentId, target: ghostNodeId } });
            this.cy.add({ group: 'edges', data: { source: ghostNodeId, target: ghostPosId } });
            this.cy.add({ group: 'edges', data: { source: ghostPosId, target: ghostWordId } });
        }
    });

    this.feedbackMsg = "Ghost structure added. Please edit labels.";
    this.classifyNodes();
    this.runLayout(false);
    this.requestUpdate();
  }

  private async deleteSelected() {
    if (!this.selectedNode) return;
    
    const nodeElement = this.cy.$id(this.selectedNode.id);
    const isLeaf = nodeElement.outgoers().length === 0;

    if (isLeaf || nodeElement.hasClass('pos') || nodeElement.hasClass('punctuation')) {
        // 1:1 Relationship: Deleting a leaf or POS implies deleting the POS unit
        // If leaf, target parent. If POS, target self.
        const target = isLeaf ? nodeElement.incomers('edge').source() : nodeElement;
        
        if (target.length > 0) {
            target.successors().remove(); // Remove children (Leaf)
            target.remove(); // Remove POS
            this.feedbackMsg = "POS Unit (Category + Word) deleted.";
        }
    } else {
        // Phrasal Node Deletion (Recursive / Subtree)
        const incoming = nodeElement.incomers('edge');
        
        // 1. Mandatory Child Check (Parent Rules)
        if (incoming.length > 0) {
            const parent = incoming.source();
            const parentLabel = parent.data('label');
            const childLabel = this.selectedNode.label;
            
            // Get siblings EXCLUDING the current node to check if any other valid child remains
            const siblingTags = parent.outgoers('node')
                .filter(n => n.id() !== this.selectedNode.id)
                .map(n => n.data('label'));

            try {
                const response = await fetch('/api/validation/check/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ parent_tag: parentLabel, child_tag: childLabel, sibling_tags: siblingTags })
                });
                const result = await response.json();
                if (!result.allowed) {
                    this.feedbackMsg = `Validation Error: ${result.reason}`;
                    this.requestUpdate();
                    return;
                }
            } catch (e) {
                console.error("Validation check failed", e);
                this.feedbackMsg = "Server error during validation.";
                return;
            }
        }

        // 2. Execution: Delete the node and its entire subtree ("Kill the family")
        this.cy.batch(() => {
            nodeElement.successors().remove(); // Remove all descendants
            nodeElement.remove();              // Remove the head
        });
        
        this.feedbackMsg = "Subtree deleted.";
    }

    this.clearSelection();
    this.runLayout(false);
  }

  private runLayout(fit: boolean = true) {
    if (!this.cy) return;

    this.cy.resize();
    // Merge config with dynamic fit option
    this.cy.layout({ ...this.layoutConfig, fit: fit }).run();
  }

  public getCurrentPtb(): string {
    if (!this.cy) return '';
    return serializeCytoscapeToPtb(this.cy);
  }

  private renderValidationIssues(errors: string[]) {
    if (errors.length === 0) return html``;
    return html`
      <div class="bg-red-50 border-l-2 border-red-500 p-2 rounded-r mb-4 text-xs">
          <div class="font-bold text-red-700 mb-1 flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">error</span> Validation Issues
          </div>
          <ul class="list-disc list-inside text-red-600 space-y-1 leading-tight">
              ${errors.map(e => html`<li></li>`)}
          </ul>
      </div>
    `;
  }

  private renderInspector() {
    if (!this.selectedNode) {
      return html`
        <div class="h-full flex flex-col items-center justify-center text-gray-400 p-6 text-center">
          <span class="material-symbols-outlined text-4xl mb-2">touch_app</span>
          <p class="text-sm">Select a node to view properties and actions.</p>
        </div>
      `;
    }

    const nodeElement = this.cy.$id(this.selectedNode.id);
    const isLeaf = !nodeElement.isParent() && nodeElement.outgoers().length === 0;
    const isPos = nodeElement.hasClass('pos');
    const isPunctuation = nodeElement.hasClass('punctuation');
    const canAddChild = !isLeaf && !isPos && !isPunctuation;

    // TODO: Check if it's a "Ghost" leaf based on data
    const isGhost = this.selectedNode.label.includes('👻'); 
    const canEditLabel = !isLeaf || isGhost;
    const isGhostLeaf = isLeaf && isGhost;

    // Use contextually valid tags instead of all tags
    const validTags = this.validConversionTags;
    // Leaves are valid by definition (content), unless explicitly marked as error.
    // Structural nodes must be in the validTags list.
    const isCurrentTagValid = isLeaf ? true : validTags.includes(this.selectedNode.label);
    const isDropdownDisabled = validTags.length === 0;

    // Determine Header Style based on Node Type & Validity
    let headerBg = '#E69F00'; // Default: Phrasal (Orange)
    let headerText = '#161616';
    let typeLabel = 'Phrasal Node';

    if (!isCurrentTagValid || nodeElement.hasClass('error')) {
        headerBg = '#D55E00'; // Error (Vermilion)
        headerText = '#F4F4F4';
        typeLabel = 'Invalid / Error';
    } else if (isPunctuation) {
        headerBg = '#0072B2'; // Punctuation (Blue)
        headerText = '#F4F4F4';
        typeLabel = 'Punctuation';
    } else if (isLeaf) {
        headerBg = '#009E73'; // Leaf (Green)
        headerText = '#F4F4F4';
        typeLabel = 'Terminal (Leaf)';
    } else if (isPos) {
        headerBg = '#56B4E9'; // POS (Sky)
        headerText = '#161616';
        typeLabel = 'Syntactic Category';
    }

    // Check for "Only Child" status (Prevention of Empty Parents)
    // Logic updated for 1:1 POS-Leaf relationship:
    // If it's a leaf, we check if its PARENT (POS) is an only child of the Grandparent.
    let nodeToCheck = nodeElement;
    if (isLeaf) {
        const parent = nodeElement.incomers('edge').source();
        if (parent.length > 0) nodeToCheck = parent;
    }

    const incomingEdges = nodeToCheck.incomers('edge');
    let isOnlyChild = false;
    if (incomingEdges.length > 0) {
        const parent = incomingEdges.source();
        if (parent.outgoers('node').length === 1) {
            isOnlyChild = true;
        }
    }

    return html`
      <div class="flex flex-col gap-6">
        
        <!-- Node Identity Header -->
        <div class="rounded-lg p-4 shadow-sm flex flex-col items-center justify-center gap-2 transition-colors duration-300" style="background-color: ${headerBg}; color: ${headerText};">
            <div class="text-[10px] uppercase tracking-widest opacity-80 font-bold">${typeLabel}</div>
            <div class="text-2xl font-mono font-bold tracking-tight">${this.selectedNode.label}</div>
        </div>

        <!-- Header / Identity -->
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
            Edit Label
          </label>
          
          ${this.renderEditControl(canEditLabel, isGhostLeaf, isCurrentTagValid, isDropdownDisabled, validTags)}
        </div>

        ${this.renderValidationIssues(this.validationErrors)}

        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Actions</label>
          
          <div class="grid grid-cols-4 gap-2 mb-2">
            <button 
              @click=${this.handleAddChild}
              class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-ibm-blue disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:text-gray-400" 
              title="${canAddChild ? 'Add Child' : 'Cannot add child to Terminal/POS'}"
              ?disabled=${!canAddChild}
            >
              <span class="material-symbols-outlined">add_circle</span>
            </button>
            <button 
              @click=${this.deleteSelected} 
              ?disabled=
              class="p-2 bg-white border border-gray-300 rounded hover:bg-red-50 text-red-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:text-gray-400" 
              title="${isOnlyChild ? 'Cannot delete: Parent would be empty' : 'Delete Node'}"
            >
              <span class="material-symbols-outlined">delete</span>
            </button>
            <button class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-600" title="Move Left">
              <span class="material-symbols-outlined">arrow_back</span>
            </button>
            <button class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-600" title="Move Right">
              <span class="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>

          <button 
            @click=${this.startMoveMode}
            class="w-full py-2 px-3 rounded flex items-center justify-center gap-2 transition-colors ${this.isMoveMode ? 'bg-ibm-orange text-white animate-pulse' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'}"
          >
            <span class="material-symbols-outlined text-sm">open_with</span>
            ${this.isMoveMode ? 'Click Target Parent...' : 'Move Subtree'}
          </button>
        </div>

        <!-- Feedback Area -->
        <div class="mt-auto min-h-[60px] p-3 rounded ${this.feedbackMsg ? 'bg-blue-50 border border-blue-100 text-ibm-blue' : 'bg-transparent'} text-xs transition-all">
          ${this.feedbackMsg}
        </div>

      </div>
    `;
  }

  private renderEditControl(canEditLabel: boolean, isGhostLeaf: boolean, isCurrentTagValid: boolean, isDropdownDisabled: boolean, validTags: string[]) {
    if (!canEditLabel) {
      return html`
        <div class="w-full p-2 bg-gray-100 border border-gray-200 rounded text-gray-500 font-mono italic text-center">
          Immutable
        </div>
      `;
    }

    if (isGhostLeaf) {
      return html`
        <input 
          type="text" 
          class="w-full p-2 bg-white border border-gray-300 rounded shadow-sm focus:border-ibm-blue focus:ring-1 focus:ring-ibm-blue outline-none text-base-dark font-mono font-bold"
          .value=${this.selectedNode.label}
          @change=${this.handleLabelChange}
          placeholder="Type word here..."
        />
      `;
    }

    return html`
      <select 
        class="w-full p-2 bg-white border ${isCurrentTagValid ? 'border-gray-300' : 'border-red-500 bg-red-50'} rounded shadow-sm focus:border-ibm-blue focus:ring-1 focus:ring-ibm-blue outline-none text-base-dark font-mono font-bold disabled:opacity-50 disabled:cursor-not-allowed"
        @change=${this.handleLabelChange}
        ?disabled=${isDropdownDisabled}
      >
        ${validTags.map(tag => html`
          <option value="${tag}" ?selected=${tag === this.selectedNode.label}>
            ${tag}
          </option>
        `)}
      </select>
    `;
  }

  private loadPtb(ptbString: string) {
    if (!this.cy) return;
    
    const elements = parsePtbToCytoscape(ptbString);

    this.cy.elements().remove();
    this.cy.add(elements);
    
    this.classifyNodes();
    this.runLayout(true); // Fit to screen on new tree load
  }

  private classifyNodes() {
    this.cy.batch(() => {
      this.cy.nodes().forEach(node => {
        const isLeaf = node.outdegree(false) === 0;
        const label = node.data('label');
        
        // Reset classes
        node.classes([]);

        // Check for Error/Ghost first
        if (label.includes('👻') || label.includes('ERR')) {
            node.addClass('error');
            if (label.includes('👻')) node.addClass('ghost');
            return;
        }

        // Punctuation Detection (Regex for common punctuation marks or tags like fp, fc)
        const isPunctuation = /^[\.,:;'"\(\)\[\]\{}\-–—\?!]+$/.test(label) || 
                              ['fp','fc','fg','fz','fs','fd'].includes(label.toLowerCase());

        if (isPunctuation) {
            node.addClass('punctuation');
            return;
        }

        if (isLeaf) {
            node.addClass('leaf');
        } else {
            // If all children are leaves, it's likely a POS tag.
            // Use outgoers().nodes() because children() is for compound nodes.
            const childrenAreLeaves = node.outgoers().nodes().every(child => child.outdegree(false) === 0);
            if (childrenAreLeaves) {
                node.addClass('pos');
            }
            // Otherwise, it remains default (Phrasal/Grouping)
        }
      });
    });
  }

  override render() {
    return html`
      <div class="flex flex-col h-full w-full bg-base-light rounded-lg overflow-hidden border border-gray-200 shadow-sm">
        
        <!-- Toolbar -->
        <div class="flex items-center gap-2 px-4 py-2 border-b border-gray-200 bg-base-light-dim text-sm">
            <div class="flex gap-1">
                <button class="p-1.5 text-gray-600 hover:text-ibm-blue hover:bg-gray-200 rounded transition-colors" title="Undo">
                    <span class="material-symbols-outlined text-[18px]">undo</span>
                </button>
                <button class="p-1.5 text-gray-600 hover:text-ibm-blue hover:bg-gray-200 rounded transition-colors" title="Redo">
                    <span class="material-symbols-outlined text-[18px]">redo</span>
                </button>
            </div>
            <div class="w-px h-4 bg-gray-300 mx-1"></div>
            <div class="flex gap-1">
                <button class="p-1.5 text-gray-600 hover:text-ibm-blue hover:bg-gray-200 rounded transition-colors" title="Fit View">
                    <span class="material-symbols-outlined text-[18px]">fit_screen</span>
                </button>
                <button class="p-1.5 text-gray-600 hover:text-ibm-blue hover:bg-gray-200 rounded transition-colors" title="Reset Layout">
                    <span class="material-symbols-outlined text-[18px]">account_tree</span>
                </button>
            </div>
        </div>

        <!-- Workspace -->
        <div class="flex flex-1 overflow-hidden relative min-h-0">
            <!-- Canvas Wrapper: Ensures #cy fills space absolutely without collapsing -->
            <div class="flex-1 relative min-w-0">
                <div id="cy" class="absolute inset-0 bg-base-light"></div>
            </div>

            <!-- Inspector (Right Sidebar) -->
            <div class="w-80 bg-base-light-dim border-l border-gray-200 p-4 overflow-y-auto hidden md:block shadow-inner">
                ${this.renderInspector()}
            </div>
        </div>
      </div>
    `;
  }
}
