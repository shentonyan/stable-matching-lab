"""Package reproducible sources and public aggregates, excluding raw records/build files."""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]


def package(output):
    allowed=[]
    for directory in ("paper","stablematch","tests","experiments","docs","results"):
        for path in (ROOT/directory).rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or "build" in path.relative_to(ROOT).parts:
                continue
            if path.suffix.lower() in (".py",".tex",".md",".json",".csv",".png",".pdf",".bib"):
                allowed.append(path)
    for name in ("README.md","requirements.txt","pytest.ini","LICENSE","LICENSE.md",".gitignore",".gitattributes"):
        path=ROOT/name
        if path.is_file():
            allowed.append(path)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,"w",ZIP_DEFLATED) as archive:
        for path in sorted(set(allowed)):
            archive.write(path,"matching-paper/"+path.relative_to(ROOT).as_posix())
    print(f"Packaged {len(set(allowed))} files: {output}")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    package(parser.parse_args().output)
