import { LitElement, html, PropertyValueMap } from 'lit';
import { customElement, query, state, property } from 'lit/decorators.js';
import cytoscape from 'cytoscape';
import { parsePtbToCytoscape, serializeCytoscapeToPtb } from './utils/ptb-utils';

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

  @state()
  private rules: any = {};

  private resizeObserver: ResizeObserver | null = null;

  // Switch to Light DOM to use global Tailwind styles
  override createRenderRoot() {
    return this;
  }

  override firstUpdated() {
    this.initGraph();
    this.fetchRules();

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

  private async fetchRules() {
    try {
      const response = await fetch('/api/rules');
      if (response.ok) {
        this.rules = await response.json();
        console.log("Rules loaded:", Object.keys(this.rules).length);
      }
    } catch (e) {
      console.error("Failed to load validation rules:", e);
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
            'background-color': '#56B4E9', // gram-primary
            'label': 'data(label)',
            'color': '#ffffff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-family': 'monospace',
            'font-weight': 'bold',
            'border-width': 0
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        },
        // State Styles
        {
          selector: ':selected',
          style: {
            'border-width': 4,
            'border-color': '#FE6100', // IBM Orange
            'background-color': '#785EF0' // IBM Purple
          }
        },
        {
          selector: '.ghost',
          style: {
            'background-opacity': 0.5,
            'border-style': 'dashed'
          }
        }
      ],

      layout: {
        name: 'breadthfirst', // Jerarquía simple por defecto
        directed: true,
        padding: 30,
        spacingFactor: 1.5
      }
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
      this.runLayout();
    });
  }

  private selectNode(node: any) {
    this.selectedNode = node.data();
    this.isMoveMode = false; // Cancel move mode if selecting
    this.feedbackMsg = '';
    // Force update because Cytoscape internal state isn't tracked by Lit
    this.requestUpdate();
  }

  private clearSelection() {
    this.selectedNode = null;
    this.isMoveMode = false;
    this.feedbackMsg = '';
    this.requestUpdate();
  }

  private handleMoveOperation(targetParent: any) {
    if (!this.selectedNode) return;
    
    // Logic to move this.selectedNode to be a child of targetParent
    // TODO: Implement actual graph mutation and validation here
    
    this.feedbackMsg = `Moved '${this.selectedNode.label}' to '${targetParent.data('label')}' (Simulation)`;
    this.isMoveMode = false;
    this.requestUpdate();
  }

  // --- Actions ---

  private startMoveMode() {
    this.isMoveMode = true;
    this.feedbackMsg = "Select the new parent node...";
  }

  private deleteSelected() {
    if (!this.selectedNode) return;
    // TODO: Validate if deletion is allowed (orphan prevention)
    this.cy.$id(this.selectedNode.id).remove();
    this.clearSelection();
    this.feedbackMsg = "Node deleted.";
    this.runLayout();
  }

  private runLayout() {
    this.cy.layout({
      name: 'breadthfirst',
      directed: true,
      padding: 30,
      spacingFactor: 1.5,
      animate: true,
      animationDuration: 300
    }).run();
  }

  private saveTree() {
    const ptbString = serializeCytoscapeToPtb(this.cy);
    // Dispatch event to parent
    this.dispatchEvent(new CustomEvent('save', { detail: { ptb: ptbString } }));
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

    const isLeaf = !this.cy.$id(this.selectedNode.id).isParent() && this.cy.$id(this.selectedNode.id).outgoers().length === 0;
    // TODO: Check if it's a "Ghost" leaf based on data
    const isGhost = this.selectedNode.label.includes('👻'); 
    const canEditLabel = !isLeaf || isGhost;

    // Get rules for this tag if available
    const tagRules = this.rules[this.selectedNode.label] || {};
    const allowedChildren = tagRules.allowed ? Array.from(tagRules.allowed).join(', ') : 'Any';

    return html`
      <div class="flex flex-col gap-6">
        
        <!-- Header / Identity -->
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
            ${isLeaf ? 'Terminal (Leaf)' : 'Syntactic Category'}
          </label>
          
          ${canEditLabel ? html`
            <select class="w-full p-2 bg-white border border-gray-300 rounded shadow-sm focus:border-ibm-blue focus:ring-1 focus:ring-ibm-blue outline-none text-base-dark font-mono font-bold">
              <option value="${this.selectedNode.label}" selected>${this.selectedNode.label}</option>
              <!-- TODO: Populate with valid tags from Backend Rules -->
              <option value="NP">NP (Noun Phrase)</option>
              <option value="VP">VP (Verb Phrase)</option>
            </select>
          ` : html`
            <div class="w-full p-2 bg-gray-100 border border-gray-200 rounded text-gray-500 font-mono italic">
              ${this.selectedNode.label}
            </div>
          `}
        </div>

        <!-- Metasytax Info -->
        <div class="bg-white p-3 rounded border border-gray-200 text-sm text-gray-600">
          <div class="font-bold text-ibm-blue mb-1">Metasyntax Rules</div>
          <p>Allowed Children: <span class="font-mono">${allowedChildren}</span></p>
          <p class="mt-1">ID: <span class="italic">${tagRules.id || 'Generic'}</span></p>
        </div>

        <!-- Actions -->
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Actions</label>
          
          <div class="grid grid-cols-4 gap-2 mb-2">
            <button class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-ibm-blue" title="Add Child">
              <span class="material-symbols-outlined">add_circle</span>
            </button>
            <button @click=${this.deleteSelected} class="p-2 bg-white border border-gray-300 rounded hover:bg-red-50 text-red-500" title="Delete Node">
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

        <!-- Save / Submit -->
        <button 
            @click=${this.saveTree}
            class="w-full py-3 bg-ibm-blue hover:bg-blue-600 text-white font-bold rounded shadow-md transition-colors mt-4"
        >
            Save & Return
        </button>

        <!-- Feedback Area -->
        <div class="mt-auto min-h-[60px] p-3 rounded ${this.feedbackMsg ? 'bg-blue-50 border border-blue-100 text-ibm-blue' : 'bg-transparent'} text-xs transition-all">
          ${this.feedbackMsg}
        </div>

      </div>
    `;
  }

  private loadPtb(ptbString: string) {
    if (!this.cy) return;
    
    const elements = parsePtbToCytoscape(ptbString);

    this.cy.elements().remove();
    this.cy.add(elements);
    
    // Re-run layout to organize new nodes
    this.runLayout();
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
        <div class="flex flex-1 overflow-hidden relative">
            <!-- Canvas -->
            <div id="cy" class="flex-1 bg-base-light relative"></div>

            <!-- Inspector (Right Sidebar) -->
            <div class="w-80 bg-base-light-dim border-l border-gray-200 p-4 overflow-y-auto hidden md:block shadow-inner">
                ${this.renderInspector()}
            </div>
        </div>
      </div>
    `;
  }
}