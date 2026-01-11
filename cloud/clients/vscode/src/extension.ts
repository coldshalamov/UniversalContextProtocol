/**
 * UCP VS Code Extension - Main Entry Point
 * 
 * Universal Context Protocol extension that captures editor context
 * and provides intelligent tool predictions.
 */

import * as vscode from 'vscode';
import { UCPClient } from './ucpClient';
import { ChatViewProvider } from './chatView';
import { ToolsTreeProvider } from './toolsView';
import { ContextTreeProvider } from './contextView';
import { ContextCapture } from './contextCapture';
import { StatusBarManager } from './statusBar';

let ucpClient: UCPClient;
let contextCapture: ContextCapture;
let statusBarManager: StatusBarManager;

export async function activate(context: vscode.ExtensionContext) {
    console.log('UCP extension activating...');

    // Get configuration
    const config = vscode.workspace.getConfiguration('ucp');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:8765');

    // Initialize UCP client
    ucpClient = new UCPClient(serverUrl);

    // Initialize context capture
    contextCapture = new ContextCapture();

    // Initialize status bar
    statusBarManager = new StatusBarManager(ucpClient);

    // Try to connect to UCP server
    const connected = await ucpClient.connect();
    statusBarManager.updateConnectionStatus(connected);

    // Register providers
    const chatProvider = new ChatViewProvider(context.extensionUri, ucpClient, contextCapture);
    const toolsProvider = new ToolsTreeProvider(ucpClient);
    const contextProvider = new ContextTreeProvider(contextCapture);

    // Register webview provider for chat
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('ucp.chat', chatProvider)
    );

    // Register tree providers
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('ucp.tools', toolsProvider)
    );
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('ucp.context', contextProvider)
    );

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('ucp.startChat', () => {
            vscode.commands.executeCommand('ucp.chat.focus');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucp.showTools', async () => {
            const tools = await ucpClient.getAvailableTools();
            if (tools.length === 0) {
                vscode.window.showInformationMessage('No tools available. Is UCP server running?');
                return;
            }

            const items = tools.map(t => ({
                label: t.name,
                description: t.description?.substring(0, 60),
                detail: `Tags: ${t.tags?.join(', ') || 'none'}`,
            }));

            vscode.window.showQuickPick(items, {
                placeHolder: 'Available UCP Tools',
                matchOnDescription: true,
            });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucp.predictTools', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor');
                return;
            }

            // Get context from current selection or surrounding code
            const context = contextCapture.captureEditorContext(editor);

            statusBarManager.showPredicting();

            try {
                const prediction = await ucpClient.predictTools(context.text, []);
                toolsProvider.updatePrediction(prediction);

                if (prediction.tools.length > 0) {
                    const toolNames = prediction.tools.map(t => t.name).join(', ');
                    vscode.window.showInformationMessage(`Predicted tools: ${toolNames}`);
                } else {
                    vscode.window.showInformationMessage('No specific tools predicted for this context');
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Prediction failed: ${error}`);
            } finally {
                statusBarManager.hidePredicting();
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucp.configure', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'ucp');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucp.clearHistory', () => {
            chatProvider.clearHistory();
            vscode.window.showInformationMessage('Chat history cleared');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucp.exportTrainingData', async () => {
            const data = chatProvider.exportTrainingData();

            const uri = await vscode.window.showSaveDialog({
                filters: { 'JSON Lines': ['jsonl'] },
                defaultUri: vscode.Uri.file('ucp_training_data.jsonl'),
            });

            if (uri) {
                const buffer = Buffer.from(data, 'utf-8');
                await vscode.workspace.fs.writeFile(uri, buffer);
                vscode.window.showInformationMessage(`Training data exported to ${uri.fsPath}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucp.toggleServer', async () => {
            const connected = await ucpClient.toggle();
            statusBarManager.updateConnectionStatus(connected);
            vscode.window.showInformationMessage(
                connected ? 'Connected to UCP server' : 'Disconnected from UCP server'
            );
        })
    );

    // Listen for context changes
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(async (editor) => {
            if (editor && config.get<boolean>('captureContext', true)) {
                const ctx = contextCapture.captureEditorContext(editor);
                contextProvider.updateContext(ctx);

                // Auto-predict if enabled
                if (config.get<boolean>('showPredictions', true)) {
                    try {
                        const prediction = await ucpClient.predictTools(ctx.text, []);
                        toolsProvider.updatePrediction(prediction);
                        statusBarManager.updatePrediction(prediction);
                    } catch {
                        // Silently fail predictions
                    }
                }
            }
        })
    );

    // Listen for selection changes
    context.subscriptions.push(
        vscode.window.onDidChangeTextEditorSelection(async (event) => {
            if (config.get<boolean>('captureContext', true)) {
                const ctx = contextCapture.captureSelectionContext(event);
                if (ctx) {
                    contextProvider.updateContext(ctx);
                }
            }
        })
    );

    // Watch for configuration changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async (event) => {
            if (event.affectsConfiguration('ucp.serverUrl')) {
                const newUrl = config.get<string>('serverUrl', 'http://localhost:8765');
                ucpClient.setServerUrl(newUrl);
                const connected = await ucpClient.connect();
                statusBarManager.updateConnectionStatus(connected);
            }
        })
    );

    // Add status bar and context capture to disposables
    context.subscriptions.push(statusBarManager);
    context.subscriptions.push(contextCapture);

    console.log('UCP extension activated');
}

export function deactivate() {
    console.log('UCP extension deactivating...');
    ucpClient?.disconnect();
}
