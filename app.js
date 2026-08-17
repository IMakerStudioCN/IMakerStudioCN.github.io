const state = {
  resources: [],
  category: "全部",
  query: "",
};

const elements = {
  grid: document.querySelector("#resource-grid"),
  status: document.querySelector("#status"),
  empty: document.querySelector("#empty-state"),
  filters: document.querySelector("#category-filters"),
  search: document.querySelector("#search-input"),
  resourceCount: document.querySelector("#resource-count"),
  categoryCount: document.querySelector("#category-count"),
  updatedAt: document.querySelector("#updated-at"),
  clear: document.querySelector("#clear-filters"),
  submit: document.querySelector("#submit-link"),
};

function normalize(value) {
  return value.toLocaleLowerCase("zh-CN").trim();
}

function filteredResources() {
  const query = normalize(state.query);
  return state.resources.filter((resource) => {
    const inCategory = state.category === "全部" || resource.category === state.category;
    const searchable = [resource.name, resource.description, resource.category, ...resource.tags].join(" ");
    return inCategory && (!query || normalize(searchable).includes(query));
  });
}

function renderFilters() {
  const categories = ["全部", ...new Set(state.resources.map((item) => item.category))];
  elements.filters.replaceChildren(...categories.map((category) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = category;
    button.setAttribute("aria-pressed", String(category === state.category));
    button.addEventListener("click", () => {
      state.category = category;
      renderFilters();
      renderResources();
    });
    return button;
  }));
}

function resourceCard(resource, index) {
  const link = document.createElement("a");
  link.className = "resource-card";
  link.href = resource.url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.setAttribute("aria-label", `${resource.name}，在新窗口打开`);

  const number = document.createElement("span");
  number.className = "resource-number";
  number.textContent = String(index + 1).padStart(2, "0");

  const content = document.createElement("div");
  content.className = "resource-content";
  const meta = document.createElement("div");
  meta.className = "resource-meta";
  meta.textContent = [resource.category, ...resource.tags.slice(0, 2)].join("  ·  ");
  const title = document.createElement("h3");
  title.textContent = resource.name;
  const description = document.createElement("p");
  description.textContent = resource.description;
  content.append(meta, title, description);

  const arrow = document.createElement("span");
  arrow.className = "resource-arrow";
  arrow.setAttribute("aria-hidden", "true");
  arrow.textContent = "↗";
  link.append(number, content, arrow);
  return link;
}

function renderResources() {
  const resources = filteredResources();
  elements.grid.replaceChildren(...resources.map(resourceCard));
  elements.grid.hidden = resources.length === 0;
  elements.empty.hidden = resources.length !== 0;
  elements.status.hidden = true;
}

async function loadResources() {
  try {
    const response = await fetch("./resources.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    state.resources = data.resources;
    elements.resourceCount.textContent = String(data.resources.length).padStart(2, "0");
    elements.categoryCount.textContent = String(new Set(data.resources.map((item) => item.category)).size).padStart(2, "0");
    elements.updatedAt.textContent = data.updatedAt;
    if (data.submitUrl) elements.submit.href = data.submitUrl;
    renderFilters();
    renderResources();
  } catch (error) {
    elements.status.textContent = "资源暂时无法读取，请稍后刷新页面。";
    elements.status.dataset.state = "error";
    console.error(error);
  }
}

elements.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderResources();
});

elements.clear.addEventListener("click", () => {
  state.query = "";
  state.category = "全部";
  elements.search.value = "";
  renderFilters();
  renderResources();
  elements.search.focus();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement !== elements.search) {
    event.preventDefault();
    elements.search.focus();
  }
});

loadResources();
