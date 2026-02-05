import { LitElement, html } from 'lit';
import { customElement, state, query } from 'lit/decorators.js';
import './index.css';
import './grammatomy-editor';
import { GrammatomyEditor } from './grammatomy-editor';

@customElement('grammatomy-app')
export class GrammatomyApp extends LitElement {
  @query('grammatomy-editor')
  private editor!: GrammatomyEditor;

  @state()
  private inputText = "El veloz murciélago hindú comía feliz cardillo y kiwi.";

  @state()
  private isLoading = false;

  @state()
  private isSidebarOpen = true;

  @state()
  private currentPtb: string = '';

  // Desactivamos Shadow DOM para usar Tailwind globalmente sin problemas
  // Esto permite que los estilos globales de index.css afecten al componente
  override createRenderRoot() {
    return this;
  }

  private async handleAnalyze() {
    this.isLoading = true;
    try {
        // Call via Vite Proxy (/api -> localhost:8000)
        const response = await fetch('/api/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: this.inputText,
                engine: 'stanza',
                lang: 'es'
            })
        });

        if (!response.ok) throw new Error(await response.text());

        const data = await response.json();
        
        // Pass data to the editor component
        if (data.ptb) {
            this.currentPtb = data.ptb;
        }

    } catch (e) {
        console.error("Analysis failed:", e);
        alert("Error analyzing text. Check console.");
    } finally {
        this.isLoading = false;
    }
  }

  private toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
    // Trigger resize event after transition to ensure Cytoscape updates its viewport
    setTimeout(() => window.dispatchEvent(new Event('resize')), 350);
  }

  private handleSave() {
    if (this.editor) {
        const ptb = this.editor.getCurrentPtb();
        console.log("Tree Saved:", ptb);
        alert("Tree saved! (Check console for PTB string)");
    }
  }

  override render() {
    return html`
      <div class="h-screen w-screen flex flex-col bg-base-light-dim overflow-hidden">
        <!-- Header -->
        <header class="bg-base-light border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm z-10 shrink-0">
            <div class="flex items-center gap-4">
                <button @click=${this.toggleSidebar} class="text-gray-500 hover:text-ibm-blue transition-colors p-1 rounded-md hover:bg-gray-100" title="Toggle Sidebar">
                    <span class="material-symbols-outlined">menu</span>
                </button>
                <div class="flex items-center gap-3">
                    <span class="text-2xl">🩻</span>
                    <h1 class="text-xl font-bold text-gray-800 tracking-tight">Grammatomy <span class="text-gram-primary">Studio</span></h1>
                </div>
            </div>
            <div class="text-sm text-gray-500 font-mono">v0.1.0</div>
        </header>

        <!-- Main Workspace -->
        <main class="flex-1 w-full flex overflow-hidden">
            
            <!-- Sidebar Controls (Collapsible) -->
            <aside class="${this.isSidebarOpen ? 'w-96 p-6 opacity-100' : 'w-0 p-0 opacity-0'} transition-all duration-300 ease-in-out flex flex-col overflow-hidden bg-base-light-dim border-r border-gray-200/0">
                <!-- Inner container with fixed width to prevent content squashing during transition -->
                <div class="w-84 flex flex-col gap-4 h-full min-w-[20rem]">
                    <div class="bg-base-light p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col gap-3 h-full">
                        <label class="text-sm font-bold text-gray-700">Input Text</label>
                        <textarea 
                            class="w-full flex-1 p-3 bg-base-light border border-gray-300 rounded-lg font-mono text-sm resize-none focus:ring-2 focus:ring-gram-primary focus:border-transparent outline-none"
                            .value=${this.inputText}
                            @input=${(e: any) => this.inputText = e.target.value}
                        ></textarea>
                        
                        <button 
                            @click=${this.handleAnalyze}
                            ?disabled=${this.isLoading}
                            class="w-full py-3 bg-gram-primary hover:bg-sky-600 text-white font-bold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                        >
                            ${this.isLoading ? html`<span class="animate-spin">⏳</span> Processing...` : html`🚀 Analyze`}
                        </button>

                        <button 
                            @click=${this.handleSave}
                            class="w-full py-3 bg-ibm-blue hover:bg-blue-600 text-white font-bold rounded-lg transition-colors flex justify-center items-center gap-2 mt-auto"
                        >
                            <span class="material-symbols-outlined">save</span> Save & Return
                        </button>
                    </div>
                </div>
            </aside>

            <!-- Editor Canvas -->
            <div class="flex-1 p-6 h-full overflow-hidden relative">
                <grammatomy-editor 
                    class="w-full h-full block"
                    .ptb=${this.currentPtb}
                ></grammatomy-editor>
            </div>
        </main>

        <!-- Resource Loader / Diagnostics Footer -->
        <footer class="px-6 py-2 text-center text-xs text-gray-400 border-t border-gray-200 bg-base-light shrink-0">
            <span class="font-serif">Charis SIL (Phonetics)</span> | 
            <span class="font-mono">Roboto Mono (Data)</span> | 
            <span class="material-symbols-outlined align-middle text-sm">check_circle</span> Icons Ready
        </footer>
      </div>
    `;
  }
}