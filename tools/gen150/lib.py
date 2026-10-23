# 카드·평가·핸드 분석 도구 (앱 코드와 별개, 문제 생성용)
import random, itertools
from collections import Counter

RK = "23456789TJQKA"
SU = "♠♥♦♣"
DECK = [r + s for r in RK for s in SU]
RKO = {"A": "A", "K": "K", "Q": "Q", "J": "J", "T": "10"}


def rk(c): return RK.index(c[0])


def _sh(rs):
    u = sorted(set(rs), reverse=True)
    if 12 in u: u.append(-1)
    run = 1
    for i in range(len(u) - 1):
        if u[i] - u[i + 1] == 1:
            run += 1
            if run >= 5: return u[i + 1] + 4
        else:
            run = 1
    return None


def eval7(cs):
    ranks = [rk(c) for c in cs]
    cnt = Counter(ranks)
    suits = Counter(c[-1] for c in cs)
    fs = [s for s, n in suits.items() if n >= 5]
    fr = []
    if fs:
        fr = [rk(c) for c in cs if c[-1] == fs[0]]
        sh = _sh(fr)
        if sh is not None: return (8, sh)
    g = sorted(((n, r) for r, n in cnt.items()), reverse=True)
    if g[0][0] == 4:
        return (7, g[0][1], max([r for r in cnt if r != g[0][1]], default=-1))
    if g[0][0] == 3 and len(g) > 1 and g[1][0] >= 2:
        return (6, g[0][1], max(r for n, r in g[1:] if n >= 2))
    if fs: return (5, *sorted(fr, reverse=True)[:5])
    sh = _sh(ranks)
    if sh is not None: return (4, sh)
    if g[0][0] == 3:
        return (3, g[0][1], *sorted([r for r in cnt if r != g[0][1]], reverse=True)[:2])
    if g[0][0] == 2 and len(g) > 1 and g[1][0] == 2:
        ps = sorted([r for n, r in g if n == 2], reverse=True)[:2]
        return (2, *ps, max([r for r in cnt if r not in ps], default=-1))
    if g[0][0] == 2:
        p = g[0][1]
        return (1, p, *sorted([r for r in cnt if r != p], reverse=True)[:3])
    return (0, *sorted(ranks, reverse=True)[:5])


def pct_vs_random(hero, board):
    """지금 보드에서 내 핸드가 임의의 상대 핸드를 이기는 비율(남은 카드는 고려하지 않음)"""
    used = set(hero) | set(board)
    deck = [c for c in DECK if c not in used]
    me = eval7(hero + board)
    w = 0.0; n = 0
    for a, b in itertools.combinations(deck, 2):
        o = eval7([a, b] + board)
        n += 1
        if me > o: w += 1
        elif me == o: w += .5
    return w / n


def pct_vs_range(hero, board, frac):
    """상대가 베팅·콜하는 범위(현재 보드에서 가장 강한 frac 비율)를 상대로 내 핸드가 이기는 비율"""
    used = set(hero) | set(board)
    deck = [c for c in DECK if c not in used]
    me = eval7(hero + board)
    ev = [eval7([a, b] + board) for a, b in itertools.combinations(deck, 2)]
    ev.sort(reverse=True)
    top = ev[:max(1, int(len(ev) * frac))]
    w = 0.0
    for o in top:
        if me > o: w += 1
        elif me == o: w += .5
    return w / len(top)


def board_info(board):
    ranks = [rk(c) for c in board]
    sc = Counter(c[-1] for c in board)
    mx = max(sc.values())
    paired = len(set(ranks)) < len(ranks)
    u = sorted(set(ranks))
    span3 = any(u[j + 2] - u[j] <= 4 for j in range(len(u) - 2)) if len(u) >= 3 else False
    close2 = sum(1 for j in range(len(u) - 1) if u[j + 1] - u[j] <= 2)
    wet = (mx >= 2 and (span3 or close2 >= 1)) or span3
    if len(board) >= 4: wet = mx >= 3 or span3 or (mx >= 2 and close2 >= 2)
    return dict(maxsuit=mx, paired=paired, wet=wet, top=max(ranks), mono=(mx >= 3 and len(board) == 3),
                two_tone=(mx == 2), high=RK[max(ranks)], ranks=ranks)


def board_bad(board):
    """보드만으로 스트레이트·플러시·트립스 이상이면 문제로 쓰지 않아요"""
    return eval7(board)[0] >= 3


def analyze(hero, board):
    cat = eval7(hero + board)
    bs = sorted([rk(c) for c in board], reverse=True)
    hr = sorted([rk(c) for c in hero], reverse=True)
    pocket = hr[0] == hr[1]
    made = "high"; kick = None
    if cat[0] == 1:
        p = cat[1]
        if pocket and hr[0] == p:
            made = "overpair" if p > bs[0] else "underpair"
        elif p in hr:
            dist = sorted(set(bs), reverse=True)
            made = "toppair" if p == dist[0] else ("secondpair" if len(dist) > 1 and p == dist[1] else "lowpair")
            kick = [r for r in hr if r != p][0]
    elif cat[0] == 2:
        made = "twopair" if any(p in hr for p in cat[1:3]) else "high"
    elif cat[0] == 3:
        made = "set" if pocket and hr[0] == cat[1] else ("trips" if cat[1] in hr else "high")
    elif cat[0] == 4: made = "straight"
    elif cat[0] == 5: made = "flush"
    elif cat[0] == 6: made = "fullhouse"
    elif cat[0] == 7: made = "quads"
    elif cat[0] == 8: made = "sf"
    # 보드만으로 만든 핸드는 '하이'로 취급 (예: 보드 투페어)
    bcat = eval7(board)
    if made in ("straight", "flush", "fullhouse") and bcat[0] == cat[0] and bcat[1:] == cat[1:]:
        made = "high"
    pct = pct_vs_range(hero, board, {3: .55, 4: .5, 5: .4}[len(board)])
    res = dict(made=made, cat=cat, pct=pct, kick=kick, pocket=pocket, hr=hr, bs=bs,
               overs=sum(1 for r in hr if r > bs[0]), outs=0, fd=None, oesd=False, gut=False, combo=False, bd_fd=False)
    bsc = Counter(c[-1] for c in board)
    res["flush_poss"] = max(bsc.values()) >= 3 and cat[0] < 5
    ub = sorted(set(bs))
    res["str_poss"] = len(board) >= 4 and any(ub[j + 2] - ub[j] <= 4 for j in range(len(ub) - 2)) and cat[0] < 4
    if len(board) < 5:
        used = set(hero) | set(board)
        unseen = [c for c in DECK if c not in used]
        fl_o = set(); st_o = set()
        for c in unseen:
            nb = board + [c]
            c2 = eval7(hero + nb)
            if c2[0] in (4, 5, 8) and cat[0] < 4 and eval7(nb)[0] < 4:
                if c2[0] in (5, 8): fl_o.add(c)
                else: st_o.add(c)
        res["fl_outs"] = len(fl_o); res["st_outs"] = len(st_o)
        res["outs"] = len(fl_o | st_o)
        # 플러시 드로우 넛 여부
        allc = hero + board
        for s in SU:
            n_all = sum(1 for c in allc if c[-1] == s)
            n_h = sum(1 for c in hero if c[-1] == s)
            if n_all == 4 and n_h >= 1 and cat[0] < 5:
                have = {rk(c) for c in allc if c[-1] == s}
                # 넛: 보드에 없는 가장 높은 해당 무늬 카드를 내가 가졌는지
                free = [r for r in range(12, -1, -1) if not any(c[-1] == s and rk(c) == r for c in board)]
                res["fd"] = "nut" if free[0] in {rk(c) for c in hero if c[-1] == s} else "non"
            if len(board) == 3 and n_all == 3 and n_h == 2 and cat[0] < 5:
                res["bd_fd"] = True
        st_cnt = len(st_o)
        res["oesd"] = st_cnt >= 6
        res["gut"] = 3 <= st_cnt < 6
        res["combo"] = bool(fl_o) and bool(st_o)
        res["ntier_draw_outs"] = res["outs"]
    return res


def tier_of(a, street):
    """street: 0=플랍 1=턴 2=리버 → 티어 이름 (monster/strong/good/medium/weak/air/dr_*)"""
    p = a["pct"]; m = a["made"]
    order = ["air", "weak", "medium", "good", "strong", "monster"]
    def cap(t, hi): return order[min(order.index(t), order.index(hi))]
    if m in ("straight", "flush", "fullhouse", "quads", "sf") or p >= .9: base = "monster"
    elif p >= .75: base = "strong"
    elif p >= .58: base = "good"
    elif p >= .4: base = "medium"
    elif p >= .2: base = "weak"
    else: base = "air"
    if m == "toppair":
        k = a["kick"] or 0
        base = "strong" if (k >= 11 and p >= .75) or p >= .9 else cap(base, "good")
        if base == "monster": base = "strong"
    elif m == "overpair": base = cap(base, "strong")
    elif m == "secondpair": base = cap(base, "medium")
    elif m in ("lowpair", "underpair"): base = cap(base, "medium") if p >= .5 else cap(base, "weak")
    elif m == "twopair": base = cap(base, "strong") if p < .9 else base
    elif m == "high": base = cap(base, "medium")
    # 보드가 위험하면(플러시·스트레이트 가능) 최상급으로 보지 않아요
    if a.get("flush_poss") or a.get("str_poss"):
        if m in ("set", "trips", "twopair", "overpair"): base = cap(base, "strong")
        elif m in ("toppair", "secondpair", "lowpair", "underpair"):
            base = cap(base, "medium" if street >= 1 else "good")
    if street < 2 and a["outs"] >= 4 and base in ("weak", "air", "medium", "good"):
        o = a["outs"]
        if o >= 12 or (a["fd"] == "nut" and base in ("weak", "air")) or (o >= 8 and base in ("medium", "good")):
            return "dr_s"
        if o >= 8: return "dr_m"
        if base in ("weak", "air"): return "dr_w"
    return base


def draw_equity(a, street):
    o = a["outs"]
    if street == 0: return max(0, 4 * o - max(0, o - 8)) / 100
    if street == 1: return 2 * o / 100
    return 0


def norm5(v):
    """빈도를 5 단위로 맞추고 합 100"""
    keys = list(v.keys())
    tot = sum(max(0, x) for x in v.values()) or 1
    raw = {k: max(0, v[k]) * 100 / tot for k in keys}
    r5 = {k: int(round(raw[k] / 5.0)) * 5 for k in keys}
    diff = 100 - sum(r5.values())
    if diff:
        # 가장 큰 항목에 맞춰요
        kmax = max(keys, key=lambda k: raw[k])
        r5[kmax] += diff
        if r5[kmax] < 0:
            r5[kmax] = 0
            return norm5(r5)
    return r5


def hand_class(h):
    a, b = sorted(h, key=lambda c: -rk(c))
    if a[0] == b[0]: return a[0] + b[0]
    return a[0] + b[0] + ("s" if a[-1] == b[-1] else "o")


def chen(h):
    import math
    a, b = sorted(h, key=lambda c: -rk(c))
    def pt(c):
        v = {"A": 10, "K": 8, "Q": 7, "J": 6, "T": 5}.get(c[0])
        return v if v else int(c[0]) / 2
    hi, lo = rk(a), rk(b); p = pt(a)
    if hi == lo: return max(5, 2 * p)
    if a[-1] == b[-1]: p += 2
    gap = hi - lo - 1
    p -= {0: 0, 1: 1, 2: 2, 3: 4}.get(gap, 5)
    if gap <= 1 and hi < rk("Q"): p += 1
    return math.ceil(p)


def rand_hand(rng, exclude=()):
    d = [c for c in DECK if c not in exclude]
    return rng.sample(d, 2)


def make_hand_of_class(cls, rng, exclude=()):
    """'AKs' 같은 분류에서 실제 카드 두 장을 뽑아요"""
    r1, r2 = cls[0], cls[1]
    if len(cls) == 2:
        ss = [s for s in SU if r1 + s not in exclude]
        ss = list(itertools.combinations(ss, 2))
        s1, s2 = rng.choice(ss)
        return [r1 + s1, r2 + s2]
    if cls[2] == "s":
        ss = [s for s in SU if r1 + s not in exclude and r2 + s not in exclude]
        s = rng.choice(ss); return [r1 + s, r2 + s]
    pairs = [(a, b) for a in SU for b in SU if a != b and r1 + a not in exclude and r2 + b not in exclude]
    a, b = rng.choice(pairs); return [r1 + a, r2 + b]


ALL_CLASSES = []
for i, a in enumerate("AKQJT98765432"):
    for j, b in enumerate("AKQJT98765432"):
        if i == j: ALL_CLASSES.append(a + b)
        elif j > i: ALL_CLASSES.append(a + b + "s")
        else: ALL_CLASSES.append(b + a + "o")
