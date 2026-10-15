# Hand-over: SocialEcho publishing for "Idiom Ink" TikTok

Written 2026-10-15 by the cloud session that investigated the SocialEcho API.
Audience: the Claude session running on the GPU instance (`cpod-1vrgybf1nkdu`).
No secrets are stored in this file. See "Credentials" below.

## 1. Objective

Fully unattended publishing of the finished "Idiom Ink" videos (see the GPU
server's `README_HANDOVER.md` / `PRODUCTION_GUIDE.md`) to the owner's TikTok
account via the SocialEcho API:

- One video every **7 to 9 hours**, with a random gap each time (never a fixed
  8 h), so the cadence does not look robotic.
- Total automation: no human step per post.
- The video source is not decided yet. The GPU session produces videos, so the
  open design question is how a finished MP4 gets from the GPU box to the
  uploader (see section 7).

## 2. SocialEcho connection (verified)

| Item | Value |
|---|---|
| Docs | https://www.socialecho.net/en/helpcenter/docs/socialecho-openapi-docs/ |
| Base URL | `https://api.socialecho.net` |
| Auth | `Authorization: Bearer se_...` (Team API Key) |
| Optional header | `X-Lang: en` (or `zh_CN`) |
| Rate limit | 120 requests/minute per key |
| Team | "Chinese Idioms", id `22626`, code `IAXNMQ`, timezone Atlantic/Cape_Verde (UTC-01:00) |
| TikTok account | "Idiom Ink \| Chinese Idioms", handle `kingkingking8888`, **account_id `22788134`**, status Normal, 12 followers |

Verified calls on 2026-10-15: `GET /v1/team`, `GET /v1/account?type=1`,
`GET /v1/upload/url`. All returned `code: 0`.

### Credentials

- The key was added to the cloud session's network-secret proxy for host
  `api.socialecho.net`; the proxy injects the `Authorization` header, so the
  cloud session never saw the key itself. Calls were made with plain `curl`
  and no header.
- **The GPU session will NOT have that proxy.** The owner must give it the Team
  API Key (`se_...`) another way (environment variable on the server, never
  committed to git or written into this file). Ask the owner.

## 3. Points (credits)

- Every API call consumes team points. Start: 0 (calls failed with 42200
  "insufficient points"), then the owner topped up to 100.
- Measured cost: `GET /v1/team` = 1, `GET /v1/account` = 1,
  `GET /v1/upload/url` = 1. **Remaining after those calls: 97.**
- **Publish cost is unknown.** The docs do not state it. The response `message`
  field reports it ("This operation used N points; the team has M remaining"),
  so read it from the first real post and log it.
- Budget guess: a post is roughly upload-url (1) + publish (>=1) + optional
  status check (1), about 3+ points. At ~3 posts/day that is ~9+ points/day,
  so 97 points lasts roughly 10 days. Ask the owner to top up before it runs out.
- Always record `meta.ai_points.remaining` from each response and stop the loop
  with a clear log when it falls below a safe threshold (suggest <= 6).

## 4. Publishing flow for a TikTok video

1. `GET /v1/upload/url?content_type=video%2Fmp4&title=<name>.mp4`
   returns `upload_url`, `method` (PUT), `headers`, `public_url`, `expire_in` (600 s).
2. `PUT` the MP4 to `upload_url`, using the method, URL and headers exactly as
   returned (the URL is signed and time-limited; do not modify or cache it).
   Example: `curl -X PUT "$UPLOAD_URL" -H "Content-Type: video/mp4" --upload-file video.mp4`
3. `POST /v1/publish/article` (JSON):
   ```json
   {
     "account_id": 22788134,
     "type": "video",
     "status": 1,
     "content": "caption and #hashtags (max 2,200 UTF-16 code units)",
     "extra": { "draft": false, "is_ai_generated": true },
     "attachments": [{ "url": "<public_url from step 1>" }],
     "comment": []
   }
   ```
   - `is_ai_generated` must be `true` (the production guide requires TikTok's AI-generated label on every post).
   - Use `public_url`, never `upload_url`, in `attachments[].url`.
   - `scheduled_at` is optional (publishes immediately when omitted; timestamps
     without a timezone are parsed in the team timezone, UTC-01:00).
   - `extra.music` is optional (needs all nine fields if used; see docs 5.9-5.11).
   - TikTok `title` in `extra` is **not supported** for type `video`.
4. Success response: `{"code":0,"message":"Submitted successfully","data":{"id":<record id>}}`.
   This only means the task was queued. Real publishing and TikTok review are
   asynchronous.
5. Confirm the outcome with `GET /v1/article` (post list). Save `data.id` and
   `request_id` from every publish call.

### TikTok video limits (from docs table 5.12.1)

Exactly 1 video; max 1 GiB; min 360x360; 23-60 fps; 3-600 seconds; caption
max 2,200 UTF-16 code units. (The finished episodes are 70-85 s, so this fits.)

### Open question to resolve with the first test post

The docs mark `extra.draft` (boolean) as required for TikTok video AND have a
top-level `status` (0 = draft, 1 = publish). Their relationship is not
explained. Draft mode (`status: 0`) also needs a team "draft permission" and may
return 403 / 40300. Test one real post and note what happens.

## 5. Error handling rules (from docs)

- Branch on HTTP status first; success = 2xx AND `code == 0`. Always parse the
  JSON body of non-2xx responses and log `request_id`.
- 401/40100 bad key. 403/40300 not permitted (do not retry unchanged). 404 resource not
  in this team. 409 conflict. 413 payload too large. 422/42200 validation or business
  prerequisite (including insufficient points). 429-style rate limit: honour `Retry-After`.
  500/50000 server error.
- **Never blindly retry a publish call.** On 422 or 500 a publish record may
  still have been created. First save `request_id`, check `GET /v1/article` to see
  whether a record exists, and only then decide whether to retry. Otherwise the
  same video can be posted twice.
- Pass `account_id` from `GET /v1/account` so the account is always inside the team.

## 6. Proposed schedule design (not built yet)

Chain of self-scheduling runs, not a fixed cron:

1. At the start of each run, FIRST pick `delay = random(7h, 9h)` (e.g. a uniform
   random number of minutes between 420 and 540) and schedule the next run, so a
   crash later in the run cannot break the chain.
2. Then: pick the next ready video, upload, publish, verify via `GET /v1/article`,
   log the points remaining and the record id.
3. On any failure: log it, do not double-post, stop the chain after repeated
   failures, and tell the owner. Also stop when points are low.

On the GPU server this can be a long-running loop or a cron/systemd timer that
re-arms itself with a random delay. The cloud session alternatively could use
its scheduled-task tools, but a scheduled cloud run has no access to the GPU box.

## 7. Open decisions for the owner / GPU session

1. **Where does the video come from, and how does it reach the uploader?**
   Simplest: run the whole pipeline on the GPU server (it already makes the videos),
   including this SocialEcho uploader. That removes any file transfer.
2. A queue convention, e.g. `/root/autodl-tmp/idiom_handover/publish_queue/epNN/video.mp4` plus
   a `posting.md` for the caption (the handover README says each episode already has
   a `posting.md`; check its format before writing the uploader), and a `published/`
   folder or a state file so nothing is posted twice.
3. How the SocialEcho key reaches the GPU server (environment variable, not git).
4. Top-up plan for points, and what the uploader does at low balance.
5. Whether a first test post should be a real publish or a draft (see section 4).
6. TikTok policy: the owner wants natural-looking timing. Randomised gaps are
   fine, but the content must follow TikTok's rules on repetitive/automated
   posting; this cannot be guaranteed by the API.

## 8. Infrastructure notes (read-only facts learned so far)

- The cloud session could NOT reach the GPU server: port 26218 times out from its
  container, no `ssh` client is installed, and a tunnel attempt through the egress
  proxy was blocked by the safety classifier. Network allowlist changes did not
  take effect for raw SSH in that session.
- GPU instance via CompShare (UCloud-style API, `https://api.compshare.cn`, signed
  requests with PublicKey/PrivateKey, SHA1 over sorted params + private key,
  not Bearer). Instance `cpod-1vrgybf1nkdu`, zone `cn-sh2-01`, state Running, GPU type
  RTX 5090, pay-as-you-go, image `cuda132_torch2130_py312`.
  - The API reported `GPU: 0` while Running, which may mean it was started in no-GPU
    mode (`SupportWithoutGpuStart`). Check `nvidia-smi` before rendering.
  - The CompShare API manages the instance only (list/start/stop); it cannot run commands.
- Security: the SSH password and the CompShare private key were pasted into the old
  chat. Both should be rotated by the owner; they are not recorded here.
- Never modify other projects on the GPU server (the README notes it is shared).

## 9. Suggested first steps for the GPU session

1. Read the server's `README_HANDOVER.md` and `PRODUCTION_GUIDE.md`.
2. Ask the owner for the SocialEcho Team API Key; set `SOCIALECHO_KEY` in the environment.
3. Re-verify: `curl -H "Authorization: Bearer $SOCIALECHO_KEY" https://api.socialecho.net/v1/team`
   (costs 1 point).
4. With the owner's approval, do ONE test publish of an existing finished episode
   (episodes 3-5 are finished) and record the points cost and the final status from
   `GET /v1/article`.
5. Then build the random 7-9 h loop in section 6, with logging and the guards in section 5.
