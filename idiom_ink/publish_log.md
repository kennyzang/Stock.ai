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
| 12 刻舟求剑 | video + cover OK | submitted 2026-10-20 15:28 UTC | 东方既白 (7369680943181875201) | SUBMITTED: record 558227, request_id e6229172-39b8-456d-a099-cbd28822b1a2, 260 points left; verify live |
EP12 video sha256 cf0021d411801665ea6f40077365ab58342bdd4c63f8ea49082890c07d392929; cover sha256 50b6bd333bf36114bbbb9734cd651846df6a89bff27aeb9b76179136c820003f.
| 13 自相矛盾 | video + cover OK (video sha256 7874b612f81fc51ba69d7476bbe18b2c19549a698ffd7ddae59c10742f3f0146; cover sha256 0ae9fcaf2ac3d2714ddfa4f76ac1c3258832552f198fee0ca007415279662bbc; 28.6 s) | 11-13 h after EP12's real post | 星漢倦歌 (7517268381398157313) | waiting for EP12; files at idiom_ink/releases/EP13/ (posting.md there; append its pinned comment to the description) |
