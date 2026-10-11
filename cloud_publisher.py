import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

token = os.environ.get("META_ACCESS_TOKEN")
account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
handle = "twoheartsbeat.live"

if not token or not account_id:
    print("❌ ERROR: Missing META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID environment variables.", flush=True)
    sys.exit(1)

LOG_FILE = "log.md"
DB_FILE = "content_database.json"
STATE_FILE = "published_state.json"

with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

def get_next_day():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as sf:
                sdata = json.load(sf)
                last = sdata.get("last_published", 0)
                return last + 1
        except Exception as e:
            print(f"Warning reading state file: {e}", flush=True)
    return 1

def save_published_state(day_num, post_id, permalink, title):
    state = {"published_days": [], "last_published": day_num, "history": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as sf:
                state = json.load(sf)
        except Exception:
            pass
    if day_num not in state.get("published_days", []):
        state["published_days"].append(day_num)
    state["last_published"] = day_num
    state["last_published_at"] = datetime.now().isoformat()
    state["history"].append({
        "day": day_num,
        "post_id": post_id,
        "permalink": permalink,
        "title": title
    })
    with open(STATE_FILE, "w", encoding="utf-8") as sf:
        json.dump(state, sf, indent=2)

def run_comment_sweep():
    print("💬 Running live comment sweep for keyword 'SYNC'...", flush=True)
    try:
        media_url = f"https://graph.instagram.com/v19.0/{account_id}/media?fields=id,caption&access_token={token}"
        req = urllib.request.Request(media_url, headers={'User-Agent': 'CloudAutomator/2.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get("data", [])
            for item in items[:5]:
                m_id = item.get("id")
                c_url = f"https://graph.instagram.com/v19.0/{m_id}/comments?fields=id,text,username&access_token={token}"
                try:
                    with urllib.request.urlopen(urllib.request.Request(c_url)) as c_resp:
                        c_data = json.loads(c_resp.read().decode('utf-8'))
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
                                    urllib.request.urlopen(urllib.request.Request(reply_url, data=r_data))
                                    print(f"  ✓ Auto-replied to @{c_user} on comment {c_id}", flush=True)
                                except Exception:
                                    pass
                except Exception:
                    pass
    except Exception as e:
        print(f"Comment sweep error: {e}", flush=True)

def publish_with_retry(target_day, max_retries=3):
    day_str = str(target_day)
    if day_str not in db["days"]:
        print(f"Day {target_day} not defined in content database.", flush=True)
        return False

    day_data = db["days"][day_str]
    fmt = day_data.get("format", "REEL")
    caption = day_data.get("caption")

    print("==================================================", flush=True)
    print(f"🚀 GITHUB CLOUD PUBLISHER: DAY {target_day} ({fmt})", flush=True)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST", flush=True)
    print(f"Account: @{handle} (ID: {account_id})", flush=True)
    print(f"Topic: {day_data.get('badge')}", flush=True)
    print("==================================================", flush=True)

    headers = {'User-Agent': 'Mozilla/5.0'}
    container_url = f"https://graph.instagram.com/v19.0/{account_id}/media"

    for attempt_retry in range(1, max_retries + 1):
        print(f"\n[Attempt {attempt_retry}/{max_retries}] Preparing media container for Meta Graph API...", flush=True)

        try:
            if fmt == "REEL":
                video_filename = f"Day{target_day}_Master_Cinematic_Reel_IG.mp4"
                raw_video_url = f"https://raw.githubusercontent.com/soumyadeepsarkar-2004/twoheartsbeat-automation/main/reels/{video_filename}"
                print(f"Video Source: {raw_video_url}", flush=True)

                container_params = {
                    "media_type": "REELS",
                    "video_url": raw_video_url,
                    "caption": caption,
                    "access_token": token
                }
                data = urllib.parse.urlencode(container_params).encode('utf-8')
                req = urllib.request.Request(container_url, data=data, headers=headers)
                with urllib.request.urlopen(req) as resp:
                    res = json.loads(resp.read().decode('utf-8'))
                    container_id = res.get("id")
                    print(f"✅ MEDIA CONTAINER CREATED: {container_id}", flush=True)

                # Poll status
                status_url = f"https://graph.instagram.com/v19.0/{container_id}?fields=status_code,status&access_token={token}"
                print("Polling Meta video processing servers...", flush=True)

                ingestion_finished = False
                for poll in range(25):
                    time.sleep(5)
                    s_req = urllib.request.Request(status_url)
                    with urllib.request.urlopen(s_req) as s_resp:
                        s_res = json.loads(s_resp.read().decode('utf-8'))
                        status = s_res.get("status_code")
                        print(f"  Poll {poll+1}: Status = {status}", flush=True)
                        if status == "FINISHED":
                            ingestion_finished = True
                            break
                        elif status == "ERROR":
                            print(f"  ❌ Meta processing error on container: {s_res}", flush=True)
                            break

                if not ingestion_finished:
                    print(f"⚠️ Retrying in 10s... (Attempt {attempt_retry} failed)", flush=True)
                    time.sleep(10)
                    continue

            elif fmt == "CAROUSEL":
                slides_count = day_data.get("slides_count", 8)
                print(f"Creating Carousel with {slides_count} slides...", flush=True)
                slide_ids = []
                for s_idx in range(1, slides_count + 1):
                    slide_url = f"https://raw.githubusercontent.com/soumyadeepsarkar-2004/twoheartsbeat-automation/main/carousels/Day{target_day}/slide_{s_idx}.png"
                    c_params = {
                        "image_url": slide_url,
                        "is_carousel_item": "true",
                        "access_token": token
                    }
                    c_data = urllib.parse.urlencode(c_params).encode('utf-8')
                    c_req = urllib.request.Request(container_url, data=c_data, headers=headers)
                    with urllib.request.urlopen(c_req) as c_resp:
                        c_res = json.loads(c_resp.read().decode('utf-8'))
                        slide_ids.append(c_res.get("id"))
                        print(f"  ✓ Slide {s_idx}/{slides_count} container: {c_res.get('id')}", flush=True)
                    time.sleep(1)

                parent_params = {
                    "media_type": "CAROUSEL",
                    "children": ",".join(slide_ids),
                    "caption": caption,
                    "access_token": token
                }
                p_data = urllib.parse.urlencode(parent_params).encode('utf-8')
                p_req = urllib.request.Request(container_url, data=p_data, headers=headers)
                with urllib.request.urlopen(p_req) as p_resp:
                    p_res = json.loads(p_resp.read().decode('utf-8'))
                    container_id = p_res.get("id")
                    print(f"✅ CAROUSEL PARENT CONTAINER CREATED: {container_id}", flush=True)

            # Publish Container
            print("Publishing container to live feed...", flush=True)
            pub_url = f"https://graph.instagram.com/v19.0/{account_id}/media_publish"
            pub_params = {
                "creation_id": container_id,
                "access_token": token
            }
            pub_data = urllib.parse.urlencode(pub_params).encode('utf-8')
            pub_req = urllib.request.Request(pub_url, data=pub_data)
            with urllib.request.urlopen(pub_req) as pub_resp:
                pub_res = json.loads(pub_resp.read().decode('utf-8'))
                post_id = pub_res.get("id")
                print("\n==================================================", flush=True)
                print(f"🎉 SUCCESS: DAY {target_day} IS LIVE ON INSTAGRAM!", flush=True)
                print(f"Live Post ID: {post_id}", flush=True)
                
                time.sleep(3)
                permalink = f"https://www.instagram.com/{handle}/"
                try:
                    i_url = f"https://graph.instagram.com/v19.0/{post_id}?fields=permalink&access_token={token}"
                    with urllib.request.urlopen(urllib.request.Request(i_url)) as ir:
                        permalink = json.loads(ir.read().decode('utf-8')).get("permalink", permalink)
                except Exception:
                    pass
                print(f"Live URL: {permalink}", flush=True)
                print("==================================================\n", flush=True)

                title = day_data.get('track_title') or day_data.get('headline') or 'Featured Post'
                save_published_state(target_day, post_id, permalink, title)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n| **Day {target_day} ({fmt})** | `{post_id}` | {title} | 🎉 **LIVE ON FEED** | [View Post]({permalink}) |")
                
                run_comment_sweep()
                return True

        except Exception as e:
            print(f"Attempt {attempt_retry} Exception: {e}", flush=True)
            time.sleep(10)

    print(f"❌ Failed to publish Day {target_day} after {max_retries} retries.", flush=True)
    return False

if __name__ == "__main__":
    next_day = get_next_day()
    publish_with_retry(next_day)
