
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


def run(cmd):
    print("RUN", " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), check=True)


def pexels_clip(query, dest):
    if not PEXELS_API_KEY:
        return False

    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={
                "query": query,
                "per_page": 8,
                "orientation": "portrait"
            },
            timeout=30
        )
        r.raise_for_status()

        candidates = []

        for video in r.json().get("videos", []):
            for file in video.get("video_files", []):
                if file.get("width", 0) >= 480 and file.get("link"):
                    candidates.append((
                        file.get("width", 0) * file.get("height", 0),
                        file["link"]
                    ))

        if not candidates:
            return False

        candidates.sort(reverse=True)

        response = requests.get(candidates[0][1], timeout=90)
        response.raise_for_status()

        Path(dest).write_bytes(response.content)
        return True

    except Exception as error:
        print("Pexels fallback:", error)
        return False


# Voice generation with retries and backup voices
async def make_voice(text, dest, voice):

    voices = [
        voice,
        "en-US-GuyNeural",
        "en-US-JennyNeural",
        "en-GB-RyanNeural",
        "en-GB-SoniaNeural"
    ]

    last_error = None

    for selected_voice in voices:

        for attempt in range(3):

            try:
                await edge_tts.Communicate(
                    text,
                    selected_voice
                ).save(str(dest))

                if (
                    Path(dest).exists()
                    and Path(dest).stat().st_size > 1000
                ):
                    print("Voice created:", selected_voice)
                    return

            except Exception as error:
                last_error = error
                print(
                    "Voice retry:",
                    selected_voice,
                    attempt + 1,
                    error
                )

            await asyncio.sleep(2)

    raise RuntimeError(
        f"All voice attempts failed: {last_error}"
    )


def make_ambient(path, seconds, seed):

    random.seed(seed)
    rate = 22050

    freqs = [
        random.choice([55, 65, 73, 82, 98, 110]),
        random.choice([130, 146, 164, 196]),
        random.choice([220, 247, 262, 294])
    ]

    phases = [random.random() * 6.28 for _ in freqs]

    with wave.open(str(path), "wb") as w:

        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)

        chunk = []

        for n in range(int(rate * seconds)):

            t = n / rate

            val = sum(
                math.sin(2 * math.pi * f * t + p) * a
                for f, p, a in zip(
                    freqs,
                    phases,
                    [0.12, 0.055, 0.025]
                )
            )

            fade = min(1, t / 2, (seconds - t) / 3)

            chunk.append(
                struct.pack(
                    "<h",
                    int(max(-1, min(1, val * fade * 0.65)) * 32767)
                )
            )

            if len(chunk) >= 8192:
                w.writeframes(b"".join(chunk))
                chunk = []

        if chunk:
            w.writeframes(b"".join(chunk))


def make_srt(text, seconds, path):

    words = text.split()

    chunks = [
        " ".join(words[i:i + 6])
        for i in range(0, len(words), 6)
    ]

    per = seconds / max(1, len(chunks))

    def ts(s):
        ms = int(s * 1000)
        h = ms // 3600000
        m = (ms % 3600000) // 60000
        sec = (ms % 60000) // 1000
        milli = ms % 1000

        return f"{h:02}:{m:02}:{sec:02},{milli:03}"

    out = []

    for i, chunk in enumerate(chunks):

        out += [
            str(i + 1),
            f"{ts(i * per)} --> {ts(min(seconds, (i + 1) * per))}",
            chunk,
            ""
        ]

    path.write_text("\n".join(out), encoding="utf-8")


def esc_drawtext(s):

    return (
        s.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def render_one(item, idx, voice, batch_dir):

    batch_dir.mkdir(parents=True, exist_ok=True)

    slug = f"mystery_{idx:02d}"

    voice_mp3 = batch_dir / f"{slug}_voice.mp3"

    asyncio.run(
        make_voice(
            item["narration"],
            voice_mp3,
            voice
        )
    )

    clips = []

    for j, query in enumerate(
        item.get(
            "visual_queries",
            ["mystery documentary"] * 4
        )[:4]
    ):

        clip = batch_dir / f"{slug}_clip{j}.mp4"

        if pexels_clip(query, clip):
            clips.append(clip)

    music = batch_dir / f"{slug}_music.wav"

    make_ambient(
        music,
        VIDEO_SECONDS,
        seed=idx * 97 + len(item.get("title", ""))
    )

    srt = batch_dir / f"{slug}.srt"

    make_srt(
        item["narration"],
        VIDEO_SECONDS,
        srt
    )

    output = batch_dir / f"{slug}.mp4"

    cmd = ["ffmpeg", "-y"]

    if clips:

        for clip in clips:
            cmd += ["-i", str(clip)]

        video_count = len(clips)

        vfilters = []

        for i in range(video_count):

            vfilters.append(
                f"[{i}:v]"
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},"
                f"trim=duration={VIDEO_SECONDS / video_count}[v{i}]"
            )

        inputs = "".join(
            f"[v{i}]"
            for i in range(video_count)
        )

        vfilters.append(
            f"{inputs}"
            f"concat=n={video_count}:v=1:a=0,"
            f"drawtext=text='{esc_drawtext(BRAND_NAME)}':"
            f"fontcolor=white@0.78:fontsize=34:x=60:y=90,"
            f"drawtext=text='{esc_drawtext(item['title'])}':"
            f"fontcolor=white:fontsize=58:x=60:y=250:line_spacing=12,"
            f"subtitles='{srt.as_posix()}':"
            f"force_style='FontName=DejaVu Sans,FontSize=18,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
            f"BorderStyle=1,Outline=3,Alignment=2,MarginV=220'[vout]"
        )

        vgraph = ";".join(vfilters)

    else:

        cmd += [
            "-f", "lavfi",
            "-i",
            f"color=c=#101827:s={WIDTH}x{HEIGHT}:r={FPS}:d={VIDEO_SECONDS}"
        ]

        video_count = 1

        vgraph = (
            f"[0:v]"
            f"zoompan=z='min(zoom+0.0005,1.08)':"
            f"d={VIDEO_SECONDS * FPS}:"
            f"s={WIDTH}x{HEIGHT}:fps={FPS},"
            f"drawtext=text='{esc_drawtext(BRAND_NAME)}':"
            f"fontcolor=white@0.78:fontsize=34:x=60:y=90,"
            f"drawtext=text='{esc_drawtext(item['title'])}':"
            f"fontcolor=white:fontsize=58:x=60:y=250:line_spacing=12,"
            f"subtitles='{srt.as_posix()}':"
            f"force_style='FontName=DejaVu Sans,FontSize=18,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
            f"BorderStyle=1,Outline=3,Alignment=2,MarginV=220'[vout]"
        )

    voice_idx = video_count
    music_idx = video_count + 1

    cmd += [
        "-i", str(voice_mp3),
        "-i", str(music)
    ]

    graph = (
        vgraph
        + f";[{voice_idx}:a]volume=1.0[voice]"
        + f";[{music_idx}:a]volume=0.12[music]"
        + ";[voice][music]"
        + "amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd += [
        "-filter_complex", graph,
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", str(VIDEO_SECONDS),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output)
    ]

    run(cmd)

    return output
