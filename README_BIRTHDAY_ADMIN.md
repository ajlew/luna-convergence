# Luna v3.140 — Birthday Card, changed files only

Replace `app.py`, `birthday_card.py`, and `birthday_card_voice.py`; add `birthday_background_library.py`.

## Owner background manager

At `/birthday-card`, unlock the existing Luna owner key and expand **Owner Tools · Manage Birthday Backgrounds**. Upload a Canva portrait background, enable/retire it, or move it up/down. Retired images are not deleted: previous paid orders may still reference them.

Custom backgrounds persist in a private Supabase Storage bucket. Create a PRIVATE bucket named `birthday-backgrounds` in your Supabase project. Add the following to Streamlit Cloud secrets (never to Git):

```
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVER_SIDE_SERVICE_ROLE_KEY"
```

The service-role key is powerful. Keep it secret and server-side. The app calls Storage using the service role; do not make the bucket public. If secrets/bucket are missing, the two built-in designs still work and the owner panel explains what to configure. A live Supabase integration has not been tested.

## Customer choices

Two original themes stay available plus any activated uploaded themes. The buyer selects a background and one of **Homeric Epic / Shakespearean / Ancient Oracle / Modern Celebration**. Groq receives the calculated evidence, dominant eligible natal aspect, requested three-stanza/30-word max and explicit no-rhyme instruction. It is one provider attempt, no post-LLM prose editorial inspection. Exact compliance of prose is not guaranteed; no extra paid retry is performed.

## Preserved

The Birthday Card remains A$2.40, 1080x1920 PNG + PDF, with the existing Stripe checkout; Luna version remains v3.140. Natal personality overhaul is not included. The existing owner, Contact Luna, and Weekly Studio modules remain.
