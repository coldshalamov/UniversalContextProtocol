/**
 * Sidebar Component - Chat history list
 */

import React from 'react';

interface Chat {
    id: string;
    title: string;
    messages: unknown[];
    createdAt: number;
}

interface SidebarProps {
    chats: Chat[];
    activeChat: Chat | null;
    onSelectChat: (chat: Chat) => void;
    onNewChat: () => void;
    onDeleteChat: (id: string) => void;
}

function Sidebar({ chats, activeChat, onSelectChat, onNewChat, onDeleteChat }: SidebarProps) {
    const formatDate = (timestamp: number) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <button className="new-chat-btn" onClick={onNewChat}>
                    <span className="btn-icon">+</span>
                    <span className="btn-text">New Chat</span>
                </button>
            </div>

            <div className="chat-list">
                {chats.length === 0 ? (
                    <div className="empty-state">
                        <span className="empty-icon">💬</span>
                        <span className="empty-text">No conversations yet</span>
                    </div>
                ) : (
                    chats.map(chat => (
                        <div
                            key={chat.id}
                            className={`chat-item ${activeChat?.id === chat.id ? 'active' : ''}`}
                            onClick={() => onSelectChat(chat)}
                        >
                            <div className="chat-icon">💬</div>
                            <div className="chat-info">
                                <div className="chat-title">{chat.title || 'New Chat'}</div>
                                <div className="chat-meta">
                                    {chat.messages.length} messages · {formatDate(chat.createdAt)}
                                </div>
                            </div>
                            <button
                                className="delete-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteChat(chat.id);
                                }}
                                title="Delete"
                            >
                                🗑️
                            </button>
                        </div>
                    ))
                )}
            </div>

            <div className="sidebar-footer">
                <div className="version">UCP Desktop v0.1.0</div>
            </div>
        </div>
    );
}

export default Sidebar;
