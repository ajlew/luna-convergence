"""Private Supabase Storage birthday backgrounds, persisted across Streamlit redeploys.

Create a private bucket named birthday-backgrounds. Only server-side service role keys
are used; uploads and edits are accessible solely via the app's owner access gate.
"""
from __future__ import annotations

from io import BytesIO
import json
import os
import re
import secrets
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from PIL import Image, UnidentifiedImageError

BUCKET = 'birthday-backgrounds'
CATALOG = 'catalog.json'
MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 22_000_000

class BirthdayBackgroundError(RuntimeError):
    pass

class BirthdayBackgroundLibrary:
    def __init__(self, url: str = '', service_key: str = ''):
        self.url = url.strip().rstrip('/')
        self.key = service_key.strip()
        self.configured = bool(self.url and self.key)

    @classmethod
    def from_streamlit(cls, st):
        def setting(key):
            try:
                return str(st.secrets.get(key, '') or os.environ.get(key, ''))
            except Exception:
                return str(os.environ.get(key, ''))
        return cls(setting('SUPABASE_URL'), setting('SUPABASE_SERVICE_ROLE_KEY'))

    def _request(self, method: str, path: str, data: bytes | None = None, mime='application/json') -> bytes:
        if not self.configured:
            raise BirthdayBackgroundError('Persistent birthday background storage is not configured.')
        if not self.url.startswith('https://'):
            raise BirthdayBackgroundError('Storage URL must use HTTPS.')
        url = f'{self.url}/storage/v1/object/{BUCKET}/{quote(path, safe="/")}'
        headers = {'apikey': self.key, 'Authorization': f'Bearer {self.key}', 'Content-Type': mime}
        if method == 'POST':
            headers['x-upsert'] = 'true'
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=15) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code == 404 and path == CATALOG and method == 'GET':
                return b'[]'
            raise BirthdayBackgroundError(f'Storage request failed (HTTP {exc.code}).') from exc
        except (URLError, TimeoutError) as exc:
            raise BirthdayBackgroundError('Background storage could not be reached.') from exc

    def _catalog(self):
        try:
            items = json.loads(self._request('GET', CATALOG))
        except (ValueError, TypeError) as exc:
            raise BirthdayBackgroundError('Background catalog is invalid.') from exc
        if not isinstance(items, list):
            raise BirthdayBackgroundError('Background catalog is invalid.')
        return items

    def _save(self, items):
        self._request('POST', CATALOG, json.dumps(items, separators=(',', ':')).encode('utf-8'))

    def list_entries(self):
        return self._catalog()

    def find(self, theme_id):
        if not re.fullmatch(r'bg_[a-f0-9]{16}', str(theme_id)):
            return None
        return next((x for x in self._catalog() if x.get('id') == theme_id), None)

    def get_image(self, theme_id):
        entry = self.find(theme_id)
        if not entry:
            raise BirthdayBackgroundError('Background not found.')
        return self._request('GET', entry['filename'])

    def add(self, name: str, data: bytes, *, light_text=True):
        if not (1 <= len(name.strip()) <= 55):
            raise BirthdayBackgroundError('Background name must be 1–55 characters.')
        if len(data) > MAX_BYTES:
            raise BirthdayBackgroundError('Background exceeds 8 MB.')
        try:
            with Image.open(BytesIO(data)) as img:
                w, h = img.size
                if w * h > MAX_PIXELS or w < 500 or h < 850:
                    raise BirthdayBackgroundError('Use a portrait image of at least 500 × 850 pixels and no more than 22 megapixels.')
                if not 0.5 <= w / h <= 0.65:
                    raise BirthdayBackgroundError('Use a 9:16 portrait background, ideally 1080 × 1920.')
                out = BytesIO()
                img.convert('RGB').save(out, format='JPEG', quality=90, optimize=True)
                data = out.getvalue()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise BirthdayBackgroundError('Image must be a valid JPG, PNG, or WebP.') from exc
        ident = 'bg_' + secrets.token_hex(8)
        filename = 'images/' + ident + '.jpg'
        self._request('POST', filename, data, 'image/jpeg')
        entries = self._catalog()
        entries.append({'id': ident, 'name': name.strip(), 'filename': filename, 'active': True,
                        'text': '#F7F0E4' if light_text else '#17140F',
                        'muted': '#DED5C8' if light_text else '#5D5143',
                        'accent': '#E0B654' if light_text else '#8A5E28',
                        'overlay': [7, 18, 38, 60] if light_text else [255, 248, 232, 12],
                        'stars': False})
        self._save(entries)
        return ident

    def update(self, theme_id, *, active):
        entries = self._catalog()
        for item in entries:
            if item.get('id') == theme_id:
                item['active'] = bool(active)
                self._save(entries)
                return
        raise BirthdayBackgroundError('Background not found.')

    def move(self, theme_id, by):
        entries = self._catalog()
        idx = next((i for i, item in enumerate(entries) if item.get('id') == theme_id), None)
        if idx is None:
            raise BirthdayBackgroundError('Background not found.')
        j = max(0, min(len(entries)-1, idx + by))
        entries[idx], entries[j] = entries[j], entries[idx]
        self._save(entries)


def birthday_remote_theme(theme_id):
    if not re.fullmatch(r'bg_[a-f0-9]{16}', str(theme_id)):
        return None
    lib = BirthdayBackgroundLibrary(os.environ.get('SUPABASE_URL', ''), os.environ.get('SUPABASE_SERVICE_ROLE_KEY', ''))
    # Streamlit secrets are not necessarily environment variables.
    if not lib.configured:
        try:
            import streamlit as st
            lib = BirthdayBackgroundLibrary.from_streamlit(st)
        except Exception:
            return None
    return lib.find(theme_id) if lib.configured else None


def birthday_remote_image(theme_id):
    lib = BirthdayBackgroundLibrary(os.environ.get('SUPABASE_URL', ''), os.environ.get('SUPABASE_SERVICE_ROLE_KEY', ''))
    if not lib.configured:
        import streamlit as st
        lib = BirthdayBackgroundLibrary.from_streamlit(st)
    return lib.get_image(theme_id)
