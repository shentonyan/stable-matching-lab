"""Build the working-paper PDF with local LaTeX and render local previews.

python paper/build.py [--output PATH]
Requires local pdflatex; automatic package installation is disabled.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent


def build(output=None):
    executable = shutil.which("pdflatex")
    if not executable:
        raise RuntimeError("Install a local LaTeX distribution to build the PDF")
    build_dir = HERE/"build"
    build_dir.mkdir(exist_ok=True)
    version=subprocess.run([executable,"--version"],capture_output=True,text=True,errors="replace",timeout=15)
    engine_flags=["--disable-installer"] if "MiKTeX" in version.stdout else []
    for _ in range(3):
        result = subprocess.run([executable]+engine_flags+["-interaction=nonstopmode",
                                 "-halt-on-error", "-file-line-error", "-output-directory=build", "manuscript.tex"],
                                cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if result.returncode:
            raise RuntimeError("LaTeX build failed:\n"+result.stdout[-7000:]+result.stderr[-1500:])
    log=(build_dir/"manuscript.log").read_text(encoding="utf-8",errors="replace")
    if re.search(r"undefined references|Citation .* undefined|Reference .* undefined|multiply defined",log):
        raise RuntimeError("Unresolved or duplicate references in LaTeX log")
    for warning in re.findall(r"Overfull .*", log):
        print(warning)
    pdf=build_dir/"manuscript.pdf"
    if output:
        output=Path(output)
        output.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(pdf,output)
    try:
        import pymupdf
        doc=pymupdf.open(pdf)
        previews=build_dir/"previews"
        previews.mkdir(exist_ok=True)
        for i,page in enumerate(doc):
            page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(previews/f"page-{i+1:02d}.png")
        print(f"Built {len(doc)} pages; previews: {previews}")
    except ImportError:
        print("PDF built; install PyMuPDF or use pdftoppm for visual preview")
    print(pdf)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path)
    build(parser.parse_args().output)
