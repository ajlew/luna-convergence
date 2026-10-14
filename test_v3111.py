from types import SimpleNamespace
from html import unescape
import re
from yearly_print_html import _month_activation_svg

def make_chart(longitudes):
    snap=SimpleNamespace(positions=[SimpleNamespace(planet=n,longitude=v) for n,v in longitudes.items()], ascendant=None,midheaven=None)
    transits=[{'technical_label':f'Saturn trine natal {name}', 'natal_target':name,'passes':[]} for name in longitudes]
    return _month_activation_svg(snap,transits,'2026-10-14','2026-11-13')

def test_close_planets_have_distinct_labels_and_unchanged_markers():
    result=make_chart({'Sun':207.1,'Venus':207.4,'Mercury':207.6,'Mars':207.8})
    labels=re.findall(r'<text class="planet-label" x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]+)</text>',result)
    assert len(labels)==4
    for i,a in enumerate(labels):
        for b in labels[i+1:]:
            assert abs(float(a[0])-float(b[0]))>=31 or abs(float(a[1])-float(b[1]))>=16, (a,b)
    assert result.count('class="natal-marker"')==4
    assert result.count('class="zodiac-symbol"')==12

def test_distinct_planets_not_shifted_unnecessarily():
    result=make_chart({'Sun':25,'Venus':105,'Mercury':195,'Mars':275})
    assert 'SUN' in result and 'VEN' in result
    assert result.count('class="natal-marker"')==4
