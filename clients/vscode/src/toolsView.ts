/**
 * Tools View - Tree view showing predicted and available tools
 */

import * as vscode from 'vscode';
import { UCPClient, Tool, ToolPrediction } from './ucpClient';

export class ToolsTreeProvider implements vscode.TreeDataProvider<ToolItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ToolItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private prediction: ToolPrediction | null = null;
    private availableTools: Tool[] = [];

    constructor(private readonly ucpClient: UCPClient) {
        this.refresh();
    }

    async refresh(): Promise<void> {
        this.availableTools = await this.ucpClient.getAvailableTools();
        this._onDidChangeTreeData.fire(undefined);
    }

    updatePrediction(prediction: ToolPrediction): void {
        this.prediction = prediction;
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: ToolItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: ToolItem): Promise<ToolItem[]> {
        if (!element) {
            // Root level - show categories
            const items: ToolItem[] = [];

            if (this.prediction && this.prediction.tools.length > 0) {
                items.push(new ToolItem(
                    'Predicted Tools',
                    vscode.TreeItemCollapsibleState.Expanded,
                    'category',
                    undefined,
                    `${this.prediction.tools.length} tools`
                ));
            }

            if (this.availableTools.length > 0) {
                items.push(new ToolItem(
                    'All Available',
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'category',
                    undefined,
                    `${this.availableTools.length} tools`
                ));
            }

            if (items.length === 0) {
                items.push(new ToolItem(
                    'No tools available',
                    vscode.TreeItemCollapsibleState.None,
                    'info',
                    undefined,
                    'Connect to UCP server'
                ));
            }

            return items;
        }

        // Children based on category
        if (element.contextValue === 'category') {
            if (element.label === 'Predicted Tools' && this.prediction) {
                return this.prediction.tools.map(tool => {
                    const score = this.prediction!.scores[tool.name];
                    return new ToolItem(
                        tool.name,
                        vscode.TreeItemCollapsibleState.None,
                        'predicted-tool',
                        tool,
                        score ? `Score: ${(score * 100).toFixed(0)}%` : tool.description?.substring(0, 50)
                    );
                });
            }

            if (element.label === 'All Available') {
                return this.availableTools.map(tool =>
                    new ToolItem(
                        tool.name,
                        vscode.TreeItemCollapsibleState.None,
                        'tool',
                        tool,
                        tool.description?.substring(0, 50)
                    )
                );
            }
        }

        return [];
    }
}

class ToolItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string,
        public readonly tool?: Tool,
        public readonly description?: string
    ) {
        super(label, collapsibleState);

        this.description = description;
        this.tooltip = tool?.description || label;

        // Set icons based on type
        switch (contextValue) {
            case 'category':
                this.iconPath = new vscode.ThemeIcon('folder');
                break;
            case 'predicted-tool':
                this.iconPath = new vscode.ThemeIcon('sparkle');
                break;
            case 'tool':
                this.iconPath = new vscode.ThemeIcon('tools');
                break;
            case 'info':
                this.iconPath = new vscode.ThemeIcon('info');
                break;
        }
    }
}
