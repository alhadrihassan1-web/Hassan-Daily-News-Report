import json
import urllib.request
import xml.etree.ElementTree as ET
import re
from html import unescape
from datetime import datetime

import argostranslate.package
import argostranslate.translate

SOURCES = [
    {
        "url": "https://news.google.com/rss/search?q=Saudi+Arabia&hl=en&gl=SA&ceid=SA:en",
        "category": "Saudi",
        "category_ar": "السعودية",
        "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=Middle+East&hl=en&gl=SA&ceid=SA:en",
        "category": "World",
        "category_ar": "العالم",
        "image": "https://images.unsplash.com/photo-1521295121783-8a321d551ad2?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=Battlefield+OR+Call+of+Duty&hl=en&gl=SA&ceid=SA:en",
        "category": "Gaming",
        "category_ar": "ألعاب",
        "image": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=technology+AI&hl=en&gl=SA&ceid=SA:en",
        "category": "Tech",
        "category_ar": "تقنية",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80"
    },
    {
        "url": "https://news.google.com/rss/search?q=AC+Milan+OR+Al+Ittihad&hl=en&gl=SA&ceid=SA:en",
        "category": "Sports",
        "category_ar": "رياضة",
        "image": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=900&q=80"
    }
]

def setup_translation():
    argostranslate.package.update_package_index()
    packages = argostranslate.package.get_available_packages()

    package = next(
        p for p in packages
        if p.from_code == "en" and p.to_code == "ar"
    )

    argostranslate.package.install_from_path(
        package.download()
    )

def translate(text):
    if not text:
        return ""

    try:
        return argostranslate.translate.translate(
            text,
            "en",
            "ar"
        )
    except:
        return text

def clean_html(text):
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def read_feed(source):
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall(".//item")[:4]:

        original_title = item.findtext(
            "title",
            ""
        ).strip()

        description = clean_html(
            item.findtext("description", "")
        )

        link = item.findtext(
            "link",
            ""
        ).strip()

        pub_date = item.findtext(
            "pubDate",
            ""
        ).strip()

        source_element = item.find("source")

        source_name = (
            source_element.text.strip()
            if source_element is not None
            and source_element.text
            else "News"
        )

        if not original_title or not link:
            continue

        arabic_title = translate(original_title)

        if description:
            arabic_summary = translate(
                description[:350]
            )
        else:
            arabic_summary = (
                "اضغط فتح المصدر لقراءة التفاصيل."
            )

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

print("Installing Arabic translation model...")
setup_translation()

all_news = []

for source in SOURCES:
    try:
        all_news.extend(
            read_feed(source)
        )
    except Exception as error:
        print(
            "Feed failed:",
            error
        )

all_news = all_news[:20]

with open(
    "news.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        all_news,
        file,
        ensure_ascii=False,
        indent=2
    )

print(
    f"Updated {len(all_news)} news items"
)
print(datetime.now())
