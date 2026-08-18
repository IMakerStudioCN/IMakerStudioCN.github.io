async function loadSubmissionSettings() {
  const visitorLink = document.querySelector("#visitor-submit-link");
  try {
    const response = await fetch("./resources.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (data.submitUrl) visitorLink.href = data.submitUrl;
  } catch (error) {
    console.error("无法读取投稿地址", error);
  }
}

loadSubmissionSettings();
