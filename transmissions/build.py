#!/usr/bin/env python3
"""Build touchpattern.io/transmissions from transmissions/src/*.md.

Each source file: YAML-ish frontmatter (key: value lines between ---) + markdown body.
Required keys: n, title, slug, date. Optional: recorded, status, summary, tags, substack, draft.
Files with `draft: true` are skipped. Rendering = pandoc (gfm -> html fragment).

Usage: python3 transmissions/build.py
"""
import html
import pathlib
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
SITE = "https://touchpattern.io"
CONTACT = "touchpattern@gmail.com"


def parse(path):
    text = path.read_text()
    _, fm, body = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    meta["body"] = body.strip()
    meta["_file"] = path.name
    return meta


def md(text):
    return subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "html", "--wrap=none"],
        input=text, capture_output=True, text=True, check=True,
    ).stdout


STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&display=swap');
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{background:#08080c;color:#e8e4df;font-family:'Newsreader',Georgia,serif;font-size:1.15rem;line-height:1.7;padding:4rem 1.25rem 6rem}
main{max-width:38rem;margin:0 auto}
a{color:#c9b48f;text-decoration:none;border-bottom:1px solid rgba(180,160,130,.3)}
a:hover{border-color:#c9b48f}
.mono,.meta,nav,h1,h2,h3,.n{font-family:'Space Mono','Courier New',monospace}
nav{font-size:.75rem;letter-spacing:.15em;text-transform:lowercase;margin-bottom:4rem}
nav a{border:0;color:rgba(180,160,130,.7)}
.n{font-size:.75rem;letter-spacing:.2em;color:rgba(180,160,130,.6)}
h1{font-size:1.6rem;font-weight:400;letter-spacing:.04em;line-height:1.3;margin:.6rem 0 1rem}
h2{font-size:1rem;font-weight:400;letter-spacing:.08em;margin:2.8rem 0 .8rem;color:#c9b48f}
h3{font-size:.9rem;font-weight:400;margin:2rem 0 .6rem}
.meta{font-size:.72rem;letter-spacing:.08em;color:rgba(232,228,223,.45);margin-bottom:3rem}
article p,article li{margin-bottom:1.1rem}
article ul,article ol{padding-left:1.3rem}
blockquote{border-left:1px solid rgba(180,160,130,.4);padding-left:1.1rem;color:rgba(232,228,223,.75);font-style:italic;margin:1.6rem 0}
hr{border:0;height:1px;background:linear-gradient(90deg,transparent,rgba(180,160,130,.4),transparent);margin:3rem 0}
.respond{font-family:'Space Mono',monospace;font-size:.78rem;line-height:1.8;color:rgba(232,228,223,.6);margin-top:4rem}
ol.index{list-style:none;padding:0}
ol.index li{padding:1.4rem 0;border-top:1px solid rgba(180,160,130,.15)}
ol.index a{border:0;color:#e8e4df;font-size:1.2rem}
ol.index p{color:rgba(232,228,223,.6);font-size:1rem;margin-top:.3rem}
.intro{color:rgba(232,228,223,.75);margin-bottom:3rem}
"""


def page(title, desc, inner, canonical):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/rss+xml" title="touchpattern transmissions" href="{SITE}/transmissions/feed.xml">
<style>{STYLE}</style>
</head>
<body><main>
<nav><a href="/">touchpattern</a> / <a href="/transmissions/">transmissions</a></nav>
{inner}
</main></body>
</html>
"""


def main():
    items = [parse(p) for p in sorted(SRC.glob("*.md"))]
    items = [m for m in items if m.get("draft", "").lower() != "true"]
    items.sort(key=lambda m: int(m["n"]), reverse=True)

    for m in items:
        num = f"T-{int(m['n']):03d}"
        url = f"{SITE}/transmissions/{m['slug']}/"
        bits = [f"transmitted {m['date']}"]
        if m.get("recorded"):
            bits.append(f"recorded {m['recorded']}")
        if m.get("status"):
            bits.append(m["status"])
        transcript = SRC / f"{pathlib.Path(m['_file']).stem}.transcript.txt"
        if transcript.exists():
            bits.append(f'<a href="/transmissions/{m["slug"]}/transcript/">raw transcript</a>')
        if m.get("substack"):
            bits.append(f'<a href="{m["substack"]}">substack</a>')
        subject = html.escape(f"{num} {m['title']}").replace(" ", "%20")
        inner = (
            f'<div class="n">{num}</div><h1>{html.escape(m["title"])}</h1>'
            f'<div class="meta">{" &middot; ".join(bits)}</div>'
            f'<article>{md(m["body"])}</article>'
            f'<div class="respond">Respond, build on it, argue with it: '
            f'<a href="mailto:{CONTACT}?subject={subject}">{CONTACT}</a><br>'
            f'Cite as: Gio Ray, &ldquo;{html.escape(m["title"])},&rdquo; touchpattern {num}, {m["date"]}. {url}</div>'
        )
        out = ROOT / m["slug"] / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page(f"{num} {m['title']} | touchpattern", m.get("summary", ""), inner, url))
        if transcript.exists():
            paras = "".join(f"<p>{html.escape(l.strip())}</p>" for l in transcript.read_text().splitlines() if l.strip())
            t_inner = (
                f'<div class="n">{num} &middot; raw transcript</div><h1>{html.escape(m["title"])}</h1>'
                f'<div class="meta">voice memo, recorded {m.get("recorded", m["date"])} &middot; machine transcription, unedited &middot; '
                f'<a href="/transmissions/{m["slug"]}/">back to the piece</a></div><article>{paras}</article>'
            )
            t_out = out.parent / "transcript" / "index.html"
            t_out.parent.mkdir(exist_ok=True)
            t_out.write_text(page(f"{num} transcript | touchpattern", f"Raw transcript of {num}.", t_inner, url + "transcript/"))

    rows = "".join(
        f'<li><span class="n">T-{int(m["n"]):03d} &middot; {m["date"]}</span><br>'
        f'<a href="/transmissions/{m["slug"]}/">{html.escape(m["title"])}</a>'
        f'<p>{html.escape(m.get("summary", ""))}</p></li>'
        for m in items
    )
    intro = (ROOT / "intro.md").read_text() if (ROOT / "intro.md").exists() else ""
    inner = f'<h1>transmissions</h1><div class="intro">{md(intro)}</div><ol class="index">{rows}</ol>'
    (ROOT / "index.html").write_text(
        page("transmissions | touchpattern", "Ideas from Gio Ray, logged in public as they arrive.", inner, f"{SITE}/transmissions/")
    )

    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    entries = "".join(
        f"<item><title>{html.escape(m['title'])}</title>"
        f"<link>{SITE}/transmissions/{m['slug']}/</link><guid>{SITE}/transmissions/{m['slug']}/</guid>"
        f"<pubDate>{datetime.strptime(m['date'], '%Y-%m-%d').strftime('%a, %d %b %Y 12:00:00 -0700')}</pubDate>"
        f"<description>{html.escape(m.get('summary', ''))}</description></item>"
        for m in items
    )
    (ROOT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>touchpattern transmissions</title><link>{SITE}/transmissions/</link>"
        f"<description>Ideas from Gio Ray, logged in public.</description><lastBuildDate>{now}</lastBuildDate>"
        f"{entries}</channel></rss>\n"
    )
    landing = ROOT.parent / "index.html"
    lt = landing.read_text()
    start, end = "<!--transmissions-->", "<!--/transmissions-->"
    links = '<a class="head" href="/transmissions/">transmissions</a>\n' + "".join(
        f'<a href="/transmissions/{m["slug"]}/">T-{int(m["n"]):03d} {html.escape(m["title"].lower())}</a>\n' for m in items
    )
    landing.write_text(lt[: lt.index(start) + len(start)] + "\n" + links + lt[lt.index(end):])

    print(f"built {len(items)} transmission(s)")


if __name__ == "__main__":
    main()
