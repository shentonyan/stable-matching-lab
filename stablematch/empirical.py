"""Descriptive audit of the original Columbia speed-dating encounter graph.

No imputation of unobserved encounters, inferred preference rankings or causal
claims. Only aggregate cohort statistics are returned. Decisions are used as
recorded, never as counterfactual outcomes for people who did not meet.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
import csv

import numpy as np


def _integer(value):
    try:
        number = float(value)
        if np.isfinite(number) and number.is_integer():
            return int(number)
    except (ValueError, TypeError):
        pass
    return None


def _binary(value):
    number = _integer(value)
    return number if number in (0, 1) else None


def maximum_cardinality(edges):
    """Maximum one-to-one matching count on a binary observed yes graph.

    This is a combinatorial feasibility bound, not a stable outcome or a
    reconstruction of actual relationships; the data supply no strict ranks.
    """
    adjacency = defaultdict(list)
    for left, right in sorted(set(edges)):
        adjacency[left].append(right)
    holder = {}

    def augment(left, visited):
        for right in adjacency[left]:
            if right in visited:
                continue
            visited.add(right)
            if right not in holder or augment(holder[right], visited):
                holder[right] = left
                return True
        return False

    return sum(augment(left, set()) for left in sorted(adjacency))


def audit_rows(rows, bootstrap_draws=2000, seed=20261021):
    if (not isinstance(bootstrap_draws, (int, np.integer)) or isinstance(bootstrap_draws, bool)
            or bootstrap_draws < 0):
        raise ValueError("bootstrap_draws must be a nonnegative integer")
    rows = list(rows)
    required = {"iid", "pid", "wave", "gender", "dec", "dec_o", "match"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("need original iid/pid/wave/gender/dec/dec_o/match columns")
    profiles = {}
    for row in rows:
        wave, iid, gender = (_integer(row.get(k)) for k in ("wave", "iid", "gender"))
        if wave is None or iid is None or gender not in (0, 1):
            continue
        key = (wave, iid)
        if key in profiles and profiles[key] != gender:
            raise ValueError("participant has conflicting side labels within a wave")
        profiles[key] = gender
    encounters = defaultdict(lambda: defaultdict(list))
    excluded = 0
    for row in rows:
        wave, iid, pid, gender = (_integer(row.get(k)) for k in ("wave", "iid", "pid", "gender"))
        if (wave is None or iid is None or pid is None or gender not in (0, 1)
                or profiles.get((wave, pid)) != 1-gender):
            excluded += 1
            continue
        left, right = (iid, pid) if gender == 0 else (pid, iid)
        encounters[(wave, left, right)][gender].append(
            tuple(_binary(row.get(k)) for k in ("dec", "dec_o", "match")))
    by_wave = defaultdict(lambda: dict(observed_pairs=0, complete_decision_pairs=0,
                                      mutual_yes_pairs=0, inconsistent_pairs=0,
                                      duplicate_directed_rows=0, yes_edges=[]))
    for (wave, left, right), sides in encounters.items():
        out = by_wave[wave]
        out["observed_pairs"] += 1
        out["duplicate_directed_rows"] += sum(max(0, len(records)-1) for records in sides.values())
        # Conflicting duplicate records or mismatched partner reports are
        # retained in coverage, but excluded from behavioral denominators.
        inconsistent = any(len(set(records)) > 1 for records in sides.values())
        pair = [records[0] if records else (None, None, None)
                for records in (sides.get(0, []), sides.get(1, []))]
        own = [record[0] for record in pair]
        for side in (0, 1):
            if pair[side][1] is not None and own[1-side] is not None:
                inconsistent |= pair[side][1] != own[1-side]
        if None not in own:
            joint = own[0] * own[1]
            inconsistent |= any(record[2] is not None and record[2] != joint for record in pair)
        if inconsistent:
            out["inconsistent_pairs"] += 1
            continue
        if None not in own:
            out["complete_decision_pairs"] += 1
            if all(own):
                out["mutual_yes_pairs"] += 1
                out["yes_edges"].append((left, right))
    # Include a wave even if it has no usable directed encounter records.
    for wave, _ in profiles:
        by_wave[wave]
    results = []
    for wave, out in sorted(by_wave.items()):
        nl = sum(w == wave and side == 0 for (w, _), side in profiles.items())
        nr = sum(w == wave and side == 1 for (w, _), side in profiles.items())
        possible = nl * nr
        yes_edges = out.pop("yes_edges")
        bound = maximum_cardinality(yes_edges)
        results.append(dict(wave=wave, n_left=nl, n_right=nr, possible_pairs=possible,
                            **out, coverage=out["observed_pairs"] / possible if possible else None,
                            maximum_mutual_yes_matching=bound))
    complete = sum(r["complete_decision_pairs"] for r in results)
    yes = sum(r["mutual_yes_pairs"] for r in results)
    interval = None
    if len(results) > 1 and complete and bootstrap_draws > 0:
        rng = np.random.default_rng(seed)
        totals = np.array([[r["mutual_yes_pairs"], r["complete_decision_pairs"]] for r in results])
        estimates = []
        for _ in range(bootstrap_draws):
            y, n = totals[rng.integers(len(totals), size=len(totals))].sum(axis=0)
            if n:
                estimates.append(y/n)
        if estimates:
            interval = np.quantile(estimates, [.025, .975]).tolist()
    return dict(raw_directed_rows=len(rows), excluded_directed_rows=excluded,
                waves=len(results), observed_pairs=sum(r["observed_pairs"] for r in results),
                complete_decision_pairs=complete, mutual_yes_pairs=yes,
                mutual_yes_rate=yes/complete if complete else None,
                wave_cluster_bootstrap_95=interval, bootstrap_draws=bootstrap_draws, seed=seed,
                per_wave=results,
                limits="Observed encounters only; no strict preference ranks, unobserved-pair outcomes, causal policy value or calibration of utility units.")


def audit_file(path, exclude_waves=(), **kwargs):
    path = Path(path)
    with path.open(encoding="cp1252", newline="") as stream:
        original = list(csv.DictReader(stream))
    excluded = set(exclude_waves)
    selected = [r for r in original if _integer(r.get("wave")) not in excluded]
    result = audit_rows(selected, **kwargs)
    result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    result["excluded_waves"] = sorted(excluded)
    result["source_directed_rows"] = len(original)
    result["wave_filter_removed_rows"] = len(original)-len(selected)
    return result
