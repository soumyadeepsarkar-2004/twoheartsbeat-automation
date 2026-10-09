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
    print("❌ ERROR: Missing META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID environment variables.")
    sys.exit(1)

LOG_FILE = "log.md"
DB_FILE = "content_database.json"

with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

def determine_next_day():
    if not os.path.exists(LOG_FILE):
        return 1
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    published_days = []
    for line in content.splitlines():
        if "Day " in line and "LIVE ON FEED" in line:
            parts = line.split("|")
            if len(parts) > 1:
                col = parts[1].strip()
                if "Day " in col:
                    try:
                        num = int(col.replace("**", "").replace("Day ", "").split()[0])
                        published_days.append(num)
                    except Exception:
                        pass
    if published_days:
        return max(published_days) + 1
    return 1

def run_comment_sweep():
    print("💬 Running live comment sweep for keyword 'SYNC'...")
    try:
        media_url = f"https://graph.instagram.com/v19.0/{account_id}/media?fields=id,caption&access_token={token}"
        req = urllib.request.Request(media_url, headers={'User-Agent': 'CloudAutomator/1.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get("data", [])
            for item in items[:3]:
                m_id = item.get("id")
                c_url = f"https://graph.instagram.com/v19.0/{m_id}/comments?fields=id,text,username&access_token={token}"
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
                                print(f"  ✓ Auto-replied to @{c_user} on comment {c_id}")
                            except Exception as re:
                                pass
    except Exception as e:
        print(f"Comment sweep error: {e}")

def publish_daily_post():
    target_day = determine_next_day()
    day_str = str(target_day)
    
    if day_str not in db["days"]:
        print(f"Day {target_day} not defined in content database.")
        return

    day_data = db["days"][day_str]
    fmt = day_data.get("format", "REEL")
    print("==================================================")
    print(f"🚀 GITHUB CLOUD PUBLISHER: DAY {target_day} ({fmt})")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")
    print(f"Account: @{handle} (ID: {account_id})")
    print(f"Topic: {day_data.get('badge')}")
    print("==================================================")

    # Raw GitHub URL for high-speed CDN streaming
    video_filename = f"Day{target_day}_Master_Cinematic_Reel_IG.mp4"
    raw_video_url = f"https://raw.githubusercontent.com/soumyadeepsarkar-2004/twoheartsbeat-automation/main/reels/{video_filename}"
    
    print(f"Submitting media container to Meta Graph API...")
    print(f"Video Source: {raw_video_url}")

    container_url = f"https://graph.instagram.com/v19.0/{account_id}/media"
    container_params = {
        "media_type": "REELS",
        "video_url": raw_video_url,
        "caption": day_data.get("caption"),
        "access_token": token
    }
    headers = {'User-Agent': 'TwoHeartsBeatCloudPublisher/1.0'}
    data = urllib.parse.urlencode(container_params).encode('utf-8')
    req = urllib.request.Request(container_url, data=data, headers=headers)
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        container_id = res.get("id")
        print(f"✅ MEDIA CONTAINER CREATED: {container_id}")

    status_url = f"https://graph.instagram.com/v19.0/{container_id}?fields=status_code,status&access_token={token}"
    print("Polling Meta video processing servers...")
    
    for attempt in range(20):
        time.sleep(5)
        s_req = urllib.request.Request(status_url)
        with urllib.request.urlopen(s_req) as s_resp:
            s_res = json.loads(s_resp.read().decode('utf-8'))
            status = s_res.get("status_code")
            print(f"  Attempt {attempt+1}: Status = {status}")
            if status == "FINISHED":
                print("✅ META INGESTION COMPLETE!")
                break
            elif status == "ERROR":
                print("❌ Meta Processing Error:", s_res)
                sys.exit(1)

    print("Publishing container to live feed...")
    pub_url = f"https://graph.instagram.com/v19.0/{account_id}/media_publish"
    pub_params = {
        "creation_id": container_id,
        "access_token": token
    }
    p_data = urllib.parse.urlencode(pub_params).encode('utf-8')
    p_req = urllib.request.Request(pub_url, data=p_data)
    with urllib.request.urlopen(p_req) as p_resp:
        p_res = json.loads(p_resp.read().decode('utf-8'))
        post_id = p_res.get("id")
        print("\n==================================================")
        print(f"🎉 SUCCESS: DAY {target_day} REEL IS LIVE ON INSTAGRAM!")
        print(f"Live Post ID: {post_id}")
        print(f"URL: https://www.instagram.com/{handle}/")
        print("==================================================\n")

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n| **Day {target_day} (Cloud)** | `{post_id}` | 1080x1920 9:16 Vertical, {day_data.get('track_title')}, Motion Graphics + Lofi Beat | 🎉 **LIVE ON FEED** |")

    # Run comment & DM sweep
    run_comment_sweep()

if __name__ == "__main__":
    publish_daily_post()
