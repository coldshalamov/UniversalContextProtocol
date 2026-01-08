/**
 * UCP Desktop - Main App Component
 */

import React, { useState, useEffect } from 'react';
import TitleBar from './components/TitleBar';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import SettingsModal from './components/SettingsModal';

interface Chat {
    id: string;
    title: string;
    messages: Message[];
    createdAt: number;
}

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    toolsUsed?: string[];
}

function App() {
    const [theme, setTheme] = useState<'light' | 'dark'>('dark');
    const [ucpConnected, setUcpConnected] = useState(false);
    const [provider, setProvider] = useState('anthropic');
    const [model, setModel] = useState('claude-sonnet-4-20250514');
    const [chats, setChats] = useState<Chat[]>([]);
    const [activeChat, setActiveChat] = useState<Chat | null>(null);
    const [showSettings, setShowSettings] = useState(false);
    const [loading, setLoading] = useState(false);

    // Initialize
    useEffect(() => {
        // Get theme
        window.ucp.theme.get().then(setTheme);

        // Get provider/model settings
        window.ucp.settings.get('provider').then((p) => p && setProvider(p as string));
        window.ucp.settings.get('model').then((m) => m && setModel(m as string));

        // Check UCP connection
        window.ucp.ucp.isConnected().then(setUcpConnected);

        // Listen for UCP status changes
        const cleanup = window.ucp.ucp.onStatus(setUcpConnected);

        // Create initial chat
        createNewChat();

        return cleanup;
    }, []);

    // Apply theme
    useEffect(() => {
        document.body.className = theme;
    }, [theme]);

    const createNewChat = () => {
        const newChat: Chat = {
            id: `chat_${Date.now()}`,
            title: 'New Chat',
            messages: [],
            createdAt: Date.now(),
        };
        setChats(prev => [newChat, ...prev]);
        setActiveChat(newChat);
    };

    const deleteChat = (id: string) => {
        setChats(prev => prev.filter(c => c.id !== id));
        if (activeChat?.id === id) {
            const remaining = chats.filter(c => c.id !== id);
            setActiveChat(remaining[0] || null);
        }
    };

    const sendMessage = async (content: string) => {
        if (!activeChat || !content.trim()) return;

        const userMessage: Message = {
            id: `msg_${Date.now()}`,
            role: 'user',
            content,
            timestamp: Date.now(),
        };

        // Update chat with user message
        const updatedChat = {
            ...activeChat,
            messages: [...activeChat.messages, userMessage],
            title: activeChat.messages.length === 0 ? content.slice(0, 30) : activeChat.title,
        };
        setActiveChat(updatedChat);
        setChats(prev => prev.map(c => c.id === updatedChat.id ? updatedChat : c));

        setLoading(true);

        try {
            // Get tool predictions from UCP
            let tools: unknown[] = [];
            if (ucpConnected) {
                const prediction = await window.ucp.ucp.predictTools(content, []);
                tools = (prediction as any).tools || [];
            }

            // Prepare messages for API
            const messages = updatedChat.messages.map(m => ({
                role: m.role,
                content: m.content,
            }));

            // Add system message
            messages.unshift({
                role: 'system' as const,
                content: 'You are a helpful AI assistant. Be concise but thorough.',
            });

            // Send to LLM
            const response = await window.ucp.chat.send(messages, provider, model, tools);

            const assistantMessage: Message = {
                id: `msg_${Date.now()}`,
                role: 'assistant',
                content: (response as any).content || '',
                timestamp: Date.now(),
                toolsUsed: (response as any).toolCalls?.map((tc: any) => tc.name),
            };

            // Update chat with assistant message
            const finalChat = {
                ...updatedChat,
                messages: [...updatedChat.messages, assistantMessage],
            };
            setActiveChat(finalChat);
            setChats(prev => prev.map(c => c.id === finalChat.id ? finalChat : c));

        } catch (error) {
            console.error('Chat error:', error);

            const errorMessage: Message = {
                id: `msg_${Date.now()}`,
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error}`,
                timestamp: Date.now(),
            };

            const errorChat = {
                ...updatedChat,
                messages: [...updatedChat.messages, errorMessage],
            };
            setActiveChat(errorChat);
            setChats(prev => prev.map(c => c.id === errorChat.id ? errorChat : c));
        }

        setLoading(false);
    };

    const toggleTheme = async () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        await window.ucp.theme.set(newTheme);
    };

    return (
        <div className="app">
            <TitleBar
                ucpConnected={ucpConnected}
                onToggleTheme={toggleTheme}
                onSettings={() => setShowSettings(true)}
            />

            <div className="app-content">
                <Sidebar
                    chats={chats}
                    activeChat={activeChat}
                    onSelectChat={setActiveChat}
                    onNewChat={createNewChat}
                    onDeleteChat={deleteChat}
                />

                <ChatView
                    chat={activeChat}
                    loading={loading}
                    provider={provider}
                    model={model}
                    onSendMessage={sendMessage}
                />
            </div>

            {showSettings && (
                <SettingsModal
                    provider={provider}
                    model={model}
                    onProviderChange={setProvider}
                    onModelChange={setModel}
                    onClose={() => setShowSettings(false)}
                />
            )}
        </div>
    );
}

export default App;
