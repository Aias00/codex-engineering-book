/* Progressive enhancement: the complete book, TOC and download work without JS. */
(() => {
  "use strict";
  const root = document.documentElement;
  const storage = {
    get(key) {
      try { return window.localStorage.getItem(`codex-book:${key}`); }
      catch (_) { return null; }
    },
    set(key, value) {
      try { window.localStorage.setItem(`codex-book:${key}`, value); }
      catch (_) { /* Private browsing or disabled storage must not stop reading. */ }
    }
  };
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
  const savedTheme = storage.get("theme");
  if (savedTheme === "light" || savedTheme === "dark") root.dataset.theme = savedTheme;
  let fontSize = Number(storage.get("font-size"));
  if (!Number.isFinite(fontSize) || fontSize < 15 || fontSize > 24) {
    fontSize = window.matchMedia("(max-width: 900px)").matches ? 17 : 18;
  }
  const smaller = document.getElementById("font-smaller");
  const larger = document.getElementById("font-larger");
  const themeToggle = document.getElementById("theme-toggle");
  const themeLabel = document.getElementById("theme-label");
  function applyFont() {
    root.style.setProperty("--body-size", `${fontSize}px`);
    smaller.disabled = fontSize <= 15;
    larger.disabled = fontSize >= 24;
  }
  function updateThemeLabel() {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : systemDark.matches;
    const label = dark ? "切换到浅色主题" : "切换到深色主题";
    themeToggle.setAttribute("aria-label", label);
    themeToggle.title = label;
    themeLabel.textContent = dark ? "深色" : "浅色";
    document.querySelector('meta[name="theme-color"]').content = dark ? "#181e1c" : "#f7f6f2";
  }
  smaller.addEventListener("click", () => {
    fontSize = Math.max(15, fontSize - 1); applyFont(); storage.set("font-size", fontSize);
  });
  larger.addEventListener("click", () => {
    fontSize = Math.min(24, fontSize + 1); applyFont(); storage.set("font-size", fontSize);
  });
  themeToggle.addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : systemDark.matches;
    root.dataset.theme = dark ? "light" : "dark";
    storage.set("theme", root.dataset.theme);
    updateThemeLabel();
  });
  if (systemDark.addEventListener) systemDark.addEventListener("change", updateThemeLabel);
  applyFont();
  updateThemeLabel();
  document.querySelector(".enhanced-controls").hidden = false;

  const menu = document.getElementById("chapter-menu");
  const mobile = window.matchMedia("(max-width: 900px)");
  menu.open = !mobile.matches;
  if (mobile.addEventListener) mobile.addEventListener("change", event => { menu.open = !event.matches; });
  menu.addEventListener("click", event => {
    if (mobile.matches && event.target.closest("a[href^='#']")) menu.open = false;
  });

  const article = document.getElementById("book-content");
  const headings = [...article.querySelectorAll("h1[id], h2[id], h3[id]")];
  const links = [...document.querySelectorAll("#TOC a[href^='#']")];
  const linkById = new Map(links.map(link => [decodeURIComponent(link.hash.slice(1)), link]));
  const chapters = [...article.querySelectorAll("h1[id]")];
  const savedChapter = storage.get("chapter");
  const savedTarget = savedChapter && document.getElementById(savedChapter);
  if (savedTarget && article.contains(savedTarget) && savedTarget !== chapters[0]) {
    const start = document.getElementById("start-reading");
    start.href = `#${encodeURIComponent(savedChapter)}`;
    start.firstChild.textContent = "继续阅读 ";
    const note = document.getElementById("resume-note");
    note.textContent = `上次读到：${savedTarget.textContent.trim().replace(/\s+/g, " ")}`;
    note.hidden = false;
  }
  const progressBar = document.getElementById("progress-bar");
  const progressLabel = document.getElementById("progress-label");
  let activeLink = null;
  let ticking = false;
  let lastChapter = null;
  function updateReading() {
    const headerHeight = Number.parseInt(getComputedStyle(root).getPropertyValue("--header-height"), 10) || 72;
    const offset = headerHeight + 60;
    const start = article.getBoundingClientRect().top + window.scrollY;
    const end = start + article.offsetHeight - window.innerHeight + headerHeight;
    const progress = Math.min(100, Math.max(0, ((window.scrollY - start + offset) / Math.max(1, end - start)) * 100));
    progressBar.style.width = `${progress}%`;
    progressLabel.textContent = `${Math.round(progress)}%`;
    let current = null;
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= offset) current = heading;
      else break;
    }
    const nextLink = current ? linkById.get(current.id) : null;
    if (nextLink !== activeLink) {
      if (activeLink) activeLink.removeAttribute("aria-current");
      if (nextLink) nextLink.setAttribute("aria-current", "location");
      activeLink = nextLink;
    }
    let chapter = null;
    for (const heading of chapters) {
      if (heading.getBoundingClientRect().top <= offset) chapter = heading;
      else break;
    }
    if (chapter && chapter.id !== lastChapter) {
      storage.set("chapter", chapter.id);
      lastChapter = chapter.id;
    }
    ticking = false;
  }
  function scheduleUpdate() {
    if (!ticking) {
      window.requestAnimationFrame(updateReading);
      ticking = true;
    }
  }
  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate, { passive: true });
  window.addEventListener("load", scheduleUpdate, { once: true });
  updateReading();
})();

/* BEGIN AIAS SHARED READER */
/* Aias Reader 1.0. Shared preference across books on aias00.github.io. */
(() => {
  'use strict';
  const root = document.documentElement;
  const key = 'aias-reader-theme';
  const read = () => { try { return localStorage.getItem(key); } catch { return null; } };
  let theme = read() === 'dark' ? 'dark' : 'light';
  let control;
  function apply() {
    root.dataset.theme = theme;
    if (document.body) document.body.classList.toggle('dark', theme === 'dark');
    const palette = document.querySelector('[data-md-component="palette"]');
    if (palette) {
      const scheme = theme === 'dark' ? 'slate' : 'default';
      document.body.dataset.mdColorScheme = scheme;
      const selected = palette.querySelector(`input[data-md-color-scheme="${scheme}"]`);
      if (selected) {
        selected.checked = true;
        palette.querySelectorAll('label[for]').forEach(label => { label.hidden = label.htmlFor === selected.id; });
      }
    }
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#1c1f24' : '#f7f7f3');
    if (!control) return;
    if (control.tagName === 'SELECT') {
      control.value = theme;
    } else {
      control.textContent = theme === 'dark' ? '切换浅色' : '切换深色';
      control.setAttribute('aria-pressed', String(theme === 'dark'));
    }
    control.setAttribute('aria-label', theme === 'dark' ? '切换到浅色模式' : '切换到深色模式');
  }
  apply();
  function initialize() {
    const palette = document.querySelector('[data-md-component="palette"]');
    if (palette) {
      palette.addEventListener('change', event => {
        theme = event.target.dataset.mdColorScheme === 'slate' ? 'dark' : 'light';
        try { localStorage.setItem(key, theme); } catch { /* Optional persistence. */ }
        apply();
      });
      apply();
      return;
    }
    control = document.querySelector('#theme-toggle, #theme, select[name="theme"]');
    if (!control) {
      const bar = document.createElement('div');
      bar.className = 'aias-reader-tools';
      const home = document.createElement('a');
      home.href = 'https://aias00.github.io/#books';
      home.textContent = 'Aias · 电子书架';
      control = document.createElement('button');
      control.type = 'button';
      bar.append(home, control);
      (document.querySelector('main') || document.body).prepend(bar);
    }
    control.hidden = false;
    control.classList.add('aias-reader-theme');
    if (control.tagName === 'SELECT') {
      control.replaceChildren(...['light', 'dark'].map(value => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value === 'light' ? '浅色' : '深色';
        return option;
      }));
    }
    const eventName = control.tagName === 'SELECT' ? 'change' : 'click';
    // Capture before legacy handlers; all other reader controls keep working.
    document.addEventListener(eventName, event => {
      if (!control.contains(event.target)) return;
      event.stopImmediatePropagation();
      if (eventName === 'click') event.preventDefault();
      theme = control.tagName === 'SELECT' ? control.value : theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(key, theme); } catch { /* Reading works without storage. */ }
      apply();
    }, true);
    apply();
  }
  // Legacy initializers finish first; the shared preference is applied last.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(initialize, 0), { once: true });
  } else {
    setTimeout(initialize, 0);
  }
  addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    theme = event.newValue === 'dark' ? 'dark' : 'light';
    apply();
  });
})();
/* END AIAS SHARED READER */
