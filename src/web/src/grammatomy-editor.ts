import { LitElement, html, PropertyValueMap } from "lit";
import { customElement, query, state, property } from "lit/decorators.js";
import cytoscape from "cytoscape";
import {
  parsePtbToCytoscape,
  serializeCytoscapeToPtb,
  serializeNodeToPtb,
} from "./utils/ptb-utils";
// @ts-ignore
import dagre from "cytoscape-dagre";
import { SubTree } from "./types";
cytoscape.use(dagre);
import { GhostLogic } from "./lib/ghost-logic";

const KNOWN_POS_TAGS = new Set([
  "NOUN", "VERB", "DET", "ADJ", "ADV", "PRON", "ADP", "AUX", "CCONJ", "SCONJ", "NUM", "PART", "INTJ", "SYM", "PROPN",
  "n", "v", "d", "a", "r", "p", "c", "w", "z", "f", "i",
  "nc", "np", "aq", "rg", "rn"
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
  private readonly container!: HTMLElement;

  private cy!: cytoscape.Core;

  @property({ type: String })
  ptb: string = "";

  @property({ type: Array })
  subtrees: SubTree[] = [];

  @property({ type: Boolean })
  isMainTree: boolean = true;

  @property({ type: String })
  parentLabel: string = "";

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

  @state()
  private contextMenu: { open: boolean; x: number; y: number; target: any; type: 'node' | 'bg' } | null = null;

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
    globalThis.addEventListener('keydown', this.handleKeyDown);
  }

  override firstUpdated() {
    // Wait for the first render to complete
    this.updateComplete.then(() => {
        this.attemptInitialization();
    });
  }

  override updated(
    changedProperties: PropertyValueMap<any> | Map<PropertyKey, unknown>,
  ) {
    if (this.cy && changedProperties.has("ptb") && this.ptb) {
      this.loadPtb(this.ptb, true);
    }
    // Reload subtrees if they change externally (though usually editor generates them)
    if (changedProperties.has("subtrees")) {
        // Logic to display indicators for existing subtrees could go here
    }
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    this.resizeObserver?.disconnect();
    globalThis.removeEventListener('keydown', this.handleKeyDown);
  }

  private attemptInitialization() {
      if (this.cy) return;
      
      // Use the @query property which resolves to Shadow DOM
      let container = this.container;
      
      // REMOVED SELF-HEALING: Manual innerHTML injection destroys Lit's DOM tracking
      if (!container) {
          // If container is missing despite render(), we can't initialize Cytoscape yet.
          // We rely on Lit to render the structure defined in render().
          return;
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
            shape: "triangle",
            padding: "20px",
            "text-margin-y": "15px",
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
          selector: "node.link-node",
          style: {
            "background-color": "#0072B2", // Palette: Dark Blue (Freed up from Punctuation)
            "shape": "triangle",
            "color": "#FFFFFF",
            "border-color": "#000000",
            "border-width": 1,
            "font-weight": "bold",
            "font-family": "Roboto Mono",
            padding: "20px",
            "text-margin-y": "15px",
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

    // Navigation via Link Nodes (Manual Double Tap for robustness)
    let lastTapTime = 0;
    let lastTapTarget: string | null = null;

    this.cy.on("tap", "node.link-node", (evt) => {
      const node = evt.target;
      const currentTime = Date.now();
      const tapInterval = currentTime - lastTapTime;

      if (tapInterval < 500 && tapInterval > 0 && lastTapTarget === node.id()) {
          let label = node.data('label');
          if (label && label.toString().startsWith("LINK-")) {
              label = label.replace("LINK-", "");
          }

          this.dispatchEvent(new CustomEvent('request-navigation', {
            detail: { label: label || "UP" }, // Default to UP if label is empty/0
            bubbles: true,
            composed: true
          }));
          
          lastTapTime = 0;
          lastTapTarget = null;
      } else {
          lastTapTime = currentTime;
          lastTapTarget = node.id();
      }
    });

    // Context Menu (Right Click)
    this.cy.on("cxttap", (evt) => {
        const target = evt.target;
        const { x, y } = evt.renderedPosition;
        
        // Calculate screen coordinates for fixed positioning
        const rect = this.container.getBoundingClientRect();
        const menuX = rect.left + x;
        const menuY = rect.top + y;

        if (target === this.cy) {
            this.contextMenu = { open: true, x: menuX, y: menuY, target: null, type: 'bg' };
        } else if (target.isNode()) {
            this.contextMenu = { open: true, x: menuX, y: menuY, target: target, type: 'node' };
            this.selectNode(target); // Auto-select on right click for clarity
        }
    });
  }

  /**
   * Recalculates a global index for every node based on a Depth-First Search (DFS)
   * that respects the local sibling order. This ensures that layout algorithms
   * like Dagre preserve the linear reading order of the sentence.
   */
  private recalculateGlobalIndices() {
    const roots = this.cy.nodes().filter((n) => n.incomers().length === 0);
    // Sort roots by their local index (if forest) using toArray() to allow sort
    const rootsArray = roots.toArray().sort((a, b) => (a.data("index") ?? 0) - (b.data("index") ?? 0));

    let counter = 0;
    const traverse = (node: any) => {
      node.data("globalIndex", counter++);
      const children = node.outgoers("node").toArray().sort((a: any, b: any) => {
        return (a.data("index") ?? 0) - (b.data("index") ?? 0);
      });
      children.forEach((child: any) => traverse(child));
    };

    rootsArray.forEach((root) => traverse(root));
  }

  private readonly handleKeyDown = (e: KeyboardEvent) => {
    // Ignore if focus is on an input/textarea
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return;
    }

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      if (e.shiftKey) {
        this.redo();
      } else {
        this.undo();
      }
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') {
      e.preventDefault();
      this.redo();
    } else if ((e.ctrlKey || e.metaKey) && e.key === '0') {
      e.preventDefault();
      this.fit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      this.cancelCut();
      this.clearSelection();
    }
  }

  // --- Core Logic Methods ---

  private loadPtb(ptbString: string, fit: boolean = true) {
    if (!this.cy) return;

    this.clearSelection(); // Ensure panel is closed and state is clean
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

    // Visual Fix: Rename generic LINK-0 to specific parent label if available
    if (this.parentLabel) {
        const link0 = this.cy.nodes().filter((n: any) => n.data('label') === 'LINK-0');
        link0.data('label', `LINK-${this.parentLabel}`);
    }

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
      this.cy?.style().update(); // Force style refresh after batch validation
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
    const isLink = nodeElement.hasClass("link-node") || nodeData.label.startsWith("LINK-");

    // Reset any direct style overrides from previous validation
    nodeElement.removeStyle();
    nodeElement.incomers("edge").removeStyle();

    if ((isLeaf && !isGhost) || isLink) {
      return { isValid: true, errors: [], validTags: [], trace: [] };
    }

    const incomingEdges = nodeElement.incomers("edge");
    let parentTag: string | null = null;
    let isParentLink = false;
    if (incomingEdges.length > 0) {
      const source = incomingEdges.source();
      if (source && source.length > 0) {
        parentTag = source.data("label");
        if (source.hasClass("link-node") || parentTag?.startsWith("LINK-")) {
            isParentLink = true;
        }
      }
    }

    const childrenNodes = nodeElement.outgoers("node");
    const hasGhostChild = childrenNodes.some(
      (n) => n.data("isGhost") || n.data("label").includes("👻"),
    );
    const cleanChildrenLabels = childrenNodes
      .filter((n) => !n.data("isGhost") && !n.data("label").includes("👻"))
      .filter((n) => !n.hasClass("link-node") && !n.data("label").startsWith("LINK-"))
      .map((n) => n.data("label"));
    const descendantLabels = nodeElement
      .successors("node")
      .map((n) => n.data("label"));

    let localValidTags: string[] = [];
    let localErrors: string[] = [];
    let localTrace: string[] = [];
    let isContextValid = false;
    let isLaxValid = true;
    let isStrictValid = true;

    const isRoot = nodeData.label === "ROOT" && !parentTag;

    if (isParentLink) {
        isContextValid = true;
    } else {
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
            else if (!isGhost) {
                isContextValid = false;
                localErrors.push("Server error during context validation.");
            }
          }
        } catch (e) {
          console.error("Context validation failed", e);
          if (isRoot) isContextValid = true;
          else localErrors.push("Network error.");
        }
    }
    
    // DISABLED FOR TESTING LAX VALIDATION ISOLATION
    // if (!isContextValid) {
    //     localErrors.push(`Context Error: Tag '${nodeData.label}' is incompatible with parent '${parentTag || "ROOT"}'.`);
    //     // Apply direct style override for context error
    //     nodeElement.incomers("edge").style({
    //         "line-color": "#D55E00",
    //         "target-arrow-color": "#D55E00",
    //         "width": 3,
    //         "z-index": 9999 // Ensure it's drawn on top
    //     });
    // }

    if (!isContextValid) {
        localErrors.push(`Context Error: Tag '${nodeData.label}' is incompatible with parent '${parentTag || "ROOT"}'.`);
        // Apply direct style override for context error
        nodeElement.incomers("edge").style({
            "line-color": "#D55E00",
            "target-arrow-color": "#D55E00",
            "width": 3,
            "z-index": 9999 // Ensure it's drawn on top
        });
    }

    // 2. Strict Validation (Mild -> Red Edge) - MOVED UP
    try {
      const strictResponse = await fetch("/api/validation/check/requirements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tag: nodeData.label,
          children_tags: cleanChildrenLabels,
          descendant_tags: descendantLabels,
          strategy: "strict",
        }),
      });
      if (strictResponse.ok) {
        const res = await strictResponse.json();
        isStrictValid = res.allowed;
        if (res.trace) localTrace.push(...res.trace); // Keep strict trace for detail
        if (!isStrictValid) {
          if (!hasGhostChild) {
            localErrors.push(`[Strict] ${res.reason}`);
          } else {
            isStrictValid = true;
          }
        }
      }
    } catch (e) {
      console.error("Strict validation failed", e);
    }

    // 3. Lax Validation (Severe -> Hexagon) - MOVED DOWN
    try {
      const laxResponse = await fetch("/api/validation/check/requirements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tag: nodeData.label,
          children_tags: cleanChildrenLabels,
          descendant_tags: descendantLabels,
          strategy: "lax",
        }),
      });
      if (laxResponse.ok) {
        const res = await laxResponse.json();
        isLaxValid = res.allowed;
        // Only trace lax if it fails or if we want full verbosity
        if (!isLaxValid) {
          if (!hasGhostChild) {
            localErrors.push(`[Lax] ${res.reason}`);
            // Apply direct style override for lax error
            nodeElement.style({
                "background-color": "#D55E00",
                "color": "#F4F4F4",
                "shape": "hexagon",
            });
          } else {
            isLaxValid = true;
          }
        }
      }
    } catch (e) {
      console.error("Lax validation failed", e);
    }

    const isValid = isContextValid && isLaxValid && isStrictValid;
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
      this.cy.nodes().toArray().forEach((node: any) => {
        const isLeaf = node.outdegree(false) === 0;
        const label = node.data("label");
        
        if (label && label.toString().startsWith("LINK-")) {
            node.addClass("link-node");
            node.unselectify();
        }
        const isLink = node.hasClass("link-node");

        // Reset structural classes only, preserving validation state (error)
        node.removeClass("pos leaf punctuation ghost-node");

        if (label.includes("👻") || label.includes("ERR") || node.data('isGhost')) {
          if (label.includes("👻") || node.data('isGhost')) node.addClass("ghost-node");
          return;
        }

        const isPunctuation =
          /^[.,:;'"()[\]{}\-–—?!]+$/.test(label) ||
          ["fp", "fc", "fg", "fz", "fs", "fd", "punct"].includes(label.toLowerCase());

        if (isLeaf && !isLink) {
          node.addClass("leaf");
        } else {
          if (!isLink && (isPunctuation || KNOWN_POS_TAGS.has(label) || KNOWN_POS_TAGS.has(label.toUpperCase()))) {
            node.addClass("pos");
          }
        }

        if (isPunctuation) {
          node.addClass("punctuation");
        }
      });
    });
  }

  // --- Interaction Methods ---

  private async selectNode(node: any) {
    if (node.hasClass("link-node") || node.data("label").startsWith("LINK-")) {
        this.clearSelection();
        return;
    }

    this.cy.elements().removeClass("subtree-highlight");
    node.successors().addClass("subtree-highlight");

    this.selectedNode = node.data();
    this.pendingLabel = this.selectedNode.label;
    this.validationErrors = [];
    
    this.dispatchEvent(new CustomEvent('selection-changed', {
        detail: this.selectedNode,
        bubbles: true,
        composed: true
    }));

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

  public clearSelection() {
    this.cy.elements().removeClass("subtree-highlight");
    this.selectedNode = null;
    this.selectedNodeRule = {};
    this.validConversionTags = [];
    this.validationErrors = [];
    this.validationTrace = [];
    this.feedbackMsg = "";

    this.dispatchEvent(new CustomEvent('selection-changed', {
        detail: null,
        bubbles: true,
        composed: true
    }));

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
    const children = parent.outgoers("node").toArray().sort((a: any, b: any) => (a.data("index") ?? 0) - (b.data("index") ?? 0));
    
    if (children.length <= 1) return;

    // Normalize indices to 0, 1, 2... to prevent collisions/gaps
    children.forEach((child: any, i: number) => child.data("index", i));

    const currentIndex = children.findIndex((n: any) => n.id() === nodeToMove.id());
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
      /^[.,:;'"()[\]{}\-–—?!]+$/.test(label) || 
      ["fp", "fc", "fg", "fz", "fs", "fd", "punct", "PUNCT"].includes(label.toLowerCase());
    
    const isPos = KNOWN_POS_TAGS.has(label) || KNOWN_POS_TAGS.has(label.toUpperCase());

    // Calculate next index safely (max + 1) to avoid collisions with existing siblings
    const children = (this.cy.$id(this.selectedNode.id) as any).outgoers("node");
    let maxIndex = -1;
    children.toArray().forEach((child: any) => {
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
        const children = (this.cy.$id(this.selectedNode.id) as any).outgoers("node");
        children.forEach((child: any) => { if (child.data("index") === undefined) child.data("index", nextIndex); });
      }
    });

    this.recalculateGlobalIndices(); // New nodes added
    this.classifyNodes();
    this.runLayout(false);
    this.requestUpdate();
  }

  private reindexChildren(parentNode: any) {
    if (!parentNode || parentNode.empty()) return;
    
    const children = (parentNode.outgoers("node") as any).toArray().sort((a: any, b: any) => {
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

    if ((nodeElement as any).data("label") === "ROOT") {
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

  private async handleContextExport(format: string) {
      if (!this.contextMenu) return;
      
      let ptb = "";
      let filename = "tree";
      
      if (this.contextMenu.type === 'node' && this.contextMenu.target) {
          ptb = serializeNodeToPtb(this.contextMenu.target);
          const label = this.contextMenu.target.data('label') || 'node';
          filename = `subtree_${label.replace(/[^a-zA-Z0-9]/g, '_')}`;
      } else {
          ptb = this.getCurrentPtb();
          filename = "full_tree";
      }
      
      this.contextMenu = null; // Close menu
      this.requestUpdate();

      // Call API
      try {
          let endpoint = '/api/export/image';
          let isText = false;
          let ext = format;
          
          if (format === 'ascii') {
              endpoint = '/api/export/ascii';
              isText = true;
              ext = 'txt';
          } else if (format === 'latex') {
              endpoint = '/api/export/latex';
              isText = true;
              ext = 'tex';
          }

          const response = await fetch(endpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ptb, format })
          });

          if (!response.ok) throw new Error(await response.text());

          if (isText) {
              const text = await response.text();
              const blob = new Blob([text], { type: 'text/plain' });
              this.downloadBlob(blob, `.`);
          } else {
              const blob = await response.blob();
              this.downloadBlob(blob, `.`);
          }
          
          this.feedbackMsg = `Exported ${format.toUpperCase()} successfully.`;
      } catch (e) {
          console.error("Export failed:", e);
          this.feedbackMsg = "Export failed.";
      }
      this.requestUpdate();
  }

  private downloadBlob(blob: Blob, name: string) {
      const url = globalThis.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      globalThis.URL.revokeObjectURL(url);
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
    const elements = parsePtbToCytoscape(this.clipboard) as any[];
    
    // Find the root of the pasted tree (node with no source in the elements list)
    const targets = new Set(elements.filter((e: any) => 'source' in e.data).map((e: any) => e.data.target));
    const rootElement = elements.find((e: any) => !('source' in e.data) && !targets.has(e.data.id));
    
    if (!rootElement) {
        this.feedbackMsg = "Invalid clipboard content.";
        return;
    }

    // Generate unique IDs for pasted elements to avoid collisions
    const idMap = new Map<string, string>();
    const timestamp = Date.now();
    elements.forEach((el: any, i: number) => {
        const oldId = el.data.id;
        if (!('source' in el.data)) {
            const newId = `paste__`;
            idMap.set(oldId, newId);
            el.data.id = newId;
        }
    });

    // Update edges with new IDs
    elements.forEach((el: any) => {
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
                        data: { source: parent.id(), target: (rootElement as any).data.id }
                    });
                    // Assign index to new root
                    this.cy.$id((rootElement as any).data.id).data("index", ghostIndex);
                }
                
                // Remove ghost
                targetNode.remove();
                this.feedbackMsg = "Pasted: Replaced ghost node.";
            } else {
                // Append as last child
                const children = (targetNode as any).outgoers("node");
                let maxIndex = -1;
                children.toArray().forEach(child => {
                    const idx = child.data("index");
                    if (typeof idx === 'number' && idx > maxIndex) maxIndex = idx;
                });
                const nextIndex = maxIndex + 1;

                // Add new elements
                this.cy.add(elements);
                
                // Link target to new root
                this.cy.add({
                    group: "edges",
                    data: { source: targetNode.id(), target: (rootElement as any).data.id }
                });
                
                // Assign index
                this.cy.$id((rootElement as any).data.id).data("index", nextIndex);
                this.feedbackMsg = "Pasted: Appended as child.";
            }
        });

        this.classifyNodes();
        this.recalculateGlobalIndices(); // Topology changed (paste)
        this.runLayout(false);
        
        // Validate the modified branch
        const newRootId = (rootElement as any).data.id;
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

  public undo() {
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

  public redo() {
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

  public fit() {
    this.runLayout(true);
  }

  public focusNode(nodeId: string) {
    if (!this.cy) return;
    const node = this.cy.$id(nodeId);
    if (node.empty()) return;

    node.emit('tap'); // Trigger selection and inspector

    this.cy.animate({
      center: { eles: node },
      zoom: 1.5,
      duration: 800,
      easing: 'ease-in-out'
    });
  }

  public focusNodeByGlobalIndex(index: number) {
    if (!this.cy) return;
    const node = this.cy.nodes().filter((n: any) => n.data('globalIndex') === index);
    if (node.empty()) return;

    // Do not select (tap) to keep the inspector closed and view centered

    this.cy.animate({
      center: { eles: node },
      zoom: 1.5,
      duration: 800,
      easing: 'ease-in-out'
    });
  }

  public focusNodeByLabel(label: string) {
    if (!this.cy) return;
    const node = this.cy.nodes().filter((n: any) => n.data('label') === label);
    if (node.empty()) return;

    this.cy.animate({
      center: { eles: node },
      zoom: 1.5,
      duration: 800,
      easing: 'ease-in-out'
    });
  }

  public getSelectedNodeId(): string | null {
      return this.selectedNode ? this.selectedNode.id : null;
  }

  public executeDetach(nodeId: string, label: string): { mainPtb: string, fragmentPtb: string } | null {
      const node = this.cy.$id(nodeId);
      if (node.empty()) return null;

      // Strategy: Detach Content (Keep Container)
      // We keep the selected node in the main tree but move its children to the fragment.
      const children = node.outgoers().nodes().sort((a: any, b: any) => (a.data('index') || 0) - (b.data('index') || 0));
      
      if (children.length === 0) {
          return null; // Cannot detach empty node
      }

      // 1. Extract Content (Children)
      const contentPtb = children.map((child: any) => serializeNodeToPtb(child)).join(' ');
      const containerLabel = node.data('label');
      
      // 2. Construct Fragment PTB (Wrapper: ROOT -> LINK -> Content)
      // Strategy: Children Only. We do NOT duplicate the container.
      const fragmentPtb = `(ROOT LINK-${containerLabel} ${contentPtb})`;

      // 3. Replace in Main Graph (Surgery)
      this.cy.batch(() => {
          // Remove children edges (effectively removing children from this node)
          node.outgoers().remove();

          // Add Link Node as the ONLY child of the container
          const linkId = `link_${Date.now()}`;
          this.cy.add({
              group: 'nodes',
              data: { id: linkId, label: `LINK-${label}`, index: 0 },
              classes: 'link-node'
          });
          
          this.cy.add({
              group: 'edges',
              data: { source: node.id(), target: linkId }
          });
      });

      // 4. Serialize Modified Main Graph
      const mainPtb = this.getCurrentPtb();

      return { mainPtb, fragmentPtb };
  }

  public getDetachPayload(): { ptb: string, nodeIndex: number, label: string } | null {
      if (!this.selectedNode) return null;
      
      // Ensure global indices are up to date with current structure
      // (They should be, as they are updated on layout/modification)
      const globalIndex = this.selectedNode.globalIndex;
      const label = this.selectedNode.label;
      
      return { ptb: this.getCurrentPtb(), nodeIndex: globalIndex, label };
  }

  override render() {
    const isPanelOpen = !!this.selectedNode;

    return html`
      <div class="h-full w-full relative overflow-hidden bg-white">
        <!-- Cytoscape Container (Full Screen Layer) -->
        <div id="cy" class="absolute inset-0 z-0 bg-gray-50"></div>

        <!-- Inspector & Toolbar Overlay (Sliding Panel) -->
        <div 
            class="absolute top-0 right-0 h-full w-80 bg-white shadow-2xl border-l border-gray-200 z-20 flex flex-col transform transition-transform duration-300 ease-in-out ${isPanelOpen ? 'translate-x-0' : 'translate-x-full'}"
        >
            <!-- Inspector Content -->
            <div id="inspector-slot" class="flex-1 p-4 overflow-y-auto">
                ${this.renderNodeInspector()}
            </div>
        </div>
      </div>
    `;
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
          ${errors.map((e) => html`<li></li>`)}
        </ul>
        <div class="mt-2 pt-2 border-t border-red-200">
            <div class="font-bold text-red-800 mb-1 text-[10px] uppercase">Trace Log</div>
            <ul class="font-mono text-[10px] text-gray-600 space-y-1">
                ${trace.map(t => html`<li></li>`)}
            </ul>
        </div>
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
            <option value="" ?selected=${mark === this.pendingLabel}></option>
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
        ?disabled=
      >
        ${isGhostLeaf
          ? html`<option value="" disabled selected>Select tag...</option>`
          : html``}
        ${validTags.map(
          (tag) => html`
            <option value="" ?selected=${tag === this.pendingLabel}>
              
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

  private renderNodeInspector() {
    if (!this.selectedNode) {
      return html`
        <div class="h-full flex flex-col items-center justify-center text-gray-400 p-6 text-center">
          <span class="material-symbols-outlined text-4xl mb-2">touch_app</span>
          <p class="text-sm">Select a node to view properties and actions.</p>
        </div>
      `;
    }

    try {
    const nodeElement = this.cy.$id(this.selectedNode.id);
    const isLeaf =
      !(nodeElement as any).isParent() && nodeElement.outgoers().length === 0;
    const isPos = nodeElement.hasClass("pos");
    const isPunctuation = nodeElement.hasClass("punctuation");
    const isLink = nodeElement.hasClass("link-node");
    
    let isWordLeaf = false;
    let isPunctuationLeaf = false;
    
    if (isLeaf) {
      const incoming = nodeElement.incomers("edge");
      if (incoming.length > 0) {
        const parent = incoming.source();
        if (parent && parent.length > 0 && parent.hasClass("pos") && !parent.hasClass("punctuation")) isWordLeaf = true;
        if (parent && parent.length > 0 && parent.hasClass("punctuation")) isPunctuationLeaf = true;
      }
    }

    const isGhost = this.selectedNode.isGhost || this.selectedNode.label.includes("👻");
    const canEditLabel = !isLink;
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
    } else if (isLeaf) {
      headerBg = "#009E73";
      headerText = "#F4F4F4";
      typeLabel = "Terminal (Leaf)";
    } else if (isPos) {
      headerBg = "#56B4E9";
      headerText = "#161616";
      typeLabel = "Syntactic Category";
    } else if (isLink) {
      headerBg = "#0072B2";
      headerText = "#FFFFFF";
      typeLabel = "Subtree Link";
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
        const children = parent.outgoers("node").toArray().sort((a: any, b: any) => (a.data('index') ?? 0) - (b.data('index') ?? 0));
        const currentIndex = children.findIndex((n: any) => n.id() === nodeElement.id());
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
          style="background-color: ; color: ;"
        >
          <div
            class="text-[10px] uppercase tracking-widest opacity-80 font-bold"
          >
            
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
              ?disabled=
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
            <button @click=${this.deleteSelected} ?disabled= class="p-2 bg-white border border-gray-300 rounded hover:bg-red-50 text-red-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:text-gray-400 flex justify-center items-center" title="${isOnlyChild ? "Cannot delete: Parent would be empty" : "Delete Node"}"><span class="material-symbols-outlined">delete</span></button>
            <button @click=${() => this.handleReorder("left")} class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center" title="Move Left" ?disabled=${!canMoveLeft}><span class="material-symbols-outlined">arrow_back</span></button>
            <button @click=${() => this.handleReorder("right")} class="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center" title="Move Right" ?disabled=${!canMoveRight}><span class="material-symbols-outlined">arrow_forward</span></button>
          </div>
        </div>
      </div>
    `;
    } catch (e) {
        console.error("GrammatomyEditor: Error in render()", e);
        return html`<div class="text-red-500 p-4">Render Error: </div>`;
    }
  }
}