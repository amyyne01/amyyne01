#!/usr/bin/env python3
"""Build the animated Projects section from projects.json.

    python scripts/build_projects.py

Writes assets/projects/*.svg (one header + one clickable row per project, dark and light) and
rewrites the block between the <!-- projects:start --> and <!-- projects:end --> markers in README.md.
Add, remove or reorder entries in projects.json and run it again. No dependencies.
"""
import html, json, math, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "projects"
W = 1200
ROW_H = 78
NAME_MAX, DESC_MAX = 28, 92

PAL = {
    "dark": dict(text="#e6edf3", muted="#8b949e", accent="#4493f8"),
    "light": dict(text="#1f2328", muted="#59636e", accent="#0969da"),
}
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
CSS = (
    f"text{{font-family:{FONT}}}"
    ".c{opacity:0;animation:show .01s linear forwards}"
    ".k{opacity:0;animation:blink 1.05s steps(1,end) infinite;animation-delay:.3s}"
    ".f{opacity:0;animation:show .4s linear forwards}"
    "@keyframes show{to{opacity:1}}@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}"
    ".st{display:none}"
    "@media (prefers-reduced-motion:reduce){.c,.f{animation:none;opacity:1}.k{animation:none;opacity:1}.mv{display:none}.st{display:inline}}"
)


def hash1(n):
    v = math.sin(n * 12.9898 + 4.1) * 43758.5453
    return v - math.floor(v)


def typed(text, size, start, rate=0.018):
    return "".join(
        f'<tspan class="c" style="animation-delay:{start + i * rate:.3f}s">{html.escape(ch)}</tspan>'
        for i, ch in enumerate(text)
    )


def wrap_svg(h, label, body, mode):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" '
        f'aria-label="{html.escape(label)}"><title>{html.escape(label)}</title><style>{CSS}</style>{body}</svg>'
    )


# ---------- header: `$ ls projects/` plus a halftone ripple band
def header(mode):
    p = PAL[mode]
    H, STEP, ROWS, X0, X1, PERIOD, K = 96, 8.8, 6, 430, 1152, 7.0, 10
    cw = 23 * 0.6
    cmd = "ls projects/"
    cur_x = 48 + cw * 2 + cw * len(cmd)
    live, stat = [], []
    cs, mid_x, cy = math.sqrt(0.5), (X0 + X1) / 2, H / 2
    for v in range(-200, 200):
        for u in range(-200, 200):
            x, y = mid_x + (u * cs - v * cs) * STEP, cy + (u * cs + v * cs) * STEP
            if x < X0 or x > X1 or abs(y - cy) > ROWS * STEP * 0.62:
                continue
            t = (x - X0) / (X1 - X0)
            env = math.sin(math.pi * t) ** 0.7
            vals = []
            for k in range(K):
                ph = 2 * math.pi * k / K
                wave = 0.5 + 0.5 * math.sin(t * 9.0 - ph) * math.cos((y - cy) / 14.0 + ph * 0.5)
                vals.append(STEP * (0.07 + 0.36 * math.sqrt(max(0.0, env * (0.25 + 0.75 * wave)))))
            if max(vals) < 0.5:
                continue
            d = 1.0 + abs(t - 0.5) + hash1(round(x * 3) + round(y * 7)) * 0.3
            seq = ";".join(f"{r:.1f}" for r in vals + [vals[0]])
            live.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0"><animate attributeName="r" from="0" to="{vals[0]:.1f}" begin="{d:.2f}s" dur=".6s" fill="freeze"/>'
                f'<animate attributeName="r" values="{seq}" begin="{d + 0.6:.2f}s" dur="{PERIOD}s" repeatCount="indefinite"/></circle>')
            stat.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{vals[0]:.1f}"/>')
    body = (
        f'<text x="48" y="{H / 2 + 8}" font-size="23" font-weight="700" fill="{p["accent"]}">$</text>'
        f'<text x="{48 + cw * 2:.1f}" y="{H / 2 + 8}" font-size="23" fill="{p["text"]}">{typed(cmd, 23, 0.35, 0.07)}</text>'
        f'<rect class="k" x="{cur_x:.1f}" y="{H / 2 - 14}" width="13" height="26" fill="{p["accent"]}"/>'
        f'<g fill="{p["text"]}"><g class="mv">{"".join(live)}</g><g class="st">{"".join(stat)}</g></g>'
    )
    return 96, wrap_svg(96, "Projects", body, mode)


# ---------- one row per project
def row(proj, index, mode):
    p = PAL[mode]
    name, desc = proj["name"], proj["description"]
    if len(name) > NAME_MAX or len(desc) > DESC_MAX:
        raise SystemExit(f'"{name}": keep name <= {NAME_MAX} and description <= {DESC_MAX} characters')
    start = 1.4 + index * 0.45
    name_end = 48 + len(name) * 24 * 0.6
    dots = "".join(
        f'<circle cx="{x}" cy="{ROW_H - 6}" r="1.3"/>' for x in range(52, W - 40, 9)
    )
    body = (
        f'<text x="48" y="32" font-size="24" font-weight="700" fill="{p["text"]}">{typed(name, 24, start)}</text>'
        f'<text x="{name_end + 16:.1f}" y="32" font-size="16" fill="{p["accent"]}">{typed(proj.get("role", ""), 16, start + 0.3)}</text>'
        f'<text x="{W - 48}" y="32" font-size="17" text-anchor="end" fill="{p["muted"]}"><tspan class="f" style="animation-delay:{start + 0.2:.2f}s">{html.escape(proj.get("stack", ""))}</tspan></text>'
        f'<text x="48" y="60" font-size="19" fill="{p["muted"]}">{typed(desc, 19, start + 0.15, 0.012)}</text>'
        f'<g fill="{p["muted"]}" opacity=".35"><g class="f" style="animation-delay:{start:.2f}s">{dots}</g></g>'
    )
    return wrap_svg(ROW_H, f'{name}: {desc} {proj.get("stack", "")}', body, mode)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for mode in PAL:
        (OUT / f"header-{mode}.svg").write_text(header(mode)[1], encoding="utf-8")
        for i, pr in enumerate(projects):
            (OUT / f"{slug(pr['name'])}-{mode}.svg").write_text(row(pr, i, mode), encoding="utf-8")
    parts = [
        '<p>\n  <picture>\n    <source media="(prefers-color-scheme: dark)" srcset="assets/projects/header-dark.svg">\n'
        '    <img src="assets/projects/header-light.svg" width="830" alt="$ ls projects/">\n  </picture>\n</p>\n'
    ]
    for pr in projects:
        s = slug(pr["name"])
        parts.append(
            f'<a href="{pr["url"]}">\n  <picture>\n    <source media="(prefers-color-scheme: dark)" srcset="assets/projects/{s}-dark.svg">\n'
            f'    <img src="assets/projects/{s}-light.svg" width="830" alt="{html.escape(pr["name"])}: {html.escape(pr["description"])} {html.escape(pr.get("stack", ""))}">\n  </picture>\n</a>\n'
        )
    block = "<!-- projects:start -->\n" + "\n".join(parts) + "<!-- projects:end -->"
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    if "<!-- projects:start -->" in text:
        text = re.sub(r"<!-- projects:start -->.*<!-- projects:end -->", lambda m: block, text, flags=re.S)
    else:
        raise SystemExit("README.md has no projects markers")
    readme.write_text(text, encoding="utf-8")
    print(f"{len(projects)} projects -> {OUT.relative_to(ROOT)}, README updated")


if __name__ == "__main__":
    main()
