/**
 * Status Bar Manager - Shows UCP status and predictions in status bar
 */

import * as vscode from 'vscode';
import { UCPClient, ToolPrediction } from './ucpClient';

export class StatusBarManager implements vscode.Disposable {
    private statusItem: vscode.StatusBarItem;
    private predictionItem: vscode.StatusBarItem;

    constructor(private readonly ucpClient: UCPClient) {
        // Main status item
        this.statusItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusItem.command = 'ucp.toggleServer';
        this.statusItem.tooltip = 'Click to toggle UCP connection';
        this.statusItem.show();

        // Prediction indicator
        this.predictionItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            99
        );
        this.predictionItem.command = 'ucp.showTools';
        this.predictionItem.tooltip = 'Click to see available tools';

        this.updateConnectionStatus(false);
    }

    dispose(): void {
        this.statusItem.dispose();
        this.predictionItem.dispose();
    }

    updateConnectionStatus(connected: boolean): void {
        if (connected) {
            this.statusItem.text = '$(check) UCP';
            this.statusItem.backgroundColor = undefined;
        } else {
            this.statusItem.text = '$(circle-slash) UCP';
            this.statusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
    }

    updatePrediction(prediction: ToolPrediction): void {
        if (prediction.tools.length > 0) {
            const count = prediction.tools.length;
            this.predictionItem.text = `$(sparkle) ${count} tool${count > 1 ? 's' : ''}`;
            this.predictionItem.tooltip = prediction.tools.map(t => t.name).join(', ');
            this.predictionItem.show();
        } else {
            this.predictionItem.hide();
        }
    }

    showPredicting(): void {
        this.predictionItem.text = '$(sync~spin) Predicting...';
        this.predictionItem.show();
    }

    hidePredicting(): void {
        this.predictionItem.hide();
    }
}
