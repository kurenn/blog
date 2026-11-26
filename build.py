#!/usr/bin/env python3
"""Build the static blog. See README.md for the supported Markdown subset."""
import argparse
import datetime as dt
import email.utils
import html
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / 'docs'
# Posts dated after today (Monterrey time, UTC-6 all year) stay unpublished until that day's
# scheduled build, so several posts can be merged at once and still come out on their dates.
SITE_TZ = dt.timezone(dt.timedelta(hours=-6))
BASE = 'https://blog.kurenn.dev'
ESC = html.escape
NAME = re.compile(r'^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$')
INLINE = re.compile(r'(`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|\[[^\]\n]+\]\([^\s)]+\))')
LOGO = '''██████╗ ██╗      ██████╗  ██████╗
██╔══██╗██║     ██╔═══██╗██╔════╝
██████╔╝██║     ██║   ██║██║  ███╗
██╔══██╗██║     ██║   ██║██║   ██║
██████╔╝███████╗╚██████╔╝╚██████╔╝
╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝'''


def inline(text):
    def render(match):
        s = match.group(0)
        if s.startswith('`'):
            return '<code>' + ESC(s[1:-1]) + '</code>'
        if s.startswith('**'):
            return '<strong>' + ESC(s[2:-2]) + '</strong>'
        if s.startswith('*'):
            return '<em>' + ESC(s[1:-1]) + '</em>'
        label, url = s[1:].split('](', 1)
        url = url[:-1]
        try:
            parsed = urlsplit(url)
            # Network-path URLs are external, not relative paths.
            if any(ord(c) < 32 or ord(c) == 127 for c in url):
                return ESC(label)
            if parsed.scheme and parsed.scheme.lower() not in ('http', 'https', 'mailto'):
                return ESC(label)
            if not parsed.scheme and url.startswith('//'):
                return ESC(label)
            external = parsed.scheme.lower() in ('http', 'https')
            return '<a href="' + ESC(url, quote=True) + '"' + (' rel="noopener"' if external else '') + '>' + ESC(label) + '</a>'
        except ValueError:
            return ESC(label)
    parts = []
    last = 0
    for match in INLINE.finditer(text):
        parts.append(ESC(text[last:match.start()]))
        parts.append(render(match))
        last = match.end()
    parts.append(ESC(text[last:]))
    return ''.join(parts)


def markdown(source):
    lines = source.splitlines()
    out = []
    i = 0
    def kind(line):
        if re.match(r'^```', line): return 'code'
        if re.match(r'^#{2,3}\s+', line): return 'heading'
        if re.match(r'^\s*>\s?', line): return 'quote'
        if re.match(r'^\s*[-*+]\s+', line): return 'ul'
        if re.match(r'^\s*\d+\.\s+', line): return 'ol'
        return 'paragraph'
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        typ = kind(line)
        if typ == 'code':
            language = line[3:].strip()
            i += 1
            block = []
            while i < len(lines) and not re.match(r'^```\s*$', lines[i]):
                block.append(lines[i]); i += 1
            if i == len(lines):
                raise ValueError('unclosed fenced code block')
            i += 1
            cls = ' class="language-' + ESC(language, quote=True) + '"' if re.fullmatch(r'[A-Za-z0-9_+-]+', language) else ''
            out.append('<pre><code' + cls + '>' + ESC('\n'.join(block)) + '</code></pre>')
        elif typ == 'heading':
            m = re.match(r'^(#{2,3})\s+(.*)$', line)
            n = len(m.group(1))
            out.append(f'<h{n}>' + inline(m.group(2)) + f'</h{n}>'); i += 1
        elif typ == 'quote':
            block = []
            while i < len(lines) and kind(lines[i]) == 'quote':
                block.append(re.sub(r'^\s*>\s?', '', lines[i])); i += 1
            out.append('<blockquote>' + markdown('\n'.join(block)) + '</blockquote>')
        elif typ in ('ul', 'ol'):
            items = []
            pattern = r'^\s*[-*+]\s+' if typ == 'ul' else r'^\s*\d+\.\s+'
            while i < len(lines) and kind(lines[i]) == typ:
                items.append('<li>' + inline(re.sub(pattern, '', lines[i])) + '</li>'); i += 1
            out.append('<' + typ + '>' + ''.join(items) + '</' + typ + '>')
        else:
            para = [line.strip()]; i += 1
            while i < len(lines) and lines[i].strip() and kind(lines[i]) == 'paragraph':
                para.append(lines[i].strip()); i += 1
            out.append('<p>' + inline(' '.join(para)) + '</p>')
    return '\n'.join(out)


def load_posts():
    posts = []
    slugs = set()
    for path in sorted((ROOT / 'posts').glob('*.md')):
        match = NAME.fullmatch(path.name)
        if not match:
            raise ValueError(f'{path.name}: expected YYYY-MM-DD-slug.md')
        slug = match.group(2)
        if slug in slugs:
            raise ValueError(f'{path.name}: duplicate slug {slug}')
        slugs.add(slug)
        lines = path.read_text(encoding='utf-8').splitlines()
        if not lines or lines[0].strip() != '---':
            raise ValueError(f'{path.name}: missing front matter opening ---')
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == '---')
        except StopIteration:
            raise ValueError(f'{path.name}: missing front matter closing ---') from None
        fields = {}
        for line in lines[1:end]:
            if ':' not in line:
                raise ValueError(f'{path.name}: invalid front matter line: {line}')
            key, value = line.split(':', 1)
            key = key.strip()
            if key in fields:
                raise ValueError(f'{path.name}: duplicate front matter key {key}')
            fields[key] = value.strip()
        for key in ('title', 'date', 'summary'):
            if not fields.get(key):
                raise ValueError(f'{path.name}: missing {key}')
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fields['date']):
                raise ValueError()
            date = dt.date.fromisoformat(fields['date'])
        except ValueError:
            raise ValueError(f'{path.name}: bad date {fields["date"]}') from None
        if fields['date'] != match.group(1):
            raise ValueError(f'{path.name}: date/filename mismatch')
        body = '\n'.join(lines[end + 1:]).strip()
        try:
            rendered = markdown(body)
        except ValueError as error:
            raise ValueError(f'{path.name}: {error}') from error
        # Words in source prose/code; Markdown punctuation does not count as words.
        words = len(re.findall(r'\b[\w]+(?:[\u2019\'-][\w]+)*\b', body, re.UNICODE))
        posts.append(dict(fields, slug=slug, date_obj=date, body=rendered,
                          minutes=max(1, math.ceil(words / 230))))
    return sorted(posts, key=lambda p: (p['date'], p['slug']), reverse=True)


def page(title, description, url, content, home=False):
    heading = '<div class="fit"><pre class="fitted logo" role="img" aria-label="blog">' + ESC(LOGO) + '</pre></div>' if home else '<a class="site-name" href="/">kurenn / blog</a>'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ESC(title)}</title>
<meta name="description" content="{ESC(description, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{ESC(title, quote=True)}">
<meta property="og:description" content="{ESC(description, quote=True)}">
<meta property="og:url" content="{ESC(url, quote=True)}">
<link rel="alternate" type="application/rss+xml" title="Abraham Kuri's blog" href="/feed.xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#1a1b26">
<link rel="stylesheet" href="/style.css">
<script src="/site.js" defer></script>
</head>
<body>
<canvas id="px" aria-hidden="true"></canvas>
<main>
<header>{heading}</header>
<nav aria-label="Main navigation">
<span><span class="b">[</span><a href="/">Home</a><span class="b">]</span></span>
<span><span class="b">[</span><a href="https://kurenn.dev" rel="noopener">kurenn.dev</a><span class="b">]</span></span>
<span><span class="b">[</span><a href="https://github.com/kurenn" rel="noopener">GitHub</a><span class="b">]</span></span>
<span><span class="b">[</span><a href="/feed.xml">RSS</a><span class="b">]</span></span>
</nav>
{content}
<footer>© 2026 Abraham Kuri</footer>
</main>
</body>
</html>
'''


def build_files(posts):
    files = {}
    description = 'Short notes from Abraham Kuri.'
    listing = []
    for p in posts:
        listing.append(f'<article class="tile post-card"><div class="meta"><time datetime="{p["date"]}">{p["date"]}</time> · {p["minutes"]} min read</div><h2><a href="/posts/{p["slug"]}/">{ESC(p["title"])}</a></h2><p>{ESC(p["summary"])}</p></article>')
    content = '<section class="post-list" aria-label="Posts">' + ('\n'.join(listing) if listing else '<p>No posts yet.</p>') + '</section>'
    files['index.html'] = page('Blog · Abraham Kuri', description, BASE + '/', content, True)
    for i, p in enumerate(posts):
        links = []
        if i + 1 < len(posts):
            other = posts[i + 1]
            links.append(f'<a href="/posts/{other["slug"]}/">← Previous: {ESC(other["title"])}</a>')
        if i > 0:
            other = posts[i - 1]
            links.append(f'<a href="/posts/{other["slug"]}/">Next: {ESC(other["title"])} →</a>')
        content = f'''<article class="post">
<header><h1>{ESC(p['title'])}</h1><div class="meta"><time datetime="{p['date']}">{p['date']}</time> · {p['minutes']} min read</div></header>
<div class="prose">{p['body']}</div>
</article>
<nav class="post-nav" aria-label="Post navigation">{' '.join(links)} <a href="/">← All posts</a></nav>'''
        files[f'posts/{p["slug"]}/index.html'] = page(p['title'] + ' · Abraham Kuri', p['summary'], BASE + '/posts/' + p['slug'] + '/', content)
    files['404.html'] = page('Page not found · Abraham Kuri', 'This page could not be found.', BASE + '/404.html', '<section class="tile"><h1>Page not found</h1><p>There is nothing here. <a href="/">Return home</a>.</p></section>')
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for name, value in [('title', 'Abraham Kuri'), ('link', BASE + '/'), ('description', description)]:
        ET.SubElement(channel, name).text = value
    for p in posts[:20]:
        item = ET.SubElement(channel, 'item')
        url = BASE + '/posts/' + p['slug'] + '/'
        date = dt.datetime.combine(p['date_obj'], dt.time(), tzinfo=dt.timezone.utc)
        for name, value in [('title', p['title']), ('link', url), ('guid', url), ('pubDate', email.utils.format_datetime(date, usegmt=True)), ('description', p['summary'])]:
            ET.SubElement(item, name).text = value
    ET.indent(rss, space='  ')
    files['feed.xml'] = ET.tostring(rss, encoding='unicode', xml_declaration=True) + '\n'
    files['CNAME'] = 'blog.kurenn.dev'
    files['.nojekyll'] = ''
    for asset in ('style.css', 'site.js', 'favicon.svg'):
        files[asset] = (ROOT / 'templates' / asset).read_text(encoding='utf-8')
    out = {name: value.encode('utf-8') for name, value in files.items()}
    for asset in ('favicon.ico', 'apple-touch-icon.png'):
        out[asset] = (ROOT / 'templates' / asset).read_bytes()
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='compare generated files without writing')
    parser.add_argument('--today', type=dt.date.fromisoformat, help='publish as of this date (YYYY-MM-DD), for previews')
    args = parser.parse_args()
    today = args.today or dt.datetime.now(SITE_TZ).date()
    try:
        posts = load_posts()
        for p in posts:
            if p['date_obj'] > today:
                print(f"scheduled, not published yet: {p['date']} {p['slug']}", file=sys.stderr)
        expected = build_files([p for p in posts if p['date_obj'] <= today])
        existing = {p.relative_to(DOCS).as_posix(): p for p in DOCS.rglob('*') if p.is_file()} if DOCS.exists() else {}
        differences = sorted(name for name in set(expected) | set(existing)
                             if name not in expected or name not in existing or existing[name].read_bytes() != expected[name])
        if args.check:
            for name in differences:
                print('docs/' + name)
            return 1 if differences else 0
        DOCS.mkdir(parents=True, exist_ok=True)
        # docs is generated output: remove stale files and then empty directories.
        for name in sorted(set(existing) - set(expected)):
            existing[name].unlink()
        for name, data in expected.items():
            path = DOCS / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for directory in sorted((p for p in DOCS.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            if not any(directory.iterdir()):
                directory.rmdir()
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f'build: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
