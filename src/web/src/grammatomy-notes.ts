import { LitElement, html } from 'lit';
import { customElement, property, query, state } from 'lit/decorators.js';
import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import { Markdown } from 'tiptap-markdown';

@customElement('grammatomy-notes')
export class GrammatomyNotes extends LitElement {
  @query('#editor') private editorElement!: HTMLElement;
  
  private editor: Editor | null = null;

  @property({ type: String })
  value: string = ""; // Markdown content input

  @property({ type: String })
  placeholder: string = "Type your notes here...";

  @property({ type: Boolean })
  readonly: boolean = false;

  @state()
  private isFocused = false;

  override createRenderRoot() {
    return this; // Light DOM for Tailwind compatibility
  }

  override firstUpdated() {
    this.initEditor();
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    this.editor?.destroy();
  }

  // Watch for external value changes (e.g. switching trees)
  override updated(changedProperties: Map<string, any>) {
    if (changedProperties.has('value') && this.editor && !this.isFocused) {
        // Only update if not focused to avoid cursor jumping
        // Check if content actually changed to avoid loops
        const currentMarkdown = this.editor.storage.markdown.getMarkdown();
        if (currentMarkdown !== this.value) {
            this.editor.commands.setContent(this.value);
        }
    }
  }

  private initEditor() {
    if (this.editor) return;

    this.editor = new Editor({
      element: this.editorElement,
      extensions: [
        StarterKit,
        Markdown,
      ],
      content: this.value,
      editable: !this.readonly,
      editorProps: {
        attributes: {
          class: 'prose prose-sm max-w-none focus:outline-none min-h-[150px] p-4 text-gray-700 leading-relaxed',
        },
      },
      onUpdate: ({ editor }) => {
        const markdown = editor.storage.markdown.getMarkdown();
        this.dispatchEvent(new CustomEvent('change', { detail: markdown }));
        this.requestUpdate(); // Force toolbar update
      },
      onFocus: () => this.isFocused = true,
      onBlur: () => this.isFocused = false,
      onSelectionUpdate: () => this.requestUpdate(), // Update toolbar active states
    });

    // Force re-render to show toolbar now that editor is initialized
    this.requestUpdate();
  }

  public focus() {
      this.editor?.commands.focus();
  }

  public refresh() {
      if (this.editor) {
          this.editor.view.updateState(this.editor.state);
          this.focus();
      }
  }

  // Toolbar Actions
  private toggleBold() { this.editor?.chain().focus().toggleBold().run(); }
  private toggleItalic() { this.editor?.chain().focus().toggleItalic().run(); }
  private toggleHeading(level: 1 | 2) { this.editor?.chain().focus().toggleHeading({ level }).run(); }
  private toggleBulletList() { this.editor?.chain().focus().toggleBulletList().run(); }
  private toggleOrderedList() { this.editor?.chain().focus().toggleOrderedList().run(); }

  private renderToolbarButton(icon: string, isActive: boolean, onClick: () => void, title: string) {
      return html`
        <button 
            @click=${onClick}
            class="p-1.5 rounded hover:bg-gray-200 transition-colors ${isActive ? 'bg-blue-100 text-blue-700' : 'text-gray-600'}"
            title="${title}"
            ?disabled=${this.readonly}
        >
            <span class="material-symbols-outlined text-[18px]">${icon}</span>
        </button>
      `;
  }

  override render() {
    return html`
      <style>
        /* Restore default styles for TipTap content inside Tailwind environment */
        .ProseMirror h1 { font-size: 1.5em; font-weight: 800; margin-top: 0.8em; margin-bottom: 0.4em; line-height: 1.2; }
        .ProseMirror h2 { font-size: 1.25em; font-weight: 700; margin-top: 0.6em; margin-bottom: 0.3em; line-height: 1.3; }
        .ProseMirror ul { list-style-type: disc; padding-left: 1.5em; margin-top: 0.5em; margin-bottom: 0.5em; }
        .ProseMirror ol { list-style-type: decimal; padding-left: 1.5em; margin-top: 0.5em; margin-bottom: 0.5em; }
        .ProseMirror li { margin-bottom: 0.2em; }
        .ProseMirror blockquote { border-left: 4px solid #e5e7eb; padding-left: 1em; color: #4b5563; font-style: italic; margin: 1em 0; }
        .ProseMirror code { background-color: #f3f4f6; padding: 0.2em 0.4em; border-radius: 0.25em; font-family: monospace; font-size: 0.9em; }
        .ProseMirror pre { background-color: #1f2937; color: #f9fafb; padding: 0.75em 1em; border-radius: 0.5em; font-family: monospace; overflow-x: auto; margin: 1em 0; }
        .ProseMirror p { margin-bottom: 0.8em; }
        .ProseMirror:focus { outline: none; }
      </style>

      <div class="flex flex-col border border-gray-200 rounded-lg bg-white overflow-hidden shadow-sm focus-within:ring-2 focus-within:ring-blue-100 transition-shadow">
        <!-- Toolbar -->
        ${!this.readonly ? html`
            <div class="flex items-center gap-1 p-1 border-b border-gray-100 bg-gray-50/50">
                ${this.renderToolbarButton('format_bold', this.editor?.isActive('bold') || false, () => this.toggleBold(), 'Bold')}
                ${this.renderToolbarButton('format_italic', this.editor?.isActive('italic') || false, () => this.toggleItalic(), 'Italic')}
                <div class="w-px h-4 bg-gray-300 mx-1"></div>
                ${this.renderToolbarButton('format_h1', this.editor?.isActive('heading', { level: 1 }) || false, () => this.toggleHeading(1), 'Heading 1')}
                ${this.renderToolbarButton('format_h2', this.editor?.isActive('heading', { level: 2 }) || false, () => this.toggleHeading(2), 'Heading 2')}
                <div class="w-px h-4 bg-gray-300 mx-1"></div>
                ${this.renderToolbarButton('format_list_bulleted', this.editor?.isActive('bulletList') || false, () => this.toggleBulletList(), 'Bullet List')}
                ${this.renderToolbarButton('format_list_numbered', this.editor?.isActive('orderedList') || false, () => this.toggleOrderedList(), 'Ordered List')}
            </div>
        ` : ''}
        
        <!-- Editor Area -->
        <div id="editor" class="bg-white"></div>
        
        <!-- Footer / Status -->
        <div class="px-3 py-1 bg-gray-50 border-t border-gray-100 text-[10px] text-gray-400 flex justify-end">
            Markdown Mode
        </div>
      </div>
    `;
  }
}