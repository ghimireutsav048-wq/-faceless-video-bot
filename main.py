import argparse, json, os, random
from pathlib import Path
from .generate import make_batch
from .render import render_one
from .config import VOICE_POOL

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--count",type=int,default=1)
    args=p.parse_args()
    out=Path("output"); out.mkdir(exist_ok=True)
    batch=make_batch(max(1,min(args.count,10)))
    metadata=[]
    voices=VOICE_POOL[:]
    random.shuffle(voices)
    for i,item in enumerate(batch,1):
        voice=voices[(i-1)%len(voices)]
        video=render_one(item,i,voice,out)
        record={**item,"voice":voice,"video_file":str(video)}
        metadata.append(record)
        print("Created",video)
    (out/"metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
if __name__=="__main__": main()
