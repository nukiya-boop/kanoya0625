#!/usr/bin/env python3
"""
Instagram Reels: 1080x1920, 30s
- Blurred background fills frame, original image shown uncropped on top
- Top telop with slide-in animation
- Stylish xfade transitions
"""
import subprocess, os

FONT   = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUT    = "/home/user/kanoya0625/kanoya_insta.mp4"
IMG_DIR= "/home/user/kanoya0625/images"
W, H   = 1080, 1920
FPS    = 25
FADE   = 0.8
DUR    = (30 + 7 * FADE) / 8  # ≈ 4.45s → total 30s

SLIDES = [
    ("7C1A4283.jpg", "奈良春日　鹿のや",            "KANOYA",                  "wipeup"),
    ("7C1A4155.jpg", "ゆったりと流れる\n穏やかな時間", "日常の喧騒を忘れて",      "smoothleft"),
    ("7C1A4163.jpg", "緑薫る坪庭を\n眺めながら",     "自然とひとつになる贅沢",    "slideup"),
    ("7C1A4182.jpg", "柔らかな光に\n包まれて",       "心も体も、そっとほどけていく","wipeleft"),
    ("7C1A4204.jpg", "窓の外は\n青々とした木々",     "季節の移ろいを感じる",      "smoothup"),
    ("7C1A4215.jpg", "大切な人と過ごす\n特別な夜",   "すべての疲れが癒されていく", "slideleft"),
    ("7C1A4217.jpg", "古都の静けさの中で",           "深く、ゆっくりと眠れる場所", "wiperight"),
    ("7C1A4284.jpg", "あなたの\nくつろぎがここにある","奈良春日　鹿のや",          "fadeblack"),
]

def e(text):
    return (text.replace("\\", "\\\\")
                .replace("'", "'")
                .replace(":", "\\:")
                .replace(",", "\\,"))

def slide_filter(idx, main_text, sub_text):
    total_frames = int((DUR + FADE) * FPS)
    fade_out_start = DUR - FADE

    # --- Background: scale to fill → blur → darken ---
    bg = (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},setsar=1,"
          f"boxblur=luma_radius=28:luma_power=2,"
          f"colorchannelmixer=rr=0.55:gg=0.55:bb=0.55[bg{idx}]")

    # --- Foreground: scale to fit (no crop) ---
    fg = (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"setsar=1[fg{idx}]")

    # --- Overlay fg centered on bg ---
    comp = f"[bg{idx}][fg{idx}]overlay=(W-w)/2:(H-h)/2[comp{idx}]"

    # --- Ken Burns on composed frame ---
    z = f"'1+0.018*on/{total_frames}'" if idx % 2 == 0 else f"'1.04-0.018*on/{total_frames}'"
    zoompan = (f"[comp{idx}]zoompan=z={z}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               f":d={total_frames}:s={W}x{H}:fps={FPS}[zp{idx}]")

    # --- Text animations ---
    a_main = (f"'if(lt(t,0.7),t/0.7,"
              f"if(gt(t,{fade_out_start:.3f}),(t-{fade_out_start:.3f})/{FADE:.2f}*(-1)+1,1))'")
    a_sub  = (f"'if(lt(t,1.1),0,if(lt(t,1.7),(t-1.1)/0.6,"
              f"if(gt(t,{fade_out_start:.3f}),(t-{fade_out_start:.3f})/{FADE:.2f}*(-1)+1,1)))'")

    MAIN_TOP   = int(H * 0.07)
    SUB_TOP    = int(H * 0.22)
    SLIDE_DIST = 40
    LINE_Y     = int(H * 0.205)

    lines = main_text.split("\n")
    line_h = 88
    draws = []

    for li, line in enumerate(lines):
        final_y = MAIN_TOP + li * line_h
        y_expr  = f"'if(lt(t,0.7),{final_y}+{SLIDE_DIST}*(1-t/0.7),{final_y})'"
        draws.append(
            f"drawtext=fontfile={FONT}:text='{e(line)}'"
            f":fontsize=72:fontcolor=white"
            f":shadowcolor=black@0.8:shadowx=3:shadowy=3"
            f":x=(w-text_w)/2:y={y_expr}:alpha={a_main}"
        )

    draws.append(
        f"drawbox=x=(w-320)/2:y={LINE_Y}:w=320:h=2:color=white@0.6:t=fill"
        f":enable='if(lt(t,1.1),0,1)'"
    )

    sub_y_expr = (f"'if(lt(t,1.1),{SUB_TOP+SLIDE_DIST},"
                  f"if(lt(t,1.7),{SUB_TOP+SLIDE_DIST}-(t-1.1)/0.6*{SLIDE_DIST},{SUB_TOP}))'")
    draws.append(
        f"drawtext=fontfile={FONT}:text='{e(sub_text)}'"
        f":fontsize=40:fontcolor=white@0.92"
        f":shadowcolor=black@0.7:shadowx=2:shadowy=2"
        f":x=(w-text_w)/2:y={sub_y_expr}:alpha={a_sub}"
    )

    text_filter = f"[zp{idx}]" + ",".join(draws) + f"[v{idx}]"

    return [bg, fg, comp, zoompan, text_filter]

def build():
    inputs, filters = [], []
    n = len(SLIDES)

    for i, (fname, main, sub, _) in enumerate(SLIDES):
        inputs += ["-loop", "1", "-t", str(DUR + FADE), "-i",
                   os.path.join(IMG_DIR, fname)]
        filters.extend(slide_filter(i, main, sub))

    chain = "[v0]"
    for i in range(1, n):
        offset     = round(i * (DUR - FADE), 4)
        transition = SLIDES[i][3]
        label      = f"[xf{i}]" if i < n - 1 else "[vout]"
        filters.append(
            f"{chain}[v{i}]xfade=transition={transition}"
            f":duration={FADE}:offset={offset}{label}"
        )
        chain = f"[xf{i}]"

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + ["-filter_complex", ";".join(filters),
           "-map", "[vout]",
           "-c:v", "libx264", "-crf", "20", "-preset", "fast",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", "30",
           OUT]
    )

    print("Rendering…")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-5000:])
    else:
        mb = os.path.getsize(OUT) / 1024 / 1024
        print(f"Done → {OUT}  ({mb:.1f} MB)")

if __name__ == "__main__":
    build()
