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

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("steps", JSON.stringify(steps));

        const res = await fetch("http://127.0.0.1:8000/generate-manual-from-frs", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            alert("API failed: " + res.status);
            return;
        }

        const data = await res.json();

        console.log("API response:", data);

        alert("Manual generated!");

        // ✅ CORRECT DOWNLOAD
        const url = `http://127.0.0.1:8000/download/pdf/1/${data.version}`;

        chrome.downloads.download({
            url: url,
            filename: `manual_v${data.version}.pdf`,
            saveAs: true
        });
    });
};