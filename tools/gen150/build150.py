import sys, json, random, collections, re, os
from gen2 import *

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = HERE

# 종류별 (쉬움, 보통, 어려움) 개수 — 새 문제 109개
PLAN = {
    "pf_hu_push": (4, 1, 1), "pf_hu_call": (4, 1, 1), "pf10_push": (2, 1, 0), "pf10_call": (2, 1, 0),
    "short_rfi": (1, 4, 1), "short_def": (1, 4, 1), "short_ipdef": (1, 3, 1),
    "rfi": (3, 9, 3), "def": (3, 13, 3), "ipdef": (2, 9, 2), "vs3b": (1, 6, 3), "mw": (0, 7, 2),
    "rfi_mid": (0, 2, 1), "def_mid": (1, 2, 0), "ipdef_mid": (0, 2, 0),
}
assert sum(sum(v) for v in PLAN.values()) == 109, sum(sum(v) for v in PLAN.values())


def existing_keys():
    """원본 앱의 41개 핸드(me + 카드) — 중복을 피하려고 읽어요"""
    src = open(os.path.join(SCR, "holdem-gto-quiz.html"), encoding="utf-8").read()
    ks = set()
    for m in re.finditer(r'\{(?:d:\d+,)?(?:pf:\[[^\]]*\],)?me:"([A-Z+0-9]+)",vs:"[A-Z+0-9]+",(?:vs2:"[A-Z+0-9]+",)?hand:\["(..)","(..)"\]', src):
        ks.add(m.group(1) + m.group(2) + m.group(3))
    return ks


def valid(H):
    for st in H["s"]:
        keys = [k for k, _ in st["o"]]
        if set(keys) != set(st["f"].keys()): return False
        if sum(st["f"].values()) != 100: return False
        if any((not isinstance(v, int)) or v < 0 for v in st["f"].values()): return False
    cards = list(H["hand"]) + list(H["vh"]) + (H.get("vh2") or [])
    b = [c for st in H["s"] for c in st["b"]]
    if H.get("run"): b = H["run"]
    cards += b
    if len(set(cards)) != len(cards): return False
    return True


def main(seed=2026):
    rng = random.Random(seed)
    ex = existing_keys()
    chosen = []; used_keys = set(ex); used_cls = collections.Counter()
    for kind, (e, m, h) in PLAN.items():
        need = {1: e, 2: m, 3: h}
        pool = {1: [], 2: [], 3: []}
        tries = 0
        while any(len(pool[t]) < need[t] * 6 + 4 for t in need if need[t]) and tries < 4000:
            tries += 1
            H = gen_any(rng, kind)
            if not valid(H): continue
            k = H["me"] + H["hand"][0] + H["hand"][1]
            if k in used_keys: continue
            # 프리플랍 폴드 100% 트래시는 전체에서 소량만
            t, D = diff_of(H)
            pool[t].append((H, D))
        for t in (1, 2, 3):
            cand = pool[t]
            rng.shuffle(cand)
            picked = []
            for H, D in cand:
                if len(picked) >= need[t]: break
                k = H["me"] + H["hand"][0] + H["hand"][1]
                cls = (H["me"], hand_class(H["hand"]))
                if k in used_keys or used_cls[cls] >= 1: continue
                f0 = H["s"][0]["f"]
                if f0.get("fold", 0) >= 90 and H["_line"] not in ("pushfold",):
                    if sum(1 for c in chosen if c["s"][0]["f"].get("fold", 0) >= 90 and c["_line"] != "pushfold") >= 4: continue
                picked.append(H); used_keys.add(k); used_cls[cls] += 1
            if len(picked) < need[t]:
                print("부족", kind, t, len(picked), "/", need[t], "후보", len(cand))
                # 부족분은 인접 난이도에서 보충
                for H, D in sum((pool[x] for x in (2, 1, 3) if x != t), []):
                    if len(picked) >= need[t]: break
                    k = H["me"] + H["hand"][0] + H["hand"][1]
                    if k in used_keys: continue
                    picked.append(H); used_keys.add(k)
            chosen += picked
    return chosen


if __name__ == "__main__":
    ch = main()
    print(len(ch))
    json.dump(ch, open(os.path.join(SCR, "gen150", "new_hands.json"), "w"), ensure_ascii=False)
    C = collections.Counter(diff_of(H)[0] for H in ch); print(sorted(C.items()))
