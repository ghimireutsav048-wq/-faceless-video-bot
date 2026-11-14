
import asyncio
import math
import random
import struct
import wave
import subprocess
from pathlib import Path

import requests
import edge_tts

from config import *


SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "MysteryVideoFactory/1.0"
})


def run(cmd):
    subprocess.run(
        list(map(str, cmd)),
        check=True
    )


# Search Wikimedia Commons for images
def commons_image(query, dest):
    try:
        response = SESSION.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6,
                "gsrlimit": 10,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": 1080,
                "format": "json"
            },
            timeout=30
        )

        response.raise_for_status()

        pages = response.json().get(
            "query", {}
        ).get("pages", {})

        candidates = list(pages.values())
        random.shuffle(candidates)

        for page in candidates:
            info = page.get("imageinfo", [])

            if not info:
                continue

            url = info[0].get("thumburl") or info[0].get("url")

            if not url:
                continue

            image = SESSION.get(url, timeout=45)
            image.raise_for_status()

            if len(image.content) < 5000:
                continue

            Path(dest).write_bytes(image.content)

            print("Image downloaded:", page.get("title"))
            return True

    except Exception as error:
        print("Wikimedia error:", error)

    return False


# Generate narration and collect actual spoken-word timings
async def make_voice(text, dest, voice):

    voices = list(dict.fromkeys([
        voice,
        "en-US-GuyNeural",
        "en-US-JennyNeural",
        "en-GB-RyanNeural",
        "en-GB-SoniaNeural"
    ]))

    last_error = None

    for selected_voice in voices:

        for attempt in range(3):

            try:
                if Path(dest).exists():
                    Path(dest).unlink()

                communicate = edge_tts.Communicate(
                    text,
                    selected_voice
                )

                audio_data = bytearray()
                word_boundaries = []

                async for event in communicate.stream():

                    if event["type"] == "audio":
                        audio_data.extend(event["data"])

                    elif event["type"] == "WordBoundary":

                        data = event["data"]

                        word_boundaries.append({
                            "start": data["offset"] / 10000000,
                            "duration": data["duration"] / 10000000,
                            "text": data["text"]
                        })

                if len(audio_data) > 1000 and word_boundaries:

                    Path(dest).write_bytes(audio_data)

                    print("Voice created:", selected_voice)
                    print(
                        "Subtitle word timings:",
                        len(word_boundaries)
                    )

                    return word_boundaries

                raise RuntimeError(
                    "Voice audio or word timing is missing."
                )

            except Exception as error:

                last_error = error
                print("Voice retry:", error)

            await asyncio.sleep(3)

    raise RuntimeError(
        f"Voice generation failed: {last_error}"
    )


# Generate atmospheric background music
def make_ambient(path, seconds, seed):

    random.seed(seed)

    rate = 22050

    freqs = [
        random.choice([55, 65, 73, 82, 98, 110]),
        random.choice([130, 146, 164, 196]),
        random.choice([220, 247, 262, 294])
    ]

    phases = [
        random.random() * 6.28
        for _ in freqs
    ]

    with wave.open(str(path), "wb") as audio:

        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)

        chunk = []

        for n in range(int(rate * seconds)):

            t = n / rate

            value = sum(
                math.sin(2 * math.pi * f * t + p) * a
                for f, p, a in zip(
                    freqs,
                    phases,
                    [0.12, 0.055, 0.025]
                )
            )

            fade = min(
                1,
                t / 2,
                (seconds - t) / 3
            )

            sample = int(
                max(
                    -1,
                    min(1, value * fade * 0.65)
                ) * 32767
            )

            chunk.append(struct.pack("<h", sample))

            if len(chunk) >= 8192:
                audio.writeframes(b"".join(chunk))
                chunk = []

        if chunk:
            audio.writeframes(b"".join(chunk))


# Create subtitles using actual voice word timings
def make_srt(word_boundaries, seconds, path):

    def timestamp(value):

        ms = int(value * 1000)

        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        secs = (ms % 60000) // 1000
        millis = ms % 1000

        return (
            f"{hours:02}:{minutes:02}:"
            f"{secs:02},{millis:03}"
        )

    output = []

    # Display approximately four words at a time
    group_size = 4

    for i in range(0, len(word_boundaries), group_size):

        group = word_boundaries[i:i + group_size]

        if not group:
            continue

        start = max(0, group[0]["start"])

        last_word = group[-1]

        end = (
            last_word["start"]
            + last_word["duration"]
            + 0.12
        )

        end = min(seconds, end)

        if end <= start:
            continue

        caption = " ".join(
            word["text"] for word in group
        )

        output.extend([
            str(len(output) // 4 + 1),
            f"{timestamp(start)} --> {timestamp(end)}",
            caption,
            ""
        ])

    path.write_text(
        "\n".join(output),
        encoding="utf-8"
    )


def esc_drawtext(value):

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


# Turn a downloaded image into a moving video scene
def image_to_video(image, output, seconds, seed):

    random.seed(seed)

    zoom = random.choice([
        "min(zoom+0.0007,1.12)",
        "min(zoom+0.0005,1.10)"
    ])

    command = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image),
        "-vf",
        (
            f"scale={WIDTH}:{HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"zoompan=z='{zoom}':"
            f"d={int(seconds * FPS)}:"
            f"s={WIDTH}x{HEIGHT}:fps={FPS},"
            "setsar=1"
        ),
        "-t", str(seconds),
        "-r", str(FPS),
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        str(output)
    ]

    run(command)


# Render one complete 60-second video
def render_one(item, idx, voice, batch_dir):

    batch_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    slug = f"horror_{idx:02}"

    voice_file = batch_dir / f"{slug}_voice.mp3"

    word_boundaries = asyncio.run(
        make_voice(
            item["narration"],
            voice_file,
            voice
        )
    )

    clips = []

    image_queries = item.get(
        "visual_queries",
        ["cinematic horror house"] * 4
    )[:4]

    for j, query in enumerate(image_queries):

        image_file = batch_dir / f"{slug}_image{j}.jpg"
        clip_file = batch_dir / f"{slug}_clip{j}.mp4"

        if commons_image(query, image_file):

            image_to_video(
                image_file,
                clip_file,
                VIDEO_SECONDS / max(1, len(image_queries)),
                idx * 100 + j
            )

            clips.append(clip_file)

    # Create 60 seconds of atmospheric background sound
    music_file = batch_dir / f"{slug}_music.wav"

    make_ambient(
        music_file,
        VIDEO_SECONDS,
        seed=idx * 97 + len(item.get("title", ""))
    )

    # Generate subtitles from actual spoken-word timings
    subtitle_file = batch_dir / f"{slug}.srt"

    make_srt(
        word_boundaries,
        VIDEO_SECONDS,
        subtitle_file
    )

    output_file = batch_dir / f"{slug}.mp4"

    command = ["ffmpeg", "-y"]

    if clips:

        for clip in clips:
            command += ["-i", str(clip)]

        count = len(clips)
        filters = []

        for i in range(count):

            filters.append(
                f"[{i}:v]trim=duration={VIDEO_SECONDS/count},"
                f"setpts=PTS-STARTPTS[v{i}]"
            )

        inputs = "".join(
            f"[v{i}]" for i in range(count)
        )

        filters.append(
            f"{inputs}concat=n={count}:v=1:a=0,"
            f"scale={WIDTH}:{HEIGHT},fps={FPS},"
            f"drawtext=text='{esc_drawtext(BRAND_NAME)}':"
            "fontcolor=white@0.8:fontsize=34:x=60:y=90,"
            f"drawtext=text='{esc_drawtext(item['title'])}':"
            "fontcolor=white:fontsize=52:x=60:y=250,"
            f"subtitles='{subtitle_file.as_posix()}':"
            "force_style='FontName=DejaVu Sans,FontSize=18,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
            "BorderStyle=1,Outline=3,Alignment=2,MarginV=220'"
            "[vout]"
        )

        video_filter = ";".join(filters)

    else:

        command += [
            "-f", "lavfi",
            "-i",
            f"color=c=#101827:s={WIDTH}x{HEIGHT}:r={FPS}:d={VIDEO_SECONDS}"
        ]

        count = 1

        video_filter = (
            f"[0:v]zoompan=z='min(zoom+0.0005,1.08)':"
            f"d={VIDEO_SECONDS * FPS}:"
            f"s={WIDTH}x{HEIGHT}:fps={FPS},"
            f"drawtext=text='{esc_drawtext(BRAND_NAME)}':"
            "fontcolor=white@0.8:fontsize=34:x=60:y=90,"
            f"drawtext=text='{esc_drawtext(item['title'])}':"
            "fontcolor=white:fontsize=52:x=60:y=250,"
            f"subtitles='{subtitle_file.as_posix()}':"
            "force_style='FontName=DejaVu Sans,FontSize=18,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
            "BorderStyle=1,Outline=3,Alignment=2,MarginV=220'"
            "[vout]"
        )

    voice_index = count
    music_index = count + 1

    command += [
        "-i", str(voice_file),
        "-i", str(music_file),

        "-filter_complex",

        video_filter
        + f";[{voice_index}:a]volume=1.0[voice]"
        + f";[{music_index}:a]volume=0.12[music]"
        + ";[voice][music]amix=inputs=2:duration=longest:"
          "dropout_transition=0[aout]",

        "-map", "[vout]",
        "-map", "[aout]",

        "-t", str(VIDEO_SECONDS),

        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "128k",

        str(output_file)
    ]

    run(command)

    print("Finished video:", output_file)

    return output_file
