JS_CODE = r"""
(function(){

// ---- State ----
var activeConversationId = null;
var isStreaming = false;

// ---- i18n helper ----
function _t(key, fallback) {
    return (window.__LANG__ && window.__LANG__[key]) || fallback;
}

// ---- DOM helpers ----
function qs(sel, ctx) { return (ctx || document).querySelector(sel); }
function qsa(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

// ---- Sidebar toggle (mobile) ----
window.toggleSidebar = function() {
    var sidebar = qs('.sidebar');
    var overlay = qs('.mobile-overlay');
    if (sidebar) sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('open');
};

window.closeSidebar = function() {
    var sidebar = qs('.sidebar');
    var overlay = qs('.mobile-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
};

// ---- Auto-grow textarea ----
function autoGrow(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}
document.addEventListener('input', function(e) {
    if (e.target.id === 'chat-input') autoGrow(e.target);
});

// ---- Safe markdown renderer using DOM methods ----
function renderMarkdownToFragment(text) {
    if (!text) return document.createDocumentFragment();

    var codeBlocks = [];
    var processed = text.replace(/```(\w*)\n([\s\S]*?)```/g, function(m, lang, code) {
        var idx = codeBlocks.length;
        codeBlocks.push(code.trim());
        return '\n%%CODEBLOCK_' + idx + '%%\n';
    });

    var fragment = document.createDocumentFragment();
    var paragraphs = processed.split('\n\n');

    paragraphs.forEach(function(para) {
        para = para.trim();
        if (!para) return;

        var cbMatch = para.match(/^%%CODEBLOCK_(\d+)%%$/);
        if (cbMatch) {
            var pre = document.createElement('pre');
            var code = document.createElement('code');
            code.textContent = codeBlocks[parseInt(cbMatch[1])];
            pre.appendChild(code);
            fragment.appendChild(pre);
            return;
        }

        var lines = para.split('\n');
        var isUList = lines.every(function(l) { return /^[\-\*] /.test(l.trim()) || l.trim() === ''; });
        var isOList = lines.every(function(l) { return /^\d+\. /.test(l.trim()) || l.trim() === ''; });

        if (isUList) {
            var ul = document.createElement('ul');
            lines.forEach(function(l) {
                l = l.trim();
                if (/^[\-\*] /.test(l)) {
                    var li = document.createElement('li');
                    appendInlineFormatted(li, l.replace(/^[\-\*] /, ''));
                    ul.appendChild(li);
                }
            });
            fragment.appendChild(ul);
        } else if (isOList) {
            var ol = document.createElement('ol');
            lines.forEach(function(l) {
                l = l.trim();
                if (/^\d+\. /.test(l)) {
                    var li = document.createElement('li');
                    appendInlineFormatted(li, l.replace(/^\d+\. /, ''));
                    ol.appendChild(li);
                }
            });
            fragment.appendChild(ol);
        } else {
            var p = document.createElement('p');
            var sublines = para.split('\n');
            sublines.forEach(function(sl, i) {
                appendInlineFormatted(p, sl);
                if (i < sublines.length - 1) p.appendChild(document.createElement('br'));
            });
            fragment.appendChild(p);
        }
    });

    return fragment;
}

function appendInlineFormatted(parent, text) {
    var regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\))/g;
    var lastIndex = 0;
    var match;
    while ((match = regex.exec(text)) !== null) {
        if (match.index > lastIndex) {
            parent.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
        }
        if (match[2]) {
            var strong = document.createElement('strong');
            strong.textContent = match[2];
            parent.appendChild(strong);
        } else if (match[3]) {
            var em = document.createElement('em');
            em.textContent = match[3];
            parent.appendChild(em);
        } else if (match[4]) {
            var code = document.createElement('code');
            code.textContent = match[4];
            parent.appendChild(code);
        } else if (match[5] && match[6]) {
            var a = document.createElement('a');
            a.textContent = match[5];
            a.href = match[6];
            a.target = '_blank';
            a.rel = 'noopener';
            parent.appendChild(a);
        }
        lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) {
        parent.appendChild(document.createTextNode(text.slice(lastIndex)));
    }
}

// ---- Scroll to bottom ----
function scrollToBottom(smooth) {
    var container = qs('#messages');
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
}

// ---- Build compact tender list item using DOM API (safe) ----
var FLAGS = {EE:'\u{1f1ea}\u{1f1ea}',GB:'\u{1f1ec}\u{1f1e7}',LV:'\u{1f1f1}\u{1f1fb}',PL:'\u{1f1f5}\u{1f1f1}',LT:'\u{1f1f1}\u{1f1f9}',FR:'\u{1f1eb}\u{1f1f7}'};

function createTenderListItem(t) {
    var item = document.createElement('div');
    item.className = 'tender-list-item';
    item.addEventListener('click', function() { showTenderDetail(t.id); });

    var flag = document.createElement('span');
    flag.className = 'tender-list-flag';
    flag.textContent = FLAGS[t.country_code] || '';
    item.appendChild(flag);

    var info = document.createElement('div');
    info.className = 'tender-list-info';
    var name = document.createElement('div');
    name.className = 'tender-list-name';
    name.textContent = t.name || '';
    info.appendChild(name);
    var org = document.createElement('div');
    org.className = 'tender-list-org';
    org.textContent = t.authority || '';
    info.appendChild(org);
    item.appendChild(info);

    if (t.is_green || t.is_eu_funded) {
        var tags = document.createElement('div');
        tags.className = 'tender-list-tags';
        if (t.is_green) {
            var gt = document.createElement('span');
            gt.className = 'tender-list-tag tlt-green';
            gt.textContent = _t('tender.green', 'Green');
            tags.appendChild(gt);
        }
        if (t.is_eu_funded) {
            var et = document.createElement('span');
            et.className = 'tender-list-tag tlt-eu';
            et.textContent = _t('tender.eu', 'EU');
            tags.appendChild(et);
        }
        item.appendChild(tags);
    }

    var meta = document.createElement('div');
    meta.className = 'tender-list-meta';
    var valStr = t.value ? new Intl.NumberFormat('en',{style:'currency',currency:t.currency||'EUR',maximumFractionDigits:0}).format(t.value) : '';
    if (valStr) {
        var valSpan = document.createElement('span');
        valSpan.className = 'tender-list-value';
        valSpan.textContent = valStr;
        meta.appendChild(valSpan);
    }
    if (t.quality_score != null) {
        var qBadge = document.createElement('span');
        var qsVal = Math.round(t.quality_score);
        if (qsVal >= 70) {
            qBadge.className = 'tender-list-badge tlb-quality-high';
        } else if (qsVal >= 50) {
            qBadge.className = 'tender-list-badge tlb-quality-mid';
        } else {
            qBadge.className = 'tender-list-badge tlb-quality-low';
        }
        qBadge.textContent = qsVal + '/100';
        meta.appendChild(qBadge);
    }
    if (t.deadline) {
        try {
            var dt = new Date(t.deadline);
            var daysLeft = Math.ceil((dt - new Date()) / 86400000);
            var badge = document.createElement('span');
            if (daysLeft > 0) {
                badge.className = 'tender-list-badge ' + (daysLeft < 7 ? 'tlb-urgent' : 'tlb-normal');
                badge.textContent = _t('tender.days_left', '{days}d left').replace('{days}', daysLeft);
            } else {
                badge.className = 'tender-list-badge tlb-expired';
                badge.textContent = _t('tender.expired', 'Expired');
            }
            meta.appendChild(badge);
        } catch(e) {}
    }
    if (t.tendly_url) {
        var linkBtn = document.createElement('a');
        linkBtn.className = 'tender-list-link';
        linkBtn.href = t.tendly_url;
        linkBtn.target = '_blank';
        linkBtn.rel = 'noopener';
        linkBtn.title = _t('tender.view_on_tendly', 'View on Tendly');
        linkBtn.addEventListener('click', function(e) { e.stopPropagation(); });
        var linkSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        linkSvg.setAttribute('width', '14');
        linkSvg.setAttribute('height', '14');
        linkSvg.setAttribute('viewBox', '0 0 24 24');
        linkSvg.setAttribute('fill', 'none');
        linkSvg.setAttribute('stroke', 'currentColor');
        linkSvg.setAttribute('stroke-width', '2');
        linkSvg.setAttribute('stroke-linecap', 'round');
        linkSvg.setAttribute('stroke-linejoin', 'round');
        var p1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p1.setAttribute('d', 'M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6');
        linkSvg.appendChild(p1);
        var p2 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        p2.setAttribute('points', '15 3 21 3 21 9');
        linkSvg.appendChild(p2);
        var p3 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        p3.setAttribute('x1', '10');
        p3.setAttribute('y1', '14');
        p3.setAttribute('x2', '21');
        p3.setAttribute('y2', '3');
        linkSvg.appendChild(p3);
        linkBtn.appendChild(linkSvg);
        item.appendChild(linkBtn);
    }
    item.appendChild(meta);

    return item;
}

function createTenderResultsElement(tenderList) {
    var MAX_VISIBLE = 5;
    var container = document.createElement('div');
    container.className = 'tender-results';

    var header = document.createElement('div');
    header.className = 'tender-results-header';
    var title = document.createElement('span');
    title.className = 'tender-results-title';
    title.textContent = _t('tender.matching', 'Matching tenders');
    header.appendChild(title);
    var count = document.createElement('span');
    count.className = 'tender-results-count';
    count.textContent = tenderList.length + ' ' + (tenderList.length !== 1 ? _t('tender.results', 'results') : _t('tender.result', 'result'));
    header.appendChild(count);
    container.appendChild(header);

    var list = document.createElement('div');
    list.className = 'tender-list';

    tenderList.forEach(function(t, i) {
        var item = createTenderListItem(t);
        if (i >= MAX_VISIBLE) {
            item.style.display = 'none';
            item.dataset.hidden = '1';
        }
        list.appendChild(item);
    });

    if (tenderList.length > MAX_VISIBLE) {
        var btn = document.createElement('button');
        btn.className = 'tender-show-more-btn';
        btn.dataset.expanded = '0';
        var chevronSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>';
        var btnText = document.createElement('span');
        btnText.textContent = _t('tender.view_all', 'View all {count} results').replace('{count}', tenderList.length);
        btn.appendChild(btnText);
        var chevronWrap = document.createElement('span');
        chevronWrap.style.display = 'flex';
        chevronWrap.innerHTML = chevronSvg;
        btn.appendChild(chevronWrap);

        btn.addEventListener('click', function() {
            var expanded = btn.dataset.expanded === '1';
            var hiddenItems = list.querySelectorAll('[data-hidden]');
            hiddenItems.forEach(function(el) {
                el.style.display = expanded ? 'none' : '';
            });
            btn.dataset.expanded = expanded ? '0' : '1';
            btnText.textContent = expanded ? _t('tender.view_all', 'View all {count} results').replace('{count}', tenderList.length) : _t('tender.show_less', 'Show less');
            btn.classList.toggle('expanded', !expanded);
        });
        list.appendChild(btn);
    }

    container.appendChild(list);
    return container;
}

function extractTryAlsoSuggestions(text) {
    if (!text) return [];
    var match = text.match(/\*?\*?Try also:?\*?\*?\s*([\s\S]+?)$/i);
    if (!match) return [];
    var raw = match[1];
    var lines = raw.split('\n');
    var results = [];
    lines.forEach(function(line) {
        var cleaned = line.replace(/^\s*[\*\-\d\.]+\s*/, '').replace(/^["']+|["']+$/g, '').trim();
        if (cleaned.length > 3 && cleaned.length < 80) results.push(cleaned);
    });
    if (results.length === 0) {
        results = raw.split(/[,|]/).map(function(s) { return s.replace(/^\s*[\-\*\"\']+\s*/, '').replace(/[\"\'\.\s]+$/, '').trim(); });
        results = results.filter(function(s) { return s.length > 3 && s.length < 80; });
    }
    return results;
}

function createSuggestionChips(suggestions) {
    if (!suggestions || suggestions.length === 0) return null;
    var container = document.createElement('div');
    container.className = 'suggestion-chips';
    suggestions.forEach(function(text) {
        var chip = document.createElement('button');
        chip.className = 'suggestion-chip';
        var arrow = document.createElement('span');
        arrow.style.display = 'flex';
        arrow.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
        chip.appendChild(document.createTextNode(text));
        chip.appendChild(arrow);
        chip.addEventListener('click', function() { sendMessage(text); });
        container.appendChild(chip);
    });
    return container;
}

// ---- Copy actions ----
// Note: SVG icons below are trusted, hardcoded strings - same pattern as existing icons in this file
var COPY_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
var CHECK_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
var LINK_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>';

function createSvgIcon(svgString) {
    var parser = new DOMParser();
    var doc = parser.parseFromString(svgString, 'image/svg+xml');
    return document.adoptNode(doc.documentElement);
}

window.copyMessageContent = function(btn) {
    var msgEl = btn.closest('.message');
    if (!msgEl) return;
    var textEl = msgEl.querySelector('.message-text');
    if (!textEl) return;
    var text = textEl.innerText || textEl.textContent || '';
    navigator.clipboard.writeText(text.trim()).then(function() {
        showCopiedFeedback(btn, _t('chat.copied', 'Copied'));
    }).catch(function() {
        var ta = document.createElement('textarea');
        ta.value = text.trim();
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showCopiedFeedback(btn, _t('chat.copied', 'Copied'));
    });
};

window.copyConversationLink = function(btn) {
    var cid = activeConversationId || document.body.dataset.conversationId;
    if (!cid) return;
    var url = window.location.origin + '/chat/c/' + cid;
    navigator.clipboard.writeText(url).then(function() {
        if (btn) showCopiedFeedback(btn, _t('chat.link_copied', 'Link copied'));
    }).catch(function() {
        var ta = document.createElement('textarea');
        ta.value = url;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        if (btn) showCopiedFeedback(btn, _t('chat.link_copied', 'Link copied'));
    });
};

function showCopiedFeedback(btn, labelText) {
    var label = btn.querySelector('.action-btn-label');
    var origLabel = label ? label.textContent : '';
    var origSvg = btn.querySelector('svg');
    var newIcon = createSvgIcon(CHECK_ICON);
    if (origSvg) btn.replaceChild(newIcon, origSvg);
    if (label) label.textContent = labelText;
    btn.classList.add('copied');
    setTimeout(function() {
        var isLink = btn.classList.contains('copy-link-btn');
        var restoredIcon = createSvgIcon(isLink ? LINK_ICON : COPY_ICON);
        var currentSvg = btn.querySelector('svg');
        if (currentSvg) btn.replaceChild(restoredIcon, currentSvg);
        if (label) label.textContent = origLabel;
        btn.classList.remove('copied');
    }, 2000);
}

function createMessageActionBar() {
    var bar = document.createElement('div');
    bar.className = 'message-actions';

    var copyBtn = document.createElement('button');
    copyBtn.className = 'msg-action-btn copy-msg-btn';
    copyBtn.title = _t('chat.copy', 'Copy');
    copyBtn.addEventListener('click', function() { copyMessageContent(copyBtn); });
    copyBtn.appendChild(createSvgIcon(COPY_ICON));
    var copyLabel = document.createElement('span');
    copyLabel.className = 'action-btn-label';
    copyLabel.textContent = _t('chat.copy', 'Copy');
    copyBtn.appendChild(copyLabel);
    bar.appendChild(copyBtn);

    var linkBtn = document.createElement('button');
    linkBtn.className = 'msg-action-btn copy-link-btn';
    linkBtn.title = _t('chat.copy_link', 'Copy link');
    linkBtn.addEventListener('click', function() { copyConversationLink(linkBtn); });
    linkBtn.appendChild(createSvgIcon(LINK_ICON));
    var linkLabel = document.createElement('span');
    linkLabel.className = 'action-btn-label';
    linkLabel.textContent = _t('chat.copy_link', 'Copy link');
    linkBtn.appendChild(linkLabel);
    bar.appendChild(linkBtn);

    return bar;
}

// ---- Canvas Panel Management ----
window.openCanvas = function(title, html) {
    var panel = qs('#canvas-panel');
    var body = qs('#canvas-body');
    var titleEl = qs('#canvas-title');
    if (!panel || !body) return;

    // Set title
    if (titleEl) titleEl.textContent = title || 'Detail';

    // Insert HTML content
    while (body.firstChild) body.removeChild(body.firstChild);
    if (typeof html === 'string') {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');
        var nodes = doc.body.childNodes;
        while (nodes.length > 0) {
            body.appendChild(document.adoptNode(nodes[0]));
        }
    } else if (html instanceof Node) {
        body.appendChild(html);
    }

    // Show panel
    panel.classList.add('open');
};

window.closeCanvas = function() {
    var panel = qs('#canvas-panel');
    if (panel) panel.classList.remove('open');
};

// Open a server-rendered artifact in canvas by fetching its HTML
window.openArtifact = function(type, id, title) {
    var convId = activeConversationId || document.body.dataset.conversationId || '';
    var url = '/api/artifact/' + type + '/' + encodeURIComponent(id) + '?conversation_id=' + encodeURIComponent(convId);
    fetch(url)
        .then(function(resp) {
            if (!resp.ok) return null;
            return resp.text();
        })
        .then(function(html) {
            if (!html) return;
            openCanvas(title || type, html);
        })
        .catch(function(e) { console.error('Artifact load error', e); });
};

// Open tender detail in canvas (replaces old overlay approach)
window.showTenderDetail = function(id) {
    fetch('/api/tender/' + id)
        .then(function(resp) {
            if (!resp.ok) return null;
            return resp.text();
        })
        .then(function(html) {
            if (!html) return;

            // Clean up any legacy overlay panels
            var existing = qs('.detail-panel');
            if (existing) existing.remove();
            var existingOverlay = qs('.detail-overlay');
            if (existingOverlay) existingOverlay.remove();

            // Open in canvas
            openCanvas(_t('canvas.tender_detail', 'Tender Detail'), html);
        })
        .catch(function(e) { console.error('Tender detail error', e); });
};

// Legacy close — now closes canvas
window.closeDetailPanel = function() {
    closeCanvas();
};

window.toggleReqItems = function(sectionId) {
    var hidden = document.getElementById(sectionId + '-hidden');
    var btn = document.getElementById(sectionId + '-btn');
    if (!hidden || !btn) return;
    var isVisible = hidden.style.display !== 'none';
    hidden.style.display = isVisible ? 'none' : 'block';
    btn.textContent = isVisible ? btn.dataset.showMore : btn.dataset.showLess;
};

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        // Close canvas if open
        var canvas = qs('#canvas-panel.open');
        if (canvas) {
            e.preventDefault();
            closeCanvas();
            return;
        }
        // Legacy: close old detail panel if present
        var panel = qs('.detail-panel');
        if (panel) {
            e.preventDefault();
            closeDetailPanel();
        }
    }
});

function createMessageElement(role, content) {
    var msg = document.createElement('div');
    msg.className = 'message ' + (role === 'user' ? 'user-message' : 'ai-message');

    var inner = document.createElement('div');
    inner.className = 'message-inner';

    var avatar = document.createElement('div');
    avatar.className = 'avatar ' + (role === 'user' ? 'user-avatar' : 'ai-avatar');
    avatar.textContent = role === 'user' ? 'Y' : 'T';
    inner.appendChild(avatar);

    var contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    var sender = document.createElement('div');
    sender.className = 'message-sender';
    sender.textContent = role === 'user' ? _t('chat.you', 'You') : _t('chat.tendly_ai', 'Tendly AI');
    contentDiv.appendChild(sender);

    var textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    if (role === 'user') {
        textDiv.textContent = content;
    }
    contentDiv.appendChild(textDiv);

    inner.appendChild(contentDiv);
    msg.appendChild(inner);
    return { element: msg, textDiv: textDiv, contentDiv: contentDiv, isAi: role === 'ai' };
}

function createThinkingIndicator() {
    var result = createMessageElement('ai', '');
    var indicator = document.createElement('div');
    indicator.className = 'thinking-indicator';

    var steps = [
        { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>', text: _t('chat.understanding', 'Understanding your query') },
        { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>', text: _t('chat.searching', 'Searching tenders') },
        { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>', text: _t('chat.analyzing', 'Analyzing results') },
    ];

    var stepEls = [];
    steps.forEach(function(s, idx) {
        var step = document.createElement('div');
        step.className = 'thinking-step';
        step.style.animationDelay = (idx * 0.12) + 's';

        var iconWrap = document.createElement('div');
        iconWrap.className = 'thinking-step-icon';
        iconWrap.innerHTML = s.icon;
        step.appendChild(iconWrap);

        var textEl = document.createElement('span');
        textEl.className = 'thinking-step-text';
        textEl.textContent = s.text;
        step.appendChild(textEl);

        var dots = document.createElement('span');
        dots.className = 'thinking-dots-inline';
        dots.style.display = 'none';
        for (var d = 0; d < 3; d++) dots.appendChild(document.createElement('span'));
        textEl.appendChild(dots);

        indicator.appendChild(step);
        stepEls.push({ el: step, dots: dots });
    });

    // Skeleton shimmer
    var skeleton = document.createElement('div');
    skeleton.className = 'thinking-skeleton';
    for (var k = 0; k < 3; k++) {
        var line = document.createElement('div');
        line.className = 'skeleton-line';
        skeleton.appendChild(line);
    }
    indicator.appendChild(skeleton);

    result.textDiv.replaceWith(indicator);

    // Animate through steps
    var currentStep = 0;
    function activateStep(idx) {
        if (idx >= stepEls.length) return;
        if (idx > 0) {
            stepEls[idx - 1].el.classList.remove('active');
            stepEls[idx - 1].el.classList.add('done');
            stepEls[idx - 1].dots.style.display = 'none';
            var checkSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>';
            stepEls[idx - 1].el.querySelector('.thinking-step-icon').innerHTML = checkSvg;
        }
        stepEls[idx].el.classList.add('active');
        stepEls[idx].dots.style.display = 'inline-flex';
        currentStep = idx;
    }

    // Start first step immediately
    setTimeout(function() { activateStep(0); }, 300);
    // Progress to step 2 after 1.5s
    var t1 = setTimeout(function() { activateStep(1); }, 1800);
    // Progress to step 3 after 4s
    var t2 = setTimeout(function() { activateStep(2); }, 4500);

    result.element._thinkingTimers = [t1, t2];
    return result.element;
}

function sendMessage(text) {
    if (!text.trim() || isStreaming) return;

    // Client-side rate limit check (server also enforces)
    var rate = window.__RATE__ || {};
    if (rate.remaining === 0 && rate.limit !== -1) {
        showUpgradeModal(rate.tier);
        return;
    }

    isStreaming = true;

    var input = qs('#chat-input');
    var sendBtn = qs('#send-btn');
    if (input) { input.value = ''; input.style.height = 'auto'; }
    if (sendBtn) sendBtn.disabled = true;

    var welcomeWrapper = qs('.welcome-wrapper');
    if (welcomeWrapper) {
        var messagesDiv = document.createElement('div');
        messagesDiv.id = 'messages';
        messagesDiv.className = 'messages-container';
        welcomeWrapper.replaceWith(messagesDiv);
    }

    var messagesEl = qs('#messages');

    if (messagesEl) {
        var userMsg = createMessageElement('user', text);
        messagesEl.appendChild(userMsg.element);
        scrollToBottom(true);
    }

    var thinkingEl = createThinkingIndicator();
    if (messagesEl) {
        messagesEl.appendChild(thinkingEl);
        scrollToBottom(true);
    }

    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ conversation_id: activeConversationId, message: text }),
    }).then(function(resp) {
        // Keep thinking indicator visible — only replace on first chunk
        var aiMsg = null;
        var thinkingRemoved = false;
        var rawText = '';
        var reader = resp.body.getReader();
        var decoder = new TextDecoder();
        var buffer = '';
        var pendingEventType = '';

        function removeThinking() {
            if (thinkingRemoved) return;
            thinkingRemoved = true;
            if (thinkingEl) {
                if (thinkingEl._thinkingTimers) thinkingEl._thinkingTimers.forEach(clearTimeout);
                if (thinkingEl.parentNode) thinkingEl.remove();
            }
        }

        function ensureAiMsg() {
            if (aiMsg) return;
            removeThinking();
            aiMsg = createMessageElement('ai', '');
            aiMsg.textDiv.classList.add('streaming-cursor');
            if (messagesEl) {
                messagesEl.appendChild(aiMsg.element);
                scrollToBottom(true);
            }
        }

        function readChunk() {
            reader.read().then(function(result) {
                if (result.done) {
                    ensureAiMsg();
                    aiMsg.textDiv.classList.remove('streaming-cursor');
                    var suggestions = extractTryAlsoSuggestions(rawText);
                    if (suggestions.length > 0) {
                        var cleanedText = rawText.replace(/\*?\*?Try also:?\*?\*?\s*[\s\S]*$/i, '').trim();
                        aiMsg.textDiv.textContent = '';
                        aiMsg.textDiv.appendChild(renderMarkdownToFragment(cleanedText));
                        var chips = createSuggestionChips(suggestions);
                        if (chips) aiMsg.contentDiv.appendChild(chips);
                    }
                    // Add copy/link action buttons
                    if (aiMsg.isAi) {
                        aiMsg.contentDiv.appendChild(createMessageActionBar());
                    }
                    isStreaming = false;
                    if (sendBtn) sendBtn.disabled = false;
                    if (input) input.focus();
                    scrollToBottom(true);
                    return;
                }
                buffer += decoder.decode(result.value, {stream: true});
                var lines = buffer.split('\n');
                buffer = lines.pop();

                lines.forEach(function(line) {
                    if (line.indexOf('event: ') === 0) {
                        pendingEventType = line.slice(7).trim();
                    } else if (line.indexOf('data: ') === 0) {
                        var data = line.slice(6);
                        try {
                            var parsed = JSON.parse(data);
                            if (pendingEventType === 'chunk' && parsed.text != null) {
                                ensureAiMsg();
                                rawText += parsed.text;
                                while (aiMsg.textDiv.firstChild) {
                                    aiMsg.textDiv.removeChild(aiMsg.textDiv.firstChild);
                                }
                                aiMsg.textDiv.appendChild(renderMarkdownToFragment(rawText));
                                scrollToBottom(false);
                            } else if (pendingEventType === 'tenders') {
                                ensureAiMsg();
                                var tenderList = Array.isArray(parsed) ? parsed : (parsed.tenders || []);
                                if (tenderList.length > 0) {
                                    var resultsEl = createTenderResultsElement(tenderList);
                                    aiMsg.contentDiv.appendChild(resultsEl);
                                    scrollToBottom(false);
                                }
                            } else if (pendingEventType === 'artifact') {
                                // Open canvas with artifact content
                                var artType = parsed.type || 'tender_detail';
                                var artId = parsed.id;
                                var artTenderId = parsed.tender_id;
                                if (artType === 'tender_detail' && artTenderId) {
                                    showTenderDetail(artTenderId);
                                } else if (artType === 'competitor_intel' && artId) {
                                    openArtifact(artType, artId, _t('canvas.competitor_intel', 'Competitor Intelligence'));
                                } else if (artType === 'tender_comparison' && artId) {
                                    openArtifact(artType, artId, _t('canvas.tender_comparison', 'Tender Comparison'));
                                } else if (artType === 'risk_analysis' && artId) {
                                    openArtifact(artType, artId, _t('canvas.risk_analysis', 'Risk Analysis'));
                                } else if (artType === 'winning_strategy' && artId) {
                                    openArtifact(artType, artId, _t('canvas.winning_strategy', 'Winning Strategy'));
                                } else if (artType === 'gap_analysis' && artId) {
                                    openArtifact(artType, artId, _t('canvas.gap_analysis', 'Gap Analysis'));
                                } else if (artType === 'requirements' && artId) {
                                    openArtifact(artType, artId, _t('canvas.requirements', 'Requirements'));
                                } else if (artType === 'price_benchmark' && artId) {
                                    openArtifact(artType, artId, _t('canvas.price_benchmark', 'Price Benchmarks'));
                                } else if (artType === 'rfp_draft' && artId) {
                                    openArtifact(artType, artId, _t('canvas.rfp_draft', 'RFP Draft'));
                                }
                            } else if (pendingEventType === 'rate_limit') {
                                // Rate limit hit — show upgrade modal
                                removeThinking();
                                isStreaming = false;
                                if (sendBtn) sendBtn.disabled = false;
                                if (input) input.focus();
                                showUpgradeModal(parsed.tier || 'anonymous');
                                return;
                            } else if (pendingEventType === 'done') {
                                activeConversationId = parsed.conversation_id || activeConversationId;
                                if (parsed.title) updateSidebarTitle(activeConversationId, parsed.title);
                                addConversationToSidebar(activeConversationId, parsed.title || 'New Chat');
                                // Update rate info from server
                                if (parsed.rate) {
                                    window.__RATE__ = parsed.rate;
                                    updateMessageCounter();
                                }
                                // Save to localStorage
                                saveMessageToHistory(activeConversationId, text, rawText, parsed.title);
                            }
                        } catch(e) {}
                        pendingEventType = '';
                    }
                });

                readChunk();
            }).catch(function(err) {
                console.error('Stream read error', err);
                removeThinking();
                ensureAiMsg();
                aiMsg.textDiv.classList.remove('streaming-cursor');
                aiMsg.textDiv.textContent = _t('chat.stream_error', 'Sorry, something went wrong. Please try again.');
                isStreaming = false;
                if (sendBtn) sendBtn.disabled = false;
                if (input) input.focus();
            });
        }
        readChunk();

    }).catch(function(err) {
        if (thinkingEl && thinkingEl._thinkingTimers) thinkingEl._thinkingTimers.forEach(clearTimeout);
        if (thinkingEl && thinkingEl.parentNode) {
            var errContent = thinkingEl.querySelector('.message-content');
            if (errContent) {
                while (errContent.firstChild) errContent.removeChild(errContent.firstChild);
                var sender = document.createElement('div');
                sender.className = 'message-sender';
                sender.textContent = _t('chat.tendly_ai', 'Tendly AI');
                errContent.appendChild(sender);
                var errMsg = document.createElement('div');
                errMsg.className = 'message-text';
                errMsg.textContent = _t('chat.error', 'Sorry, something went wrong. Please try again.');
                errContent.appendChild(errMsg);
            }
        }
        console.error('Chat error', err);
        isStreaming = false;
        if (sendBtn) sendBtn.disabled = false;
        if (input) input.focus();
    });
}

function addConversationToSidebar(id, title) {
    if (!id) return;
    var list = qs('.conversation-list');
    if (!list) return;
    if (list.querySelector('[data-conv-id="' + id + '"]')) return;
    var empty = list.querySelector('.conv-empty');
    if (empty) empty.remove();

    var a = document.createElement('a');
    a.className = 'conv-item active';
    a.dataset.convId = id;
    a.href = '/chat/c/' + id;
    a.addEventListener('click', function(e) { e.preventDefault(); window.location.href = '/chat/c/' + id; });

    var textSpan = document.createElement('span');
    textSpan.className = 'conv-item-text';
    textSpan.textContent = title;
    a.appendChild(textSpan);

    var delBtn = document.createElement('button');
    delBtn.className = 'conv-delete';
    delBtn.addEventListener('click', function(e) { e.stopPropagation(); e.preventDefault(); window.deleteConversation(id); });
    var delSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    delSvg.setAttribute('viewBox', '0 0 24 24');
    delSvg.setAttribute('fill', 'none');
    delSvg.setAttribute('stroke', 'currentColor');
    delSvg.setAttribute('stroke-width', '2');
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M18 6L6 18M6 6l12 12');
    delSvg.appendChild(path);
    delBtn.appendChild(delSvg);
    a.appendChild(delBtn);

    list.insertBefore(a, list.firstChild);

    qsa('.conv-item', list).forEach(function(el) {
        if (el.dataset.convId !== id) el.classList.remove('active');
    });
}

function updateSidebarTitle(id, title) {
    var item = document.querySelector('[data-conv-id="'+id+'"] .conv-item-text');
    if (item) item.textContent = title;
}

window.loadConversation = function(e, id) {
    e.preventDefault();
    window.location.href = '/chat/c/' + id;
    return false;
};

window.newChat = function() {
    window.location.href = '/chat';
};

window.deleteConversation = function(id) {
    fetch('/api/conversations/' + id, { method: 'DELETE' })
        .then(function() {
            var el = document.querySelector('[data-conv-id="'+id+'"]');
            if (el) el.remove();
            if (activeConversationId === id) {
                window.location.href = '/chat';
            }
        })
        .catch(function(e) { console.error('Delete error', e); });
};

window.useSuggestion = function(text) {
    var input = qs('#chat-input');
    if (input) { input.value = text; input.focus(); }
    sendMessage(text);
};

document.addEventListener('submit', function(e) {
    if (e.target.id === 'chat-form') {
        e.preventDefault();
        var input = qs('#chat-input');
        if (input) sendMessage(input.value);
    }
});

document.addEventListener('keydown', function(e) {
    if (e.target.id === 'chat-input' && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(e.target.value);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    activeConversationId = document.body.dataset.conversationId || null;
    scrollToBottom(false);
    var input = qs('#chat-input');
    if (input) input.focus();
    updateMessageCounter();
});

// ---- Role Switcher ----
window.switchRole = function(role) {
    fetch('/api/role/switch/' + role, { method: 'POST' })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (data.ok) {
                window.__ROLE__ = role;
                // Update tab active states
                var buyerTab = qs('#role-tab-buyer');
                var sellerTab = qs('#role-tab-seller');
                if (buyerTab) buyerTab.className = 'role-tab' + (role === 'buyer' ? ' active' : '');
                if (sellerTab) sellerTab.className = 'role-tab' + (role === 'seller' ? ' active' : '');
                // Show/hide buyer nav section
                var buyerNav = qs('.sidebar-nav-section');
                if (buyerNav) buyerNav.style.display = role === 'buyer' ? '' : 'none';
                // Reload to get full server-side update
                window.location.reload();
            }
        })
        .catch(function(e) { console.error('Role switch error', e); });
};

// ---- Save to Pipeline ----
function showToast(message, type) {
    var existing = qs('.toast-notification');
    if (existing) existing.remove();
    var toast = document.createElement('div');
    toast.className = 'toast-notification toast-' + (type || 'success');
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(function() { toast.classList.add('show'); });
    setTimeout(function() {
        toast.classList.remove('show');
        setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
}

window.saveTender = function(tenderId) {
    if (!window.__AUTH__) {
        promptLogin();
        return;
    }
    var btn = document.getElementById('save-btn-' + tenderId);
    if (btn) {
        btn.disabled = true;
        btn.textContent = '...';
    }
    fetch('/api/save-tender/' + tenderId, { method: 'POST' })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (data.ok || data.already_saved) {
                showToast(_t('pipeline.saved', 'Saved to pipeline'), 'success');
                if (btn) {
                    btn.disabled = false;
                    btn.className = 'detail-save-btn saved';
                    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg> ' + _t('tender.saved', 'Saved');
                    btn.setAttribute('onclick', 'unsaveTender(' + tenderId + ')');
                }
            } else if (!data.authenticated) {
                promptLogin();
                if (btn) btn.disabled = false;
            } else {
                showToast(_t('pipeline.save_error', 'Failed to save tender'), 'error');
                if (btn) btn.disabled = false;
            }
        })
        .catch(function() {
            showToast(_t('pipeline.save_error', 'Failed to save tender'), 'error');
            if (btn) btn.disabled = false;
        });
};

window.unsaveTender = function(tenderId) {
    var btn = document.getElementById('save-btn-' + tenderId);
    if (btn) {
        btn.disabled = true;
        btn.textContent = '...';
    }
    fetch('/api/unsave-tender/' + tenderId, { method: 'POST' })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (data.ok) {
                showToast(_t('pipeline.removed', 'Removed from pipeline'), 'success');
                if (btn) {
                    btn.disabled = false;
                    btn.className = 'detail-save-btn';
                    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg> ' + _t('tender.save_to_pipeline', 'Save to Pipeline');
                    btn.setAttribute('onclick', 'saveTender(' + tenderId + ')');
                }
            } else {
                showToast(_t('pipeline.save_error', 'Failed to save tender'), 'error');
                if (btn) btn.disabled = false;
            }
        })
        .catch(function() {
            showToast(_t('pipeline.save_error', 'Failed to save tender'), 'error');
            if (btn) btn.disabled = false;
        });
};

// Trusted static SVG strings used only for hardcoded icons (never user input)
var BOOKMARK_SVG = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>';
var CLOSE_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>';
var BOLT_SVG = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>';
var CHECK_MARK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>';

function _createIconDiv(svgStr, className) {
    var parser = new DOMParser();
    var doc = parser.parseFromString(svgStr, 'image/svg+xml');
    var svg = document.adoptNode(doc.documentElement);
    var div = document.createElement('div');
    if (className) div.className = className;
    div.appendChild(svg);
    return div;
}

function _createCloseButton(onClickFn) {
    var parser = new DOMParser();
    var doc = parser.parseFromString(CLOSE_SVG, 'image/svg+xml');
    var svg = document.adoptNode(doc.documentElement);
    var btn = document.createElement('button');
    btn.className = 'login-modal-close';
    btn.appendChild(svg);
    btn.addEventListener('click', onClickFn);
    return btn;
}

window.promptLogin = function() {
    var existing = qs('.login-modal-overlay');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.className = 'login-modal-overlay';
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) overlay.remove();
    });

    var modal = document.createElement('div');
    modal.className = 'login-modal';

    modal.appendChild(_createIconDiv(BOOKMARK_SVG, 'login-modal-icon'));

    var title = document.createElement('h3');
    title.className = 'login-modal-title';
    title.textContent = _t('auth.login_prompt_title', 'Save to Pipeline');
    modal.appendChild(title);

    var text = document.createElement('p');
    text.className = 'login-modal-text';
    text.textContent = _t('auth.login_prompt_text', 'Log in to your Tendly account to save tenders to your pipeline and track them.');
    modal.appendChild(text);

    var actions = document.createElement('div');
    actions.className = 'login-modal-actions';

    var loginBtn = document.createElement('a');
    loginBtn.className = 'login-modal-btn login-modal-btn-primary';
    loginBtn.href = '/login';
    loginBtn.textContent = _t('auth.login_button', 'Log in');
    actions.appendChild(loginBtn);

    var signupBtn = document.createElement('a');
    signupBtn.className = 'login-modal-btn login-modal-btn-secondary';
    signupBtn.href = 'https://tendly.eu/signup';
    signupBtn.target = '_blank';
    signupBtn.rel = 'noopener';
    signupBtn.textContent = _t('auth.signup_button', 'Sign up');
    actions.appendChild(signupBtn);

    modal.appendChild(actions);
    modal.appendChild(_createCloseButton(function() { overlay.remove(); }));

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
};

// ---- Message Counter ----
function updateMessageCounter() {
    var counter = qs('#msg-counter');
    if (!counter) return;
    var rate = window.__RATE__ || {};
    var remaining = rate.remaining;
    var limit = rate.limit;

    if (limit === -1 || remaining === -1) {
        counter.className = 'msg-counter unlimited';
        counter.textContent = '';
        return;
    }

    counter.textContent = _t('chat.messages_remaining', '{remaining} of {limit} messages remaining')
        .replace('{remaining}', remaining)
        .replace('{limit}', limit);

    if (remaining <= 0) {
        counter.className = 'msg-counter exhausted';
    } else if (remaining <= Math.ceil(limit * 0.25)) {
        counter.className = 'msg-counter low';
    } else {
        counter.className = 'msg-counter';
    }
}

// ---- Upgrade Modal ----
function showUpgradeModal(tier) {
    var existing = qs('.upgrade-modal-overlay');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.className = 'upgrade-modal-overlay';
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) overlay.remove();
    });

    var modal = document.createElement('div');
    modal.className = 'upgrade-modal';

    modal.appendChild(_createIconDiv(BOLT_SVG, 'upgrade-modal-icon'));

    var title = document.createElement('h3');
    title.className = 'upgrade-modal-title';
    modal.appendChild(title);

    var text = document.createElement('p');
    text.className = 'upgrade-modal-text';
    modal.appendChild(text);

    if (tier === 'anonymous') {
        title.textContent = _t('upgrade.anon_title', 'Message limit reached');
        text.textContent = _t('upgrade.anon_text', 'Sign up for a free Tendly account to get 20 messages per day and save tenders to your pipeline.');
    } else {
        title.textContent = _t('upgrade.free_title', 'Daily limit reached');
        text.textContent = _t('upgrade.free_text', 'Upgrade to Tendly Professional for unlimited chat messages, AI matching, and more.');
    }

    var features = document.createElement('div');
    features.className = 'upgrade-modal-features';
    var featureTexts = [
        _t('upgrade.feature_unlimited', 'Unlimited chat messages'),
        _t('upgrade.feature_matching', 'AI tender matching'),
        _t('upgrade.feature_pipeline', 'Save tenders to pipeline'),
    ];
    featureTexts.forEach(function(ft) {
        var row = document.createElement('div');
        row.className = 'upgrade-modal-feature';
        var parser = new DOMParser();
        var doc = parser.parseFromString(CHECK_MARK_SVG, 'image/svg+xml');
        row.appendChild(document.adoptNode(doc.documentElement));
        var span = document.createElement('span');
        span.textContent = ft;
        row.appendChild(span);
        features.appendChild(row);
    });
    modal.appendChild(features);

    var actions = document.createElement('div');
    actions.className = 'upgrade-modal-actions';

    if (tier === 'anonymous') {
        var loginBtn = document.createElement('a');
        loginBtn.className = 'upgrade-modal-btn-primary';
        loginBtn.href = '/login';
        loginBtn.textContent = _t('auth.login_button', 'Log in');
        actions.appendChild(loginBtn);

        var signupBtn = document.createElement('a');
        signupBtn.className = 'upgrade-modal-btn-secondary';
        signupBtn.href = 'https://tendly.eu/signup';
        signupBtn.target = '_blank';
        signupBtn.rel = 'noopener';
        signupBtn.textContent = _t('auth.signup_button', 'Sign up');
        actions.appendChild(signupBtn);
    } else {
        var upgradeBtn = document.createElement('a');
        upgradeBtn.className = 'upgrade-modal-btn-primary';
        upgradeBtn.href = 'https://tendly.eu/pricing';
        upgradeBtn.target = '_blank';
        upgradeBtn.rel = 'noopener';
        upgradeBtn.textContent = _t('upgrade.view_plans', 'View plans');
        actions.appendChild(upgradeBtn);

        var dismissBtn = document.createElement('button');
        dismissBtn.className = 'upgrade-modal-btn-secondary';
        dismissBtn.textContent = _t('upgrade.dismiss', 'Maybe later');
        dismissBtn.addEventListener('click', function() { overlay.remove(); });
        actions.appendChild(dismissBtn);
    }
    modal.appendChild(actions);

    modal.appendChild(_createCloseButton(function() { overlay.remove(); }));

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
}

// ---- localStorage Chat History ----
function _historyKey() {
    if (window.__AUTH__) {
        try {
            var stored = localStorage.getItem('tendly_chat_user');
            if (stored) return 'tendly_chat_history_' + stored;
        } catch(e) {}
    }
    return 'tendly_chat_history_anon';
}

function saveMessageToHistory(convId, userText, aiText, title) {
    if (!convId) return;
    try {
        var key = _historyKey();
        var history = JSON.parse(localStorage.getItem(key) || '{}');
        if (!history[convId]) {
            history[convId] = { title: title || 'New Chat', messages: [], updated: Date.now() };
        }
        history[convId].title = title || history[convId].title;
        history[convId].updated = Date.now();
        if (userText) {
            history[convId].messages.push({ role: 'user', content: userText, ts: Date.now() });
        }
        if (aiText) {
            history[convId].messages.push({ role: 'ai', content: aiText, ts: Date.now() });
        }
        // Keep max 50 conversations
        var convIds = Object.keys(history);
        if (convIds.length > 50) {
            convIds.sort(function(a, b) { return (history[a].updated || 0) - (history[b].updated || 0); });
            delete history[convIds[0]];
        }
        localStorage.setItem(key, JSON.stringify(history));
    } catch(e) {
        // localStorage full or disabled
    }
}

})();
"""
