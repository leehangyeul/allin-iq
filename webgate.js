// ALLIN IQ web: player accounts (access code + nickname + password).
// Loaded after the game script; replaces the claude.ai join flow with server accounts.
// A nickname is taken once and never changes; the same nickname + password brings the player back on any device.
(function () {
  const A = () => window.HGQ_AUTH || null;
  const isPlayerAcc = () => { const a = A(); return !!(a && !a.isAdmin && !a.anon && a.name); };

  // runs once the server session is known, before the game reads or writes any record
  const origSet = window.__fbSet;
  window.__fbSet = (x) => {
    try {
      const a = A();
      if (a) {
        const last = lsGet("hgq-uid");
        // a different person on this device: start from that person's server record, not the last one's
        if (last && last !== a.uid) { clearLocal(); results = []; lsSet("hgq-acc", ""); lsSet("hgq-kick", "0"); if (!a.isAdmin) { MYNAME = ""; lsSet("hgq-name", ""); } }
        lsSet("hgq-uid", a.uid);
        if (isPlayerAcc()) { MYNAME = a.name; lsSet("hgq-name", a.name); }
        if (a.isAdmin && MYNAME) a.reserve(MYNAME).catch(() => {});
      }
    } catch (e) { console.warn(e); }
    origSet(x);
  };

  window.gateState = gateState = function () {
    if (typeof window === "undefined" || !window.claude) return "open";
    if (LB.db && !LB.rowsReady) return "loading";
    if (LB.owner) return "open";
    if (!ACC.ready) return "loading";
    if (!LB.db) return "signin";
    if (!LB.rowsReady) return "loading";
    if (isBlocked(LB.uid)) return "blocked";
    if (!ACC.h) return "nocode";
    if (!isPlayerAcc()) return "lock";
    return accMine() === ACC.h ? "open" : "lock";
  };

  // the admin's own nickname is reserved too, so no player can take it
  const origName = nameScreen;
  window.nameScreen = nameScreen = function (next) {
    const a = A();
    if (!LB.owner || !a) { origName(next); return; }
    origName(async () => {
      const r = await a.reserve(MYNAME);
      if (r && r.err === "taken") { MYNAME = ""; lsSet("hgq-name", ""); origName(next); const e = $("nmerr"); if (e) { e.textContent = "이미 플레이어가 쓰는 닉네임이에요. 다른 닉네임을 정해 주세요."; e.hidden = false; } return; }
      next();
    });
  };

  const ERR = {
    taken: "이미 사용 중인 닉네임이에요. 다른 닉네임을 정해 주세요.",
    badpw: "닉네임 또는 비밀번호가 맞지 않아요.",
    nouser: "이 닉네임으로 가입한 기록이 없어요. '처음이에요'에서 가입해 주세요.",
    badtemp: "확인 코드가 맞지 않아요. 관리자에게 받은 6자리 숫자를 다시 확인해 주세요.",
    noreset: "비밀번호 초기화가 요청된 닉네임이 아니에요. 관리자에게 먼저 초기화를 요청해 주세요.",
    wait: "여러 번 틀려서 잠시 막혔어요. 몇 분 뒤에 다시 시도해 주세요.",
    setup: "서버 설정이 아직 끝나지 않았어요. 관리자에게 알려 주세요.",
    denied: "서버에서 확인하지 못했어요. 접속 코드를 다시 확인해 주세요.",
    badname: "닉네임에 / 기호는 쓸 수 없어요.",
    badpin: "비밀번호는 숫자 4~6자리로 정해 주세요.",
    other: "처음 입력했던 닉네임으로 다시 시도해 주세요.",
    net: "연결에 실패했어요. 잠시 후 다시 시도해 주세요.",
  };
  const J = { mode: null, name: "", msg: "" };

  window.joinScreen = joinScreen = function () {
    SCREEN = "join"; const g = gateState(); ACC.shown = true; const a = A();
    const recode = isPlayerAcc();
    if (!J.mode || (recode && J.mode !== "recode")) J.mode = recode ? "recode" : (lsGet("hgq-had") ? "login" : "new");
    if (!recode && J.mode === "recode") J.mode = "new";
    if (!J.name && MYNAME) J.name = MYNAME;
    const sub = J.mode === "recode" ? "새 접속 코드를 입력하세요" : J.mode === "login" ? "닉네임과 비밀번호로 이어서 해요" : J.mode === "reset" ? "새 비밀번호를 정해요" : "접속 코드, 닉네임, 비밀번호를 정해요";
    $("top").innerHTML = topHTML(J.mode === "login" ? "이어하기" : J.mode === "reset" ? "비밀번호 다시 정하기" : "참가하기", sub, "", true); bindBack();
    $("prog").innerHTML = "";
    $("stage").innerHTML = `<div class="band"><div class="bfelt"><div class="bb">${bigCard("A♠", "sm")}${bigCard("K♥", "sm")}</div><div class="bline"><span class="muted">한 번 가입하면 어느 기기에서든 이어서 해요</span></div></div></div>`;
    const pinIn = (id, ph) => `<input id="${id}" type="password" inputmode="numeric" pattern="[0-9]*" maxlength="6" autocomplete="${J.mode === "login" ? "current-password" : "new-password"}" placeholder="${ph}">`;
    const codeIn = `<label for="jc">접속 코드</label><input id="jc" maxlength="20" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="관리자에게 받은 코드">`;
    const nameIn = (ph) => `<label for="jn">닉네임 (1~12자)</label><input id="jn" maxlength="12" autocomplete="username" value="${esc(J.name)}" placeholder="${ph}">`;
    let body;
    if (g === "loading") body = `<div class="lb"><p class="lbw">확인 중이에요…</p></div>`;
    else if (g === "signin") body = `<div class="lb"><div class="lbh"><b>연결할 수 없어요</b></div><p class="lbw">서버에 연결하지 못했어요. 인터넷 연결을 확인하고 새로고침해 주세요.</p></div>`;
    else if (g === "blocked") body = `<div class="lb"><div class="lbh"><b>참가할 수 없어요</b></div><p class="lbw">관리자가 이 계정의 참가를 제한했어요. 관리자에게 문의해 주세요.</p></div>`;
    else if (g === "nocode") body = `<div class="lb"><div class="lbh"><b>아직 열리지 않았어요</b></div><p class="lbw">관리자가 접속 코드를 정하면 참가할 수 있어요. 잠시 후 다시 열어 주세요.</p></div>`;
    else if (J.mode === "recode") body = `<form class="namef" id="joinf"><p class="warn2">${esc(MYNAME)} 님, 접속 코드가 바뀌었어요. 관리자에게 받은 새 코드를 입력해 주세요. 기록은 그대로 남아 있어요.</p>
        ${codeIn}<p class="warn2" id="jerr" hidden></p><button class="cta" type="submit" id="jgo">계속하기</button>
        <button class="lnk" type="button" id="jOut">다른 닉네임으로 들어가기</button></form>`;
    else {
      const tabs = J.mode === "reset" ? "" : `<div class="jtabs" role="tablist"><button type="button" role="tab" class="${J.mode === "new" ? "on" : ""}" data-jm="new" aria-selected="${J.mode === "new"}">처음이에요</button><button type="button" role="tab" class="${J.mode === "login" ? "on" : ""}" data-jm="login" aria-selected="${J.mode === "login"}">이어하기</button></div>`;
      let f = "";
      if (J.mode === "new") f = `${codeIn}${nameIn("예: 홀덤왕")}
          <label for="jp">비밀번호 (숫자 4~6자리)</label>${pinIn("jp", "다른 기기에서 이어할 때 필요해요")}
          <label for="jp2">비밀번호 확인</label>${pinIn("jp2", "한 번 더 입력")}
          <p class="note jnote">닉네임은 한 번 정하면 바꿀 수 없어요. 다른 기기에서는 '이어하기'에서 같은 닉네임과 비밀번호를 넣으면 기록이 그대로 이어져요.</p>`;
      else if (J.mode === "login") f = `${codeIn}${nameIn("가입한 닉네임")}
          <label for="jp">비밀번호</label>${pinIn("jp", "숫자 4~6자리")}
          <button class="lnk" type="button" id="jForgot">비밀번호를 잊었어요</button>`;
      else f = `<p class="note jnote">관리자에게 비밀번호 초기화를 요청하면 6자리 확인 코드를 받아요. 그 코드로 새 비밀번호를 정하면 기록은 그대로 이어져요.</p>
          ${codeIn}${nameIn("가입한 닉네임")}
          <label for="jt">확인 코드 (관리자에게 받은 6자리)</label><input id="jt" inputmode="numeric" pattern="[0-9]*" maxlength="6" autocomplete="one-time-code" placeholder="예: 123456">
          <label for="jp">새 비밀번호 (숫자 4~6자리)</label>${pinIn("jp", "새 비밀번호")}
          <label for="jp2">새 비밀번호 확인</label>${pinIn("jp2", "한 번 더 입력")}
          <button class="lnk" type="button" id="jToLogin">이어하기로 돌아가기</button>`;
      const old = J.mode === "new" && a && a.anon && MYNAME && (STATS.n || DSTATS.n) ? `<p class="warn2">이 기기에 남아 있는 기록(${esc(MYNAME)})을 이어가려면 같은 닉네임으로 비밀번호를 정해 주세요.</p>` : "";
      body = `<form class="namef" id="joinf">${tabs}${old}${accMine() && ACC.h && accMine() !== ACC.h ? `<p class="warn2">접속 코드가 바뀌었어요. 관리자에게 받은 새 코드를 입력해 주세요.</p>` : ""}${f}
        <p class="warn2" id="jerr" ${J.msg ? "" : "hidden"}>${esc(J.msg)}</p><button class="cta" type="submit" id="jgo">${J.mode === "new" ? "가입하고 시작" : J.mode === "login" ? "이어하기" : "새 비밀번호 저장"}</button></form>`;
    }
    J.msg = "";
    $("panel").innerHTML = `${body}<button class="ghost" id="jBack">처음 화면으로</button>`;
    $("jBack").onclick = () => { ACC.pending = null; menu(); };
    if (a && !a.isAdmin && !isPlayerAcc()) { const r = document.createElement("div"); r.className = "admrow"; r.innerHTML = `<button class="lnk" id="admIn2">관리자 로그인</button>`; $("panel").appendChild(r); $("admIn2").onclick = () => a.admin(); }
    const keep = () => { const n = $("jn"); if (n) J.name = n.value; };
    document.querySelectorAll("[data-jm]").forEach((b) => b.onclick = () => { keep(); J.mode = b.dataset.jm; joinScreen(); });
    const fg = $("jForgot"); if (fg) fg.onclick = () => { keep(); J.mode = "reset"; joinScreen(); };
    const tl = $("jToLogin"); if (tl) tl.onclick = () => { keep(); J.mode = "login"; joinScreen(); };
    const jo = $("jOut"); if (jo) jo.onclick = () => leave();
    const f = $("joinf"); if (!f) return;
    const err = (t) => { const e = $("jerr"); e.textContent = t; e.hidden = false; };
    f.onsubmit = async (e) => {
      e.preventDefault(); const a = A(); if (!a) { err(ERR.net); return; }
      if (Date.now() < ACC.until) { err(`잠시 후 다시 시도해 주세요 (${Math.ceil((ACC.until - Date.now()) / 1000)}초).`); return; }
      const code = normAcc($("jc").value);
      if (!code) { err("접속 코드를 입력해 주세요."); return; }
      let name = "", pin = "", pin2 = "", temp = "";
      if (J.mode !== "recode") {
        name = a.nameClean($("jn").value); J.name = name;
        pin = String($("jp").value || "").trim(); const p2 = $("jp2"); pin2 = p2 ? String(p2.value || "").trim() : pin;
        const t = $("jt"); temp = t ? String(t.value || "").replace(/\D/g, "") : "";
        if (!name) { err("닉네임을 입력해 주세요."); return; }
        if (a.nameBad(name)) { err(ERR.badname); return; }
        if (!a.pinOk(pin)) { err(J.mode === "login" ? "비밀번호를 입력해 주세요 (숫자 4~6자리)." : ERR.badpin); return; }
        if (pin !== pin2) { err("비밀번호 확인이 일치하지 않아요."); return; }
        if (J.mode === "reset" && temp.length !== 6) { err("확인 코드 6자리를 입력해 주세요."); return; }
      }
      const b = $("jgo"); b.disabled = true; b.textContent = "확인 중…";
      const h = await accHash(ACC.salt, code);
      if (!h || h !== ACC.h) {
        b.disabled = false; b.textContent = J.mode === "recode" ? "계속하기" : J.mode === "new" ? "가입하고 시작" : J.mode === "login" ? "이어하기" : "새 비밀번호 저장";
        ACC.tries++; if (ACC.tries >= 5) { ACC.tries = 0; ACC.until = Date.now() + 30000; err("5번 틀렸어요. 30초 뒤에 다시 시도해 주세요."); } else err("접속 코드가 맞지 않아요."); return;
      }
      ACC.tries = 0;
      let r;
      if (J.mode === "recode") r = await a.recode(code);
      else if (J.mode === "new") r = await a.register({ name, pin, code });
      else if (J.mode === "login") r = await a.login({ name, pin, code });
      else r = await a.claim({ name, temp, pin, code });
      if (!r || !r.ok) {
        const c = (r && r.err) || "net";
        if (c === "reset") { J.mode = "reset"; J.msg = "관리자가 이 닉네임의 비밀번호를 초기화했어요. 받은 확인 코드로 새 비밀번호를 정해 주세요."; joinScreen(); return; }
        b.disabled = false; b.textContent = "다시 시도"; err(ERR[c] || ERR.net); return;
      }
      lsSet("hgq-acc", h); lsSet("hgq-had", "1");
      if (r.name) { MYNAME = r.name; lsSet("hgq-name", r.name); }
      if (r.switched) { b.textContent = "불러오는 중…"; clearLocal(); lsSet("hgq-kick", "0"); if (r.uid) lsSet("hgq-uid", r.uid); location.reload(); return; }
      a.anon = false; if (r.name) a.name = r.name; LB.writeFail = false; ACC.sig = null; J.mode = null; J.name = "";
      lbPush();
      const fn = ACC.pending; ACC.pending = null; (fn || menu)();
    };
    setTimeout(() => { try { const t = $("jc"); t && t.focus(); } catch (e) {} }, 50);
  };

  // sign this device out of the nickname (shared phones); the record stays on the server
  async function leave() {
    const a = A(); lsSet("hgq-acc", ""); lsSet("hgq-name", ""); MYNAME = "";
    if (a) await a.leave(); else location.reload();
  }

  // start screen: players can't rename; show who is signed in and a sign-out link
  const origMenu = menu;
  window.menu = menu = function () {
    origMenu();
    if (LB.owner) return;
    const rn = $("rename"); if (rn) rn.remove();
    if (isPlayerAcc() && MENUTAB === "more") {
      const p = $("panel"); const row = document.createElement("div"); row.className = "admrow";
      row.innerHTML = `<span>${esc(MYNAME)} 님으로 로그인됨</span><button class="lnk" id="plOut">로그아웃</button>`;
      p.insertBefore(row, p.querySelector(".mnavsp")); $("plOut").onclick = () => leave();
    }
  };

  // admin: one-time code so a player who forgot the password can set a new one and keep the record
  const origPl = adminPlayersHTML;
  window.adminPlayersHTML = adminPlayersHTML = function () {
    let h = origPl();
    if (!A() || !A().isAdmin) return h;
    h = h.replace(/(<button class="lnk dng" data-blk="[^"]*" data-nm="([^"]*)">차단<\/button>)/g, (m, all, nm) => `<button class="lnk" data-rst="${nm}">비밀번호 초기화</button>${all}`);
    if (RST.name) h = h.replace('<ul class="adl">', `<div class="rstbox"><b>${esc(RST.name)}</b> 님 확인 코드<div class="codebox sm">${esc(RST.temp)}</div><p class="lbs">이 6자리를 플레이어에게 알려 주세요. 플레이어는 '이어하기 → 비밀번호를 잊었어요'에서 이 코드로 새 비밀번호를 정해요. 기록은 그대로 이어져요.</p></div><ul class="adl">`);
    return h;
  };
  const RST = { name: "", temp: "" };
  const origBind = adminBindPlayers;
  window.adminBindPlayers = adminBindPlayers = function () {
    origBind();
    document.querySelectorAll("#adPl [data-rst]").forEach((b) => b.onclick = async () => {
      const a = A(); if (!a) return; b.disabled = true; b.textContent = "처리 중…";
      const r = await a.adminReset(b.dataset.rst);
      if (r && r.ok) { RST.name = r.name; RST.temp = r.temp; LB.msg = ""; }
      else { RST.name = ""; LB.msg = r && r.err === "nouser" ? "이 플레이어는 비밀번호 계정이 없어요 (예전 방식으로 들어온 플레이어)." : "초기화하지 못했어요. 잠시 후 다시 시도해 주세요."; }
      adminLive();
    });
  };

  const css = document.createElement("style");
  css.textContent = `
.jtabs{display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:4px;border-radius:14px;background:#0E1118;border:1px solid #232838;margin-bottom:6px}
.jtabs button{min-height:44px;border:0;border-radius:10px;background:transparent;color:#9A9384;font-weight:700;font-size:15px}
.jtabs button.on{background:linear-gradient(160deg,#F0D7AE,#C79E66);color:#0B0A08}
.jnote{text-align:left;margin:4px 0 2px}
#jForgot,#jToLogin,#jOut{align-self:flex-start;min-height:40px;font-size:13px}
.rstbox{margin:8px 0 12px;padding:12px 14px;border-radius:14px;border:1px solid #D4AF7C;background:#14120E}
.rstbox .codebox{margin:8px 0}`;
  document.head.appendChild(css);

  if (SCREEN === "menu") menu();
})();
