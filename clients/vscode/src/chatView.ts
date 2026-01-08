/**
 * Chat View Provider - Webview-based chat interface
 */

import * as vscode from 'vscode';
import { UCPClient, Message, ToolPrediction } from './ucpClient';
import { ContextCapture, EditorContext } from './contextCapture';
import { marked } from 'marked';

interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    toolsUsed?: string[];
}

interface TrainingData {
    sessionId: string;
    messages: ChatMessage[];
    toolPredictions: Array<{
        context: string;
        predicted: string[];
        used: string[];
    }>;
}

export class ChatViewProvider implements vscode.WebviewViewProvider {
    private view?: vscode.WebviewView;
    private messages: ChatMessage[] = [];
    private toolPredictions: Array<{ context: string; predicted: string[]; used: string[] }> = [];
    private sessionId: string;

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly ucpClient: UCPClient,
        private readonly contextCapture: ContextCapture
    ) {
        this.sessionId = `session_${Date.now()}`;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ): void {
        this.view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri],
        };

        webviewView.webview.html = this.getHtmlContent();

        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(async (message) => {
            switch (message.type) {
                case 'sendMessage':
                    await this.handleUserMessage(message.content);
                    break;
                case 'clearHistory':
                    this.clearHistory();
                    break;
                case 'regenerate':
                    await this.regenerateLastResponse();
                    break;
            }
        });
    }

    private async handleUserMessage(content: string): Promise<void> {
        // Add user message
        const userMessage: ChatMessage = {
            role: 'user',
            content,
            timestamp: Date.now(),
        };
        this.messages.push(userMessage);
        this.updateView();

        // Get editor context
        const editor = vscode.window.activeTextEditor;
        let editorContext: EditorContext | null = null;
        if (editor) {
            editorContext = this.contextCapture.captureEditorContext(editor);
        }

        // Build context for UCP
        const ucpContext = editorContext
            ? `${content}\n\nContext:\n${editorContext.text}`
            : content;

        // Get tool predictions
        let prediction: ToolPrediction | null = null;
        if (this.ucpClient.isConnected()) {
            prediction = await this.ucpClient.predictTools(ucpContext, []);
            if (prediction.tools.length > 0) {
                this.toolPredictions.push({
                    context: ucpContext.substring(0, 500),
                    predicted: prediction.tools.map(t => t.name),
                    used: [],
                });
            }
        }

        // Show typing indicator
        this.sendToView({ type: 'typing', isTyping: true });

        try {
            // Send to LLM via UCP (or direct if not connected)
            const messages: Message[] = this.messages.map(m => ({
                role: m.role,
                content: m.content,
            }));

            // Add system message with context
            if (editorContext) {
                messages.unshift({
                    role: 'system',
                    content: `You are a helpful coding assistant. The user is working in ${editorContext.language} in file ${editorContext.fileName}.`,
                });
            }

            const response = await this.ucpClient.chat(
                messages,
                prediction?.tools
            );

            // Add assistant message
            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: response.content,
                timestamp: Date.now(),
                toolsUsed: response.toolCalls?.map(tc => tc.name),
            };
            this.messages.push(assistantMessage);

            // Record tool usage
            if (response.toolCalls && this.toolPredictions.length > 0) {
                const lastPrediction = this.toolPredictions[this.toolPredictions.length - 1];
                lastPrediction.used = response.toolCalls.map(tc => tc.name);

                // Report feedback to UCP
                if (prediction) {
                    await this.ucpClient.reportUsage(
                        prediction,
                        response.toolCalls.map(tc => tc.name),
                        true
                    );
                }
            }

        } catch (error) {
            // Handle error - still show a message
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error}. Please check if the UCP server is running.`,
                timestamp: Date.now(),
            };
            this.messages.push(errorMessage);
        }

        this.sendToView({ type: 'typing', isTyping: false });
        this.updateView();
    }

    private async regenerateLastResponse(): Promise<void> {
        // Remove last assistant message and regenerate
        if (this.messages.length >= 2 && this.messages[this.messages.length - 1].role === 'assistant') {
            this.messages.pop();
            const lastUserMessage = this.messages[this.messages.length - 1];
            if (lastUserMessage.role === 'user') {
                this.messages.pop();
                await this.handleUserMessage(lastUserMessage.content);
            }
        }
    }

    clearHistory(): void {
        this.messages = [];
        this.toolPredictions = [];
        this.sessionId = `session_${Date.now()}`;
        this.updateView();
    }

    exportTrainingData(): string {
        const data: TrainingData = {
            sessionId: this.sessionId,
            messages: this.messages,
            toolPredictions: this.toolPredictions,
        };
        return JSON.stringify(data) + '\n';
    }

    private updateView(): void {
        if (!this.view) return;

        const messagesHtml = this.messages.map(m => {
            const isUser = m.role === 'user';
            const contentHtml = marked(m.content);
            const toolsHtml = m.toolsUsed?.length
                ? `<div class="tools-used">🔧 ${m.toolsUsed.join(', ')}</div>`
                : '';

            return `
                <div class="message ${isUser ? 'user' : 'assistant'}">
                    <div class="avatar">${isUser ? '👤' : '🤖'}</div>
                    <div class="content">
                        ${contentHtml}
                        ${toolsHtml}
                    </div>
                </div>
            `;
        }).join('');

        this.sendToView({ type: 'messages', html: messagesHtml });
    }

    private sendToView(message: object): void {
        this.view?.webview.postMessage(message);
    }

    private getHtmlContent(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UCP Chat</title>
    <style>
        :root {
            --primary: #7c3aed;
            --primary-dark: #5b21b6;
            --bg: var(--vscode-editor-background);
            --fg: var(--vscode-editor-foreground);
            --border: var(--vscode-panel-border);
            --user-bg: var(--vscode-textBlockQuote-background);
            --assistant-bg: var(--vscode-editor-inactiveSelectionBackground);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            background: var(--bg);
            color: var(--fg);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }
        
        .message {
            display: flex;
            gap: 10px;
            margin-bottom: 16px;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
        }
        
        .content {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 12px;
            line-height: 1.5;
        }
        
        .message.user .content {
            background: var(--primary);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .content {
            background: var(--assistant-bg);
            border-bottom-left-radius: 4px;
        }
        
        .content pre {
            background: rgba(0,0,0,0.2);
            padding: 8px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 8px 0;
        }
        
        .content code {
            font-family: var(--vscode-editor-font-family);
            font-size: 0.9em;
        }
        
        .tools-used {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(255,255,255,0.1);
            font-size: 0.85em;
            opacity: 0.8;
        }
        
        .typing-indicator {
            display: none;
            padding: 12px;
        }
        
        .typing-indicator.visible {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--primary);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        .input-container {
            padding: 12px;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 8px;
        }
        
        #input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            font-family: inherit;
            font-size: inherit;
            resize: none;
            outline: none;
            min-height: 40px;
            max-height: 120px;
        }
        
        #input:focus {
            border-color: var(--primary);
        }
        
        button {
            padding: 8px 16px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        
        button:hover {
            background: var(--primary-dark);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            opacity: 0.7;
        }
        
        .empty-state h3 {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="chat-container" id="chat">
        <div class="empty-state">
            <h3>🚀 UCP Chat</h3>
            <p>Ask me anything! I'll use the right tools automatically.</p>
        </div>
    </div>
    
    <div class="typing-indicator" id="typing">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    
    <div class="input-container">
        <textarea id="input" placeholder="Type a message..." rows="1"></textarea>
        <button id="send">Send</button>
    </div>
    
    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chat');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('send');
        const typingIndicator = document.getElementById('typing');
        
        function sendMessage() {
            const content = input.value.trim();
            if (!content) return;
            
            vscode.postMessage({ type: 'sendMessage', content });
            input.value = '';
            input.style.height = '40px';
            sendBtn.disabled = true;
        }
        
        sendBtn.addEventListener('click', sendMessage);
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            sendBtn.disabled = !input.value.trim();
        });
        
        window.addEventListener('message', (event) => {
            const message = event.data;
            
            switch (message.type) {
                case 'messages':
                    chatContainer.innerHTML = message.html || '';
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    sendBtn.disabled = false;
                    break;
                case 'typing':
                    typingIndicator.classList.toggle('visible', message.isTyping);
                    break;
            }
        });
    </script>
</body>
</html>`;
    }
}
