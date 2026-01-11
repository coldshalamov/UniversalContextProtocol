/**
 * Settings Modal Component
 */

import React, { useState, useEffect } from 'react';

interface Provider {
    name: string;
    displayName: string;
    models: string[];
}

interface SettingsModalProps {
    provider: string;
    model: string;
    onProviderChange: (provider: string) => void;
    onModelChange: (model: string) => void;
    onClose: () => void;
}

function SettingsModal({
    provider,
    model,
    onProviderChange,
    onModelChange,
    onClose,
}: SettingsModalProps) {
    const [providers, setProviders] = useState<Provider[]>([]);
    const [models, setModels] = useState<string[]>([]);
    const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
    const [newApiKey, setNewApiKey] = useState('');
    const [selectedProvider, setSelectedProvider] = useState(provider);
    const [selectedModel, setSelectedModel] = useState(model);
    const [ucpUrl, setUcpUrl] = useState('http://localhost:8765');

    useEffect(() => {
        // Load providers
        window.ucp.providers.list().then((list) => {
            setProviders(list as Provider[]);
        });

        // Load UCP URL
        window.ucp.settings.get('ucpServerUrl').then((url) => {
            if (url) setUcpUrl(url as string);
        });

        // Check which providers have API keys
        const checkKeys = async () => {
            const keysStatus: Record<string, boolean> = {};
            for (const p of ['openai', 'anthropic', 'google', 'groq', 'together', 'deepseek', 'mistral']) {
                keysStatus[p] = await window.ucp.apiKeys.has(p);
            }
            setApiKeys(keysStatus);
        };
        checkKeys();
    }, []);

    useEffect(() => {
        // Load models for selected provider
        window.ucp.providers.models(selectedProvider).then((list) => {
            setModels(list);
            if (!list.includes(selectedModel)) {
                setSelectedModel(list[0] || '');
            }
        });
    }, [selectedProvider]);

    const handleSave = async () => {
        await window.ucp.settings.set('provider', selectedProvider);
        await window.ucp.settings.set('model', selectedModel);
        await window.ucp.settings.set('ucpServerUrl', ucpUrl);

        onProviderChange(selectedProvider);
        onModelChange(selectedModel);
        onClose();
    };

    const handleSetApiKey = async () => {
        if (newApiKey.trim()) {
            await window.ucp.apiKeys.set(selectedProvider, newApiKey.trim());
            setApiKeys({ ...apiKeys, [selectedProvider]: true });
            setNewApiKey('');
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Settings</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="modal-content">
                    <section className="settings-section">
                        <h3>AI Provider</h3>
                        <div className="setting-row">
                            <label>Provider</label>
                            <select
                                value={selectedProvider}
                                onChange={(e) => setSelectedProvider(e.target.value)}
                            >
                                {providers.map((p) => (
                                    <option key={p.name} value={p.name}>
                                        {p.displayName} {apiKeys[p.name] ? '✓' : ''}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="setting-row">
                            <label>Model</label>
                            <select
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                            >
                                {models.map((m) => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>

                        <div className="setting-row">
                            <label>API Key {apiKeys[selectedProvider] ? '(set)' : '(not set)'}</label>
                            <div className="api-key-input">
                                <input
                                    type="password"
                                    value={newApiKey}
                                    onChange={(e) => setNewApiKey(e.target.value)}
                                    placeholder={apiKeys[selectedProvider] ? '••••••••' : 'Enter API key'}
                                />
                                <button onClick={handleSetApiKey} disabled={!newApiKey.trim()}>
                                    Save Key
                                </button>
                            </div>
                        </div>
                    </section>

                    <section className="settings-section">
                        <h3>UCP Server</h3>
                        <div className="setting-row">
                            <label>Server URL</label>
                            <input
                                type="text"
                                value={ucpUrl}
                                onChange={(e) => setUcpUrl(e.target.value)}
                                placeholder="http://localhost:8765"
                            />
                        </div>
                    </section>

                    <section className="settings-section">
                        <h3>Appearance</h3>
                        <div className="setting-row">
                            <label>Theme</label>
                            <div className="theme-buttons">
                                <button
                                    className="theme-btn"
                                    onClick={() => window.ucp.theme.set('light')}
                                >
                                    ☀️ Light
                                </button>
                                <button
                                    className="theme-btn"
                                    onClick={() => window.ucp.theme.set('dark')}
                                >
                                    🌙 Dark
                                </button>
                                <button
                                    className="theme-btn"
                                    onClick={() => window.ucp.theme.set('system')}
                                >
                                    🖥️ System
                                </button>
                            </div>
                        </div>
                    </section>
                </div>

                <div className="modal-footer">
                    <button className="cancel-btn" onClick={onClose}>Cancel</button>
                    <button className="save-btn" onClick={handleSave}>Save Changes</button>
                </div>
            </div>
        </div>
    );
}

export default SettingsModal;
