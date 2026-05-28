import requests
import gzip
from io import BytesIO
from lxml import etree
from deep_translator import GoogleTranslator
from langdetect import detect
import time

# ---------------- CONFIG ----------------
EPG_URL = "https://github.com/didikc/EPG/raw/master/epg/guide.xml.gz"
OUTPUT_XML = "epg.xml"
OUTPUT_GZ = "epg.xml.gz"

TAGS_TO_TRANSLATE = ['title', 'desc', 'sub-title']

# ✅ Target channels for capitalization fix
TARGET_CHANNELS = {
    "HBOAsia.sg@SD",
    "HBOSignatureAsia.sg@SD",
    "HBOFamilyAsia.sg@SD",
    "HBOHitsAsia.sg@SD",
    "CinemaxAsia.sg@SD",
    "AXNAsia.sg@Singapore"
}

# ----------------------------------------

print("⬇️ Downloading EPG...")
response = requests.get(EPG_URL, timeout=30)

if response.status_code != 200:
    raise Exception("❌ Failed to download EPG")

print("📦 Decompressing...")
with gzip.open(BytesIO(response.content), 'rb') as f:
    xml_data = f.read()

print("🔍 Parsing XML...")
root = etree.fromstring(xml_data)

translator = GoogleTranslator(source='auto', target='en')

cache = {}

# ---------------- FUNCTIONS ----------------

def safe_detect(text):
    try:
        return detect(text)
    except:
        return "unknown"

# ✅ Fix FULL CAPS → Title Case
def fix_full_caps(text):
    if not text:
        return text

    if text.strip().isupper():
        text = text.lower().title()

    return text

def selective_translate(text, channel=None):
    if not text or not text.strip():
        return text

    text = text.strip()

    # ✅ Apply ONLY to selected channels (HBO, AXN, Cinemax)
    if channel in TARGET_CHANNELS:
        text = fix_full_caps(text)

    # ✅ Cache
    if text in cache:
        return cache[text]

    lang = safe_detect(text)

    # ✅ Keep Bahasa Indonesia
    if lang == "id":
        cache[text] = text
        return text

    # ✅ Keep English
    if lang == "en":
        cache[text] = text
        return text

    # ✅ Translate others → English
    try:
        translated = translator.translate(text)
        cache[text] = translated

        print(f"🌐 {lang} → EN | {text[:50]} -> {translated[:50]}")
        time.sleep(0.1)

        return translated

    except Exception as e:
        print(f"⚠️ Failed: {text[:40]} ({e})")
        return text

# ---------------- PROCESS ----------------

print("🌍 Translating... (this may take time for large EPG)\n")

count = 0

for elem in root.iter():
    tag = elem.tag.lower() if hasattr(elem.tag, 'lower') else ""

    if tag in TAGS_TO_TRANSLATE and elem.text:
        parent = elem.getparent()
        channel = parent.get("channel") if parent is not None else None

        elem.text = selective_translate(elem.text, channel)
        count += 1

        if count % 500 == 0:
            print(f"✅ Processed {count} items...")

# ---------------- SAVE ----------------

print("\n💾 Saving XML...")
tree = etree.ElementTree(root)
tree.write(OUTPUT_XML, encoding="utf-8",
           pretty_print=True, xml_declaration=True)

print("📦 Compressing to GZ...")
with gzip.open(OUTPUT_GZ, "wb") as f:
    f.write(etree.tostring(root, encoding="utf-8", pretty_print=True))

print("\n✅ DONE!")
print(f"XML file  : {OUTPUT_XML}")
print(f"GZ  file  : {OUTPUT_GZ}")
