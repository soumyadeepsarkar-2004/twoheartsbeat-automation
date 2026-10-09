# Master Operating Log: Two Hearts Beat Instagram Automation (@twoheartsbeat.live)
*Maintained autonomously across all 13 skills from instagram-agent-skill.*

## Account Credentials & Identity
- **Handle:** `@twoheartsbeat.live`
- **Numerical User ID:** `27727350543604731`
- **Connected URL:** https://twoheartsbeat.vercel.app/
- **Target Audience:** Indian couples & friends in Long Distance Relationships (Delhi ↔ Bangalore, Mumbai ↔ Pune, Tier-2 ↔ Metro)
- **Primary Keyword Call to Action:** `SYNC`

---

## 13-Skill Automation Architecture & Status

| Skill | Local Asset / Engine Script | Operational Role | Current Status |
|---|---|---|---|
| **`/ig-plan`** | `plan_30_days.md` | Master 30-Day calendar, daily hooks, stories & engagement targets | ✅ Active & Documented |
| **`/ig-profile`** | `profile_optimization.md` | 12-item rubric audit, name field indexing, bio copy & pinned 3 | ✅ Audited (88/100 projected) |
| **`/ig-reel`** | `generate_reel_day.py` | 1080x1920 Playwright motion graphics + TTS voice + ducked lofi music | ✅ Active (Days 1, 2, 3 Rendered) |
| **`/ig-caption`** | `validate_caption.py` | Lints visible fold (<125 chars), search terms, and <=5 hashtag cap | ✅ Active (`caption.py` integrated) |
| **`/ig-human`** | `validate_caption.py` | Detects AI markers, strips slop words via `slop.json` | ✅ Active (`detect.py` integrated) |
| **`/ig-carousel`** | `generate_carousel_day.py` | Renders 1080x1350 4:5 slide decks with high dwell time | ✅ Active (Day 4 deck generated) |
| **`/ig-story`** | Embedded in `plan_30_days.md` | Daily 4-5 frame sequences with interactive polls, quizzes, sliders | ✅ Active (30 days mapped) |
| **`/ig-comment`** | Embedded in `plan_30_days.md` | Daily 20-min 10-account engagement rounds (reach/peers/buyers) | ✅ Active (Target lists ready) |
| **`/ig-reply`** | `instagram_live_automator.py` | Triages comments into KEYWORD, LEAD, SUBSTANCE, QUESTION, SUPPORT | ✅ Active via Meta Graph API |
| **`/ig-dm`** | `instagram_live_automator.py` | Auto-delivers twoheartsbeat.vercel.app room link on keyword `SYNC` | ✅ Active via Meta Graph API |
| **`/ig-audit`** | `run_audit.py` | Pulls Meta Graph API insights, calculates hold@3s & outlier multiples | ✅ Active (`audit_report.md` created) |
| **`/ig-viral`** | `swipe.md` | Swipe file tracking top-performing formulas and outlier multiples | ✅ Active & Crated |
| **`/ig-repurpose`**| Operating Protocol | Transforms user questions and comments into new Reel scenes | ✅ Active & Integrated |

---

## Content Asset & Production Log

| Day | Format | Asset Path | Status | Live Post ID / Link |
|---|---|---|---|---|
| **Day 1** | REEL (Cinematic) | `reels_output/Day1_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `18471692641139223` ([View Live Reel](https://www.instagram.com/reel/DeSIE0EgecH/)) |
| **Day 2** | REEL (Cinematic) | `reels_output/Day2_Master_Cinematic_Reel_IG.mp4` | 📦 **RENDERED & READY** | Queued for daily schedule |
| **Day 3** | REEL (Cinematic) | `reels_output/Day3_Master_Cinematic_Reel_IG.mp4` | 📦 **RENDERED & READY** | Queued for daily schedule |
| **Day 4** | CAROUSEL | `carousel_output/Day4/slide_1.png` - `8.png` | 📦 **RENDERED & READY** | 8 high-res 1080x1350 PNG slides ready |
| **Days 5-30**| REELS & CAROUSELS | `content_database.json` & `plan_30_days.md` | 🗓️ **SCHEDULED** | Ready for on-demand / scheduled rendering |

---

## Live Automator Daemons
- **Threaded Media Server:** Serving port 8080 (`task-493`).
- **Localtunnel:** Exposing port 8080 to Meta ingest crawlers (`task-495`).
- **Live Comment & DM Responder:** `instagram_live_automator.py` polling for keyword `SYNC`.
- **Daily Master Runner:** `run_daily_automation.bat` / `daily_automation_scheduler.py`.
