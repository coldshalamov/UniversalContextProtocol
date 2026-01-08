/**
 * Context View - Tree view showing current captured context
 */

import * as vscode from 'vscode';
import { ContextCapture, EditorContext } from './contextCapture';

export class ContextTreeProvider implements vscode.TreeDataProvider<ContextItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ContextItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private currentContext: EditorContext | null = null;

    constructor(private readonly contextCapture: ContextCapture) { }

    updateContext(context: EditorContext): void {
        this.currentContext = context;
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: ContextItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ContextItem): ContextItem[] {
        if (!element) {
            // Root level
            if (!this.currentContext) {
                return [new ContextItem('No context captured', 'Open a file to capture context', 'info')];
            }

            return [
                new ContextItem('File', this.getFileName(this.currentContext.fileName), 'file',
                    vscode.TreeItemCollapsibleState.Collapsed),
                new ContextItem('Language', this.currentContext.language, 'language'),
                new ContextItem('Line', `${this.currentContext.lineNumber}`, 'line'),
                ...(this.currentContext.selection
                    ? [new ContextItem('Selection', `${this.currentContext.selection.length} chars`, 'selection')]
                    : []),
                ...(this.currentContext.diagnostics?.length
                    ? [new ContextItem('Diagnostics', `${this.currentContext.diagnostics.length}`, 'diagnostics',
                        vscode.TreeItemCollapsibleState.Collapsed)]
                    : []),
                ...(this.currentContext.openFiles?.length
                    ? [new ContextItem('Open Files', `${this.currentContext.openFiles.length}`, 'files',
                        vscode.TreeItemCollapsibleState.Collapsed)]
                    : []),
            ];
        }

        // Children
        if (element.contextValue === 'diagnostics' && this.currentContext?.diagnostics) {
            return this.currentContext.diagnostics.map((d, i) =>
                new ContextItem(`Issue ${i + 1}`, d, 'diagnostic-item')
            );
        }

        if (element.contextValue === 'files' && this.currentContext?.openFiles) {
            return this.currentContext.openFiles.map(f =>
                new ContextItem(this.getFileName(f), f, 'file-item')
            );
        }

        return [];
    }

    private getFileName(path: string): string {
        return path.split(/[/\\]/).pop() || path;
    }
}

class ContextItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly value: string,
        public readonly contextValue: string,
        collapsibleState: vscode.TreeItemCollapsibleState = vscode.TreeItemCollapsibleState.None
    ) {
        super(label, collapsibleState);

        this.description = value;
        this.tooltip = value;

        // Set icons
        const icons: Record<string, string> = {
            'file': 'file',
            'language': 'code',
            'line': 'location',
            'selection': 'selection',
            'diagnostics': 'warning',
            'files': 'files',
            'info': 'info',
            'diagnostic-item': 'error',
            'file-item': 'file',
        };

        this.iconPath = new vscode.ThemeIcon(icons[contextValue] || 'circle-outline');
    }
}
