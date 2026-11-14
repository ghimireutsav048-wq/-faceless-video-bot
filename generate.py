import json
import requests

from config import GEMINI_API_KEY

FALLBACK = [
    {
        "topic": "The Antikythera mechanism",
        "angle": "An ancient machine that calculated astronomical cycles",
        "fact_pack": (
            "The Antikythera mechanism is an ancient Greek geared device "
            "recovered from a shipwreck near Antikythera. Researchers describe "
            "it as an ancient astronomical calculator."
        ),
        "source_url": "https://www.nature.com/articles/444534a"
    },
    {
        "topic": "The Wow! signal",
        "angle": "A mysterious radio signal detected in 1977",
        "fact_pack": (
            "A strong narrowband radio signal was detected by Ohio State "
            "University's Big Ear radio telescope in 1977. Its origin has "
            "not been conclusively identified."
        ),
        "source_url": "https://www.seti.org/wow-signal"
    },
    {
        "topic": "The Tunguska event",
        "angle": "A massive explosion over Siberia in 1908",
        "fact_pack": (
            "In 1908, a huge explosion flattened trees over a wide area "
            "near the Podkamennaya Tunguska River in Siberia. The leading "
            "explanation is an airburst from a small asteroid or comet fragment."
        ),
        "source_url": "https://science.nasa.gov/solar-system/asteroids/"
    },
    {
        "topic": "The Dancing Plague of 1518",
        "angle": "People reportedly dancing uncontrollably in Strasbourg",
        "fact_pack": (
            "Historical accounts describe people dancing uncontrollably "
            "in Strasbourg in 1518. The details and explanations remain debated."
        ),
        "source_url": "https://www.britannica.com/event/dancing-plague-of-1518"
    },
    {
        "topic": "The Taos Hum",
        "angle": "A strange low-frequency sound reported by residents",
        "fact_pack": (
            "Some residents and visitors in Taos, New Mexico, report hearing "
            "a persistent low-frequency hum. Investigations have not established "
            "one definitive source."
        ),
        "source_url": "https://www.britannica.com/story/what-is-the-taos-hum"
    }
]
def gemini_script(item):
    if not GEMINI_API_KEY:
        return None

    prompt = f"""
You are a professional TikTok mystery storyteller.

Create a highly engaging 30-45 second faceless video script.

TOPIC: {item['topic']}
ANGLE: {item['angle']}
VERIFIED FACTS: {item['fact_pack']}

STRICT RULES:
- Use ONLY the verified facts provided.
- Never invent dates, statistics, quotes or events.
- Do not present theories as proven facts.
- Write natural spoken English, not encyclopedia language.
- Narration must contain 85-105 words.

STORY STRUCTURE:
1. First sentence: a powerful curiosity hook.
2. Quickly introduce the real event.
3. Reveal the strangest verified detail.
4. Build suspense using short, natural sentences.
5. Explain what is known and what remains unknown.
6. Finish with an interesting question viewers may want to answer.

STYLE:
- Make viewers curious immediately.
- Use short, punchy sentences.
- Keep the mystery alive until the ending.
- Avoid boring introductions.
- Avoid generic phrases such as "Today we will explore".
- No fake danger or exaggerated claims.

Return ONLY valid JSON with these exact keys:
title, hook, narration, caption, hashtags, visual_queries, source_url

Requirements:
- title: maximum 65 characters.
- hook: one powerful sentence.
- narration: 85-105 words.
- caption: maximum 180 characters.
- hashtags: exactly 5.
- visual_queries: exactly 4 visual search phrases.
- source_url: use the supplied source.

SOURCE:
{item['source_url']}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=body,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(raw)

        result["source_url"] = item["source_url"]
        return result

    except Exception as error:
        print("Gemini unavailable:", str(error))
        return None
def make_batch(count):
    results = []

    for i in range(count):
        item = FALLBACK[i % len(FALLBACK)]

        story = gemini_script(item)

        if not story:
            story = {
                "title": item["topic"] + ": The Unsolved Mystery",
                "hook": "This real mystery is stranger than you might expect.",
                "narration": (
                    f"{item['topic']} is a real historical or scientific mystery. "
                    f"But what actually happened? {item['fact_pack']} "
                    "Researchers have studied this mystery, but important "
                    "questions remain unanswered. Some explanations sound "
                    "convincing, while others go beyond the available evidence. "
                    "The most interesting part is what we still cannot prove. "
                    "What do you think is the most likely explanation?"
                ),
                "caption": (
                    "A real mystery with unanswered questions. "
                    "What do you think happened?"
                ),
                "hashtags": [
                    "#Mystery",
                    "#UnsolvedMystery",
                    "#InterestingFacts",
                    "#History",
                    "#TikTokFacts"
                ],
                "visual_queries": [
                    item["topic"],
                    "cinematic historical mystery",
                    "dark documentary atmosphere",
                    "mysterious investigation"
                ],
                "source_url": item["source_url"]
            }

        results.append(story)

    return results
