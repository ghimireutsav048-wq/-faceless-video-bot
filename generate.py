
import json
import requests

from config import GEMINI_API_KEY


def make_batch(count):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it in GitHub repository Secrets."
        )

    prompt = """
You are a professional cinematic horror storyteller.

Create ONE original, extremely suspenseful horror story divided into
EXACTLY FIVE connected episodes.

HORROR STYLE:
- Haunted houses and abandoned buildings.
- Blood stains, bloody fingerprints and strange discoveries.
- Ghostly figures, unexplained noises and mysterious shadows.
- Locked rooms, hidden basements and secret passages.
- Missing people and disturbing evidence.
- Psychological horror and terrifying plot twists.

The story should feel realistic and cinematic, like a horror movie.
It is fictional. Never claim it is a true event.
Do not copy existing movies or books.

STORY RULES:
- Exactly five connected episodes.
- Each narration must contain 125-140 spoken words.
- Each episode should take approximately 60 seconds to narrate.
- Start every episode with an extremely powerful hook.
- Use natural spoken English.
- Build suspense gradually.
- Make viewers curious about what happens next.
- Avoid boring introductions and unnecessary descriptions.
- Do not repeat scenes or information unnecessarily.

EPISODES:
Part 1: Introduce the terrifying location and the first disturbing discovery.
Part 2: Reveal something even more frightening.
Part 3: Introduce a shocking discovery that changes the story.
Part 4: Bring the main character face to face with the horror.
Part 5: Reveal the truth and deliver a powerful ending.

CLIFFHANGERS:
Parts 1-4 must end with a strong suspenseful cliffhanger.
Part 5 must resolve the main mystery.

TITLES:
Create short, frightening, curiosity-driven titles.
Every episode needs its own hook.
Avoid generic titles like "A Strange Mystery".

VISUALS:
Provide exactly four cinematic visual search phrases per episode.
Use realistic horror settings, abandoned houses, basements,
blood stains, shadows, doors and mysterious figures.

Return ONLY valid JSON with this exact structure:
{
  "series_title": "A powerful horror series title",
  "episodes": [
    {
      "title": "Suspenseful episode title",
      "hook": "Powerful opening sentence",
      "narration": "125-140 words of narration",
      "caption": "Short engaging caption",
      "hashtags": [
        "#Horror",
        "#HauntedHouse",
        "#ScaryStories",
        "#PsychologicalHorror",
        "#Part1"
      ],
      "visual_queries": [
        "cinematic horror scene one",
        "cinematic horror scene two",
        "cinematic horror scene three",
        "cinematic horror scene four"
      ]
    }
  ]
}

There must be exactly five episodes.
Make the story frightening, original and highly engaging.
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash-lite:generateContent"
    )

    response = requests.post(
        url,
        params={"key": GEMINI_API_KEY},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.9,
                "responseMimeType": "application/json",
                "maxOutputTokens": 8192
            }
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"]
    result = json.loads(raw)

    episodes = result["episodes"]

    if len(episodes) != 5:
        raise RuntimeError("The AI did not create exactly five episodes.")

    series_title = result["series_title"]

    for index, episode in enumerate(episodes, 1):
        episode["series_title"] = series_title
        episode["part_number"] = index
        episode["title"] = (
            f"{series_title} - Part {index}: {episode['title']}"
        )

        if len(episode["visual_queries"]) != 4:
            raise RuntimeError("An episode is missing visual search phrases.")

    return episodes[:count]
