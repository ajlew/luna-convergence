import ast
import pathlib
import unittest
from unittest.mock import patch
import luna_customer_features as f

class SupportStorageTest(unittest.TestCase):
    def test_existing_supabase_secret_aliases(self):
        with patch.object(f.requests,'request') as req:
            req.return_value.content=b'[]'
            req.return_value.json.return_value=[]
            f.store_request({'SUPABASE_URL':'https://demo.supabase.co','SUPABASE_SERVICE_ROLE_KEY':'test-only'},'luna_support_requests','POST',payload={'status':'new'})
            self.assertEqual(req.call_args.args[1],'https://demo.supabase.co/rest/v1/luna_support_requests')
    def test_existing_smtp_secret_aliases(self):
        cfg=f.mail_config({'SMTP_USER':'lunaconvergence@gmail.com','SMTP_APP_PASSWORD':'placeholder','SMTP_FROM':'lunaconvergence@gmail.com'})
        self.assertEqual(cfg['owner'],'lunaconvergence@gmail.com')
    def test_support_path_does_not_require_database_to_send_email(self):
        tree=ast.parse(pathlib.Path(__file__).with_name('app.py').read_text())
        func=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='contact_luna_page')
        source=ast.get_source_segment(pathlib.Path(__file__).with_name('app.py').read_text(),func)
        self.assertIn('if emailed or stored:',source)
        self.assertIn('notify_owner(st.secrets',source)
        self.assertIn('except Exception:\n                    pass',source)

if __name__=='__main__': unittest.main()
