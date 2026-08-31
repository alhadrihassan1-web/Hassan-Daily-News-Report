import json
import urllib.request
import xml.etree.ElementTree as ET
import re
from html import unescape
from datetime import datetime
from deep_translator import GoogleTranslator

SOURCES = [
    {
        "url": "https://news.google.com/rss/search?q=السعودية&hl=ar&gl=SA&ceid=SA:ar",
        "category": "Saudi",
        "category_ar": "السعودية",
        "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=الشرق+الأوسط&hl=ar&gl=SA&ceid=SA:ar",
        "category": "World",
        "category_ar": "العالم",
        "image": "https://images.unsplash.com/photo-1521295121783-8a321d551ad2?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=Battlefield+OR+Call+of+Duty&hl=ar&gl=SA&ceid=SA:ar",
        "category": "Gaming",
        "category_ar": "ألعاب",
        "image": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=تقنية+ذكاء+اصطناعي&hl=ar&gl=SA&ceid=SA:ar",
        "category": "Tech",
        "category_ar": "تقنية",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=ميلان+OR+الاتحاد&hl=ar&gl=SA&ceid=SA:ar",
        "category": "Sports",
        "category_ar": "رياضة",
        "image": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=900&q=80"
    }
]

def clean_html(text):
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def has_english(text):
    letters = re.findall(r"[A-Za-z]", text or "")
    return len(letters) >= 5

def translate_to_arabic(text):
    if not text:
        return ""

    if not has_english(text):
        return text

    try:
        return GoogleTranslator(
            source="auto",
            target="ar"
        ).translate(text)
    except Exception as error:
        print("Translation failed:", error)
        return text

def clean_title(title, source_name):
    # إزالة اسم المصدر المتكرر من نهاية العنوان
    endings = [
        " - " + source_name,
        " | " + source_name
    ]

    for ending in endings:
        if title.endswith(ending):
            title = title[:-len(ending)]

    return title.strip()

def read_feed(source):
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall(".//item")[:5]:
        title = item.findtext("title", "").strip()
        description = clean_html(
            item.findtext("description", "")
        )
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        source_element = item.find("source")

        source_name = (
            source_element.text.strip()
            if source_element is not None and source_element.text
            else "News"
        )

        if not title or not link:
            continue

        title = clean_title(title, source_name)

        arabic_title = translate_to_arabic(title)

        if description:
            description = description[:400]
            arabic_summary = translate_to_arabic(description)
        else:
            arabic_summary = "اضغط فتح المصدر لقراءة تفاصيل الخبر."

        items.append({
            "id": str(abs(hash(link))),
            "title": arabic_title,
            "summary": arabic_summary,
            "category": source["category"],
            "category_ar": source["category_ar"],
            "source": source_name,
            "date": pub_date,
            "image": source["image"],
            "url": link,
            "breaking": False
        })

    return items

all_news = []

for source in SOURCES:
    try:
        all_news.extend(read_feed(source))
    except Exception as error:
        print("Feed failed:", error)

all_news = all_news[:25]

with open("news.json", "w", encoding="utf-8") as file:
    json.dump(
        all_news,
        file,
        ensure_ascii=False,
        indent=2
    )

print(f"Updated {len(all_news)} news items.")
print(datetime.now())
