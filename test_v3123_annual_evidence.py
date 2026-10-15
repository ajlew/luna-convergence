import sys,types
sys.modules.setdefault("year_ahead",types.ModuleType("year_ahead")).YearPacket=type("YearPacket",(),{})
from paid_yearly_editorial import _annual_act_evidence

def test_year_acts_are_dated_and_no_future_bleed():
    material={'major_issues':[{'primary':{'technical':'Saturn opposition natal Venus','passes':[{'date':'2027-07-02','pass_label':'initial'}], 'triggers':[]}, 'supporting':[{'technical':'Jupiter sextile natal Venus','passes':[{'date':'2026-11-28','pass_label':'initial'},{'date':'2026-12-28','pass_label':'return'}]}]}]}
    first=[{'number':1,'start':'2026-10-15','end':'2026-11-14'}, {'number':2,'start':'2026-11-15','end':'2026-12-14'}, {'number':3,'start':'2026-12-15','end':'2027-01-14'}]
    second=[{'number':9,'start':'2027-06-15','end':'2027-07-14'}]
    assert [(x['date'], x['contact']) for x in _annual_act_evidence(material, first)]==[('2026-11-28','Jupiter sextile natal Venus'),('2026-12-28','Jupiter sextile natal Venus')]
    assert [x['contact'] for x in _annual_act_evidence(material, second)]==['Saturn opposition natal Venus']

def test_unnamed_trigger_not_invented():
    material={'major_issues':[{'primary':{'technical':'Saturn conjunction natal Ascendant','passes':[],'triggers':[{'date':'2027-03-17','planet':'Venus','label':'Venus activates the pattern'}]}}]}
    result=_annual_act_evidence(material,[{'number':6,'start':'2027-03-15','end':'2027-04-14'}])
    assert result[0]['contact']=='Venus activates the pattern'
    assert result[0]['kind']=='calculated supporting trigger'
