CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* === Reset & Base === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { height: 100%; -webkit-text-size-adjust: 100%; }
body {
    height: 100%;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #f9fafb;
    color: #111827;
    line-height: 1.5;
    overflow: hidden;
}

/* === Global scrollbar === */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

/* === Layout === */
.app-layout {
    display: flex;
    height: 100vh;
    width: 100%;
}

/* === Sidebar === */
.sidebar {
    width: 260px;
    min-width: 260px;
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    transition: transform 0.25s cubic-bezier(.4,0,.2,1), opacity 0.25s;
    z-index: 40;
}
.sidebar-header {
    padding: 18px 18px 14px;
    border-bottom: 1px solid #f3f4f6;
}
.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
}
.logo-mark {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px; color: #fff;
    flex-shrink: 0;
}
.logo-text {
    font-size: 16px;
    font-weight: 700;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.3px;
}
.logo-badge {
    font-size: 9px;
    font-weight: 600;
    color: #7c3aed;
    background: #f5f3ff;
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}
.logo-badge-beta {
    font-size: 8px;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.new-chat-btn {
    display: flex; align-items: center; gap: 8px;
    margin: 12px 12px 4px;
    padding: 9px 13px;
    background: transparent;
    border: 1px solid #e5e7eb;
    border-radius: 9px;
    color: #2563eb;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
}
.new-chat-btn:hover {
    background: #eff6ff;
    border-color: #93c5fd;
}
.new-chat-btn svg { width: 15px; height: 15px; stroke: currentColor; fill: none; }

.conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 6px 8px 0;
    scrollbar-width: thin;
    scrollbar-color: #e5e7eb transparent;
}
.conversation-list::-webkit-scrollbar { width: 4px; }
.conversation-list::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }

.conv-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 11px;
    border-radius: 8px;
    cursor: pointer;
    color: #6b7280;
    font-size: 13px;
    text-decoration: none;
    transition: all 0.15s ease;
    overflow: hidden;
    position: relative;
    border-left: 2px solid transparent;
}
.conv-item:hover {
    background: #f3f4f6;
    color: #111827;
    border-left-color: #d1d5db;
}
.conv-item.active {
    background: #eff6ff;
    color: #2563eb;
    font-weight: 500;
    border-left-color: #2563eb;
}
.conv-item-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
}
.conv-delete {
    opacity: 0;
    flex-shrink: 0;
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 2px;
    border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    transition: opacity 0.15s, color 0.15s;
}
.conv-item:hover .conv-delete { opacity: 1; }
.conv-delete:hover { color: #ef4444; }
.conv-delete svg { width: 14px; height: 14px; }

.sidebar-footer {
    padding: 12px 18px;
    border-top: 1px solid #f3f4f6;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.sidebar-footer-lang {
    width: 100%;
}
.sidebar-footer-text {
    font-size: 11px;
    color: #9ca3af;
    letter-spacing: 0.2px;
    text-align: center;
}
.language-switcher {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: #f9fafb;
    font-size: 12px;
    color: #374151;
    cursor: pointer;
    outline: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 8px center;
    padding-right: 28px;
}
.language-switcher:hover {
    border-color: #d1d5db;
    background: #f3f4f6;
}

/* === Role Switcher (buyer/seller toggle) === */
.role-switcher-wrap {
    padding: 8px 12px 4px;
}
.role-switcher {
    display: flex;
    background: #f3f4f6;
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
}
.role-tab {
    flex: 1;
    padding: 6px 0;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    background: transparent;
    color: #6b7280;
}
.role-tab:hover {
    color: #374151;
}
.role-tab.active {
    background: #ffffff;
    color: #2563eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* === Chat main area === */
.chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    position: relative;
    background: #f9fafb;
}

/* === Message area === */
.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 0 0 24px;
    scrollbar-width: thin;
    scrollbar-color: #d1d5db transparent;
}

.message {
    padding: 20px 0;
}
.message + .message {
    border-top: none;
}
.ai-message {
    background: #ffffff;
    border-bottom: 1px solid #f0f0f0;
}
.user-message {
    background: #f9fafb;
}
.message:last-child { border-bottom: none; }
.message-inner {
    max-width: 768px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    gap: 14px;
}

.avatar {
    width: 28px; height: 28px;
    border-radius: 50%;
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px;
    font-weight: 600;
    margin-top: 1px;
}
.user-avatar {
    background: #e5e7eb;
    color: #4b5563;
}
.ai-avatar {
    background: linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%);
    color: #fff;
}

.message-content { flex: 1; min-width: 0; }
.message-sender {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 4px;
    letter-spacing: -0.1px;
}
.message-text {
    font-size: 15px;
    line-height: 1.7;
    color: #111827;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
.message-text p, .message-text li, .message-text span { color: inherit; }
.message-text p { margin-bottom: 10px; }
.message-text p:last-child { margin-bottom: 0; }
.message-text strong { color: #111827; font-weight: 600; }
.message-text em { color: #7c3aed; font-style: italic; }
.message-text ul, .message-text ol { margin: 8px 0 8px 20px; }
.message-text li { margin-bottom: 4px; }
.message-text code {
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    color: #7c3aed;
}
.message-text pre {
    background: #f8f9fa;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 14px;
    overflow-x: auto;
    margin: 10px 0;
}
.message-text pre code { background: none; padding: 0; color: #374151; }
.message-text a { color: #2563eb; text-decoration: none; }
.message-text a:hover { text-decoration: underline; }

.user-message .message-text { color: #111827; }

/* === Tender results list === */
.tender-results {
    margin-top: 16px;
}
.tender-results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}
.tender-results-title {
    font-size: 13px;
    font-weight: 600;
    color: #6b7280;
}
.tender-results-count {
    font-size: 12px;
    color: #9ca3af;
}
.tender-list {
    display: flex;
    flex-direction: column;
    gap: 0;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
    background: #ffffff;
}
.tender-list-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    cursor: pointer;
    transition: all 0.15s ease;
    border-bottom: 1px solid #f3f4f6;
    background: #ffffff;
    border-left: 3px solid transparent;
}
.tender-list-item:last-child { border-bottom: none; }
.tender-list-item:hover {
    background: #f9fafb;
    border-left-color: #2563eb;
}
.tender-list-flag {
    font-size: 18px;
    flex-shrink: 0;
    width: 28px;
    text-align: center;
}
.tender-list-info {
    flex: 1;
    min-width: 0;
}
.tender-list-name {
    font-size: 13.5px;
    font-weight: 600;
    color: #111827;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
}
.tender-list-org {
    font-size: 12px;
    color: #6b7280;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 1px;
}
.tender-list-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 3px;
    flex-shrink: 0;
}
.tender-list-value {
    font-size: 12.5px;
    font-weight: 600;
    color: #111827;
    white-space: nowrap;
}
.tender-list-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 20px;
    white-space: nowrap;
    letter-spacing: 0.2px;
}
.tlb-urgent { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.tlb-normal { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.tlb-expired { background: #f3f4f6; color: #6b7280; border: 1px solid #d1d5db; }
.tlb-quality-high { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.tlb-quality-mid { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.tlb-quality-low { background: #f3f4f6; color: #9ca3af; border: 1px solid #d1d5db; }

.tender-list-tags {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
}
.tender-list-tag {
    font-size: 9px;
    padding: 2px 6px;
    border-radius: 20px;
    font-weight: 600;
}
.tlt-green { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.tlt-eu { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }

.tender-list-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    color: #9ca3af;
    flex-shrink: 0;
    transition: all 0.15s;
    text-decoration: none;
}
.tender-list-link:hover {
    color: #2563eb;
    background: #eff6ff;
}
.detail-tendly-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px 16px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.2s;
    margin-bottom: 8px;
    width: 100%;
}
.detail-tendly-link:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}
.detail-tendly-link svg {
    width: 14px;
    height: 14px;
}
.tender-show-more-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: 100%;
    padding: 10px 14px;
    background: #f9fafb;
    border: none;
    border-top: 1px solid #f3f4f6;
    color: #2563eb;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.12s;
}
.tender-show-more-btn:hover {
    background: #eff6ff;
}
.tender-show-more-btn svg {
    width: 14px;
    height: 14px;
    transition: transform 0.2s;
}
.tender-show-more-btn.expanded svg {
    transform: rotate(180deg);
}

/* === Message action buttons (copy, link) === */
.message-actions {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-top: 10px;
    opacity: 0;
    transition: opacity 0.15s ease;
}
.message:hover .message-actions,
.message-actions.visible {
    opacity: 1;
}
.msg-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 5px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.15s ease;
    font-family: inherit;
}
.msg-action-btn:hover {
    background: #f3f4f6;
    color: #374151;
}
.msg-action-btn svg {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
}
.msg-action-btn.copied {
    color: #16a34a;
}
.msg-action-btn.copied:hover {
    background: #f0fdf4;
    color: #16a34a;
}
.action-btn-label {
    pointer-events: none;
}

/* === Suggestion chips (Try also) === */
.suggestion-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
}
.suggestion-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    font-size: 13px;
    color: #374151;
    cursor: pointer;
    transition: all 0.18s ease;
    font-weight: 500;
}
.suggestion-chip:hover {
    background: #eff6ff;
    border-color: #93c5fd;
    color: #2563eb;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(37,99,235,0.1);
}
.suggestion-chip svg {
    width: 12px;
    height: 12px;
    color: #9ca3af;
}

/* === Welcome screen === */
.welcome-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 24px 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(37,99,235,0.04) 0%, transparent 60%);
}
.welcome-content {
    max-width: 640px;
    width: 100%;
    text-align: center;
}
.welcome-icon {
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    box-shadow: 0 4px 16px rgba(37,99,235,0.2);
}
.welcome-icon svg {
    width: 28px;
    height: 28px;
    color: #fff;
    stroke: #fff;
    fill: none;
}
.welcome-title {
    font-size: 30px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 10px;
    letter-spacing: -0.5px;
    line-height: 1.2;
}
.welcome-title-gradient {
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.welcome-subtitle {
    font-size: 15px;
    color: #6b7280;
    margin-bottom: 36px;
    line-height: 1.6;
    max-width: 480px;
    margin-left: auto;
    margin-right: auto;
}
.suggestions-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    text-align: left;
}
.suggestion-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    display: flex;
    align-items: flex-start;
    gap: 12px;
    position: relative;
    overflow: hidden;
}
.suggestion-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    opacity: 0;
    transition: opacity 0.2s ease;
}
.suggestion-card:hover {
    border-color: #93c5fd;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(37,99,235,0.1), 0 2px 6px rgba(0,0,0,0.04);
}
.suggestion-card:hover::before {
    opacity: 1;
}
.suggestion-card:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(37,99,235,0.08);
}
.suggestion-icon {
    width: 36px; height: 36px;
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.suggestion-icon svg {
    width: 18px; height: 18px;
}
.suggestion-icon-blue { background: #eff6ff; color: #2563eb; }
.suggestion-icon-purple { background: #f5f3ff; color: #7c3aed; }
.suggestion-icon-green { background: #f0fdf4; color: #16a34a; }
.suggestion-icon-amber { background: #fffbeb; color: #d97706; }
.suggestion-text-wrap { flex: 1; min-width: 0; }
.suggestion-title {
    font-size: 13.5px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 2px;
}
.suggestion-desc {
    font-size: 12px;
    color: #9ca3af;
    line-height: 1.4;
}

/* === Chat input area === */
.chat-input-area {
    padding: 0 24px 24px;
    max-width: 768px;
    margin: 0 auto;
    width: 100%;
}
.chat-form { width: 100%; }
.input-wrapper {
    display: flex;
    align-items: flex-end;
    background: #ffffff;
    border: 1.5px solid #e5e7eb;
    border-radius: 16px;
    padding: 4px 6px 4px 8px;
    gap: 4px;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.input-wrapper:focus-within {
    border-color: #93c5fd;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.chat-textarea {
    flex: 1 1 auto;
    min-width: 0;
    width: 100%;
    background: transparent;
    border: none;
    color: #111827;
    font-size: 15px;
    font-family: inherit;
    padding: 12px 0;
    resize: none;
    outline: none;
    max-height: 120px;
    min-height: 22px;
    line-height: 1.5;
}
.chat-textarea::placeholder { color: #9ca3af; }
.chat-textarea:focus { box-shadow: none !important; outline: none !important; }

.send-btn {
    width: 38px !important; height: 38px !important;
    min-width: 38px; max-width: 38px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    border: none;
    border-radius: 12px;
    color: #fff;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex: 0 0 38px;
    transition: opacity 0.15s, transform 0.1s;
    margin-bottom: 3px;
    padding: 0;
}
.send-btn:hover { opacity: 0.9; transform: scale(1.03); }
.send-btn:disabled { opacity: 0.35; cursor: not-allowed; transform: none; }
.send-btn svg { width: 18px; height: 18px; }

.attach-btn {
    background: transparent;
    border: none;
    color: #4b5563;
    width: 38px; height: 38px;
    min-width: 38px;
    border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    cursor: pointer;
    flex: 0 0 38px;
    margin-bottom: 3px;
    margin-right: 4px;
    transition: background 0.15s, color 0.15s;
}
.attach-btn:hover { background: #f3f4f6; color: #2563eb; }
.attach-btn svg { width: 22px !important; height: 22px !important; flex-shrink: 0; display: block; }

.chat-attachment-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    margin: 0 6px 6px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 999px;
    font-size: 12px;
    color: #1e40af;
    width: fit-content;
}
.chat-attachment-chip button {
    background: transparent;
    border: none;
    color: #1e40af;
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
    padding: 0 4px;
}
.chat-attachment-chip button:hover { color: #dc2626; }

.input-hint {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-top: 10px;
}
.input-disclaimer {
    font-size: 11px;
    color: #9ca3af;
    text-align: center;
}
.input-shortcut {
    font-size: 11px;
    color: #b0b5bf;
    display: flex;
    align-items: center;
    gap: 3px;
    flex-shrink: 0;
}
.input-shortcut kbd {
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 3px;
    padding: 0 4px;
    font-size: 10px;
    font-family: inherit;
    color: #9ca3af;
    line-height: 1.6;
}

/* === Typing indicator (ChatGPT-style) === */
.typing-indicator {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 8px 4px;
    min-height: 20px;
}
.typing-dot {
    width: 7px;
    height: 7px;
    background: #9ca3af;
    border-radius: 50%;
    animation: typingPulse 1.4s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingPulse {
    0%, 60%, 100% { opacity: 0.25; transform: translateY(0); }
    30%           { opacity: 1;    transform: translateY(-3px); }
}

/* Streaming cursor */
.streaming-cursor::after {
    content: '|';
    animation: blink 0.8s step-end infinite;
    color: #7c3aed;
    font-weight: 300;
}
@keyframes blink { 50% { opacity: 0; } }

/* === Tender detail panel === */
.detail-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.2);
    z-index: 49;
    backdrop-filter: blur(2px);
}
.detail-overlay.open { display: block; }
.detail-panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 460px;
    max-width: 100vw;
    background: #ffffff;
    border-left: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    z-index: 50;
    box-shadow: -4px 0 24px rgba(0,0,0,0.08);
    animation: panelSlideIn 0.25s cubic-bezier(.4,0,.2,1);
}
@keyframes panelSlideIn {
    from { transform: translateX(100%); opacity: 0.8; }
    to { transform: translateX(0); opacity: 1; }
}
.detail-panel.closing {
    animation: panelSlideOut 0.2s cubic-bezier(.4,0,.2,1) forwards;
}
@keyframes panelSlideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
}
.detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid #f3f4f6;
    background: #ffffff;
}
.detail-header-title {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
}
.detail-close-btn {
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 4px;
    border-radius: 6px;
    display: flex;
    transition: background 0.12s, color 0.12s;
}
.detail-close-btn:hover { background: #f3f4f6; color: #374151; }
.detail-close-btn svg { width: 18px; height: 18px; }
.detail-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    scrollbar-width: thin;
    scrollbar-color: #e5e7eb transparent;
}
.detail-section {
    margin-bottom: 22px;
    padding-bottom: 18px;
    border-bottom: 1px solid #f3f4f6;
}
.detail-section:last-child {
    border-bottom: none;
    padding-bottom: 0;
}
.detail-section-title {
    font-size: 11px;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 10px;
}
.detail-field { margin-bottom: 12px; }
.detail-field-label {
    font-size: 11px;
    color: #9ca3af;
    margin-bottom: 2px;
    font-weight: 500;
}
.detail-field-value {
    font-size: 14px;
    color: #374151;
    line-height: 1.5;
}
.detail-badge {
    display: inline-block;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 600;
}
.detail-badge-green { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.detail-badge-eu { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.detail-badge-active { background: #f5f3ff; color: #7c3aed; border: 1px solid #ddd6fe; }

/* Document items - refined styling with file type icons */
.detail-doc-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 13px;
    color: #4b5563;
    transition: all 0.15s ease;
    cursor: default;
}
.detail-doc-item:hover {
    background: #f9fafb;
    border-color: #d1d5db;
}
.detail-doc-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.detail-doc-icon svg {
    width: 16px;
    height: 16px;
}
.detail-doc-icon-pdf { background: #fef2f2; color: #dc2626; }
.detail-doc-icon-doc { background: #eff6ff; color: #2563eb; }
.detail-doc-icon-xls { background: #f0fdf4; color: #16a34a; }
.detail-doc-icon-zip { background: #fffbeb; color: #d97706; }
.detail-doc-icon-img { background: #faf5ff; color: #7c3aed; }
.detail-doc-icon-default { background: #f3f4f6; color: #6b7280; }
.detail-doc-info {
    flex: 1;
    min-width: 0;
}
.detail-doc-name {
    font-size: 13px;
    font-weight: 500;
    color: #374151;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
}
.detail-doc-meta {
    font-size: 11px;
    color: #9ca3af;
    margin-top: 1px;
}
.detail-doc-action {
    flex-shrink: 0;
    color: #9ca3af;
    display: flex;
    align-items: center;
}
.detail-doc-action svg {
    width: 14px;
    height: 14px;
}

/* Quality score ring */
.quality-score-display {
    display: flex;
    align-items: center;
    gap: 14px;
}
.quality-score-ring {
    position: relative;
    width: 52px;
    height: 52px;
    flex-shrink: 0;
}
.quality-score-ring svg {
    transform: rotate(-90deg);
    width: 52px;
    height: 52px;
}
.quality-score-ring .ring-bg {
    fill: none;
    stroke: #f3f4f6;
    stroke-width: 4;
}
.quality-score-ring .ring-fg {
    fill: none;
    stroke-width: 4;
    stroke-linecap: round;
}
.quality-score-number {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}
.quality-score-label {
    font-size: 12px;
    color: #6b7280;
    line-height: 1.4;
}

/* Evaluation criteria progress bars */
.eval-criteria-item {
    margin-bottom: 10px;
}
.eval-criteria-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}
.eval-criteria-name {
    font-size: 13px;
    color: #4b5563;
}
.eval-criteria-weight {
    font-size: 13px;
    font-weight: 600;
    color: #111827;
}
.eval-criteria-bar {
    height: 4px;
    background: #f3f4f6;
    border-radius: 2px;
    overflow: hidden;
}
.eval-criteria-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
}

/* Winner/result card */
.detail-winner-card {
    background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 8px;
}
.detail-winner-label {
    font-size: 10px;
    font-weight: 700;
    color: #16a34a;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
}
.detail-winner-label svg {
    width: 12px;
    height: 12px;
}
.detail-winner-name {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 6px;
}
.detail-winner-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 12px;
    color: #4b5563;
}

.detail-source-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #2563eb;
    text-decoration: none;
    padding: 10px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    transition: all 0.15s;
    width: 100%;
    justify-content: center;
}
.detail-source-link svg {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
}
.detail-source-link:hover {
    background: #eff6ff;
    border-color: #93c5fd;
}

/* === AI Requirements sections === */
.req-section {
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 8px;
}
.req-section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}
.req-section-icon {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.req-section-icon svg {
    width: 14px;
    height: 14px;
}
.req-section-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    flex: 1;
}
.req-section-count {
    font-size: 11px;
    font-weight: 700;
    border-radius: 10px;
    padding: 1px 7px;
}
.req-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 6px 0;
    font-size: 13px;
    line-height: 1.5;
    color: #374151;
}
.req-item + .req-item {
    border-top: 1px solid rgba(0,0,0,0.04);
}
.req-item-bullet {
    flex-shrink: 0;
    margin-top: 2px;
    font-weight: 700;
    font-size: 11px;
}
.req-show-more-btn {
    background: rgba(0,0,0,0.03);
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 6px;
    padding: 5px 0;
    font-size: 12px;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    width: 100%;
    margin-top: 6px;
    transition: all 0.15s;
}
.req-show-more-btn:hover {
    background: rgba(0,0,0,0.05);
    color: #374151;
}

/* === Mobile hamburger === */
.mobile-header {
    display: none;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
}
.hamburger-btn {
    background: none;
    border: none;
    color: #374151;
    cursor: pointer;
    padding: 6px;
    display: flex;
    border-radius: 6px;
    -webkit-tap-highlight-color: transparent;
}
.hamburger-btn:active { background: #f3f4f6; }
.hamburger-btn svg { width: 22px; height: 22px; }
.mobile-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.3);
    z-index: 35;
    backdrop-filter: blur(2px);
}

/* === Responsive === */
@media (max-width: 900px) {
    .suggestions-grid { grid-template-columns: 1fr; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        left: 0; top: 0; bottom: 0;
        transform: translateX(-100%);
        box-shadow: 4px 0 20px rgba(0,0,0,0.1);
    }
    .sidebar.open {
        transform: translateX(0);
    }
    .mobile-overlay.open { display: block; }
    .mobile-header { display: flex; }
    .suggestions-grid { grid-template-columns: 1fr; }
    .detail-panel { width: 100%; }
    .message-inner { padding: 0 16px; }
    .chat-input-area { padding: 0 12px 12px; }
    .welcome-wrapper { padding: 24px 16px 0; }
    .welcome-title { font-size: 24px; }
    .welcome-subtitle { font-size: 14px; margin-bottom: 24px; }
    .welcome-icon { width: 48px; height: 48px; border-radius: 14px; }
    .welcome-icon svg { width: 24px; height: 24px; }
    .tender-list-item { padding: 10px 12px; gap: 10px; }
    .conv-item { padding: 10px 12px; min-height: 40px; }
    .input-shortcut { display: none; }
    .message-actions { opacity: 1; }
    .action-btn-label { display: none; }
    /* Canvas becomes full-screen overlay on mobile */
    .canvas-panel.open {
        position: fixed;
        top: 0; right: 0; bottom: 0; left: 0;
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        z-index: 50;
        border-left: none;
    }
}
@media (max-width: 480px) {
    .welcome-title { font-size: 22px; }
    .welcome-subtitle { font-size: 13px; }
    .suggestion-card { padding: 12px; }
    .tender-list-meta { display: none; }
    .tender-list-item { border-left-width: 2px; }
}

/* === User Section in Sidebar === */
.sidebar-user-section {
    padding: 10px 14px;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 4px;
}
.user-info-row {
    display: flex;
    align-items: center;
    gap: 10px;
}
.user-avatar-small {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.user-info-text {
    min-width: 0;
    flex: 1;
}
.user-name-text {
    font-size: 13px;
    font-weight: 600;
    color: #111827;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.user-email-text {
    font-size: 11px;
    color: #6b7280;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.sidebar-login-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    transition: opacity 0.15s;
    width: 100%;
    justify-content: center;
}
.sidebar-login-btn:hover { opacity: 0.9; }

/* === Save to Pipeline Button (Detail Panel) === */
.detail-header-actions {
    display: flex;
    align-items: center;
    gap: 6px;
}
.detail-save-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
    background: #fff;
    color: #374151;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
}
.detail-save-btn:hover {
    border-color: #7c3aed;
    color: #7c3aed;
    background: #f5f3ff;
}
.detail-save-btn.saved {
    border-color: #7c3aed;
    color: #7c3aed;
    background: #f5f3ff;
}
.detail-save-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* === Toast Notification === */
.toast-notification {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    z-index: 10000;
    opacity: 0;
    transition: opacity 0.3s, transform 0.3s;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.toast-notification.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}
.toast-success {
    background: #059669;
    color: #fff;
}
.toast-error {
    background: #dc2626;
    color: #fff;
}

/* === Login Modal === */
.login-modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 9000;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(2px);
}
.login-modal {
    background: #fff;
    border-radius: 16px;
    padding: 32px;
    max-width: 400px;
    width: 90%;
    text-align: center;
    position: relative;
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}
.login-modal-icon {
    margin-bottom: 16px;
}
.login-modal-title {
    font-size: 18px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 8px;
}
.login-modal-text {
    font-size: 14px;
    color: #6b7280;
    line-height: 1.5;
    margin-bottom: 24px;
}
.login-modal-actions {
    display: flex;
    gap: 10px;
    justify-content: center;
}
.login-modal-btn {
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    transition: opacity 0.15s;
    display: inline-block;
}
.login-modal-btn-primary {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff;
}
.login-modal-btn-primary:hover { opacity: 0.9; }
.login-modal-btn-secondary {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #e5e7eb;
}
.login-modal-btn-secondary:hover { background: #e5e7eb; }
.login-modal-close {
    position: absolute;
    top: 12px;
    right: 12px;
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    display: flex;
}
.login-modal-close:hover { color: #374151; background: #f3f4f6; }

/* === Logout Button === */
.sidebar-logout-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    color: #9ca3af;
    text-decoration: none;
    flex-shrink: 0;
    transition: all 0.15s;
}
.sidebar-logout-btn:hover {
    color: #dc2626;
    background: #fef2f2;
}

/* === Message Counter === */
.msg-counter {
    font-size: 11px;
    color: #9ca3af;
    font-weight: 500;
    transition: color 0.2s;
}
.msg-counter.low {
    color: #d97706;
}
.msg-counter.exhausted {
    color: #dc2626;
    font-weight: 600;
}
.msg-counter.unlimited {
    display: none;
}

/* === Upgrade Modal (ChatGPT-style) === */
.upgrade-modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.45);
    z-index: 9000;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.upgrade-modal {
    background: #fff;
    border-radius: 20px;
    padding: 36px 32px 28px;
    max-width: 440px;
    width: 92%;
    text-align: center;
    position: relative;
    box-shadow: 0 24px 48px rgba(0,0,0,0.18);
    animation: modalSlideUp 0.3s cubic-bezier(.4,0,.2,1);
}
@keyframes modalSlideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}
.upgrade-modal-icon {
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #f5f3ff, #eff6ff);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 18px;
}
.upgrade-modal-title {
    font-size: 20px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 8px;
}
.upgrade-modal-text {
    font-size: 14px;
    color: #6b7280;
    line-height: 1.6;
    margin-bottom: 24px;
}
.upgrade-modal-actions {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.upgrade-modal-btn-primary {
    display: block;
    width: 100%;
    padding: 12px 24px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    text-decoration: none;
    text-align: center;
    transition: opacity 0.15s;
    cursor: pointer;
}
.upgrade-modal-btn-primary:hover { opacity: 0.9; }
.upgrade-modal-btn-secondary {
    display: block;
    width: 100%;
    padding: 10px 24px;
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    text-align: center;
    cursor: pointer;
    transition: background 0.15s;
}
.upgrade-modal-btn-secondary:hover { background: #e5e7eb; }
.upgrade-modal-close {
    position: absolute;
    top: 14px;
    right: 14px;
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 4px;
    border-radius: 6px;
    display: flex;
}
.upgrade-modal-close:hover { color: #374151; background: #f3f4f6; }
.upgrade-modal-feature {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #374151;
    text-align: left;
    padding: 4px 0;
}
.upgrade-modal-feature svg {
    width: 16px;
    height: 16px;
    color: #7c3aed;
    flex-shrink: 0;
}
.upgrade-modal-features {
    margin-bottom: 20px;
    padding: 0 8px;
}

/* === Canvas Panel (Right Pane) === */
.canvas-panel {
    width: 0;
    min-width: 0;
    max-width: 0;
    background: #ffffff;
    border-left: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    opacity: 0;
    transition: width 0.3s cubic-bezier(.4,0,.2,1),
                min-width 0.3s cubic-bezier(.4,0,.2,1),
                max-width 0.3s cubic-bezier(.4,0,.2,1),
                opacity 0.25s ease;
}
.canvas-panel.open {
    width: 440px;
    min-width: 440px;
    max-width: 440px;
    opacity: 1;
}
.canvas-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid #f3f4f6;
    background: #ffffff;
    flex-shrink: 0;
}
.canvas-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1;
}
.canvas-header-title {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.canvas-close-btn {
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 4px;
    border-radius: 6px;
    display: flex;
    flex-shrink: 0;
    transition: background 0.12s, color 0.12s;
}
.canvas-close-btn:hover { background: #f3f4f6; color: #374151; }
.canvas-close-btn svg { width: 18px; height: 18px; }
.canvas-body {
    flex: 1;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #e5e7eb transparent;
}
/* When canvas is open and showing content from the old detail panel, reuse its styles */
.canvas-body .detail-body {
    padding: 20px;
}
.canvas-body .detail-panel {
    position: static;
    width: 100%;
    max-width: 100%;
    box-shadow: none;
    border-left: none;
    animation: none;
    height: auto;
}
.canvas-body .detail-header {
    display: none; /* Canvas has its own header */
}

/* === Main Content Area (non-chat pages) === */
.main-content {
    flex: 1;
    overflow-y: auto;
    background: #f9fafb;
}
.page-content {
    max-width: 900px;
    margin: 0 auto;
    padding: 28px 32px;
}
.page-header {
    margin-bottom: 24px;
}

/* === Stats Grid === */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
.stat-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 18px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.stat-icon-wrap {
    width: 44px; height: 44px;
    display: flex; align-items: center; justify-content: center;
    background: #f9fafb;
    border-radius: 10px;
    flex-shrink: 0;
}
.stat-value {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
}
.stat-label {
    font-size: 12px;
    color: #6b7280;
    margin-top: 2px;
}

/* === Dashboard Sections === */
.dashboard-section {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}

/* === Plans List === */
.plans-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 12px;
}
.procurement-card {
    display: block;
    text-decoration: none;
    color: inherit;
}
.procurement-card-inner {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.procurement-card:hover .procurement-card-inner {
    border-color: #93c5fd;
    box-shadow: 0 2px 8px rgba(37,99,235,0.08);
}

/* === Quick Actions === */
.quick-actions-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}
.quick-action-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    color: #374151;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.15s;
}
.quick-action-btn:hover {
    border-color: #93c5fd;
    background: #eff6ff;
    color: #2563eb;
}

/* === Info Grid (procurement detail) === */
.info-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}
.info-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
}

/* === Workflow Steps === */
.workflow-steps {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* === Buttons === */
.btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 18px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.9; }
.btn-secondary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 18px;
    background: #ffffff;
    color: #374151;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.15s;
}
.btn-secondary:hover { background: #f9fafb; border-color: #d1d5db; }

/* === Forms === */
.procurement-form {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 24px;
}
.form-group {
    margin-bottom: 18px;
}
.form-label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
}
.form-input, .form-select, .form-textarea {
    width: 100%;
    padding: 9px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    color: #111827;
    background: #ffffff;
    transition: border-color 0.15s;
    font-family: inherit;
}
.form-input:focus, .form-select:focus, .form-textarea:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.form-input-error,
.form-input-error:focus,
.form-select.form-input-error,
.form-textarea.form-input-error {
    border-color: #dc2626 !important;
    box-shadow: 0 0 0 3px rgba(220,38,38,0.12) !important;
}
.form-help {
    font-size: 11px;
    color: #6b7280;
    margin: 4px 0 0;
}
.form-error {
    font-size: 12px;
    color: #dc2626;
    margin: 4px 0 0;
}
.form-required-hint {
    font-size: 12px;
    color: #6b7280;
    margin: 0 0 16px;
}
.form-required-asterisk {
    color: #dc2626;
    font-weight: 700;
    margin-left: 2px;
}
.form-banner {
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 13px;
    border: 1px solid transparent;
}
.form-banner-error {
    background: #fef2f2;
    border-color: #fecaca;
    color: #dc2626;
}
.form-banner-success {
    background: #f0fdf4;
    border-color: #bbf7d0;
    color: #15803d;
}
.form-textarea {
    resize: vertical;
    min-height: 80px;
}
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 24px;
    padding-top: 18px;
    border-top: 1px solid #f3f4f6;
}

/* === Sidebar nav items === */
.sidebar-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 14px;
    color: #4b5563;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    border-radius: 8px;
    transition: all 0.15s;
    margin-bottom: 2px;
}
.sidebar-nav-item:hover {
    background: #f3f4f6;
    color: #111827;
}
.sidebar-nav-item.active {
    background: #eff6ff;
    color: #2563eb;
    font-weight: 600;
}
.sidebar-nav-item svg {
    flex-shrink: 0;
}
.sidebar-chat-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* === Dynamic form rows (evaluation criteria, requirements) === */
.form-section {
    margin-top: 20px;
    padding-top: 18px;
    border-top: 1px solid #f3f4f6;
}
.dynamic-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
}
.dynamic-row-fields {
    display: flex;
    gap: 8px;
    flex: 1;
    min-width: 0;
}
.dynamic-row-header {
    display: flex;
}
.btn-add-row {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 5px 12px;
    background: #f0f9ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
}
.btn-add-row:hover {
    background: #dbeafe;
    border-color: #93c5fd;
}
.btn-remove-row {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
    background: #fff;
    color: #9ca3af;
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.15s;
}
.btn-remove-row:hover {
    background: #fef2f2;
    border-color: #fca5a5;
    color: #ef4444;
}

/* === Document card === */
.doc-card {
    transition: border-color 0.15s;
}
.doc-card:hover {
    border-color: #d1d5db;
}

/* === Responsive adjustments for buyer pages === */
@media (max-width: 768px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .quick-actions-grid { grid-template-columns: 1fr; }
    .info-grid { grid-template-columns: repeat(2, 1fr); }
    .form-row { grid-template-columns: 1fr; }
    .page-content { padding: 20px 16px; }
    .dynamic-row-fields { flex-wrap: wrap; }
    .dynamic-row-fields input,
    .dynamic-row-fields select {
        flex: 1 1 100% !important;
        min-width: 0;
    }
    .dynamic-row-header { display: none; }
    .btn-add-row { font-size: 11px; padding: 4px 10px; }
}
@media (max-width: 480px) {
    .stats-grid { grid-template-columns: 1fr; }
    .info-grid { grid-template-columns: 1fr; }
}

/* === Clickable elements: cursor === */
.info-card {
    cursor: pointer;
}

/* === Accessibility: focus states === */
.sidebar-nav-item:focus-visible,
.btn-primary:focus-visible,
.btn-secondary:focus-visible,
a:focus-visible {
    outline: 2px solid #0369A1;
    outline-offset: 2px;
    border-radius: 4px;
}

.form-input:focus-visible,
.form-select:focus-visible,
.form-textarea:focus-visible {
    outline: none;
    border-color: #0369A1;
    box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.15);
}

/* === HTMX loading indicators === */
.htmx-indicator {
    display: none;
}
.htmx-request .htmx-indicator,
.htmx-request.htmx-indicator {
    display: block;
}
.loading-spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid #e5e7eb;
    border-top-color: #0369A1;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

/* === AI Document Review Panel === */
.review-panel {
    padding: 0;
}
.review-scores {
    padding: 16px 0;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 16px;
}
.review-section {
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid #f3f4f6;
}
.review-section:last-child {
    border-bottom: none;
    padding-bottom: 0;
}
.review-section-title {
    font-size: 11px;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 10px;
}

/* Responsive review scores */
@media (max-width: 480px) {
    .review-scores > div {
        gap: 12px !important;
    }
}

/* === Reduced motion === */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
"""
