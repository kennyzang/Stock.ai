# Instructions: publishing a video with the SocialEcho API

Read the official docs first (they are the source of truth, last updated 2026-09):
https://www.socialecho.net/en/helpcenter/docs/socialecho-openapi-docs/
Most useful sections: 3 (auth), 4 (errors), 5.2 (accounts), 5.6 (upload URL), 5.12 (publish), 6 (tips).

## Setup
- Base URL: `https://api.socialecho.net`
- Auth header on every request: `Authorization: Bearer <Team API Key>` (key starts with `se_`).
  Ask the owner for the key. Keep it in an environment variable, never in git, logs or chat.
- Optional: `X-Lang: en`. Rate limit: 120 requests/minute.
- Find your TikTok account first: `GET /v1/account?type=1` and use that account's `id` as `account_id`.
  Only publish to the account the owner told you to use (check `app.title` = TikTok and `status.value` = 1).

## Points
Every API call costs team points (at least 1 each). Check `meta.ai_points.remaining` in each response.
Do not make unnecessary calls. If the balance is low or a call returns 422 with "insufficient points", stop and tell the owner.

## Publish one TikTok video
1. `GET /v1/upload/url?content_type=video%2Fmp4&title=<name>.mp4` returns `upload_url`, `headers`, `public_url`.
2. `PUT` the MP4 to `upload_url` with the returned headers (e.g. `Content-Type: video/mp4`). Use the URL unmodified.
3. `POST /v1/publish/article` with JSON:
   ```json
   {
     "account_id": <id from GET /v1/account>,
     "type": "video",
     "status": 1,
     "content": "caption #hashtags",
     "extra": { "draft": false, "is_ai_generated": false },
     "attachments": [{ "url": "<public_url>" }],
     "comment": []
   }
   ```
   Use `public_url` (not `upload_url`). Omit `scheduled_at` to publish immediately.
4. Success means `HTTP 2xx` and `code: 0`, but that only means the task was queued.
   Save `data.id` and `request_id`, then confirm the result with `GET /v1/article`.

Video limits: 1 video, up to 1 GiB, at least 360x360, 23-60 fps, 3-600 s. Caption up to 2,200 characters.

## Rules
- **Do not blindly retry a failed publish** (HTTP 422/500). A record may already exist. Check `GET /v1/article` first, or the video may post twice.
- Branch on the HTTP status, then on `code`. Log `request_id` for every call.
- Do not post the same video twice; keep a record of what has been published.
- If anything is unclear or fails twice, stop and report to the owner instead of guessing.
- Publishing cost per post is not documented. Note it from the first response message.
