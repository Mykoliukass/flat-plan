/* Comment box shared by plan.html (2D) and plan3d.html (3D).
   Comments are stored in a free Supabase database (see supabase-setup.sql).
   Fill in the two values below once the Supabase project exists — both are PUBLIC values meant for web pages
   (the database only allows reading and adding comments, never editing or deleting). */
const COMMENTS_CONFIG = {
  url: "https://gwozuwxkqoloacudfsjm.supabase.co",
  key: "sb_publishable_usIBmxpvX3zhvj7GoEazKA_jordw-jd",   // public publishable key (read + add only)
};

(function () {
  const PAGE = window.COMMENTS_PAGE;                 // "2d" or "3d", set by the page
  const ready = !!(COMMENTS_CONFIG.url && COMMENTS_CONFIG.key);
  const isNewKey = COMMENTS_CONFIG.key.startsWith("sb_");
  const headers = () => Object.assign({ apikey: COMMENTS_CONFIG.key, "Content-Type": "application/json" },
                                      isNewKey ? {} : { Authorization: "Bearer " + COMMENTS_CONFIG.key });
  const api = (q = "") => COMMENTS_CONFIG.url.replace(/\/$/, "") + "/rest/v1/comments" + q;
  const store = { get(k) { try { return localStorage.getItem(k) || ""; } catch (e) { return ""; } },
                  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };

  /* ---------- styles + panel ---------- */
  const css = document.createElement("style");
  css.textContent = `
    #cmt-btn { position:fixed; right:16px; bottom:16px; z-index:20; font:600 14px system-ui,sans-serif; padding:10px 14px;
               border:0; border-radius:22px; background:#1f5c40; color:#fff; box-shadow:0 2px 10px rgba(0,0,0,.25); cursor:pointer; }
    #cmt-panel { position:fixed; right:16px; bottom:68px; z-index:20; width:min(340px, calc(100vw - 32px)); max-height:min(70vh, 560px);
                 display:none; flex-direction:column; background:#fff; color:#1d1d1b; border:1px solid #ddd9cf; border-radius:12px;
                 box-shadow:0 6px 24px rgba(0,0,0,.2); font:14px/1.4 system-ui,sans-serif; overflow:hidden; }
    #cmt-panel.open { display:flex; }
    #cmt-panel header { all:unset; display:flex; align-items:center; justify-content:space-between; padding:10px 12px; border-bottom:1px solid #eee; }
    #cmt-panel h3 { margin:0; font-size:15px; }
    #cmt-list { overflow:auto; padding:6px 12px; flex:1; }
    .cmt { padding:8px 0; border-bottom:1px solid #f0eee8; }
    .cmt .meta { color:#8a8a84; font-size:12px; }
    .cmt .pin { display:inline-block; min-width:18px; padding:0 5px; border-radius:9px; background:#d0542c; color:#fff; font-size:11px; font-weight:700; text-align:center; margin-right:4px; cursor:pointer; }
    #cmt-form { padding:10px 12px; border-top:1px solid #eee; display:grid; gap:6px; }
    #cmt-form input, #cmt-form textarea { font:inherit; padding:6px 8px; border:1px solid #d6d3ca; border-radius:6px; width:100%; box-sizing:border-box; }
    #cmt-form textarea { min-height:64px; resize:vertical; }
    #cmt-form .row { display:flex; gap:6px; align-items:center; }
    #cmt-form button { font:inherit; padding:6px 10px; border-radius:6px; border:1px solid #c9c5ba; background:#f6f4ef; cursor:pointer; }
    #cmt-form button.send { background:#1f5c40; color:#fff; border-color:#1f5c40; margin-left:auto; }
    #cmt-form button.pinning { background:#d0542c; color:#fff; border-color:#d0542c; }
    #cmt-status { font-size:12px; color:#8a8a84; min-height:16px; }
    .cmt-hp { position:absolute; left:-9999px; }
  `;
  document.head.appendChild(css);

  const btn = document.createElement("button"); btn.id = "cmt-btn"; btn.textContent = "💬 Comments";
  const panel = document.createElement("div"); panel.id = "cmt-panel";
  panel.innerHTML = `
    <header><h3>Comments</h3><button id="cmt-close" style="all:unset;cursor:pointer;font-size:18px" aria-label="Close">×</button></header>
    <div id="cmt-list"></div>
    <form id="cmt-form" autocomplete="off">
      <input id="cmt-name" placeholder="Your name (optional)" maxlength="60">
      <textarea id="cmt-body" placeholder="What do you think?" maxlength="2000" required></textarea>
      <input class="cmt-hp" id="cmt-hp" tabindex="-1" aria-hidden="true">
      <div class="row">
        <button type="button" id="cmt-pin">📍 Pin to a spot</button>
        <span id="cmt-pinned" style="font-size:12px;color:#8a8a84"></span>
        <button type="submit" class="send">Send</button>
      </div>
      <div id="cmt-status"></div>
    </form>`;
  document.body.append(btn, panel);
  const $ = id => document.getElementById(id);
  $("cmt-name").value = store.get("flat-cmt-name");
  btn.onclick = () => { panel.classList.toggle("open"); if (panel.classList.contains("open")) load(); };
  $("cmt-close").onclick = () => panel.classList.remove("open");

  /* ---------- pin picking ---------- */
  let pinning = false, pinned = null, comments = [];
  const setPinning = on => {
    pinning = on; $("cmt-pin").classList.toggle("pinning", on);
    $("cmt-pin").textContent = on ? (PAGE === "3d" ? "Click a spot in 3D…" : "Click a spot on the plan…") : "📍 Pin to a spot";
  };
  $("cmt-pin").onclick = () => { if (pinned) { pinned = null; $("cmt-pinned").textContent = ""; refreshPins(); } setPinning(!pinning); };
  function setPinned(p) {
    pinned = p; setPinning(false);
    $("cmt-pinned").textContent = `pinned (${p.x.toFixed(2)}, ${p.y.toFixed(2)}) ✕`;
    $("cmt-pinned").style.cursor = "pointer";
    $("cmt-pinned").onclick = () => { pinned = null; $("cmt-pinned").textContent = ""; refreshPins(); };
    refreshPins(); $("cmt-body").focus();
  }

  /* ---------- load + send ---------- */
  async function load() {
    const list = $("cmt-list");
    if (!ready) { list.innerHTML = `<p style="color:#8a8a84">Comments aren't connected yet — the database is still being set up.</p>`; return; }
    try {
      const r = await fetch(api("?select=*&order=created_at.asc"), { headers: headers() });
      if (!r.ok) throw new Error(r.status);
      comments = await r.json();
    } catch (e) { list.innerHTML = `<p style="color:#b03a2e">Couldn't load comments (${e.message}).</p>`; return; }
    // handled comments are listed in comments-status.json (kept with the site, updated by Claude)
    let status = {};
    try { const r = await fetch("comments-status.json?t=" + Date.now()); if (r.ok) status = await r.json(); } catch (e) {}
    const isDone = c => status[c.id] && status[c.id].status === "done";
    const open = comments.filter(c => !isDone(c)), done = comments.filter(isDone);
    let n = 0;
    list.innerHTML = open.length ? "" : `<p style="color:#8a8a84">${done.length ? "All comments handled — add a new one!" : "No comments yet — be the first!"}</p>`;
    const when = c => new Date(c.created_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
    open.forEach(c => {
      const d = document.createElement("div"); d.className = "cmt";
      const pinNo = c.x != null ? ++n : null; c._pin = pinNo;
      d.innerHTML = `<div class="meta">${pinNo ? `<span class="pin">${pinNo}</span>` : ""}<b></b> · ${when(c)} · ${c.page.toUpperCase()}</div><div class="text"></div>`;
      d.querySelector("b").textContent = c.name || "Anonymous";
      d.querySelector(".text").textContent = c.body;                 // textContent: no HTML injection
      if (pinNo) d.querySelector(".pin").onclick = () => focusPin(c);
      list.appendChild(d);
    });
    done.forEach(c => { c._pin = null; });                           // no pins for handled comments
    if (done.length) {
      const det = document.createElement("details"); det.style.marginTop = "8px";
      det.innerHTML = `<summary style="cursor:pointer;color:#2f8a57;font-weight:600">✓ Done (${done.length})</summary>`;
      done.forEach(c => {
        const d = document.createElement("div"); d.className = "cmt"; d.style.opacity = "0.75";
        d.innerHTML = `<div class="meta"><b></b> · ${when(c)}</div><div class="text" style="text-decoration:line-through"></div><div class="meta reply" style="color:#2f8a57"></div>`;
        d.querySelector("b").textContent = c.name || "Anonymous";
        d.querySelector(".text").textContent = c.body;
        d.querySelector(".reply").textContent = "✓ " + (status[c.id].note || "done");
        det.appendChild(d);
      });
      list.appendChild(det);
    }
    list.scrollTop = list.scrollHeight;
    refreshPins();
  }
  $("cmt-form").onsubmit = async e => {
    e.preventDefault();
    if (!ready) { $("cmt-status").textContent = "Comments aren't connected yet."; return; }
    if ($("cmt-hp").value) return;                                   // bot trap
    const body = $("cmt-body").value.trim(); if (!body) return;
    const name = $("cmt-name").value.trim().slice(0, 60); store.set("flat-cmt-name", name);
    const layout = (document.getElementById("bath") || {}).value || null;
    const row = { page: PAGE, name: name || null, body, layout,
                  x: pinned ? pinned.x : null, y: pinned ? pinned.y : null, z: pinned && pinned.z != null ? pinned.z : null };
    $("cmt-status").textContent = "Sending…";
    try {
      const r = await fetch(api(), { method: "POST", headers: Object.assign(headers(), { Prefer: "return=minimal" }), body: JSON.stringify(row) });
      if (!r.ok) throw new Error(r.status + " " + (await r.text()).slice(0, 120));
      $("cmt-body").value = ""; pinned = null; $("cmt-pinned").textContent = "";
      $("cmt-status").textContent = "Thanks! Saved ✓"; setTimeout(() => $("cmt-status").textContent = "", 2500);
      load();
    } catch (err) { $("cmt-status").textContent = "Couldn't save: " + err.message; }
  };

  /* ---------- page-specific pins ---------- */
  let refreshPins = () => {}, focusPin = () => {};

  if (PAGE === "2d") {
    const svgEl = document.getElementById("plan"), NS = "http://www.w3.org/2000/svg";
    const toPlan = ev => { const pt = svgEl.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
                           return pt.matrixTransform(svgEl.getScreenCTM().inverse()); };
    svgEl.addEventListener("click", ev => {                          // capture phase: beats Mark mode while pinning
      if (!pinning) return; ev.stopImmediatePropagation(); ev.preventDefault();
      const p = toPlan(ev); setPinned({ x: p.x, y: p.y, z: null });
    }, true);
    refreshPins = () => {
      svgEl.querySelectorAll(".cmt-pin2d").forEach(n => n.remove());
      const add = (x, y, label, color) => {
        const g = document.createElementNS(NS, "g"); g.setAttribute("class", "cmt-pin2d");
        const c = document.createElementNS(NS, "circle");
        Object.entries({ cx: x, cy: y, r: 0.11, fill: color, stroke: "#fff", "stroke-width": 0.02 }).forEach(([k, v]) => c.setAttribute(k, v));
        const t = document.createElementNS(NS, "text");
        Object.entries({ x, y: y + 0.045, "text-anchor": "middle", style: "font-size:0.13px;font-weight:700;fill:#fff" }).forEach(([k, v]) => t.setAttribute(k, v));
        t.textContent = label; g.append(c, t); svgEl.appendChild(g);
      };
      comments.forEach(c => { if (c._pin) add(c.x, c.y, c._pin, "#d0542c"); });
      if (pinned) add(pinned.x, pinned.y, "+", "#1f5c40");
    };
    focusPin = () => svgEl.scrollIntoView({ behavior: "smooth", block: "center" });
    if (typeof window.draw === "function") {                         // re-add pins whenever the plan redraws
      const orig = window.draw; window.draw = function () { orig.apply(this, arguments); refreshPins(); };
    }
  }

  if (PAGE === "3d") {
    const pinGroup = new THREE.Group(); scene.add(pinGroup);
    const canvas = renderer.domElement; let down = null;
    canvas.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY]; });
    canvas.addEventListener("pointerup", e => {
      if (!pinning || !down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;   // ignore drags
      const m = new THREE.Vector2(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
      const r = new THREE.Raycaster(); r.setFromCamera(m, camera);
      const hit = r.intersectObjects(world.children, true).find(h => h.object.isMesh && !(h.object.material && h.object.material.transparent));
      if (hit) setPinned({ x: hit.point.x, y: hit.point.z, z: hit.point.y });
    });
    const label = (text, color) => {
      const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d");
      g.fillStyle = color; g.beginPath(); g.arc(32, 32, 28, 0, Math.PI * 2); g.fill();
      g.lineWidth = 4; g.strokeStyle = "#fff"; g.stroke();
      g.fillStyle = "#fff"; g.font = "bold 30px system-ui"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, 32, 34);
      const tex = new THREE.CanvasTexture(c); tex.encoding = THREE.sRGBEncoding;
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, toneMapped: false }));
      s.scale.set(0.22, 0.22, 1); s.renderOrder = 10; return s;
    };
    refreshPins = () => {
      while (pinGroup.children.length) pinGroup.remove(pinGroup.children[0]);
      const add = (x, y, z, text, color) => { const s = label(String(text), color); s.position.set(x, (z ?? 1.0) + 0.12, y); pinGroup.add(s); };
      comments.forEach(c => { if (c._pin) add(c.x, c.y, c.z, c._pin, "#d0542c"); });
      if (pinned) add(pinned.x, pinned.y, pinned.z, "+", "#1f5c40");
    };
    focusPin = c => { if (typeof centerOn === "function") centerOn(new THREE.Vector3(c.x, c.z ?? 1.0, c.y)); };
  }

  if (ready) load();                                                 // show existing pins right away
})();
