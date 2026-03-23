let isRecording = false;

// Listen for start/stop from popup
chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === "START") {
        isRecording = true;
        console.log("✅ Recording started");
    }

    if (msg.action === "STOP") {
        isRecording = false;
        console.log("🛑 Recording stopped");
    }
});

// Capture clicks
document.addEventListener("click", function (e) {
    if (!isRecording) return;

    const el = e.target;

    const text =
        el.innerText ||
        el.getAttribute("aria-label") ||
        el.placeholder ||
        el.name ||
        el.id ||
        "button";

    const step = {
        type: "click",
        text: text.trim()
    };

    // 🔥 IMPORTANT: send for screenshot capture
    chrome.runtime.sendMessage({
        action: "CAPTURE_SCREENSHOT",
        step: step
    });
});

// Capture inputs
document.addEventListener("change", function (e) {
    if (!isRecording) return;

    const el = e.target;

    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        const step = {
            type: "input",
            field: el.name || el.id,
            value: el.type === "password" ? "****" : el.value
        };

        chrome.runtime.sendMessage({ action: "RECORD", data: step });
    }
});