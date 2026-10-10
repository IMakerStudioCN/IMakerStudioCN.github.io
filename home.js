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

function initWorkCarousel() {
  const carousel = document.querySelector(".works-carousel");
  const track = document.querySelector("#works-track");
  const slides = [...document.querySelectorAll(".work-slide")];
  const current = document.querySelector("#works-current");
  const total = document.querySelector("#works-total");
  const progress = document.querySelector("#works-progress-bar");
  if (!carousel || !track || !slides.length || !current || !total || !progress) return;

  let activeIndex = 0;
  let touchStartX = null;

  const showSlide = (requestedIndex) => {
    activeIndex = (requestedIndex + slides.length) % slides.length;
    track.style.setProperty("--work-index", String(activeIndex));
    progress.style.setProperty("--work-progress", `${((activeIndex + 1) / slides.length) * 100}%`);
    current.textContent = String(activeIndex + 1).padStart(2, "0");
    slides.forEach((slide, index) => {
      const isActive = index === activeIndex;
      slide.setAttribute("aria-hidden", String(!isActive));
      const link = slide.querySelector("a");
      if (link) link.tabIndex = isActive ? 0 : -1;
    });
  };

  total.textContent = String(slides.length).padStart(2, "0");
  carousel.querySelectorAll("[data-direction]").forEach((button) => {
    button.addEventListener("click", () => {
      showSlide(activeIndex + (button.dataset.direction === "next" ? 1 : -1));
    });
  });

  carousel.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    showSlide(activeIndex + (event.key === "ArrowRight" ? 1 : -1));
  });

  const viewport = carousel.querySelector(".works-viewport");
  viewport?.addEventListener("touchstart", (event) => {
    touchStartX = event.changedTouches[0]?.clientX ?? null;
  }, { passive: true });
  viewport?.addEventListener("touchend", (event) => {
    if (touchStartX === null) return;
    const distance = (event.changedTouches[0]?.clientX ?? touchStartX) - touchStartX;
    if (Math.abs(distance) > 45) showSlide(activeIndex + (distance < 0 ? 1 : -1));
    touchStartX = null;
  }, { passive: true });

  showSlide(0);
}

function initSectionReveals() {
  const sections = [...document.querySelectorAll(".studio-about, .works-section, .resource-bridge, .contribution-section, .studio-closing")];
  if (!sections.length) return;
  sections.forEach((section) => section.classList.add("reveal-section"));
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
    sections.forEach((section) => section.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12 });
  sections.forEach((section) => observer.observe(section));
}

loadHomeResources();
initWorkCarousel();
initSectionReveals();
