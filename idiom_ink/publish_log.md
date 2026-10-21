# Publish log

One row per SocialEcho post. Episodes 01–05 were posted manually before automation; never repost them.

| Episode | Video file | Scheduled at (UTC) | SocialEcho record id | request_id | Points left | Verified published? |
|---|---|---|---|---|---|---|
| 06 瓜田李下 | `ep06_gua-tian-li-xia.mp4` (89.4 s) | 2026-10-16 18:34 | 543997 | 96451d82-e19a-4d18-9920-9ff8b77d4c04 | 94 | ✅ live 2026-10-16 18:36 UTC: https://www.tiktok.com/@kingkingking8888/video/7697336312990387476 |
| 10 画蛇添足 | `ep10_hua-she-tian-zu.mp4` (24.2 s, sha256 b10839f5…) | v1 sent to the WRONG session 16:00 (nothing posted); v2 (30.6 s, sha256 8a499e96…) handed to Publication 16:40 | – | – | – | – |
| 10 画蛇添足 | `ep10_hua-she-tian-zu.mp4` (30.6 s, sha256 8a499e96…70c72a2 verified) | 2026-10-19 16:57:49 | 555073 | 3d3498ee-f96f-4fc6-8cca-89bebafb6ab8 | 270 | ✅ live (post-list entry 448040026, created 2026-10-19 16:44:38 UTC, i.e. earlier than the requested 16:57:49 UTC): https://www.tiktok.com/@kingkingking8888/video/7698420789376224533 (music 东方既白 uuid 7369680943181875201, vol 18 / original 100; pinned comment appended to description) |

## Queue (publisher session; updated 2026-10-19 18:40 UTC)
Rule: 2 posts/day, each 11-13 h after the previous REAL post time (post-list time). `scheduled_at` is unreliable (EP10 went live 13 min early), so the publisher posts at the planned time with its own timer.
| Episode | Files verified (sha256) | Planned post (UTC) | Music | Status |
|---|---|---|---|---|
| 11 掩耳盗铃 | video + cover OK | submitted 2026-10-20 03:58 UTC | 星漢倦歌 (7517268381398157313) | LIVE 2026-10-20 03:56:40 UTC https://www.tiktok.com/@kingkingking8888/video/7698593934964051207 (record 555507, request_id 9c739c94-cb49-4373-b17c-406117ad40a3, 264 points left) ; EP12 timer set for 2026-10-20 15:26 UTC |
| 12 刻舟求剑 | video + cover OK | submitted 2026-10-20 15:28 UTC | 东方既白 (7369680943181875201) | LIVE 2026-10-20 15:27:12 UTC https://www.tiktok.com/@kingkingking8888/video/7698771920782642453 (record 558227, request_id e6229172-39b8-456d-a099-cbd28822b1a2, 259 points left); EP13 timer set for 2026-10-21 02:55 UTC |
EP12 video sha256 cf0021d411801665ea6f40077365ab58342bdd4c63f8ea49082890c07d392929; cover sha256 50b6bd333bf36114bbbb9734cd651846df6a89bff27aeb9b76179136c820003f.
| 13 自相矛盾 | video + cover OK | submitted 2026-10-21 03:00 UTC (first attempt failed: OSS upload tunnel reset, 422 NoSuchKey, no record created; retried) | 星漢倦歌 (7517268381398157313) | SUBMITTED: record 559014, request_id bdd3c70d-2bd3-4535-a436-efc156119ece, 254 points left; verify live |
| 14 狐假虎威 | video + cover OK (video sha256 29ba7a9675a8447de5e984d77f8729f3c81f1c478eb82cba2559a1a7b0f29cbb; cover sha256 76884095cd0f483b46e5b1ab5df5c30c4b655bc5d1f55c06a0376e7477f7eec1; 32.2 s) | 11-13 h after EP13's real post | 东方既白 (7369680943181875201) | waiting for EP13; files at idiom_ink/releases/EP14/ (posting.md there; append its pinned comment to the description) |
