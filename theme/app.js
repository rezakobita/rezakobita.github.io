/* রেজার কবিতা — interactions */
(() => {
  const root = document.documentElement;
  root.classList.remove("no-js");
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  let DATA = { poems: [], sections: {} };
  try { DATA = JSON.parse($("#site-data").textContent); } catch (e) {}
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };
  const canVT = typeof document.startViewTransition === "function";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- toast */
  const toastEl = $(".toast");
  let toastTimer;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2200);
  }

  /* ---------- current nav item */
  const kind = document.body.classList.contains("home") ? "home"
    : document.body.classList.contains("about-page") ? "about"
    : (document.body.classList.contains("index") || document.body.classList.contains("poem-page")) ? "all" : "";
  $$(".nav a").forEach(a => { if (a.dataset.nav === kind) a.setAttribute("aria-current", "page"); });

  /* ---------- mobile menu */
  const nav = $("#nav");
  $("[data-menu]")?.addEventListener("click", () => nav.classList.toggle("open"));
  document.addEventListener("click", e => {
    if (nav?.classList.contains("open") && !e.target.closest(".nav,[data-menu]")) nav.classList.remove("open");
  });

  /* ---------- header shadow on scroll */
  const onScroll = () => document.body.classList.toggle("scrolled", scrollY > 8);
  addEventListener("scroll", onScroll, { passive: true }); onScroll();

  /* ---------- reading progress fallback (browsers without scroll timelines) */
  const bar = $(".progress");
  if (bar && document.body.classList.contains("poem-page") && !CSS.supports("animation-timeline: scroll()")) {
    const upd = () => {
      const h = document.documentElement.scrollHeight - innerHeight;
      bar.style.transform = `scaleX(${h > 0 ? Math.min(1, scrollY / h) : 0})`;
    };
    addEventListener("scroll", upd, { passive: true }); upd();
  }

  /* ---------- reveal on scroll */
  const io = "IntersectionObserver" in window ? new IntersectionObserver(entries => {
    entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
  }, { rootMargin: "0px 0px -6% 0px", threshold: .08 }) : null;
  const watch = el => io ? io.observe(el) : el.classList.add("in");
  $$(".reveal, .stanza").forEach(watch);

  /* ---------- theme toggle with a circular wipe */
  const themeBtn = $("[data-theme-toggle]");
  themeBtn?.addEventListener("click", e => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    const apply = () => {
      root.dataset.theme = next; store.set("rk-theme", next);
      $('meta[name="theme-color"]')?.setAttribute("content", next === "dark" ? "#121620" : "#f5eee1");
    };
    if (!canVT || reduce) return apply();
    root.style.setProperty("--tx", e.clientX + "px");
    root.style.setProperty("--ty", e.clientY + "px");
    root.classList.add("theme-swap");
    const t = document.startViewTransition(apply);
    t.finished.finally(() => root.classList.remove("theme-swap"));
  });

  /* ---------- random poem */
  function randomPoem(btn) {
    const list = DATA.poems.filter(p => p.s !== document.querySelector(".poem")?.dataset.slug);
    if (!list.length) return;
    const p = list[Math.floor(Math.random() * list.length)];
    btn?.classList.add("spin");
    setTimeout(() => { location.href = p.u; }, reduce ? 0 : 380);
  }
  $$("[data-random]").forEach(b => b.addEventListener("click", () => randomPoem(b.classList.contains("icon-btn") ? b : null)));

  /* ---------- shared-element title morph between pages */
  document.addEventListener("click", e => {
    const a = e.target.closest("a[data-slug]");
    if (!a) return;
    $$("[data-vt]").forEach(t => t.style.viewTransitionName = "");
    const t = a.querySelector("[data-vt]");
    if (t) t.style.viewTransitionName = "poem-title";
    try { sessionStorage.setItem("rk-last", a.dataset.slug); } catch (err) {}
  });
  // coming back from a poem: morph its title back into its card
  addEventListener("pagereveal", e => {
    if (!e.viewTransition) return;
    let last = null; try { last = sessionStorage.getItem("rk-last"); } catch (err) {}
    const t = last && $(`[data-vt="${CSS.escape(last)}"]`);
    if (t) {
      t.style.viewTransitionName = "poem-title";
      e.viewTransition.finished.finally(() => { t.style.viewTransitionName = ""; });
    }
  });
  const poemEl = $(".poem");
  if (poemEl) { try { sessionStorage.setItem("rk-last", poemEl.dataset.slug); } catch (err) {} }

  /* ---------- poem of the day (home) */
  const dailyWrap = $(".daily-wrap");
  if (dailyWrap && DATA.poems.length) {
    const d = new Date();
    const seed = d.getFullYear() * 372 + d.getMonth() * 31 + d.getDate();
    const p = DATA.poems[(seed * 7919) % DATA.poems.length];
    const el = $(".daily", dailyWrap);
    el.href = p.u; el.dataset.slug = p.s;
    el.classList.add("sec-" + p.c);
    el.innerHTML = `<span class="card-sec">${esc(DATA.sections[p.c] || "")}</span>
      <span class="featured-title card-title" data-vt="${esc(p.s)}">${esc(p.t)}</span>
      <span class="featured-lines">${p.x.map(l => `<span>${esc(l)}</span>`).join("")}</span>
      <span class="more">পুরো কবিতা পড়ুন →</span>`;
    dailyWrap.hidden = false;
    $$(".reveal", dailyWrap).forEach(watch);
  }
  function esc(s) { return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

  /* ---------- index: filter + search */
  const cards = $$("#cards .card");
  if (cards.length) {
    const chips = $$(".chip");
    const q = $("#q");
    const countEl = $(".result-count");
    const empty = $(".empty");
    let filter = "all", full = null, loading = null;
    const bnNum = n => String(n).replace(/\d/g, d => "০১২৩৪৫৬৭৮৯"[d]);
    const norm = s => s.normalize("NFC").toLowerCase().replace(/[‌‍]/g, "").replace(/[।,;:!?'"“”‘’\-–—.]/g, " ").replace(/\s+/g, " ").trim();
    const exOrig = new Map(cards.map(c => [c, $(".card-ex", c).innerHTML]));

    function loadFull() {
      if (full || loading) return loading;
      const url = (DATA.root || "/").replace(/index\.html$/, "") + "assets/search.json";
      loading = fetch(url).then(r => r.json()).then(j => { full = j; }).catch(() => { full = {}; });
      return loading;
    }
    q.addEventListener("focus", loadFull, { once: true });

    function apply(animate) {
      const term = norm(q.value || "");
      let shown = 0;
      const run = () => {
        cards.forEach(c => {
          const slug = c.dataset.slug;
          const inSec = filter === "all" || c.dataset.section === filter;
          let hit = true, snippet = null;
          if (term) {
            const title = norm($(".card-title", c).textContent);
            hit = title.includes(term);
            if (full && full[slug]) {
              const line = full[slug].split("\n").find(l => norm(l).includes(term));
              if (line) { hit = true; if (!title.includes(term)) snippet = line; }
            }
          }
          const show = inSec && hit;
          c.classList.toggle("out", !show);
          const ex = $(".card-ex", c);
          if (snippet) {
            const words = term.split(" ").filter(Boolean).map(w => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
            const re = new RegExp("(" + words.join("|") + ")", "gi");
            ex.innerHTML = `<span>${esc(snippet).replace(re, "<mark>$1</mark>")}</span>`;
          } else if (ex.innerHTML !== exOrig.get(c)) ex.innerHTML = exOrig.get(c);
          if (show) shown++;
        });
        empty.hidden = shown > 0;
        countEl.textContent = (term || filter !== "all") ? `${bnNum(shown)}টি কবিতা পাওয়া গেছে` : "";
      };
      if (animate && canVT && !reduce) {
        cards.forEach((c, i) => { c.style.viewTransitionName = "c" + i; });
        root.classList.add("filtering");
        const t = document.startViewTransition(run);
        t.finished.finally(() => { root.classList.remove("filtering"); cards.forEach(c => c.style.viewTransitionName = ""); });
      } else run();
    }

    function setFilter(f, animate) {
      filter = DATA.sections[f] ? f : "all";
      chips.forEach(ch => ch.classList.toggle("active", ch.dataset.filter === filter));
      apply(animate);
    }
    chips.forEach(ch => ch.addEventListener("click", () => {
      setFilter(ch.dataset.filter, true);
      try { history.replaceState(null, "", filter === "all" ? location.pathname : "#" + filter); } catch (e) {}
    }));
    let tm;
    q.addEventListener("input", () => {
      clearTimeout(tm);
      tm = setTimeout(async () => { if (q.value.trim()) await loadFull(); apply(false); }, 140);
    });
    addEventListener("hashchange", () => setFilter(location.hash.slice(1), true));
    cards.forEach(c => c.classList.add("in"));
    setFilter(location.hash.slice(1), false);
  }

  /* ---------- poem page: text size, share, keyboard */
  if (poemEl) {
    const steps = [0.85, 0.92, 1, 1.12, 1.25, 1.4];
    let cur = parseFloat(store.get("rk-scale") || "1");
    let idx = steps.indexOf(cur); if (idx < 0) idx = 2;
    $$("[data-size]").forEach(b => b.addEventListener("click", () => {
      idx = Math.max(0, Math.min(steps.length - 1, idx + parseInt(b.dataset.size, 10)));
      root.style.setProperty("--scale", steps[idx]);
      store.set("rk-scale", String(steps[idx]));
      toast(idx === 2 ? "স্বাভাবিক আকার" : (parseInt(b.dataset.size, 10) > 0 ? "লেখা বড় হলো" : "লেখা ছোট হলো"));
    }));

    const title = $(".poem-title").textContent.trim();
    const pageUrl = ($('link[rel="canonical"]')?.href) || location.href;
    const panel = $(".share-panel");
    const text = `${title} — ${$(".byline").textContent.trim()}`;
    $("[data-wa]", panel).href = "https://wa.me/?text=" + encodeURIComponent(text + "\n" + pageUrl);
    $("[data-fb]", panel).href = "https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent(pageUrl);
    $("[data-share]").addEventListener("click", async () => {
      if (navigator.share && matchMedia("(pointer: coarse)").matches) {
        try { await navigator.share({ title, text, url: pageUrl }); return; } catch (e) { if (e.name === "AbortError") return; }
      }
      panel.hidden = !panel.hidden;
    });
    $("[data-copy]", panel).addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(pageUrl); toast("লিংক কপি হয়েছে"); }
      catch (e) { toast(pageUrl); }
    });

    addEventListener("keydown", e => {
      if (e.altKey || e.ctrlKey || e.metaKey || /input|textarea/i.test(e.target.tagName)) return;
      const a = $(`.pager [data-key="${e.key}"]`);
      if (a) location.href = a.href;
    });
  }
})();
