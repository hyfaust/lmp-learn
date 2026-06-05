// ===== Project Data =====
const PROJECTS = [
  {
    id: "01-first-simulation",
    number: "01",
    title: "第一个模拟：LJ 熔化",
    level: "beginner",
    levelName: "入门基础",
    icon: "🔥",
    file: "projects/01-first-simulation/README.md"
  },
  {
    id: "02-units-and-boxes",
    number: "02",
    title: "单位制与模拟盒子",
    level: "beginner",
    levelName: "入门基础",
    icon: "📦",
    file: "projects/02-units-and-boxes/README.md"
  },
  {
    id: "03-energy-minimization",
    number: "03",
    title: "能量最小化",
    level: "beginner",
    levelName: "入门基础",
    icon: "⬇️",
    file: "projects/03-energy-minimization/README.md"
  },
  {
    id: "04-thermostat-nvt",
    number: "04",
    title: "温度控制与 NVT 系综",
    level: "intermediate",
    levelName: "基础操作",
    icon: "🌡️",
    file: "projects/04-thermostat-nvt/README.md"
  },
  {
    id: "05-barostat-npt",
    number: "05",
    title: "压力控制与 NPT 系综",
    level: "intermediate",
    levelName: "基础操作",
    icon: "⚖️",
    file: "projects/05-barostat-npt/README.md"
  },
  {
    id: "06-molecular-simulation",
    number: "06",
    title: "分子模拟入门",
    level: "intermediate",
    levelName: "基础操作",
    icon: "🧬",
    file: "projects/06-molecular-simulation/README.md"
  },
  {
    id: "07-metal-eam",
    number: "07",
    title: "金属体系与 EAM 势",
    level: "advanced",
    levelName: "中级应用",
    icon: "🔩",
    file: "projects/07-metal-eam/README.md"
  },
  {
    id: "08-crystal-defects",
    number: "08",
    title: "晶体缺陷与力学性质",
    level: "advanced",
    levelName: "中级应用",
    icon: "💎",
    file: "projects/08-crystal-defects/README.md"
  },
  {
    id: "09-diffusion-transport",
    number: "09",
    title: "扩散与输运性质",
    level: "advanced",
    levelName: "中级应用",
    icon: "🌊",
    file: "projects/09-diffusion-transport/README.md"
  },
  {
    id: "10-non-equilibrium-md",
    number: "10",
    title: "非平衡分子动力学",
    level: "expert",
    levelName: "高级应用",
    icon: "⚡",
    file: "projects/10-non-equilibrium-md/README.md"
  },
  {
    id: "11-free-energy-neb",
    number: "11",
    title: "自由能计算与 NEB",
    level: "expert",
    levelName: "高级应用",
    icon: "📈",
    file: "projects/11-free-energy-neb/README.md"
  },
  {
    id: "12-python-analysis",
    number: "12",
    title: "Python 接口与数据分析",
    level: "expert",
    levelName: "高级应用",
    icon: "🐍",
    file: "projects/12-python-analysis/README.md"
  }
];

const LEVEL_GROUPS = [
  { name: "🟢 入门基础 Level 1", levels: ["beginner"] },
  { name: "🟡 基础操作 Level 2", levels: ["intermediate"] },
  { name: "🟠 中级应用 Level 3", levels: ["advanced"] },
  { name: "🔴 高级应用 Level 4", levels: ["expert"] }
];

const LEVEL_BADGE = {
  beginner: { class: "badge-beginner", text: "入门" },
  intermediate: { class: "badge-intermediate", text: "基础" },
  advanced: { class: "badge-advanced", text: "中级" },
  expert: { class: "badge-advanced", text: "高级" }
};

// ===== State =====
let currentIndex = -1;
let completed = JSON.parse(localStorage.getItem("lmp_completed") || "[]");
let cache = {};

// ===== DOM Elements =====
const sidebar = document.getElementById("sidebar");
const sidebarNav = document.getElementById("sidebarNav");
const overlay = document.getElementById("overlay");
const content = document.getElementById("content");
const topbarTitle = document.getElementById("topbarTitle");
const completeBtn = document.getElementById("completeBtn");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const toc = document.getElementById("toc");
const tocToggle = document.getElementById("tocToggle");
const searchInput = document.getElementById("searchInput");

// ===== Initialize =====
function init() {
  renderNav();
  updateProgress();

  // Theme
  const savedTheme = localStorage.getItem("lmp_theme") || "light";
  setTheme(savedTheme);

  // Event listeners
  document.getElementById("themeToggle").addEventListener("click", toggleTheme);
  document.getElementById("menuToggle").addEventListener("click", toggleSidebar);
  overlay.addEventListener("click", toggleSidebar);
  completeBtn.addEventListener("click", toggleComplete);
  tocToggle.addEventListener("click", toggleTOC);
  searchInput.addEventListener("input", filterNav);

  // Handle hash navigation
  if (window.location.hash) {
    const id = window.location.hash.slice(1);
    const idx = PROJECTS.findIndex(p => p.id === id);
    if (idx >= 0) navigateTo(idx);
  }
}

// ===== Navigation =====
function renderNav(filter = "") {
  let html = "";
  const lf = filter.toLowerCase();

  for (const group of LEVEL_GROUPS) {
    const items = PROJECTS.filter(p =>
      group.levels.includes(p.level) &&
      (!lf || p.title.toLowerCase().includes(lf) || p.number.includes(lf))
    );
    if (items.length === 0) continue;

    html += `<div class="nav-group">`;
    html += `<div class="nav-group-title">${group.name}</div>`;
    for (const p of items) {
      const isCompleted = completed.includes(p.id);
      const isActive = PROJECTS[currentIndex]?.id === p.id;
      const badge = LEVEL_BADGE[p.level];
      html += `
        <a class="nav-item ${isCompleted ? "completed" : ""} ${isActive ? "active" : ""}"
           href="#${p.id}"
           data-index="${PROJECTS.indexOf(p)}"
           onclick="event.preventDefault(); navigateTo(${PROJECTS.indexOf(p)})">
          <span class="nav-icon">${p.icon}</span>
          <span class="nav-number">${p.number}</span>
          <span>${p.title}</span>
        </a>`;
    }
    html += `</div>`;
  }

  sidebarNav.innerHTML = html;
}

function filterNav() {
  renderNav(searchInput.value);
}

async function navigateTo(index) {
  if (index < 0 || index >= PROJECTS.length) return;

  currentIndex = index;
  const project = PROJECTS[index];

  // Update URL hash
  window.history.pushState(null, "", `#${project.id}`);

  // Update nav
  renderNav(searchInput.value);

  // Update topbar
  topbarTitle.textContent = `${project.icon} ${project.title}`;

  // Update complete button
  updateCompleteButton();

  // Close mobile sidebar
  if (sidebar.classList.contains("open")) toggleSidebar();

  // Show loading
  content.innerHTML = `<div class="loading"><div class="spinner"></div>加载中...</div>`;
  toc.style.display = "none";
  tocToggle.style.display = "none";

  // Fetch markdown
  try {
    let md;
    if (cache[project.file]) {
      md = cache[project.file];
    } else {
      const resp = await fetch(project.file);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      md = await resp.text();
      cache[project.file] = md;
    }

    // Render markdown
    renderMarkdown(md);

    // Build TOC
    buildTOC();

    // Add prev/next navigation
    addFooterNav();

    // Scroll to top
    window.scrollTo(0, 0);
  } catch (err) {
    content.innerHTML = `
      <h1>${project.icon} ${project.title}</h1>
      <div class="badge ${LEVEL_BADGE[project.level].class}">${LEVEL_BADGE[project.level].text}</div>
      <hr>
      <blockquote>
        <p>⚠️ 无法加载文档: ${err.message}</p>
        <p>请确保项目文件 <code>${project.file}</code> 已生成。</p>
        <p>可以先运行 <code>bash scripts/run_all.sh</code> 生成所有项目文件，然后刷新页面。</p>
      </blockquote>`;
    toc.style.display = "none";
    tocToggle.style.display = "none";
  }
}

// ===== Markdown Rendering =====
function renderMarkdown(md) {
  // Configure marked
  marked.setOptions({
    gfm: true,
    breaks: false,
    highlight: function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      // Auto-detect lammps as bash
      if (code.includes("units") || code.includes("atom_style") || code.includes("pair_style") ||
          code.includes("fix") || code.includes("run") || code.includes("lattice") ||
          code.includes("create_box") || code.includes("minimize")) {
        return hljs.highlight(code, { language: "bash" }).value;
      }
      return hljs.highlightAuto(code).value;
    }
  });

  // Custom renderer for code blocks with copy button
  const renderer = new marked.Renderer();
  const originalCode = renderer.code.bind(renderer);
  renderer.code = function(code, language, escaped) {
    const lang = language || "";
    let highlighted;
    try {
      if (lang && hljs.getLanguage(lang)) {
        highlighted = hljs.highlight(code, { language: lang }).value;
      } else if (code.includes("units") || code.includes("atom_style") || code.includes("pair_style")) {
        highlighted = hljs.highlight(code, { language: "bash" }).value;
      } else {
        highlighted = hljs.highlightAuto(code).value;
      }
    } catch (e) {
      highlighted = code;
    }
    const langLabel = lang ? lang.toUpperCase() : "CODE";
    return `<pre><div class="code-header"><span>${langLabel}</span><button class="copy-btn" onclick="copyCode(this)">📋 复制</button></div><code class="hljs language-${lang}">${highlighted}</code></pre>`;
  };

  const html = marked.parse(md, { renderer });
  content.innerHTML = `<div class="markdown-body">${html}</div>`;

  // Handle lammps code blocks that might not be tagged
  content.querySelectorAll("pre code").forEach(block => {
    if (!block.classList.contains("hljs")) {
      hljs.highlightElement(block);
    }
  });

  // Render LaTeX formulas with MathJax
  if (window.MathJax && MathJax.typesetPromise) {
    MathJax.typesetPromise([content]).catch(err => console.warn("MathJax:", err));
  }
}

function buildTOC() {
  const headings = content.querySelectorAll("h2, h3");
  if (headings.length < 3) {
    toc.style.display = "none";
    tocToggle.style.display = "none";
    return;
  }

  let html = `<div class="toc-title">目录</div>`;
  headings.forEach((h, i) => {
    const id = `heading-${i}`;
    h.id = id;
    const cls = h.tagName === "H3" ? "toc-h3" : "";
    html += `<a href="#${id}" class="${cls}" onclick="scrollToHeading('${id}'); return false;">${h.textContent}</a>`;
  });

  toc.innerHTML = html;
  tocToggle.style.display = "";
  // Restore last user preference; default to visible
  const pref = localStorage.getItem("lmp_toc_visible");
  const visible = pref !== null ? pref === "true" : true;
  toc.style.display = visible ? "block" : "none";
  tocToggle.classList.toggle("active", visible);

  // Scroll spy
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const link = toc.querySelector(`a[href="#${entry.target.id}"]`);
      if (link) {
        if (entry.isIntersecting) {
          toc.querySelectorAll("a").forEach(a => a.classList.remove("active"));
          link.classList.add("active");
        }
      }
    });
  }, { rootMargin: "-80px 0px -80% 0px" });

  headings.forEach(h => observer.observe(h));
}

function scrollToHeading(id) {
  const el = document.getElementById(id);
  if (el) {
    const y = el.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top: y, behavior: "smooth" });
  }
}

function toggleTOC() {
  const visible = toc.style.display !== "block";
  toc.style.display = visible ? "block" : "none";
  tocToggle.classList.toggle("active", visible);
  localStorage.setItem("lmp_toc_visible", visible);
}

function addFooterNav() {
  const prev = currentIndex > 0 ? PROJECTS[currentIndex - 1] : null;
  const next = currentIndex < PROJECTS.length - 1 ? PROJECTS[currentIndex + 1] : null;

  let html = `<div class="content-footer"><div class="prev-next">`;
  if (prev) {
    html += `<button class="nav-btn" onclick="navigateTo(${currentIndex - 1})">← ${prev.icon} ${prev.title}</button>`;
  }
  if (next) {
    html += `<button class="nav-btn" onclick="navigateTo(${currentIndex + 1})">${next.icon} ${next.title} →</button>`;
  }
  html += `</div></div>`;
  content.insertAdjacentHTML("beforeend", html);
}

// ===== Copy Code =====
window.copyCode = function(btn) {
  const pre = btn.closest("pre");
  const code = pre.querySelector("code");
  const text = code.textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = "✓ 已复制";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = "📋 复制";
      btn.classList.remove("copied");
    }, 2000);
  });
};

// ===== Progress =====
function toggleComplete() {
  if (currentIndex < 0) return;
  const id = PROJECTS[currentIndex].id;
  const idx = completed.indexOf(id);
  if (idx >= 0) {
    completed.splice(idx, 1);
  } else {
    completed.push(id);
  }
  localStorage.setItem("lmp_completed", JSON.stringify(completed));
  updateCompleteButton();
  updateProgress();
  renderNav(searchInput.value);
}

function updateCompleteButton() {
  if (currentIndex < 0) {
    completeBtn.style.display = "none";
    return;
  }
  completeBtn.style.display = "inline-block";
  const id = PROJECTS[currentIndex].id;
  if (completed.includes(id)) {
    completeBtn.textContent = "✓ 已完成";
    completeBtn.classList.add("completed");
  } else {
    completeBtn.textContent = "○ 标记完成";
    completeBtn.classList.remove("completed");
  }
}

function updateProgress() {
  const count = completed.length;
  const total = PROJECTS.length;
  const pct = Math.round((count / total) * 100);
  progressFill.style.width = pct + "%";
  progressText.textContent = `${count}/${total} 已完成`;
}

// ===== Theme =====
function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const btn = document.getElementById("themeToggle");
  btn.textContent = theme === "dark" ? "☀️ 亮色" : "🌙 暗色";

  // Update highlight.js theme
  const hljsLink = document.getElementById("hljs-theme");
  if (theme === "dark") {
    hljsLink.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/catppuccin-mocha.min.css";
  } else {
    hljsLink.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css";
  }

  localStorage.setItem("lmp_theme", theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  setTheme(current === "dark" ? "light" : "dark");
}

// ===== Sidebar Toggle =====
function toggleSidebar() {
  sidebar.classList.toggle("open");
  overlay.classList.toggle("show");
}

// ===== Keyboard Navigation =====
document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === "ArrowLeft" && currentIndex > 0) {
    navigateTo(currentIndex - 1);
  } else if (e.key === "ArrowRight" && currentIndex < PROJECTS.length - 1) {
    navigateTo(currentIndex + 1);
  } else if (e.key === "Escape") {
    if (sidebar.classList.contains("open")) toggleSidebar();
  }
});

// ===== Browser Back/Forward =====
window.addEventListener("popstate", () => {
  if (window.location.hash) {
    const id = window.location.hash.slice(1);
    const idx = PROJECTS.findIndex(p => p.id === id);
    if (idx >= 0) navigateTo(idx);
  }
});

// ===== Start =====
init();
