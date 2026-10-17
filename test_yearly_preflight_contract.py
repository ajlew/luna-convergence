from datetime import date, timedelta
import pytest
from yearly_preflight import verify_yearly_material, decision_stage

def sample():
    start=date(2026,10,17); end=start+timedelta(days=364)
    rows=[]
    for i in range(12):
        a=date(2026+(10+i-1)//12,(10+i-1)%12+1,17)
        b=(date(2026+(10+i)//12,(10+i)%12+1,17)-timedelta(days=1)) if i<11 else end
        rows.append({'number':i+1,'start':a.isoformat(),'end':b.isoformat(), 'dominant_game_number':1})
    return {'period':{'start':start.isoformat(),'end':end.isoformat()},'monthly_rounds':rows,'major_issues':[{'number':1,'start':'2026-10-17','end':'2027-10-16'}]}

def test_valid_rolling_year(): verify_yearly_material(sample())

def test_reject_gap():
    x=sample(); x['monthly_rounds'][2]['start']='2026-12-18'
    with pytest.raises(ValueError):verify_yearly_material(x)

def test_reject_out_of_window_exact():
    x=sample(); x['monthly_rounds'][0]['strongest_date']='2027-01-01'
    with pytest.raises(ValueError):verify_yearly_material(x)

def test_reject_unknown_game():
    x=sample(); x['monthly_rounds'][0]['dominant_game_number']=9
    with pytest.raises(ValueError):verify_yearly_material(x)

def test_monthly_stage_progression():
    x=sample()['monthly_rounds']; assert len({decision_stage(m,x[:i]) for i,m in enumerate(x[:4])})==4
