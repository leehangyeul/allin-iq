# 빈도 규칙(예시 수치) — 솔버 출력이 아니라 포커 상식에 맞춘 규칙 기반 값이에요.
# 10·15·20·25BB 푸시/폴드는 자체 계산(HU 내시, 10BB 다인원 푸시/폴드) 값을 그대로 써요.
import json, math, os
from lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = HERE
PF10 = json.load(open(os.path.join(SCR, "pushfold10.json")))
HU = json.load(open(os.path.join(SCR, "own", "hu_nash.json")))

POS = ["UTG", "UTG+1", "MP", "LJ", "HJ", "CO", "BTN", "SB", "BB"]
POSTFLOP = ["SB", "BB", "UTG", "UTG+1", "MP", "LJ", "HJ", "CO", "BTN"]
PF10POS = {"MP": "UTG+2"}  # pushfold10.json 이름 → 앱 이름


def ip(a, b):
    """a가 b보다 포스트플랍에서 늦게 행동(포지션 있음)?"""
    return POSTFLOP.index(a) > POSTFLOP.index(b)


def blind(p): return {"SB": .5, "BB": 1}.get(p, 0)


# ---------------- 프리플랍 (100BB 기준) ----------------
OPEN_THR = {"UTG": 9, "UTG+1": 8.5, "MP": 8, "LJ": 7, "HJ": 7, "CO": 6, "BTN": 5, "SB": 6}
PAIR_MIN = {"UTG": 6, "UTG+1": 5, "MP": 4, "LJ": 3, "HJ": 2, "CO": 2, "BTN": 2, "SB": 2}


def open_prob(pos, hand):
    """처음 들어가는 자리에서 레이즈할 비율(0~1)"""
    cls = hand_class(hand)
    c = chen(hand)
    if len(cls) == 2:
        r = rk(hand[0])
        pm = PAIR_MIN[pos]
        if r >= pm: return 1.0
        if r == pm - 1: return .5
        return 0.0
    t = OPEN_THR[pos]
    if c >= t: return 1.0
    if c >= t - 1: return .5
    return 0.0


def pf_rfi(pos, hand, d):
    p = open_prob(pos, hand)
    c = chen(hand)
    f = {"fold": 100 * (1 - p), "call": 0, "raise": 100 * p}
    jam = 0
    if d <= 40:
        # 짧은 스택: 약한 에이스·작은 페어는 올인 비중이 늘어요
        share = max(0, (36 - d) / 36)
        cls = hand_class(hand)
        cand = (len(cls) == 2 and rk(hand[0]) <= rk("8")) or (cls[0] == "A" and cls[-1] in "so" and c >= 6)
        if cand and p > 0: jam = 100 * p * min(.7, share)
        f = {"fold": f["fold"], "raise": f["raise"] - jam, "jam": jam}
        return norm5(f)
    return norm5(f)


def pf_def(hero, opener, hand, d=100):
    """BB/SB 또는 포지션 있는 자리에서 오픈에 대응: fold/call/raise(3벳)"""
    cls = hand_class(hand); c = chen(hand)
    bb = hero == "BB"; sb = hero == "SB"
    late = opener in ("CO", "BTN", "SB")
    pr = len(cls) == 2
    top = {"AA": 1, "KK": 1}
    # 3벳 밸류
    if cls in ("AA", "KK", "QQ", "AKs", "AKo"):
        v = {"fold": 0, "call": 15 if cls != "AA" else 5, "raise": 85 if cls != "AA" else 95}
        if cls in ("QQ", "AKo"): v = {"fold": 0, "call": 35, "raise": 65}
        return norm5(v)
    if cls in ("JJ", "TT", "AQs"):
        v = {"fold": 0, "call": 65, "raise": 35}
        if not late: v = {"fold": 0, "call": 80, "raise": 20}
        return norm5(v)
    # 3벳 블러프(A 블로커 수딧)
    bluff = cls in ("A5s", "A4s", "A3s", "A2s") and (late or bb)
    # 콜 기준
    if bb:
        thr = {"UTG": 7, "UTG+1": 6.5, "MP": 6, "LJ": 5.5, "HJ": 5, "CO": 4.5, "BTN": 3.5, "SB": 3}[opener]
    elif sb:
        thr = {"UTG": 9, "UTG+1": 8.5, "MP": 8.5, "LJ": 8, "HJ": 8, "CO": 7.5, "BTN": 7}[opener]
    else:
        thr = {"UTG": 8.5, "UTG+1": 8.5, "MP": 8, "LJ": 7.5, "HJ": 7.5, "CO": 7, "BTN": 6.5}.get(opener, 8)
    call = 0.0
    if pr:
        base = rk(hand[0])
        # 포켓페어는 셋 마이닝 가격이 좋아 대부분 콜(아주 작은 페어만 일부 폴드)
        call = 1.0 if base >= rk("4") else (.75 if (bb or opener not in ("UTG", "UTG+1")) else .5)
    else:
        if c >= thr + 1: call = 1.0
        elif c >= thr: call = .75
        elif c >= thr - 1: call = .4
        else: call = 0.0
    if cls in ("AJs", "ATs", "KQs", "KJs", "QJs", "JTs", "AQo", "KQo", "AJo") and c >= thr and not pr:
        # 강한 브로드웨이: 3벳 일부 섞기
        r3 = .2 if (late or bb) else .1
        call = max(call - r3, 0)
        return norm5({"fold": 100 * max(0, 1 - call - r3), "call": 100 * call, "raise": 100 * r3})
    if bluff:
        return norm5({"fold": 100 * max(0, 1 - call - .3), "call": 100 * call * .7, "raise": 30})
    if sb:
        # SB는 콜보다 3벳 아니면 폴드
        return norm5({"fold": 100 * (1 - call * .6), "call": 100 * call * .6, "raise": 0})
    return norm5({"fold": 100 * (1 - call), "call": 100 * call, "raise": 0})


def pf_vs3b(hero, hand, d=100):
    """내가 오픈했는데 3벳을 맞았을 때: fold/call/raise(4벳)"""
    cls = hand_class(hand)
    t = {
        "AA": (0, 10, 90), "KK": (0, 20, 80), "QQ": (0, 70, 30), "JJ": (10, 85, 5),
        "TT": (20, 80, 0), "99": (30, 70, 0), "88": (40, 60, 0), "77": (55, 45, 0),
        "AKs": (0, 45, 55), "AKo": (0, 60, 40), "AQs": (0, 80, 20), "AJs": (20, 80, 0),
        "KQs": (30, 70, 0), "ATs": (45, 55, 0), "KJs": (45, 55, 0), "QJs": (50, 50, 0),
        "AQo": (40, 60, 0), "A5s": (45, 15, 40), "A4s": (50, 15, 35), "JTs": (50, 50, 0),
        "T9s": (60, 40, 0), "98s": (70, 30, 0), "A9s": (55, 45, 0), "A8s": (65, 35, 0),
        "KTs": (65, 35, 0), "KQo": (75, 25, 0), "AJo": (70, 30, 0), "66": (70, 30, 0),
    }
    if cls in t:
        f, c, r = t[cls]
        return norm5({"fold": f, "call": c, "raise": r})
    return {"fold": 100, "call": 0, "raise": 0}


def pf_short_def(hero, opener, hand, d):
    """짧은 스택(≤40BB)에서 오픈에 대응: fold/call/jam"""
    cls = hand_class(hand); c = chen(hand)
    base = pf_def(hero, opener, hand, 100)
    # 스택이 짧을수록 3벳은 올인으로 합쳐지고 블러프 올인은 A 블로커가 중심
    jam_pct = base.get("raise", 0)
    if d <= 25:
        if cls in ("AA", "KK"): return norm5({"fold": 0, "call": 10, "jam": 90})
        if cls in ("QQ", "AKs"): return norm5({"fold": 0, "call": 30, "jam": 70})
        if cls in ("JJ", "TT", "AKo", "AQs"): return norm5({"fold": 0, "call": 55, "jam": 45})
        if cls in ("A5s", "A4s", "A3s", "A2s"): return norm5({"fold": 40, "call": 15, "jam": 45})
        j = 0
        if cls in ("99", "88", "AJs", "AQo", "KQs"): j = 25
        call = 100 - base["fold"] - j
        return norm5({"fold": base["fold"], "call": max(0, call), "jam": j})
    # 26~40BB: 올인은 프리미엄 위주
    if cls in ("AA", "KK"): return norm5({"fold": 0, "call": 30, "jam": 70})
    if cls in ("QQ", "AKs", "AKo"): return norm5({"fold": 0, "call": 55, "jam": 45})
    j = 15 if cls in ("A5s", "A4s", "JJ", "TT", "AQs") else 0
    return norm5({"fold": base["fold"], "call": max(0, 100 - base["fold"] - j), "jam": j})


# ---------------- 10~25BB 푸시/폴드 (자체 계산) ----------------
def hu_push(d, hand):
    v = HU[str(d)]["push"].get(hand_class(hand), 0)
    return v


def hu_call(d, hand):
    return HU[str(d)]["call"].get(hand_class(hand), 0)


def multi_push10(pos, hand):
    return PF10["jam"][PF10POS.get(pos, pos)].get(hand_class(hand), 0)


def multi_call10(opener, hero, hand):
    k = f"{PF10POS.get(opener, opener)}>{PF10POS.get(hero, hero)}"
    d = PF10["call"].get(k)
    if d is None: return None
    return d.get(hand_class(hand), 0)


# ---------------- 포스트플랍 ----------------
FACE = {  # (폴드, 콜, 레이즈) — 플랍·턴·리버
    "monster": [(0, 50, 50), (0, 45, 55), (0, 40, 60)],
    "strong": [(0, 80, 20), (0, 80, 20), (10, 80, 10)],
    "good": [(5, 85, 10), (20, 75, 5), (35, 65, 0)],
    "medium": [(25, 70, 5), (50, 50, 0), (70, 30, 0)],
    "weak": [(55, 45, 0), (75, 25, 0), (85, 15, 0)],
    "dr_s": [(0, 55, 45), (0, 65, 35), (90, 0, 10)],
    "dr_m": [(20, 70, 10), (40, 60, 0), (90, 0, 10)],
    "dr_w": [(45, 50, 5), (65, 35, 0), (90, 0, 10)],
    "air": [(80, 5, 15), (85, 0, 15), (90, 0, 10)],
}

BET = {  # (체크, 작은 베팅, 큰 베팅)
    "monster": {"dry": (10, 70, 20), "wet": (5, 25, 70), "t": (5, 30, 65), "r": (5, 25, 70)},
    "strong": {"dry": (20, 65, 15), "wet": (15, 25, 60), "t": (30, 25, 45), "r": (45, 30, 25)},
    "good": {"dry": (20, 70, 10), "wet": (30, 30, 40), "t": (45, 30, 25), "r": (60, 30, 10)},
    "medium": {"dry": (55, 40, 5), "wet": (60, 35, 5), "t": (80, 15, 5), "r": (75, 25, 0)},
    "weak": {"dry": (85, 15, 0), "wet": (85, 15, 0), "t": (95, 5, 0), "r": (95, 5, 0)},
    "dr_s": {"dry": (30, 25, 45), "wet": (30, 25, 45), "t": (35, 15, 50), "r": (90, 0, 10)},
    "dr_m": {"dry": (50, 30, 20), "wet": (50, 30, 20), "t": (65, 20, 15), "r": (90, 0, 10)},
    "dr_w": {"dry": (65, 30, 5), "wet": (65, 30, 5), "t": (80, 15, 5), "r": (92, 0, 8)},
    "air": {"dry": (60, 35, 5), "wet": (65, 30, 5), "t": (80, 10, 10), "r": (90, 0, 10)},
}

# 짧은 스택: 체크 / 작은 베팅 / 올인  (SPR 1.2~3.2)
BET_JAM = {
    "monster": (10, 30, 60), "strong": (15, 35, 50), "good": (30, 45, 25), "medium": (55, 35, 10),
    "weak": (85, 15, 0), "dr_s": (25, 25, 50), "dr_m": (45, 35, 20), "dr_w": (65, 30, 5), "air": (65, 25, 10),
}
# 체크 / 올인 (SPR ≤1.2)
BET_CJ = {
    "monster": (5, 95), "strong": (15, 85), "good": (35, 65), "medium": (60, 40), "weak": (85, 15),
    "dr_s": (30, 70), "dr_m": (45, 55), "dr_w": (70, 30), "air": (75, 25),
}
# 폴드 / 콜 / 올인
FACE_JAM = {
    "monster": (0, 30, 70), "strong": (0, 70, 30), "good": (15, 75, 10), "medium": (45, 50, 5),
    "weak": (65, 30, 5), "dr_s": (5, 45, 50), "dr_m": (25, 60, 15), "dr_w": (50, 40, 10), "air": (85, 0, 15),
}
EQ_PROXY = {"monster": .9, "strong": .72, "good": .58, "medium": .42, "weak": .28, "dr_s": .5, "dr_m": .36, "dr_w": .24, "air": .1}


def need_pct(p):
    """베팅 크기 p(팟 대비 비율)일 때 콜에 필요한 승률"""
    return p / (1 + 2 * p)


def face_vec(tier, street, p, ctx):
    """맞은 베팅에 대한 (폴드, 콜, 레이즈). ctx: ip, paired, eq(드로우 승률), blocker, multiway"""
    f, c, r = FACE[tier][street]
    if p <= .4:
        d = min(f, 15); f -= d; c += d
    elif p >= 1.0:
        d = min(c, 20); f += d; c -= d
    elif p >= .7:
        d = min(c, 10); f += d; c -= d
    if ctx.get("paired") and tier in ("good", "medium"):
        d = min(c, 10); f += d; c -= d
    if ctx.get("ip"):
        d = int(r * .3); r -= d; c += d
    if tier.startswith("dr_") and street < 2:
        eq = ctx.get("eq", 0); need = need_pct(p)
        if eq < need - .06:
            d = min(c, 20); f += d; c -= d
        elif eq > need + .06:
            d = min(f, 15); f -= d; c += d
    if tier == "air" and ctx.get("blocker"):
        d = min(f, 15); f -= d; r += d
    if ctx.get("mw"):
        d = r; r = 0; f += d // 2; c += d - d // 2
        if tier in ("good", "medium", "weak"):
            d = min(c, 10); f += d; c -= d
    return norm5({"fold": f, "call": c, "raise": r})


def allin_call(tier, need, eq_override=None):
    eq = EQ_PROXY[tier] if eq_override is None else eq_override
    m = eq - need
    if m >= .15: c = 95
    elif m >= .05: c = 80
    elif m >= -.05: c = 55
    elif m >= -.15: c = 25
    else: c = 5
    return norm5({"fold": 100 - c, "call": c})


def bet_vec(tier, street, wet, ctx):
    k = "t" if street == 1 else "r" if street == 2 else ("wet" if wet else "dry")
    v = BET[tier][k]
    ck, sm, lg = v
    if ctx.get("oop_init") and tier in ("strong", "good") and street >= 1:
        d = min(sm, 5); sm -= d; ck += d
    if tier == "air" and street == 2 and ctx.get("blocker"):
        d = min(ck, 15); ck -= d; lg += d
    if ctx.get("mw"):
        if tier in ("air", "dr_w", "dr_m"):
            ck += sm + lg; sm = lg = 0
        elif tier in ("medium", "good"):
            ck += lg; lg = 0
    return norm5({"check": ck, "s": sm, "l": lg})
