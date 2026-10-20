"""Record draft evidence bindings without certifying human source verification."""
import csv
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def main():
    refs=json.loads((HERE/"references.json").read_text())
    sources=[]
    for record in refs["references"]+refs["context_sources"]:
        sources.append(dict(record, verification_status="AI-inspected; accountable human check pending"))
    local={"P01":("paper/theory-notes.md","Finite derivations and independent executable witnesses"),
           "N01":("paper/results/three_gaps.csv","Exact three-gap references"),
           "N02":("paper/results/validation_summary.json","Independent synthetic-world validation"),
           "N03":("paper/results/selection_stress.csv","Post hoc complete-market diagnostic"),
           "N04":("results/empirical_audit.json","Descriptive encounter aggregates")}
    for key,(path,description) in local.items():
        sources.append(dict(id=key,path=path,title=description,
                            sha256=hashlib.sha256((ROOT/path).read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
                            verification_status="locally checked; not external human verification"))
    manifest=dict(document_id="information-stability-working-paper",human_source_verification_complete=False,
                  scope="External records are AI-inspected, not human-certified. Internal numerical and mathematical bindings support reproducibility, not novelty clearance.",sources=sources)
    (HERE/"source_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=(HERE/"manuscript.tex").read_text(encoding="utf-8").splitlines()
    claims=[]
    for idx,line in enumerate(lines):
        marker=re.fullmatch(r"% claim:(C\d+) evidence:([\w,]+)",line)
        if not marker:
            continue
        block=[]
        for following in lines[idx+1:]:
            if not following.strip():
                break
            if not following.lstrip().startswith("%"):
                block.append(following)
        normalized=" ".join(" ".join(block).split())
        claims.append(dict(claim_id=marker[1],claim_hash=hashlib.sha256(normalized.encode()).hexdigest(),
                           evidence_ids=marker[2],location=f"paper/manuscript.tex:{idx+2}",
                           analysis_intent="theory / exploratory synthetic / descriptive, as stated in prose",
                           status="bound to draft block; human scientific/source review outstanding"))
    with (HERE/"claims.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(claims[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(claims)
    consistency=dict(numeric_source="paper/generated/numbers.json",generated_artifact_manifest="paper/generated/manifest.json",
                     numbers=json.loads((HERE/"generated/numbers.json").read_text()),
                     scopes={"primary_validation":"500 independent worlds within each of two scenarios; six paired contrasts",
                             "exploration":"100 worlds/scenario; 19,200 correlated treatment rows",
                             "exact":"30 worlds; 540 treatment rows", "stress":"separate post hoc population; 500 worlds",
                             "empirical":"21 historical waves; observed encounters only"})
    (HERE/"consistency_manifest.json").write_text(json.dumps(consistency,indent=2)+"\n",encoding="utf-8")
    authorship=dict(authors=[],status="author attribution and accountability not assigned in this working draft",
                    ai_role="AI-assisted modeling, coding, source inspection, drafting and checks; not an author",
                    human_source_verification_complete=False, venue=None, submission_approved=False,
                    funding_statement=None, conflict_statement=None,
                    ethics_scope="No new participant experiment conducted by this computational project; no approval assertion is made")
    (HERE/"authorship.json").write_text(json.dumps(authorship,indent=2)+"\n",encoding="utf-8")
    print(f"Recorded {len(claims)} draft claim blocks and {len(sources)} sources; human verification remains incomplete.")


if __name__=="__main__":
    main()
