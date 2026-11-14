import json, os, sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .config import YOUTUBE_PRIVACY_STATUS

def upload(video, meta, secret_json):
    data=json.loads(secret_json)
    creds=Credentials(
      token=None, refresh_token=data["refresh_token"], token_uri=data.get("token_uri","https://oauth2.googleapis.com/token"),
      client_id=data["client_id"], client_secret=data["client_secret"],
      scopes=["https://www.googleapis.com/auth/youtube.upload"])
    youtube=build("youtube","v3",credentials=creds)
    body={"snippet":{"title":meta["title"][:100],"description":meta.get("caption","")+"\\n\\nSource: "+meta.get("source_url",""),
                     "tags":[x.lstrip("#") for x in meta.get("hashtags",[])],"categoryId":"27"},
          "status":{"privacyStatus":YOUTUBE_PRIVACY_STATUS,"selfDeclaredMadeForKids":False}}
    req=youtube.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(video),chunksize=-1,resumable=True))
    response=req.execute()
    print("Uploaded video ID:",response.get("id"))
