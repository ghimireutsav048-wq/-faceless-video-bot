import json, os, re, time, requests
from .config import GEMINI_API_KEY, VIDEO_SECONDS

FALLBACK = [
 {"topic":"The Antikythera mechanism","angle":"An ancient Greek device that modelled astronomical cycles","fact_pack":"The Antikythera mechanism is an ancient Greek geared device recovered from a shipwreck near Antikythera. Research describes it as an ancient astronomical calculator. Avoid claiming it is the world's first computer without qualification.","source_url":"https://www.nature.com/articles/444534a"},
 {"topic":"The Wow! signal","angle":"A puzzling radio signal detected in 1977","fact_pack":"The Wow! signal was a strong narrowband radio signal detected by Ohio State University's Big Ear radio telescope in 1977. It has not been conclusively identified. Do not claim aliens sent it.","source_url":"https://www.seti.org/wow-signal"},
 {"topic":"The Tunguska event","angle":"A huge 1908 explosion over Siberia","fact_pack":"In 1908, a large explosion flattened trees over a wide area near the Podkamennaya Tunguska River in Siberia. The leading explanation is an airburst from a small asteroid or comet fragment. Avoid unsupported exact energy comparisons.","source_url":"https://science.nasa.gov/solar-system/asteroids/"},
 {"topic":"The Dancing Plague of 1518","angle":"A strange historical outbreak in Strasbourg","fact_pack":"Historical accounts describe people dancing uncontrollably in Strasbourg in 1518. Details and explanations remain debated; distinguish contemporary records from later retellings.","source_url":"https://www.britannica.com/event/dancing-plague-of-1518"},
 {"topic":"The Taos Hum","angle":"A low-frequency hum reported by some residents","fact_pack":"Some residents and visitors in Taos, New Mexico have reported hearing a persistent low-frequency hum. Investigations have not established a single definitive source. Do not present it as universally audible.","source_url":"https://www.britannica.com/story/what-is-the-taos-hum"}
]

def gemini_script(item, index):
    if not GEMINI_API_KEY:
        return None
    prompt = f"""Create a 30–45 second vertical-video narration about this fact. Use ONLY the supplied fact pack; do not add facts.
Topic: {item['topic']}
Angle: {item['angle']}
Fact pack: {item['fact_pack']}
Source URL: {item['source_url']}
Return ONLY valid JSON with keys: title (max 65 chars), hook (one sentence), narration (85-105 words), caption (max 180 chars), hashtags (array of 5), visual_queries (array of 4 short Pexels search phrases), source_url.
Keep uncertainty explicit. No invented statistics, dates, quotes, or dramatic claims."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    body = {"contents":[{"parts":[{"text":prompt}]}], "generationConfig":{"temperature":0.35,"responseMimeType":"application/json"}}
    try:
        r = requests.post(url, params={"key":GEMINI_API_KEY}, json=body, timeout=60)
        r.raise_for_status()
        data = r.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        obj = json.loads(raw)
        obj["source_url"] = item["source_url"]
        return obj
    except Exception as e:
        print("Gemini unavailable; using conservative fallback:", str(e))
        return None

def make_batch(count):
    results=[]
    for i in range(count):
        item = FALLBACK[i % len(FALLBACK)]
        obj = gemini_script(item, i)
        if not obj:
            obj = {
              "title": item["topic"] + ": The Mystery",
              "hook": "This real event still raises questions.",
              "narration": f"{item['fact_pack']} The mystery is not that we know nothing. It is that the evidence leaves important details unresolved. The careful answer is more interesting than the legend: researchers continue to examine what happened, while popular explanations often go further than the evidence allows.",
              "caption": "A real historical or scientific puzzle — facts first, speculation clearly labelled.",
              "hashtags":["#Mystery","#History","#Science","#InterestingFacts","#Shorts"],
              "visual_queries":[item["topic"],"old archive mystery","dark laboratory cinematic","historical documentary"],
              "source_url":item["source_url"]
            }
        results.append(obj)
    return results
