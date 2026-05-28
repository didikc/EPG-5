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

def safe_detect(text):
    try:
        return detect(text)
    except:
        return "unknown"

def selective_translate(text):
    if not text or not text.strip():
        return text

    text = text.strip()

    # Use cache
    if text in cache:
        return cache[text]

    lang = safe_detect(text)

    # ✅ Keep Bahasa Indonesia
    if lang == "id":
        cache[text] = text
        return text

    # ✅ Keep English (skip unnecessary calls)
    if lang == "en":
        cache[text] = text
        return text

    # ✅ Translate others → English
    try:
        translated = translator.translate(text)
        cache[text] = translated

        print(f"🌐 {lang} → EN | {text[:50]} -> {translated[:50]}")
        time.sleep(0.1)  # small delay to avoid rate limit

        return translated

    except Exception as e:
        print(f"⚠️ Failed: {text[:40]} ({e})")
        return text

print("🌍 Translating... (this may take time for large EPG)\n")

count = 0

for elem in root.iter():
    tag = elem.tag.lower() if hasattr(elem.tag, 'lower') else ""

    if tag in TAGS_TO_TRANSLATE and elem.text:
        elem.text = selective_translate(elem.text)
        count += 1

        if count % 500 == 0:
            print(f"✅ Processed {count} items...")

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
