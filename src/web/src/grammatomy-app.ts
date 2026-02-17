import { LitElement, html } from 'lit';
import { customElement, state, query } from 'lit/decorators.js';
import cytoscape from 'cytoscape';
import './index.css';
import './grammatomy-editor'; // Ensure side-effect registration
import type { GrammatomyEditor } from './grammatomy-editor';
import { GrammatomyProject, TreeUnit } from './types';
import { parsePtbToCytoscape, serializeNodeToPtb } from './utils/ptb-utils';
import './grammatomy-notes';
import type { GrammatomyNotes } from './grammatomy-notes';

const PUNCTUATION_TAGS = new Set([
    ".", ",", ":", ";", "!", "?", "...", "-", "–", "—", "(", ")", "[", "]", "{", "}", "\"", "'", "«", "»", "¿", "¡",
    "fp", "fc", "fs", "fd", "fe", "fg", "fz", "fx", "ft", "fat", "fpt", "fit", "fia",
    "punct", "PUNCT", "SYM", "sym"
]);

@customElement('grammatomy-app')
export class GrammatomyApp extends LitElement {
  @query('grammatomy-editor')
  private readonly editor!: GrammatomyEditor;

  @query('grammatomy-notes')
  private readonly notesEditor!: GrammatomyNotes;

  @state()
  private project: GrammatomyProject | null = null;

  @state()
  private activeUnitId: string | null = null;

  @state()
  private activeSubtreeId: string | null = null; // null = Main Tree

  @state()
  private isLoading = false;

  @state()
  private isSidebarOpen = true;

  @state()
  private activeSidebarTab: 'tree' | 'search' = 'tree';

  // Note Editor State
  @state()
  private noteEditorState: {
      isOpen: boolean;
      targetType: 'project' | 'unit' | 'subtree';
      targetId: string;
      contextId?: string; // For subtree (unitId)
      title: string;
  } = { isOpen: false, targetType: 'project', targetId: '', title: '' };

  // Search State
  @state()
  private searchNodeTypes: string[] = [];
  @state()
  private selectedSearchType: string = "";
  @state()
  private searchRules: string[] = [];
  @state()
  private selectedSearchRule: string = "";
  @state()
  private searchResults: { unitId: string; subtreeId: string | null; nodeId: string; text: string; context: string }[] = [];

  @state()
  private showNewProjectModal = false;

  @state()
  private newProjectText = "";

  @state()
  private sidebarContextMenu: { open: boolean; x: number; y: number; unitId: string } | null = null;

  @state()
  private isProjectMenuOpen = false;

  @state()
  private isExportMenuOpen = false;

  @state()
  private selectedNodeLabel: string | null = null;

  @state()
  private isPendingRender = false;

  @state()
  private viewMode: 'edit' | 'master_map' = 'edit';

  @state()
  private masterTreeElements: any[] = [];

  @state()
  private masterFocusSelector: string = "";

  // Desactivamos Shadow DOM para usar Tailwind globalmente sin problemas
  override createRenderRoot() {
    return this;
  }

  override updated(changedProperties: any) {
      super.updated(changedProperties);
      if (this.isPendingRender) {
          this.isPendingRender = false;
      }
  }

  private openNoteEditor(type: 'project' | 'unit' | 'subtree', id: string, title: string, contextId?: string) {
      this.noteEditorState = {
          isOpen: true,
          targetType: type,
          targetId: id,
          contextId: contextId,
          title: title
      };
      this.isSidebarOpen = false; // Collapse sidebar to give space
      setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 350);
      
      // Force editor refresh and focus after transition
      setTimeout(() => {
          if (this.notesEditor) this.notesEditor.refresh();
      }, 400);
  }

  private closeNoteEditor() {
      this.noteEditorState = { ...this.noteEditorState, isOpen: false };
      setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 350);
  }

  private get currentNoteValue(): string {
      if (!this.project) return "";
      const { targetType, targetId, contextId } = this.noteEditorState;
      
      if (targetType === 'project') return this.project.notes || "";
      
      if (targetType === 'unit') {
          return this.project.units.find(u => u.id === targetId)?.notes || "";
      }
      
      if (targetType === 'subtree' && contextId) {
          const unit = this.project.units.find(u => u.id === contextId);
          return unit?.subtrees?.find(st => st.id === targetId)?.notes || "";
      }
      
      return "";
  }

  private cleanInputText(text: string): string {
    // 1. Split lines to handle line-start artifacts (line numbers)
    const lines = text.split(/\r?\n/);
    
    const cleanedLines: string[] = [];
    let previousLineEndsInPeriod = true;

    for (const rawLine of lines) {
        // Remove line numbers at start (e.g. "5   Text", "10\tText")
        let line = rawLine.replace(/^\s*\d+\s+/, '').trim();

        if (line.length === 0) continue;

        // Heuristic: If previous line didn't end in a period, and this one starts with Uppercase,
        // it's likely a continuation of the sentence broken by verse, so lowercase it.
        if (!previousLineEndsInPeriod && /^[A-ZÁÉÍÓÚÑ]/.test(line)) {
            line = line.charAt(0).toLowerCase() + line.slice(1);
        }

        previousLineEndsInPeriod = /[.?!»”"]$/.test(line);
        cleanedLines.push(line);
    }

    // 2. Join with spaces (replace line breaks)
    let content = cleanedLines.join(' ');

    // 3. Remove footnotes
    // Enclosed: [1], (1), {1}
    content = content.replace(/\[\d+\]/g, '');
    content = content.replace(/\(\d+\)/g, '');
    content = content.replace(/\{\d+}/g, '');

    // Attached suffix numbers (e.g. "word1", "word,2")
    // Match a non-digit/non-space char followed by digits
    // We replace "char+digits" with just "char"
    content = content.replace(/([^\d\s])\d+/g, '');

    // 4. Normalize whitespace
    return content.replace(/\s+/g, ' ').trim();
  }

  private openNewProjectModal() {
      this.newProjectText = "";
      this.showNewProjectModal = true;
  }

  private async createProject() {
    const text = this.newProjectText;
    if (!text) return;

    this.showNewProjectModal = false;

    this.isLoading = true;
    try {
        // Call the new unified endpoint
        const response = await fetch('/api/project/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                name: "New Project",
                lang: "es"
            })
        });

        if (!response.ok) throw new Error(await response.text());
        
        const projectData = await response.json();
        this.project = projectData;

        // Post-process units to calculate lineage for UI navigation
        if (this.project && this.project.units) {
            this.project.units.forEach(unit => {
                // Sanitize notes if needed (optional, backend usually handles this well now)
                if (unit.subtrees) {
                    unit.subtrees.forEach((st: any) => {
                        if (st.notes && st.notes.startsWith("Extracted from")) st.notes = "";
                    });
                }
                this.recalculateLineage(unit);
            });

            // Select first unit
            this.activeUnitId = this.project.units[0].id;
            this.requestUpdate();
        }

    } catch (e) {
        console.error("Project creation failed:", e);
        alert("Error creating project.");
    } finally {
        this.isLoading = false;
    }
  }

  private assignColorsTopologically(unit: TreeUnit) {
      if (!unit.subtrees) return;

      // 1. Build hierarchy map (Parent ID -> List of Children)
      const childrenMap = new Map<string | null, any[]>();
      unit.subtrees.forEach(st => {
          // Normalize parent_id: null if undefined or not found in subtrees (pointing to main)
          let pid: string | null = st.parent_subtree_id || null;
          // Verify parent exists in subtrees list, otherwise it's Main (null)
          if (pid && !unit.subtrees!.some(s => s.id === pid)) pid = null;
          
          if (!childrenMap.has(pid)) childrenMap.set(pid, []);
          childrenMap.get(pid).push(st);
      });

      // 2. Process queue (BFS)
      // Start with Main Tree children (pid = null)
      // Parent color for Main Tree is 0 (Vermilion)
      const queue: { parentId: string | null, parentColor: number }[] = [];
      queue.push({ parentId: null, parentColor: 0 });

      while (queue.length > 0) {
          const { parentId, parentColor } = queue.shift()!;
          const children = childrenMap.get(parentId) || [];
          
          // Sort children deterministically by label (A, B, C...) to ensure stable colors
          children.sort((a: any, b: any) => a.label.localeCompare(b.label));

          // Available colors excluding parent
          // Colors: 0=Vermilion, 1=Orange, 2=SkyBlue, 3=Blue
          const allColors = [0, 1, 2, 3];
          const availableColors = allColors.filter(c => c !== parentColor);

          children.forEach((child: any, index: number) => {
              // Assign color
              child.colorIndex = availableColors[index % availableColors.length];
              
              // Add to queue to process its children
              queue.push({ parentId: child.id, parentColor: child.colorIndex });
          });
      }
  }

  private handleFragmentation(e: CustomEvent) {
      const { ptb, subtrees } = e.detail;
      
      // Safety check: Fragmentation operations should only affect the main tree structure
      if (this.activeSubtreeId) return;

      if (this.activeUnitId && this.project) {
          const idx = this.project.units.findIndex(u => u.id === this.activeUnitId);
          if (idx !== -1) {
              const unit = this.project.units[idx];
              unit.current_ptb = ptb;
              unit.subtrees = subtrees;
              this.recalculateLineage(unit); // Calculate parents first
              
              // Assign colors topologically (Top-Down)
              this.assignColorsTopologically(unit);
              this.requestUpdate();
              console.log("Project updated with fragments:", unit);
          }
      }
  }

  private handleNoteChange(e: CustomEvent) {
      const content = e.detail;
      if (!this.project) return;
      const { targetType, targetId, contextId } = this.noteEditorState;

      if (targetType === 'project') {
          this.project.notes = content;
      } else if (targetType === 'unit') {
          const unit = this.project.units.find(u => u.id === targetId);
          if (unit) unit.notes = content;
      } else if (targetType === 'subtree' && contextId) {
          const unit = this.project.units.find(u => u.id === contextId);
          const subtree = unit?.subtrees?.find(st => st.id === targetId);
          if (subtree) subtree.notes = content;
      }
      this.requestUpdate(); // Force update to reflect icon changes
  }

  private async handleManualDetach() {
      if (!this.activeUnitId || !this.project || !this.editor) return;
      
      const payload = this.editor.getDetachPayload();
      if (!payload) {
          alert("Please select a node to detach.");
          return;
      }

      // Generate a new label (e.g. next available letter)
      const existingLabels = new Set(this.activeUnit?.subtrees?.map(st => st.label) || []);
      const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
      let newLabel = "A";
      for (let i = 0; i < alphabet.length; i++) {
          if (!existingLabels.has(alphabet[i])) {
              newLabel = alphabet[i];
              break;
          }
      }
      // Fallback for exhaustion
      if (existingLabels.has(newLabel)) newLabel = `Z${existingLabels.size}`;

      this.isLoading = true;
      try {
          const response = await fetch('/api/mutation/detach', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  main_ptb: payload.ptb,
                  node_path: payload.nodePath,
                  fragment_label: newLabel,
                  parent_context_label: this.activeParentLabel,
                  target_label: payload.label
              })
          });

          if (!response.ok) throw new Error(await response.text());
          const data = await response.json();

          // Update State
          this.updateTreeWithFragment(data.main_ptb, data.fragment_ptb, newLabel);
          
          console.log(`Detached node '${payload.label}' into Fragment `);

          // Integrity Check Feedback (Debug Mode)
          if (data.integrity_check) {
              const check = data.integrity_check;
              if (check.status === 'passed') {
                  alert(`✅ Integrity Check Passed\n\nThe detach operation was verified as fully reversible.`);
              } else if (check.status === 'failed') {
                  alert(`⚠️ Integrity Check Failed\n\nDifferences found:\n${check.diffs.slice(0, 5).join('\n')}`);
              } else if (check.status === 'error') {
                  alert(`⚠️ Integrity Check Crashed\n\nError: ${check.message}`);
              }
          }

      } catch (e) {
          console.error("Detach failed:", e);
          alert("Failed to detach node. See console.");
      } finally {
          this.isLoading = false;
      }
  }

  private async handleFragmentRequest() {
      if (!this.activeUnitId || !this.project) return;
      
      const unit = this.activeUnit;
      if (!unit) return;
      this.saveCurrentEditorState();

      this.isLoading = true;
      try {
          console.log(`[handleFragmentRequest] Starting fragmentation for unit ${this.activeUnitId}`);
          console.log(`  Input PTB length: ${unit.current_ptb.length}`);
          
          const response = await fetch('/api/tools/fragment', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  ptb: unit.current_ptb
              })
          });

          if (!response.ok) throw new Error(await response.text());
          const data = await response.json();

          // Log fragmentation results
          console.log(`[handleFragmentRequest] Fragmentation successful:`);
          console.log(`  main_ptb length: ${data.main_ptb.length}`);
          console.log(`  subtrees created: ${data.subtrees.length}`);
          
          // Temporary assignment for logging (will be recalculated properly with lineage)
          data.subtrees.forEach((st: any, idx: number) => {
              // We can't assign smart colors yet because we don't have lineage.
              // We'll do it after updating the project unit.
              st.colorIndex = 0; 

              const linkMatches = st.ptb.match(/LINK-\w+(-\w+)?/g) || [];
              console.log(`    [] label=${st.label}, ptb_len=${st.ptb.length}, links=${linkMatches.join(', ')}`);
          });
          
          const mainLinks = data.main_ptb.match(/LINK-\w+(-\w+)?/g) || [];
          console.log(`  main_ptb LINK nodes: ${mainLinks.join(', ')}`);

          // Update state
          const idx = this.project.units.findIndex(u => u.id === this.activeUnitId);
          if (idx !== -1) {
              console.log(`[handleFragmentRequest] Saving main_ptb to unit (${data.main_ptb.length} chars)`);
              this.project.units[idx].current_ptb = data.main_ptb;
              this.project.units[idx].subtrees = data.subtrees;
              
              // Calculate Lineage & Assign Smart Colors
              this.recalculateLineage(this.project.units[idx]);
              this.assignColorsTopologically(this.project.units[idx]);
              
              // Verify that main_ptb was actually saved
              const savedMainPtb = this.project.units[idx].current_ptb;
              const savedLinks = savedMainPtb.match(/LINK-\w+(-\w+)?/g) || [];
              console.log(`[handleFragmentRequest] After saving, main_ptb contains: ${savedLinks.join(', ')}`);
              
              this.requestUpdate();
              console.log("Fragmentation state updated successfully.");

              // Integrity Check Feedback (Debug Mode)
              if (data.integrity_check) {
                  const check = data.integrity_check;
                  if (check.status === 'passed') {
                      alert(`✅ Integrity Check Passed\n\nFragmentation verified: Master Map matches original.`);
                  } else if (check.status === 'failed') {
                      alert(`⚠️ Integrity Check Failed\n\nDifferences found:\n${check.diffs.slice(0, 5).join('\n')}`);
                  } else if (check.status === 'error') {
                      alert(`⚠️ Integrity Check Crashed\n\nError: ${check.message}`);
                  }
              }
          }
      } catch (e) {
          console.error("Fragmentation failed:", e);
          alert("Fragmentation failed.");
      } finally {
          this.isLoading = false;
      }
  }

  private updateTreeWithFragment(newMainPtb: string, fragmentPtb: string, label: string) {
      if (!this.activeUnit) return;

      // 1. Update the container (Main or Subtree)
      if (this.activeSubtreeId) {
          const st = this.activeUnit.subtrees?.find(s => s.id === this.activeSubtreeId);
          if (st) st.ptb = newMainPtb;
      } else {
          this.activeUnit.current_ptb = newMainPtb;
      }

      // 2. Add the new fragment
      const newSubtree = {
          id: `st_${Date.now()}`,
          label: label,
          ptb: fragmentPtb,
          notes: "",
          parent_subtree_id: this.activeSubtreeId || null, // Link to current view
          colorIndex: 0 // Placeholder, will be fixed by topological assignment
      };

      if (!this.activeUnit.subtrees) this.activeUnit.subtrees = [];
      this.activeUnit.subtrees.push(newSubtree);

      this.recalculateLineage(this.activeUnit);
      this.assignColorsTopologically(this.activeUnit);
      if (this.viewMode === 'master_map') this.buildMasterTree(); // Refresh map if open
      this.requestUpdate();
  }

  private async handleReabsorb(e: Event, subtreeId: string) {
      e.stopPropagation();
      if (!this.activeUnit || !this.activeUnit.subtrees) return;

      console.log(`handleReabsorb: called for subtreeId `);

      if (!this.editor) {
          console.error("handleReabsorb: Editor is null!");
          return; // Abort if editor is not ready. This is critical.
      }
      if (this.isPendingRender) {
          console.warn("Reabsorb blocked: Pending render.");
          return;
      }

      // 0. Save state immediately to capture pending edits and prevent overwriting later
      this.saveCurrentEditorState();
      console.log("handleReabsorb: Editor state saved.");

      const unit = this.activeUnit;
      const subtreeIndex = unit.subtrees.findIndex(st => st.id === subtreeId);
      if (subtreeIndex === -1) return;

      const subtree = unit.subtrees[subtreeIndex];
      const parentId = subtree.parent_subtree_id;

      // 1. Identify Parent Object (Main Unit or another Subtree)
      let parentObj: any = null;
      if (parentId === null || parentId === undefined) {
          parentObj = unit; // Main Tree
      } else {
          parentObj = unit.subtrees.find(st => st.id === parentId);
      }

      if (!parentObj) return;

      // 2. Merge Notes (Preservation)
      if (subtree.notes) {
          const header = `\n\n## Merged Fragment ${subtree.label}\n`;
          parentObj.notes = (parentObj.notes || "") + header + subtree.notes;
      }

      // 3. Merge PTB (Server-Side Structural Reabsorption)
      this.isLoading = true;
      try {
          // Diagnostic logging
          const mainPtb = parentObj.current_ptb || parentObj.ptb || "";
          const fragmentPtb = subtree.ptb;
          const linkLabel = subtree.label;
          
          console.log(`[handleReabsorb] Attempting reabsorb:`);
          console.log(`  subtree.label: `);
          console.log(`  parent type: ${parentId === null ? 'Main' : 'Subtree'}`);
          console.log(`  main_ptb length: ${mainPtb.length}`);
          console.log(`  main_ptb snippet: ${mainPtb.substring(0, 200)}...`);
          console.log(`  fragment_ptb length: ${fragmentPtb.length}`);
          console.log(`  fragment_ptb snippet: ${fragmentPtb.substring(0, 200)}...`);
          
          // Check for LINK nodes in main
          const linkMatches = mainPtb.match(/LINK-\w+(-\w+)?/g) || [];
          console.log(`  LINK nodes in main: ${linkMatches.join(', ')}`);
          
          const response = await fetch('/api/mutation/reabsorb', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  main_ptb: mainPtb,
                  fragment_ptb: fragmentPtb,
                  link_label: linkLabel
              })
          });

          if (!response.ok) throw new Error(await response.text());
          const data = await response.json();
          console.log("Reabsorb API response:", data);

          // Update Parent with new PTB
          if ('current_ptb' in parentObj) parentObj.current_ptb = data.ptb;
          else parentObj.ptb = data.ptb;

          // 4. Remove Subtree & Update
          unit.subtrees.splice(subtreeIndex, 1);
          this.recalculateLineage(unit);

          // 5. Navigate to Parent
          // Only navigate if we are not already in the target view to avoid saving stale state
          console.log("handleReabsorb: Navigating to parent (pending render).");
          this.isPendingRender = true;
          const targetIsMain = (parentId === null || parentId === undefined);
          
          if (targetIsMain) {
              if (this.activeSubtreeId !== null) this.navigateToMain();
          } else {
              if (this.activeSubtreeId !== parentId && parentId !== undefined) {
                  this.navigateToSubtree(parentId);
              }
          }
          this.requestUpdate();
          
          // Wait for the view to catch up with the model before unblocking UI
          await this.updateComplete;
          if (this.editor) {
              console.log("handleReabsorb: Awaiting editor updateComplete.");
              await this.editor.updateComplete;
          }

          // 6. Focus the reabsorbed node (Wait for render)
          if (data.focus_index !== undefined && data.focus_index !== -1) {
              await this.updateComplete;
              if (this.editor) this.editor.focusNodeByGlobalIndex(data.focus_index);
          }

      } catch (e) {
          console.error("Reabsorb failed:", e);
          alert("Failed to reabsorb fragment. See console.");
          // Make sure isLoading is cleared even on failure
      } finally {
          this.isLoading = false;
      }
  }

  private buildMasterTree() {
      if (!this.activeUnit) return;
      
      // 1. Start with Main Tree elements
      let elements = parsePtbToCytoscape(this.activeUnit.current_ptb);
      
      // Prefix IDs to avoid collisions and tag with source
      elements.forEach((el: any) => {
          if (el.data.id) el.data.id = 'main_' + el.data.id;
          if (el.data.source) el.data.source = 'main_' + el.data.source;
          if (el.data.target) el.data.target = 'main_' + el.data.target;
          if (!('source' in el.data)) {
              el.data.subtreeId = 'main'; // Explicit ID for selector
              // Apply Main Tree Color (0 = Vermilion) to Master Map elements
              (el as any).classes = ((el as any).classes ? (el as any).classes + " " : "") + `subtree-color-0`;
          }
      });

      // 2. Iteratively resolve LINKs
      let linksFound = true;
      let iterations = 0;
      const maxIterations = 50; // Safety break
      const processedLinkIds = new Set<string>(); // Track processed links to avoid loops

      while (linksFound && iterations < maxIterations) {
          linksFound = false;
          iterations++;

          // Find a LINK node in the current graph that hasn't been processed
          const linkNode = elements.find((el: any) => 
              !('source' in el.data) && el.data.label && el.data.label.toString().startsWith('LINK-') && !processedLinkIds.has(el.data.id)
          );
          
          if (linkNode) {
              const labelParts = linkNode.data.label.toString().split('-');
              // LINK-A-uid -> A
              const label = labelParts.length >= 2 ? labelParts[1] : linkNode.data.label.replace('LINK-', '');
              
              const subtree = this.activeUnit.subtrees?.find(st => st.label === label);
              
              if (subtree) {
                  // Ensure color index exists (fallback for legacy data)
                  if (subtree.colorIndex === undefined) {
                      // Fallback: simple cycle if we can't determine sequence easily
                      subtree.colorIndex = (this.activeUnit.subtrees?.indexOf(subtree) || 0) % 4;
                  }
                  const colorIndex = subtree.colorIndex;
                  processedLinkIds.add(linkNode.data.id); // Mark as processed

                  // Parse Subtree
                  const stElements = parsePtbToCytoscape(subtree.ptb);
                  const prefix = `st_${subtree.id}_`;
                  
                  stElements.forEach((el: any) => {
                      if (el.data.id) el.data.id = prefix + el.data.id;
                      if (el.data.source) el.data.source = prefix + el.data.source;
                      if (el.data.target) el.data.target = prefix + el.data.target;
                      if (!('source' in el.data)) {
                          el.data.subtreeId = subtree.id;
                          // Add color class
                          (el as any).classes = ((el as any).classes ? (el as any).classes + " " : "") + `subtree-color-${colorIndex}`;
                      }
                  });

                  // Find graft point (Incoming edge to LINK node)
                  const incomingEdge = elements.find((el: any) => 'source' in el.data && el.data.target === linkNode.data.id);
                  
                  // Find Subtree Content Root (The child of the LINK-Parent wrapper)
                  // Subtree PTB: (LINK-Parent (S ...)) -> Root is LINK-Parent
                  const stRoots = stElements.filter((el: any) => !('source' in el.data) && !stElements.some((e: any) => 'source' in e.data && e.data.target === el.data.id));
                  const stRoot = stRoots[0];

                  if (stRoot) {
                      // Get children of the wrapper root
                      const childrenEdges = stElements.filter((el: any) => 'source' in el.data && el.data.source === stRoot.data.id);
                      let nodesToConnect = childrenEdges.map((el: any) => el.data.target);

                      // KEEP LINK node and incoming edge.
                      // Style the link node as a "Master Link" (Ghostly bridge)
                      linkNode.classes = (linkNode.classes || "") + " master-link";

                      // Add subtree elements (excluding the wrapper root and its outgoing edges)
                      let stContent = stElements.filter((el: any) => el.data.id !== stRoot.data.id && el.data.source !== stRoot.data.id);
                      
                      // Note: We removed the duplication check (unwrap) logic here.
                      // In Master Map with explicit LINK nodes, we want to see the full structure:
                      // Parent -> LINK -> Child. Even if Parent and Child are both 'S', the LINK separates them visually.

                      elements = elements.concat(stContent);

                      // Connect LINK node to subtree content roots
                      if (linkNode) {
                          nodesToConnect.forEach((childId: any) => {
                              elements.push({
                                  data: { source: linkNode.data.id, target: childId }
                              });
                          });
                      }
                      linksFound = true; // We modified the graph, check again for nested links
                  } else {
                      // Malformed subtree? Just remove the link to avoid loop
                      elements = elements.filter((el: any) => el.data.id !== linkNode.data.id);
                  }
              } else {
                  // Subtree not found (maybe deleted?), mark as resolved to stop loop
                  processedLinkIds.add(linkNode.data.id);
                  linkNode.data.label = "MISSING-" + label;
              }
          }
      }
      
      this.masterTreeElements = elements;
  }

  private handleMasterMapToggle() {
      if (this.viewMode === 'edit') {
          this.toggleMasterView();
      } else {
          this.viewMode = 'edit';
          setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 50);
      }
  }

  private toggleMasterView() {
      // Save any pending changes from the current editable view before switching
      this.saveCurrentEditorState();
      
      // Determine focus target for the transition (Where are we coming from?)
      if (this.activeSubtreeId) {
          // Coming from a subtree: Focus on its nodes in the Master Map
          this.masterFocusSelector = `[subtreeId = "${this.activeSubtreeId}"]`;
      } else {
          // Coming from Main Tree: Focus on main nodes
          this.masterFocusSelector = `[subtreeId = "main"]`;
      }

      // 1. Switch to Master Map mode
      // This triggers the Editor's 'updated' lifecycle, which:
      // a) Takes a snapshot of the current view (Sidebar OPEN)
      // b) Loads the Master Tree elements
      // c) Animates the layout (Zoom Out) over 1200ms
      this.viewMode = 'master_map';
      this.buildMasterTree();
      
      // 2. Wait for the transition to finish BEFORE closing the sidebar.
      // This ensures the snapshot overlay matches the container size throughout the cross-fade.
      setTimeout(() => {
          this.isSidebarOpen = false; // Collapse sidebar
          
          // 3. After sidebar animation (300ms), trigger resize to fill the screen
          setTimeout(() => {
              globalThis.dispatchEvent(new Event('resize'));
          }, 350);
      }, 1250); // 1200ms transition + buffer

      // Integrity Check disabled for Master Map with explicit LINK nodes.
      // The visual structure (with LINKs) intentionally differs from the logical defragmented tree (without LINKs).
  }

  private async verifyMasterMapIntegrity(unit: TreeUnit) {
      // Only run if we have original data to compare against
      if (!unit.original_ptb) return;

      try {
          const response = await fetch('/api/tools/defragment', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  main_ptb: unit.current_ptb,
                  subtrees: unit.subtrees || [],
                  reference_ptb: unit.original_ptb
              })
          });

          if (response.ok) {
              const data = await response.json();
              if (data.integrity_check) {
                  const check = data.integrity_check;
                  setTimeout(() => {
                      if (check.status === 'passed') alert(`✅ Master Map Integrity Verified\n\nReconstructed tree matches original source.`);
                      else if (check.status === 'failed') alert(`⚠️ Master Map Divergence\n\nCurrent tree differs from original source.\n(This is expected if you have made edits)\n\nDiffs:\n${check.diffs.slice(0, 5).join('\n')}`);
                  }, 600); // Wait for transition animation
              }
          }
      } catch (e) {
          console.error("Integrity check failed:", e);
      }
  }

  private handleRequestNavigation(e: CustomEvent) {
      const { label } = e.detail;
      console.log("GrammatomyApp: Navigation requested to label:", label);
      if (!this.activeUnit) return;
      
      // Find subtree by label (e.g., "A")
      const subtree = this.activeUnit.subtrees?.find(st => st.label === label);
      if (subtree) {
          this.navigateToSubtree(subtree.id);
      } else {
          // If not a known child subtree, assume it's a back-link to parent
          this.navigateToParent();
      }
  }

  private handleMasterNodeDblClick(e: CustomEvent) {
      const nodeData = e.detail;
      let subtreeId = nodeData.subtreeId;
      
      // Intelligent Navigation:
      // If the user double-clicks a LINK node (e.g. LINK-F) inside Tree E,
      // they expect to go to Tree F, not Tree E.
      if (nodeData.label && nodeData.label.toString().startsWith('LINK-')) {
          const labelParts = nodeData.label.toString().split('-');
          // LINK-Label-ID -> Label
          const targetLabel = labelParts.length >= 2 ? labelParts[1] : nodeData.label.replace('LINK-', '');
          const targetSubtree = this.activeUnit?.subtrees?.find(st => st.label === targetLabel);
          if (targetSubtree) {
              subtreeId = targetSubtree.id;
          }
      }

      // 1. Zoom into the clicked node in Master Map (Visual Feedback)
      if (this.editor) {
          // We can't easily get the node object from here without querying cy, 
          // but we can assume the user just clicked it, so it's centered or we can animate zoom.
          // For simplicity, let's just switch view mode which triggers a layout animation in the editor.
          
          console.log("MasterMap: Navigate to", subtreeId, "node", nodeData.label);
          
          this.viewMode = 'edit';
          if (subtreeId) {
              this.navigateToSubtree(subtreeId);
          } else {
              this.navigateToMain();
          }
          
          // The editor will auto-fit on load. 
          // To make it "zoom to node", we would need to pass the target node ID to the editor
          // and have it focus on it after layout.
      }

      // TODO: Focus specific node (requires mapping ID back to original, which is tricky due to prefixing)
  }

  private navigateToParent() {
      if (!this.activeSubtreeId || !this.activeUnit) return;
      
      const currentSubtree = this.activeUnit.subtrees?.find(st => st.id === this.activeSubtreeId);
      
      // 1. Fast Path: Use explicit parent pointer if available
      if (currentSubtree && currentSubtree.parent_subtree_id !== undefined) {
          const targetLabel = `LINK-${currentSubtree.label}`;

          if (currentSubtree.parent_subtree_id === null) {
              this.navigateToMain();
          } else {
              this.navigateToSubtree(currentSubtree.parent_subtree_id);
          }
          
          // Focus the link node in the parent tree (The "Triangle with my name")
          setTimeout(() => {
              if (this.editor) {
                  this.editor.focusNodeByLabel(targetLabel);
              }
          }, 300);
          return;
      }

      // 2. Fallback: Search (Legacy/Safety)
      if (!currentSubtree) { 
          this.navigateToMain();
          return;
      }
      const linkTag = `LINK-${currentSubtree.label}`;
      if (this.activeUnit.current_ptb.includes(linkTag)) {
          this.navigateToMain();
      } else {
          const parentSubtree = this.activeUnit.subtrees?.find(st => st.ptb.includes(linkTag));
          if (parentSubtree) {
              this.navigateToSubtree(parentSubtree.id);
          } else {
              this.navigateToMain();
          }
      }
  }

  private recalculateLineage(unit: TreeUnit) {
      if (!unit.subtrees) return;
      
      const labelToSubtree = new Map<string, any>();
      unit.subtrees.forEach(st => {
          st.parent_subtree_id = undefined; // Reset to ensure clean state
          labelToSubtree.set(st.label, st);
      });
      
      // Helper to extract label from LINK string
      const extractLabel = (s: string) => {
          const parts = s.split('-');
          // parts[0] is "LINK", parts[1] is Label (e.g. "A"), parts[2+] is ID
          if (parts.length >= 2) return parts[1];
          return s.replace('LINK-', '');
      };

      // Helper to find links in a PTB string
      const findLinks = (ptb: string, isSubtree: boolean) => {
          const allLinks = (ptb.match(/LINK-([^\s\)]+)/g) || []);
          // For subtrees, the first LINK node is the Root (Back-link to parent).
          // We must exclude it to avoid circular lineage (Child thinking it is parent of Parent).
          const childLinks = isSubtree ? allLinks.slice(1) : allLinks;
          
          return childLinks.map(extractLabel);
      };

      // 1. Main Tree Children
      findLinks(unit.current_ptb, false).forEach(label => { 
          const st = labelToSubtree.get(label); 
          if(st) st.parent_subtree_id = null; 
      });

      // 2. Subtree Children (Recursive)
      unit.subtrees.forEach(parent => {
          findLinks(parent.ptb, true).forEach(label => { 
              const st = labelToSubtree.get(label); 
              if(st) st.parent_subtree_id = parent.id; 
          });
      });
  }

  private async parseActiveUnit() {
      if (!this.activeUnitId || !this.project) return;
      
      const unitIndex = this.project.units.findIndex(u => u.id === this.activeUnitId);
      if (unitIndex === -1) return;
      
      const unit = this.project.units[unitIndex];
      
      // If already parsed, don't re-parse
      if (unit.current_ptb) return;

      this.isLoading = true;
      try {
        const response = await fetch('/api/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: unit.sentence,
                engine: 'stanza',
                lang: 'es'
            })
        });

        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        
        if (data.ptb) {
            // Update project state
            const updatedUnits = [...this.project.units];
            updatedUnits[unitIndex] = {
                ...unit,
                original_ptb: data.ptb,
                current_ptb: data.ptb
            };
            this.project = { ...this.project, units: updatedUnits };
        }
      } catch (e) {
          console.error("Parse error:", e);
      } finally {
          this.isLoading = false;
      }
  }

  private saveCurrentEditorState() {
      if (!this.activeUnitId || !this.project || !this.editor) return;

      // FIX: Do not save state if the editor is in read-only mode (i.e., Master Map).
      // This is more robust than checking `this.viewMode`, which can change just before this call,
      // causing a race condition where the master map content overwrites the real tree.
      if (this.editor.readOnly) {
          console.log("saveCurrentEditorState: Aborted (editor is read-only).");
          return;
      }
      
      console.log("saveCurrentEditorState: called.");
      if (this.isPendingRender) {
          console.warn("Skipping save: Model is ahead of View (Pending Render)");
          return;
      }

      const currentPtb = this.editor.getCurrentPtb();
      const unitIndex = this.project.units.findIndex(u => u.id === this.activeUnitId);
      if (unitIndex === -1) return;

      if (this.activeSubtreeId) {
          // IMPORTANT: Save ONLY to the subtree, NEVER overwrite the main unit's current_ptb
          // The main unit's current_ptb contains LINK nodes that reference all subtrees.
          // Overwriting it would corrupt the fragmentation structure.
          const unit = this.project.units[unitIndex];
          if (unit.subtrees) {
              const stIndex = unit.subtrees.findIndex(st => st.id === this.activeSubtreeId);
              if (stIndex !== -1) {
                  unit.subtrees[stIndex].ptb = currentPtb;
                  console.log(`  Saved subtree ${this.activeSubtreeId} (${currentPtb.length} chars)`);
              }
          }
      } else {
          // Save to main unit (only when viewing main, not when viewing subtrees)
          console.log(`  Saving main unit current_ptb (${currentPtb.length} chars)`);
          this.project.units[unitIndex].current_ptb = currentPtb;
      }
  }

  private handleSelectionChanged(e: CustomEvent) {
      const node = e.detail;
      this.selectedNodeLabel = node ? node.label : null;
  }

  private navigateToMain() {
      this.saveCurrentEditorState();
      this.activeSubtreeId = null;
      this.viewMode = 'edit';
      setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 50);
  }

  private navigateToSubtree(subtreeId: string) {
      this.saveCurrentEditorState();
      this.activeSubtreeId = subtreeId;
      setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 50);
      this.viewMode = 'edit';
  }

  private async selectUnit(unitId: string) {
      if (this.activeUnitId === unitId) return;

      // 1. Save current work (wherever we are)
      this.saveCurrentEditorState();

      // 2. Switch
      this.activeUnitId = unitId;
      this.activeSubtreeId = null; // Reset to main tree of new unit
      this.viewMode = 'edit';
      
      // 3. Parse if needed
      await this.parseActiveUnit();

      // Force resize event for Cytoscape
      setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 50);
  }

  private handleExport() {
      if (!this.project) return;
      
      // Ensure current state is saved
      this.saveCurrentEditorState();
      
      const data = JSON.stringify(this.project, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = globalThis.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `${this.project.meta.name.replace(/\s+/g, '_')}.gmy`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      globalThis.URL.revokeObjectURL(url);
  }

  private async handleExportImage(format: 'png' | 'svg') {
      if (!this.activeUnitId || !this.project) return;
      
      // Ensure current state is saved
      this.saveCurrentEditorState();
      
      const ptbToRender = this.currentPtbToDisplay;
      if (!ptbToRender) return;

      this.isLoading = true;
      try {
          const response = await fetch('/api/export/image', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  ptb: ptbToRender,
                  format: format
              })
          });

          if (!response.ok) throw new Error(await response.text());
          
          const blob = await response.blob();
          const url = globalThis.URL.createObjectURL(blob);
          
          const a = document.createElement('a');
          a.href = url;
          const name = this.activeSubtreeId 
            ? `${this.project.meta.name}_${this.activeUnitId}_${this.activeSubtreeId}.`
            : `${this.project.meta.name}_${this.activeUnitId}.`;
            
          a.download = name;
          document.body.appendChild(a);
          a.click();
          a.remove();
          globalThis.URL.revokeObjectURL(url);

      } catch (e) {
          console.error("Export image failed:", e);
          alert("Export image failed.");
      } finally {
          this.isLoading = false;
      }
  }

  private handleSidebarContextMenu(e: MouseEvent, unitId: string) {
      e.preventDefault();
      this.sidebarContextMenu = {
          open: true,
          x: e.clientX,
          y: e.clientY,
          unitId: unitId
      };
  }

  private async handleSidebarExport(format: string) {
      if (!this.project) return;

      // If called from a sidebar row context menu, use that unit. Otherwise
      // allow certain global exports (e.g., PTB) to operate on the active unit.
      let unit: TreeUnit | undefined;
      if (this.sidebarContextMenu) {
          unit = this.project.units.find(u => u.id === this.sidebarContextMenu!.unitId);
      } else if (format === 'ptb') {
          unit = this.activeUnit;
      }

      if (!unit) return;

      const ptb = this.activeSubtreeId
          ? (unit.subtrees?.find(st => st.id === this.activeSubtreeId)?.ptb || unit.current_ptb)
          : unit.current_ptb;
      const filename = `${this.project.meta.name}_${unit.id}`;

      this.sidebarContextMenu = null; // Close menu
      this.requestUpdate();

      try {
          // Client-side PTB export: simply download the PTB text
          if (format === 'ptb') {
              const blob = new Blob([ptb], { type: 'text/plain;charset=utf-8' });
              const url = globalThis.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `.ptb`;
              document.body.appendChild(a);
              a.click();
              a.remove();
              globalThis.URL.revokeObjectURL(url);
              return;
          }

          let endpoint = '/api/export/image';
          let ext = format;
          if (format === 'ascii') {
              endpoint = '/api/export/ascii';
              ext = 'txt';
          } else if (format === 'latex') {
              endpoint = '/api/export/latex';
              ext = 'tex';
          }

          const response = await fetch(endpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ptb, format })
          });

          if (!response.ok) throw new Error(await response.text());

          const blob = await response.blob();
          const url = globalThis.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `.`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          globalThis.URL.revokeObjectURL(url);
      } catch (e) {
          console.error("Sidebar export failed:", e);
          alert("Export failed.");
      }
  }

  private handleLoadProject() {
    const input = this.querySelector('#file-loader') as HTMLInputElement;
    if (input) input.click();
  }

  private async handleFileLoad(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    const text = await file.text();

    try {
      const json = JSON.parse(text);
      // Basic validation
      if (!json.meta || !json.units) {
        throw new Error("Invalid .gmy file format");
      }
      
      this.project = json;
      if (this.project && this.project.units.length > 0) {
          this.activeUnitId = this.project.units[0].id;
          this.activeSubtreeId = null;
          this.project.units.forEach(u => this.recalculateLineage(u)); // Ensure lineage on load
      }
      // Reset input so the same file can be loaded again if needed
      input.value = '';
    } catch (err) {
      console.error("Failed to load project:", err);
      alert("Failed to load project. Invalid file format.");
    }
  }

  private handlePasteInModal(e: ClipboardEvent) {
      e.preventDefault();
      const text = e.clipboardData?.getData('text/plain') || "";
      this.newProjectText = this.cleanInputText(text);
  }

  private toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
    // Trigger resize event after transition to ensure Cytoscape updates its viewport
    setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 350);
  }

  private get activeUnit(): TreeUnit | undefined {
      return this.project?.units.find(u => u.id === this.activeUnitId);
  }

  private get currentPtbToDisplay(): string {
      if (!this.activeUnit) return "";
      if (this.activeSubtreeId) {
          return this.activeUnit.subtrees?.find(st => st.id === this.activeSubtreeId)?.ptb || "";
      }
      return this.activeUnit.current_ptb;
  }

  private get activeParentLabel(): string {
      if (!this.activeSubtreeId || !this.activeUnit) return "Main";
      const currentSubtree = this.activeUnit.subtrees?.find(st => st.id === this.activeSubtreeId);
      
      if (currentSubtree && currentSubtree.parent_subtree_id !== undefined) {
          if (currentSubtree.parent_subtree_id === null) {
              return "Main";
          } else {
              const parent = this.activeUnit.subtrees?.find(st => st.id === currentSubtree.parent_subtree_id);
              return parent ? parent.label : "ROOT";
          }
      }
      return "ROOT";
  }

  private get activeColorIndex(): number {
      if (!this.activeSubtreeId || !this.activeUnit) return 0; // Main Tree = 0 (Vermilion)
      const st = this.activeUnit.subtrees?.find(s => s.id === this.activeSubtreeId);
      return st?.colorIndex !== undefined ? st.colorIndex : -1;
  }

  private isTerminalSubtree(subtree: SubTree): boolean {
      if (!this.activeUnit) return false;
      return !(this.activeUnit.subtrees?.some(st => st.parent_subtree_id === subtree.id));
  }

  private truncateText(text: string, limit: number = 35): string {
      if (text.length <= limit) return text;
      return text.substring(0, limit) + '...';
  }

  private extractTextFromPtb(ptb: string): string {
      // Simple extraction of leaves (tokens not starting with '(' or ')')
      // This is a heuristic for preview purposes
      return ptb
          .replace(/\([^\s\)]+/g, '') // Remove opening tags (e.g. (NP)
          .replace(/\)/g, '')         // Remove closing tags
          .replace(/LINK-[^\s\)]+/g, '') // Remove LINK-X tokens
          .replace(/\s+/g, ' ')       // Normalize spaces
          .trim();
  }

  private renderSidebarContextMenu() {
      if (!this.sidebarContextMenu || !this.sidebarContextMenu.open) return html``;
      
      const { x, y } = this.sidebarContextMenu;
      const style = `top: px; left: px;`;

      return html`
        <div 
            class="fixed z-50 bg-white border border-gray-200 shadow-xl rounded-lg py-1 min-w-[160px] flex flex-col text-sm animate-in fade-in zoom-in-95 duration-100 font-sans" 
            style=""
            @mouseleave=${() => this.sidebarContextMenu = null}
        >
            <button @click=${() => this.handleSidebarExport('png')} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 transition-colors"><span class="material-symbols-outlined text-base not-italic">image</span> <span class="font-sans">PNG</span></button>
            <button @click=${() => this.handleSidebarExport('svg')} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 transition-colors"><span class="material-symbols-outlined text-base not-italic">polyline</span> <span class="font-sans">SVG</span></button>
            <button @click=${() => this.handleSidebarExport('webp')} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 transition-colors"><span class="material-symbols-outlined text-base not-italic">photo</span> <span class="font-sans">WebP</span></button>
            <div class="h-px bg-gray-100 my-1"></div>
            <button @click=${() => this.handleSidebarExport('ascii')} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 transition-colors"><span class="material-symbols-outlined text-base not-italic">notes</span> <span class="font-sans">ASCII Tree</span></button>
            <button @click=${() => this.handleSidebarExport('latex')} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 transition-colors"><span class="material-symbols-outlined text-base not-italic">functions</span> <span class="font-sans">LaTeX</span></button>
        </div>
        <!-- Backdrop to close -->
        <div class="fixed inset-0 z-40" @click=${() => this.sidebarContextMenu = null} @contextmenu=${(e: Event) => { e.preventDefault(); this.sidebarContextMenu = null; }}></div>
      `;
  }

  override render() {
    const isFragmented = this.activeUnit?.subtrees && this.activeUnit.subtrees.length > 0;
    const canFragment = this.activeUnit && !this.activeSubtreeId && !isFragmented;
    const isSplitView = this.noteEditorState.isOpen;
    
    const isDetachDisabled = !this.selectedNodeLabel || ['ROOT', 'sentence'].includes(this.selectedNodeLabel);

    return html`
      <div class="h-screen w-screen flex flex-col bg-gray-100 overflow-hidden">
        <!-- Header -->
        <header class="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between shadow-sm z-50 shrink-0 h-14 relative">
            <div class="flex items-center gap-4">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">🩻</span>
                    <h1 class="text-xl font-bold text-gray-800 tracking-tight">Grammatomy <span class="text-blue-600">Studio</span></h1>
                </div>
                
                <!-- Project Menu -->
                <div class="h-6 w-px bg-gray-300 mx-2 hidden md:block"></div>
                <div class="flex gap-2 relative">
                    <!-- Project Dropdown -->
                    <button @click=${() => this.isProjectMenuOpen = !this.isProjectMenuOpen} class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors flex items-center gap-2">
                        <span class="material-symbols-outlined text-lg">folder</span> Project <span class="material-symbols-outlined text-sm">expand_more</span>
                    </button>
                    ${this.isProjectMenuOpen ? html`
                        <div class="fixed inset-0 z-40" @click=${() => this.isProjectMenuOpen = false}></div>
                        <div class="absolute top-full left-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-xl z-50 flex flex-col py-1 animate-in fade-in zoom-in-95 duration-100">
                            <button @click=${() => { this.openNewProjectModal(); this.isProjectMenuOpen = false; }} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 text-sm"><span class="material-symbols-outlined text-lg">add_box</span> New Project</button>
                            <button @click=${() => { this.handleLoadProject(); this.isProjectMenuOpen = false; }} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 text-sm"><span class="material-symbols-outlined text-lg">folder_open</span> Load Project</button>
                            <div class="h-px bg-gray-100 my-1"></div>
                            <button @click=${() => { this.handleExport(); this.isProjectMenuOpen = false; }} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 text-sm"><span class="material-symbols-outlined text-lg">save</span> Save (.gmy)</button>
                        </div>
                    ` : ''}

                    <!-- Export Dropdown -->
                    <button @click=${() => this.isExportMenuOpen = !this.isExportMenuOpen} class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors flex items-center gap-2">
                        <span class="material-symbols-outlined text-lg">download</span> Export <span class="material-symbols-outlined text-sm">expand_more</span>
                    </button>
                    ${this.isExportMenuOpen ? html`
                        <div class="fixed inset-0 z-40" @click=${() => this.isExportMenuOpen = false}></div>
                        <div class="absolute top-full left-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-xl z-50 flex flex-col py-1 animate-in fade-in zoom-in-95 duration-100">
                            <button @click=${() => { this.handleSidebarExport('ptb'); this.isExportMenuOpen = false; }} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 text-sm"><span class="material-symbols-outlined text-lg">notes</span> Export PTB</button>


                            <button @click=${() => { this.handleExportImage('png'); this.isExportMenuOpen = false; }} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 text-sm"><span class="material-symbols-outlined text-lg">image</span> Export PNG</button>
                            <button @click=${() => { this.handleExportImage('svg'); this.isExportMenuOpen = false; }} class="text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-gray-700 text-sm"><span class="material-symbols-outlined text-lg">polyline</span> Export SVG</button>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Editor Controls (Right Aligned) -->
            <div class="flex items-center gap-2">
                <button 
                    @click=${this.handleMasterMapToggle}
                    ?disabled=${!this.activeUnit}
                    class="p-1.5 rounded transition-colors ${this.viewMode === 'master_map' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'} disabled:opacity-30 disabled:cursor-not-allowed"
                    title="${this.viewMode === 'master_map' ? 'Back to Editor' : 'Master Map'}"
                >
                    <span class="material-symbols-outlined text-[24px]">map</span>
                </button>
                <div class="h-6 w-px bg-gray-300 mx-2"></div>
                <button @click=${() => this.editor?.undo()} class="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded transition-colors" title="Undo (Ctrl+Z)">
                    <span class="material-symbols-outlined text-[20px]">undo</span>
                </button>
                <button @click=${() => this.editor?.redo()} class="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded transition-colors" title="Redo (Ctrl+Y)">
                    <span class="material-symbols-outlined text-[20px]">redo</span>
                </button>
                <button @click=${() => this.editor?.fit()} class="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded transition-colors" title="Fit View (Ctrl+0)">
                    <span class="material-symbols-outlined text-[20px]">fit_screen</span>
                </button>
                <div class="h-6 w-px bg-gray-300 mx-2"></div>
                <button @click=${this.handleManualDetach} ?disabled= class="p-1.5 text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed" title="Detach Selected Node">
                    <span class="material-symbols-outlined text-[20px]">extension</span>
                </button>
            </div>
        </header>

        <!-- Sidebar Controls (Moved outside Main to prevent clipping) -->
        <aside class="absolute top-14 bottom-0 left-0 w-96 bg-gray-50 border-r border-gray-200 shadow-2xl z-40 transform transition-transform duration-300 ease-in-out ${this.isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}">
            
            <!-- Vertical Tabs Strip (Outside Container) -->
            <div 
                class="absolute -right-10 top-4 flex flex-col gap-2 z-50"
            >
                <!-- Tree Menu Tab -->
                <button 
                    @click=${() => this.switchSidebarTab('tree')}
                    class="w-10 h-24 bg-white border-y border-r border-gray-200 rounded-r-md shadow-sm flex items-center justify-center hover:bg-gray-50 transition-all ${this.isSidebarOpen && this.activeSidebarTab === 'tree' ? 'bg-blue-50 text-blue-600 border-blue-200' : 'text-gray-500'}"
                    title="Tree Menu"
                >
                    <span class="text-[10px] font-bold tracking-widest whitespace-nowrap transform rotate-180" style="writing-mode: vertical-rl;">TREE MENU</span>
                </button>

                <!-- Search Tab -->
                <button 
                    @click=${() => this.switchSidebarTab('search')}
                    class="w-10 h-24 bg-white border-y border-r border-gray-200 rounded-r-md shadow-sm flex items-center justify-center hover:bg-gray-50 transition-all ${this.isSidebarOpen && this.activeSidebarTab === 'search' ? 'bg-blue-50 text-blue-600 border-blue-200' : 'text-gray-500'}"
                    title="Structural Search"
                >
                    <span class="text-[10px] font-bold tracking-widest whitespace-nowrap transform rotate-180" style="writing-mode: vertical-rl;">SEARCH</span>
                </button>

                <!-- Close Tab -->
                <button 
                    @click=${() => this.isSidebarOpen = false}
                    class="w-10 h-10 bg-white border-y border-r border-gray-200 rounded-r-md shadow-sm flex items-center justify-center hover:bg-red-50 hover:text-red-500 text-gray-400 transition-colors mt-2"
                    title="Close Sidebar"
                >
                    <span class="material-symbols-outlined text-lg">close</span>
                </button>
            </div>

            <!-- Inner container with fixed width to prevent content squashing during transition -->
            <div class="flex flex-col gap-4 h-full p-6">
                ${this.activeSidebarTab === 'tree' ? this.renderTreeMenu() : this.renderSearchPanel()}
            </div>
        </aside>

        <!-- Main Workspace (Split View Capable) -->
        <main class="flex-1 w-full relative overflow-hidden flex pl-12">
            
            <!-- Left Pane: Note Editor (Always rendered for smooth transition) -->
            <div class="${isSplitView ? 'w-1/2 border-r border-gray-200 opacity-100' : 'w-0 border-none opacity-0'} h-full bg-white flex flex-col transition-all duration-300 z-10 shadow-xl overflow-hidden">
                <!-- Inner container to prevent content squashing during transition -->
                <div class="min-w-[500px] h-full flex flex-col">
                    <div class="p-3 border-b border-gray-100 flex justify-between items-center bg-gray-50 shrink-0">
                        <h3 class="font-bold text-gray-700 flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-600">edit_note</span> 
                            ${this.noteEditorState.title}
                        </h3>
                        <button @click=${this.closeNoteEditor} class="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-200">
                            <span class="material-symbols-outlined">close_fullscreen</span>
                        </button>
                    </div>
                    <div class="flex-1 overflow-hidden p-4 bg-gray-50/50">
                        <grammatomy-notes
                            class="h-full block"
                            .value=${this.currentNoteValue}
                            @change=${this.handleNoteChange}
                        ></grammatomy-notes>
                    </div>
                </div>
            </div>

            <!-- Right Pane: Diagram (Resizes) -->
            <div class="${isSplitView ? 'w-1/2' : 'w-full'} h-full relative transition-all duration-300 z-0">
                <div class="w-full h-full overflow-hidden relative">
                    ${this.activeUnit ? html`
                        ${this.viewMode === 'master_map' ? html`<div class="absolute top-4 left-4 z-10 bg-white/90 px-3 py-1 rounded shadow text-xs font-bold text-blue-800 border border-blue-100">MASTER MAP (Read Only)</div>` : ''}
                        <grammatomy-editor
                            class="w-full h-full block ${this.viewMode === 'master_map' ? 'bg-slate-50' : ''}"
                            .readOnly=${this.viewMode === 'master_map'}
                            .elements=${this.viewMode === 'master_map' ? this.masterTreeElements : []}
                            .ptb=${this.viewMode === 'edit' ? this.currentPtbToDisplay : ""}
                            .parentLabel=${this.viewMode === 'edit' ? this.activeParentLabel : ""}
                            .subtrees=${this.viewMode === 'edit' ? (this.activeUnit.subtrees || []) : []}
                            .isMainTree=${this.viewMode === 'edit' ? (this.activeSubtreeId === null) : false}
                            .activeColorIndex=${this.viewMode === 'edit' ? this.activeColorIndex : -1}
                            .initialFocusSelector=${this.viewMode === 'master_map' ? this.masterFocusSelector : ""}
                            @save-fragmentation=${this.handleFragmentation}
                            @request-navigation=${this.handleRequestNavigation}
                            @selection-changed=${this.handleSelectionChanged}
                            @node-dblclick=${this.handleMasterNodeDblClick}
                        >
                        </grammatomy-editor>
                    ` : html`
                        <div class="w-full h-full flex items-center justify-center bg-gray-50 rounded-xl border border-gray-200 shadow-inner">
                            <div class="text-center text-gray-400">
                                <span class="material-symbols-outlined text-6xl mb-4 opacity-20">account_tree</span>
                                <p>Select a sentence from the sidebar to edit its tree.</p>
                            </div>
                        </div>
                    `}
                </div>
            </div>
        </main>

        <!-- New Project Modal -->
        ${this.showNewProjectModal ? html`
            <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200">
                    <div class="p-4 border-b border-gray-100 flex justify-between items-center">
                        <h3 class="font-bold text-lg text-gray-800">New Project Wizard</h3>
                        <button @click=${() => this.showNewProjectModal = false} class="text-gray-400 hover:text-gray-600"><span class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 flex-1 overflow-y-auto">
                        <p class="text-sm text-gray-600 mb-2">Paste your text below. It will be automatically cleaned (line numbers and footnotes removed).</p>
                        <div class="relative">
                            <textarea 
                                class="w-full h-64 p-4 bg-gray-50 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
                                .value=${this.newProjectText}
                                @input=${(e: any) => this.newProjectText = e.target.value}
                                @paste=${this.handlePasteInModal}
                                placeholder="Paste text here..."
                            ></textarea>
                            <div class="absolute bottom-4 right-4 text-xs text-gray-400 pointer-events-none">Auto-clean on paste active</div>
                        </div>
                    </div>
                    <div class="p-4 border-t border-gray-100 bg-gray-50 rounded-b-xl flex justify-end gap-3">
                        <button @click=${() => this.showNewProjectModal = false} class="px-4 py-2 text-gray-600 font-medium hover:bg-gray-200 rounded-lg transition-colors">Cancel</button>
                        <button @click=${this.createProject} class="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-sm">Create Project</button>
                    </div>
                </div>
            </div>
        ` : ''}

        <!-- Global Loading Overlay (UI Blocker) -->
        ${this.isLoading ? html`
            <div class="fixed inset-0 z-[100] bg-white/50 backdrop-blur-[1px] flex items-center justify-center cursor-wait">
                <div class="flex flex-col items-center gap-3">
                    <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span class="text-sm font-medium text-blue-800 animate-pulse">Processing...</span>
                </div>
            </div>
        ` : ''}

        ${this.renderSidebarContextMenu()}

        <!-- Hidden File Input for Loading -->
        <input type="file" id="file-loader" class="hidden" accept=".gmy,.json" @change=${this.handleFileLoad} />

        <!-- Resource Loader / Diagnostics Footer -->
        <footer class="px-6 py-2 text-center text-xs text-gray-400 border-t border-gray-200 bg-white shrink-0">
            <span class="font-serif">Charis SIL (Phonetics)</span> | 
            <span class="font-mono">Roboto Mono (Data)</span> | 
            <span class="material-symbols-outlined align-middle text-sm">check_circle</span> Icons Ready
        </footer>
      </div>
    `;
  }

  private switchSidebarTab(tab: 'tree' | 'search') {
      this.activeSidebarTab = tab;
      this.isSidebarOpen = true;
      if (tab === 'search') {
          this.initializeSearch();
      }
      setTimeout(() => globalThis.dispatchEvent(new Event('resize')), 350);
  }

  private renderTreeMenu() {
      if (!this.project) return html`
        <div class="h-full flex flex-col items-center justify-center text-gray-400 p-8 text-center border-2 border-dashed border-gray-200 rounded-xl">
            <span class="material-symbols-outlined text-4xl mb-2 text-gray-300">library_books</span>
            <p class="text-sm font-medium">No project loaded</p>
            <p class="text-xs mt-2">Create a new project or load an existing .gmy file to start editing.</p>
            <button @click=${this.openNewProjectModal} class="mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-colors">
                Create Project
            </button>
        </div>
      `;

      return html`
                        <div class="flex flex-col h-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                            <div class="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-start">
                                <div>
                                    <h2 @click=${this.toggleMasterView} class="font-bold cursor-pointer hover:text-blue-600 transition-colors ${this.viewMode === 'master_map' ? 'text-blue-700 underline decoration-2 underline-offset-4' : 'text-gray-800'}" title="View Full Project Map">${this.project.meta.name}</h2>
                                    <div class="text-xs text-gray-500 mt-1">${this.project.units.length} sentences</div>
                                </div>
                                <button 
                                    @click=${() => this.openNoteEditor('project', 'project', 'Project Notes')}
                                    class="p-1 rounded hover:bg-gray-200 transition-colors ${this.project.notes ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'}"
                                    title="Edit Project Notes"
                                >
                                    <span class="material-symbols-outlined text-[20px]">edit_note</span>
                                </button>
                            </div>
                            <div class="flex-1 overflow-y-auto p-2 space-y-2" @contextmenu=${(e: Event) => e.preventDefault()}>
                                ${this.project.units.map((unit, index) => html`
                                    <div @contextmenu=${(e: MouseEvent) => this.handleSidebarContextMenu(e, unit.id)}>
                                        <div 
                                            @click=${() => this.selectUnit(unit.id)}
                                            class="p-3 rounded-lg cursor-pointer border transition-all ${this.activeUnitId === unit.id ? 'bg-blue-50 border-blue-200 ring-1 ring-blue-200' : 'bg-white border-gray-100 hover:border-blue-200 hover:shadow-sm'}"
                                        >
                                            <div class="flex justify-between items-center mb-1">
                                                <div class="flex items-center gap-2">
                                                    <span class="text-xs font-mono text-gray-400">#${index + 1}</span>
                                                    <span class="text-[10px] px-1.5 py-0.5 rounded-full ${unit.status === 'validated' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}">
                                                        ${unit.status}
                                                    </span>
                                                </div>
                                                <button 
                                                    @click=${(e: Event) => { e.stopPropagation(); this.openNoteEditor('unit', unit.id, `Unit #${index + 1}: ${this.truncateText(unit.sentence, 40)}`); }}
                                                    class="p-1 rounded hover:bg-gray-100 transition-colors ${unit.notes ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'}"
                                                >
                                                    <span class="material-symbols-outlined text-[18px]">edit_note</span>
                                                </button>
                                            </div>
                                            <p class="text-sm text-gray-700 line-clamp-3 leading-relaxed font-serif">${this.truncateText(unit.sentence, 60)}</p>
                                        </div>
                                        ${this.activeUnitId === unit.id && unit.subtrees?.length ? html`
                                            <div class="ml-4 pl-2 border-l-2 border-gray-100 space-y-1 mt-1 mb-2">
                                                <div 
                                                    @click=${(e: Event) => { e.stopPropagation(); this.navigateToMain(); }}
                                                    class=${`text-xs px-2 py-1 rounded cursor-pointer flex items-center justify-between ${!this.activeSubtreeId && this.viewMode === 'edit' ? 'bg-blue-100 text-blue-800 font-bold' : 'text-gray-500 hover:bg-gray-100'}`}
                                                >
                                                    <div class="flex items-center gap-2">
                                                        <span class="material-symbols-outlined text-[14px]">account_tree</span> Main Tree
                                                    </div>
                                                </div>
                                                ${unit.subtrees.slice().sort((a, b) => a.label.localeCompare(b.label)).map(st => html`
                                                    <div 
                                                        @click=${(e: Event) => { e.stopPropagation(); this.navigateToSubtree(st.id); }}
                                                        class=${`text-xs px-2 py-1 rounded cursor-pointer flex items-center justify-between ${this.activeSubtreeId === st.id && this.viewMode === 'edit' ? 'bg-blue-100 text-blue-800 font-bold' : 'text-gray-500 hover:bg-gray-100'}`}
                                                    >
                                                        <div class="flex items-center gap-2">
                                                            <span class="w-4 h-4 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center text-[9px] font-mono">${st.label}</span>
                                                            <span class="truncate max-w-[140px]" title="${this.extractTextFromPtb(st.ptb)}">Fragment ${st.label}: ${this.truncateText(this.extractTextFromPtb(st.ptb), 25)}</span>
                                                        </div>
                                                        <div class="flex items-center gap-1">
                                                        <button 
                                                            @click=${(e: Event) => this.handleReabsorb(e, st.id)}
                                                            class="p-0.5 rounded hover:bg-gray-200 text-gray-400 hover:text-purple-600 transition-colors"
                                                            title="Reabsorb Fragment (Merge Up)"
                                                        >
                                                            <span class="material-symbols-outlined text-[16px]">extension_off</span>
                                                        </button>
                                                        <button 
                                                            @click=${(e: Event) => { 
                                                                e.stopPropagation(); 
                                                                this.openNoteEditor('subtree', st.id, `Fragment ${st.label}: ${this.truncateText(this.extractTextFromPtb(st.ptb), 40)}`, unit.id); 
                                                            }}
                                                            class="p-0.5 rounded hover:bg-gray-200 transition-colors ${st.notes ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'}"
                                                        >
                                                            <span class="material-symbols-outlined text-[16px]">edit_note</span>
                                                        </button>
                                                        </div>
                                                    </div>
                                                `)}
                                            </div>
                                        ` : ''}
                                    </div>
                                `)}
                            </div>
                        </div>
      `;
  }

  // --- Search Logic ---

  private initializeSearch() {
      if (!this.project) return;
      
      // Extract all unique node types (LHS)
      const types = new Set<string>();
      
      const processPtb = (ptb: string) => {
          if (!ptb) return;
          const elements = parsePtbToCytoscape(ptb);
          
          // Identify parents to detect leaves
          const parentIds = new Set<string>();
          elements.forEach((el: any) => {
              if ('source' in el.data) {
                  parentIds.add(el.data.source);
              }
          });

          elements.forEach((el: any) => {
              if (!('source' in el.data)) { // It's a node
                  const label = el.data.label;
                  const isLeaf = !parentIds.has(el.data.id);
                  const isGhost = label.includes("👻");
                  const isLink = label.startsWith("LINK") || label.startsWith("LINK-");
                  const isPunctuation = PUNCTUATION_TAGS.has(label);

                  if (isLink) return;
                  if (isPunctuation) return;
                  if (isLeaf && !isGhost) return; // Exclude words/terminals unless they are ghosts

                  if (label) types.add(label);
              }
          });
      };

      this.project.units.forEach(u => {
          processPtb(u.current_ptb);
          u.subtrees?.forEach(st => processPtb(st.ptb));
      });

      this.searchNodeTypes = Array.from(types).sort();

      // Default to IMPLICIT if nothing selected and populate rules immediately
      if (!this.selectedSearchType) {
          this.selectedSearchType = "IMPLICIT";
      }
      this.populateSearchRules();
  }

  private populateSearchRules() {
      if (!this.project) return;

      // Find all production rules for this LHS
      const rules = new Set<string>();
      
      const processPtb = (ptb: string) => {
          if (!ptb) return;
          const elements = parsePtbToCytoscape(ptb) as any[];
          // Map parent -> children
          const childrenMap = new Map<string, any[]>();
          elements.forEach(el => {
              if ('source' in el.data) {
                  const pid = el.data.source;
                  if (!childrenMap.has(pid)) childrenMap.set(pid, []);
                  // Find the target node to get its label
                  const targetNode = elements.find(n => !('source' in n.data) && n.data.id === el.data.target);
                  if (targetNode) {
                      childrenMap.get(pid)!.push(targetNode);
                  }
              }
          });

          elements.forEach(el => {
              const isTargetNode = this.selectedSearchType === "IMPLICIT" ? !('source' in el.data) : (!('source' in el.data) && el.data.label === this.selectedSearchType);
              if (isTargetNode) {
                  const children = childrenMap.get(el.data.id) || [];
                  if (children.length > 0) {
                      const rhs = children.map(c => {
                          // Check if child is a terminal (leaf) to abstract lexical items
                          const grandChildren = childrenMap.get(c.data.id);
                          const isLeaf = !grandChildren || grandChildren.length === 0;
                          
                          if (isLeaf) {
                              if (c.data.label.includes("👻")) return c.data.label; // Keep ghosts explicit
                              if (c.data.label.startsWith("LINK")) return c.data.label; // Keep links explicit
                              return "<terminal>"; // Abstract words/punctuation
                          }
                          return c.data.label;
                      }).join(" ");
                      rules.add(rhs);
                  }
              }
          });
      };

      this.project.units.forEach(u => {
          processPtb(u.current_ptb);
          u.subtrees?.forEach(st => processPtb(st.ptb));
      });

      this.searchRules = Array.from(rules).sort();
  }

  private handleSearchTypeSelect(e: Event) {
      const select = e.target as HTMLSelectElement;
      this.selectedSearchType = select.value;
      this.selectedSearchRule = "";
      this.searchResults = [];
      this.populateSearchRules();
  }

  private handleSearch() {
      if (!this.selectedSearchRule || !this.project) return;

      const results: any[] = [];
      const targetRhs = this.selectedSearchRule.split(" ");

      const processPtb = (ptb: string, unitId: string, subtreeId: string | null, contextText: string) => {
          if (!ptb) return;
          const elements = parsePtbToCytoscape(ptb) as any[];
          const childrenMap = new Map<string, any[]>();

          // Build parent -> children map
          elements.forEach(el => {
              if ('source' in el.data) {
                  const pid = el.data.source;
                  if (!childrenMap.has(pid)) childrenMap.set(pid, []);
                  const targetNode = elements.find(n => !('source' in n.data) && n.data.id === el.data.target);
                  if (targetNode) childrenMap.get(pid)!.push(targetNode);
              }
          });

          // Iterate potential parent nodes
          elements.forEach(el => {
              const isTargetNode = this.selectedSearchType === "IMPLICIT"
                ? !('source' in el.data)
                : (!('source' in el.data) && el.data.label === this.selectedSearchType);

              if (!isTargetNode) return;

              const children = childrenMap.get(el.data.id) || [];
              if (children.length === 0) return;

              const currentRhs = children.map((c: any) => {
                  const grandChildren = childrenMap.get(c.data.id);
                  const isLeaf = !grandChildren || grandChildren.length === 0;
                  if (isLeaf) {
                      if (c.data.label.includes("👻")) return c.data.label;
                      if (c.data.label.startsWith("LINK")) return c.data.label;
                      return "<terminal>";
                  }
                  return c.data.label;
              });

              // Check for contiguous subsequence match (or exact match)
              let match = false;
              if (targetRhs.length <= currentRhs.length) {
                  for (let i = 0; i <= currentRhs.length - targetRhs.length; i++) {
                      if (currentRhs.slice(i, i + targetRhs.length).every((val, k) => val === targetRhs[k])) {
                          match = true;
                          break;
                      }
                  }
              } else {
                  match = (currentRhs.length === targetRhs.length && currentRhs.every((val, i) => val === targetRhs[i]));
              }

              if (match) {
                  results.push({
                      unitId,
                      subtreeId,
                      nodeId: el.data.id,
                      text: contextText.substring(0, 40) + (contextText.length > 40 ? "..." : ""),
                      context: `${el.data.label} -> ... ${this.selectedSearchRule} ...`
                  });
              }
          });
      };

      this.project.units.forEach(u => {
          processPtb(u.current_ptb, u.id, null, u.sentence);
          u.subtrees?.forEach(st => processPtb(st.ptb, u.id, st.id, `[Fragment ${st.label}] ...`));
      });

      this.searchResults = results;
  }

  private async navigateToSearchResult(res: any) {
      // 1. Select Unit
      await this.selectUnit(res.unitId);
      
      // 2. Select Subtree if needed
      if (res.subtreeId) {
          this.navigateToSubtree(res.subtreeId);
      } else {
          this.navigateToMain();
      }

      // 3. Select Node (Wait for render)
      setTimeout(() => {
          if (this.editor) {
              this.editor.focusNode(res.nodeId);
          }
      }, 200);
  }

  private renderSearchPanel() {
      return html`
        <div class="flex flex-col h-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="p-4 border-b border-gray-100 bg-gray-50/50">
                <h2 class="font-bold text-gray-800 flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-600">search</span> Structural Search
                </h2>
                <div class="text-xs text-gray-500 mt-1">Find patterns by production rule</div>
            </div>
            
            <div class="p-4 space-y-4 border-b border-gray-100">
                <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Node Type (LHS)</label>
                    <select 
                        class="w-full p-2 bg-gray-50 border border-gray-300 rounded text-sm font-mono"
                        @change=${this.handleSearchTypeSelect}
                        .value=${this.selectedSearchType}
                    >
                        <option value="IMPLICIT">Implicit Structure</option>
                        ${this.searchNodeTypes.map(t => html`<option value=""></option>`)}
                    </select>
                </div>

                <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Production Rule (RHS)</label>
                    <select 
                        class="w-full p-2 bg-gray-50 border border-gray-300 rounded text-sm font-mono"
                        @change=${(e: any) => this.selectedSearchRule = e.target.value}
                        .value=${this.selectedSearchRule}
                    >
                        <option value="">Select Rule...</option>
                        ${this.searchRules.map(r => html`<option value="">${this.selectedSearchType === 'IMPLICIT' ? '... ' + r + ' ...' : this.selectedSearchType + ' -> ' + r}</option>`)}
                    </select>
                </div>

                <button 
                    @click=${this.handleSearch}
                    ?disabled=${!this.selectedSearchRule}
                    class="w-full py-2 bg-blue-600 text-white rounded font-bold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    Find Occurrences
                </button>
            </div>

            <div class="flex-1 overflow-y-auto p-2 space-y-2 bg-gray-50">
                ${this.searchResults.length === 0 ? html`
                    <div class="text-center text-gray-400 mt-8 text-sm">
                        No results found or search not started.
                    </div>
                ` : this.searchResults.map((res, i) => html`
                    <div 
                        @click=${() => this.navigateToSearchResult(res)}
                        class="p-3 bg-white border border-gray-200 rounded hover:border-blue-300 hover:shadow-sm cursor-pointer transition-all group"
                    >
                        <div class="flex justify-between items-start mb-1">
                            <span class="text-xs font-mono text-blue-600 font-bold group-hover:underline">#${i + 1}</span>
                            <span class="text-[10px] text-gray-400 font-mono">${res.nodeId}</span>
                        </div>
                        <div class="text-xs font-mono text-gray-500 mb-1 bg-gray-50 p-1 rounded">${res.context}</div>
                        <p class="text-sm text-gray-800 font-serif italic">"${res.text}"</p>
                    </div>
                `)}
            </div>
        </div>
      `;
  }
  
}
