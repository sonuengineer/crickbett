/**
 * CricketArb Extension Background Service Worker
 *
 * Handles:
 * - Extension icon click → toggles capture panel
 * - Keep-alive alarm while auto-capture is running
 * - Token management
 */

chrome.action.onClicked.addListener(async (tab) => {
  try {
    await chrome.tabs.sendMessage(tab.id, { action: 'toggle_panel' });
  } catch (e) {
    console.log('Content script not ready, clicking popup instead');
  }
});

// Keep service worker alive while auto-capture is running
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'cricketarb-keepalive') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'ping' }).catch(() => {});
      }
    });
  }
});

// Listen for auto-capture state changes from content script
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'auto_capture_started') {
    chrome.alarms.create('cricketarb-keepalive', { periodInMinutes: 0.4 }); // Every 24s
  }
  if (msg.action === 'auto_capture_stopped') {
    chrome.alarms.clear('cricketarb-keepalive');
  }
});
