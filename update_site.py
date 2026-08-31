import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

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

def improve_with_ai(title, source_name):
    if not OPENAI_API_KEY:
        return title, "اضغط فتح المصدر لقراءة تفاصيل الخبر."

    prompt = f"""
حوّل الخبر التالي إلى صيغة عربية مناسبة لموقع أخبار شخصي.

العنوان الأصلي:
{title}

المصدر:
{source_name}

أرجع JSON فقط بهذا الشكل:
{{
  "title": "عنوان عربي واضح ومختصر",
  "summary": "ملخص عربي من سطر إلى سطرين فقط"
}}

لا تضف معلومات غير موجودة في العنوان.
"""

    payload = {
        "model": "gpt-5.6-luna",
        "input": prompt
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.loads(response.read().decode("utf-8"))

        text = ""

        for output in result.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text":
                    text += content.get("text", "")

        text = text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        ai_data = json.loads(text)

        return (
            ai_data.get("title", title),
            ai_data.get("summary", "اضغط فتح المصدر لقراءة التفاصيل.")
        )

    except Exception as error:
        print("AI error:", error)
        return title, "اضغط فتح المصدر لقراءة تفاصيل الخبر."


def read_feed(source):
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)

    items = []

    for item in root.findall(".//item")[:4]:

        original_title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        source_element = item.find("source")

        source_name = (
            source_element.text.strip()
            if source_element is not None and source_element.text
            else "News"
        )

        if not original_title or not link:
            continue

        arabic_title, arabic_summary = improve_with_ai(
            original_title,
            source_name
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


all_news = []

for source in SOURCES:
    try:
        all_news.extend(read_feed(source))
    except Exception as error:
        print("Feed error:", error)

all_news = all_news[:20]

with open("news.json", "w", encoding="utf-8") as file:
    json.dump(
        all_news,
        file,
        ensure_ascii=False,
        indent=2
    )

print(f"Updated {len(all_news)} news items.")
print(datetime.now())
