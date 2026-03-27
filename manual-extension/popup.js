document.getElementById("start").onclick = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, { action: "START" });
    });
};

document.getElementById("stop").onclick = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, { action: "STOP" });
    });
};
document.getElementById("generate").onclick = () => {

    chrome.runtime.sendMessage({ action: "GET_STEPS" }, async (steps) => {

        console.log("Steps:", steps);

        if (!steps || steps.length === 0) {
            alert("No steps recorded!");
            return;
        }

        const fileInput = document.getElementById("frsFile");

        if (!fileInput.files.length) {
            alert("Please upload FRS file");
            return;
        }

        // ✅ CLEAN STEPS (SAFE)
        const cleanedSteps = steps.map(s => ({
            type: s.type,
            text: s.text,
            field: s.field,
            value: s.value,
            screenshot: s.screenshot || null
        }));

        console.log("📤 Sending Steps:", cleanedSteps);

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("steps", JSON.stringify(cleanedSteps));

        try {
            const res = await fetch("http://127.0.0.1:8000/generate-manual-from-frs", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                const errorText = await res.text();
                console.error("❌ API Error:", errorText);
                alert("API failed: " + errorText);
                return;
            }

            const data = await res.json();

            console.log("✅ API response:", data);

            alert("Manual generated!");

            const url = `http://127.0.0.1:8000/download/pdf/1/${data.version}`;

            chrome.downloads.download({
                url: url,
                filename: `manual_v${data.version}.pdf`,
                saveAs: true
            });

        } catch (err) {
            console.error("❌ Fetch Error:", err);
            alert("Request failed");
        }
    });
};