#!/usr/bin/env python3
"""
Instagram Reels format: 1080x1920, 30 seconds
"""
import subprocess
import os

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUT = "/home/user/kanoya0625/kanoya_insta.mp4"
IMG_DIR = "/home/user/kanoya0625/images"
W, H = 1080, 1920
FPS = 25
FADE = 0.5

# 8 slides × DUR - 7 × FADE = 30s → DUR = (30 + 7*0.5) / 8 = 4.1875
DUR = 4.1875

SLIDES = [
    ("7C1A4283.jpg", "奈良春日　鹿のや", "KANOYA", "center"),
    ("7C1A4155.jpg", "ゆったりと流れる\n穏やかな時間", "日常の喧騒を忘れて", "bottom"),
    ("7C1A4163.jpg", "緑薫る坪庭を\n眺めながら", "自然とひとつになる贅沢", "bottom"),
    ("7C1A4182.jpg", "柔らかな光に\n包まれて", "心も体も、そっとほどけていく", "bottom"),
    ("7C1A4204.jpg", "窓の外は\n青々とした木々", "季節の移ろいを感じる", "bottom"),
    ("7C1A4215.jpg", "大切な人と過ごす\n特別な夜", "すべての疲れが癒されていく", "bottom"),
    ("7C1A4217.jpg", "古都の静けさの中で", "深く、ゆっくりと眠れる場所", "bottom"),
    ("7C1A4284.jpg", "あなたの\nくつろぎがここにある", "奈良春日　鹿のや", "center"),
]

def escape(text):
    return (text.replace("\\", "\\\\")
                .replace("'", "’")
                .replace(":", "\\:")
                .replace(",", "\\,")
                .replace("\n", "\n"))

def make_slide_filter(idx, main_text, sub_text, pos):
    total_frames = int(DUR * FPS) + int(FADE * FPS)

    # Scale to fill 1080x1920, crop center
    scale_crop = (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H},setsar=1")

    # Ken Burns
    if idx % 2 == 0:
        zoom_expr = f"'1+0.025*on/{total_frames}'"
    else:
        zoom_expr = f"'1.05-0.025*on/{total_frames}'"
    zoompan = (f"zoompan=z={zoom_expr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               f":d={total_frames}:s={W}x{H}:fps={FPS}")

    fade_out_start = DUR - FADE

    # Text position
    if pos == "center":
        main_y = "(h-text_h)/2-80"
        sub_y = "(h-text_h)/2+80"
    else:
        main_y = "h*0.72"
        sub_y = "h*0.86"

    alpha_main = (f"'if(lt(t,0.6),t/0.6,"
                  f"if(gt(t,{fade_out_start:.3f}),(t-{fade_out_start:.3f})/{FADE}*(-1)+1,1))'")
    alpha_sub = (f"'if(lt(t,1.0),0,if(lt(t,1.6),(t-1.0)/0.6,"
                 f"if(gt(t,{fade_out_start:.3f}),(t-{fade_out_start:.3f})/{FADE}*(-1)+1,1)))'")

    # Split main_text lines for drawtext (handle \n)
    lines = main_text.split("\n")
    line_h = 80  # approx line height for fontsize=68
    draws = []
    for li, line in enumerate(lines):
        offset = (li - (len(lines)-1)/2) * line_h
        y_expr = f"({main_y})+{offset:.0f}"
        draws.append(
            f"drawtext=fontfile={FONT}:text='{escape(line)}'"
            f":fontsize=68:fontcolor=white"
            f":shadowcolor=black@0.8:shadowx=3:shadowy=3"
            f":x=(w-text_w)/2:y={y_expr}:alpha={alpha_main}"
        )

    draws.append(
        f"drawtext=fontfile={FONT}:text='{escape(sub_text)}'"
        f":fontsize=38:fontcolor=white@0.9"
        f":shadowcolor=black@0.7:shadowx=2:shadowy=2"
        f":x=(w-text_w)/2:y={sub_y}:alpha={alpha_sub}"
    )

    full = f"{scale_crop},{zoompan}," + ",".join(draws) + f"[v{idx}]"
    return full

def build_video():
    inputs = []
    filter_parts = []
    n = len(SLIDES)

    for i, (fname, main, sub, pos) in enumerate(SLIDES):
        path = os.path.join(IMG_DIR, fname)
        inputs += ["-loop", "1", "-t", str(DUR + FADE), "-i", path]
        filter_parts.append(make_slide_filter(i, main, sub, pos))

    # Chain xfade
    chain = "[v0]"
    for i in range(1, n):
        offset = round(i * DUR - FADE * (i - 1) - FADE, 4)
        # Actually: offset = i * DUR - i * FADE = i*(DUR-FADE)
        offset = round(i * (DUR - FADE), 4)
        next_label = f"[xf{i}]" if i < n - 1 else "[vout]"
        filter_parts.append(
            f"{chain}[v{i}]xfade=transition=fade:duration={FADE}:offset={offset}{next_label}"
        )
        chain = f"[xf{i}]"

    filter_complex = ";".join(filter_parts)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + ["-filter_complex", filter_complex,
           "-map", "[vout]",
           "-c:v", "libx264", "-crf", "22", "-preset", "fast",
           "-pix_fmt", "yuv420p",
           "-r", str(FPS),
           "-t", "30",
           OUT]
    )

    print("Running ffmpeg (Instagram 1080x1920, 30s)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDERR:", result.stderr[-4000:])
    else:
        size_mb = os.path.getsize(OUT) / 1024 / 1024
        print(f"Done! Output: {OUT} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    build_video()
