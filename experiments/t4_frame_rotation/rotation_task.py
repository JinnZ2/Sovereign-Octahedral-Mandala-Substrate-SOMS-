"""
T4 — Frame-of-reference rotation task, as text
===============================================
Levinson / Brown rotation task rendered for a text-only model. The subject
sees an array from one viewpoint, is rotated 180 degrees, and must say
whether a described array is "the same". The answer depends on the frame:

  relative   (egocentric)   left/right travel with the viewer  -> same words on Table 2 is "same"
  absolute   (allocentric)  west/east fixed                    -> reversed words on Table 2 is "same"
  intrinsic  (object-based) anchored to a fixed landmark       -> reversed words (landmark fixed)

Two-table protocol (Levinson's animals-in-a-row): the array is on Table 1;
the subject turns 180 degrees to Table 2 and must set out "the same"
arrangement. "Same" is ambiguous there, which is the point; a question about
an untouched table has a physically correct answer and tests nothing.

Hypotheses (stated before any run)
  H-corpus   a text model defaults to the relative frame (the corpus's default quotient:
             English left/right usage dominates)
  H-Haun     Haun et al. 2006 PNAS: great apes and prelinguistic children default to a
             place-based (allocentric) frame; egocentric is a cultural override. If the model's
             default follows the "base" frame it would answer absolute; if it follows the
             corpus it answers relative. The overlay reads the corpus default, not the base.

Arms (the only difference is which frame vocabulary the stimulus makes available)
  A  bare        left/right only, no cardinal terms, no landmark
  B  cardinal    the same scene with north/south/east/west stated
  C  landmark    the same scene with a fixed table feature (a candle at one end)
  D  neutral     no frame words at all: positions given as "nearer the window" etc.

Each stimulus has three candidate answer arrays; the scorer maps the model's
same/different verdicts to the frame they imply. A response consistent with
no frame is "mixed". A response is never scored by its explanation, only by
the verdicts.

STATUS: instrument only. No model has been run: this environment has no
model endpoint, and the session that wrote the stimuli has read the
hypotheses, so it cannot be the subject. `runs/constructed.jsonl` exercises
the scorer and every record says constructed: true.

Usage
  python rotation_task.py stimuli [--seed 0] [--n 12]     # print stimuli (JSONL)
  python rotation_task.py prompt <stim_id> <arm>          # one prompt, verbatim
  python rotation_task.py plan --seed 7                   # randomized run order
  python rotation_task.py score RUNS.jsonl                # frame per response + tally
  python rotation_task.py selftest
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OBJECTS = ["a cup", "a book", "a lamp", "a key", "a spoon", "a shell", "a coin", "a stone"]
ARMS = ("A", "B", "C", "D")


def make_stimulus(rng, stim_id):
    objs = rng.sample(OBJECTS, 3)
    # Table 1: viewer faces north; array reads (viewer's left->right) objs[0], objs[1], objs[2],
    # so objs[0] is at the WEST end. The viewer turns 180 degrees to Table 2 and faces south.
    #   relative frame "same": keep left->right  -> objs[0], objs[1], objs[2]   (objs[0] now EAST)
    #   absolute frame "same": keep west->east   -> objs[2], objs[1], objs[0]   from the new viewpoint
    verbatim = list(objs)                          # relative-frame SAME
    reversed_ = list(reversed(objs))               # absolute-frame SAME
    distractor = [objs[1], objs[0], objs[2]]       # neither
    cands = [("verbatim", verbatim), ("reversed", reversed_), ("distractor", distractor)]
    rng.shuffle(cands)
    return {"stim_id": stim_id, "objects": objs, "candidates": [{"label": l, "order": o} for l, o in cands]}


def prompt(stim, arm):
    o = stim["objects"]
    L = []
    if arm == "A":
        L.append(f"You are standing at Table 1. On it, from your left to your right, are {o[0]}, {o[1]}, and {o[2]}.")
        L.append("You turn around to face Table 2, which is directly behind you. Table 2 is empty.")
        L.append("You are asked to set out the same arrangement on Table 2.")
    elif arm == "B":
        L.append(f"You are standing at Table 1, facing north. On it, from your left (west) to your right (east), "
                 f"are {o[0]}, {o[1]}, and {o[2]}.")
        L.append("You turn around to face Table 2, which is directly behind you, so you now face south. Table 2 is empty.")
        L.append("You are asked to set out the same arrangement on Table 2.")
    elif arm == "C":
        L.append(f"You are standing at Table 1. A candle is fixed to the wall at the right-hand end of the room. On the "
                 f"table, from your left to your right, are {o[0]}, {o[1]}, and {o[2]}; {o[2]} is nearest the candle.")
        L.append("You turn around to face Table 2, which is directly behind you. The candle has not moved. Table 2 is empty.")
        L.append("You are asked to set out the same arrangement on Table 2.")
    elif arm == "D":
        L.append(f"On Table 1, nearest the window is {o[0]}, then {o[1]}, then {o[2]} nearest the door.")
        L.append("Table 2 stands between the same window and the same door. Table 2 is empty.")
        L.append("You are asked to set out the same arrangement on Table 2.")
    else:
        raise ValueError(arm)
    L.append("")
    L.append("For each candidate arrangement below, answer whether it is the same arrangement. Answer with the "
             "candidate number and the single word SAME or DIFFERENT, one per line, nothing else.")
    for i, c in enumerate(stim["candidates"], 1):
        co = c["order"]
        if arm == "D":
            L.append(f"{i}. Nearest the window {co[0]}, then {co[1]}, then {co[2]} nearest the door.")
        else:
            L.append(f"{i}. From your left to your right: {co[0]}, {co[1]}, {co[2]}.")
    return "\n".join(L)


# Which candidate a frame calls SAME.
#   arm A/B/C: verbatim words = relative frame; reversed words = absolute (B) or absolute/intrinsic (C).
#   arm D: no viewer-relative wording exists, so only the place-anchored (verbatim) reading is available;
#          D is the floor control. A model that says SAME to "reversed" in D is not using any frame.
FRAME_SAME = {"relative": "verbatim", "absolute": "reversed", "intrinsic": "reversed"}


def score_response(stim, arm, text):
    verdicts = {}
    for line in text.strip().splitlines():
        parts = line.strip().replace(".", " ").split()
        if len(parts) >= 2 and parts[0].isdigit():
            i = int(parts[0]) - 1
            if 0 <= i < len(stim["candidates"]):
                verdicts[stim["candidates"][i]["label"]] = parts[1].upper()
    if set(verdicts) != {"verbatim", "reversed", "distractor"}:
        return {"frame": "unparsed", "verdicts": verdicts}
    if verdicts["distractor"] == "SAME":
        return {"frame": "mixed", "verdicts": verdicts}
    same = sorted(k for k, v in verdicts.items() if v == "SAME")
    if arm == "D":
        return {"frame": "place_anchored" if same == ["verbatim"] else "mixed", "verdicts": verdicts}
    if same == ["verbatim"]:
        return {"frame": "relative", "verdicts": verdicts}
    if same == ["reversed"]:
        return {"frame": "absolute_or_intrinsic" if arm == "C" else "absolute", "verdicts": verdicts}
    return {"frame": "mixed", "verdicts": verdicts}


def load_stimuli(seed=0, n=12):
    rng = random.Random(seed)
    return [make_stimulus(rng, f"rt-{k:02d}") for k in range(n)]


def plan(stimuli, seed=7):
    rng = random.Random(seed)
    rows = [{"stim_id": s["stim_id"], "arm": a} for s in stimuli for a in ARMS]
    rng.shuffle(rows)
    return [{"order_index": i, **r} for i, r in enumerate(rows)]


def score_file(path, stimuli):
    by_id = {s["stim_id"]: s for s in stimuli}
    tally = {a: {} for a in ARMS}
    rows = []
    constructed = False
    for line in open(path):
        if not line.strip():
            continue
        r = json.loads(line)
        constructed |= bool(r.get("constructed"))
        s = by_id[r["stim_id"]]
        sc = score_response(s, r["arm"], r["raw_response"])
        rows.append({**r, **sc})
        tally[r["arm"]][sc["frame"]] = tally[r["arm"]].get(sc["frame"], 0) + 1
    return {"constructed": constructed, "n": len(rows), "tally_by_arm": tally, "rows": rows}


def selftest():
    st = load_stimuli(0, 3)
    s = st[0]
    idx = {c["label"]: i + 1 for i, c in enumerate(s["candidates"])}
    rel = "\n".join(f"{idx[k]} {'SAME' if k == 'verbatim' else 'DIFFERENT'}" for k in idx)
    ab = "\n".join(f"{idx[k]} {'SAME' if k == 'reversed' else 'DIFFERENT'}" for k in idx)
    assert score_response(s, "A", rel)["frame"] == "relative"
    assert score_response(s, "A", ab)["frame"] == "absolute"
    assert score_response(s, "C", ab)["frame"] == "absolute_or_intrinsic"
    assert score_response(s, "D", rel)["frame"] == "place_anchored"
    assert score_response(s, "D", ab)["frame"] == "mixed"
    assert score_response(s, "A", "1 SAME\n2 SAME\n3 SAME")["frame"] == "mixed"
    assert score_response(s, "A", "I think it is the same")["frame"] == "unparsed"
    for a in ARMS:
        p = prompt(s, a)
        assert all(o in p for o in s["objects"]) and "Table 2" in p
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("stimuli"); p.add_argument("--seed", type=int, default=0); p.add_argument("--n", type=int, default=12)
    p = sub.add_parser("prompt"); p.add_argument("stim_id"); p.add_argument("arm", choices=ARMS)
    p = sub.add_parser("plan"); p.add_argument("--seed", type=int, default=7)
    p = sub.add_parser("score"); p.add_argument("runs")
    sub.add_parser("selftest")
    a = ap.parse_args()
    st = load_stimuli(getattr(a, "seed", 0) if a.cmd == "stimuli" else 0, getattr(a, "n", 12) if a.cmd == "stimuli" else 12)
    if a.cmd == "stimuli":
        for s in st:
            print(json.dumps(s))
    elif a.cmd == "prompt":
        s = next(x for x in st if x["stim_id"] == a.stim_id)
        print(prompt(s, a.arm))
    elif a.cmd == "plan":
        for r in plan(st, a.seed):
            print(json.dumps(r))
    elif a.cmd == "score":
        out = score_file(a.runs, st)
        if out["constructed"]:
            print("*** CONSTRUCTED FIXTURE: these are not model responses ***")
        print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    elif a.cmd == "selftest":
        selftest()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
