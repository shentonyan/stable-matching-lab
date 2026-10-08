"""Exhaustive (n=3) or sampled (n>=4) search for profitable misreports.

usage: python experiments/run_manipulation.py N [SAMPLES] [SEED]
"""

from __future__ import annotations

import itertools
import json
import random
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stablematch.explore import scan_profile  # noqa: E402


def _work(args):
    men, women = args
    r = scan_profile([list(x) for x in men], [list(x) for x in women])
    return (r.n_stable, r.men_gain, r.women_gain, r.women_gain_by_truncation, r.n_women_gaining)


def profiles_exhaustive(n):
    perms = list(itertools.permutations(range(n)))
    for combo in itertools.product(perms, repeat=2 * n):
        yield combo[:n], combo[n:]


def profiles_sampled(n, samples, seed):
    rng = random.Random(seed)
    for _ in range(samples):
        def one():
            l = list(range(n))
            rng.shuffle(l)
            return tuple(l)
        yield tuple(one() for _ in range(n)), tuple(one() for _ in range(n))


def main():
    n = int(sys.argv[1])
    samples = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    if samples:
        gen, mode = profiles_sampled(n, samples, seed), f"random sample of {samples} profiles (seed {seed})"
    else:
        gen, mode = profiles_exhaustive(n), "all profiles"

    total = 0
    c = Counter()
    by_stable = Counter()
    by_stable_gain = Counter()
    gaining_women_hist = Counter()
    with Pool() as pool:
        for ns, mg, wg, wt, nw in pool.imap_unordered(_work, gen, chunksize=256):
            total += 1
            c["men_gain"] += mg
            c["women_gain"] += wg
            c["women_gain_by_truncation"] += wt
            c["women_gain_but_unique_stable"] += wg and ns == 1
            c["unique_stable"] += ns == 1
            by_stable[ns] += 1
            by_stable_gain[ns] += wg
            gaining_women_hist[nw] += 1

    out = {
        "n": n,
        "mode": mode,
        "profiles": total,
        **{k: c[k] for k in (
            "unique_stable", "men_gain", "women_gain",
            "women_gain_by_truncation", "women_gain_but_unique_stable")},
        "profiles_by_num_stable": dict(sorted(by_stable.items())),
        "profiles_with_a_gaining_woman_by_num_stable": dict(sorted(by_stable_gain.items())),
        "profiles_by_num_gaining_women": dict(sorted(gaining_women_hist.items())),
    }
    Path(__file__).resolve().parents[1].joinpath("results", f"manipulation_n{n}.json").write_text(
        json.dumps(out, indent=2)
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
