// Immediately check active tab when extension starts
chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("checkActiveTab", { periodInMinutes: 1 });
  chrome.alarms.get("checkActiveTab", (alarm) => {
    if (alarm) {
      // Manually trigger the alarm handler
      chrome.alarms.onAlarm.dispatch({ name: "checkActiveTab" });
    }
  });
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("checkActiveTab", { periodInMinutes: 1 });
  chrome.alarms.get("checkActiveTab", (alarm) => {
    if (alarm) {
      chrome.alarms.onAlarm.dispatch({ name: "checkActiveTab" });
    }
  });
});

// Called when Chrome starts up (e.g. after reboot)
chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("checkActiveTab", {
    periodInMinutes: 1
  });
});

// Helper function to check if server is available
async function isServerAvailable() {
  try {
    const response = await fetch("http://localhost:5000/get_block_status", {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      },
      // Adding a timeout of 2 seconds
      signal: AbortSignal.timeout(2000)
    });
    return response.ok;
  } catch (error) {
    console.log("Server check failed:", error.message);
    return false;
  }
}

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "checkActiveTab") return;

  // 1) Is user active?
  const state = await chrome.idle.queryState(300);  // idle if no input for ≥5min
  if (state !== "active") return;

  // 2) Is Chrome focused?
  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true
  });
  if (!tab || !tab.url) return;
  const domani = new URL(tab.url).hostname;
  const timestamp = new Date().toISOString(); // current time in ISO format

  // Check if server is available before making requests
  const serverAvailable = await isServerAvailable();
  
  if (serverAvailable) {
    try {
      const logResponse = await fetch("http://localhost:5000/log_time", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          domain: domani,
          seconds: 60,
          timestamp: timestamp
        })
      });
      
      if (logResponse.ok) {
        console.log("Data 60 sec to python of:", domani);
      } else {
        console.error("Server returned error:", await logResponse.text());
      }
    } catch (error) {
      console.error("Error sending data to server:", error.message);
    }
    
    try {
      const res = await fetch("http://localhost:5000/get_block_status");
      if (res.ok) {
        const data = await res.json();
        await updateBlockRules(data);
      } else {
        console.error("Error getting block status:", await res.text());
        // Fall back to zero productivity mode if server responds but with error
        applyZeroProductivityRules();
      }
    } catch (error) {
      console.error("Error getting block status:", error.message);
      // Fall back to zero productivity mode if server doesn't respond
      applyZeroProductivityRules();
    }
  } else {
    console.log("Server unavailable - applying default blocking rules");
    // Apply default blocking rules when server is down
    applyZeroProductivityRules();
  }
});

async function updateBlockRules(data) {
  const allRuleIds = [1, 2, 3, 4, 5, 6]; // Only include IDs that exist in rules.json
  const alwaysAllowIds = [6, 1];
  const zeroProductivityIds = [6, 5,1];
  const ruletorev = data.unblock_rule_ids || [];

  try {
    const rulesRes = await fetch("rules.json");
    const allRules = await rulesRes.json();

    if (ruletorev.length === 0) {async function updateBlockRules(data) {
  const allRuleIds = [1, 2, 3, 4, 5, 6]; // Only include IDs that exist in rules.json
  const alwaysAllowIds = [6, 1];
  const zeroProductivityIds = [6,1,5];
  const ruletorev = data.unblock_rule_ids || [];

  try {
    const rulesRes = await fetch("rules.json");
    const allRules = await rulesRes.json();

    if (ruletorev.length === 0) {
      console.log("zero productivity or close to that");
      const rulesToAddForZeroProductivity = allRules.filter(rule => zeroProductivityIds.includes(rule.id));
      await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: allRuleIds,
        addRules: rulesToAddForZeroProductivity
      });
    } else {
      console.log("not zero productivity");
      const rulesToAdd = allRules.filter(rule => !ruletorev.includes(rule.id) || alwaysAllowIds.includes(rule.id));
      await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: allRuleIds,
        addRules: rulesToAdd
      });
    }
  } catch (error) {
    console.error("Error updating blocking rules:", error);
  }
}
      console.log("zero productivity or close to that");
      const rulesToAddForZeroProductivity = allRules.filter(rule => zeroProductivityIds.includes(rule.id));
      await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: allRuleIds,
        addRules: rulesToAddForZeroProductivity
      });
    } else {
      console.log("not zero productivity");
      const rulesToAdd = allRules.filter(rule => ruletorev.includes(rule.id) || alwaysAllowIds.includes(rule.id));
      await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: allRuleIds,
        addRules: rulesToAdd
      });
    }
  } catch (error) {
    console.error("Error updating blocking rules:", error);
  }
}


async function applyZeroProductivityRules() {
  try {
    const rulesRes = await fetch("rules.json");
    const allRules = await rulesRes.json();
    const allRuleIds = [1, 2, 3, 4, 5, 6];
    const zeroProductivityIds = [6, 5,1];
    
    const rulesToAddForZeroProductivity = allRules.filter(rule => zeroProductivityIds.includes(rule.id));
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: allRules.filter(rule => allRuleIds.includes(rule.id)).map(rule => rule.id),
      addRules: rulesToAddForZeroProductivity
    });
  } catch (error) {
    console.error("Error applying zero productivity rules:", error);
  }
}