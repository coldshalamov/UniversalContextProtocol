/**
 * Title Bar Component - Custom frameless window title bar
 */

import React from 'react';

interface TitleBarProps {
    ucpConnected: boolean;
    onToggleTheme: () => void;
    onSettings: () => void;
}

function TitleBar({ ucpConnected, onToggleTheme, onSettings }: TitleBarProps) {
    return (
        <div className="title-bar">
            <div className="title-bar-drag">
                <div className="app-logo">
                    <span className="logo-icon">⚡</span>
                    <span className="logo-text">UCP Desktop</span>
                </div>
            </div>

            <div className="title-bar-status">
                <div className={`ucp-status ${ucpConnected ? 'connected' : ''}`}>
                    <span className="status-dot"></span>
                    <span className="status-text">
                        {ucpConnected ? 'UCP Connected' : 'UCP Offline'}
                    </span>
                </div>
            </div>

            <div className="title-bar-actions">
                <button className="action-btn" onClick={onToggleTheme} title="Toggle Theme">
                    🌓
                </button>
                <button className="action-btn" onClick={onSettings} title="Settings">
                    ⚙️
                </button>

                <div className="window-controls">
                    <button
                        className="window-btn minimize"
                        onClick={() => window.ucp.window.minimize()}
                        title="Minimize"
                    >
                        <svg viewBox="0 0 12 12">
                            <rect y="5" width="12" height="2" fill="currentColor" />
                        </svg>
                    </button>
                    <button
                        className="window-btn maximize"
                        onClick={() => window.ucp.window.maximize()}
                        title="Maximize"
                    >
                        <svg viewBox="0 0 12 12">
                            <rect x="1" y="1" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" />
                        </svg>
                    </button>
                    <button
                        className="window-btn close"
                        onClick={() => window.ucp.window.close()}
                        title="Close"
                    >
                        <svg viewBox="0 0 12 12">
                            <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" strokeWidth="2" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}

export default TitleBar;
