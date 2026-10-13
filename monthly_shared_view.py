"""Paid Monthly customer view: one content document for screen, HTML and PDF.

No LLM calls or ephemeris calculations are performed by this renderer.
"""
from __future__ import annotations
from html import escape
import re

CSS = r'''
@page {size:A4; margin:17mm 17mm 16mm; @bottom-right {content:counter(page);font:9pt Arial;color:#777}}
.luna-monthly,.luna-monthly *{box-sizing:border-box}.luna-monthly{font-family:'Josefin Sans',Arial,sans-serif}
.luna-monthly{max-width:850px;margin:20px auto;background:white;padding:36px 48px;color:#181818}
.luna-monthly h1,.luna-monthly h2{font-family:'Bodoni Moda',Georgia,serif;font-weight:500;line-height:1.08}
.luna-monthly h1{font-size:43px;margin:10px 0 16px}.luna-monthly h2{font-size:28px;margin:28px 0 11px}
.luna-monthly p{font-size:15px;line-height:1.62;margin:0 0 13px}
.luna-monthly .topline,.luna-monthly .kicker{font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.13em;text-transform:uppercase}
.luna-monthly .topline{border-bottom:1px solid #111;padding-bottom:12px;display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap}
.luna-monthly .deck{font-size:17px}.luna-monthly .block{padding-top:12px;border-top:1px solid #cfcfcf;margin-top:22px}
.luna-monthly .wheels{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}
.luna-monthly .wheels svg{display:block;max-width:100%;height:auto;max-height:300px}
.luna-monthly .kicker{display:block;color:#555;margin-bottom:6px}
.luna-monthly .event{border-bottom:1px solid #d7d7d7;padding:11px 0;break-inside:avoid}
.luna-monthly .event b{font-size:14px}.luna-monthly .event span{font-size:12px;color:#555;display:block;margin-top:3px}
.luna-monthly .muted{font-size:12px;color:#555}.luna-monthly .story p{font-size:15px;line-height:1.65}
.luna-monthly .evidence{padding:14px;background:#f5f5f2;break-inside:avoid}
.luna-monthly .evidence p{font-size:12px;margin:3px 0}
.luna-monthly footer{border-top:1px solid #ddd;margin-top:30px;padding-top:10px;font-size:10px;color:#666}
@media(max-width:640px){.luna-monthly{padding:22px 18px;margin:0}.luna-monthly h1{font-size:32px}.luna-monthly .wheels{grid-template-columns:1fr 1fr;gap:8px}}
@media print{html,body{background:white!important}.luna-monthly{max-width:none;margin:0;padding:0}.luna-monthly .block{break-before:auto}.luna-monthly .wheels{break-inside:avoid}.luna-monthly h1,.luna-monthly h2{break-after:avoid}.luna-monthly .story p{orphans:3;widows:3}.luna-monthly footer{break-inside:avoid}}
'''

def _clean_paragraph(text):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    # Do not silently rewrite speculative astrology claims. Report validation belongs upstream.
    return escape(text)

def build_monthly_shared_html(*, title, label, intro, paragraphs, natal_svg='', activation_svg='', contacts=(), key_dates=(), evidence=(), reference='', full_document=True):
    if not paragraphs:
        raise ValueError('Paid Monthly export requires a completed story.')
    story = ''.join(f'<p>{_clean_paragraph(p)}</p>' for p in paragraphs if str(p).strip())
    if not story:
        raise ValueError('Paid Monthly export requires nonempty story paragraphs.')
    wheels = ''
    if natal_svg or activation_svg:
        wheels = '<section class="block"><h2>Your natal activation</h2><div class="wheels">'
        for caption, svg in [('Natal reference', natal_svg), ('Monthly activation', activation_svg)]:
            if svg:
                wheels += f'<div><span class="kicker">{caption}</span>{svg}</div>'
        wheels += '</div></section>'
    contacts_html = ''
    if contacts:
        contacts_html = '<section class="block"><h2>Personal transits</h2>'
        for row in contacts:
            contacts_html += f'<div class="event"><b>{escape(str(row[0]))}</b><span>{escape(str(row[1]))}</span></div>'
        contacts_html += '</section>'
    dates_html = ''
    if key_dates:
        dates_html = '<section class="block"><h2>Key dates</h2>'
        for dt, name in key_dates:
            dates_html += f'<div class="event"><b>{escape(str(dt))}</b><span>{escape(str(name))}</span></div>'
        dates_html += '</section>'
    evidence_html = ''
    if evidence:
        evidence_html = '<section class="block"><h2>Why Luna sees this</h2><div class="evidence">'
        evidence_html += ''.join(f'<p>{escape(str(x))}</p>' for x in evidence)
        evidence_html += '</div></section>'
    content = (f'<article class="luna-monthly"><div class="topline"><b>Luna Convergence</b><span>{escape(str(label))}</span></div>'
               f'<span class="kicker" style="margin-top:22px">Your personal Monthly</span>'
               f'<h1>{escape(str(title))}</h1><p class="deck">{escape(str(intro))}</p>'
               f'<section class="block story"><h2>Read the month</h2>{story}</section>'
               f'{wheels}{contacts_html}{dates_html}{evidence_html}'
               f'<footer>Symbolic astrology, not professional advice. '
               f'{"Order reference · " + escape(str(reference)) if reference else ""}</footer></article>')
    if not full_document:
        return f'<style>{CSS}</style>{content}'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Luna Convergence Monthly</title>'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:wght@400;500&family=Josefin+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">'
            f'<style>{CSS}</style></head><body>{content}</body></html>')

def html_to_pdf(html: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=html).write_pdf()
