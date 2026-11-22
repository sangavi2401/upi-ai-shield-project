document.addEventListener("DOMContentLoaded", function () {

    // 1. MESSAGE SCANNER

    const scanForm = document.getElementById("scanForm");
    const messageInput = document.getElementById("messageInput");
    const scanResult = document.getElementById("scanResult");
    const shareWhatsappBtn = document.getElementById("shareWhatsappBtn");

    let latestReport = "";

    if (shareWhatsappBtn) {
        shareWhatsappBtn.disabled = true;
    }

    if (scanForm) {

        scanForm.addEventListener("submit", async function (event) {

            event.preventDefault();

            if (!messageInput || !scanResult) {
                console.error("Message scanner HTML elements are missing.");
                return;
            }

            const message = messageInput.value.trim();

            if (!message) {
                scanResult.textContent = "Please enter a message first.";
                return;
            }

            scanResult.textContent = "Analyzing message... Please wait.";

            if (shareWhatsappBtn) {
                shareWhatsappBtn.disabled = true;
            }

            try {

                const response = await fetch("/scan", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message: message
                    })
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(
                        result.error || "Scanning failed."
                    );
                }

                latestReport =
                    "UPI Shield AI Scan Report\n\n" +
                    "Risk Level: " + result.risk_level +
                    "\nRisk Score: " + result.risk_score + "/100" +
                    "\nDetected Patterns: " +
                    (
                        Array.isArray(result.detected_patterns) &&
                        result.detected_patterns.length
                            ? result.detected_patterns.join(", ")
                            : "None"
                    ) +
                    "\nRule-Based Explanation: " + result.explanation +
                    "\n\nAI Analysis:\n" +
                    (result.ai_analysis || "AI analysis unavailable.");

                scanResult.textContent = latestReport;

                if (shareWhatsappBtn) {
                    shareWhatsappBtn.disabled = false;
                }

                updateStats(result.risk_score >= 20);

                addActivity("Message scanned", result.risk_level);

            } catch (error) {

                scanResult.textContent = "Error: " + error.message;

                console.error("Scan error:", error);

            }

        });

    }


    // 2. WHATSAPP REPORT SHARING

    if (shareWhatsappBtn) {

        shareWhatsappBtn.addEventListener("click", function () {

            if (!latestReport) {
                alert("Please scan a message first.");
                return;
            }

            const whatsappURL =
                "https://wa.me/?text=" +
                encodeURIComponent(latestReport);

            window.open(whatsappURL, "_blank");

        });

    }


    // 3. PAYMENT LINK CHECKER - CONNECTED TO FLASK

    const linkCheckForm = document.getElementById("linkCheckForm");
    const paymentLinkInput = document.getElementById("paymentLinkInput");
    const linkCheckResult = document.getElementById("linkCheckResult");

    if (linkCheckForm) {

        linkCheckForm.addEventListener("submit", async function (event) {

            event.preventDefault();

            if (!paymentLinkInput || !linkCheckResult) {
                console.error("Payment link checker HTML elements are missing.");
                return;
            }

            const link = paymentLinkInput.value.trim();

            if (!link) {
                linkCheckResult.textContent =
                    "Please enter a payment link first.";
                return;
            }

            linkCheckResult.textContent =
                "Checking payment link... Please wait.";

            try {

                const response = await fetch("/check-link", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        url: link
                    })
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(
                        result.error || "Payment link checking failed."
                    );
                }

                let report =
                    "Payment Link Analysis\n\n" +
                    "Link: " + result.checked_url +
                    "\nRisk Level: " + result.risk_level +
                    "\nRisk Score: " + result.risk_score + "/100" +
                    "\n\nWarnings:\n";

                if (
                    Array.isArray(result.warnings) &&
                    result.warnings.length > 0
                ) {
                    report += result.warnings.join("\n");
                } else {
                    report += "No basic warning signs detected.";
                }

                report += "\n\n" + result.explanation;

                linkCheckResult.textContent = report;

                updateStats(result.risk_score >= 20);

                addActivity(
                    "Payment link checked",
                    result.risk_level
                );

            } catch (error) {

                linkCheckResult.textContent =
                    "Error: " + error.message;

                console.error("Link checking error:", error);

            }

        });

    }


    // 4. QR IMAGE FILE SELECTION

    const qrUploadForm = document.getElementById("qrUploadForm");
    const qrImageInput = document.getElementById("qrImageInput");
    const qrFileName = document.getElementById("qrFileName");
    const qrResult = document.getElementById("qrResult");

    if (qrImageInput) {

        qrImageInput.addEventListener("change", function () {

            const file = qrImageInput.files[0];

            if (!file) {
                return;
            }

            if (!file.type.startsWith("image/")) {

                if (qrFileName) {
                    qrFileName.textContent =
                        "Please select an image file.";
                }

                qrImageInput.value = "";
                return;

            }

            if (qrFileName) {
                qrFileName.textContent =
                    "Selected: " + file.name;
            }

            if (qrResult) {
                qrResult.textContent =
                    "Image selected. QR decoding will be connected in the next step.";
            }

        });

    }

    if (qrUploadForm) {

        qrUploadForm.addEventListener("submit", function (event) {

            event.preventDefault();

            if (!qrImageInput || !qrImageInput.files.length) {

                if (qrResult) {
                    qrResult.textContent =
                        "Please select a QR image first.";
                }

                return;

            }

            if (qrResult) {
                qrResult.textContent =
                    "Image received. Actual QR decoding is not connected yet.";
            }

        });

    }


    // 5. DASHBOARD STATISTICS

    let totalScans = 0;
    let fraudAlerts = 0;

    function updateStats(isSuspicious) {

        totalScans++;

        if (isSuspicious) {
            fraudAlerts++;
        }

        const totalElement =
            document.getElementById("totalScans");

        const alertsElement =
            document.getElementById("fraudAlerts");

        if (totalElement) {
            totalElement.textContent = totalScans;
        }

        if (alertsElement) {
            alertsElement.textContent = fraudAlerts;
        }

    }


    // 6. RECENT ACTIVITY

    function addActivity(title, description) {

        const activityList =
            document.getElementById("activityList");

        if (!activityList) {
            return;
        }

        const item = document.createElement("div");

        item.className = "activity-item";

        const titleElement =
            document.createElement("strong");

        titleElement.textContent = title;

        const descriptionElement =
            document.createElement("span");

        descriptionElement.textContent = description;

        item.appendChild(titleElement);
        item.appendChild(descriptionElement);

        activityList.prepend(item);

    }


    // 7. DASHBOARD SEARCH

    const dashboardSearch =
        document.getElementById("dashboardSearch");

    if (dashboardSearch) {

        dashboardSearch.addEventListener("input", function () {

            const searchText =
                dashboardSearch.value.toLowerCase();

            document.querySelectorAll(
                ".activity-item, .feature-card"
            ).forEach(function (item) {

                item.style.display =
                    item.textContent.toLowerCase().includes(searchText)
                        ? ""
                        : "none";

            });

        });

    }

});
const qrUploadForm = document.getElementById("qrUploadForm");
const qrImageInput = document.getElementById("qrImageInput");
const qrFileName = document.getElementById("qrFileName");
const qrResult = document.getElementById("qrResult");

if (qrUploadForm) {
    qrUploadForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const file = qrImageInput.files[0];

        if (!file) {
            qrResult.textContent = "Please select a QR code image first.";
            return;
        }

        qrResult.textContent = "Scanning QR code... Please wait.";

        const formData = new FormData();
        formData.append("qr_image", file);

        try {
            const response = await fetch("/check-qr", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "QR scanning failed.");
            }

            if (!result.qr_found) {
                qrResult.textContent = result.message;
                return;
            }

            qrResult.textContent =
                "QR Code Successfully Scanned\n\n" +
                "Decoded Content: " + result.decoded_content +
                "\n\n" + result.message;

            addActivity("QR code scanned", "Completed");
            updateStats(false);

        } catch (error) {
            qrResult.textContent = "Error: " + error.message;
        }
    });
}

if (qrImageInput && qrFileName) {
    qrImageInput.addEventListener("change", function () {
        qrFileName.textContent = this.files.length
            ? this.files[0].name
            : "No file selected";
    });
}