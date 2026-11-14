# Mystery Video Factory (free-tier starter)

A GitHub Actions pipeline that creates vertical 30–45 second mystery/fact videos using:
- Gemini API (optional, free-tier subject to Google quotas) for grounded script drafts
- Pexels API (free key) for stock footage
- `edge-tts` for different Microsoft Edge neural voices (free to use, unofficial endpoint; may change or rate-limit)
- FFmpeg for rendering
- Original synthesized ambient audio (no music API and no music licensing dependency)
- YouTube Data API for upload (OAuth setup required)

**No Creatomate. No paid rendering API.** GitHub-hosted Actions on public repositories are free under GitHub's current policy. Private repos have included minutes and may incur charges if exceeded. See GitHub's billing docs.

## Important limitations
1. "Free" means no paid rendering service. Gemini/Pexels free quotas and service availability can change.
2. This starter does not promise ten fully AI-generated videos every day. It uses stock footage and programmatically generated ambient audio; it does not generate AI video clips.
3. Gemini drafts are grounded with Google Search where available, but automated research can still be wrong. Keep `AUTO_PUBLISH=false` until you have reviewed test videos and scripts.
4. TikTok Direct Post is intentionally not wired into this starter. TikTok requires an approved `video.publish` scope and an audited app for public posting; unaudited apps are restricted to private posting. TikTok also restricts apps that exist only for internal use. Upload to TikTok manually until you have a compliant approved integration.
5. YouTube uploads require a Google Cloud project, YouTube Data API v3, and OAuth credentials. A newly created/unverified API project may have upload restrictions.
6. `edge-tts` is an unofficial client for Microsoft's public Edge TTS service, not a guaranteed production API. If it stops working, replace it with local Piper TTS.

## 1. Create the GitHub repository on iPhone
1. Open https://github.com/new in Safari.
2. Create a **public** repository named `mystery-video-factory` (public Actions runners are free under GitHub's current policy).
3. Upload/extract the contents of this ZIP into the repository. On iPhone, the easiest route is GitHub website → Add file → Upload files. If the GitHub mobile app cannot upload folders, use Safari's desktop website or upload files individually.
4. In the repo, open **Settings → Secrets and variables → Actions → New repository secret**.
5. Add:
   - `GEMINI_API_KEY` (optional, from https://aistudio.google.com/)
   - `PEXELS_API_KEY` (from https://www.pexels.com/api/)
   - `YOUTUBE_CLIENT_SECRET_JSON` (optional initially; see YouTube setup below)

Never put API keys in source files or commit them.

## 2. Run a test
1. Open **Actions** in the repository.
2. Select **Mystery Video Factory**.
3. Tap **Run workflow**.
4. Set `number_of_videos` to `1`, and `publish_to_youtube` to `false`.
5. When complete, open the run and download the `mystery-videos` artifact. Review the MP4 and `metadata.json`.

## 3. Turn on scheduled production
The workflow runs daily at 08:15 UTC and 17:15 UTC (GitHub schedules can be delayed). It creates one video per run by default. Change the cron schedule and `DEFAULT_VIDEO_COUNT` only after confirming that the free runner quota and the free API quotas are sufficient. Ten videos/day may take longer than the free-tier budget and may be throttled.

## 4. YouTube setup (optional)
1. Go to https://console.cloud.google.com/ and create a project.
2. Enable **YouTube Data API v3**.
3. Configure OAuth consent screen and create an OAuth Client ID (Desktop app).
4. Run the workflow with YouTube publishing disabled until you have generated a valid refresh-token JSON using Google's OAuth flow on a computer. The secret `YOUTUBE_CLIENT_SECRET_JSON` expects a JSON object containing the OAuth client fields plus a `refresh_token`. Store the entire JSON string as the GitHub secret.
5. Set `publish_to_youtube=true` on a manual workflow run.
6. First upload may be private while you test. Change `YOUTUBE_PRIVACY_STATUS` to `public` only after checking your content and API project status.

The API's default `videos.insert` quota is documented by Google; verify your current project quota in Cloud Console.

## 5. TikTok
This project exports TikTok-ready 9:16 MP4s as workflow artifacts. Upload manually in the TikTok app. Do not use browser automation or unofficial auto-clickers to bypass TikTok controls. For official automation, see TikTok's Content Posting API and its audit requirements:
https://developers.tiktok.com/docs/en/content-posting-api-get-started

## Settings
Edit `factory/config.py`:
- `DEFAULT_VIDEO_COUNT`
- `VIDEO_SECONDS` (30–45)
- `VOICE_POOL` (different voice picked per video)
- `BRAND_NAME` and visual colours
- `AUTO_PUBLISH` defaults to false for safety

## Fact quality
The script generator requests a verifiable source URL and asks Gemini to use Google Search grounding. Check `metadata.json` before publishing. Do not publish claims with missing/weak sources. Never treat an AI-generated script as proof.

## License
Your own code is provided for reuse. Pexels media remains subject to Pexels' license and terms. Review the license for each source.
