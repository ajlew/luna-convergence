from datetime import date, timedelta
import unittest
from monthly_preflight_contract import MonthlyPreflightError, validate_monthly_facts, validate_prompt_budget


def make_packet(n=31):
    return {"subject":{"core_positions":{"Sun":{"sign":"Libra"},"Moon":{"sign":"Scorpio"}}},
            "month_context":{"start":"2026-10-01","end":"2026-10-31"},
            "collective_month":{"collective_story":"Published arc"},
            "daily_signals":[{} for _ in range(n)]}

class MonthlyPreflightTests(unittest.TestCase):
    def test_valid_packet(self): validate_monthly_facts(make_packet())
    def test_missing_moon(self):
        p=make_packet();del p['subject']['core_positions']['Moon']
        with self.assertRaises(MonthlyPreflightError):validate_monthly_facts(p)
    def test_missing_sign(self):
        p=make_packet();p['subject']['core_positions']['Sun']['sign']=''
        with self.assertRaises(MonthlyPreflightError):validate_monthly_facts(p)
    def test_bad_period(self):
        p=make_packet();p['month_context']['end']='2026-10-30'
        with self.assertRaises(MonthlyPreflightError):validate_monthly_facts(p)
    def test_missing_day(self):
        with self.assertRaises(MonthlyPreflightError):validate_monthly_facts(make_packet(30))
    def test_missing_background(self):
        p=make_packet();p['collective_month']={}
        with self.assertRaises(MonthlyPreflightError):validate_monthly_facts(p)
    def test_budget(self):
        validate_prompt_budget(2500, 2500)
        with self.assertRaises(MonthlyPreflightError):validate_prompt_budget(4000,2000)

if __name__=='__main__':unittest.main()
