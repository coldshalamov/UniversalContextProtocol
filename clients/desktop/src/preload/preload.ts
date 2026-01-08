/**
 * Preload Script - Exposes safe APIs to the renderer
 */

import { contextBridge, ipcRenderer } from 'electron';

// Types for the exposed API
export interface UCPApi {
    // Window controls
    window: {
        minimize: () => void;
        maximize: () => void;
        close: () => void;
    };

    // Settings
    settings: {
        get: (key: string) => Promise<unknown>;
        set: (key: string, value: unknown) => Promise<void>;
        getAll: () => Promise<Record<string, unknown>>;
    };

    // API Keys
    apiKeys: {
        set: (provider: string, key: string) => Promise<void>;
        get: (provider: string) => Promise<string | null>;
        has: (provider: string) => Promise<boolean>;
    };

    // UCP
    ucp: {
        connect: () => Promise<boolean>;
        disconnect: () => Promise<void>;
        isConnected: () => Promise<boolean>;
        predictTools: (context: string, recentTools: string[]) => Promise<unknown>;
        getTools: () => Promise<unknown[]>;
        searchTools: (query: string) => Promise<unknown[]>;
        reportUsage: (prediction: unknown, used: string[], success: boolean) => Promise<boolean>;
        onStatus: (callback: (connected: boolean) => void) => () => void;
    };

    // Chat
    chat: {
        send: (messages: unknown[], provider: string, model: string, tools?: unknown[]) => Promise<unknown>;
        stream: (messages: unknown[], provider: string, model: string, tools?: unknown[]) => Promise<void>;
        onChunk: (callback: (chunk: unknown) => void) => () => void;
        onDone: (callback: () => void) => () => void;
    };

    // Providers
    providers: {
        list: () => Promise<unknown[]>;
        models: (provider: string) => Promise<string[]>;
    };

    // Theme
    theme: {
        get: () => Promise<'light' | 'dark'>;
        set: (theme: 'light' | 'dark' | 'system') => Promise<void>;
    };

    // Events
    on: (channel: string, callback: (...args: unknown[]) => void) => () => void;
}

// Expose APIs
contextBridge.exposeInMainWorld('ucp', {
    // Window controls
    window: {
        minimize: () => ipcRenderer.send('window:minimize'),
        maximize: () => ipcRenderer.send('window:maximize'),
        close: () => ipcRenderer.send('window:close'),
    },

    // Settings
    settings: {
        get: (key: string) => ipcRenderer.invoke('settings:get', key),
        set: (key: string, value: unknown) => ipcRenderer.invoke('settings:set', key, value),
        getAll: () => ipcRenderer.invoke('settings:getAll'),
    },

    // API Keys
    apiKeys: {
        set: (provider: string, key: string) => ipcRenderer.invoke('apiKey:set', provider, key),
        get: (provider: string) => ipcRenderer.invoke('apiKey:get', provider),
        has: (provider: string) => ipcRenderer.invoke('apiKey:has', provider),
    },

    // UCP
    ucp: {
        connect: () => ipcRenderer.invoke('ucp:connect'),
        disconnect: () => ipcRenderer.invoke('ucp:disconnect'),
        isConnected: () => ipcRenderer.invoke('ucp:isConnected'),
        predictTools: (context: string, recentTools: string[]) =>
            ipcRenderer.invoke('ucp:predictTools', context, recentTools),
        getTools: () => ipcRenderer.invoke('ucp:getTools'),
        searchTools: (query: string) => ipcRenderer.invoke('ucp:searchTools', query),
        reportUsage: (prediction: unknown, used: string[], success: boolean) =>
            ipcRenderer.invoke('ucp:reportUsage', prediction, used, success),
        onStatus: (callback: (connected: boolean) => void) => {
            const handler = (_: unknown, connected: boolean) => callback(connected);
            ipcRenderer.on('ucp:status', handler);
            return () => ipcRenderer.removeListener('ucp:status', handler);
        },
    },

    // Chat
    chat: {
        send: (messages: unknown[], provider: string, model: string, tools?: unknown[]) =>
            ipcRenderer.invoke('chat:send', messages, provider, model, tools),
        stream: (messages: unknown[], provider: string, model: string, tools?: unknown[]) =>
            ipcRenderer.invoke('chat:stream', messages, provider, model, tools),
        onChunk: (callback: (chunk: unknown) => void) => {
            const handler = (_: unknown, chunk: unknown) => callback(chunk);
            ipcRenderer.on('chat:chunk', handler);
            return () => ipcRenderer.removeListener('chat:chunk', handler);
        },
        onDone: (callback: () => void) => {
            const handler = () => callback();
            ipcRenderer.on('chat:done', handler);
            return () => ipcRenderer.removeListener('chat:done', handler);
        },
    },

    // Providers
    providers: {
        list: () => ipcRenderer.invoke('providers:list'),
        models: (provider: string) => ipcRenderer.invoke('providers:models', provider),
    },

    // Theme
    theme: {
        get: () => ipcRenderer.invoke('theme:get'),
        set: (theme: 'light' | 'dark' | 'system') => ipcRenderer.invoke('theme:set', theme),
    },

    // Generic event handler
    on: (channel: string, callback: (...args: unknown[]) => void) => {
        const handler = (_: unknown, ...args: unknown[]) => callback(...args);
        ipcRenderer.on(channel, handler);
        return () => ipcRenderer.removeListener(channel, handler);
    },
} as UCPApi);

// Declare window type extension
declare global {
    interface Window {
        ucp: UCPApi;
    }
}
