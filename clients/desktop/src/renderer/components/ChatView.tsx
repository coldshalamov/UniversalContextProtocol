/**
 * Chat View Component - Main chat interface
 */

import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    toolsUsed?: string[];
}

interface Chat {
    id: string;
    title: string;
    messages: Message[];
    createdAt: number;
}

interface ChatViewProps {
    chat: Chat | null;
    loading: boolean;
    provider: string;
    model: string;
    onSendMessage: (content: string) => void;
}

function ChatView({ chat, loading, provider, model, onSendMessage }: ChatViewProps) {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chat?.messages]);

    // Focus input
    useEffect(() => {
        inputRef.current?.focus();
    }, [chat?.id]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !loading) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    if (!chat) {
        return (
            <div className="chat-view empty">
                <div className="welcome">
                    <div className="welcome-icon">⚡</div>
                    <h1>Welcome to UCP Desktop</h1>
                    <p>Start a new conversation to begin chatting with AI, powered by intelligent tool injection.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="chat-view">
            <div className="chat-header">
                <div className="chat-title">{chat.title}</div>
                <div className="chat-info">
                    <span className="provider-badge">{provider}</span>
                    <span className="model-badge">{model}</span>
                </div>
            </div>

            <div className="messages-container">
                {chat.messages.length === 0 ? (
                    <div className="empty-chat">
                        <div className="suggestions">
                            <h3>Try asking:</h3>
                            <div className="suggestion-grid">
                                <button
                                    className="suggestion"
                                    onClick={() => onSendMessage('What can you help me with?')}
                                >
                                    <span className="suggestion-icon">🤔</span>
                                    <span>What can you help me with?</span>
                                </button>
                                <button
                                    className="suggestion"
                                    onClick={() => onSendMessage('Write a Python function to sort a list')}
                                >
                                    <span className="suggestion-icon">🐍</span>
                                    <span>Write a Python sort function</span>
                                </button>
                                <button
                                    className="suggestion"
                                    onClick={() => onSendMessage('Explain how MCP works')}
                                >
                                    <span className="suggestion-icon">📚</span>
                                    <span>Explain how MCP works</span>
                                </button>
                                <button
                                    className="suggestion"
                                    onClick={() => onSendMessage('What tools are available?')}
                                >
                                    <span className="suggestion-icon">🔧</span>
                                    <span>What tools are available?</span>
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="messages">
                        {chat.messages.map(message => (
                            <MessageBubble key={message.id} message={message} />
                        ))}

                        {loading && (
                            <div className="message assistant">
                                <div className="message-avatar">🤖</div>
                                <div className="message-content">
                                    <div className="typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            <form className="input-container" onSubmit={handleSubmit}>
                <div className="input-wrapper">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
                        rows={1}
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        className="send-btn"
                        disabled={!input.trim() || loading}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z" />
                        </svg>
                    </button>
                </div>
                <div className="input-hint">
                    <span>Press Enter to send · Shift+Enter for new line</span>
                </div>
            </form>
        </div>
    );
}

export default ChatView;
