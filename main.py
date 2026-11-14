
import argparse
import json
import random
from pathlib import Path

from generate import make_batch
from render import render_one
from config import VOICE_POOL, DEFAULT_VIDEO_COUNT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=DEFAULT_VIDEO_COUNT)
    args = parser.parse_args()

    count = max(1, min(args.count, 5))

    output = Path("output")
    output.mkdir(exist_ok=True)

    batch = make_batch(count)

    if len(batch) < count:
        raise RuntimeError("Not enough video scripts were generated.")

    metadata = []
    voices = VOICE_POOL[:]
    random.shuffle(voices)

    for i, item in enumerate(batch, 1):
        voice = voices[(i - 1) % len(voices)]
        video = render_one(item, i, voice, output)

        record = {
            **item,
            "voice": voice,
            "video_file": str(video)
        }

        metadata.append(record)
        print("Created:", video)

    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
