from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from birthday_background_library import BirthdayBackgroundLibrary, BirthdayBackgroundError
from birthday_card import _stanza_lines
from birthday_card_voice import validate_birthday_poem, _prompt

def test_three_stanzas_survive_layout():
    image = Image.new('RGB', (400, 400))
    lines = _stanza_lines(ImageDraw.Draw(image), 'First sky\n\nSecond sea\n\nThird road', ImageFont.load_default(), 300)
    assert lines == ['First sky', '', 'Second sea', '', 'Third road']

def test_no_editorial_poem_rejection():
    poem = 'The first line\n\nThe second line\n\nThe final line'
    assert validate_birthday_poem({'poem': poem}, {}) == poem

def test_style_and_no_rhyme_prompt():
    facts = {'poetry_style':'Ancient Oracle','sun_sign_options':['Libra'],'moon_sign_options':['Scorpio'],'variation_key':'test'}
    prompt = _prompt(facts)
    assert 'THREE short stanzas' in prompt and 'childish rhymes' in prompt

def test_background_image_validation():
    class Stub(BirthdayBackgroundLibrary):
        def __init__(self): super().__init__('https://example.supabase.co','test'); self.calls=[]
        def _request(self,*args,**kwargs):
            self.calls.append((args,kwargs))
            return b'[]' if args[0]=='GET' else b'{}'
    lib=Stub()
    im=Image.new('RGB',(1080,1920)); buf=BytesIO(); im.save(buf,format='JPEG')
    ident=lib.add('Violet Cosmos',buf.getvalue())
    assert ident.startswith('bg_')
    assert any(x[0][1]=='catalog.json' for x in lib.calls)
