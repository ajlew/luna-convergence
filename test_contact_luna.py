import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from luna_customer_features import support_subject, REPORT_TYPES, ISSUE_TYPES, notify_owner, challenge, verify_code

class ContactLunaTests(unittest.TestCase):
    def test_menu_categories(self):
        self.assertIn('Year Ahead (paid)', REPORT_TYPES)
        self.assertIn('Monthly Report (paid)', REPORT_TYPES)
        self.assertIn('PDF / printing problem', ISSUE_TYPES)
    def test_subject_routes_product_and_issue(self):
        self.assertEqual(support_subject('Year Ahead (paid)', 'Cannot download or access'), '[Luna Support] Year Ahead (paid) | Cannot download or access')
    def test_invalid_subject_fails(self):
        with self.assertRaises(ValueError): support_subject('bogus', 'Other')
    def test_email_verification(self):
        code, state=challenge('Customer@example.com')
        self.assertTrue(verify_code(state,'customer@example.com',code))
    @patch('luna_customer_features.smtplib.SMTP')
    def test_notify_owner_subject_and_reply_to(self,smtp):
        secrets={'LUNA_SMTP_HOST':'smtp.example.com','LUNA_SUPPORT_FROM_EMAIL':'verified@example.com','LUNA_SMTP_USER':'mail','LUNA_SMTP_PASSWORD':'password','LUNA_SUPPORT_TO_EMAIL':'owner@example.com'}
        notify_owner(secrets,sender_address='customer@example.com',report_type='Monthly Report (paid)',issue_type='PDF / printing problem',order_reference='LC-123',message='Page missing')
        m=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        self.assertEqual(m['To'],'owner@example.com')
        self.assertEqual(m['Reply-To'],'customer@example.com')
        self.assertIn('Monthly Report (paid)',m['Subject'])
        self.assertIn('LC-123',m.get_content())
if __name__=='__main__': unittest.main()
