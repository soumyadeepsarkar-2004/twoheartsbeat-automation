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
    """Generates studio-grade expressive Indian voiceover with calibrated speed and pitch."""
    print(f"🎙️ Generating Calibrated Neural Voiceover [{voice_name}]...")
    # Calibrated -1Hz pitch for grounded warmth, +3% rate for engaging delivery
    communicate = edge_tts.Communicate(text, voice_name, rate="+3%", pitch="-1Hz")
    await communicate.save(output_mp3)
    print(f"  ✓ Studio Voiceover saved: {output_mp3} ({os.path.getsize(output_mp3)} bytes)")

def render_day_reel(day_num):
    day_str = str(day_num)
    if day_str not in db["days"]:
        raise ValueError(f"Day {day_num} not found in content_database.json")
    
    data = db["days"][day_str]
    template_name = data.get("template", "template_character_skit.html")
    voice_name = data.get("voice", "hi-IN-MadhurNeural")
    bgm_filename = data.get("bgm", "bgm_rainy_midnight.mp3")

    print(f"\n=======================================================")
    print(f"🎬 PRODUCING DAY {day_num} INNOVATIVE CHARACTER REEL")
    print(f"Template: {template_name}")
    print(f"Neural Voice: {voice_name}")
    print(f"Soundtrack: {bgm_filename}")
    print(f"Topic: {data.get('badge')}")
    print(f"Track: {data.get('track_title')} by {data.get('track_artist')}")
    print(f"=======================================================\n")

    # 2. Prepare customized HTML from template
    template_path = os.path.join(motion_assets, template_name)
    if not os.path.exists(template_path):
        template_path = os.path.join(motion_assets, "template_character_skit.html")
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
    dist = data.get("distance_text", "2,150 KM")
    track_title = data.get("track_title", "Alag Aasmaan")
    track_artist = data.get("track_artist", "Anuv Jain")
    quote = data.get("quote", "Because kilometers disappear when you listen at the exact same millisecond.")
    drift_ms = str(data.get("drift_ms", "1,840"))
    subtitle = data.get("subtitle", data.get("sub", "When you both listen to the exact same second, distance stops existing."))

    # Character dialogue & image cutouts
    dialogue1 = data.get("dialogue1", "Wait, what chorus are you on?! My Spotify Jam just desynced by 4 seconds again 😭")
    dialogue2 = data.get("dialogue2", "Stop counting 3-2-1! Join my room on Two Hearts Beat — exact same beat! 🎧✨")
    sync_status = data.get("sync_status", "0.00 MS SYNC LOCKED")

    char1_name = data.get("char1", "soumya_frustrated.png")
    char2_name = data.get("char2", "maya_vibing.png")
    char1_path = os.path.join(motion_assets, "characters", char1_name)
    char2_path = os.path.join(motion_assets, "characters", char2_name)
    char1_url = f"file:///{char1_path.replace(os.sep, '/')}"
    char2_url = f"file:///{char2_path.replace(os.sep, '/')}"

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
    html = html.replace("{{DIALOGUE1}}", dialogue1)
    html = html.replace("{{DIALOGUE2}}", dialogue2)
    html = html.replace("{{SYNC_STATUS}}", sync_status)
    html = html.replace("{{CHAR_IMG_1}}", char1_url)
    html = html.replace("{{CHAR_IMG_2}}", char2_url)

    # Explainer template replacements
    explainer_speech = data.get("explainer_speech", "Commercial apps charge monthly fees and still drift by seconds. So I coded Two Hearts Beat — exact same millisecond sync on both phones. 100% free, zero installs.")
    char_main_name = data.get("char_main", "soumya_explaining.png")
    char_main_path = os.path.join(motion_assets, "characters", char_main_name)
    char_main_url = f"file:///{char_main_path.replace(os.sep, '/')}"

    html = html.replace("{{EXPLAINER_SPEECH}}", explainer_speech)
    html = html.replace("{{CHAR_IMG_MAIN}}", char_main_url)

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

    sfx_dir = os.path.join(motion_assets, "sfx")
    ping_wav = os.path.join(sfx_dir, "ping.wav")
    scratch_wav = os.path.join(sfx_dir, "scratch.wav")
    sync_lock_wav = os.path.join(sfx_dir, "sync_lock.wav")
    has_sfx = os.path.exists(ping_wav) and os.path.exists(scratch_wav) and os.path.exists(sync_lock_wav)

    master_reel_output = os.path.join(output_dir, f"Day{day_num}_Master_Cinematic_Reel_IG.mp4")
    cloud_reel_output = os.path.join(reels_cloud_dir, f"Day{day_num}_Master_Cinematic_Reel_IG.mp4")

    print(f"Assembling final Instagram Reel with Calibrated Audio & SFX...")

    if has_sfx:
        filter_str = (
            "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.35[voice];"
            "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.20,afade=t=out:st=22.5:d=1.5[music];"
            "[3:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=500|500,volume=0.6[sfx_ping];"
            "[4:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=2500|2500,volume=0.45[sfx_scratch];"
            "[5:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=6000|6000,volume=0.85[sfx_lock];"
            "[voice][music][sfx_ping][sfx_scratch][sfx_lock]amix=inputs=5:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            ffmpeg_bin, "-y",
            "-i", target_webm,
            "-i", voice_mp3,
            "-i", bgm_path,
            "-i", ping_wav,
            "-i", scratch_wav,
            "-i", sync_lock_wav,
            "-filter_complex", filter_str,
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
    else:
        filter_str = (
            "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.35[voice];"
            "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.22,afade=t=out:st=22.5:d=1.5[music];"
            "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            ffmpeg_bin, "-y",
            "-i", target_webm,
            "-i", voice_mp3,
            "-i", bgm_path,
            "-filter_complex", filter_str,
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
    print(f"🎉 DAY {day_num} CHARACTER REEL RENDERED & STAGED FOR CLOUD!")
    print(f"Local Master: {master_reel_output}")
    print(f"Cloud Master: {cloud_reel_output}")
    print(f"File Size: {os.path.getsize(cloud_reel_output)} bytes")
    print(f"Resolution: 1080x1920 (9:16 Vertical)")
    print(f"=======================================================\n")
    return cloud_reel_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, default=19, help="Day number to generate (1-35)")
    args = parser.parse_args()
    render_day_reel(args.day)
