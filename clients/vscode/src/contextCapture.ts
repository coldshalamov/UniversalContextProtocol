/**
 * Context Capture - Captures editor and workspace context for UCP
 */

import * as vscode from 'vscode';

export interface EditorContext {
    text: string;
    language: string;
    fileName: string;
    lineNumber: number;
    selection?: string;
    surroundingCode?: string;
    workspaceFolder?: string;
    openFiles?: string[];
    recentEdits?: string[];
    diagnostics?: string[];
}

export class ContextCapture implements vscode.Disposable {
    private recentEdits: Map<string, string[]> = new Map();
    private disposables: vscode.Disposable[] = [];
    private maxRecentEdits = 10;

    constructor() {
        // Track document changes for recent edits
        this.disposables.push(
            vscode.workspace.onDidChangeTextDocument((event) => {
                const uri = event.document.uri.toString();
                const edits = this.recentEdits.get(uri) || [];

                for (const change of event.contentChanges) {
                    if (change.text.trim()) {
                        edits.push(change.text.substring(0, 200));
                        if (edits.length > this.maxRecentEdits) {
                            edits.shift();
                        }
                    }
                }

                this.recentEdits.set(uri, edits);
            })
        );
    }

    dispose(): void {
        this.disposables.forEach(d => d.dispose());
    }

    /**
     * Capture context from the active text editor
     */
    captureEditorContext(editor: vscode.TextEditor): EditorContext {
        const document = editor.document;
        const selection = editor.selection;
        const position = selection.active;

        // Get selected text if any
        const selectedText = document.getText(selection);

        // Get surrounding code (15 lines before and after cursor)
        const startLine = Math.max(0, position.line - 15);
        const endLine = Math.min(document.lineCount - 1, position.line + 15);
        const surroundingRange = new vscode.Range(
            new vscode.Position(startLine, 0),
            new vscode.Position(endLine, document.lineAt(endLine).text.length)
        );
        const surroundingCode = document.getText(surroundingRange);

        // Get diagnostics (errors/warnings) for the file
        const diagnostics = vscode.languages.getDiagnostics(document.uri);
        const diagnosticTexts = diagnostics
            .slice(0, 5)
            .map(d => `${d.severity === 0 ? 'ERROR' : 'WARN'}: ${d.message}`);

        // Get open files
        const openFiles = vscode.window.tabGroups.all
            .flatMap(group => group.tabs)
            .filter(tab => tab.input instanceof vscode.TabInputText)
            .map(tab => (tab.input as vscode.TabInputText).uri.fsPath)
            .slice(0, 10);

        // Get workspace folder
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);

        // Get recent edits for this file
        const recentEdits = this.recentEdits.get(document.uri.toString()) || [];

        // Build context text for UCP
        const contextParts: string[] = [];

        contextParts.push(`File: ${document.fileName}`);
        contextParts.push(`Language: ${document.languageId}`);
        contextParts.push(`Line: ${position.line + 1}`);

        if (selectedText) {
            contextParts.push(`\nSelected code:\n${selectedText}`);
        }

        contextParts.push(`\nSurrounding code:\n${surroundingCode}`);

        if (diagnosticTexts.length > 0) {
            contextParts.push(`\nDiagnostics:\n${diagnosticTexts.join('\n')}`);
        }

        return {
            text: contextParts.join('\n'),
            language: document.languageId,
            fileName: document.fileName,
            lineNumber: position.line + 1,
            selection: selectedText || undefined,
            surroundingCode,
            workspaceFolder: workspaceFolder?.name,
            openFiles,
            recentEdits,
            diagnostics: diagnosticTexts,
        };
    }

    /**
     * Capture context from a selection change event
     */
    captureSelectionContext(
        event: vscode.TextEditorSelectionChangeEvent
    ): EditorContext | null {
        if (!event.textEditor) {
            return null;
        }

        // Only capture if there's a meaningful selection
        const selection = event.selections[0];
        if (selection.isEmpty) {
            return null;
        }

        return this.captureEditorContext(event.textEditor);
    }

    /**
     * Capture workspace-level context
     */
    captureWorkspaceContext(): Record<string, unknown> {
        const workspaceFolders = vscode.workspace.workspaceFolders || [];

        return {
            workspaceFolders: workspaceFolders.map(f => ({
                name: f.name,
                path: f.uri.fsPath,
            })),
            openEditors: vscode.window.visibleTextEditors.map(e => ({
                fileName: e.document.fileName,
                language: e.document.languageId,
            })),
            activeEditor: vscode.window.activeTextEditor?.document.fileName,
            terminalCount: vscode.window.terminals.length,
        };
    }

    /**
     * Get symbols from the current file for richer context
     */
    async captureSymbols(document: vscode.TextDocument): Promise<vscode.DocumentSymbol[]> {
        try {
            const symbols = await vscode.commands.executeCommand<vscode.DocumentSymbol[]>(
                'vscode.executeDocumentSymbolProvider',
                document.uri
            );
            return symbols || [];
        } catch {
            return [];
        }
    }

    /**
     * Get definition of symbol under cursor
     */
    async captureDefinition(
        document: vscode.TextDocument,
        position: vscode.Position
    ): Promise<string | null> {
        try {
            const definitions = await vscode.commands.executeCommand<vscode.Location[]>(
                'vscode.executeDefinitionProvider',
                document.uri,
                position
            );

            if (definitions && definitions.length > 0) {
                const def = definitions[0];
                const defDoc = await vscode.workspace.openTextDocument(def.uri);
                return defDoc.getText(def.range);
            }
        } catch {
            // Definition lookup failed
        }
        return null;
    }
}
