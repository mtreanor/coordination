"""Export the diagrams in docs/figures/diagrams.html as standalone SVGs and PNGs.

    uv run scripts/export_figures.py

Each inline <svg> in the page becomes docs/figures/<name>.svg (light theme, styles
inlined) and a 2x PNG rendered by headless Chrome. Edit the page, then rerun this.
"""

import pathlib
import re
import subprocess

FIGURES = pathlib.Path(__file__).resolve().parent.parent / "docs" / "figures"
NAMES = ["system-overview", "rue-tick", "decision-request", "who-knows-what"]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> None:
    page = (FIGURES / "diagrams.html").read_text()
    css = page[page.index("<style>") + len("<style>"): page.index("</style>")]
    tokens = dict(re.findall(r"--([\w-]+):\s*([^;]+);", re.search(r":root \{(.*?)\n\}", css, re.S).group(1)))
    rules = "\n".join(line.replace("svg ", "", 1) for line in css.splitlines()
                      if line.strip().startswith("svg ") and "figure" not in line)
    rules = re.sub(r"var\(--([\w-]+)\)", lambda m: tokens[m.group(1)], rules).replace("currentColor", tokens["fg"])
    style = f"<style>\ntext {{ font-family: {tokens['sans']}; }}\n{rules}\n</style>"

    svgs = re.findall(r"<svg .*?</svg>", page, re.S)
    if len(svgs) != len(NAMES):
        raise SystemExit(f"expected {len(NAMES)} diagrams in the page, found {len(svgs)}")
    for name, svg in zip(NAMES, svgs):
        width, height = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups()
        svg = svg.replace("<svg ", f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" ', 1)
        svg = re.sub(r"(<svg[^>]*>)", rf'\1\n{style}\n<rect width="{width}" height="{height}" fill="#ffffff"/>', svg, count=1)
        path = FIGURES / f"{name}.svg"
        path.write_text(svg + "\n")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", f"--window-size={width},{height}",
                        f"--screenshot={FIGURES / f'{name}.png'}", path.as_uri()],
                       check=True, capture_output=True)
        print(f"{name}: {width}x{height}")


if __name__ == "__main__":
    main()
