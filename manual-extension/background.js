let steps = [];

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

    if (msg.action === "CAPTURE_SCREENSHOT") {

        // ✅ COMPRESS IMAGE HERE
        chrome.tabs.captureVisibleTab(null, {
            format: "jpeg",   // 🔥 change from PNG → JPEG
            quality: 50       // 🔥 compress (0–100)
        }, function (image) {

            const stepData = {
                type: msg.step.type,
                text: msg.step.text,
                screenshot: image
            };

            steps.push(stepData);

            console.log("✅ Saved step:", stepData);
        });
    }

    if (msg.action === "GET_STEPS") {
        sendResponse(steps);
    }

    if (msg.action === "CLEAR") {
        steps = [];
    }
});