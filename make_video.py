#!/usr/bin/env python3
"""
Create a relaxing/healing slideshow video for 奈良春日 鹿のや (KANOYA)
"""
import subprocess
import os

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUT = "/home/user/kanoya0625/kanoya_room.mp4"
IMG_DIR = "/home/user/kanoya0625/images"
W, H = 1920, 1080
DUR = 6  # seconds per image
FADE = 1  # crossfade duration

# Image order and telop config
# Each: (filename, main_text, sub_text, text_pos)
# text_pos: "top" | "bottom" | "center"
SLIDES = [
    ("7C1A4283.jpg",
     "奈良春日　鹿のや",
     "KANOYA",
     "center"),
    ("7C1A4155.jpg",
     "ゆったりと流れる、穏やかな時間",
     "日常の喧騒を忘れ、静寂に包まれる",
     "bottom"),
    ("7C1A4163.jpg",
     "緑薫る坪庭を、眺めながら",
     "自然とひとつになる、贅沢なひととき",
     "bottom"),
    ("7C1A4182.jpg",
     "柔らかな光に包まれて",
     "心も体も、そっとほどけていく",
     "bottom"),
    ("7C1A4204.jpg",
     "窓の外は、青々とした木々",
     "季節の移ろいを、部屋から感じる",
     "bottom"),
    ("7C1A4215.jpg",
     "大切な人と過ごす、特別な夜",
     "すべての疲れが、癒されていく",
     "bottom"),
    ("7C1A4217.jpg",
     "古都の静けさの中で",
     "深く、ゆっくりと眠れる場所",
     "bottom"),
    ("7C1A4284.jpg",
     "奈良春日　鹿のや",
     "あなたの「くつろぎ」が、ここにある",
     "center"),
]

def escape(text):
    return text.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")

def make_slide_filter(idx, img_path, main_text, sub_text, pos):
    """Build ffmpeg filter for one slide with Ken Burns zoom and text overlay."""
    # Scale and crop to 1920x1080, maintaining aspect
    scale_crop = f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"

    # Ken Burns: alternate between zoom-in and zoom-out
    if idx % 2 == 0:
        # slow zoom in
        zoom_expr = f"'1+0.03*on/{DUR*25}'"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    else:
        # slow zoom out
        zoom_expr = f"'1.05-0.03*on/{DUR*25}'"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    total_frames = DUR * 25
    zoompan = (f"zoompan=z={zoom_expr}:x={x_expr}:y={y_expr}"
               f":d={total_frames}:s={W}x{H}:fps=25")

    # Text positions
    if pos == "center":
        main_y = f"(h-text_h)/2-60"
        sub_y = f"(h-text_h)/2+60"
    else:  # bottom
        main_y = f"h-200"
        sub_y = f"h-140"

    fade_in = f"alpha='if(lt(t,0.8),t/0.8,1)'"
    fade_out_start = DUR - 0.8

    main_draw = (
        f"drawtext=fontfile={FONT}"
        f":text='{escape(main_text)}'"
        f":fontsize=64:fontcolor=white"
        f":shadowcolor=black@0.7:shadowx=3:shadowy=3"
        f":x=(w-text_w)/2:y={main_y}"
        f":alpha='if(lt(t,0.8),t/0.8,if(gt(t,{fade_out_start}),(t-{fade_out_start})/0.8*(-1)+1,1))'"
    )
    sub_draw = (
        f"drawtext=fontfile={FONT}"
        f":text='{escape(sub_text)}'"
        f":fontsize=36:fontcolor=white@0.9"
        f":shadowcolor=black@0.6:shadowx=2:shadowy=2"
        f":x=(w-text_w)/2:y={sub_y}"
        f":alpha='if(lt(t,1.2),0,if(lt(t,2.0),(t-1.2)/0.8,if(gt(t,{fade_out_start}),(t-{fade_out_start})/0.8*(-1)+1,1)))'"
    )

    full = f"{scale_crop},{zoompan},{main_draw},{sub_draw}[v{idx}]"
    return full

def build_video():
    inputs = []
    filter_parts = []

    for i, (fname, main, sub, pos) in enumerate(SLIDES):
        path = os.path.join(IMG_DIR, fname)
        inputs += ["-loop", "1", "-t", str(DUR + FADE), "-i", path]
        filter_parts.append(make_slide_filter(i, path, main, sub, pos))

    n = len(SLIDES)
    # Chain xfade transitions
    chain = "[v0]"
    for i in range(1, n):
        offset = i * DUR - FADE
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
           "-c:v", "libx264", "-crf", "18", "-preset", "slow",
           "-pix_fmt", "yuv420p",
           "-r", "25",
           OUT]
    )

    print("Running ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDERR:", result.stderr[-3000:])
    else:
        print(f"Done! Output: {OUT}")

if __name__ == "__main__":
    build_video()
