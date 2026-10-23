from gen import *

# ================= 푸시/폴드 (자체 계산 값) =================
def _pick_by_mix(rng, items, key):
    """items: [(cls, p)] 중에서 경계(혼합) 핸드를 40% 확률로 우선 뽑아요"""
    mixed = [c for c, p in items if .05 < p < .95]
    if mixed and rng.random() < .4: return rng.choice(mixed)
    near = [c for c, p in items if p in (0, 1)]
    return rng.choice(near)


def _note_jam(p, d, who):
    if p >= .95: return f"{d}BB에서 {who}는 이 핸드로 올인하는 게 기본이에요. 상대가 콜하는 범위를 계산해도 올인 쪽이 더 이득이에요."
    if p <= .05: return f"{d}BB에서 {who}는 이 핸드로 올인하면 콜 범위에 지는 경우가 많아 손해예요. 폴드가 기본이에요."
    return f"{d}BB 올인 경계에 있는 핸드예요. 올인과 폴드를 섞어서 써요."


def _note_call(p, d):
    if p >= .95: return f"필요 승률보다 이 핸드의 승률이 높아 콜이 기본이에요. 상대 올인 범위가 넓은 자리예요."
    if p <= .05: return f"상대 올인 범위를 상대로 필요 승률에 못 미쳐요. 폴드가 기본이에요."
    return f"콜 경계에 있는 핸드예요. 콜과 폴드를 섞어서 써요."


def _run_board(rng, hero, vh):
    d = [c for c in DECK if c not in hero and c not in vh]
    return rng.sample(d, 5)


def gen_pf_hu_push(rng, d=None):
    d = d or rng.choice([10, 15, 20, 25])
    items = [(c, hu_push(d, make_hand_of_class(c, random.Random(1)))) for c in ALL_CLASSES]
    cls = _pick_by_mix(rng, items, None)
    p = dict(items)[cls]
    hand = make_hand_of_class(cls, rng)
    f = norm5({"fold": 100 * (1 - p), "jam": 100 * p})
    # 호출 범위의 핸드를 villain으로
    ok = [c for c in ALL_CLASSES if hu_call(d, make_hand_of_class(c, random.Random(1))) >= .5]
    vh = None
    for _ in range(50):
        vh = make_hand_of_class(rng.choice(ok), rng, exclude=set(hand))
        if not set(vh) & set(hand): break
    board = _run_board(rng, hand, vh)
    H = dict(me="SB", vs="BB", hand=hand, vh=vh, d=d, run=board,
             key=f"{d}BB 이하에서는 레이즈 후 접기가 비싸서 올인 아니면 폴드로 단순해져요. 올인할 핸드는 상대 콜 범위를 상대로 EV로 정해요.",
             pf=[.5, 1, 0, d],
             s=[dict(b=[], a="앞에서 모두 폴드, 히어로 차례", o=JF, f=f, h=f"{d}BB · SB 푸시/폴드 · {cls}", n=_note_jam(p, d, "SB"))])
    H["_line"] = "pushfold"; H["_kind"] = "pf_hu_push"; H["_ptag"] = "SRP"; H["_role"] = "-"; H["_src"] = "own-hu-nash"
    return H


def gen_pf_hu_call(rng, d=None):
    d = d or rng.choice([10, 15, 20, 25])
    items = [(c, hu_call(d, make_hand_of_class(c, random.Random(1)))) for c in ALL_CLASSES]
    cls = _pick_by_mix(rng, items, None)
    p = dict(items)[cls]
    hand = make_hand_of_class(cls, rng)
    f = norm5({"fold": 100 * (1 - p), "call": 100 * p})
    ok = [c for c in ALL_CLASSES if hu_push(d, make_hand_of_class(c, random.Random(1))) >= .5]
    vh = None
    for _ in range(50):
        vh = make_hand_of_class(rng.choice(ok), rng, exclude=set(hand))
        if not set(vh) & set(hand): break
    board = _run_board(rng, hand, vh)
    H = dict(me="BB", vs="SB", hand=hand, vh=vh, d=d, run=board,
             key=f"짧은 스택의 올인에는 팟 오즈가 좋아서 콜 범위가 넓어요. 필요 승률과 상대 올인 범위를 비교해서 정해요.",
             pf=[1, d, 0, d],
             s=[dict(b=[], a=f"빌런 {d}BB 올인", o=JC, f=f, h=f"{d}BB · BB 콜/폴드 · {cls}", n=_note_call(p, d))])
    H["_line"] = "pushfold"; H["_kind"] = "pf_hu_call"; H["_ptag"] = "SRP"; H["_role"] = "-"; H["_src"] = "own-hu-nash"
    return H


def gen_pf10_push(rng):
    pos = rng.choice(["UTG", "UTG+1", "MP", "LJ", "HJ", "CO", "BTN"])
    items = [(c, multi_push10(pos, make_hand_of_class(c, random.Random(1)))) for c in ALL_CLASSES]
    cls = _pick_by_mix(rng, items, None)
    p = dict(items)[cls]
    hand = make_hand_of_class(cls, rng)
    f = norm5({"fold": 100 * (1 - p), "jam": 100 * p})
    # 콜할 가능성이 높은 BB 핸드
    pool = [c for c in ALL_CLASSES if (multi_call10(pos, "BB", make_hand_of_class(c, random.Random(1))) or 0) >= .5]
    vh = None
    for _ in range(50):
        vh = make_hand_of_class(rng.choice(pool or ALL_CLASSES[:20]), rng, exclude=set(hand))
        if not set(vh) & set(hand): break
    board = _run_board(rng, hand, vh)
    H = dict(me=pos, vs="BB", hand=hand, vh=vh, d=10, run=board,
             key="9인 테이블 10BB에서 앞 포지션일수록 올인 범위가 좁고, 뒤로 갈수록 넓어져요. 뒤에 남은 사람 수가 이 핸드의 가치를 정해요.",
             pf=[0, 1, .5, 10],
             s=[dict(b=[], a="앞에서 모두 폴드, 히어로 차례", o=JF, f=f, h=f"10BB · {pos} 푸시/폴드 · {cls}", n=_note_jam(p, 10, pos))])
    H["_line"] = "pushfold"; H["_kind"] = "pf10_push"; H["_ptag"] = "SRP"; H["_role"] = "-"; H["_src"] = "own-pf10"
    return H


def gen_pf10_call(rng):
    ops = ["UTG", "UTG+1", "MP", "LJ", "HJ", "CO", "BTN"]
    opener = rng.choice(ops)
    hero = rng.choice(["BB", "BB", "SB"] if opener != "SB" else ["BB"])
    key_ok = multi_call10(opener, hero, ["A♠", "A♥"])
    if key_ok is None:
        hero = "BB"
    items = [(c, multi_call10(opener, hero, make_hand_of_class(c, random.Random(1)))) for c in ALL_CLASSES]
    cls = _pick_by_mix(rng, items, None)
    p = dict(items)[cls]
    hand = make_hand_of_class(cls, rng)
    f = norm5({"fold": 100 * (1 - p), "call": 100 * p})
    pool = [c for c in ALL_CLASSES if multi_push10(opener, make_hand_of_class(c, random.Random(1))) >= .5]
    vh = None
    for _ in range(50):
        vh = make_hand_of_class(rng.choice(pool), rng, exclude=set(hand))
        if not set(vh) & set(hand): break
    board = _run_board(rng, hand, vh)
    hIn = blind(hero); dead = 1.5 - hIn - (blind(opener))
    # 사이 자리는 모두 폴드, 히어로 SB면 BB가 데드
    H = dict(me=hero, vs=opener, hand=hand, vh=vh, d=10, run=board,
             key="짧은 스택의 올인에는 팟 오즈가 좋아서 콜 범위가 넓어요. 올인한 자리가 앞일수록 상대 범위가 좁고 강해요.",
             pf=[hIn, 10, dead, 10],
             s=[dict(b=[], a=f"{opener} 10BB 올인, 나머지 폴드".replace(opener + " ", "빌런 ", 1), o=JC, f=f, h=f"10BB · {hero}가 {opener} 올인에 대응 · {cls}", n=_note_call(p, 10))])
    H["_line"] = "pushfold"; H["_kind"] = "pf10_call"; H["_ptag"] = "SRP"; H["_role"] = "-"; H["_src"] = "own-pf10"
    return H


# ================= 멀티웨이 (3인 팟) =================
def gen_mw(rng, d=100):
    mode = rng.choice(["btn", "btn", "co", "bb"])
    if mode == "bb":
        hero = "BB"; opener = rng.choice(["UTG", "MP", "HJ", "CO"]); caller = rng.choice([p for p in ["HJ", "CO", "BTN", "SB"] if POS.index(p) > POS.index(opener)])
    else:
        hero = "BTN" if mode == "btn" else "CO"
        opener = rng.choice(["UTG", "UTG+1", "MP", "LJ"] if hero == "BTN" else ["UTG", "MP", "LJ"])
        cands = [p for p in POS[:POS.index(hero)] if POS.index(p) > POS.index(opener)]
        caller = rng.choice(cands)
    allow_trash = rng.random() < .05
    for _ in range(60):
        hand = make_hand_of_class(rng.choice(ALL_CLASSES), rng)
        f = pf_def(hero, opener, hand, d)
        if f["fold"] < 90 or allow_trash: break
    # 멀티웨이: 스퀴즈/3벳은 조금 늘리고 투기적 핸드는 콜 가치 상승
    cls = hand_class(hand)
    sz = 2.5
    if hero == "BB": pf = [1, sz, 1.5 - 1 - blind(opener) - (blind(caller) if caller == "SB" else 0) + (0 if caller != "SB" else 0), 14, sz]
    else: pf = [0, sz, 1.5, 9, sz]
    if hero == "BB":
        dead = 1.5 - 1 - (0 if caller == "SB" else 0)
        dead = .5 if caller != "SB" else 0
        # 호출자가 SB이면 SB 칩(.5)은 빌런2의 투입분에 포함
        pf = [1, sz, dead, 14, sz]
    main = argmax_f(f, ("fold",))
    if f["fold"] >= 90: main = "call"
    lab = "스퀴즈 14BB" if hero == "BB" else "3벳"
    P = dict(line="mw", me=hero, vs=opener, vs2=caller, d=d, hand=hand, pf=pf,
             pre=dict(o=VB(lab), f=f, a=f"빌런1 {n2s(sz)}BB 오픈 → 빌런2 콜, 나머지 폴드",
                      n=note_def(f, cls, opener) + " 멀티웨이라 데드머니가 있어 콜 가격은 더 좋아요.", h=f"{hero} · {opener} 오픈 + {caller} 콜 · {cls}"),
             main=main, ptag="SRP" if main == "call" else "3B", cls=cls, open_to=sz)
    return P


def build_post_mw(rng, P):
    me, D = P["me"], P["d"]; hero = P["hand"]
    hs, vst, pot = sim_pre(P)
    hero_ip = ip(me, P["vs"]) and ip(me, P["vs2"])
    hero_ip_vs = True if hero_ip else False
    init = P["main"] in ("raise", "jam")
    board = deal_board(rng, hero)
    streets = []; tiers = []; agg = 0
    alive = ["빌런1", "빌런2"]
    for i in range(3):
        bd = board[:3 + i]; newc = board[:3] if i == 0 else [board[2 + i]]
        a = analyze(hero, bd); t = tier_of(a, i); bi = board_info(bd); tiers.append(t)
        eq = draw_equity(a, i)
        two = len(alive) == 2
        ctx = dict(ip=hero_ip, paired=bi["paired"], eq=eq, blocker=False, mw=two, oop_init=False)
        r = rng.random()
        if hero_ip:
            kind = "first" if r < (.85 if init else .62) else "face"
        else:
            kind = "face" if r < .72 else "first"
        st = {"b": newc}
        if kind == "first":
            if hero_ip:
                a_txt = "빌런1 체크 → 빌런2 체크" if two else f"{alive[0]} 체크"
            else:
                a_txt = ("히어로 먼저 행동 (두 빌런이 콜)" if (i == 0 and two) else "히어로 먼저 행동")
            small, large = sizes_for(P["ptag"], i, bi["wet"])
            o = HB(small, large)
            bv = bet_vec(t, i, bi["wet"], ctx)
            f = {"check": bv["check"], "b%d" % small: bv["s"], "b%d" % large: bv["l"]}
            note = rng_pick(BET_N.get(t, BET_N["air"]))
            st.update(a=a_txt, o=o, f=f, h=" · ".join([hdesc(a, i), board_desc(bi, i)]), n=note)
            mk = argmax_f(f)
            if mk.startswith("b"):
                am = min(r1(pot * int(mk[1:]) / 100), hs, vst)
                hs = r1(hs - am); vst = r1(vst - am); pot = r1(pot + am * (1 + len(alive)))
        else:
            vp = vil_sizes(P["ptag"], i, bi["wet"], rng)
            amt = min(r1(pot * vp / 100), vst)
            pattern = rng.choice(["bc", "bc", "bf", "cb"] if two else ["b"])
            if not two:
                a_txt = f"{alive[0]} {vp}% 베팅"; paid = amt
            elif pattern == "bc":
                a_txt = f"빌런1 {vp}% 베팅 → 빌런2 콜"; paid = 2 * amt
            elif pattern == "bf":
                a_txt = f"빌런1 {vp}% 베팅 → 빌런2 폴드"; paid = amt
            else:
                a_txt = f"빌런1 체크 → 빌런2 {vp}% 베팅 → 빌런1 폴드"; paid = amt
            if not hero_ip: a_txt = "히어로 체크 → " + a_txt
            agg += 1
            call_amt = min(amt, hs)
            pot_b = r1(pot + paid)
            need = call_amt / (pot_b + call_amt) if (pot_b + call_amt) else 0
            if amt >= hs - .05 or amt >= vst - .05:
                o = FC
                f = allin_call(t, need, EQ_PROXY[t] if not t.startswith("dr_") else max(eq, EQ_PROXY[t] * .6))
            else:
                o = VB("체크레이즈" if (not hero_ip and i == 0) else "레이즈")
                fv = face_vec(t, i, amt / pot if pot else .5, ctx)
                f = {"fold": fv["fold"], "call": fv["call"], "raise": fv["raise"]}
            nkey = t if t not in ("good", "medium") else f"{t}_{i}"
            note = rng_pick(FACE_N.get(nkey, FACE_N["air"]))
            st.update(a=a_txt, o=o, f=f, h=" · ".join([hdesc(a, i), board_desc(bi, i), "필요 승률 약 %d%%" % round(need * 100)]), n=note)
            mk = argmax_f(f)
            if mk == "call":
                hs = r1(hs - call_amt); vst = r1(vst - amt); pot = r1(pot + paid + call_amt)
            elif mk == "raise":
                to = min(r1(amt * 3), hs); hs = r1(hs - to); vst = r1(max(0, vst - to)); pot = r1(pot + paid + to * 2)
            if two:
                if pattern == "bf": alive = ["빌런1"]
                elif pattern == "cb": alive = ["빌런2"]
        streets.append(st)
        if hs <= .05 or vst <= .05: break
    P["role"] = "MW"; P["hero_ip"] = hero_ip
    P["streets"] = streets; P["tiers"] = tiers; P["board"] = board; P["agg"] = agg
    return P


def finish_mw(rng, P):
    hero = P["hand"]; board = P["board"]
    v1 = pick_villain_hand(rng, board, hero, P["vs"], min(P["agg"], 1), "opener")
    used = list(board) + list(hero) + list(v1)
    v2 = None
    for _ in range(100):
        pool = [c for c in DECK if c not in used]
        v2 = rng.sample(pool, 2)
        if vil_range_ok(P["vs2"], v2, "caller"): break
    s = [dict(b=[], a=P["pre"]["a"], o=P["pre"]["o"], f=P["pre"]["f"], h=P["pre"]["h"], n=P["pre"]["n"])]
    for st in P["streets"]:
        s.append(dict(b=st["b"], a=st["a"], o=st["o"], f=st["f"], h=st["h"], n=st["n"]))
    hard = sorted(range(len(P["streets"])), key=lambda i: max(P["streets"][i]["f"].values()))
    tier_main = P["tiers"][hard[0]]
    H = dict(me=P["me"], vs=P["vs"], vs2=P["vs2"], hand=hero, vh=v1, vh2=v2, key=line_key("mw", tier_main, 0), pf=P["pf"], s=s, multi=True)
    if P["d"] != 100: H["d"] = P["d"]
    if len(P["streets"]) < 3: H["run"] = board
    H["_line"] = "mw"; H["_ptag"] = P["ptag"]; H["_role"] = "MW"; H["_kind"] = "mw"
    return H


def gen_mw_hand(rng):
    P = gen_mw(rng)
    if P["main"] == "jam": P["main"] = "raise"
    build_post_mw(rng, P)
    return finish_mw(rng, P)


def gen_any(rng, kind):
    if kind == "pf_hu_push": return gen_pf_hu_push(rng)
    if kind == "pf_hu_call": return gen_pf_hu_call(rng)
    if kind == "pf10_push": return gen_pf10_push(rng)
    if kind == "pf10_call": return gen_pf10_call(rng)
    if kind == "mw": return gen_mw_hand(rng)
    return gen_one(rng, kind)


if __name__ == "__main__":
    rng = random.Random(3)
    for k in ["pf_hu_push", "pf_hu_call", "pf10_push", "pf10_call", "mw"]:
        H = gen_any(rng, k)
        print(json.dumps(H, ensure_ascii=False)[:1400]); print(diff_of(H)); print()
