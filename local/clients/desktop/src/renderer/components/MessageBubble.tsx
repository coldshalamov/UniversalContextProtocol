/**
 * Message Bubble Component - Individual chat message
 */

import React from 'react';
import { marked } from 'marked';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    toolsUsed?: string[];
}

interface MessageBubbleProps {
    message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    // Parse markdown for assistant messages
    const contentHtml = isUser
        ? message.content
        : marked(message.content, { breaks: true });

    const formatTime = (timestamp: number) => {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className={`message ${message.role}`}>
            <div className="message-avatar">
                {isUser ? '👤' : '🤖'}
            </div>

            <div className="message-wrapper">
                <div className="message-content">
                    {isUser ? (
                        <p>{message.content}</p>
                    ) : (
                        <div
                            className="markdown-content"
                            dangerouslySetInnerHTML={{ __html: contentHtml as string }}
                        />
                    )}
                </div>

                {message.toolsUsed && message.toolsUsed.length > 0 && (
                    <div className="tools-used">
                        <span className="tools-label">🔧 Tools used:</span>
                        <div className="tools-list">
                            {message.toolsUsed.map((tool, i) => (
                                <span key={i} className="tool-badge">{tool}</span>
                            ))}
                        </div>
                    </div>
                )}

                <div className="message-meta">
                    <span className="message-time">{formatTime(message.timestamp)}</span>
                </div>
            </div>
        </div>
    );
}

export default MessageBubble;
