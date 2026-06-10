/* ═══════════════════════════════════════════════════════════════════════════
   Sémantický Index Dokumentů – Frontend Application
   ═══════════════════════════════════════════════════════════════════════════ */

const API_BASE = 'https://proud-tigers-worry.loca.lt/api/v1';

// ── DOM Elements ─────────────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const dropZone = $('#drop-zone');
const fileInput = $('#file-input');
const uploadProgress = $('#upload-progress');
const progressFill = $('#progress-fill');
const progressText = $('#progress-text');
const searchInput = $('#search-input');
const searchBtn = $('#search-btn');
const searchSpinner = $('#search-spinner');
const searchResults = $('#search-results');
const documentsList = $('#documents-list');
const refreshBtn = $('#refresh-btn');
const toastContainer = $('#toast-container');
const statDocs = $('#stat-docs');
const statChunks = $('#stat-chunks');

// ── Toast Notifications ──────────────────────────────────────────────────────

const TOAST_ICONS = {
    success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    error: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    info: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
};

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `${TOAST_ICONS[type] || TOAST_ICONS.info}<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        toast.addEventListener('animationend', () => toast.remove());
    }, 4000);
}

// ── File Upload ──────────────────────────────────────────────────────────────

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Please upload a PDF file.', 'error');
        return;
    }

    // Show progress
    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressFill.classList.add('indeterminate');
    progressText.textContent = `Uploading ${file.name}…`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_BASE}/documents`, {
            method: 'POST',
            headers: { 'Bypass-Tunnel-Reminder': 'true' },
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Upload failed (${res.status})`);
        }

        const data = await res.json();
        progressFill.classList.remove('indeterminate');
        progressFill.style.width = '100%';
        progressText.textContent = 'Processing document…';

        showToast(`"${file.name}" uploaded! Processing in background.`, 'success');

        // Poll for completion
        pollDocumentStatus(data.document_id);

        // Refresh list
        setTimeout(loadDocuments, 500);
    } catch (err) {
        progressFill.classList.remove('indeterminate');
        progressFill.style.width = '0%';
        progressText.textContent = 'Upload failed.';
        showToast(err.message, 'error');
    }

    // Reset file input
    fileInput.value = '';
}

async function pollDocumentStatus(docId) {
    const maxAttempts = 120; // 2 minutes max
    let attempts = 0;

    const poll = async () => {
        attempts++;
        try {
            const res = await fetch(`${API_BASE}/documents/${docId}`, {
                headers: { 'Bypass-Tunnel-Reminder': 'true' }
            });
            const doc = await res.json();

            if (doc.status === 'ready') {
                progressFill.style.width = '100%';
                progressText.textContent = `Done! ${doc.chunk_count} chunks indexed.`;
                showToast(`"${doc.filename}" is ready for search! (${doc.chunk_count} chunks)`, 'success');
                loadDocuments();
                setTimeout(() => { uploadProgress.style.display = 'none'; }, 3000);
                return;
            }
            if (doc.status === 'failed') {
                progressText.textContent = `Failed: ${doc.error_message || 'Unknown error'}`;
                showToast(`Processing failed: ${doc.error_message || 'Unknown error'}`, 'error');
                loadDocuments();
                setTimeout(() => { uploadProgress.style.display = 'none'; }, 5000);
                return;
            }
            if (attempts < maxAttempts) {
                setTimeout(poll, 2000);
            }
        } catch {
            if (attempts < maxAttempts) setTimeout(poll, 3000);
        }
    };

    setTimeout(poll, 2000);
}

// ── Search ───────────────────────────────────────────────────────────────────

let searchTimeout = null;

searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    const query = searchInput.value.trim();
    if (query.length >= 3) {
        searchTimeout = setTimeout(() => performSearch(query), 400);
    }
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        clearTimeout(searchTimeout);
        const query = searchInput.value.trim();
        if (query) performSearch(query);
    }
});

searchBtn.addEventListener('click', () => {
    clearTimeout(searchTimeout);
    const query = searchInput.value.trim();
    if (query) performSearch(query);
});

async function performSearch(query) {
    searchBtn.style.display = 'none';
    searchSpinner.style.display = 'block';

    try {
        const res = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Bypass-Tunnel-Reminder': 'true'
            },
            body: JSON.stringify({ query, limit: 8 }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Search failed');
        }

        const data = await res.json();
        renderSearchResults(data.results);
    } catch (err) {
        showToast(err.message, 'error');
        searchResults.innerHTML = `<div class="empty-state"><p>Search error: ${err.message}</p></div>`;
    } finally {
        searchBtn.style.display = 'flex';
        searchSpinner.style.display = 'none';
    }
}

function renderSearchResults(results) {
    if (!results || results.length === 0) {
        searchResults.innerHTML = `
            <div class="empty-state">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" opacity="0.3">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <p>No matching results found</p>
            </div>`;
        return;
    }

    searchResults.innerHTML = results
        .map((r, i) => {
            const scorePercent = Math.round(r.score * 100);
            const scoreClass = r.score >= 0.7 ? 'high' : r.score >= 0.4 ? 'medium' : 'low';
            const truncated = r.text.length > 300 ? r.text.substring(0, 300) + '…' : r.text;

            return `
                <div class="result-card" style="animation-delay: ${i * 0.06}s">
                    <div class="result-header">
                        <span class="result-filename">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14 2 14 8 20 8"/>
                            </svg>
                            ${escapeHtml(r.filename)}
                        </span>
                        <span class="result-score ${scoreClass}">${scorePercent}% match</span>
                    </div>
                    <p class="result-text">${escapeHtml(truncated)}</p>
                    <p class="result-meta">Chunk #${r.chunk_index + 1}</p>
                </div>`;
        })
        .join('');
}

// ── Document List ────────────────────────────────────────────────────────────

refreshBtn.addEventListener('click', loadDocuments);

async function loadDocuments() {
    try {
        const res = await fetch(`${API_BASE}/documents`, {
            headers: { 'Bypass-Tunnel-Reminder': 'true' }
        });
        if (!res.ok) throw new Error('Failed to load documents');
        const docs = await res.json();
        renderDocuments(docs);
        updateStats(docs);
    } catch (err) {
        // Silently fail on initial load if backend not ready
        console.warn('Could not load documents:', err.message);
    }
}

function renderDocuments(docs) {
    if (!docs || docs.length === 0) {
        documentsList.innerHTML = `
            <div class="empty-state">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" opacity="0.3">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
                <p>No documents uploaded yet</p>
            </div>`;
        return;
    }

    documentsList.innerHTML = docs
        .map((d, i) => {
            const date = d.created_at
                ? new Date(d.created_at).toLocaleString('cs-CZ', { dateStyle: 'short', timeStyle: 'short' })
                : '';

            return `
                <div class="doc-item" style="animation-delay: ${i * 0.05}s">
                    <div class="doc-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                    </div>
                    <div class="doc-info">
                        <div class="doc-name" title="${escapeHtml(d.filename)}">${escapeHtml(d.filename)}</div>
                        <div class="doc-details">
                            <span>${date}</span>
                            ${d.chunk_count ? `<span>${d.chunk_count} chunks</span>` : ''}
                        </div>
                    </div>
                    <span class="status-badge ${d.status}">${d.status}</span>
                    <button class="delete-btn" onclick="deleteDocument('${d.id}', '${escapeHtml(d.filename)}')" title="Delete document">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>`;
        })
        .join('');
}

function updateStats(docs) {
    statDocs.textContent = docs.length;
    const totalChunks = docs.reduce((sum, d) => sum + (d.chunk_count || 0), 0);
    statChunks.textContent = totalChunks;
}

// ── Delete Document ──────────────────────────────────────────────────────────

async function deleteDocument(docId, filename) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;

    try {
        const res = await fetch(`${API_BASE}/documents/${docId}`, { 
            method: 'DELETE',
            headers: { 'Bypass-Tunnel-Reminder': 'true' }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Delete failed');
        }
        showToast(`"${filename}" deleted.`, 'success');
        loadDocuments();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
});
