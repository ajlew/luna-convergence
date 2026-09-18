"""Shared editorial typography: Monthly Key Dates is the reference."""
from html import escape
STYLE = """<style>
.luna-plain-reading,.luna-editorial{max-width:100%;overflow-wrap:anywhere;font-family:"Josefin Sans","Avenir Next",Arial,sans-serif;}
.luna-plain-reading p,.luna-editorial p{line-height:1.62;margin:.35rem 0 .8rem;}
.luna-plain-reading h2,.luna-editorial h3{font-family:"Bodoni Moda",Georgia,serif!important;font-size:clamp(1.7rem,3vw,2.55rem)!important;font-weight:500;line-height:1.02!important;margin:1.35rem 0 .75rem;}
.luna-plain-reading .eyebrow,.luna-plain-reading summary,.luna-plain-reading .lean-daily-label,.luna-editorial .luna-meta{font-family:"IBM Plex Mono",monospace!important;font-size:.68rem;line-height:1.35;letter-spacing:.045em;text-transform:uppercase;}
.luna-calculations{margin:1rem 0 1.5rem;border-top:1px solid #aaa;border-bottom:1px solid #aaa;padding:.8rem 0;}
.luna-calculations summary{cursor:pointer;}
.luna-calculations li{margin:.45rem 0;}
.luna-editorial{padding:1.35rem 0;border-bottom:1px solid #111;}
.luna-plain-reading .lean-daily-move p{font-family:"Bodoni Moda",Georgia,serif!important;font-size:clamp(1.2rem,1.8vw,1.5rem);line-height:1.4;}
.luna-plain-reading .lean-daily-move{max-width:100%;padding:1rem 0;}
.luna-plain-reading .lean-daily-label{margin:.3rem 0;}
@media(max-width:600px){.luna-calculations ul{padding-left:1.2rem;}}
@media print{.luna-calculations::details-content{display:block;content-visibility:visible;}}
</style>"""

def meaning_html(day, event, body):
    from plain_readings import clean_prose
    body = clean_prose(body)
    paragraphs=''.join('<p>'+escape(p)+'</p>' for p in body.split('\n\n') if p.strip())
    return (STYLE + '<article class="luna-editorial"><div class="luna-meta">'
            + escape(day.strftime('%A · %d %B %Y')) + '</div><h3>' + escape(event)
            + '</h3><div class="luna-meta">Collective meaning &amp; energy</div>'
            + paragraphs + '</article>')
