import os
import sys
import json
import time
import random
import argparse
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# IST timezone helper (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

token = os.environ.get("META_ACCESS_TOKEN")
account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
handle = "twoheartsbeat.live"
REPO_OWNER = "soumyadeepsarkar-2004"
REPO_NAME = "twoheartsbeat-automation"
BRANCH = "main"

# Fallback tokens for local testing if not in environment
if not token or not account_id:
    config_paths = [
        "meta_config.json",
        os.path.join(r"C:\Users\shann\.gemini\instagram", "meta_config.json")
    ]
    for p in config_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    token = token or cfg.get("access_token")
                    account_id = account_id or cfg.get("numerical_id") or cfg.get("instagram_account_id")
            except Exception:
                pass

if not token or not account_id:
    print("❌ ERROR: Missing META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID environment variables.", flush=True)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "log.md")
DB_FILE = os.path.join(SCRIPT_DIR, "content_database.json")
STATE_FILE = os.path.join(SCRIPT_DIR, "published_state.json")
COMMENTS_FILE = os.path.join(SCRIPT_DIR, "processed_comments.json")

if not os.path.exists(DB_FILE):
    alt_db = os.path.join(r"C:\Users\shann\.gemini\instagram", "content_database.json")
    if os.path.exists(alt_db):
        DB_FILE = alt_db

with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

def get_processed_comments():
    if os.path.exists(COMMENTS_FILE):
        try:
            with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"replied_comment_ids": []}

def save_processed_comments(data):
    try:
        with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning saving processed comments: {e}", flush=True)

def get_current_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as sf:
                return json.load(sf)
        except Exception as e:
            print(f"Warning reading state file: {e}", flush=True)
    return {"published_days": [], "last_published": 0, "history": []}

def get_next_day(state):
    published = set(state.get("published_days", []))
    total_days = max(len(db.get("days", {})), 30)
    for d in range(1, total_days + 1):
        if d not in published:
            return d
    return state.get("last_published", 0) + 1

def save_published_state(day_num, post_id, permalink, title):
    state = get_current_state()
    if day_num not in state.get("published_days", []):
        state["published_days"].append(day_num)
    state["last_published"] = day_num
    now_ist = datetime.now(IST).isoformat()
    state["last_published_at"] = now_ist
    
    # Avoid duplicate entries in history
    existing_entries = [h for h in state.get("history", []) if h.get("day") == day_num]
    if not existing_entries:
        state["history"].append({
            "day": day_num,
            "post_id": post_id,
            "permalink": permalink,
            "title": title,
            "published_at": now_ist
        })
    else:
        existing_entries[0]["post_id"] = post_id
        existing_entries[0]["permalink"] = permalink
        existing_entries[0]["title"] = title
        existing_entries[0]["published_at"] = now_ist

    with open(STATE_FILE, "w", encoding="utf-8") as sf:
        json.dump(state, sf, indent=2)
    print(f"💾 Updated state file: Day {day_num} marked as published ({post_id})", flush=True)

def is_already_published_recently(state, min_hours=12):
    """Checks if a post was already published recently to prevent duplicate runs on catch-up crons."""
    last_pub_at = state.get("last_published_at")
    if not last_pub_at:
        return False
    try:
        last_dt = datetime.fromisoformat(last_pub_at)
        now_dt = datetime.now(IST)
        diff_hours = (now_dt - last_dt.astimezone(IST)).total_seconds() / 3600.0
        return diff_hours < min_hours
    except Exception:
        return False

def make_meta_request(url, data=None, headers=None, method=None):
    """Robust HTTP request handler with detailed Meta error extraction."""
    if headers is None:
        headers = {'User-Agent': 'TwoHeartsBeatCloudAutomator/2.0'}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
            err_json = json.loads(error_body)
            err_msg = err_json.get("error", {}).get("message", error_body)
            err_code = err_json.get("error", {}).get("code", "unknown")
            err_sub = err_json.get("error", {}).get("error_subcode", "")
            raise RuntimeError(f"Meta Graph API HTTP {e.code} Error [{err_code}:{err_sub}]: {err_msg}")
        except Exception:
            raise RuntimeError(f"Meta Graph API HTTP {e.code} Error: {error_body or str(e)}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network Connection Error: {e.reason}")

def check_if_day_already_on_live_feed(target_day):
    """Queries recent live media on Instagram to see if target_day is already published on the profile."""
    day_str = str(target_day)
    day_data = db.get("days", {}).get(day_str, {})
    if not day_data:
        return None
    
    expected_title = (day_data.get("track_title") or day_data.get("headline") or "").lower().strip()
    expected_caption_snippet = day_data.get("caption", "")[:35].lower().strip()
    
    print(f"🔍 Checking Instagram live feed for Day {target_day}...", flush=True)
    try:
        media_url = f"https://graph.instagram.com/v19.0/{account_id}/media?fields=id,caption,media_type,permalink,timestamp&limit=15&access_token={token}"
        res = make_meta_request(media_url)
        for post in res.get("data", []):
            caption = post.get("caption", "").lower()
            if expected_caption_snippet and expected_caption_snippet in caption:
                return post
            if expected_title and expected_title in caption:
                return post
    except Exception as e:
        print(f"Warning checking live feed: {e}", flush=True)
    return None

REPLY_TEMPLATES = [
    "@{user} Here is your private room link: twoheartsbeat.vercel.app 🎧 Zero audio lag between you two! Vibe together tonight 🫀",
    "@{user} Built this for long distance couples! Hop in here: twoheartsbeat.vercel.app 🎵 Exact same millisecond on both ends.",
    "@{user} Grab your synced room here: twoheartsbeat.vercel.app 🎧 No app install needed, just send them the code!",
    "@{user} Here you go! twoheartsbeat.vercel.app 🫀 Create a room and listen together without any delay.",
    "@{user} Listen together in real-time here: twoheartsbeat.vercel.app 🎧 0ms lag, works on phone & laptop!"
]

INTENT_KEYWORDS = ["sync", "link", "room", "app", "website", "how", "join", "try", "code", "song"]

def run_comment_sweep():
    print("💬 Running live comment sweep for inbound intent keywords...", flush=True)
    state = get_processed_comments()
    replied_ids = set(state.get("replied_comment_ids", []))
    new_replies_count = 0

    try:
        media_url = f"https://graph.instagram.com/v19.0/{account_id}/media?fields=id,caption&limit=10&access_token={token}"
        data = make_meta_request(media_url)
        items = data.get("data", [])
        for item in items:
            m_id = item.get("id")
            c_url = f"https://graph.instagram.com/v19.0/{m_id}/comments?fields=id,text,username&access_token={token}"
            try:
                c_data = make_meta_request(c_url)
                for c in c_data.get("data", []):
                    c_id = c.get("id")
                    if c_id in replied_ids:
                        continue
                    c_text = c.get("text", "").lower()
                    c_user = c.get("username", "user")

                    if any(kw in c_text for kw in INTENT_KEYWORDS):
                        reply_msg = random.choice(REPLY_TEMPLATES).format(user=c_user)
                        reply_url = f"https://graph.instagram.com/v19.0/{c_id}/replies"
                        r_params = {
                            "message": reply_msg,
                            "access_token": token
                        }
                        r_data = urllib.parse.urlencode(r_params).encode('utf-8')
                        try:
                            make_meta_request(reply_url, data=r_data)
                            replied_ids.add(c_id)
                            new_replies_count += 1
                            print(f"  ✓ Auto-replied to @{c_user} on comment {c_id}: {reply_msg}", flush=True)
                            time.sleep(2)
                        except Exception as re:
                            print(f"  ⚠️ Reply to @{c_user} failed: {re}", flush=True)
            except Exception:
                pass

        state["replied_comment_ids"] = list(replied_ids)
        save_processed_comments(state)
        print(f"💬 Comment sweep finished. Replied to {new_replies_count} new comments.", flush=True)
    except Exception as e:
        print(f"Comment sweep error: {e}", flush=True)

def publish_carousel_slide_with_retry(slide_idx, target_day, max_retries=3):
    """Uploads a single carousel slide container with multi-tier CDN fallback."""
    endpoints = [
        f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/carousels/Day{target_day}/slide_{slide_idx}.jpg",
        f"https://cdn.jsdelivr.net/gh/{REPO_OWNER}/{REPO_NAME}@{BRANCH}/carousels/Day{target_day}/slide_{slide_idx}.jpg",
        f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/carousels/Day{target_day}/slide_{slide_idx}.png",
    ]

    container_url = f"https://graph.instagram.com/v19.0/{account_id}/media"
    last_err = None

    for attempt in range(1, max_retries + 1):
        for ep_url in endpoints:
            try:
                c_params = {
                    "image_url": ep_url,
                    "is_carousel_item": "true",
                    "access_token": token
                }
                c_data = urllib.parse.urlencode(c_params).encode('utf-8')
                res = make_meta_request(container_url, data=c_data)
                slide_container_id = res.get("id")
                if slide_container_id:
                    print(f"  ✓ Slide {slide_idx} created: {slide_container_id} (via {ep_url[:40]}...)", flush=True)
                    return slide_container_id
            except Exception as e:
                last_err = e
                time.sleep(2)

        print(f"  ⚠️ Slide {slide_idx} attempt {attempt} failed, retrying in 5s...", flush=True)
        time.sleep(5)

    raise RuntimeError(f"Failed to create container for slide {slide_idx}: {last_err}")

def publish_with_retry(target_day, max_retries=3):
    day_str = str(target_day)
    if day_str not in db["days"]:
        print(f"❌ ERROR: Day {target_day} not defined in content database.", flush=True)
        return False

    day_data = db["days"][day_str]
    fmt = day_data.get("format", "REEL")
    caption = day_data.get("caption")
    title = day_data.get('track_title') or day_data.get('headline') or 'Featured Post'

    now_ist_str = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    print("==================================================", flush=True)
    print(f"🚀 GITHUB CLOUD PUBLISHER: DAY {target_day} ({fmt})", flush=True)
    print(f"Timestamp: {now_ist_str} IST", flush=True)
    print(f"Account: @{handle} (ID: {account_id})", flush=True)
    print(f"Topic: {day_data.get('badge')}", flush=True)
    print("==================================================", flush=True)

    # 1. PRE-FLIGHT LIVE FEED RECONCILIATION
    # Check if target_day is ALREADY on the Instagram profile before doing anything!
    existing_post = check_if_day_already_on_live_feed(target_day)
    if existing_post:
        post_id = existing_post.get("id")
        permalink = existing_post.get("permalink") or f"https://www.instagram.com/{handle}/"
        print("\n==================================================", flush=True)
        print(f"✨ RECONCILED: Day {target_day} is ALREADY LIVE on Instagram!", flush=True)
        print(f"Live Post ID: {post_id}", flush=True)
        print(f"Live URL: {permalink}", flush=True)
        print("==================================================\n", flush=True)
        save_published_state(target_day, post_id, permalink, title)
        run_comment_sweep()
        return True

    container_url = f"https://graph.instagram.com/v19.0/{account_id}/media"

    for attempt_retry in range(1, max_retries + 1):
        print(f"\n[Attempt {attempt_retry}/{max_retries}] Preparing media container for Meta Graph API...", flush=True)

        try:
            if fmt == "REEL":
                video_filename = f"Day{target_day}_Master_Cinematic_Reel_IG.mp4"
                
                video_endpoints = [
                    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/reels/{video_filename}",
                    f"https://cdn.jsdelivr.net/gh/{REPO_OWNER}/{REPO_NAME}@{BRANCH}/reels/{video_filename}"
                ]

                container_id = None
                for v_url in video_endpoints:
                    print(f"Attempting Video URL: {v_url}", flush=True)
                    try:
                        container_params = {
                            "media_type": "REELS",
                            "video_url": v_url,
                            "caption": caption,
                            "access_token": token
                        }
                        data = urllib.parse.urlencode(container_params).encode('utf-8')
                        res = make_meta_request(container_url, data=data)
                        container_id = res.get("id")
                        if container_id:
                            print(f"✅ MEDIA CONTAINER CREATED: {container_id}", flush=True)
                            break
                    except Exception as e:
                        print(f"  Endpoint failed: {e}", flush=True)
                        time.sleep(3)

                if not container_id:
                    raise RuntimeError("Failed to create Reel media container from all video endpoints.")

                # Poll status
                status_url = f"https://graph.instagram.com/v19.0/{container_id}?fields=status_code,status&access_token={token}"
                print("Polling Meta video processing servers...", flush=True)

                ingestion_finished = False
                for poll in range(40):
                    time.sleep(5)
                    try:
                        s_res = make_meta_request(status_url)
                        status = s_res.get("status_code")
                        print(f"  Poll {poll+1}/40: Status = {status}", flush=True)
                        if status == "FINISHED":
                            ingestion_finished = True
                            break
                        elif status == "ERROR":
                            print(f"  ❌ Meta processing error on container: {s_res}", flush=True)
                            break
                    except Exception as pe:
                        print(f"  Poll warning (transient): {pe}", flush=True)

                if not ingestion_finished:
                    print(f"⚠️ Retrying in 10s... (Attempt {attempt_retry} failed)", flush=True)
                    time.sleep(10)
                    continue

            elif fmt == "CAROUSEL":
                slides_count = day_data.get("slides_count", 7)
                print(f"Creating Carousel with {slides_count} slides...", flush=True)
                slide_ids = []
                for s_idx in range(1, slides_count + 1):
                    slide_id = publish_carousel_slide_with_retry(s_idx, target_day)
                    slide_ids.append(slide_id)
                    time.sleep(1)

                parent_params = {
                    "media_type": "CAROUSEL",
                    "children": ",".join(slide_ids),
                    "caption": caption,
                    "access_token": token
                }
                p_data = urllib.parse.urlencode(parent_params).encode('utf-8')
                p_res = make_meta_request(container_url, data=p_data)
                container_id = p_res.get("id")
                print(f"✅ CAROUSEL PARENT CONTAINER CREATED: {container_id}", flush=True)

                # Poll status for Carousel Parent
                status_url = f"https://graph.instagram.com/v19.0/{container_id}?fields=status_code,status&access_token={token}"
                print("Polling Meta carousel processing servers...", flush=True)

                carousel_finished = False
                for poll in range(30):
                    time.sleep(5)
                    try:
                        s_res = make_meta_request(status_url)
                        status = s_res.get("status_code")
                        print(f"  Carousel Poll {poll+1}/30: Status = {status}", flush=True)
                        if status == "FINISHED":
                            carousel_finished = True
                            break
                        elif status == "ERROR":
                            print(f"  ❌ Meta carousel error: {s_res}", flush=True)
                            break
                    except Exception as pe:
                        print(f"  Poll transient warning: {pe}", flush=True)

                if not carousel_finished:
                    print(f"⚠️ Carousel ingestion not ready, retrying in 10s... (Attempt {attempt_retry} failed)", flush=True)
                    time.sleep(10)
                    continue

                # Delay 15s for Meta CDN edge cache distribution of carousel children
                print("Waiting 15s for Meta CDN edge distribution...", flush=True)
                time.sleep(15)

            # Publish Container to live feed with verification recovery
            print("Publishing container to live feed...", flush=True)
            pub_url = f"https://graph.instagram.com/v19.0/{account_id}/media_publish"
            pub_params = {
                "creation_id": container_id,
                "access_token": token
            }
            pub_data = urllib.parse.urlencode(pub_params).encode('utf-8')
            
            post_id = None
            try:
                pub_res = make_meta_request(pub_url, data=pub_data)
                post_id = pub_res.get("id")
            except Exception as pe:
                print(f"⚠️ Publish request error: {pe}", flush=True)
                print("Checking if post was actually landed by Meta backend...", flush=True)
                time.sleep(10)
                reconciled = check_if_day_already_on_live_feed(target_day)
                if reconciled:
                    post_id = reconciled.get("id")
                    print(f"✅ Verified: Post is LIVE on Instagram feed despite network/API response: {post_id}", flush=True)
                else:
                    if "2207051" in str(pe) or "action is blocked" in str(pe).lower():
                        print("🛑 Meta rate/action limit (2207051) detected. Halting retries to protect account standing.", flush=True)
                        return False
                    raise pe
            
            print("\n==================================================", flush=True)
            print(f"🎉 SUCCESS: DAY {target_day} IS LIVE ON INSTAGRAM!", flush=True)
            print(f"Live Post ID: {post_id}", flush=True)
            
            time.sleep(3)
            permalink = f"https://www.instagram.com/{handle}/"
            try:
                i_url = f"https://graph.instagram.com/v19.0/{post_id}?fields=permalink&access_token={token}"
                i_res = make_meta_request(i_url)
                permalink = i_res.get("permalink", permalink)
            except Exception:
                pass
            
            print(f"Live URL: {permalink}", flush=True)
            print("==================================================\n", flush=True)

            save_published_state(target_day, post_id, permalink, title)
            
            # Update log.md
            try:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n| **Day {target_day} ({fmt})** | `{post_id}` | {title} | 🎉 **LIVE ON FEED** | [View Post]({permalink}) |")
            except Exception as le:
                print(f"Warning updating log.md: {le}", flush=True)

            run_comment_sweep()
            return True

        except Exception as e:
            print(f"Attempt {attempt_retry} Exception: {e}", flush=True)
            if "2207051" in str(e) or "action is blocked" in str(e).lower():
                print("🛑 Meta action block detected. Stopping retry loop to protect account.", flush=True)
                return False
            time.sleep(10)

    print(f"❌ Failed to publish Day {target_day} after {max_retries} retries.", flush=True)
    return False

def main():
    parser = argparse.ArgumentParser(description="Two Hearts Beat Cloud Publisher")
    parser.add_argument("--day", type=int, default=None, help="Specific Day number to publish (default: auto next day)")
    parser.add_argument("--force", action="store_true", help="Force publish even if already published today")
    parser.add_argument("--sweep-only", action="store_true", help="Only run comment sweep and exit")
    args = parser.parse_args()

    if args.sweep_only:
        run_comment_sweep()
        sys.exit(0)

    state = get_current_state()

    # Determine target day
    if args.day is not None:
        target_day = args.day
        print(f"Manual override: Target Day specified as {target_day}", flush=True)
    else:
        target_day = get_next_day(state)

    total_days = max(len(db.get("days", {})), 30)
    if target_day > total_days:
        print(f"🎉 All {total_days} days have been published successfully! The campaign is complete.", flush=True)
        sys.exit(0)

    # Check idempotency
    force_env = os.environ.get("FORCE_PUBLISH", "").lower() in ("true", "1", "yes")
    force_run = args.force or force_env

    if not force_run and args.day is None:
        if is_already_published_recently(state, min_hours=12):
            last_day = state.get("last_published")
            last_at = state.get("last_published_at", "")
            print(f"✨ Day {last_day} was already published recently (last at {last_at}).", flush=True)
            print("Autopilot is active and in sync. Exiting safely to prevent duplicate posting.", flush=True)
            sys.exit(0)

    success = publish_with_retry(target_day)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
