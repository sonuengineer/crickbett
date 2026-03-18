document.addEventListener('DOMContentLoaded', () => {
  const tokenInput = document.getElementById('token');
  const status = document.getElementById('status');

  // Load saved token
  chrome.storage.local.get(['cricketarb_token'], (result) => {
    if (result.cricketarb_token) {
      tokenInput.value = result.cricketarb_token;
      status.textContent = 'Token saved';
      status.className = 'status status-ok';
    }
  });

  // Save token
  document.getElementById('save-token').addEventListener('click', () => {
    const token = tokenInput.value.trim();
    if (!token) {
      status.textContent = 'Enter a token first';
      status.className = 'status status-err';
      return;
    }
    chrome.storage.local.set({ cricketarb_token: token }, () => {
      status.textContent = 'Token saved!';
      status.className = 'status status-ok';

      // Send to active tab's content script
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, { action: 'set_token', token });
        }
      });
    });
  });

  // Open capture panel
  document.getElementById('open-panel').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'toggle_panel' });
        window.close();
      }
    });
  });

  // Check auto-capture status on popup open
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'get_auto_status' }, (response) => {
        const el = document.getElementById('auto-status');
        if (chrome.runtime.lastError || !response) {
          el.textContent = 'Panel not open on this page';
          return;
        }
        if (response.autoCaptureEnabled) {
          el.textContent = `Active: ${response.oddsDetected} odds tracked, ${response.changesSent} updates sent`;
          el.style.color = '#00d4aa';
        } else {
          el.textContent = `Inactive (${response.scansPerformed > 0 ? 'was running' : 'not started'})`;
        }
      });
    }
  });
});
