import { LitElement, html, PropertyValueMap } from "lit";
import { customElement, query, state, property } from "lit/decorators.js";
import cytoscape from "cytoscape";
import {
  parsePtbToCytoscape,
  serializeCytoscapeToPtb,
  serializeNodeToPtb,
  GraphNode
} from "./utils/ptb-utils";
import dagre from "cytoscape-dagre";
cytoscape.use(dagre);
import { GhostLogic } from "./lib/ghost-logic";

const KNOWN_POS_TAGS = new Set([
  "NOUN", "VERB", "DET", "ADJ", "ADV", "PRON", "ADP", "AUX", "CCONJ", "SCONJ", "NUM", "PART", "INTJ", "SYM", "PROPN",
  "n", "v", "d", "a", "r", "p", "c", "w", "z", "f", "i",
  "nc", "np", "aq", "rg", "rn", "sp"
]);

const PUNCTUATION_MARKS = [
  ".", ",", ":", ";", "!", "?", "...", 
  "-", "–", "—", 
  "(", ")", "[", "]", "{", "}", 
  "\"", "'", "«", "»", 
  "¿", "¡"
];

@customElement("grammatomy-editor")
export class GrammatomyEditor extends LitElement {
  @query("#cy")
  private container!: HTMLElement;

  private cy!: cytoscape.Core;

  @property({ type: String })
  ptb: string = "";

  @property({ type: String })
  validationStrategy: string = "lax";

  @state()
  private selectedNode: any = null;

  @state()
  private feedbackMsg: string = "";

  @state()
  private pendingMoveNodeId: string | null = null;

  @state()
  private availableTags: string[] = [];
  @state()
  private validConversionTags: string[] = [];
  @state()
  private validationErrors: string[] = [];
  @state()
  private validationTrace: string[] = [];
  @state()
  private selectedNodeRule: any = {};

  @state()
  private pendingLabel: string = "";

  @state()
  private undoStack: string[] = [];

  @state()
  private redoStack: string[] = [];

  @state()
  private clipboard: string | null = null;

  private resizeObserver: ResizeObserver | null = null;

  private readonly layoutConfig: any = {
    name: "dagre",
    rankDir: "TB",
    spacingFactor: 1.1,
    animate: true,
    animationDuration: 400,
    fit: true,
    ranker: 'network-simplex',
    // Sort based on global DFS index to ensure correct left-to-right order across branches
    sort: (a: any, b: any) => {
      return (a.data("globalIndex") ?? 0) - (b.data("globalIndex") ?? 0);
    },
  };

  override createRenderRoot() {
    return this;
  }

  override connectedCallback() {
    super.connectedCallback();
    this.classList.add("block", "h-full", "w-full");
    window.addEventListener('keydown', this.handleKeyDown);
  }

  override async firstUpdated() {
    // Wait for the first render to complete
    await this.updateComplete;
    this.attemptInitialization();
  }

  override updated(
    changedProperties: PropertyValueMap<any> | Map<PropertyKey, unknown>,
  ) {
    if (this.cy && changedProperties.has("ptb") && this.ptb) {
      this.loadPtb(this.ptb, true);
    }
    if (this.cy && changedProperties.has("validationStrategy")) {
      console.log(`[Editor] Revalidating with strategy: ${this.validationStrategy}`);
      this.validateAllNodes().then(() => this.classifyNodes());
    }
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    this.resizeObserver?.disconnect();
    window.removeEventListener('keydown', this.handleKeyDown);
  }

  private attemptInitialization() {
      if (this.cy) return;
      
      // Direct query in Light DOM
      let container = this.querySelector("#cy");
      
      // SELF-HEALING: If Lit failed to render the DOM, inject fallback structure manually
      if (!container) {
          console.warn("GrammatomyEditor: Container #cy not found via Lit. Injecting fallback DOM.");
          this.innerHTML = `
            <div class="flex flex-col h-full w-full bg-white rounded-lg overflow-hidden border border-gray-200 shadow-sm" style="min-height: 500px;">
                <div class="flex flex-1 overflow-hidden relative min-h-0">
                    <div class="flex-1 relative min-w-0">
                        <div id="cy" class="absolute inset-0 bg-gray-50"></div>
                    </div>
                    <div id="inspector-slot" class="w-80 bg-gray-50 border-l border-gray-200 p-4 overflow-y-auto hidden md:block shadow-inner">
                        <!-- Inspector will be rendered here by Lit in next cycle if possible, or we rely on this structure -->
                    </div>
                </div>
            </div>
          `;
          container = this.querySelector("#cy");
      }
      
      if (container) {
          console.log("GrammatomyEditor: Container #cy found. Initializing Cytoscape.");
          this.initGraph(container as HTMLElement);
          this.fetchTags();
          this.setupResizeObserver(container as HTMLElement);
          
          if (this.ptb) {
              console.log("GrammatomyEditor: Loading initial PTB data.");
              this.loadPtb(this.ptb, true);
          }
      } else {
          console.error("GrammatomyEditor: FATAL - Container #cy not found in DOM after updateComplete.");
          console.log("Current innerHTML:", this.innerHTML);
      }
  }

  private setupResizeObserver(container: HTMLElement) {
      if (this.resizeObserver) return;
      
      this.resizeObserver = new ResizeObserver(() => {
        this.cy?.resize();
      });
      this.resizeObserver.observe(container);
  }

  private async fetchTags() {
    try {
      const response = await fetch("/api/validation/tags");
      if (response.ok) {
        this.availableTags = await response.json();
      }
    } catch (e) {
      console.error("Failed to load tags:", e);
    }
  }

  private initGraph(container: HTMLElement) {
    this.cy = cytoscape({
      container: container,
      elements: [],

      style: [
        {
          selector: "node",
          style: {
            "background-color": "#E69F00",
            "border-width": 2,
            "border-color": "rgba(0,0,0,0.1)",
            label: "data(label)",
            color: "#161616",
            shape: "round-rectangle",
            width: "label",
            height: "label",
            padding: "8px",
            "text-valign": "center",
            "text-halign": "center",
            "font-family": "Roboto Mono",
            "font-size": "12px",
            "font-weight": "bold",
          },
        },
        {
          selector: "node.pos",
          style: {
            "background-color": "#56B4E9",
            color: "#161616",
          },
        },
        {
          selector: "node.leaf",
          style: {
            "background-color": "#009E73",
            color: "#F4F4F4",
            "border-width": 0,
          },
        },
        {
          selector: "node.punctuation",
          style: {
            "background-color": "#0072B2",
            color: "#F4F4F4",
            shape: "tag",
          },
        },
        {
          selector: "node.error",
          style: {
            "background-color": "#D55E00",
            color: "#F4F4F4",
            shape: "hexagon",
            "border-width": 3,
            "border-color": "#FFFFFF",
          },
        },
        {
          selector: ".ghost",
          style: {
            "background-opacity": 0.5,
            "border-style": "dashed",
            "background-color": "#999999",
            color: "#161616",
          },
        },
        {
          selector: "node.ghost-node",
          style: {
            "background-opacity": 0.5,
            "border-style": "dashed",
            "background-color": "#ffffff",
            "border-color": "#009E73",
            color: "#009E73",
          },
        },
        {
          selector: "node.ghost-node:selected",
          style: {
            "border-width": 4,
            "border-color": "#D55E00",
            "border-style": "dashed",
          },
        },
        {
          selector: ".cut-dimmed",
          style: {
            "opacity": 0.4,
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#A0A0A0",
            "target-arrow-color": "#A0A0A0",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
          },
        },
        {
          selector: ":selected",
          style: {
            "border-width": 4,
            "border-color": "#D55E00",
          },
        },
        {
          selector: "node.subtree-highlight",
          style: {
            "background-color": "#161616",
            color: "#E69F00",
            "border-color": "#E69F00",
          },
        },
        {
          selector: "node.pos.subtree-highlight",
          style: {
            "background-color": "#161616",
            color: "#56B4E9",
            "border-color": "#56B4E9",
          },
        },
        {
          selector: "node.leaf.subtree-highlight",
          style: {
            "background-color": "#161616",
            color: "#F4F4F4",
            "border-width": 2,
            "border-color": "#F4F4F4",
          },
        },
        {
          selector: "node.punctuation.subtree-highlight",
          style: {
            "background-color": "#F4F4F4",
            color: "#0072B2",
            "border-width": 2,
            "border-color": "#0072B2",
          },
        },
        {
          selector: "node.ghost-node.subtree-highlight",
          style: {
            "background-color": "#ffffff",
            "border-color": "#009E73",
            color: "#009E73",
            "border-style": "dashed",
            "background-opacity": 0.5,
          },
        },
      ],

      layout: this.layoutConfig,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    this.cy.on("tap", "node", (evt) => {
      const node = evt.target;
      this.selectNode(node);
    });

    this.cy.on("tap", (evt) => {
      if (evt.target === this.cy) {
        this.clearSelection();
        this.cancelCut();
      }
    });

    this.cy.on("dragfree", "node", () => {
      this.runLayout(false);
    });
  }

  /**
   * Recalculates a global index for every node based on a Depth-First Search (DFS)
   * that respects the local sibling order. This ensures that layout algorithms
   * like Dagre preserve the linear reading order of the sentence.
   */
  private recalculateGlobalIndices() {
    const roots = this.cy.nodes().filter((n) => n.incomers().length === 0);
    // Sort roots by their local index (if forest)
    roots.sort((a, b) => (a.data("index") ?? 0) - (b.data("index") ?? 0));

    let counter = 0;
    const traverse = (node: any) => {
      node.data("globalIndex", counter++);
      const children = node.outgoers("node").sort((a: any, b: any) => {
        return (a.data("index") ?? 0) - (b.data("index") ?? 0);
      });
      children.forEach((child: any) => traverse(child));
    };

    roots.forEach((root) => traverse(root));
  }

  private handleKeyDown = (e: KeyboardEvent) => {
    // Ignore if focus is on an input/textarea
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return;
    }

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      if (e.shiftKey) {
        this.handleRedo();
      } else {
        this.handleUndo();
      }
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') {
      e.preventDefault();
      this.handleRedo();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      this.cancelCut();
      this.clearSelection();
    }
  }

  // --- Core Logic Methods ---

  private loadPtb(ptbString: string, fit: boolean = true) {
    if (!this.cy) return;

    const elements = parsePtbToCytoscape(ptbString);

    // Assign indices based on the strict order of the PTB string (insertion order)
    const childCounts = new Map<string, number>();
    const nodeMap = new Map<string, any>();
    
    // First pass: Index nodes by ID for quick lookup
    for (const el of elements) {
        if (!('source' in el.data)) {
            nodeMap.set(el.data.id, el);
        }
    }

    // Second pass: Process edges to assign indices to target nodes
    // The 'elements' array preserves the order from the PTB string
    for (const el of elements) {
        if ('source' in el.data) {
            const source = el.data.source;
            const target = el.data.target;
            
            const currentIndex = childCounts.get(source) || 0;
            childCounts.set(source, currentIndex + 1);
            
            const node = nodeMap.get(target);
            if (node) {
                node.data.index = currentIndex;
            }
        }
    }
    
    // Handle Roots (nodes not targeted by any edge)
    let rootIndex = 0;
    for (const el of elements) {
        if (!('source' in el.data)) {
             // If index is undefined, it means no edge targets this node -> it's a root
             if (el.data.index === undefined) {
                 el.data.index = rootIndex++;
             }
        }
    }

    this.cy.elements().remove();
    this.cy.add(elements);

    this.classifyNodes();
    this.recalculateGlobalIndices(); // Calculate global order before validation/layout
    this.validateAllNodes();
    
    this.runLayout(fit);
  }

  public getCurrentPtb(): string {
    if (!this.cy) return "";
    return serializeCytoscapeToPtb(this.cy);
  }

  private pushState() {
    const currentPtb = this.getCurrentPtb();
    if (currentPtb) {
      this.undoStack = [...this.undoStack, currentPtb];
      this.redoStack = [];
      if (this.undoStack.length > 50) {
        this.undoStack.shift();
      }
    }
  }

  private async validateAllNodes() {
    // Perform Bottom-Up Validation (Post-Order)
    // 1. Get all nodes
    const allNodes = this.cy.nodes();
    
    // 2. Sort by depth (deepest first) or topological sort
    // A simple way is to use the fact that leaves have no outgoers in the tree structure (edges go Parent->Child)
    // Cytoscape's topological sort gives parents before children. We reverse it.
    const sortedNodes = allNodes.sort((a, b) => {
        // Sort by depth descending
        const depthA = this.getNodeDepth(a);
        const depthB = this.getNodeDepth(b);
        return depthB - depthA;
    });

    try {
      // Validate sequentially to propagate validity
      for (let i = 0; i < sortedNodes.length; i++) {
          await this.validateNode(sortedNodes[i]);
      }
      console.log("Initial tree validation complete.");
    } catch (e) {
      console.error("Error during initial batch validation:", e);
    }
  }

  private getNodeDepth(node: any): number {
      // Calculate depth from root
      return node.incomers("edge").length === 0 ? 0 : node.ancestors().length;
  }

  private async validateNode(
    nodeElement: cytoscape.NodeSingular,
  ): Promise<{ isValid: boolean; errors: string[]; validTags: string[]; trace: string[] }> {
    const nodeData = nodeElement.data();
    const isLeaf = !nodeElement.isParent() && nodeElement.outgoers().length === 0;
    const isGhost = nodeData.isGhost || nodeData.label.includes("👻");

    nodeElement.removeClass("error");

    if (isLeaf && !isGhost) {
      return { isValid: true, errors: [], validTags: [], trace: [] };
    }

    const incomingEdges = nodeElement.incomers("edge");
    let parentTag: string | null = null;
    if (incomingEdges.length > 0) {
      const source = incomingEdges.source();
      if (source && source.length > 0) {
        parentTag = source.data("label");
      }
    }

    const childrenNodes = nodeElement.outgoers("node");
    const hasGhostChild = childrenNodes.some(
      (n) => n.data("isGhost") || n.data("label").includes("👻"),
    );
    const cleanChildrenLabels = childrenNodes
      .filter((n) => !n.data("isGhost") && !n.data("label").includes("👻"))
      .map((n) => n.data("label"));
    const descendantLabels = nodeElement
      .successors("node")
      .map((n) => n.data("label"));

    let localValidTags: string[] = [];
    let localErrors: string[] = [];
    let localTrace: string[] = [];
    let isContextValid = false;
    let isStructureValid = false;

    const isRoot = nodeData.label === "ROOT" && !parentTag;

    try {
      const convResponse = await fetch("/api/validation/options", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          parent_tag: parentTag,
          current_tag: nodeData.label,
          children_tags: cleanChildrenLabels,
        }),
      });
      if (convResponse.ok) {
        const result = await convResponse.json();
        localValidTags = result.options || [];
        if (result.trace) localTrace.push(...result.trace);
        
        if (isRoot) {
          isContextValid = true;
          if (!localValidTags.includes("ROOT")) localValidTags.push("ROOT");
        } else {
          isContextValid = isGhost || result.valid;
        }
      } else {
        if (isRoot) isContextValid = true;
        else {
            isContextValid = false;
            localErrors.push("Server error during context validation.");
        }
      }
    } catch (e) {
      console.error("Context validation failed", e);
      if (isRoot) isContextValid = true;
      else localErrors.push("Network error.");
    }

    if (!isContextValid) {
        localErrors.push(`Context Error: Tag '${nodeData.label}' is incompatible with parent '${parentTag || "ROOT"}'.`);
    }

    try {
      const reqResponse = await fetch("/api/validation/check/requirements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tag: nodeData.label,
          children_tags: cleanChildrenLabels,
          descendant_tags: descendantLabels,
          strategy: this.validationStrategy,
        }),
      });
      if (reqResponse.ok) {
        const reqResult = await reqResponse.json();
        isStructureValid = reqResult.allowed;
        if (reqResult.trace) localTrace.push(...reqResult.trace);
        if (!isStructureValid) {
          if (!hasGhostChild) {
            localErrors.push(reqResult.reason);
          } else {
            isStructureValid = true;
          }
        }
      } else {
        isStructureValid = false;
        localErrors.push("Server error during requirements validation.");
      }
    } catch (e) {
      console.error("Requirements validation failed", e);
      localErrors.push("Network error.");
    }

    const isValid = isContextValid && isStructureValid;
    if (!isValid) {
      nodeElement.addClass("error");
    }

    return { isValid, errors: localErrors, validTags: localValidTags, trace: localTrace };
  }

  private async validateAncestors(startNode: cytoscape.NodeSingular) {
    let current = startNode;
    while (current && current.length > 0) {
      await this.validateNode(current);
      const parent = current.incomers("edge").source();
      if (parent && parent.length > 0) {
        current = parent;
      } else {
        break;
      }
    }
    this.classifyNodes();
    this.requestUpdate();
  }

  private classifyNodes() {
    this.cy.batch(() => {
      this.cy.nodes().forEach((node) => {
        const isLeaf = node.outdegree(false) === 0;
        const label = node.data("label");

        const hasError = node.hasClass("error");
        node.classes([]);
        if (hasError) node.addClass("error");

        if (label.includes("👻") || label.includes("ERR") || node.data('isGhost')) {
          if (label.includes("ERR")) {
            node.addClass("error");
          } else {
            node.removeClass("error");
          }
          if (label.includes("👻") || node.data('isGhost')) node.addClass("ghost-node");
          return;
        }

        const isPunctuation =
          /^[\.,:;'"\(\)\[\]\{}\-–—\?!]+$/.test(label) ||
          ["fp", "fc", "fg", "fz", "fs", "fd", "punct"].includes(label.toLowerCase());

        if (isPunctuation) {
          node.addClass("punctuation");
          return;
        }

        if (isLeaf) {
          node.addClass("leaf");
        } else {
          if (KNOWN_POS_TAGS.has(label) || KNOWN_POS_TAGS.has(label.toUpperCase())) {
            node.addClass("pos");
          }
        }
      });
    });
  }

  // --- Interaction Methods ---

  private async selectNode(node: any) {
    this.cy.elements().removeClass("subtree-highlight");
    node.successors().addClass("subtree-highlight");

    this.selectedNode = node.data();
    this.pendingLabel = this.selectedNode.label;
    this.validationErrors = [];
    
    this.requestUpdate();

    try {
      const nodeElement = this.cy.$id(this.selectedNode.id);
      const isLeaf = !nodeElement.isParent() && nodeElement.outgoers().length === 0;
      const isGhost = this.selectedNode.isGhost || this.selectedNode.label.includes("👻");

      if (isLeaf && !isGhost) {
        this.validConversionTags = [];
        if (!this.selectedNode.label.includes("👻") && !this.selectedNode.label.includes("ERR")) {
          nodeElement.removeClass("error");
        }
      } else {
        const validationResult = await this.validateNode(nodeElement);
        this.validConversionTags = validationResult.validTags;
        this.validationErrors = validationResult.errors;
        this.validationTrace = validationResult.trace;
      }

      try {
        const encodedLabel = encodeURIComponent(this.selectedNode.label);
        const response = await fetch(`/api/validation/rules/${encodedLabel}`);
        if (response.ok) {
          this.selectedNodeRule = await response.json();
        } else {
          this.selectedNodeRule = {};
        }
      } catch (e) {
        console.error("Failed to fetch node rules", e);
        this.selectedNodeRule = {};
      }
    } catch (err) {
      console.error("Error in selectNode async flow:", err);
    } finally {
      this.feedbackMsg = "";
      this.requestUpdate();
    }
  }

  private clearSelection() {
    this.cy.elements().removeClass("subtree-highlight");
    this.selectedNode = null;
    this.selectedNodeRule = {};
    this.validConversionTags = [];
    this.validationErrors = [];
    this.validationTrace = [];
    this.feedbackMsg = "";
    this.requestUpdate();
  }

  private handlePendingLabelChange(e: Event) {
    const target = e.target as HTMLSelectElement | HTMLInputElement;
    this.pendingLabel = target.value;
  }

  private async applyLabelChange() {
    if (!this.selectedNode || this.pendingLabel === this.selectedNode.label) return;

    this.pushState();

    if (this.selectedNode.isGhost || this.selectedNode.label.includes("👻")) {
       GhostLogic.resolveGhost(this.cy, this.selectedNode.id, this.pendingLabel);
       this.runLayout(false);
    } else {
       this.cy.$id(this.selectedNode.id).data("label", this.pendingLabel);
    }
    
    this.selectedNode = this.cy.$id(this.selectedNode.id).data();
    this.pendingLabel = this.selectedNode.label;
    
    await this.validateAncestors(this.cy.$id(this.selectedNode.id));
    this.classifyNodes();

    this.feedbackMsg = `Node label changed to '${this.selectedNode.label}'.`;
    this.requestUpdate();
  }

  private handleReorder(direction: "left" | "right") {
    if (!this.selectedNode) return;
    const nodeToMove = this.cy.$id(this.selectedNode.id);
    const parent = nodeToMove.incomers("edge").source();

    if (parent.empty()) {
      this.feedbackMsg = "Cannot reorder ROOT or orphan nodes.";
      return;
    }

    // Sort by logical index, NOT visual position
    const children = parent.outgoers("node").sort((a, b) => (a.data("index") ?? 0) - (b.data("index") ?? 0));
    
    if (children.length <= 1) return;

    // Normalize indices to 0, 1, 2... to prevent collisions/gaps
    children.forEach((child, i) => child.data("index", i));

    const currentIndex = children.findIndex((n) => n.id() === nodeToMove.id());
    if (currentIndex === -1) return;

    const newIndex = direction === "left" ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= children.length) return;

    const neighborNode = children[newIndex];
    
    // Swap indices
    nodeToMove.data("index", newIndex);
    neighborNode.data("index", currentIndex);

    this.recalculateGlobalIndices(); // Update global order after swap
    this.feedbackMsg = `Node reordered.`;
    this.runLayout(false);
    this.requestUpdate();
  }

  private handleAddChild() {
    if (!this.selectedNode) return;

    const label = this.selectedNode.label;
    const isPunctuation = 
      /^[\.,:;'"\(\)\[\]\{}\-–—\?!]+$/.test(label) || 
      ["fp", "fc", "fg", "fz", "fs", "fd", "punct", "PUNCT"].includes(label.toLowerCase());
    
    const isPos = KNOWN_POS_TAGS.has(label) || KNOWN_POS_TAGS.has(label.toUpperCase());

    // Calculate next index safely (max + 1) to avoid collisions with existing siblings
    const children = this.cy.$id(this.selectedNode.id).outgoers("node");
    let maxIndex = -1;
    children.forEach(child => {
        const idx = child.data("index");
        if (typeof idx === 'number' && idx > maxIndex) maxIndex = idx;
    });
    const nextIndex = maxIndex + 1;

    this.pushState();
    this.cy.batch(() => {
      if (isPunctuation) {
        const leafId = `punct_${Date.now()}`;
        this.cy.add({
          group: "nodes",
          data: { id: leafId, label: ".", index: nextIndex },
          classes: "punctuation leaf"
        });
        this.cy.add({
          group: "edges",
          data: { source: this.selectedNode.id, target: leafId }
        });
        this.feedbackMsg = "Punctuation leaf added.";
      } else if (isPos) {
        const leafId = `leaf_${Date.now()}`;
        this.cy.add({
          group: "nodes",
          data: { id: leafId, label: "∅", index: nextIndex },
          classes: "leaf"
        });
        this.cy.add({
          group: "edges",
          data: { source: this.selectedNode.id, target: leafId }
        });
        this.feedbackMsg = "Leaf node added.";
      } else {
        GhostLogic.spawnGhost(this.cy, this.selectedNode.id);
        this.feedbackMsg = "Ghost node added.";
        
        // Assign index to the newly spawned ghost (it's the one we just added)
        const children = this.cy.$id(this.selectedNode.id).outgoers("node");
        children.forEach(child => { if (child.data("index") === undefined) child.data("index", nextIndex); });
      }
    });

    this.recalculateGlobalIndices(); // New nodes added
    this.classifyNodes();
    this.runLayout(false);
    this.requestUpdate();
  }

  private reindexChildren(parentNode: any) {
    if (!parentNode || parentNode.empty()) return;
    
    const children = parentNode.outgoers("node").sort((a: any, b: any) => {
        const idxA = a.data('index');
        const idxB = b.data('index');
        
        // Primary sort: Structural Index
        if (idxA !== undefined && idxB !== undefined && idxA !== idxB) {
            return idxA - idxB;
        }
        
        // Secondary sort: Visual X Position (Tie-breaker)
        // This prevents swapping if indices are lost or collided before layout
        return a.position('x') - b.position('x');
    });
    
    children.forEach((child: any, i: number) => child.data('index', i));
  }

  private async deleteSelected() {
    if (!this.selectedNode) return;

    // If deleting the node currently marked for move, cancel the move state
    if (this.selectedNode.id === this.pendingMoveNodeId) {
        this.cancelCut();
    }

    if (!confirm("Are you sure you want to delete this node?")) return;

    const nodeElement = this.cy.$id(this.selectedNode.id);
    if (nodeElement.empty()) return;

    if (nodeElement.data("label") === "ROOT") {
      this.feedbackMsg = "Cannot delete ROOT.";
      return;
    }

    const isLeaf = nodeElement.outgoers().length === 0;
    const isGhost = this.selectedNode.isGhost || this.selectedNode.label.includes("👻");

    let targetToDelete = nodeElement;

    if (
      (isLeaf && !isGhost) ||
      nodeElement.hasClass("pos") ||
      nodeElement.hasClass("punctuation")
    ) {
      if (isLeaf) {
        const parent = nodeElement.incomers("edge").source();
        if (parent.length > 0) targetToDelete = parent;
      }
    }

    const parentOfDeleted = targetToDelete.incomers("edge").source();

    this.pushState();

    const branch = targetToDelete.successors().union(targetToDelete);
    branch.remove();

    this.feedbackMsg = "Node deleted.";

    if (parentOfDeleted.length > 0 && parentOfDeleted.inside()) {
      if (parentOfDeleted.outgoers("node").length === 0) {
        const ghostId = GhostLogic.spawnGhost(this.cy, parentOfDeleted.id());
        this.cy.$id(ghostId).data("index", 0);
        this.feedbackMsg += " Parent was empty, ghost added.";
        
        // Ensure the parent itself maintains its index relative to its siblings
        // (No change needed for parentOfDeleted, but good to know)
        this.runLayout(false);
      }
      
      try {
        await this.validateAncestors(parentOfDeleted);
      } catch (e) {
        console.error("Ancestor validation failed after delete:", e);
      }
    }

    // Reindex siblings of the deleted node (if any remain) to close gaps
    // If parentOfDeleted is valid, reindex its children
    if (parentOfDeleted.length > 0) this.reindexChildren(parentOfDeleted);
    this.recalculateGlobalIndices(); // Topology changed

    this.clearSelection();
    this.runLayout(false);
  }

  // --- Clipboard Operations ---

  private copySelected() {
    if (!this.selectedNode) return;
    let node = this.cy.$id(this.selectedNode.id);

    // Auto-select parent if leaf (Word/Sign) to ensure POS+Word unit
    const isLeaf = node.outdegree(false) === 0;
    const isGhost = node.data("isGhost") || node.data("label").includes("👻");
    if (isLeaf && !isGhost) {
        const parent = node.incomers("edge").source();
        if (parent.length > 0) node = parent;
    }

    this.clipboard = serializeNodeToPtb(node);
    this.feedbackMsg = "Subtree copied to clipboard.";
    this.requestUpdate();
  }

  private cancelCut() {
    if (this.pendingMoveNodeId) {
      const node = this.cy.$id(this.pendingMoveNodeId);
      node.successors().union(node).removeClass("cut-dimmed");
      this.pendingMoveNodeId = null;
      this.feedbackMsg = "Cut operation cancelled.";
      this.requestUpdate();
    }
  }

  private cutSelected() {
    if (!this.selectedNode) return;
    
    // If there was a previous cut, cancel it (restore visuals)
    if (this.pendingMoveNodeId) {
        this.cancelCut();
    }

    let node = this.cy.$id(this.selectedNode.id);

    // Auto-select parent if leaf (Word/Sign) to ensure POS+Word unit
    const isLeaf = node.outdegree(false) === 0;
    const isGhost = node.data("isGhost") || node.data("label").includes("👻");
    if (isLeaf && !isGhost) {
        const parent = node.incomers("edge").source();
        if (parent.length > 0) node = parent;
    }

    this.pendingMoveNodeId = node.id();
    // Apply visual style to subtree
    node.successors().union(node).addClass("cut-dimmed");
    
    this.feedbackMsg = "Node marked for move. Select destination and click 'Move Here'.";
    this.requestUpdate();
  }

  private async pasteFromClipboard() {
    if (!this.clipboard) return;
    if (!this.selectedNode) return;

    let targetNode = this.cy.$id(this.selectedNode.id);
    const isGhost = targetNode.data("isGhost") || targetNode.data("label").includes("👻");
    const isTerminal = targetNode.hasClass("pos") || targetNode.hasClass("punctuation") || targetNode.hasClass("leaf");
    
    if (isTerminal) {
        this.feedbackMsg = "Cannot paste into a Terminal/POS/Leaf node.";
        return;
    }

    this.pushState();

    // Parse clipboard content into elements
    const elements = parsePtbToCytoscape(this.clipboard);
    
    // Find the root of the pasted tree (node with no source in the elements list)
    const targets = new Set(elements.filter(e => 'source' in e.data).map(e => e.data.target));
    const rootElement = elements.find(e => !('source' in e.data) && !targets.has(e.data.id));
    
    if (!rootElement) {
        this.feedbackMsg = "Invalid clipboard content.";
        return;
    }

    // Generate unique IDs for pasted elements to avoid collisions
    const idMap = new Map<string, string>();
    const timestamp = Date.now();
    elements.forEach((el, i) => {
        const oldId = el.data.id;
        if (!('source' in el.data)) {
            const newId = `paste_${timestamp}_${i}`;
            idMap.set(oldId, newId);
            el.data.id = newId;
        }
    });

    // Update edges with new IDs
    elements.forEach(el => {
        if ('source' in el.data) {
            el.data.source = idMap.get(el.data.source) || el.data.source;
            el.data.target = idMap.get(el.data.target) || el.data.target;
        }
    });

    try {
        this.cy.batch(() => {
            // If target is Ghost, replace it
            if (isGhost) {
                const parent = targetNode.incomers("edge").source();
                const ghostIndex = targetNode.data("index") || 0;
                
                // Add new elements
                this.cy.add(elements);
                
                // Link parent to new root
                if (parent.length > 0) {
                    this.cy.add({
                        group: "edges",
                        data: { source: parent.id(), target: rootElement.data.id }
                    });
                    // Assign index to new root
                    this.cy.$id(rootElement.data.id).data("index", ghostIndex);
                }
                
                // Remove ghost
                targetNode.remove();
                this.feedbackMsg = "Pasted: Replaced ghost node.";
            } else {
                // Append as last child
                const children = targetNode.outgoers("node");
                let maxIndex = -1;
                children.forEach(child => {
                    const idx = child.data("index");
                    if (typeof idx === 'number' && idx > maxIndex) maxIndex = idx;
                });
                const nextIndex = maxIndex + 1;

                // Add new elements
                this.cy.add(elements);
                
                // Link target to new root
                this.cy.add({
                    group: "edges",
                    data: { source: targetNode.id(), target: rootElement.data.id }
                });
                
                // Assign index
                this.cy.$id(rootElement.data.id).data("index", nextIndex);
                this.feedbackMsg = "Pasted: Appended as child.";
            }
        });

        this.classifyNodes();
        this.recalculateGlobalIndices(); // Topology changed (paste)
        this.runLayout(false);
        
        // Validate the modified branch
        const newRootId = rootElement.data.id;
        if (newRootId) {
            const newRoot = this.cy.$id(newRootId);
            const parent = newRoot.incomers("edge").source();
            if (parent.length > 0) await this.validateAncestors(parent);
        }
    } catch (e) {
        console.error("Paste failed:", e);
        this.feedbackMsg = "Error pasting content. Check console.";
        // Ensure we recover UI state
        this.runLayout(false);
    }
    
    this.requestUpdate();
  }

  private async completeMove() {
    if (!this.selectedNode || !this.pendingMoveNodeId) return;
    
    let targetNode = this.cy.$id(this.selectedNode.id);
    const isGhost = targetNode.data("isGhost") || targetNode.data("label").includes("👻");
    const isTerminal = targetNode.hasClass("pos") || targetNode.hasClass("punctuation") || targetNode.hasClass("leaf");
    
    if (isTerminal) {
        this.feedbackMsg = "Cannot move into a Terminal/POS/Leaf node.";
        return;
    }

    const nodeToMove = this.cy.$id(this.pendingMoveNodeId);
    
    if (nodeToMove.empty()) { this.cancelCut(); return; }
    if (nodeToMove.id() === targetNode.id()) { this.feedbackMsg = "Cannot move to self."; return; }
    if (nodeToMove.successors().contains(targetNode)) { this.feedbackMsg = "Cannot move into descendant."; return; }

    // Handle Ghost Target Replacement for Move
    if (isGhost) {
        const ghostParent = targetNode.incomers("edge").source();
        if (ghostParent.length > 0) {
            GhostLogic.deleteSubtree(this.cy, targetNode.id());
            targetNode = ghostParent;
        }
    }

    const oldParent = nodeToMove.incomers("edge").source();

    this.pushState();
    this.cy.batch(() => {
        nodeToMove.incomers("edge").remove();
        this.cy.add({
            group: "edges",
            data: { source: targetNode.id(), target: nodeToMove.id() }
        });
    });

    // Cleanup visual state
    nodeToMove.successors().union(nodeToMove).removeClass("cut-dimmed");
    this.pendingMoveNodeId = null;

    this.feedbackMsg = "Node moved successfully.";
    this.classifyNodes();
    this.recalculateGlobalIndices();
    
    this.validateAncestors(targetNode);
    if (oldParent.length > 0) this.validateAncestors(oldParent);
    
    this.runLayout(false);
    this.requestUpdate();
  }

  private _dispatchStrategyChange(e: Event) {
    const newValue = (e.target as HTMLSelectElement).value;
    this.dispatchEvent(new CustomEvent('strategy-change', {
      detail: { strategy: newValue },
      bubbles: true,
      composed: true
    }));
  }

  private handleUndo() {
    if (this.undoStack.length === 0) return;

    const currentPtb = this.getCurrentPtb();
    const previousPtb = this.undoStack.pop();
    
    if (previousPtb) {
      this.redoStack = [...this.redoStack, currentPtb];
      this.undoStack = [...this.undoStack];
      this.loadPtb(previousPtb, false);
      this.feedbackMsg = "Undo successful.";
    }
  }

  private handleRedo() {
    if (this.redoStack.length === 0) return;

    const currentPtb = this.getCurrentPtb();
    const nextPtb = this.redoStack.pop();

    if (nextPtb) {
      this.undoStack = [...this.undoStack, currentPtb];
      this.redoStack = [...this.redoStack];
      this.loadPtb(nextPtb, false);
      this.feedbackMsg = "Redo successful.";
    }
  }

  private runLayout(fit: boolean = true) {
    if (!this.cy) return;

    this.cy.resize();
    this.cy.layout({ ...this.layoutConfig, fit: fit }).run();
  }

  private renderValidationIssues(errors: string[], trace: string[]) {
    if (errors.length === 0) return html``;
    return html`
      <div
        class="bg-red-50 border-l-2 border-red-500 p-2 rounded-r mb-4 text-xs"
      >
        <div class="font-bold text-red-700 mb-1 flex items-center gap-1">
          <span class="material-symbols-outlined text-[16px]">error</span>
          Validation Issues
        </div>
        <ul class="list-disc list-inside text-red-600 space-y-1 leading-tight">
          ${errors.map((e) => html`<li>${e}</li>`)}
        </ul>
        <div class="mt-2 pt-2 border-t border-red-200">
            <div class="font-bold text-red-800 mb-1 text-[10px] uppercase">Trace Log</div>
            <ul class="font-mono text-[10px] text-gray-600 space-y-1">
                ${trace.map(t => html`<li>${t}</li>`)}
            </ul>
        </ul>
      </div>
    `;
  }

  private renderEditControl(
    canEditLabel: boolean,
    isGhostLeaf: boolean,
    isWordLeaf: boolean,
    isPunctuationLeaf: boolean,
    isCurrentTagValid: boolean,
    isDropdownDisabled: boolean,
    validTags: string[],
  ) {
    if (!canEditLabel) {
      return html`
        <div
          class="w-full p-2 bg-gray-100 border border-gray-200 rounded text-gray-500 font-mono italic text-center"
        >
          Immutable
        </div>
      `;
    }

    if (isWordLeaf) {
      return html`
        <input
          type="text"
          class="w-full p-2 bg-white border border-gray-300 rounded shadow-sm focus:border-ibm-blue focus:ring-1 focus:ring-ibm-blue outline-none text-base-dark font-mono font-bold"
          .value=${this.pendingLabel}
          @input=${this.handlePendingLabelChange}
          placeholder="Type word..."
        />
      `;
    }

    if (isPunctuationLeaf) {
      return html`
        <select
          class="w-full p-2 bg-white border border-gray-300 rounded shadow-sm focus:border-ibm-blue focus:ring-1 focus:ring-ibm-blue outline-none text-base-dark font-mono font-bold"
          @change=${this.handlePendingLabelChange}
        >
          ${PUNCTUATION_MARKS.map(mark => html`
            <option value="${mark}" ?selected=${mark === this.pendingLabel}>${mark}</option>
          `)}
        </select>
      `;
    }

    return html`
      <select
        class="w-full p-2 bg-white border ${isCurrentTagValid
          ? "border-gray-300"
          : "border-red-500 bg-red-50"} rounded shadow-sm focus:border-ibm-blue focus:ring-1 focus:ring-ibm-blue outline-none text-base-dark font-mono font-bold disabled:opacity-50 disabled:cursor-not-allowed"
        @change=${this.handlePendingLabelChange}
        ?disabled=${isDropdownDisabled}
      >
        ${isGhostLeaf
          ? html`<option value="" disabled selected>Select tag...</option>`
          : html``}
        ${validTags.map(
          (tag) => html`
            <option value="${tag}" ?selected=${tag === this.pendingLabel}>
              ${tag}
            </option>
          `,
        )}
      </select>
    `;
  }

  private renderApplyButton(canEditLabel: boolean) {
    if (!canEditLabel) return html``;
    
    const hasChanged = this.pendingLabel !== this.selectedNode.label;
    
    return html`
      <button
        @click=${this.applyLabelChange}
        class="w-full mt-2 py-1 px-2 bg-ibm-blue text-white rounded text-xs font-bold uppercase tracking-wide hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        ?disabled=${!hasChanged}
      >
        Confirm Change
      </button>
    `;
  }

  private renderToolbar() {
    return html`
      <div class="flex gap-2 justify-end items-center">
        <button
          @click=${this.handleUndo}
          class="p-1.5 text-gray-600 hover:text-ibm-blue hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Undo (Ctrl+Z)"
          ?disabled=${this.undoStack.length === 0}
        >
          <span class="material-symbols-outlined text-[18px]">undo</span>
        </button>
        <button
          @click=${this.handleRedo}
          class="p-1.5 text-gray-600 hover:text-ibm-blue hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Redo (Ctrl+Y)"
          ?disabled=${this.redoStack.length === 0}
        >
          <span class="material-symbols-outlined text-[18px]">redo</span>
        </button>
        <div class="flex-1"></div>
        <div class="flex items-center gap-2">
          <label for="strategy-select" class="text-xs text-gray-500 font-medium">Validation:</label>
          <select id="strategy-select" class="text-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" .value=${this.validationStrategy} @change=${this._dispatchStrategyChange}>
            <option value="lax">Lax (Neural)</option>
            <option value="strict">Strict (AnCora)</option>
          </select>
        </div>
        <div class="flex-1"></div>
        <button @click=${() => this.runLayout(true)} class="p-1.5 text-gray-600 hover:text-ibm-blue hover:bg-gray-200 rounded transition-colors" title="Fit View"><span class="material-symbols-outlined text-[18px]">fit_screen</span></button>
      </div>
    `;
  }

  private renderNodeInspector() {
    if (!this.selectedNode) {
      return html`
        <div class="h-full flex flex-col items-center justify-center text-gray-400 p-6 text-center">
          <span class="material-symbols-outlined text-4xl mb-2">touch_app</span>
          <p class="text-sm">Select a node to view properties and actions.</p>
        </div>
      `;
    }

    const nodeElement = this.cy.$id(this.selectedNode.id);
    const isLeaf =
      !nodeElement.isParent() && nodeElement.outgoers().length === 0;
    const isPos = nodeElement.hasClass("pos");
    const isPunctuation = nodeElement.hasClass("punctuation");
    
    let isWordLeaf = false;
    let isPunctuationLeaf = false;
    
    if (isLeaf) {
      const incoming = nodeElement.incomers("edge");
      if (incoming.length > 0) {
        const parent = incoming.source();
        if (parent && parent.length > 0 && parent.hasClass("pos")) isWordLeaf = true;
        if (parent && parent.length > 0 && parent.hasClass("punctuation")) isPunctuationLeaf = true;
      }
    }

    const isGhost = this.selectedNode.isGhost || this.selectedNode.label.includes("👻");
    const canEditLabel = true;
    const isGhostLeaf = isLeaf && isGhost;
    const isTerminal = nodeElement.hasClass("pos") || nodeElement.hasClass("punctuation") || nodeElement.hasClass("leaf");
    
    const hasChildren = nodeElement.outgoers("node").length > 0;
    const canAddChild = !isWordLeaf && !isPunctuationLeaf && !isGhost && !((isPos || isPunctuation) && hasChildren) && !isPunctuationLeaf;

    const validTags = this.validConversionTags;
    let isCurrentTagValid = isLeaf
      ? true
      : validTags.includes(this.selectedNode.label);

    if (this.selectedNode.label === "ROOT" && nodeElement.incomers().length === 0) {
        isCurrentTagValid = true;
    }

    const isDropdownDisabled = validTags.length === 0;

    let headerBg = "#E69F00";
    let headerText = "#161616";
    let typeLabel = "Phrasal Node";

    if (!isCurrentTagValid || nodeElement.hasClass("error")) {
      headerBg = "#D55E00";
      headerText = "#F4F4F4";
      typeLabel = "Invalid / Error";
    } else if (isPunctuation) {
      headerBg = "#0072B2";
      headerText = "#F4F4F4";
      typeLabel = "Punctuation";
    } else if (isLeaf) {
      headerBg = "#009E73";
      headerText = "#F4F4F4";
      typeLabel = "Terminal (Leaf)";
    } else if (isPos) {
      headerBg = "#56B4E9";
      headerText = "#161616";
      typeLabel = "Syntactic Category";
    }

    let nodeToCheck = nodeElement;
    if (isLeaf) {
      const incoming = nodeElement.incomers("edge");
      if (incoming.length > 0) {
          const parent = incoming.source();
          if (parent && parent.length > 0) nodeToCheck = parent;
      }
    }

    const incomingEdges = nodeToCheck.incomers("edge");
    let isOnlyChild = false;
    if (incomingEdges.length > 0) {
      const parent = incomingEdges.source();
      if (parent && parent.length > 0 && parent.outgoers("node").length === 1) {
        isOnlyChild = true;
      }
    }

    const parentEdges = nodeElement.incomers("edge");
    const parent = parentEdges.length > 0 ? parentEdges.source() : null;
    
    let canMoveLeft = false;
    let canMoveRight = false;
    if (parent && parent.length > 0) {
        // Use logical index for button state too
        const children = parent.outgoers("node").sort((a, b) => (a.data('index') ?? 0) - (b.data('index') ?? 0));
        const currentIndex = children.findIndex(n => n.id() === nodeElement.id());
        if (currentIndex > 0) {
            canMoveLeft = true;
        }
        if (currentIndex !== -1 && currentIndex < children.length - 1) {
            canMoveRight = true;
        }
    }

    return html`
      <div class="flex flex-col gap-6">
        <div
          class="rounded-lg p-4 shadow-sm flex flex-col items-center justify-center gap-2 transition-colors duration-300"
          style="background-color: ${headerBg}; color: ${headerText};"
        >
          <div
            class="text-[10px] uppercase tracking-widest opacity-80 font-bold"
          >
            ${typeLabel}
          </div>
          <div class="text-2xl font-mono font-bold tracking-tight">
            ${this.selectedNode.label}
          </div>
        </div>

        <div>
          <label
            class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1"
          >
            Edit Label
          </label>

          ${this.renderEditControl(
            canEditLabel,
            isGhostLeaf,
            isWordLeaf,
            isPunctuationLeaf,
            isCurrentTagValid,
            isDropdownDisabled,
            validTags,
          )}
          ${this.renderApplyButton(canEditLabel)}
        </div>

        ${this.renderValidationIssues(this.validationErrors, this.validationTrace)}

        <div>
          <label
            class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2"
            >Actions</label
          >
          
          <!-- Row 1: Clipboard & Move (Family) -->
          <div class="grid grid-cols-4 gap-2 mb-2">
            <button
              @click=${this.cutSelected}
              ?disabled=${isOnlyChild}
              class="p-2 bg-purple-50 border border-purple-200 rounded hover:bg-purple-100 text-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
              title="Cut Subtree"
            >
              <span class="material-symbols-outlined">content_cut</span>
            </button>
            <button
              @click=${this.completeMove}
              ?disabled=${!this.pendingMoveNodeId || isTerminal}
              class="p-2 bg-purple-50 border border-purple-200 rounded hover:bg-purple-100 text-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
              title="Move Here"
            >
              <span class="material-symbols-outlined">drive_file_move</span>
            </button>
            <button
              @click=${this.copySelected}
              class="p-2 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
              title="Copy Subtree"
            >
              <span class="material-symbols-outlined">content_copy</span>
            </button>
            <button
              @click=${this.pasteFromClipboard}
              ?disabled=${!this.clipboard || isTerminal}
              class="p-2 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
              title="Paste Subtree"
            >
              <span class="material-symbols-outlined">content_paste</span>
            </button>
          </div>

          <!-- Row 2: Structure & Reorder -->
          <div class="grid grid-cols-4 gap-2 mb-2">
            <button @click=${this.handleAddChild} class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-ibm-blue disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:text-gray-400 flex justify-center items-center" title="${canAddChild ? "Add Child" : "Cannot add child to Terminal/POS"}" ?disabled=${!canAddChild}><span class="material-symbols-outlined">add_circle</span></button>
            <button @click=${this.deleteSelected} ?disabled=${isOnlyChild} class="p-2 bg-white border border-gray-300 rounded hover:bg-red-50 text-red-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:text-gray-400 flex justify-center items-center" title="${isOnlyChild ? "Cannot delete: Parent would be empty" : "Delete Node"}"><span class="material-symbols-outlined">delete</span></button>
            <button @click=${() => this.handleReorder("left")} class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center" title="Move Left" ?disabled=${!canMoveLeft}><span class="material-symbols-outlined">arrow_back</span></button>
            <button @click=${() => this.handleReorder("right")} class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center" title="Move Right" ?disabled=${!canMoveRight}><span class="material-symbols-outlined">arrow_forward</span></button>
          </div>
        </div>
      </div>
    `;
  }

  override render() {
    try {
    return html`
      <div
        class="flex flex-col h-full w-full bg-base-light rounded-lg overflow-hidden border border-gray-200 shadow-sm"
      >
        <div class="flex flex-1 overflow-hidden relative min-h-0">
          <div class="flex-1 relative min-w-0">
            <div id="cy" class="absolute inset-0 bg-base-light bg-gray-50"></div>
          </div>

          <div
            class="w-80 bg-base-light-dim border-l border-gray-200 flex flex-col hidden md:flex shadow-inner"
          >
            <div class="p-4 border-b border-gray-200 bg-white/50">
                ${this.renderToolbar()}
            </div>
            <div class="flex-1 p-4 overflow-y-auto">
                ${this.renderNodeInspector()}
            </div>
            <div class="p-3 border-t border-gray-200 bg-white/50 min-h-[40px]">
                 <div class="rounded ${this.feedbackMsg ? "bg-blue-50 border border-blue-100 text-ibm-blue p-2" : ""} text-xs transition-all">
                    ${this.feedbackMsg}
                 </div>
            </div>
          </div>
        </div>
      </div>
    `;
    } catch (e) {
        console.error("GrammatomyEditor: Error in render()", e);
        return html`<div class="text-red-500 p-4">Render Error: ${e}</div>`;
    }
  }
}
