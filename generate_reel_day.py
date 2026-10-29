import os
import sys
import json
import argparse
import subprocess
import time
import asyncio
from playwright.sync_api import sync_playwright
import imageio_ffmpeg
import edge_tts

sys.stdout.reconfigure(encoding='utf-8')

ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
scratch_dir = r"C:\Users\shann\.gemini\antigravity\scratch"
config_dir = r"C:\Users\shann\.gemini\instagram"
cloud_repo_dir = os.path.join(scratch_dir, "cloud_repo")
motion_assets = os.path.join(scratch_dir, "motion_assets")
motion_renders = os.path.join(scratch_dir, "motion_renders")
output_dir = os.path.join(scratch_dir, "reels_output")
reels_cloud_dir = os.path.join(cloud_repo_dir, "reels")

os.makedirs(motion_assets, exist_ok=True)
os.makedirs(motion_renders, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)
os.makedirs(reels_cloud_dir, exist_ok=True)

# 1. Load content database
db_path = os.path.join(cloud_repo_dir, "content_database.json")
if not os.path.exists(db_path):
    db_path = os.path.join(config_dir, "content_database.json")

with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

async def synthesize_neural_voice(text, voice_name, output_mp3):
    """Generates studio-grade expressive Indian English voiceover via edge-tts."""
    print(f"🎙️ Generating Neural Voiceover [{voice_name}]...")
    communicate = edge_tts.Communicate(text, voice_name, rate="+3%", pitch="+0Hz")
    await communicate.save(output_mp3)
    print(f"  ✓ Studio Voiceover saved: {output_mp3} ({os.path.getsize(output_mp3)} bytes)")

def render_day_reel(day_num):
    day_str = str(day_num)
    if day_str not in db["days"]:
        raise ValueError(f"Day {day_num} not found in content_database.json")
    
    data = db["days"][day_str]
    template_name = data.get("template", "template_split_test.html")
    voice_name = data.get("voice", "en-IN-PrabhatNeural")
    bgm_filename = data.get("bgm", "bgm_indie_groove.mp3")

    print(f"\n=======================================================")
    print(f"🎬 PRODUCING DAY {day_num} INNOVATIVE 9:16 CINEMATIC REEL")
    print(f"Template: {template_name}")
    print(f"Neural Voice: {voice_name}")
    print(f"Soundtrack: {bgm_filename}")
    print(f"Topic: {data.get('badge')}")
    print(f"Track: {data.get('track_title')} by {data.get('track_artist')}")
    print(f"=======================================================\n")

    # 2. Prepare customized HTML from template
    template_path = os.path.join(motion_assets, template_name)
    if not os.path.exists(template_path):
        template_path = os.path.join(motion_assets, "reel_motion_graphic.html")
        print(f"⚠️ Specified template not found, falling back to: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Dynamic replacements
    badge = data.get("badge", "RELATABLE LDR FACTS")
    headline = data.get("headline", "Stop counting <em>3-2-1</em><br>on call.")
    sub = data.get("sub", "Late-night calls should not feel this distant.")
    city1 = data.get("city1", "Delhi 📍")
    city2 = data.get("city2", "Bangalore 📍")
    dist = data.get("distance_text", "1,740 KM")
    track_title = data.get("track_title", "Faasle")
    track_artist = data.get("track_artist", "Aditya Rikhari")
    quote = data.get("quote", "Because kilometers disappear when you listen at the exact same millisecond.")
    drift_ms = str(data.get("drift_ms", "1,840"))
    subtitle = data.get("subtitle", data.get("sub", "When you both listen to the exact same second, distance stops existing."))

    # Apply substitutions
    html = html.replace("{{BADGE}}", badge)
    html = html.replace("{{HEADLINE}}", headline)
    html = html.replace("{{SUB}}", sub)
    html = html.replace("{{CITY1}}", city1)
    html = html.replace("{{CITY2}}", city2)
    html = html.replace("{{DISTANCE}}", dist)
    html = html.replace("{{TRACK_TITLE}}", track_title)
    html = html.replace("{{TRACK_ARTIST}}", track_artist)
    html = html.replace("{{QUOTE}}", quote)
    html = html.replace("{{DRIFT_MS}}", drift_ms)
    html = html.replace("{{SUBTITLE}}", subtitle)

    # Legacy replacements if using older template
    html = html.replace("DELHI ↔ BANGALORE · 1,700 KM", badge)
    html = html.replace('Delhi to Bangalore.<br><em>1,700 km</em> apart.', headline)
    html = html.replace('Counting 3-2-1 on a WhatsApp call never syncs.', sub)
    html = html.replace('Delhi 📍', city1)
    html = html.replace('Bangalore 📍', city2)
    html = html.replace('1,740 KM', dist)
    html = html.replace('Pehle Bhi Main', track_title)
    html = html.replace('Vishal Mishra · Animal', track_artist)
    html = html.replace('"Because 1,700 kilometers disappear when you listen at the exact same second."', f'"{quote}"')

    custom_html_path = os.path.join(motion_assets, f"reel_day_{day_num}.html")
    with open(custom_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated customized motion template: {custom_html_path}")

    # 3. Generate Studio Neural Voiceover
    narration_text = data.get("narration")
    voice_mp3 = os.path.join(output_dir, f"narration_day_{day_num}.mp3")
    asyncio.run(synthesize_neural_voice(narration_text, voice_name, voice_mp3))

    # 4. Record motion graphics via Playwright Chromium (9:16 Vertical 1080x1920)
    target_webm = os.path.join(motion_renders, f"raw_day_{day_num}.webm")
    file_url = f"file:///{custom_html_path.replace(os.sep, '/')}"

    print("Launching Chromium 1080x1920 screen capture...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-gpu-sandbox',
                '--no-sandbox',
                '--enable-features=VaapiVideoDecoder',
                '--autoplay-policy=no-user-gesture-required'
            ]
        )
        context = browser.new_context(
            viewport={'width': 1080, 'height': 1920},
            device_scale_factor=1,
            record_video_dir=motion_renders,
            record_video_size={'width': 1080, 'height': 1920}
        )
        page = context.new_page()
        page.goto(file_url, wait_until='networkidle')
        print("Recording 24.5 seconds of high-fidelity 9:16 motion graphics...")
        page.wait_for_timeout(24500)
        temp_video = page.video.path()
        context.close()
        browser.close()

    # Move or rename recorded video
    if os.path.exists(target_webm):
        os.remove(target_webm)
    os.rename(temp_video, target_webm)
    print(f"✅ Motion capture completed: {target_webm} ({os.path.getsize(target_webm)} bytes)")

    # 5. FFmpeg Assembly with Meta Instagram Compliance
    bgm_path = os.path.join(motion_assets, bgm_filename)
    if not os.path.exists(bgm_path):
        bgm_path = os.path.join(motion_assets, "lofi_ambient.mp3")

    master_reel_output = os.path.join(output_dir, f"Day{day_num}_Master_Cinematic_Reel_IG.mp4")
    cloud_reel_output = os.path.join(reels_cloud_dir, f"Day{day_num}_Master_Cinematic_Reel_IG.mp4")

    print(f"Assembling final Instagram Reel with BGM [{bgm_filename}] & H.264 High Profile...")
    cmd = [
        ffmpeg_bin, "-y",
        "-i", target_webm,
        "-i", voice_mp3,
        "-i", bgm_path,
        "-filter_complex", (
            "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.35[voice];"
            "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.22,afade=t=out:st=22.5:d=1.5[music];"
            "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.1",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-t", "24.0",
        master_reel_output
    ]
    subprocess.run(cmd, check=True)

    # Copy to cloud_repo/reels
    import shutil
    shutil.copy2(master_reel_output, cloud_reel_output)

    print("\n=======================================================")
    print(f"🎉 DAY {day_num} REEL RENDERED & STAGED FOR CLOUD!")
    print(f"Local Master: {master_reel_output}")
    print(f"Cloud Master: {cloud_reel_output}")
    print(f"File Size: {os.path.getsize(cloud_reel_output)} bytes")
    print(f"Resolution: 1080x1920 (9:16 Vertical)")
    print(f"=======================================================\n")
    return cloud_reel_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, default=12, help="Day number to generate (1-30)")
    args = parser.parse_args()
    render_day_reel(args.day)
