# UCP Desktop

A beautiful, premium desktop application for AI chat with intelligent tool injection. Built with Electron and React.

## ✨ Features

### 🎨 Stunning Design
- Modern glassmorphism UI inspired by ChatGPT Desktop and Claude Desktop
- Smooth animations and micro-interactions
- Dark and light themes with system preference detection
- Custom frameless window with native-feeling controls

### 🤖 Multi-Provider Support
Out of the box support for 10+ LLM providers:
- **OpenAI** - GPT-4, GPT-4-turbo, o1
- **Anthropic** - Claude 4, Claude 3.5 Sonnet
- **Google** - Gemini 2.0, Gemini 1.5 Pro
- **Groq** - Ultra-fast Llama inference
- **Together AI** - Open source models
- **DeepSeek** - DeepSeek Chat & Reasoner
- **Mistral** - Mistral Large
- **xAI** - Grok
- **Perplexity** - Web-connected AI
- **OpenRouter** - Multi-model router
- **Ollama** - Local models

### 🔧 Intelligent Tool Injection
Powered by UCP:
- Automatic tool prediction based on context
- Real-time connection status
- Tool usage indicators in messages
- Feedback loop for learning

### 💾 Session Management
- Multiple conversation threads
- Persistent chat history
- Quick access sidebar
- Training data export

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- UCP Server (optional, for tool prediction)

### Installation

```bash
cd clients/desktop
npm install
npm run dev
```

### Building for Production

```bash
# Windows
npm run package:win

# macOS
npm run package:mac

# Linux
npm run package:linux
```

## 🎮 Usage

### First Launch
1. Open Settings (⚙️ button or Cmd/Ctrl+,)
2. Select your preferred provider
3. Enter your API key
4. Start chatting!

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line |
| `Cmd/Ctrl+N` | New chat |
| `Cmd/Ctrl+,` | Open settings |

### Chat Interface
- Click suggestions to start a conversation
- Messages are rendered with full Markdown support
- Code blocks have syntax highlighting
- Tool usage is shown below messages

### Settings
- **Provider**: Select your LLM provider
- **Model**: Choose a model for the current provider
- **API Key**: Securely stored on your system
- **Theme**: Light, Dark, or System
- **UCP Server**: Configure the UCP server URL

## 🏗 Architecture

```
desktop/
├── src/
│   ├── main/           # Electron main process
│   │   ├── main.ts         # App lifecycle, IPC
│   │   ├── ucpService.ts   # UCP server client
│   │   └── providerService.ts  # LLM provider handler
│   ├── preload/        # Context bridge
│   │   └── preload.ts      # Safe API exposure
│   └── renderer/       # React UI
│       ├── App.tsx         # Main app component
│       ├── components/     # UI components
│       └── styles/         # SCSS styles
├── resources/          # App icons and assets
└── package.json        # Dependencies and build config
```

### Main Process
- Window management with custom title bar
- System tray with quick actions
- IPC handlers for renderer communication
- Persistent settings via electron-store
- LLM provider implementation

### Renderer Process
- React 18 with TypeScript
- SCSS with CSS custom properties
- Marked for Markdown rendering
- Fully reactive state management

## 🎨 Theming

The app uses CSS custom properties for easy theming:

```scss
:root {
  --bg-primary: #0f0f1a;
  --bg-secondary: #1a1a2e;
  --accent-primary: #7c3aed;
  --accent-gradient: linear-gradient(135deg, #7c3aed, #a855f7, #ec4899);
  // ...
}

body.light {
  --bg-primary: #ffffff;
  --bg-secondary: #f7f7f8;
  // ...
}
```

## 🔒 Security

- API keys stored using electron-store (encrypted on macOS via Keychain)
- Context isolation enabled
- Node integration disabled in renderer
- Preload script for safe IPC
- Content Security Policy enforced

## 📦 Distribution

### Windows
- NSIS installer (recommended)
- Portable executable

### macOS
- DMG installer
- App bundle

### Linux
- AppImage (universal)
- DEB package (Debian/Ubuntu)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test on your target platform(s)
5. Submit a pull request

## 📄 License

MIT License - see main repository LICENSE
