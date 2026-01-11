# UCP VS Code Extension

Intelligent tool injection for AI-powered coding. This extension integrates the Universal Context Protocol (UCP) into VS Code, automatically predicting and injecting the right tools based on your code context.

## Features

### 🔮 Context-Aware Tool Prediction
Automatically analyzes your code and predicts which tools will be needed:
- Current file and language detection
- Error and warning analysis
- Selection-based context
- Recent edit tracking

### 💬 In-Editor Chat
Chat with AI directly in VS Code with tools automatically injected:
- Streaming responses
- Markdown rendering with syntax highlighting
- Tool usage indicators

### 📊 Prediction Visualization
See what UCP is thinking:
- Real-time tool predictions in the sidebar
- Confidence scores for each tool
- Context preview

### 🔧 Deep VS Code Integration
- Status bar showing UCP connection status
- Keyboard shortcuts for quick access
- Context menu for code selection

## Quick Start

1. Install the extension
2. Start the UCP server: `ucp serve`
3. Configure your API key (Cmd/Ctrl+Shift+P → "UCP: Configure Settings")
4. Start chatting! (Cmd/Ctrl+Shift+U)

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| UCP: Start Chat | `Ctrl+Shift+U` | Open the chat panel |
| UCP: Predict Tools | Right-click menu | Get predictions for selected code |
| UCP: Show Available Tools | - | Browse all indexed tools |
| UCP: Configure Settings | - | Open settings |
| UCP: Export Training Data | - | Export session for UCP learning |
| UCP: Toggle Server Connection | - | Connect/disconnect from UCP |

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ucp.serverUrl` | `http://localhost:8765` | UCP server URL |
| `ucp.provider` | `anthropic` | Default LLM provider |
| `ucp.model` | `claude-sonnet-4-20250514` | Default model |
| `ucp.autoInject` | `true` | Auto-inject predicted tools |
| `ucp.captureContext` | `true` | Capture workspace context |
| `ucp.maxTools` | `5` | Max tools to inject |
| `ucp.showPredictions` | `true` | Show predictions in status bar |

## Views

### Chat View
The main chat interface in the sidebar. Messages are rendered with Markdown support including code blocks with syntax highlighting.

### Predicted Tools View
Shows tools predicted to be useful for the current context:
- 🔮 **Predicted Tools**: Tools selected for the current context
- 🔧 **All Available**: All tools indexed by UCP

### Context View
Shows what context UCP is using:
- Current file and language
- Line number
- Selection (if any)
- Diagnostics (errors/warnings)
- Open files

## How It Works

1. **Context Capture**: The extension monitors your editor activity, capturing:
   - Active file and language
   - Cursor position and selection
   - Surrounding code (15 lines before/after)
   - Diagnostics from the language server
   - Recent edits

2. **Tool Prediction**: This context is sent to the UCP server, which returns predicted tools based on semantic similarity and learned patterns.

3. **LLM Integration**: When you chat, the extension:
   - Adds captured context to your message
   - Injects predicted tools into the LLM request
   - Streams the response back to the chat view

4. **Feedback Loop**: After each interaction, the extension reports which tools were actually used, helping UCP improve future predictions.

## Development

### Building

```bash
cd clients/vscode
npm install
npm run compile
```

### Running in Dev Mode

1. Open the extension folder in VS Code
2. Press F5 to launch the Extension Development Host
3. The extension will be active in the new window

### Packaging

```bash
npm run package
# Creates ucp-vscode-0.1.0.vsix
```

### Installing from VSIX

```bash
code --install-extension ucp-vscode-0.1.0.vsix
```

## API

The extension exposes these VS Code commands that can be called programmatically:

```typescript
// Start chat interface
vscode.commands.executeCommand('ucp.startChat');

// Get tool predictions for text
const prediction = await vscode.commands.executeCommand('ucp.predictTools');

// Check UCP connection
const connected = await vscode.commands.executeCommand('ucp.isConnected');
```

## Telemetry

The extension collects the following data for UCP learning (stored locally):
- Tool predictions and which were used
- Context snapshots (truncated for privacy)
- Session durations

Export this data with "UCP: Export Training Data" to contribute to UCP improvement.

## Requirements

- VS Code 1.85.0 or later
- UCP Server running (see main README)
- Node.js 18+ (for development)

## Known Issues

- Streaming responses may have slight delay
- Context capture is limited to text files
- Tool prediction requires active UCP server

## Release Notes

### 0.1.0
- Initial release
- Chat view with streaming
- Tool prediction and display
- Context capture
- Training data export
