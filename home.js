async function loadHomeResources() {
  const list = document.querySelector("#home-resource-list");
  try {
    const response = await fetch("./resources.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const resources = Array.isArray(data.resources) ? data.resources : [];
    document.querySelector("#home-resource-count").textContent = String(resources.length).padStart(2, "0");
    document.querySelector("#home-category-count").textContent = String(new Set(resources.map((item) => item.category)).size).padStart(2, "0");
    document.querySelector("#home-updated-at").textContent = data.updatedAt || "—";
    const recent = resources.slice(-3).reverse();
    if (!recent.length) {
      list.innerHTML = '<p class="status">资源站正在整理中。</p>';
      return;
    }
    list.replaceChildren(...recent.map((resource, index) => {
      const link = document.createElement("a");
      link.className = "latest-resource";
      link.href = resource.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.setAttribute("aria-label", `${resource.name}，在新窗口打开`);
      const number = document.createElement("span");
      number.className = "latest-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const content = document.createElement("div");
      const meta = document.createElement("small");
      meta.textContent = [resource.category, resource.type].filter(Boolean).join(" · ");
      const title = document.createElement("strong");
      title.textContent = resource.name;
      const description = document.createElement("p");
      description.textContent = resource.description;
      content.append(meta, title, description);
      const arrow = document.createElement("span");
      arrow.className = "latest-arrow";
      arrow.setAttribute("aria-hidden", "true");
      arrow.textContent = "↗";
      link.append(number, content, arrow);
      return link;
    }));
  } catch (error) {
    list.innerHTML = '<p class="status" data-state="error">资源概况暂时无法读取，请进入资源站查看。</p>';
    console.error(error);
  }
}

loadHomeResources();
