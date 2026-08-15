from __future__ import annotations

"""Structured historical astronomy memory for Luna Convergence (compact archive).

The archive stores one geocentric-tropical Swiss Ephemeris snapshot per UTC day
for 1950–2050. To keep the GitHub deployment artifact small, the SQLite archive
stores only the values needed for historical matching: date key, body id,
longitude and longitudinal speed. Sign, degree and retrograde state are derived
at read time.
"""

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
import os
import sqlite3
import swisseph as swe

ARCHIVE_VERSION = "1.1-compact"
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "luna_ephemeris_1950_2050.sqlite3"
ASPECTS = ("conjunction", "sextile", "square", "trine", "opposition")
SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
BODY_NAMES = (
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "True Node",
)
BODY_TO_ID = {name: i for i, name in enumerate(BODY_NAMES)}
PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO, "True Node": swe.TRUE_NODE,
}
_DIRECTED_TARGETS = {
    0.0: ("conjunction", 0.0), 60.0: ("sextile", 60.0),
    90.0: ("square", 90.0), 120.0: ("trine", 120.0),
    180.0: ("opposition", 180.0), 240.0: ("trine", 120.0),
    270.0: ("square", 90.0), 300.0: ("sextile", 60.0),
}

def archive_path() -> Path:
    override = os.environ.get("LUNA_HISTORICAL_EPHEMERIS_DB", "").strip()
    return Path(override).expanduser().resolve() if override else DEFAULT_DB_PATH

def _connect(path: Path | None = None) -> sqlite3.Connection:
    db = path or archive_path()
    if not db.exists():
        raise FileNotFoundError(f"Luna historical ephemeris archive is missing: {db}")
    c = sqlite3.connect(str(db)); c.row_factory = sqlite3.Row; return c

def archive_available(path: Path | None = None) -> bool:
    return (path or archive_path()).exists()

def metadata(path: Path | None = None) -> dict[str, str]:
    if not archive_available(path): return {}
    with _connect(path) as c:
        rows = c.execute("SELECT key, value FROM metadata ORDER BY key").fetchall()
    return {str(r['key']): str(r['value']) for r in rows}

def archive_stats(path: Path | None = None) -> dict[str, Any]:
    if not archive_available(path): return {"available": False, "path": str(path or archive_path())}
    with _connect(path) as c:
        positions = int(c.execute("SELECT COUNT(*) FROM positions").fetchone()[0])
        days = int(c.execute("SELECT COUNT(DISTINCT day_key) FROM positions").fetchone()[0])
        bodies = int(c.execute("SELECT COUNT(DISTINCT body_id) FROM positions").fetchone()[0])
    m = metadata(path)
    return {"available": True, "path": str(path or archive_path()),
            "start_year": int(m.get('start_year',0) or 0), "end_year": int(m.get('end_year',0) or 0),
            "frame": m.get('frame',''), "zodiac": m.get('zodiac',''), "node": m.get('node',''),
            "snapshot_utc": m.get('snapshot_utc',''), "positions": positions, "days": days,
            "bodies": bodies, "event_mode": m.get('event_mode','on demand')}

def _day_key(value: date | str) -> int:
    s = value.isoformat() if isinstance(value, date) else str(value)[:10]
    return int(s.replace('-',''))

def _day_text(key: int) -> str:
    s=f"{int(key):08d}"; return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

def _sign_degree(lon: float) -> tuple[str,float]:
    v=lon%360.0; return SIGNS[int(v//30)%12], v%30.0

def positions_on(day: date | str, path: Path | None = None) -> list[dict[str, Any]]:
    key=_day_key(day)
    with _connect(path) as c:
        rows=c.execute("SELECT day_key, body_id, longitude, speed_longitude FROM positions WHERE day_key=? ORDER BY body_id",(key,)).fetchall()
    out=[]
    for r in rows:
        lon=float(r['longitude']); speed=float(r['speed_longitude']); sign,deg=_sign_degree(lon)
        out.append({"date_utc":_day_text(r['day_key']),"body":BODY_NAMES[int(r['body_id'])],
                    "longitude":lon,"latitude":0.0,"distance_au":0.0,"speed_longitude":speed,
                    "sign":sign,"degree_in_sign":deg,"retrograde":int(speed<0)})
    return out

def _calc(jd: float, body: str):
    pid=PLANET_IDS[body]
    try: return swe.calc_ut(jd,pid,swe.FLG_SWIEPH|swe.FLG_SPEED)[0]
    except swe.Error: return swe.calc_ut(jd,pid,swe.FLG_MOSEPH|swe.FLG_SPEED)[0]

def _jd_from_date_key(key: str) -> float:
    y,m,d=(int(p) for p in key.split('-')); return swe.julday(y,m,d,0.0)

def _iso_from_jd(jd: float) -> str:
    y,m,d,hour=swe.revjul(jd,swe.GREG_CAL); h=int(hour); mmf=(hour-h)*60; minute=int(mmf); second=min(59,int(round((mmf-minute)*60)))
    return datetime(int(y),int(m),int(d),h,minute,second,tzinfo=timezone.utc).isoformat()

def _equivalent_near(raw: float,target: float)->float: return raw+360.0*round((target-raw)/360.0)

def _refine_aspect(jd0:float,jd1:float,body1:str,body2:str,target:float)->float:
    def fs(jd):
        a,b=_calc(jd,body1),_calc(jd,body2); raw=(b[0]-a[0])%360.0
        return _equivalent_near(raw,target)-target,b[3]-a[3]
    f0,_=fs(jd0); f1,_=fs(jd1); denom=f1-f0; frac=.5 if abs(denom)<1e-10 else max(0,min(1,-f0/denom)); jd=jd0+frac*(jd1-jd0)
    for _ in range(2):
        f,s=fs(jd)
        if abs(s)<1e-8: break
        corr=f/s
        if abs(corr)>.75: break
        jd=max(jd0,min(jd1,jd-corr))
    return jd

def _normalise_when(value,*,end=False):
    if value is None:return None
    key=value.isoformat() if hasattr(value,'isoformat') else str(value); return key[:10] if len(key)>=10 else key

def _aspect_candidates(body1:str,body2:str,path:Path|None=None)->list[dict[str,Any]]:
    if body1 not in BODY_TO_ID or body2 not in BODY_TO_ID or body1==body2:return []
    with _connect(path) as c:
        rows=c.execute("""SELECT a.day_key,a.longitude lon1,b.longitude lon2 FROM positions a JOIN positions b ON b.day_key=a.day_key WHERE a.body_id=? AND b.body_id=? ORDER BY a.day_key""",(BODY_TO_ID[body1],BODY_TO_ID[body2])).fetchall()
    if len(rows)<2:return []
    events=[]; prev=rows[0]; prev_raw=(float(prev['lon2'])-float(prev['lon1']))%360; prev_u=prev_raw
    for current in rows[1:]:
        raw=(float(current['lon2'])-float(current['lon1']))%360; delta=((raw-prev_raw+180)%360)-180; curr_u=prev_u+delta; lo,hi=sorted((prev_u,curr_u))
        for k in range(int(lo//360)-1,int(hi//360)+2):
            for directed,(aspect_name,angle) in _DIRECTED_TARGETS.items():
                target=directed+360*k
                if not ((prev_u<target<=curr_u) or (curr_u<=target<prev_u)):continue
                jd0=_jd_from_date_key(_day_text(prev['day_key'])); jd1=_jd_from_date_key(_day_text(current['day_key'])); exact=_refine_aspect(jd0,jd1,body1,body2,target)
                a,b=_calc(exact,body1),_calc(exact,body2); s1,d1=_sign_degree(a[0]); s2,d2=_sign_degree(b[0])
                events.append({"exact_utc":_iso_from_jd(exact),"event_type":"aspect","body1":body1,"body2":body2,"aspect":aspect_name,"angle":angle,"body1_sign":s1,"body1_degree":d1,"body2_sign":s2,"body2_degree":d2,"direction":None,"note":f"{body1} {aspect_name} {body2}"})
        prev,prev_raw,prev_u=current,raw,curr_u
    unique={(e['exact_utc'],e['aspect']):e for e in events}; return sorted(unique.values(),key=lambda r:r['exact_utc'])

def aspect_events(body1:str,body2:str,aspect:str,*,sign:str|None=None,before=None,after=None,ascending:bool=False,limit:int=20,path:Path|None=None)->list[dict[str,Any]]:
    aspect=aspect.lower()
    if aspect not in ASPECTS:return []
    rows=[r for r in _aspect_candidates(body1,body2,path) if r['aspect']==aspect]
    if sign:rows=[r for r in rows if r['body1_sign']==sign]
    before_key=_normalise_when(before); after_key=_normalise_when(after)
    if before_key: rows=[r for r in rows if r['exact_utc'][:10] < before_key or r['exact_utc'] < str(before)]
    if after_key: rows=[r for r in rows if r['exact_utc'][:10] > after_key or r['exact_utc'] > str(after)]
    rows=sorted(rows,key=lambda r:r['exact_utc'],reverse=not ascending)
    return rows[:max(0,int(limit))]

def previous_aspect(body1:str,body2:str,aspect:str,when,*,sign:str|None=None,path:Path|None=None):
    rows=aspect_events(body1,body2,aspect,sign=sign,before=when,ascending=False,limit=1,path=path); return rows[0] if rows else None

def next_aspect(body1:str,body2:str,aspect:str,when,*,sign:str|None=None,path:Path|None=None):
    rows=aspect_events(body1,body2,aspect,sign=sign,after=when,ascending=True,limit=1,path=path); return rows[0] if rows else None
