import random, json, sys, math
from lib import *
from rules import *
from texts import *


def r1(x): return math.floor(x * 10 + 0.5) / 10
def n2s(x):
    x = r1(x); return str(int(x)) if x == int(x) else str(x)


# ---- 옵션 세트 (앱의 VB/HB/PO/VJ/... 와 같은 모양) ----
def VB(rl): return [["fold", "폴드"], ["call", "콜"], ["raise", rl]]
def HB(a, b): return [["check", "체크"], ["b%d" % a, "베팅 %d%%" % a], ["b%d" % b, "베팅 %d%%" % b]]
def PO(o): return [["fold", "폴드"], ["raise", "오픈 %sBB" % n2s(o)], ["jam", "올인"]]
def OPEN(o): return [["fold", "폴드"], ["call", "림프"], ["raise", "오픈 %sBB" % n2s(o)]]
VJ = [["fold", "폴드"], ["call", "콜"], ["jam", "올인"]]
FC = [["fold", "폴드"], ["call", "콜"]]
CJ = [["check", "체크"], ["jam", "올인"]]
def HJm(a): return [["check", "체크"], ["b%d" % a, "베팅 %d%%" % a], ["jam", "올인"]]
def OVB(a): return [["check", "체크"], ["b%d" % a, "베팅 %d%%" % a], ["b125", "오버벳 125%"]]
JF = [["fold", "폴드"], ["jam", "올인"]]
JC = [["fold", "폴드"], ["call", "콜"]]


def hdesc(a, street):
    parts = []
    m = a["made"]
    if m == "high":
        parts.append({2: "오버카드 두 장", 1: "오버카드 한 장"}.get(a["overs"], "하이카드"))
    else:
        base = MADE_KO[m]
        if m == "toppair":
            base += " 좋은 키커" if a["kick"] is not None and a["kick"] >= 8 else " 약한 키커"
        parts.append(base)
    if street < 2:
        dr = []
        if a.get("fd") == "nut": dr.append("넛 플러시 드로우")
        elif a.get("fd") == "non": dr.append("플러시 드로우")
        if a.get("oesd"): dr.append("오픈엔드")
        elif a.get("gut"): dr.append("거트샷")
        if dr and a["outs"] >= 4: parts.append(" + ".join(dr) + " · 아웃츠 %d장" % a["outs"])
        elif a.get("bd_fd") and not dr: parts.append("백도어 플러시 드로우")
    return " · ".join(parts)


def argmax_f(f, avoid=("fold",)):
    if f.get("fold", 0) >= 50:
        for k in ("call", "check"):
            if k in f: return k
    ks = [k for k in f if k not in avoid] or list(f.keys())
    return max(ks, key=lambda k: f[k])


# =================== 프리플랍 구성 ===================
def pick_class(rng, weights_fn):
    ws = [weights_fn(c) for c in ALL_CLASSES]
    return rng.choices(ALL_CLASSES, weights=ws)[0]


def note_open(pos, p, jam):
    if p >= .95:
        s = rng_pick([f"{pos}에서 열 수 있는 핸드예요. 오픈이 기본이에요.", f"{pos} 오픈 레인지 안에 들어가는 핸드예요. 레이즈로 주도권을 잡아요."])
    elif p >= .4:
        s = f"{pos} 오픈 레인지의 경계에 있는 핸드예요. 폴드와 오픈을 반반 섞어요."
    else:
        s = f"{pos}에서는 열기엔 약한 핸드예요. 폴드가 기본이에요."
    if jam: s += " 스택이 짧아서 일부는 올인으로 열어요."
    return s


_pick_seed = [0]
def rng_pick(seq):
    _pick_seed[0] += 1
    return seq[_pick_seed[0] % len(seq)]


def note_def(f, cls, opener):
    r = f.get("raise", 0) + f.get("jam", 0); c = f.get("call", 0); fo = f["fold"]
    pair = len(cls) == 2; suited = len(cls) == 3 and cls[2] == "s"
    if r >= 60: return "강한 핸드라 3벳으로 팟을 키워요. 콜만 하면 상대 레인지에서 받을 값이 줄어요."
    if cls in ("A5s", "A4s", "A3s", "A2s") and r > 0: return "A 블로커가 상대의 강한 에이스를 줄여 줘서 3벳 블러프를 가끔 섞어요."
    if r >= 15 and c >= 40: return "콜이 기본이지만 3벳도 섞어서 콜 레인지가 너무 약해지지 않게 해요."
    if c >= 60 and pair: return "포켓페어는 가격이 좋아 콜로 셋을 노려요. 맞추면 큰 팟을 이길 수 있어요."
    if c >= 60 and suited: return "수딧 핸드는 드로우와 페어를 모두 만들 수 있어 콜이 좋아요."
    if c >= 60: return "필요 승률이 낮아 콜로 싸게 플랍을 봐요."
    if fo >= 85: return f"{opener} 오픈 레인지를 상대로는 약한 핸드예요. 폴드가 기본이에요."
    return f"{opener} 오픈 레인지가 강한 편이라 이 핸드는 콜과 폴드를 섞어요."


def note_vs3b(f, cls):
    if f.get("raise", 0) >= 60: return "3벳을 한 사람의 레인지에서도 앞서는 핸드라 4벳으로 팟을 키워요."
    if cls in ("A5s", "A4s") and f.get("raise", 0) > 0: return "A 블로커로 상대의 AA·AK 조합을 줄이고 폴드 에퀴티를 노려 가끔 4벳 블러프를 섞어요."
    if f.get("raise", 0) >= 20: return "콜이 기본이지만 4벳도 섞어 상대가 3벳을 쉽게 하지 못하게 해요."
    if f["call"] >= 60: return "포지션이나 핸드 질이 좋아 콜로 플랍을 봐요. 4벳하면 강한 핸드에게만 지는 경우가 많아요."
    if f["fold"] >= 85: return "3벳 레인지를 상대로는 약해서 접는 게 기본이에요."
    return "3벳을 맞은 뒤에는 이 핸드를 콜과 폴드로 섞어서 써요."


def pre_pos_text(pos): return pos


# ---- 프리플랍 문제 만들기 ----
def P_rfi(rng, d=100, pos=None, vs=None, tough=False):
    pos = pos or rng.choice(["UTG", "UTG+1", "MP", "LJ", "HJ", "CO", "BTN", "SB"])
    wt = (lambda c: 10 if open_prob(pos, make_hand_of_class(c, random.Random(1))) >= .5 else .3) if not tough else (lambda c: 1)
    cls = pick_class(rng, wt)
    hand = make_hand_of_class(cls, rng)
    sz = 3 if pos == "SB" else (2.2 if d <= 30 else 2.5)
    vs = vs or ("BB" if pos != "SB" and rng.random() > .12 else ("SB" if pos != "SB" else "BB"))
    if pos == "SB": vs = "BB"
    hIn = blind(pos); vIn = blind(vs); dead = 1.5 - hIn - vIn
    f = pf_rfi(pos, hand, d)
    jam = f.get("jam", 0)
    o = PO(sz) if d <= 40 else OPEN(sz)
    if d > 40: f = {"fold": f["fold"], "call": 0, "raise": f["raise"]}
    p = (f["raise"] + f.get("jam", 0)) / 100
    return dict(line="rfi", me=pos, vs=vs, d=d, hand=hand, pf=[hIn, vIn, dead, sz],
                pre=dict(o=o, f=f, a="앞에서 모두 폴드, 히어로 차례", n=note_open(pos, p, jam > 0),
                         h=f"{pos} · {hand_class(hand)}"),
                main="raise", ptag="SRP", cls=cls, open_to=sz)


def P_def(rng, d=100, hero=None, opener=None):
    hero = hero or ("BB" if rng.random() < .8 else "SB")
    if hero == "BB": opener = opener or rng.choice(["UTG", "UTG+1", "MP", "LJ", "HJ", "CO", "BTN", "BTN", "SB"])
    else: opener = opener or rng.choice(["UTG", "MP", "HJ", "CO", "BTN", "BTN"])
    hand = None
    allow_trash = rng.random() < .05
    for _ in range(60):
        cls = rng.choice(ALL_CLASSES)
        hand = make_hand_of_class(cls, rng)
        f = pf_def(hero, opener, hand, d) if d > 40 else pf_short_def(hero, opener, hand, d)
        if f["fold"] < 90 or allow_trash: break
    sz = 3 if opener == "SB" else (2.2 if d <= 30 else 2.5)
    hIn = blind(hero); vIn = sz
    dead = 1.5 - blind(hero) - blind(opener)
    thr = 11 if hero == "BB" else 10
    if opener == "SB": thr = 11
    key = "jam" if d <= 40 else "raise"
    o = VJ if d <= 40 else VB("3벳")
    main = argmax_f(f, ("fold",))
    if f["fold"] >= 90: main = "call"
    return dict(line="def" if d > 40 else "short", me=hero, vs=opener, d=d, hand=hand,
                pf=[hIn, vIn, dead, thr],
                pre=dict(o=o, f=f, a=f"빌런 {n2s(sz)}BB 오픈, 나머지 폴드", n=note_def(f, hand_class(hand), opener),
                         h=f"{hero} vs {opener} 오픈 · {hand_class(hand)}"),
                main=main, ptag="SRP" if main == "call" else "3B", cls=hand_class(hand), open_to=sz)


def P_ipdef(rng, d=100, hero=None, opener=None):
    hero = hero or rng.choice(["LJ", "HJ", "HJ", "CO", "CO", "BTN", "BTN"])
    cand = {"LJ": ["UTG", "UTG+1", "MP"], "HJ": ["UTG", "UTG+1", "MP", "LJ"], "CO": ["UTG", "UTG+1", "MP", "LJ", "HJ"], "BTN": ["UTG", "MP", "LJ", "HJ", "CO"]}
    opener = opener or rng.choice(cand[hero])
    allow_trash = rng.random() < .05
    for _ in range(60):
        hand = make_hand_of_class(rng.choice(ALL_CLASSES), rng)
        f = pf_def(hero, opener, hand, d) if d > 40 else pf_short_def(hero, opener, hand, d)
        if f["fold"] < 90 or allow_trash: break
    sz = 2.2 if d <= 30 else 2.5
    thr = 9 if hero == "BTN" else 8
    dead = 1.5
    main = argmax_f(f, ("fold",))
    if f["fold"] >= 90: main = "call"
    o = VJ if d <= 40 else VB("3벳")
    return dict(line="ipdef" if d > 40 else "short", me=hero, vs=opener, d=d, hand=hand, pf=[0, sz, dead, thr],
                pre=dict(o=o, f=f, a=f"빌런 {n2s(sz)}BB 오픈, 나머지 폴드", n=note_def(f, hand_class(hand), opener),
                         h=f"{hero} vs {opener} 오픈 · {hand_class(hand)}"),
                main=main, ptag="SRP" if main == "call" else "3B", cls=hand_class(hand), open_to=sz)


def P_vs3b(rng, d=100, hero=None, villain=None):
    hero = hero or rng.choice(["UTG", "UTG+1", "MP", "LJ", "HJ", "CO", "BTN"])
    later = {"UTG": ["MP", "HJ", "CO", "BTN", "SB", "BB"], "UTG+1": ["MP", "HJ", "CO", "BTN", "SB", "BB"], "MP": ["HJ", "CO", "BTN", "SB", "BB"], "LJ": ["HJ", "CO", "BTN", "SB", "BB"], "HJ": ["CO", "BTN", "SB", "BB"],
             "CO": ["BTN", "SB", "BB"], "BTN": ["SB", "BB"]}
    villain = villain or rng.choice(later[hero])
    hand = None
    allow_fold = rng.random() < .12
    for _ in range(80):
        cls = pick_class(rng, lambda c: 1)
        hand = make_hand_of_class(cls, rng)
        if open_prob(hero, hand) >= .5 and (allow_fold or pf_vs3b(hero, hand, d)["fold"] < 100): break
    f = pf_vs3b(hero, hand, d)
    sz3 = 11 if villain == "BB" else (10 if villain == "SB" else 8)
    sz4 = 25 if sz3 >= 10 else 22
    dead = 1.5 - blind(villain)
    main = argmax_f(f, ("fold",))
    if f["fold"] >= 90: main = "call"
    return dict(line="vs3b", me=hero, vs=villain, d=d, hand=hand, pf=[2.5, sz3, dead, sz4],
                pre=dict(o=VB("4벳"), f=f, a=f"히어로 2.5BB 오픈 → 빌런 3벳 {n2s(sz3)}BB", n=note_vs3b(f, hand_class(hand)),
                         h=f"{hero} 오픈 후 {villain} 3벳 · {hand_class(hand)}"),
                main=main, ptag="3B" if main == "call" else "4B", cls=hand_class(hand), open_to=2.5)


# =================== 포스트플랍 ===================
def sizes_for(ptag, i, wet):
    if ptag == "SRP":
        return {0: (50, 75) if wet else (33, 66), 1: (50, 75), 2: (50, 75)}[i]
    return {0: (33, 66) if wet else (25, 50), 1: (33, 66), 2: (50, 75)}[i]


def vil_sizes(ptag, i, wet, rng):
    if i == 0: ch = [50, 66] if wet else [25, 33, 33, 50]
    elif i == 1: ch = [50, 66, 75]
    else: ch = [50, 66, 75, 75, 100]
    if ptag != "SRP" and i == 0: ch = [25, 33, 50]
    return rng.choice(ch)


def role_of(P):
    me, vs = P["me"], P["vs"]
    hero_ip = ip(me, vs)
    init = P["main"] in ("raise", "jam") if P["line"] in ("rfi",) else (P["main"] in ("raise", "jam"))
    if P["line"] == "rfi": init = True
    if P["line"] in ("def", "ipdef", "short"):
        init = P["main"] in ("raise", "jam")
    if P["line"] == "vs3b":
        init = P["main"] in ("raise", "jam")
    # 3벳을 한 쪽이 주도권
    if P["line"] in ("def", "ipdef", "short") and P["main"] in ("raise", "jam"): init = True
    if P["line"] == "vs3b" and P["main"] == "call": init = False
    if P["line"] == "vs3b" and P["main"] == "raise": init = True
    if hero_ip and init: return "F1", hero_ip
    if (not hero_ip) and init: return "F3", hero_ip
    if (not hero_ip) and (not init): return "F2", hero_ip
    return "F4", hero_ip


def sim_pre(P):
    D = P["d"]; hIn, vIn, dead, to = P["pf"][:4]; v2 = P["pf"][4] if len(P["pf"]) > 4 else 0
    hs = D - hIn; vst = D - vIn
    pot = hIn + vIn + v2 + dead
    m = P["main"]
    if m in ("raise", "jam"):
        t = r1(hs + hIn) if m == "jam" else min(to, r1(hs + hIn))
        hs = r1(hs - (t - hIn)); pot = r1(pot + (t - hIn))
        pay = min(r1(t - vIn), vst); vst = r1(vst - pay); pot = r1(pot + pay)
        if v2:
            pot = r1(pot + (t - v2))
    elif m == "call":
        c = r1(vIn - hIn)
        hs = r1(hs - c); pot = r1(pot + c)
    return hs, vst, pot


def deal_board(rng, hero, banned=()):
    for _ in range(200):
        d = [c for c in DECK if c not in hero and c not in banned]
        b = rng.sample(d, 5)
        if not (board_bad(b[:3]) or board_bad(b[:4]) or board_bad(b)):
            return b
    return b


def vil_range_ok(pos, cards, mode):
    c = chen(cards); cls = hand_class(cards)
    if mode == "caller": return c >= 4 or (len(cls) == 2)
    thr = OPEN_THR.get(pos, 5)
    return c >= thr - 1 or (len(cls) == 2 and rk(cards[0]) >= 2)


def pick_villain_hand(rng, board, hero, pos, agg, mode):
    used = set(hero) | set(board)
    deck = [c for c in DECK if c not in used]
    want = rng.random()
    for tries in range(400):
        h = rng.sample(deck, 2)
        if tries < 300 and not vil_range_ok(pos, h, mode): continue
        p = pct_vs_random(h, board)
        if agg >= 2:
            ok = p >= .75 if want < .78 else p < .3
        elif agg == 1:
            ok = .35 <= p <= .92
        else:
            ok = .15 <= p <= .75
        if ok or tries >= 350: return h
    return h


def build_post(rng, P, nstreets=3):
    me, vs, D = P["me"], P["vs"], P["d"]
    hero = P["hand"]
    role, hero_ip = role_of(P)
    hs, vst, pot = sim_pre(P)
    board = deal_board(rng, hero)
    ptag = P["ptag"]
    streets = []; tiers = []; agg = 0
    ended = False
    pre_tag = {"SRP": "%s가 콜" % vs, "3B": "3벳에 콜", "4B": "4벳에 콜"}[ptag]
    pre_tag_f3 = {"SRP": "빌런 콜", "3B": "3벳 팟, 빌런 콜", "4B": "4벳 팟, 빌런 콜"}[ptag]
    for i in range(nstreets):
        bd = board[:3 + i]
        newc = board[:3] if i == 0 else [board[2 + i]]
        a = analyze(hero, bd)
        t = tier_of(a, i)
        bi = board_info(bd)
        tiers.append(t)
        spr = hs / pot if pot > 0 else 99
        eq = draw_equity(a, i)
        blk = False
        # 블로커: 3장 이상 무늬 보드에서 내가 해당 무늬 A를 가졌거나, 보드에 A가 있고 내가 A를 가짐
        for s in SU:
            if sum(1 for c in bd if c[-1] == s) >= 3 and ("A" + s) in hero: blk = True
        if bi["top"] == rk("A") * 0 + 12 and any(c[0] == "A" for c in hero) and t == "air": pass
        # --- 이 스트리트에서 누가 먼저 행동? ---
        if role == "F1":
            lead = (i >= 1 and rng.random() < (.12 if i == 1 else .16))
            kind = "face" if lead else "first"
        elif role == "F3":
            kind = "first"
        elif role == "F2":
            kind = "face"
        else:  # F4
            pb = {0: .78, 1: .62, 2: .55}[i]
            kind = "face" if rng.random() < pb else "first"
        if D <= 40 and role == "F2": kind = "face"
        vp = vil_sizes(ptag, i, bi["wet"], rng) if kind == "face" else None
        st = {"b": newc if i else newc}
        if kind == "first":
            if role == "F1": a_txt = (f"빌런 체크 ({pre_tag})" if i == 0 else "빌런 체크")
            elif role == "F3": a_txt = (f"히어로 먼저 행동 ({pre_tag_f3})" if i == 0 else "히어로 먼저 행동")
            else: a_txt = "빌런 체크"
            small, large = sizes_for(ptag, i, bi["wet"])
            amt_s = r1(pot * small / 100)
            ctx = dict(oop_init=(not hero_ip), blocker=blk, mw=False)
            if spr <= 1.2 or amt_s >= hs:
                o = CJ
                ck, jm = BET_CJ[t]
                if t == "air" and i == 2 and not blk: ck, jm = 90, 10
                f = norm5({"check": ck, "jam": jm})
            elif spr <= 3.2:
                sm = 33 if i == 0 else 50
                o = HJm(sm)
                ck, s_, jm = BET_JAM[t]
                if i == 2 and t == "air" and not blk: ck, s_, jm = 85, 10, 5
                f = norm5({"check": ck, "b%d" % sm: s_, "jam": jm})
            else:
                o = HB(small, large)
                bv = bet_vec(t, i, bi["wet"], ctx)
                f = {"check": bv["check"], "b%d" % small: bv["s"], "b%d" % large: bv["l"]}
                if i == 2 and t == "monster" and a["pct"] >= .985 and rng.random() < .5:
                    o = OVB(75)
                    f = norm5({"check": 5, "b75": 35, "b125": 60})
            note = rng_pick(BET_N.get(t, BET_N["air"]))
            hh = [hdesc(a, i), board_desc(bi, i)]
            st.update(a=a_txt, o=o, f=f, h=" · ".join(hh), n=note)
            # 시뮬레이션: 주 행동
            mk = argmax_f(f, ("fold",))
            if mk == "jam":
                hs_pay = hs; vst_pay = min(vst, hs)
                pot = r1(pot + hs_pay + vst_pay); hs = 0; vst = r1(vst - vst_pay)
            elif mk.startswith("b"):
                pctb = int(mk[1:]); am = min(r1(pot * pctb / 100), hs, vst)
                hs = r1(hs - am); vst = r1(vst - am); pot = r1(pot + 2 * am)
            if mk.startswith("b") or mk == "jam": agg += 0
        else:
            amt = min(r1(pot * vp / 100), vst)
            v_all = vst <= amt + .05
            call_amt = min(amt, hs)
            hero_all = amt >= hs
            if v_all or hero_all:
                a_txt = "빌런 올인"
                amt = min(vst, vst)
            else:
                a_txt = f"빌런 {vp}% 베팅"
            if role == "F2":
                a_txt = "히어로 체크 → " + a_txt
            agg += 1
            pot_b = r1(pot + amt)
            need = call_amt / (pot_b + call_amt) if (pot_b + call_amt) else 0
            rem = hs - call_amt
            ctx = dict(ip=hero_ip, paired=bi["paired"], eq=eq, blocker=blk, mw=False)
            if v_all or hero_all:
                o = FC
                eqo = EQ_PROXY[t] if t not in ("dr_s", "dr_m", "dr_w") else (eq if i < 2 else .1)
                if t in ("dr_s", "dr_m", "dr_w"): eqo = max(eq, EQ_PROXY[t] * .6)
                f = allin_call(t, need, eqo)
            else:
                spr_a = rem / (pot + 2 * amt) if (pot + 2 * amt) else 99
                if spr_a <= 1.0:
                    o = VJ
                    fo, cl, jm = FACE_JAM[t]
                    if t.startswith("dr_") and i < 2:
                        if eq < need - .06: d_ = min(cl, 20); fo += d_; cl -= d_
                    if t == "air" and i == 2 and not blk: fo, cl, jm = 92, 0, 8
                    f = norm5({"fold": fo, "call": cl, "jam": jm})
                else:
                    o = VB("체크레이즈" if (role == "F2" and i == 0) else "레이즈")
                    fv = face_vec(t, i, amt / pot if pot else .5, ctx)
                    f = {"fold": fv["fold"], "call": fv["call"], "raise": fv["raise"]}
            nkey = t
            if t in ("good", "medium"): nkey = f"{t}_{i}"
            note = rng_pick(FACE_N.get(nkey, FACE_N["air"]))
            hh = [hdesc(a, i), board_desc(bi, i), "필요 승률 약 %d%%" % round(need * 100)]
            st.update(a=a_txt, o=o, f=f, h=" · ".join(hh), n=note)
            mk = argmax_f(f, ("fold",))
            if mk == "call":
                hs = r1(hs - call_amt); vst = r1(vst - amt); pot = r1(pot + amt + call_amt)
            elif mk in ("raise", "jam"):
                to = hs if mk == "jam" else min(r1(amt * 3), hs)
                hs = r1(hs - to); vst = r1(max(0, vst - to)); pot = r1(pot + amt + to + (to - amt if to > amt else 0))
            else:
                pass
        streets.append(st)
        if hs <= 0.05 or vst <= 0.05:
            ended = True; break
    P["role"] = role; P["hero_ip"] = hero_ip
    P["streets"] = streets; P["tiers"] = tiers; P["board"] = board; P["agg"] = agg; P["ended"] = ended
    return P


def finish_hand(rng, P, mode="opener"):
    """villain 핸드와 최종 dict 구성"""
    hero = P["hand"]; board = P["board"]
    vmode = "caller" if (P["line"] == "rfi" or P["main"] in ("raise", "jam") and P["line"] != "vs3b") else "opener"
    if P["line"] == "vs3b": vmode = "opener"
    vh = pick_villain_hand(rng, board, hero, P["vs"], P["agg"], vmode)
    s = [dict(b=[], a=P["pre"]["a"], o=P["pre"]["o"], f=P["pre"]["f"], h=P["pre"]["h"], n=P["pre"]["n"])]
    for st in P["streets"]:
        s.append(dict(b=st["b"], a=st["a"], o=st["o"], f=st["f"], h=st["h"], n=st["n"]))
    hard = sorted(range(len(P["streets"])), key=lambda i: max(P["streets"][i]["f"].values()))
    tier_main = P["tiers"][hard[0]] if P["tiers"] else "air"
    key = line_key(P["line"] if P["line"] in LINE_KEY else "rfi", tier_main, 0)
    H = dict(me=P["me"], vs=P["vs"], hand=hero, vh=vh, key=key, pf=P["pf"], s=s)
    if P["d"] != 100: H["d"] = P["d"]
    if len(P["streets"]) < 3: H["run"] = board
    H["_line"] = P["line"]; H["_ptag"] = P["ptag"]; H["_role"] = P["role"]
    return H


def hdec_t(f):
    m = max(f.values())
    return 1 if m >= 85 else 2 if m >= 60 else 3


def diff_of(H):
    ts = [hdec_t(st["f"]) for st in H["s"]]
    D = sum(ts) / len(ts) + (.3 if H.get("multi") else 0)
    return 1 if D < 1.6 else 2 if D <= 2.2 else 3, D


def gen_one(rng, kind):
    if kind == "rfi": P = P_rfi(rng)
    elif kind == "rfi_mid": P = P_rfi(rng, d=rng.choice([60, 75]))
    elif kind == "def": P = P_def(rng)
    elif kind == "def_mid": P = P_def(rng, d=rng.choice([60, 75]))
    elif kind == "ipdef": P = P_ipdef(rng)
    elif kind == "ipdef_mid": P = P_ipdef(rng, d=rng.choice([60, 75]))
    elif kind == "vs3b": P = P_vs3b(rng)
    elif kind == "vs3b_mid": P = P_vs3b(rng, d=rng.choice([60, 75]))
    elif kind == "short_rfi": P = P_rfi(rng, d=rng.choice([20, 25, 30, 35, 40]))
    elif kind == "short_def": P = P_def(rng, d=rng.choice([20, 25, 30, 35, 40]))
    elif kind == "short_ipdef": P = P_ipdef(rng, d=rng.choice([20, 25, 30, 35, 40]))
    else: raise ValueError(kind)
    if P["main"] == "jam":
        P["main"] = "raise"
    build_post(rng, P)
    H = finish_hand(rng, P)
    H["_kind"] = kind
    return H


if __name__ == "__main__":
    rng = random.Random(1)
    for k in ["rfi", "def", "ipdef", "vs3b", "short_def"]:
        H = gen_one(rng, k)
        print(json.dumps(H, ensure_ascii=False)[:1500]); print(diff_of(H))
