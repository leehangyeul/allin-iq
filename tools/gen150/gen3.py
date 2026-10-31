# 새 문제 200개 생성기: 자체 계산 푸시/폴드(8·12·15·20BB, 9인) + 헤즈업 + 예시값(규칙) 문제
import sys, json, random, collections, re, os
from gen2 import *
from build150 import valid

HERE = os.path.dirname(os.path.abspath(__file__))
PF2 = os.path.join(HERE, "..", "pf2")
DRK = "AKQJT98765432"
DHL = [(DRK[i] + DRK[i]) if i == j else (DRK[i] + DRK[j] + "s" if i < j else DRK[j] + DRK[i] + "o") for i in range(13) for j in range(13)]
IDX = {c: i for i, c in enumerate(DHL)}
PF = {s: json.load(open(os.path.join(PF2, f"pf_{s}.json"))) for s in (8, 12, 15, 20)}
APP = {"UTG+2": "MP"}           # 계산 파일 이름 → 앱 이름
CALC = {"MP": "UTG+2"}
SEATS = ["UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB", "BB"]


def _cls_hand(rng, cls, exclude=()):
    for _ in range(60):
        h = make_hand_of_class(cls, rng, exclude=set(exclude))
        if not set(h) & set(exclude): return h
    return None


def _pick(rng, freqs, evs):
    """경계(혼합·EV 0 근처) 핸드를 45% 확률로 우선, 나머지는 콤보 수 비율로 고르게"""
    ok = [i for i in range(169) if not ((freqs[i] >= .95 and evs[i] <= 0) or (freqs[i] <= .05 and evs[i] >= 0))]
    edge = [i for i in ok if .05 < freqs[i] < .95 or abs(evs[i]) < .35]
    if edge and rng.random() < .45: return rng.choice(edge)
    # 플레이하는 핸드 절반, 폴드 핸드 절반(트래시 폴드만 쌓이지 않게)
    play = [i for i in ok if freqs[i] >= .5]; fold = [i for i in ok if freqs[i] < .5 and evs[i] > -3]
    return rng.choice(play if (rng.random() < .5 and play) or not fold else fold)


def _ev_txt(ev):
    return f"{ev:+.2f}BB".replace("+", "+")


def note_jam(p, ev, d, pos):
    if p >= .95: return f"{d}BB {pos}에서 이 핸드는 올인이 기본이에요. 계산해 보면 올인이 폴드보다 평균 {ev:+.2f}BB 이득이에요. 뒤에 남은 사람들의 콜 범위를 상대로도 접는 판과 이기는 판이 충분해요."
    if p <= .05: return f"{d}BB {pos}에서 이 핸드로 올인하면 폴드보다 평균 {abs(ev):.2f}BB 손해예요. 뒤에서 콜하는 강한 핸드에 지는 경우가 많아 폴드가 기본이에요."
    return f"{d}BB {pos} 올인 경계에 있는 핸드예요. 올인과 폴드의 EV 차이가 {abs(ev):.2f}BB로 거의 같아서 둘을 섞어 써요."


def note_call(p, ev, d, op):
    if p >= .95: return f"{op}의 {d}BB 올인 범위를 상대로 이 핸드의 승률이 필요 승률보다 높아요. 계산해 보면 콜이 폴드보다 평균 {ev:+.2f}BB 이득이라 콜이 기본이에요."
    if p <= .05: return f"{op}의 {d}BB 올인 범위를 상대로 필요 승률에 못 미쳐요. 콜하면 폴드보다 평균 {abs(ev):.2f}BB 손해라 폴드가 기본이에요."
    return f"{op}의 {d}BB 올인에 콜과 폴드의 EV 차이가 {abs(ev):.2f}BB로 거의 같은 경계 핸드예요. 둘을 섞어 써요."


def gen_pf_push(rng, d=None):
    d = d or rng.choice([8, 12, 15, 20])
    T = PF[d]
    cp = rng.choice(SEATS[:8])
    pos = APP.get(cp, cp)
    i = _pick(rng, T["jam"][cp], T["jam_ev"][cp]); cls = DHL[i]
    p, ev = T["jam"][cp][i], T["jam_ev"][cp][i]
    hand = _cls_hand(rng, cls)
    f = norm5({"fold": 100 * (1 - p), "jam": 100 * p})
    cpool = [DHL[k] for k in range(169) if T["call"][cp + ">BB"][k] >= .5]
    vh = _cls_hand(rng, rng.choice(cpool), hand)
    board = rng.sample([c for c in DECK if c not in hand and c not in vh], 5)
    behind = len(SEATS) - SEATS.index(cp) - 1
    H = dict(me=pos, vs="BB", hand=hand, vh=vh, d=d, run=board, cv=1,
             key=f"{d}BB에서는 레이즈 후 접기가 비싸서 올인 아니면 폴드로 정해요. 뒤에 남은 {behind}명 중 누군가 콜할 확률과, 콜당했을 때의 승률이 올인 범위를 정해요.",
             pf=[blind(pos), 1, 0 if pos == "SB" else .5, d],
             s=[dict(b=[], a="앞에서 모두 폴드, 히어로 차례", o=JF, f=f, h=f"{d}BB · {pos} 푸시/폴드 · {cls}", n=note_jam(p, ev, d, pos))])
    H.update(_line="pushfold", _kind="pf_push", _ptag="SRP", _role="-", _src=f"own-pf{d}")
    return H


def gen_pf_call(rng, d=None):
    d = d or rng.choice([8, 12, 15, 20])
    T = PF[d]
    u = rng.random()
    if u < .5: hero_c = "BB"
    elif u < .7: hero_c = "SB"
    else: hero_c = rng.choice(["UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN"])
    ops = [s for s in SEATS[:SEATS.index(hero_c)]]
    op_c = rng.choice(ops)
    k = op_c + ">" + hero_c
    i = _pick(rng, T["call"][k], T["call_ev"][k]); cls = DHL[i]
    p, ev = T["call"][k][i], T["call_ev"][k][i]
    hand = _cls_hand(rng, cls)
    f = norm5({"fold": 100 * (1 - p), "call": 100 * p})
    jpool = [DHL[q] for q in range(169) if T["jam"][op_c][q] >= .5]
    vh = _cls_hand(rng, rng.choice(jpool), hand)
    board = rng.sample([c for c in DECK if c not in hand and c not in vh], 5)
    hero, op = APP.get(hero_c, hero_c), APP.get(op_c, op_c)
    hIn = blind(hero); dead = 1.5 - hIn - blind(op)
    a = f"빌런 {d}BB 올인, 나머지 폴드" if hero == "BB" else f"빌런 {d}BB 올인, 사이 자리 폴드"
    H = dict(me=hero, vs=op, hand=hand, vh=vh, d=d, run=board, cv=1,
             key=("짧은 스택의 올인에는 팟 오즈가 좋아서 콜 범위가 넓어요. 올인한 자리가 앞일수록 상대 범위가 좁고 강해요." if hero in ("SB", "BB")
                  else "뒤에 아직 행동할 사람이 남아 있어서, 콜은 올인 범위를 이길 만큼 강한 핸드로만 해요. 올인한 자리가 앞일수록 상대 범위가 좁고 강해요."),
             pf=[hIn, d, dead, d],
             s=[dict(b=[], a=a, o=JC, f=f, h=f"{d}BB · {hero}가 {op} 올인에 대응 · {cls}", n=note_call(p, ev, d, op))])
    H.update(_line="pushfold", _kind="pf_call", _ptag="SRP", _role="-", _src=f"own-pf{d}")
    return H


def gen3_any(rng, kind):
    if kind == "pf_push": return gen_pf_push(rng)
    if kind == "pf_call": return gen_pf_call(rng)
    H = gen_any(rng, kind)
    if kind.startswith("pf"): H["cv"] = 1
    return H


# 종류별 (쉬움, 보통, 어려움) — 계산 100 + 예시값 100
PLAN3 = {
    "pf_push": (24, 8, 6), "pf_call": (24, 8, 6), "pf_hu_push": (6, 2, 2), "pf_hu_call": (6, 2, 2), "pf10_push": (2, 1, 0), "pf10_call": (1, 1, 0),
    "short_rfi": (2, 6, 2), "short_def": (2, 6, 2), "short_ipdef": (1, 4, 1),
    "rfi": (2, 9, 3), "def": (2, 10, 5), "ipdef": (2, 8, 3), "vs3b": (1, 6, 0), "mw": (0, 8, 5),
    "rfi_mid": (0, 3, 1), "def_mid": (1, 2, 0), "ipdef_mid": (0, 2, 0),
}
SIT = {"pf_push": "f", "pf_call": "f", "pf_hu_push": "f", "pf_hu_call": "f", "pf10_push": "f", "pf10_call": "f",
       "short_rfi": "o", "rfi": "o", "rfi_mid": "o", "short_def": "b", "def": "b", "def_mid": "b",
       "short_ipdef": "p", "ipdef": "p", "ipdef_mid": "p", "vs3b": "t", "mw": "m"}


def existing_keys(src):
    ks = set(re.findall(r'"([A-Z+0-9]+\|[^"|]{4,6})":"[obptmf]"', src[src.index("const HSIT="):src.index("const HEV=")]))
    return ks


def main(src_path, seed=20261101, banned=()):
    src = open(src_path, encoding="utf-8").read()
    rng = random.Random(seed)
    used = existing_keys(src) | set(banned)
    print("기존 키", len(used))
    used_cls = collections.Counter()
    chosen = []
    for kind, (e, m, h) in PLAN3.items():
        need = {1: e, 2: m, 3: h}
        pool = {1: [], 2: [], 3: []}
        tries = 0
        while any(len(pool[t]) < need[t] * 5 + 3 for t in need if need[t]) and tries < 6000:
            tries += 1
            H = gen3_any(rng, kind)
            if not H or not H.get("vh") or not valid(H): continue
            t, D = diff_of(H)
            pool[t].append(H)
        for t in (1, 2, 3):
            got = 0
            cands = pool[t][:]; rng.shuffle(cands)
            extra = [x for tt in (2, 1, 3) if tt != t for x in pool[tt]]
            for H in cands + extra:
                if got >= need[t]: break
                k = H["me"] + "|" + "".join(H["hand"])
                cls = (H["me"], hand_class(H["hand"]), H.get("d"), H["s"][0]["a"][:12])
                if k in used or used_cls[cls] >= 1: continue
                f0 = H["s"][0]["f"]
                if f0.get("fold", 0) >= 90 and H["_line"] != "pushfold":
                    if sum(1 for c in chosen if c["s"][0]["f"].get("fold", 0) >= 90 and c["_line"] != "pushfold") >= 5: continue
                chosen.append(H); used.add(k); used_cls[cls] += 1; got += 1
            if got < need[t]: print("부족", kind, t, got, "/", need[t], "후보", len(cands))
    return chosen


if __name__ == "__main__":
    bf = os.path.join(HERE, "banned200.json")
    ch = main(sys.argv[1], banned=json.load(open(bf)) if os.path.exists(bf) else ())
    print(len(ch))
    json.dump(ch, open(os.path.join(HERE, "new200.json"), "w"), ensure_ascii=False)
    print(sorted(collections.Counter(diff_of(H)[0] for H in ch).items()))
    print(collections.Counter(H["_kind"] for H in ch))
    print(collections.Counter(H.get("d") for H in ch))
