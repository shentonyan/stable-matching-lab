import csv
import pytest

from stablematch.empirical import audit_rows, audit_file, maximum_cardinality


def pair(l, r, a, b, wave=1):
    return [dict(iid=str(l), pid=str(r), wave=str(wave), gender="0", dec=str(a), dec_o=str(b), match=str(a*b)),
            dict(iid=str(r), pid=str(l), wave=str(wave), gender="1", dec=str(b), dec_o=str(a), match=str(a*b))]


def test_reciprocal_rows_not_double_counted_and_missing_not_negative():
    rows = pair(1, 3, 1, 1) + pair(1, 4, 0, 1) + pair(2, 3, 1, 0)
    result = audit_rows(rows)
    w = result["per_wave"][0]
    assert result["raw_directed_rows"] == 6
    assert result["observed_pairs"] == 3
    assert w["possible_pairs"] == 4
    assert w["coverage"] == .75
    assert result["mutual_yes_rate"] == pytest.approx(1/3)
    assert w["maximum_mutual_yes_matching"] == 1


def test_inconsistent_partner_report_excluded_not_repaired():
    rows = pair(1, 2, 1, 1)
    rows[1]["dec_o"] = "0"
    result = audit_rows(rows)
    assert result["observed_pairs"] == 1
    assert result["complete_decision_pairs"] == 0
    assert result["per_wave"][0]["inconsistent_pairs"] == 1
    assert result["mutual_yes_rate"] is None


def test_missing_own_decision_not_filled_from_partner_hint():
    rows = pair(1, 2, 1, 1)
    rows[0]["dec"] = ""
    assert audit_rows(rows)["complete_decision_pairs"] == 0


def test_duplicates_do_not_inflate_counts_and_conflicts_are_flagged():
    rows = pair(1, 2, 1, 1)
    result = audit_rows(rows + [rows[0].copy()])
    assert result["complete_decision_pairs"] == 1
    assert result["per_wave"][0]["duplicate_directed_rows"] == 1
    bad = dict(rows[0], dec="0")
    assert audit_rows(rows + [bad])["per_wave"][0]["inconsistent_pairs"] == 1


def test_maximum_cardinality_reassigns_instead_of_greedy():
    assert maximum_cardinality([(0, 0), (0, 1), (1, 0)]) == 2
    assert maximum_cardinality([]) == 0


def test_schema_and_side_conflicts_fail_closed():
    with pytest.raises(ValueError):
        audit_rows([dict(dec="1")])
    rows = pair(1, 2, 1, 1)
    with pytest.raises(ValueError):
        audit_rows(rows + [dict(rows[0], gender="1")])


def test_wave_filter_changes_only_explicit_selected_cohorts(tmp_path):
    rows = pair(1, 2, 1, 1, wave=1)+pair(3, 4, 0, 0, wave=12)
    source = tmp_path/"test.csv"
    with source.open("w", encoding="cp1252", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    all_waves = audit_file(source)
    selected = audit_file(source, exclude_waves=[12])
    assert all_waves["mutual_yes_rate"] == .5
    assert selected["mutual_yes_rate"] == 1
    assert selected["source_directed_rows"] == 4
    assert selected["wave_filter_removed_rows"] == 2
    assert selected["sha256"] == all_waves["sha256"]


def test_bootstrap_draws_must_be_nonnegative_integer():
    for invalid in (-1, .5, True):
        with pytest.raises(ValueError):
            audit_rows(pair(1, 2, 1, 1), bootstrap_draws=invalid)
