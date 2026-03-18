/**
 * CricketArb Content Script — Auto-Capture Edition
 *
 * Runs on any betting website. Two modes:
 *   1. MANUAL: Click "Select Odds" → click odds on page → click "Send"
 *   2. AUTO:   Set teams → click "Auto" → extension scans page every 7s
 *              and sends changed odds to backend automatically.
 *
 * Auto-capture flow:
 *   findOddsElements() → extractOddsValue() → associateSelection()
 *   → detectChanges() → autoSendOdds() → POST /api/v1/cricket/capture
 */

(function () {
  'use strict';

  if (window.__cricketArbLoaded) return;
  window.__cricketArbLoaded = true;

  const BACKEND_URL = 'http://localhost:8000';

  // ======== STATE ========

  // Manual capture state
  let capturedOdds = [];
  let panelVisible = false;
  let selectionMode = false;
  let authToken = null;

  // Auto-capture state
  let autoCaptureEnabled = false;
  let autoCaptureInterval = null;
  let autoCaptureScanMs = 7000;
  let lastOddsSnapshot = {};
  let autoSendInProgress = false;
  let mutationObserverInstance = null;
  let mutationDebounceTimer = null;
  let autoCaptureStats = {
    scansPerformed: 0,
    oddsDetected: 0,
    changesSent: 0,
    lastScanTime: null,
    lastSendTime: null,
    errors: 0,
  };

  // Rate limiter
  const RATE_LIMIT = {
    maxSendsPerMinute: 8,
    sendTimestamps: [],
  };

  // Load auth token
  chrome.storage.local.get(['cricketarb_token'], (result) => {
    authToken = result.cricketarb_token || null;
  });

  // ======== ODDS DETECTION (shared by manual + auto) ========

  const ODDS_PATTERNS = {
    decimal: /\b([1-9]\d{0,2}\.\d{1,3})\b/,
    fractional: /\b(\d{1,3})\s*\/\s*(\d{1,3})\b/,
    american_pos: /\+(\d{2,4})\b/,
    american_neg: /\-(\d{2,4})\b/,
  };

  function detectOddsFormat(text) {
    text = text.trim();

    // Fractional: 5/2
    const fracMatch = text.match(/^(\d{1,3})\s*\/\s*(\d{1,3})$/);
    if (fracMatch) {
      const num = parseInt(fracMatch[1]);
      const den = parseInt(fracMatch[2]);
      // Reject cricket scores (245/7) — real odds denominators are ≤ 20
      if (den > 0 && den <= 20 && num > 0) {
        return { format: 'fractional', original: text, decimal: (num / den) + 1 };
      }
    }

    // American: +150, -200
    const amerMatch = text.match(/^([+-]\d{2,4})$/);
    if (amerMatch) {
      const val = parseInt(amerMatch[1]);
      let decimal;
      if (val > 0) {
        decimal = (val / 100) + 1;
      } else {
        decimal = (100 / Math.abs(val)) + 1;
      }
      return { format: 'american', original: text, decimal: Math.round(decimal * 100) / 100 };
    }

    // Decimal: 1.50, 2.10
    const decMatch = text.match(/^(\d{1,3}\.\d{1,3})$/);
    if (decMatch) {
      const val = parseFloat(decMatch[1]);
      if (val >= 1.01 && val <= 1000) {
        return { format: 'decimal', original: text, decimal: val };
      }
    }

    return null;
  }

  // ======== AUTO-CAPTURE: DOM SCANNING ENGINE ========

  // CSS class keywords that betting sites commonly use for odds elements
  const ODDS_CLASS_KEYWORDS = [
    'odd', 'price', 'bet-btn', 'bet-button', 'rate', 'coefficient',
    'selection-price', 'betspot', 'market-price', 'back-price', 'lay-price',
    'odds-value', 'bet-odds', 'coupon-price', 'outcome', 'runner-price',
    'betslip', 'wager', 'stake-info', 'market-runner',
  ];

  /**
   * Strategy 1: Find elements by CSS class heuristics.
   * Most betting sites use semantic class names for odds.
   */
  function findByClassHeuristics(root) {
    const selector = ODDS_CLASS_KEYWORDS
      .map(kw => `[class*="${kw}"]`)
      .join(', ');
    try {
      return [...root.querySelectorAll(selector)];
    } catch {
      return [];
    }
  }

  /**
   * Strategy 2: Find elements by data attributes.
   * Modern SPAs use data-* attributes for odds values.
   */
  function findByDataAttributes(root) {
    const selector = [
      '[data-odds]', '[data-price]', '[data-decimal]',
      '[data-betid]', '[data-selection-id]', '[data-runner-id]',
      '[data-market]', '[data-outcome]', '[data-odd]',
    ].join(', ');
    try {
      return [...root.querySelectorAll(selector)];
    } catch {
      return [];
    }
  }

  /**
   * Strategy 3: Structural patterns — buttons/spans with odds-like text
   * inside common betting containers.
   */
  function findByStructure(root) {
    const results = [];
    // Look for buttons/spans that contain a single odds-like number
    const candidates = root.querySelectorAll('button, span, td, a, div');
    for (const el of candidates) {
      // Skip our own panel
      if (el.closest('#cricketarb-panel')) continue;
      // Skip large containers — odds are in leaf-ish elements
      if (el.children.length > 3) continue;

      const text = el.textContent.trim();
      // Quick check: must be short text that looks like a number
      if (text.length < 2 || text.length > 12) continue;
      if (ODDS_PATTERNS.decimal.test(text) || ODDS_PATTERNS.fractional.test(text) ||
          ODDS_PATTERNS.american_pos.test(text) || ODDS_PATTERNS.american_neg.test(text)) {
        results.push(el);
      }
    }
    return results;
  }

  /**
   * Strategy 4: Brute-force TreeWalker for text nodes with odds-like values.
   * Expensive — only used as fallback when other strategies find < 2 elements.
   */
  function findByTextWalker(root) {
    const results = [];
    const walker = document.createTreeWalker(
      root, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => {
          if (node.parentElement && node.parentElement.closest('#cricketarb-panel')) {
            return NodeFilter.FILTER_REJECT;
          }
          const text = node.textContent.trim();
          if (text.length >= 2 && text.length <= 12 && ODDS_PATTERNS.decimal.test(text)) {
            return NodeFilter.FILTER_ACCEPT;
          }
          return NodeFilter.FILTER_REJECT;
        }
      }
    );
    let count = 0;
    while (walker.nextNode() && count < 200) {
      results.push(walker.currentNode.parentElement);
      count++;
    }
    return results;
  }

  /**
   * Main DOM scanner: tries strategies in order, de-duplicates results.
   */
  function findOddsElements() {
    const seen = new Set();
    const results = [];

    function addUnique(elements) {
      for (const el of elements) {
        if (!el || seen.has(el)) continue;
        if (el.closest('#cricketarb-panel')) continue;
        seen.add(el);
        results.push(el);
      }
    }

    // Try strategies 1-3 first
    addUnique(findByClassHeuristics(document.body));
    addUnique(findByDataAttributes(document.body));

    // Strategy 3 only if we haven't found enough
    if (results.length < 4) {
      addUnique(findByStructure(document.body));
    }

    // Strategy 4 only as last resort
    if (results.length < 2) {
      addUnique(findByTextWalker(document.body));
    }

    // Also scan same-origin iframes
    const iframes = document.querySelectorAll('iframe');
    for (const iframe of iframes) {
      try {
        const doc = iframe.contentDocument;
        if (doc && doc.body) {
          addUnique(findByClassHeuristics(doc.body));
          addUnique(findByDataAttributes(doc.body));
        }
      } catch {
        // Cross-origin iframe — cannot access
      }
    }

    return results;
  }

  /**
   * Extract odds value from a DOM element.
   * Checks data attributes first (most reliable), then text content.
   * Returns { format, original, decimal } or null.
   */
  function extractOddsValue(element) {
    // Check data attributes first
    const dataOdds = element.getAttribute('data-odds') ||
                     element.getAttribute('data-price') ||
                     element.getAttribute('data-decimal') ||
                     element.getAttribute('data-odd');
    if (dataOdds) {
      const val = parseFloat(dataOdds);
      if (val >= 1.01 && val <= 1000) {
        return { format: 'decimal', original: dataOdds, decimal: val };
      }
    }

    // Try text content
    const text = element.textContent.trim();
    if (text.length < 1 || text.length > 15) return null;

    // Reject date-like patterns: 12/03, 2025-01-15
    if (/^\d{1,2}[\/\-]\d{1,2}([\/\-]\d{2,4})?$/.test(text)) return null;
    // Reject time-like: 14:30, 2:15 PM
    if (/^\d{1,2}:\d{2}/.test(text)) return null;
    // Reject percentage: 45%, 12.5%
    if (/%/.test(text)) return null;

    return detectOddsFormat(text);
  }

  /**
   * Associate a team/selection name with an odds element by walking the DOM.
   */
  function associateSelection(oddsElement) {
    // Strategy 1: aria-label or data attributes on the element or parents
    const ariaLabel = oddsElement.getAttribute('aria-label');
    if (ariaLabel && ariaLabel.length > 1 && ariaLabel.length < 60) {
      // Extract team name from labels like "India - 2.50"
      const cleaned = ariaLabel.replace(/[\d.\/+-]+/g, '').trim();
      if (cleaned.length > 1) return cleaned;
    }

    const dataSelection = oddsElement.closest('[data-selection]');
    if (dataSelection) {
      const name = dataSelection.getAttribute('data-selection');
      if (name && name.length > 1) return name;
    }

    const dataRunner = oddsElement.closest('[data-runner-name]');
    if (dataRunner) {
      const name = dataRunner.getAttribute('data-runner-name');
      if (name && name.length > 1) return name;
    }

    // Strategy 2: Same-row association (tables, lists)
    const row = oddsElement.closest('tr, li, [role="row"]');
    if (row) {
      const cells = row.querySelectorAll('td, th, span, div, a');
      for (const cell of cells) {
        if (cell === oddsElement || cell.contains(oddsElement)) continue;
        const text = cell.textContent.trim();
        if (text.length > 1 && text.length < 60 && !/^[\d.\/+\-]+$/.test(text) && !/^\d{1,2}:\d{2}/.test(text)) {
          // Prefer cells with team/name-related classes
          const cls = (cell.className || '').toLowerCase();
          if (cls.includes('team') || cls.includes('name') || cls.includes('participant') ||
              cls.includes('runner') || cls.includes('selection') || cls.includes('event')) {
            return text;
          }
        }
      }
      // Fallback: first non-numeric text in the row
      for (const cell of cells) {
        if (cell === oddsElement || cell.contains(oddsElement)) continue;
        const text = cell.textContent.trim();
        if (text.length > 1 && text.length < 60 && !/^[\d.\/+\-]+$/.test(text)) {
          return text;
        }
      }
    }

    // Strategy 3: Walk up parent tree (max 5 levels)
    let parent = oddsElement.parentElement;
    for (let i = 0; i < 5 && parent; i++) {
      const siblings = parent.children;
      for (const sib of siblings) {
        if (sib === oddsElement || sib.contains(oddsElement)) continue;
        const text = sib.textContent.trim();
        if (text.length > 1 && text.length < 60 && !/^[\d.\/+\-]+$/.test(text) && !/^\d{1,2}:\d{2}/.test(text)) {
          const cls = (sib.className || '').toLowerCase();
          if (cls.includes('team') || cls.includes('name') || cls.includes('participant') ||
              cls.includes('runner') || cls.includes('selection')) {
            return text;
          }
        }
      }
      // Try first non-numeric sibling text
      for (const sib of siblings) {
        if (sib === oddsElement || sib.contains(oddsElement)) continue;
        const text = sib.textContent.trim();
        if (text.length > 1 && text.length < 50 && !/^[\d.\/+\-]+$/.test(text)) {
          return text;
        }
      }
      parent = parent.parentElement;
    }

    // Strategy 4: Match against user-provided team names
    const teamA = document.getElementById('cab-team-a')?.value?.trim();
    const teamB = document.getElementById('cab-team-b')?.value?.trim();
    if (teamA || teamB) {
      // Check if any ancestor text contains team A or team B
      const ancestorText = (oddsElement.closest('div, section, article') || document.body).textContent;
      if (teamA && ancestorText.includes(teamA)) return teamA;
      if (teamB && ancestorText.includes(teamB)) return teamB;
    }

    return 'Unknown';
  }

  /**
   * Main scan orchestrator: finds odds elements, extracts values, associates selections.
   * Returns array of { selection, odds_decimal, odds_original, odds_format, element }.
   */
  function scanPageForOdds() {
    const elements = findOddsElements();
    const results = [];
    const seenValues = new Set(); // De-dup by selection+odds

    for (const el of elements) {
      const parsed = extractOddsValue(el);
      if (!parsed) continue;

      const selection = associateSelection(el);
      const key = `${selection}::${parsed.decimal}`;
      if (seenValues.has(key)) continue;
      seenValues.add(key);

      results.push({
        selection,
        odds_decimal: parsed.decimal,
        odds_original: parsed.original,
        odds_format: parsed.format,
        element: el,
      });
    }

    return results;
  }

  /**
   * Compare current scan with last snapshot. Return only changed items.
   */
  function detectChanges(currentOdds) {
    const changed = [];
    const newSnapshot = {};

    for (const item of currentOdds) {
      const key = `${item.selection}::${item.odds_format}`;
      newSnapshot[key] = item.odds_decimal;

      const prev = lastOddsSnapshot[key];
      if (prev === undefined || Math.abs(prev - item.odds_decimal) > 0.001) {
        changed.push(item);
      }
    }

    lastOddsSnapshot = newSnapshot;
    return changed;
  }

  // ======== AUTO-CAPTURE CONTROLLER ========

  function isRateLimited() {
    const now = Date.now();
    RATE_LIMIT.sendTimestamps = RATE_LIMIT.sendTimestamps.filter(t => now - t < 60000);
    if (RATE_LIMIT.sendTimestamps.length >= RATE_LIMIT.maxSendsPerMinute) {
      return true;
    }
    RATE_LIMIT.sendTimestamps.push(now);
    return false;
  }

  function startAutoCapture() {
    const teamA = document.getElementById('cab-team-a')?.value?.trim();
    const teamB = document.getElementById('cab-team-b')?.value?.trim();
    const bookmaker = document.getElementById('cab-bookmaker')?.value?.trim();

    if (!teamA || !teamB) {
      showStatus('Enter Team A and Team B first', 'error');
      return false;
    }
    if (!bookmaker) {
      showStatus('Enter bookmaker name', 'error');
      return false;
    }
    if (!authToken) {
      showStatus('Set JWT token in extension popup first', 'error');
      return false;
    }

    autoCaptureEnabled = true;
    lastOddsSnapshot = {};
    autoCaptureStats = { scansPerformed: 0, oddsDetected: 0, changesSent: 0, lastScanTime: null, lastSendTime: null, errors: 0 };

    // Start periodic scanning
    autoCaptureInterval = setInterval(runAutoScan, autoCaptureScanMs);

    // Start MutationObserver for instant detection
    startMutationObserver();

    // Notify background to keep service worker alive
    try {
      chrome.runtime.sendMessage({ action: 'auto_capture_started' });
    } catch { /* background might not be ready */ }

    // Update UI
    const btn = document.getElementById('cab-auto-capture');
    if (btn) {
      btn.textContent = 'Stop';
      btn.classList.add('cab-active');
    }
    const section = document.getElementById('cab-auto-section');
    if (section) section.style.display = 'block';

    updateAutoStatus('active', 'Auto-capture started. Scanning...');
    showStatus('Auto-capture ON — scanning every ' + (autoCaptureScanMs / 1000) + 's', 'success');

    // Run first scan immediately
    runAutoScan();
    return true;
  }

  function stopAutoCapture() {
    autoCaptureEnabled = false;

    if (autoCaptureInterval) {
      clearInterval(autoCaptureInterval);
      autoCaptureInterval = null;
    }
    if (mutationObserverInstance) {
      mutationObserverInstance.disconnect();
      mutationObserverInstance = null;
    }
    if (mutationDebounceTimer) {
      clearTimeout(mutationDebounceTimer);
      mutationDebounceTimer = null;
    }

    try {
      chrome.runtime.sendMessage({ action: 'auto_capture_stopped' });
    } catch { /* ok */ }

    const btn = document.getElementById('cab-auto-capture');
    if (btn) {
      btn.textContent = 'Auto';
      btn.classList.remove('cab-active');
    }

    updateAutoStatus('idle', 'Stopped');
    showStatus('Auto-capture OFF', 'info');
  }

  function toggleAutoCapture() {
    if (autoCaptureEnabled) {
      stopAutoCapture();
    } else {
      startAutoCapture();
    }
  }

  /**
   * The heartbeat function — called every N seconds and by MutationObserver.
   */
  async function runAutoScan() {
    if (!autoCaptureEnabled || autoSendInProgress) return;

    autoCaptureStats.scansPerformed++;
    autoCaptureStats.lastScanTime = new Date();

    try {
      // 1. Scan the page
      const scannedOdds = scanPageForOdds();
      autoCaptureStats.oddsDetected = scannedOdds.length;

      // Update preview list
      updateAutoOddsList(scannedOdds);

      if (scannedOdds.length === 0) {
        updateAutoStatus('scanning', 'No odds found on page');
        updateAutoStatsDisplay();
        return;
      }

      // 2. Detect changes
      const changedOdds = detectChanges(scannedOdds);

      if (changedOdds.length === 0) {
        updateAutoStatus('active', `${scannedOdds.length} odds tracked, no changes`);
        updateAutoStatsDisplay();
        return;
      }

      // 3. Rate limit check
      if (isRateLimited()) {
        updateAutoStatus('scanning', 'Rate limited, waiting...');
        updateAutoStatsDisplay();
        return;
      }

      // 4. Send changed odds
      updateAutoStatus('sending', `Sending ${changedOdds.length} changed odds...`);
      await autoSendOdds(changedOdds);

      autoCaptureStats.changesSent++;
      autoCaptureStats.lastSendTime = new Date();
      updateAutoStatus('active', `Sent ${changedOdds.length} odds @ ${new Date().toLocaleTimeString()}`);

    } catch (err) {
      autoCaptureStats.errors++;
      updateAutoStatus('error', `Error: ${err.message}`);
    }

    updateAutoStatsDisplay();
  }

  /**
   * Send auto-captured odds to backend.
   */
  async function autoSendOdds(oddsItems) {
    autoSendInProgress = true;

    const teamA = document.getElementById('cab-team-a').value.trim();
    const teamB = document.getElementById('cab-team-b').value.trim();
    const bookmaker = document.getElementById('cab-bookmaker').value.trim();
    const market = document.getElementById('cab-market').value;

    const payload = {
      match_team_a: teamA,
      match_team_b: teamB,
      bookmaker: bookmaker,
      market_type: market,
      source_url: window.location.href,
      odds: oddsItems.map(o => ({
        selection: o.selection,
        odds_decimal: o.odds_decimal,
        odds_original: o.odds_original,
        odds_format: o.odds_format,
        is_back: true,
        is_live: true,
      })),
    };

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

      const resp = await fetch(`${BACKEND_URL}/api/v1/cricket/capture`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        if (resp.status === 401) {
          stopAutoCapture();
          showStatus('Auth failed. Set token in extension popup.', 'error');
        }
        throw new Error(`HTTP ${resp.status}`);
      }
    } finally {
      autoSendInProgress = false;
    }
  }

  // ======== MUTATION OBSERVER ========

  function startMutationObserver() {
    if (mutationObserverInstance) {
      mutationObserverInstance.disconnect();
    }

    mutationObserverInstance = new MutationObserver((mutations) => {
      if (!autoCaptureEnabled || autoSendInProgress) return;

      // Check if any mutation is potentially odds-related
      const isRelevant = mutations.some(m => {
        for (const node of m.addedNodes) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const text = node.textContent || '';
            if (text.length < 200 && ODDS_PATTERNS.decimal.test(text)) return true;
          }
        }
        if (m.type === 'characterData') {
          const text = (m.target.textContent || '').trim();
          if (text.length < 15 && ODDS_PATTERNS.decimal.test(text)) return true;
        }
        if (m.target && m.target.className && typeof m.target.className === 'string') {
          const cls = m.target.className.toLowerCase();
          if (ODDS_CLASS_KEYWORDS.some(kw => cls.includes(kw))) return true;
        }
        return false;
      });

      if (isRelevant && !mutationDebounceTimer) {
        mutationDebounceTimer = setTimeout(() => {
          mutationDebounceTimer = null;
          if (autoCaptureEnabled && !autoSendInProgress) {
            runAutoScan();
          }
        }, 2000);
      }
    });

    mutationObserverInstance.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  // ======== AUTO-CAPTURE UI UPDATES ========

  function updateAutoStatus(state, text) {
    const indicator = document.getElementById('cab-auto-indicator');
    const statusText = document.getElementById('cab-auto-status-text');
    if (!indicator || !statusText) return;

    indicator.className = 'cab-auto-indicator';
    switch (state) {
      case 'active':
      case 'sending':
        indicator.classList.add('active');
        break;
      case 'scanning':
        indicator.classList.add('scanning');
        break;
      case 'error':
        indicator.classList.add('error');
        break;
      default:
        indicator.classList.add('idle');
    }
    statusText.textContent = text;
  }

  function updateAutoStatsDisplay() {
    const el = document.getElementById('cab-auto-stats');
    if (!el) return;
    el.textContent =
      `Scans: ${autoCaptureStats.scansPerformed} | ` +
      `Detected: ${autoCaptureStats.oddsDetected} | ` +
      `Sent: ${autoCaptureStats.changesSent} | ` +
      `Errors: ${autoCaptureStats.errors}`;
  }

  function updateAutoOddsList(oddsItems) {
    const el = document.getElementById('cab-auto-odds-list');
    if (!el) return;

    if (oddsItems.length === 0) {
      el.innerHTML = '<div style="color:#666;font-size:11px;text-align:center;padding:4px;">No odds detected</div>';
      return;
    }

    el.innerHTML = oddsItems.slice(0, 20).map(o => `
      <div class="cab-auto-odds-item">
        <span class="selection">${o.selection}</span>
        <span class="value">${o.odds_decimal}</span>
      </div>
    `).join('');
  }

  // ======== FLOATING PANEL UI ========

  function createPanel() {
    const panel = document.createElement('div');
    panel.id = 'cricketarb-panel';
    panel.innerHTML = `
      <div class="cab-header">
        <span class="cab-logo">CricketArb</span>
        <div class="cab-header-btns">
          <button id="cab-auto-capture" title="Auto-detect and send odds every few seconds">Auto</button>
          <button id="cab-select-mode" title="Click to select odds on page">Select</button>
          <button id="cab-minimize" title="Minimize">_</button>
          <button id="cab-close" title="Close">X</button>
        </div>
      </div>
      <div class="cab-body">
        <div class="cab-match-info">
          <input type="text" id="cab-team-a" placeholder="Team A (e.g. India)" />
          <span class="cab-vs">vs</span>
          <input type="text" id="cab-team-b" placeholder="Team B (e.g. Australia)" />
          <input type="text" id="cab-bookmaker" placeholder="Bookmaker" value="${guessBookmaker()}" />
          <select id="cab-market">
            <option value="match_winner">Match Winner</option>
            <option value="total_runs">Total Runs O/U</option>
            <option value="team_runs">Team Runs</option>
            <option value="top_batsman">Top Batsman</option>
            <option value="session_runs">Session Runs</option>
          </select>
        </div>

        <!-- Auto-capture section (hidden until Auto is clicked) -->
        <div class="cab-auto-section" id="cab-auto-section" style="display:none;">
          <div class="cab-auto-header">
            <span class="cab-auto-indicator idle" id="cab-auto-indicator"></span>
            <span id="cab-auto-status-text">Idle</span>
            <select id="cab-scan-interval" title="Scan interval">
              <option value="5000">5s</option>
              <option value="7000" selected>7s</option>
              <option value="10000">10s</option>
              <option value="15000">15s</option>
            </select>
          </div>
          <div class="cab-auto-stats" id="cab-auto-stats">
            Scans: 0 | Detected: 0 | Sent: 0 | Errors: 0
          </div>
          <div class="cab-auto-odds" id="cab-auto-odds-list"></div>
        </div>

        <!-- Manual capture section -->
        <div class="cab-odds-list" id="cab-odds-list">
          <p class="cab-hint">Click "Select" to pick odds on page, or "Auto" to scan automatically</p>
        </div>
        <div class="cab-manual-entry">
          <input type="text" id="cab-selection" placeholder="Selection (e.g. India)" />
          <input type="text" id="cab-odds-input" placeholder="Odds (e.g. 2.10)" />
          <label><input type="checkbox" id="cab-is-live" /> Live</label>
          <button id="cab-add-odds">+ Add</button>
        </div>
        <div class="cab-actions">
          <button id="cab-send" class="cab-btn-send" disabled>Send to CricketArb (0 odds)</button>
          <button id="cab-clear" class="cab-btn-clear">Clear</button>
        </div>
        <div id="cab-status" class="cab-status"></div>
      </div>
    `;
    document.body.appendChild(panel);

    makeDraggable(panel, panel.querySelector('.cab-header'));

    // Event listeners
    document.getElementById('cab-auto-capture').addEventListener('click', toggleAutoCapture);
    document.getElementById('cab-select-mode').addEventListener('click', toggleSelectionMode);
    document.getElementById('cab-minimize').addEventListener('click', minimizePanel);
    document.getElementById('cab-close').addEventListener('click', closePanel);
    document.getElementById('cab-add-odds').addEventListener('click', addManualOdds);
    document.getElementById('cab-send').addEventListener('click', sendOdds);
    document.getElementById('cab-clear').addEventListener('click', clearOdds);

    document.getElementById('cab-odds-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') addManualOdds();
    });

    document.getElementById('cab-scan-interval').addEventListener('change', (e) => {
      autoCaptureScanMs = parseInt(e.target.value);
      if (autoCaptureEnabled && autoCaptureInterval) {
        clearInterval(autoCaptureInterval);
        autoCaptureInterval = setInterval(runAutoScan, autoCaptureScanMs);
        showStatus('Scan interval changed to ' + (autoCaptureScanMs / 1000) + 's', 'info');
      }
    });

    return panel;
  }

  function guessBookmaker() {
    const host = window.location.hostname.toLowerCase();
    const bookmakerMap = {
      'bet365': 'bet365', 'betfair': 'betfair', 'pinnacle': 'pinnacle',
      '1xbet': '1xbet', 'betway': 'betway', 'dream11': 'dream11',
      'parimatch': 'parimatch', 'mostbet': 'mostbet', 'fairplay': 'fairplay',
      'lotus365': 'lotus365', 'betwinners': 'betwinners', 'dafabet': 'dafabet',
      'unibet': 'unibet', 'williamhill': 'william_hill', 'ladbrokes': 'ladbrokes',
      'paddypower': 'paddypower', 'sportsbet': 'sportsbet', 'bwin': 'bwin',
      'marathon': 'marathonbet', '10cric': '10cric', 'fun88': 'fun88',
      '22bet': '22bet', 'melbet': 'melbet', 'rajabets': 'rajabets',
      'betwinner': 'betwinner', 'stake': 'stake', 'betmgm': 'betmgm',
    };
    for (const [key, name] of Object.entries(bookmakerMap)) {
      if (host.includes(key)) return name;
    }
    return '';
  }

  function makeDraggable(element, handle) {
    let offsetX, offsetY, isDragging = false;
    handle.addEventListener('mousedown', (e) => {
      if (e.target.tagName === 'BUTTON' || e.target.tagName === 'SELECT') return;
      isDragging = true;
      offsetX = e.clientX - element.getBoundingClientRect().left;
      offsetY = e.clientY - element.getBoundingClientRect().top;
      handle.style.cursor = 'grabbing';
    });
    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      element.style.left = (e.clientX - offsetX) + 'px';
      element.style.top = (e.clientY - offsetY) + 'px';
      element.style.right = 'auto';
      element.style.bottom = 'auto';
    });
    document.addEventListener('mouseup', () => {
      isDragging = false;
      handle.style.cursor = 'grab';
    });
  }

  // ======== MANUAL SELECTION MODE ========

  function toggleSelectionMode() {
    selectionMode = !selectionMode;
    const btn = document.getElementById('cab-select-mode');

    if (selectionMode) {
      btn.textContent = 'Stop';
      btn.classList.add('cab-active');
      document.body.classList.add('cricketarb-selecting');
      showStatus('Click any odds value on the page to capture it', 'info');
    } else {
      btn.textContent = 'Select';
      btn.classList.remove('cab-active');
      document.body.classList.remove('cricketarb-selecting');
      document.querySelectorAll('.cab-highlight').forEach(el => el.classList.remove('cab-highlight'));
    }
  }

  document.addEventListener('click', (e) => {
    if (!selectionMode) return;
    if (e.target.closest('#cricketarb-panel')) return;

    e.preventDefault();
    e.stopPropagation();

    const text = e.target.textContent.trim();
    const parsed = detectOddsFormat(text);

    if (parsed) {
      const selectionName = guessSelection(e.target);
      capturedOdds.push({
        selection: selectionName,
        odds_decimal: parsed.decimal,
        odds_original: parsed.original,
        odds_format: parsed.format,
        is_back: true,
        is_live: document.getElementById('cab-is-live')?.checked || false,
      });
      e.target.classList.add('cab-captured');
      updateOddsList();
      showStatus(`Captured: ${selectionName} @ ${parsed.decimal}`, 'success');
    } else {
      showStatus(`"${text}" doesn't look like odds`, 'error');
    }
  }, true);

  function guessSelection(element) {
    const parent = element.parentElement;
    if (!parent) return 'Unknown';

    const siblings = parent.children;
    for (const sib of siblings) {
      if (sib === element) continue;
      const text = sib.textContent.trim();
      if (text.length > 1 && text.length < 50 && !/^\d/.test(text)) {
        return text;
      }
    }

    const prev = parent.previousElementSibling;
    if (prev) {
      const text = prev.textContent.trim();
      if (text.length > 1 && text.length < 50) return text;
    }

    return 'Unknown';
  }

  // ======== MANUAL ENTRY ========

  function addManualOdds() {
    const selectionInput = document.getElementById('cab-selection');
    const oddsInput = document.getElementById('cab-odds-input');

    const selection = selectionInput.value.trim();
    const oddsRaw = oddsInput.value.trim();

    if (!selection || !oddsRaw) {
      showStatus('Enter both selection name and odds', 'error');
      return;
    }

    const parsed = detectOddsFormat(oddsRaw);
    if (!parsed) {
      showStatus(`"${oddsRaw}" is not valid odds. Use: 2.10, 5/2, or +150`, 'error');
      return;
    }

    capturedOdds.push({
      selection: selection,
      odds_decimal: parsed.decimal,
      odds_original: parsed.original,
      odds_format: parsed.format,
      is_back: true,
      is_live: document.getElementById('cab-is-live')?.checked || false,
    });

    selectionInput.value = '';
    oddsInput.value = '';
    selectionInput.focus();
    updateOddsList();
    showStatus(`Added: ${selection} @ ${parsed.decimal}`, 'success');
  }

  // ======== MANUAL ODDS LIST ========

  function updateOddsList() {
    const list = document.getElementById('cab-odds-list');
    const sendBtn = document.getElementById('cab-send');

    if (capturedOdds.length === 0) {
      list.innerHTML = '<p class="cab-hint">Click "Select" to pick odds on page, or "Auto" to scan automatically</p>';
      sendBtn.textContent = 'Send to CricketArb (0 odds)';
      sendBtn.disabled = true;
      return;
    }

    list.innerHTML = capturedOdds.map((o, i) => `
      <div class="cab-odds-item">
        <span class="cab-odds-selection">${o.selection}</span>
        <span class="cab-odds-value">${o.odds_decimal} <small>(${o.odds_format})</small></span>
        <button class="cab-remove" data-index="${i}">x</button>
      </div>
    `).join('');

    list.querySelectorAll('.cab-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        capturedOdds.splice(parseInt(btn.dataset.index), 1);
        updateOddsList();
      });
    });

    sendBtn.textContent = `Send to CricketArb (${capturedOdds.length} odds)`;
    sendBtn.disabled = false;
  }

  // ======== MANUAL SEND ========

  async function sendOdds() {
    const teamA = document.getElementById('cab-team-a').value.trim();
    const teamB = document.getElementById('cab-team-b').value.trim();
    const bookmaker = document.getElementById('cab-bookmaker').value.trim();
    const market = document.getElementById('cab-market').value;

    if (!teamA || !teamB) { showStatus('Enter both team names', 'error'); return; }
    if (!bookmaker) { showStatus('Enter bookmaker name', 'error'); return; }
    if (capturedOdds.length === 0) { showStatus('No odds captured', 'error'); return; }

    const payload = {
      match_team_a: teamA,
      match_team_b: teamB,
      bookmaker: bookmaker,
      market_type: market,
      source_url: window.location.href,
      odds: capturedOdds.map(o => ({
        selection: o.selection,
        odds_decimal: o.odds_decimal,
        odds_original: o.odds_original,
        odds_format: o.odds_format,
        is_back: o.is_back,
        is_live: o.is_live,
      })),
    };

    const sendBtn = document.getElementById('cab-send');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

      const resp = await fetch(`${BACKEND_URL}/api/v1/cricket/capture`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (resp.ok) {
        const data = await resp.json();
        showStatus(
          `Sent ${capturedOdds.length} odds! ${data.arbs_found ? `ARB DETECTED: ${data.arbs_found}!` : 'Checking...'}`,
          data.arbs_found ? 'arb' : 'success'
        );
        capturedOdds = [];
        updateOddsList();
      } else if (resp.status === 401) {
        showStatus('Not logged in. Set token in extension popup.', 'error');
      } else {
        const err = await resp.text();
        showStatus(`Error: ${err}`, 'error');
      }
    } catch (e) {
      showStatus(`Cannot reach backend at ${BACKEND_URL}. Is it running?`, 'error');
    }

    sendBtn.disabled = capturedOdds.length === 0;
    sendBtn.textContent = `Send to CricketArb (${capturedOdds.length} odds)`;
  }

  // ======== HELPERS ========

  function showStatus(msg, type) {
    const el = document.getElementById('cab-status');
    if (!el) return;
    el.textContent = msg;
    el.className = `cab-status cab-status-${type}`;
    if (type !== 'error') {
      setTimeout(() => { el.textContent = ''; el.className = 'cab-status'; }, 4000);
    }
  }

  function minimizePanel() {
    const body = document.querySelector('.cab-body');
    body.style.display = body.style.display === 'none' ? 'block' : 'none';
  }

  function closePanel() {
    if (autoCaptureEnabled) stopAutoCapture();
    const panel = document.getElementById('cricketarb-panel');
    if (panel) panel.remove();
    panelVisible = false;
    selectionMode = false;
    document.body.classList.remove('cricketarb-selecting');
  }

  function clearOdds() {
    capturedOdds = [];
    updateOddsList();
    document.querySelectorAll('.cab-captured').forEach(el => el.classList.remove('cab-captured'));
  }

  // ======== MESSAGE LISTENER ========

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'toggle_panel') {
      if (panelVisible) {
        closePanel();
      } else {
        createPanel();
        panelVisible = true;
      }
    }
    if (msg.action === 'set_token') {
      authToken = msg.token;
      chrome.storage.local.set({ cricketarb_token: msg.token });
    }
    if (msg.action === 'ping') {
      sendResponse({ alive: true, autoCaptureEnabled });
    }
    if (msg.action === 'get_auto_status') {
      sendResponse({
        autoCaptureEnabled,
        oddsDetected: autoCaptureStats.oddsDetected,
        changesSent: autoCaptureStats.changesSent,
        scansPerformed: autoCaptureStats.scansPerformed,
      });
    }
    return true; // Keep message channel open for async sendResponse
  });

})();
