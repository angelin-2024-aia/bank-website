// Attack banner update logic
function updateUIForAttackType(type) {
  const banner = document.getElementById("attack-banner");
  const label = document.getElementById("attack-label");
  const detail = document.getElementById("attack-detail");

  if (!banner || !label || !detail) return;

  banner.classList.remove(
    "stb-attack-normal",
    "stb-attack-warning",
    "stb-attack-danger"
  );

  if (type === "brute_force") {
    banner.classList.add("stb-attack-danger");
    label.textContent = "🚨 Alert: Suspicious login activity detected";
    detail.textContent =
      "Multiple failed login attempts from unusual IP ranges. Please secure your account.";
  } else if (type === "recon") {
    banner.classList.add("stb-attack-warning");
    label.textContent = "⚠️ Notice: Reconnaissance behaviour observed";
    detail.textContent =
      "Unusual page scanning and parameter probing detected. Monitor your account activity.";
  } else if (type === "malware_download") {
    banner.classList.add("stb-attack-warning");
    label.textContent = "⚠️ Alert: Suspicious file download detected";
    detail.textContent =
      "Potential malware signatures detected in recent download. Please scan your device.";
  } else if (type === "anomaly") {
    banner.classList.add("stb-attack-warning");
    label.textContent = "🔍 Alert: Anomalous behaviour detected";
    detail.textContent =
      "AI detected unusual activity patterns on your account. Review your recent transactions.";
  } else {
    banner.classList.add("stb-attack-normal");
    label.textContent = "✓ Environment: Normal traffic";
    detail.textContent =
      "No suspicious activity detected on your account.";
  }
}

// Polling function (uncomment when Madhu API ready)
/*
function pollAttackType() {
  fetch("/api/last-attack-type")
    .then((response) => response.json())
    .then((data) => {
      if (data && data.type) {
        updateUIForAttackType(data.type);
      }
    })
    .catch((error) => {
      console.error("API polling error:", error);
    });
}

// Start polling on dashboard page
if (location.pathname.endsWith("dashboard.html")) {
  // Poll every 5 seconds
  setInterval(pollAttackType, 5000);
  // Initial poll
  pollAttackType();
}
*/

// Demo: Change attack type on page load (remove later)
document.addEventListener("DOMContentLoaded", function () {
  // Uncomment one for testing:
  // updateUIForAttackType("brute_force");
  // updateUIForAttackType("recon");
  // updateUIForAttackType("malware_download");
  // updateUIForAttackType("anomaly");
});
