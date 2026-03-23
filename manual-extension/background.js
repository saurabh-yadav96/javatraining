let steps = [];

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

    if (msg.action === "CAPTURE_SCREENSHOT") {

        chrome.tabs.captureVisibleTab(null, {}, function (image) {

            const stepData = {
                type: msg.step.type,
                text: msg.step.text,
                screenshot: image   
            };

            steps.push(stepData);

            console.log("Saved step:", stepData);
        });
    }

    if (msg.action === "GET_STEPS") {
        sendResponse(steps);
    }

    if (msg.action === "CLEAR") {
        steps = [];
    }
});