"""Customer previews, support verification, persistent likes. No LLM calls."""
from __future__ import annotations
import hashlib
import hmac
import re
import secrets
import smtplib
import time
from email.message import EmailMessage
import requests

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def config_value(secrets_obj, name):
    try:
        return str(secrets_obj.get(name) or '').strip()
    except (AttributeError, KeyError, TypeError):
        return ''

def mail_config(secrets_obj):
    """Reuse the app's existing Gmail secrets; allow Luna-specific overrides."""
    user = config_value(secrets_obj, 'LUNA_SMTP_USER') or config_value(secrets_obj, 'SMTP_USER')
    password = config_value(secrets_obj, 'LUNA_SMTP_PASSWORD') or config_value(secrets_obj, 'SMTP_APP_PASSWORD')
    sender = (config_value(secrets_obj, 'LUNA_SUPPORT_FROM_EMAIL')
              or config_value(secrets_obj, 'SMTP_FROM') or user)
    owner = config_value(secrets_obj, 'LUNA_SUPPORT_TO_EMAIL') or user
    host = (config_value(secrets_obj, 'LUNA_SMTP_HOST')
            or config_value(secrets_obj, 'SMTP_HOST') or 'smtp.gmail.com')
    port = config_value(secrets_obj, 'LUNA_SMTP_PORT') or config_value(secrets_obj, 'SMTP_PORT') or '587'
    return {'host': host, 'port': port, 'user': user, 'password': password,
            'sender': sender, 'owner': owner}


def store_request(secrets_obj, table, method='GET', payload=None, params=None):
    base = (config_value(secrets_obj, 'LUNA_SUPABASE_URL') or config_value(secrets_obj, 'SUPABASE_URL')).rstrip('/')
    key = (config_value(secrets_obj, 'LUNA_SUPABASE_SERVICE_ROLE_KEY') or config_value(secrets_obj, 'SUPABASE_SERVICE_ROLE_KEY'))
    if not base or not key:
        raise RuntimeError('Persistent customer storage is not configured.')
    if table not in {'luna_support_requests', 'luna_free_likes'}:
        raise ValueError('Unknown storage table')
    r = requests.request(method, f'{base}/rest/v1/{table}',
        headers={'apikey':key,'Authorization':f'Bearer {key}',
                 'Content-Type':'application/json','Prefer':'return=representation'},
        json=payload,params=params,timeout=12)
    r.raise_for_status()
    return r.json() if r.content else []

def send_code(secrets_obj, address, code):
    if not EMAIL_RE.fullmatch(address):
        raise ValueError('Enter a valid email address.')
    cfg = mail_config(secrets_obj)
    host, sender, user, password = (cfg[k] for k in ('host', 'sender', 'user', 'password'))
    if not all((host,sender,user,password)):
        raise RuntimeError('Email verification has not been configured.')
    msg=EmailMessage()
    msg['From']=sender; msg['To']=address; msg['Subject']='Verify your Luna support request'
    msg.set_content(f'Your Luna verification code is {code}. It expires in 10 minutes.\nIf you did not request support, ignore this email.')
    port=int(cfg['port'])
    with smtplib.SMTP(host,port,timeout=15) as smtp:
        smtp.starttls(); smtp.login(user,password); smtp.send_message(msg)

def challenge(address):
    code=f'{secrets.randbelow(1_000_000):06d}'
    return code, {'email':address.lower().strip(),'digest':hashlib.sha256(code.encode()).hexdigest(),
                  'expires':time.time()+600,'attempts':0}

def verify_code(state,address,code,now=None):
    if not state or state.get('email') != address.lower().strip() or (now or time.time()) > state.get('expires',0):
        return False
    if state.get('attempts',0)>=5: return False
    state['attempts']=state.get('attempts',0)+1
    return hmac.compare_digest(state['digest'],hashlib.sha256(str(code).strip().encode()).hexdigest())

def like_key(category,sign,period):
    token='|'.join((str(category).lower().strip(),str(sign).lower().strip(),str(period).strip()))
    return hashlib.sha256(token.encode()).hexdigest()[:40]

def social_card_dimensions():
    return (1080,1920)


REPORT_TYPES = (
    'Year Ahead (paid)', 'Monthly Report (paid)', 'Birthday Card',
    'Social Card / Instagram Story', 'Weekly Studio', 'Free Daily Horoscope',
    'Free Weekly Horoscope', 'Free Monthly Horoscope', 'Natal Snapshot',
    'Payment / Order (unsure of report)', 'Other',
)
ISSUE_TYPES = (
    'Cannot download or access', 'PDF / printing problem',
    'Report content question', 'Payment or checkout', 'Refund or return',
    'Email delivery / private link', 'Technical problem', 'Feedback / suggestion', 'Other',
)

def support_subject(report_type: str, issue_type: str) -> str:
    if report_type not in REPORT_TYPES or issue_type not in ISSUE_TYPES:
        raise ValueError('Unknown support category')
    return f'[Luna Support] {report_type} | {issue_type}'


def notify_owner(secrets_obj, *, sender_address: str, report_type: str,
                 issue_type: str, order_reference: str, message: str) -> None:
    """Email the owner after a verified submission has been stored.

    Reply-To is the customer; mail is sent FROM the configured verified address
    to avoid spoofed sender headers and SMTP deliverability problems.
    """
    subject = support_subject(report_type, issue_type)
    if not EMAIL_RE.fullmatch(sender_address):
        raise ValueError('Invalid customer email')
    cfg = mail_config(secrets_obj)
    host, sender, user, password, owner = (cfg[k] for k in ('host', 'sender', 'user', 'password', 'owner'))
    if not all((host, sender, user, password, owner)):
        raise RuntimeError('Owner notification is not configured')
    if not EMAIL_RE.fullmatch(owner):
        raise ValueError('Invalid owner destination')
    mail = EmailMessage()
    mail['From'] = sender
    mail['To'] = owner
    mail['Reply-To'] = sender_address
    mail['Subject'] = subject
    mail.set_content('\n'.join((
        'New verified Luna support request', '',
        f'Product: {report_type}', f'Issue: {issue_type}',
        f'Customer email: {sender_address}',
        f'Order reference: {order_reference or "Not provided"}', '',
        'Message:', message, '',
        'Reply to this email to respond to the customer.',
    )))
    port = int(cfg['port'])
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(mail)


def support_mail_status(secrets_obj):
    """Non-sensitive config status; never expose password or app-password."""
    cfg = mail_config(secrets_obj)
    absent = [name for name in ('user', 'password', 'sender') if not cfg[name]]
    if absent:
        aliases = {'user': 'SMTP_USER', 'password': 'SMTP_APP_PASSWORD', 'sender': 'SMTP_FROM'}
        return 'Missing Streamlit secrets: ' + ', '.join(aliases[name] for name in absent)
    try:
        port = int(cfg['port'])
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        return 'Invalid SMTP port (must be 1–65535)'
    if port != 587:
        return 'Unsupported SMTP port for current STARTTLS client (expected 587)'
    if not EMAIL_RE.fullmatch(cfg['sender']):
        return 'SMTP_FROM is not a valid email address'
    if not EMAIL_RE.fullmatch(cfg['owner']):
        return 'Support inbox email is not valid'
    return 'ready'
