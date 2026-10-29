import os
import sys
import json
import time
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
    # Check if local meta_config.json exists
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

if not os.path.exists(DB_FILE):
    # Try parent or local scratch path
    alt_db = os.path.join(r"C:\Users\shann\.gemini\instagram", "content_database.json")
    if os.path.exists(alt_db):
        DB_FILE = alt_db

with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

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
    state["history"].append({
        "day": day_num,
        "post_id": post_id,
        "permalink": permalink,
        "title": title,
        "published_at": now_ist
    })
    with open(STATE_FILE, "w", encoding="utf-8") as sf:
        json.dump(state, sf, indent=2)

def is_already_published_recently(state, min_hours=12):
    """Checks if a post was already published recently (within 12 hours) to prevent duplicate runs on catch-up crons."""
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
        with urllib.request.urlopen(req, timeout=30) as resp:
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

def run_comment_sweep():
    print("💬 Running live comment sweep for keywords 'SYNC' and 'link'...", flush=True)
    try:
        media_url = f"https://graph.instagram.com/v19.0/{account_id}/media?fields=id,caption&access_token={token}"
        data = make_meta_request(media_url)
        items = data.get("data", [])
        for item in items[:5]:
            m_id = item.get("id")
            c_url = f"https://graph.instagram.com/v19.0/{m_id}/comments?fields=id,text,username&access_token={token}"
            try:
                c_data = make_meta_request(c_url)
                for c in c_data.get("data", []):
                    c_id = c.get("id")
                    c_text = c.get("text", "").lower()
                    c_user = c.get("username", "user")
                    if "sync" in c_text or "link" in c_text:
                        reply_url = f"https://graph.instagram.com/v19.0/{c_id}/replies"
                        r_params = {
                            "message": f"@{c_user} Here is your private room link: twoheartsbeat.vercel.app 🎧 Zero audio lag between you two! Vibe together tonight 🫀",
                            "access_token": token
                        }
                        r_data = urllib.parse.urlencode(r_params).encode('utf-8')
                        try:
                            make_meta_request(reply_url, data=r_data)
                            print(f"  ✓ Auto-replied to @{c_user} on comment {c_id}", flush=True)
                        except Exception as e:
                            # Already replied or permissions error
                            pass
            except Exception:
                pass
    except Exception as e:
        print(f"Comment sweep error: {e}", flush=True)

def publish_carousel_slide_with_retry(slide_idx, target_day, max_retries=3):
    """Uploads a single carousel slide container with multi-tier CDN fallback."""
    endpoints = [
        # Primary: Raw GitHub (JPG)
        f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/carousels/Day{target_day}/slide_{slide_idx}.jpg",
        # Failover 1: jsdelivr CDN (JPG)
        f"https://cdn.jsdelivr.net/gh/{REPO_OWNER}/{REPO_NAME}@{BRANCH}/carousels/Day{target_day}/slide_{slide_idx}.jpg",
        # Failover 2: Raw GitHub (PNG)
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

    now_ist_str = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    print("==================================================", flush=True)
    print(f"🚀 GITHUB CLOUD PUBLISHER: DAY {target_day} ({fmt})", flush=True)
    print(f"Timestamp: {now_ist_str} IST", flush=True)
    print(f"Account: @{handle} (ID: {account_id})", flush=True)
    print(f"Topic: {day_data.get('badge')}", flush=True)
    print("==================================================", flush=True)

    container_url = f"https://graph.instagram.com/v19.0/{account_id}/media"

    for attempt_retry in range(1, max_retries + 1):
        print(f"\n[Attempt {attempt_retry}/{max_retries}] Preparing media container for Meta Graph API...", flush=True)

        try:
            if fmt == "REEL":
                video_filename = f"Day{target_day}_Master_Cinematic_Reel_IG.mp4"
                
                # Multi-tier CDN endpoints for video
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
                slides_count = day_data.get("slides_count", 8)
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

                # Poll status for Carousel Parent to prevent Media ID not available error
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

            # Publish Container to live feed
            print("Publishing container to live feed...", flush=True)
            pub_url = f"https://graph.instagram.com/v19.0/{account_id}/media_publish"
            pub_params = {
                "creation_id": container_id,
                "access_token": token
            }
            pub_data = urllib.parse.urlencode(pub_params).encode('utf-8')
            pub_res = make_meta_request(pub_url, data=pub_data)
            post_id = pub_res.get("id")
            
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

            title = day_data.get('track_title') or day_data.get('headline') or 'Featured Post'
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
            time.sleep(10)

    print(f"❌ Failed to publish Day {target_day} after {max_retries} retries.", flush=True)
    return False

def main():
    parser = argparse.ArgumentParser(description="Two Hearts Beat Cloud Publisher")
    parser.add_argument("--day", type=int, default=None, help="Specific Day number to publish (default: auto next day)")
    parser.add_argument("--force", action="store_true", help="Force publish even if already published today")
    args = parser.parse_args()

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
