/**
 * UCP Desktop - Main Electron Process
 * 
 * Creates the main window and handles IPC communication
 */

import { app, BrowserWindow, ipcMain, shell, Menu, Tray, nativeTheme } from 'electron';
import { join } from 'path';
import Store from 'electron-store';
import { UCPService } from './ucpService';
import { ProviderService } from './providerService';

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
    app.quit();
}

// Initialize persistent store
const store = new Store({
    defaults: {
        windowBounds: { width: 1200, height: 800 },
        theme: 'system',
        provider: 'anthropic',
        model: 'claude-sonnet-4-20250514',
        ucpServerUrl: 'http://localhost:8765',
        apiKeys: {},
    },
});

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let ucpService: UCPService;
let providerService: ProviderService;

function createWindow(): void {
    const bounds = store.get('windowBounds') as { width: number; height: number };

    mainWindow = new BrowserWindow({
        width: bounds.width,
        height: bounds.height,
        minWidth: 600,
        minHeight: 400,
        frame: false, // Frameless for custom title bar
        transparent: false,
        backgroundColor: nativeTheme.shouldUseDarkColors ? '#1a1a2e' : '#ffffff',
        titleBarStyle: 'hiddenInset',
        webPreferences: {
            preload: join(__dirname, '../preload/preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: false,
        },
        show: false, // Show when ready
        icon: join(__dirname, '../../resources/icon.png'),
    });

    // Show when ready to prevent flash
    mainWindow.once('ready-to-show', () => {
        mainWindow?.show();
    });

    // Save window bounds on resize
    mainWindow.on('resize', () => {
        if (mainWindow) {
            const [width, height] = mainWindow.getSize();
            store.set('windowBounds', { width, height });
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Load the app
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
    }

    // Open external links in browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });
}

function createTray(): void {
    tray = new Tray(join(__dirname, '../../resources/icon.png'));

    const contextMenu = Menu.buildFromTemplate([
        { label: 'Show UCP Desktop', click: () => mainWindow?.show() },
        { type: 'separator' },
        { label: 'New Chat', click: () => mainWindow?.webContents.send('new-chat') },
        { type: 'separator' },
        { label: 'Quit', click: () => app.quit() },
    ]);

    tray.setToolTip('UCP Desktop');
    tray.setContextMenu(contextMenu);

    tray.on('click', () => {
        mainWindow?.show();
    });
}

function setupIPC(): void {
    // Window controls
    ipcMain.on('window:minimize', () => mainWindow?.minimize());
    ipcMain.on('window:maximize', () => {
        if (mainWindow?.isMaximized()) {
            mainWindow.unmaximize();
        } else {
            mainWindow?.maximize();
        }
    });
    ipcMain.on('window:close', () => mainWindow?.hide());

    // Settings
    ipcMain.handle('settings:get', (_, key) => store.get(key));
    ipcMain.handle('settings:set', (_, key, value) => store.set(key, value));
    ipcMain.handle('settings:getAll', () => store.store);

    // API Keys (stored securely)
    ipcMain.handle('apiKey:set', (_, provider, key) => {
        const keys = store.get('apiKeys') as Record<string, string>;
        keys[provider] = key;
        store.set('apiKeys', keys);
        providerService.updateApiKey(provider, key);
    });

    ipcMain.handle('apiKey:get', (_, provider) => {
        const keys = store.get('apiKeys') as Record<string, string>;
        return keys[provider] || null;
    });

    ipcMain.handle('apiKey:has', (_, provider) => {
        const keys = store.get('apiKeys') as Record<string, string>;
        return !!keys[provider];
    });

    // UCP Service
    ipcMain.handle('ucp:connect', () => ucpService.connect());
    ipcMain.handle('ucp:disconnect', () => ucpService.disconnect());
    ipcMain.handle('ucp:isConnected', () => ucpService.isConnected());
    ipcMain.handle('ucp:predictTools', (_, context, recentTools) =>
        ucpService.predictTools(context, recentTools));
    ipcMain.handle('ucp:getTools', () => ucpService.getAvailableTools());
    ipcMain.handle('ucp:searchTools', (_, query) => ucpService.searchTools(query));
    ipcMain.handle('ucp:reportUsage', (_, prediction, used, success) =>
        ucpService.reportUsage(prediction, used, success));

    // Provider Service (Chat)
    ipcMain.handle('chat:send', async (_, messages, provider, model, tools) => {
        return await providerService.chat(messages, provider, model, tools);
    });

    ipcMain.handle('chat:stream', async (event, messages, provider, model, tools) => {
        for await (const chunk of providerService.streamChat(messages, provider, model, tools)) {
            event.sender.send('chat:chunk', chunk);
        }
        event.sender.send('chat:done');
    });

    ipcMain.handle('providers:list', () => providerService.listProviders());
    ipcMain.handle('providers:models', (_, provider) => providerService.getModels(provider));

    // Theme
    ipcMain.handle('theme:get', () => {
        const theme = store.get('theme') as string;
        if (theme === 'system') {
            return nativeTheme.shouldUseDarkColors ? 'dark' : 'light';
        }
        return theme;
    });

    ipcMain.handle('theme:set', (_, theme) => {
        store.set('theme', theme);
        if (theme === 'system') {
            nativeTheme.themeSource = 'system';
        } else {
            nativeTheme.themeSource = theme;
        }
    });
}

// App lifecycle
app.whenReady().then(() => {
    // Initialize services
    const ucpUrl = store.get('ucpServerUrl') as string;
    ucpService = new UCPService(ucpUrl);
    providerService = new ProviderService(store.get('apiKeys') as Record<string, string>);

    setupIPC();
    createWindow();
    createTray();

    // Auto-connect to UCP
    ucpService.connect().then(connected => {
        mainWindow?.webContents.send('ucp:status', connected);
    });

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    ucpService?.disconnect();
});

// Handle second instance
app.on('second-instance', () => {
    if (mainWindow) {
        if (mainWindow.isMinimized()) mainWindow.restore();
        mainWindow.focus();
    }
});
