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
| **`/ig-reel`** | `generate_reel_day.py` | 1080x1920 Playwright motion graphics + Neural Voice + 5 BGMs | ✅ Upgraded (4 Visual Templates, Studio Neural Voices) |
| **`/ig-caption`** | `validate_caption.py` | Lints visible fold (<125 chars), search terms, and <=5 hashtag cap | ✅ Active (`caption.py` integrated) |
| **`/ig-human`** | `validate_caption.py` | Detects AI markers, strips slop words via `slop.json` | ✅ Active (`detect.py` integrated) |
| **`/ig-carousel`** | `generate_carousel_day.py` | Renders 1080x1350 4:5 slide decks with high dwell time | ✅ Active (Carousel parent polling active) |
| **`/ig-story`** | Embedded in `plan_30_days.md` | Daily 4-5 frame sequences with interactive polls, quizzes, sliders | ✅ Active (30 days mapped) |
| **`/ig-comment`** | Embedded in `plan_30_days.md` | Daily 20-min 10-account engagement rounds (reach/peers/buyers) | ✅ Active (Target lists ready) |
| **`/ig-reply`** | `instagram_live_automator.py` | Triages comments into KEYWORD, LEAD, SUBSTANCE, QUESTION, SUPPORT | ✅ Active via Meta Graph API |
| **`/ig-dm`** | `instagram_live_automator.py` | Auto-delivers twoheartsbeat.vercel.app room link on keyword `SYNC` | ✅ Active via Meta Graph API |
| **`/ig-audit`** | `run_audit.py` | Pulls Meta Graph API insights, calculates hold@3s & outlier multiples | ✅ Active (`audit_report.md` created) |
| **`/ig-viral`** | `swipe.md` | Swipe file tracking top-performing formulas and outlier multiples | ✅ Active & Created |
| **`/ig-repurpose`**| Operating Protocol | Transforms user questions and comments into new Reel scenes | ✅ Active & Integrated |

---

## Content Asset & Production Log

| Day | Format | Asset Path | Status | Live Post ID / Link |
|---|---|---|---|---|
| **Day 1** | REEL (Cinematic) | `reels_output/Day1_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `18471692641139223` ([View Live Reel](https://www.instagram.com/reel/DeSIE0EgecH/)) |
| **Day 2** | REEL (Cinematic) | `reels_output/Day2_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `18118273427324508` ([View Live Reel](https://www.instagram.com/reel/DeXObEZkdqd/)) |
| **Day 3** | REEL (Cinematic) | `reels_output/Day3_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `17878189179632139` ([View Live Reel](https://www.instagram.com/reel/DeXOkVwiaNn/)) |
| **Day 4** | CAROUSEL (8 Slides) | `carousels/Day4/slide_1.jpg` - `8.jpg` | 🎉 **PUBLISHED** | `17992575363047675` ([View Live Post](https://www.instagram.com/p/DeXRpB3n5PA/)) |
| **Day 5** | REEL (Cinematic) | `reels/Day5_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `18126352054881451` ([View Live Reel](https://www.instagram.com/reel/DeXUye-Ew9m/)) |
| **Day 6** | REEL (Cinematic) | `reels/Day6_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `17982633632904320` ([View Live Reel](https://www.instagram.com/reel/DeZ2rcCjwff/)) |
| **Day 7** | REEL (Cinematic) | `reels/Day7_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `18110480381228818` ([View Live Reel](https://www.instagram.com/reel/DecoWdnAtDc/)) |
| **Day 8** | REEL (Cinematic) | `reels/Day8_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `17977715631148517` ([View Live Reel](https://www.instagram.com/reel/DefBHJhgLma/)) |
| **Day 9** | REEL (Cinematic) | `reels/Day9_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `18411032008090330` ([View Live Reel](https://www.instagram.com/reel/Dehj43qn8Kz/)) |
| **Day 10** | REEL (Cinematic) | `reels/Day10_Master_Cinematic_Reel_IG.mp4` | 🎉 **PUBLISHED** | `17998109147822307` ([View Live Reel](https://www.instagram.com/reel/DekHMJIkdST/)) |
| **Day 11** | CAROUSEL (7 Slides) | `carousels/Day11/slide_1.jpg` - `7.jpg` | 🎉 **PUBLISHED** | `18131634085705141` ([View Live Post](https://www.instagram.com/p/DepL1BYmqTu/)) |
| **Days 12-16** | REELS (Multi-Template) | `reels/Day12-16_Master_Cinematic_Reel_IG.mp4` | 🚀 **STAGED IN CLOUD** | Ready for automated release |

---

## Live Automator Daemons & Cloud Engines
- **Cloud Runner:** GitHub Actions (`daily-730pm-post.yml`) active in [soumyadeepsarkar-2004/twoheartsbeat-automation](https://github.com/soumyadeepsarkar-2004/twoheartsbeat-automation).
- **Auto-Retries & Fallbacks:** Multi-tier retry engine with exponential backoff and `published_state.json` sync.
- **Live Comment & DM Responder:** `instagram_live_automator.py` polling for keyword `SYNC`.
- **Local Fallback:** Windows Task Scheduler `\TwoHeartsBeatDailyAutomation` triggering daily at 19:30:00 IST.
