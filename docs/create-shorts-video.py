#!/usr/bin/env python3
"""DockProbe YouTube Shorts Video Generator

Generates a 60-second promotional video (1080x1920, 30fps) for YouTube Shorts.
Uses Pillow for frame generation and ffmpeg for MP4 encoding.

Scenes:
  1. Hook (0-5s)       — Quick cuts: terminal → dashboard → telegram
  2. Install (5-12s)   — Terminal typing animation
  3. Dashboard (12-20s) — Dashboard hero + Ken Burns zoom
  4. Containers (20-28s) — Container table + panning
  5. Charts (28-36s)    — Chart section + zoom
  6. Anomaly (36-44s)   — Red pulse + telegram alert
  7. Tech Stack (44-50s) — Text items sequential reveal
  8. Why Different (50-57s) — Comparison layout
  9. CTA (57-60s)       — Logo + GitHub + Star

Usage:
  sudo apt-get install -y ffmpeg
  python3 docs/create-shorts-video.py
"""

import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ─── Constants ───────────────────────────────────────────────────────────────

W, H = 1080, 1920
FPS = 30
DURATION = 60
TOTAL_FRAMES = FPS * DURATION  # 1800
FADE_FRAMES = 15  # 0.5s crossfade between scenes

# Brand colors
BG = (13, 17, 23)
ACCENT = (55, 210, 8)
WHITE = (255, 255, 255)
RED = (255, 59, 48)
GRAY = (139, 148, 158)
DARK_BAR = (13, 17, 23, 220)
TELEGRAM_BLUE = (0, 136, 204)

# Paths
SCRIPT_DIR = Path(__file__).parent
SCREENSHOTS = SCRIPT_DIR / "screenshots"
OUTPUT = SCRIPT_DIR / "dockprobe-shorts.mp4"

# Font paths
FONT_BOLD = "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
FONT_HEAVY = "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def new_frame():
    return Image.new("RGB", (W, H), BG)


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def draw_progress_bar(img, progress):
    draw = ImageDraw.Draw(img)
    bar_w = int(W * max(0, min(1, progress)))
    if bar_w > 0:
        draw.rectangle([0, H - 4, bar_w, H], fill=ACCENT)


def draw_centered(draw, text, y, font, color=WHITE):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, fill=color, font=font)


def fit_to_width(img, target_w=None):
    if target_w is None:
        target_w = W
    ratio = target_w / img.width
    new_h = int(img.height * ratio)
    return img.resize((target_w, new_h), Image.LANCZOS)


def ken_burns(img, t, start_scale=1.0, end_scale=1.3,
              start_center=(0.5, 0.5), end_center=(0.5, 0.5)):
    """Zoom/pan by interpolating a crop rectangle over the source image."""
    t = ease_in_out(t)
    scale = lerp(start_scale, end_scale, t)
    cx = lerp(start_center[0], end_center[0], t)
    cy = lerp(start_center[1], end_center[1], t)

    crop_w = img.width / scale
    crop_h = img.height / scale
    left = cx * img.width - crop_w / 2
    top = cy * img.height - crop_h / 2

    # Clamp to image bounds
    left = max(0, min(left, img.width - crop_w))
    top = max(0, min(top, img.height - crop_h))

    box = (int(left), int(top), int(left + crop_w), int(top + crop_h))
    return img.crop(box)


def crossfade(img_a, img_b, t):
    return Image.blend(img_a, img_b, max(0.0, min(1.0, t)))


def draw_dark_bar(draw, y, h):
    draw.rectangle([0, y, W, y + h], fill=DARK_BAR)


def draw_terminal_chrome(draw, x, y, w, h):
    """Draw a macOS-style terminal window frame."""
    # Body
    draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=(22, 27, 34))
    # Header
    draw.rounded_rectangle([x, y, x + w, y + 45], radius=12, fill=(30, 34, 42))
    draw.rectangle([x, y + 30, x + w, y + 45], fill=(30, 34, 42))
    # Traffic light dots
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = x + 20 + i * 25
        draw.ellipse([cx, y + 13, cx + 14, y + 27], fill=c)
    # Title
    font_sm = load_font(FONT_REGULAR, 14)
    draw.text((x + w // 2 - 25, y + 14), "Terminal", fill=GRAY, font=font_sm)


# ─── Scene Generators ────────────────────────────────────────────────────────

class VideoGenerator:
    def __init__(self):
        self.screenshots = {}
        for name in ("dashboard-hero", "container-table", "charts", "dashboard-full"):
            path = SCREENSHOTS / f"{name}.png"
            if path.exists():
                self.screenshots[name] = Image.open(path).convert("RGB")

        # Scene definitions: (start_frame, end_frame, method)
        self.scenes = [
            (0, 150, self.scene_hook),
            (150, 360, self.scene_install),
            (360, 600, self.scene_dashboard),
            (600, 840, self.scene_containers),
            (840, 1080, self.scene_charts),
            (1080, 1320, self.scene_anomaly),
            (1320, 1500, self.scene_tech_stack),
            (1500, 1710, self.scene_why_different),
            (1710, 1800, self.scene_cta),
        ]

    def generate_frames(self):
        """Yield (frame_number, PIL.Image) for all 1800 frames."""
        prev_last_frame = None

        for scene_idx, (start, end, scene_fn) in enumerate(self.scenes):
            length = end - start
            scene_cache = {}

            # Generate all frames for this scene
            for f in range(start, end):
                t = (f - start) / max(1, length - 1)
                frame = scene_fn(f, t, length)
                draw_progress_bar(frame, f / TOTAL_FRAMES)
                scene_cache[f] = frame

            # Apply crossfade from previous scene
            if prev_last_frame is not None:
                for f in range(start, min(start + FADE_FRAMES, end)):
                    fade_t = (f - start) / FADE_FRAMES
                    scene_cache[f] = crossfade(prev_last_frame, scene_cache[f], fade_t)
                    draw_progress_bar(scene_cache[f], f / TOTAL_FRAMES)

            # Yield frames
            for f in range(start, end):
                yield f, scene_cache[f]

            prev_last_frame = scene_cache[end - 1].copy()

    # ── Scene 1: Hook (0-5s, 150 frames) ─────────────────────────────────

    def scene_hook(self, frame_num, t, length):
        # 3 sub-scenes of 50 frames each
        sub = frame_num // 50
        sub_t = (frame_num % 50) / 49

        if sub == 0:
            return self._hook_terminal(sub_t)
        elif sub == 1:
            return self._hook_dashboard(sub_t)
        else:
            return self._hook_telegram(sub_t)

    def _hook_terminal(self, t):
        frame = new_frame()
        draw = ImageDraw.Draw(frame, "RGBA")

        # Title
        font_title = load_font(FONT_HEAVY, 56)
        draw_centered(draw, "Docker Monitoring", 250, font_title, ACCENT)
        font_sub = load_font(FONT_REGULAR, 34)
        draw_centered(draw, "Made Simple", 320, font_sub, WHITE)

        # Terminal
        tx, ty, tw, th = 50, 450, W - 100, 700
        draw_terminal_chrome(draw, tx, ty, tw, th)

        lines = [
            ("$ ", "docker ps", ACCENT),
            ("", "CONTAINER   STATUS    CPU    MEM", GRAY),
            ("", "nginx       Up        2.1%   128MB", WHITE),
            ("", "postgres    Up        5.3%   256MB", WHITE),
            ("", "redis       Up        0.8%   64MB", WHITE),
            ("", "", WHITE),
            ("$ ", "dockprobe monitor --all", ACCENT),
            ("", "Monitoring 3 containers...", ACCENT),
        ]

        total_chars = sum(len(p + c) for p, c, _ in lines)
        chars_shown = int(t * total_chars * 1.1)

        font_mono = load_font(FONT_MONO, 24)
        consumed = 0
        cy = ty + 65
        for prompt, content, color in lines:
            full = prompt + content
            if not full:
                cy += 30
                continue
            vis = max(0, min(len(full), chars_shown - consumed))
            if vis > 0:
                # Draw prompt in gray, content in color
                x = tx + 25
                p_vis = min(len(prompt), vis)
                if p_vis > 0:
                    draw.text((x, cy), prompt[:p_vis], fill=GRAY, font=font_mono)
                x += int(draw.textlength(prompt, font=font_mono))
                c_vis = vis - p_vis
                if c_vis > 0:
                    draw.text((x, cy), content[:c_vis], fill=color, font=font_mono)
            consumed += len(full)
            cy += 36

        # Blinking cursor
        if int(t * 30) % 2 == 0 and t < 0.95:
            draw.rectangle([tx + 25, cy, tx + 37, cy + 24], fill=ACCENT)

        return frame

    def _hook_dashboard(self, t):
        frame = new_frame()
        if "dashboard-hero" in self.screenshots:
            img = self.screenshots["dashboard-hero"]
            cropped = ken_burns(img, t, 1.0, 1.15, (0.5, 0.5), (0.5, 0.4))
            fitted = fit_to_width(cropped, W)
            y = (H - fitted.height) // 2
            frame.paste(fitted, (0, max(0, y)))

        draw = ImageDraw.Draw(frame, "RGBA")
        draw_dark_bar(draw, H - 260, 110)
        font = load_font(FONT_BOLD, 44)
        draw_centered(draw, "Real-time Dashboard", H - 240, font, WHITE)

        return frame

    def _hook_telegram(self, t):
        frame = new_frame()
        draw = ImageDraw.Draw(frame, "RGBA")

        font_title = load_font(FONT_HEAVY, 48)
        draw_centered(draw, "Instant Alerts", 300, font_title, WHITE)

        # Notification card — slide in from right
        slide = int((1.0 - ease_in_out(min(t * 2, 1.0))) * 300)
        cx = 80 + slide
        cy = 550
        cw = W - 160
        ch = 420

        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=20,
                               fill=(30, 34, 42, 240))

        # Telegram icon
        draw.rounded_rectangle([cx + 20, cy + 20, cx + 70, cy + 70],
                               radius=10, fill=(*TELEGRAM_BLUE, 255))
        fi = load_font(FONT_BOLD, 28)
        draw.text((cx + 34, cy + 27), "T", fill=WHITE, font=fi)

        fn = load_font(FONT_BOLD, 26)
        fb = load_font(FONT_REGULAR, 22)
        draw.text((cx + 90, cy + 25), "DockProbe Alert", fill=WHITE, font=fn)
        draw.text((cx + 90, cy + 60), "just now", fill=GRAY, font=fb)

        alert_lines = [
            "Container 'nginx' CPU spike",
            "   CPU: 2.1%  ->  89.3%",
            "   Memory: 128MB  ->  412MB",
            "",
            "   Action required",
        ]
        ay = cy + 120
        reveal = ease_in_out(min(t * 1.5, 1.0))
        for line in alert_lines:
            if not line:
                ay += 15
                continue
            vis = int(len(line) * reveal)
            draw.text((cx + 40, ay), line[:vis], fill=WHITE, font=fb)
            ay += 38

        # Pulse border
        if t > 0.5:
            pulse_t = (t - 0.5) * 2
            pa = int(100 * (1 - pulse_t))
            if pa > 0:
                draw.rounded_rectangle(
                    [cx - 4, cy - 4, cx + cw + 4, cy + ch + 4],
                    radius=22, outline=(*RED, pa), width=3)

        return frame

    # ── Scene 2: Install (5-12s, 210 frames) ─────────────────────────────

    def scene_install(self, frame_num, t, length):
        frame = new_frame()
        draw = ImageDraw.Draw(frame, "RGBA")

        # Title
        ft = load_font(FONT_HEAVY, 48)
        draw_centered(draw, "Get Started in Seconds", 180, ft, WHITE)
        fs = load_font(FONT_REGULAR, 28)
        draw_centered(draw, "One command. That's it.", 250, fs, GRAY)

        # Terminal
        tx, ty, tw, th = 40, 370, W - 80, 1050
        draw_terminal_chrome(draw, tx, ty, tw, th)

        commands = [
            ("$ ", "git clone https://github.com/"),
            ("  ", "  your-user/dockprobe.git"),
            None,
            ("$ ", "cd dockprobe"),
            None,
            ("$ ", "docker-compose up -d"),
            None,
            ("  ", "Creating network...       done"),
            ("  ", "Building dockprobe...     done"),
            ("  ", "Starting dockprobe_1...   done"),
            None,
            ("  ", "DockProbe is running at"),
            ("  ", "http://localhost:9090"),
        ]

        total_chars = sum(len(item[0] + item[1]) for item in commands if item is not None)
        chars_shown = int(ease_in_out(min(t * 1.15, 1.0)) * total_chars)

        fm = load_font(FONT_MONO, 22)
        fmb = load_font(FONT_MONO_BOLD, 22)
        consumed = 0
        cy = ty + 65

        for item in commands:
            if item is None:
                cy += 28
                continue
            prompt, content = item
            full_len = len(prompt) + len(content)
            vis = max(0, min(full_len, chars_shown - consumed))
            if vis > 0:
                x = tx + 25
                p_vis = min(len(prompt), vis)
                if p_vis > 0:
                    draw.text((x, cy), prompt[:p_vis], fill=GRAY, font=fm)
                x += int(draw.textlength(prompt, font=fm))
                c_vis = vis - p_vis
                if c_vis > 0:
                    # Color: $ lines in green, checkmarks in green, URLs in accent
                    if prompt.startswith("$"):
                        color = ACCENT
                        f_use = fmb
                    elif "done" in content:
                        color = ACCENT
                        f_use = fm
                    elif "http" in content:
                        color = ACCENT
                        f_use = fmb
                    elif "running" in content.lower():
                        color = ACCENT
                        f_use = fmb
                    else:
                        color = WHITE
                        f_use = fm
                    draw.text((x, cy), content[:c_vis], fill=color, font=f_use)
            consumed += full_len
            cy += 34

        # Blinking cursor
        if int(frame_num / 15) % 2 == 0 and t < 0.9:
            draw.rectangle([tx + 25, cy + 2, tx + 37, cy + 24], fill=ACCENT)

        return frame

    # ── Scene 3: Dashboard (12-20s, 240 frames) ──────────────────────────

    def scene_dashboard(self, frame_num, t, length):
        frame = new_frame()

        if "dashboard-hero" in self.screenshots:
            img = self.screenshots["dashboard-hero"]
            cropped = ken_burns(img, t, 1.0, 1.25, (0.5, 0.35), (0.5, 0.55))
            fitted = fit_to_width(cropped, W)
            y = (H - fitted.height) // 2 - 50
            frame.paste(fitted, (0, max(0, y)))

        draw = ImageDraw.Draw(frame, "RGBA")

        # Top bar
        draw_dark_bar(draw, 0, 130)
        ft = load_font(FONT_BOLD, 42)
        draw_centered(draw, "Real-time Dashboard", 40, ft, WHITE)

        # Bottom caption
        draw_dark_bar(draw, H - 220, 110)
        fc = load_font(FONT_REGULAR, 28)
        draw_centered(draw, "CPU, Memory, Network — at a glance", H - 200, fc, GRAY)

        return frame

    # ── Scene 4: Containers (20-28s, 240 frames) ─────────────────────────

    def scene_containers(self, frame_num, t, length):
        frame = new_frame()

        if "container-table" in self.screenshots:
            img = self.screenshots["container-table"]
            cropped = ken_burns(img, t, 1.05, 1.2, (0.5, 0.3), (0.5, 0.7))
            fitted = fit_to_width(cropped, W - 40)
            x = (W - fitted.width) // 2
            y = (H - fitted.height) // 2
            frame.paste(fitted, (x, max(0, y)))

        draw = ImageDraw.Draw(frame, "RGBA")
        draw_dark_bar(draw, 0, 130)
        ft = load_font(FONT_BOLD, 42)
        draw_centered(draw, "Container Status", 40, ft, WHITE)

        draw_dark_bar(draw, H - 220, 110)
        fc = load_font(FONT_REGULAR, 28)
        draw_centered(draw, "Every container, every metric", H - 200, fc, GRAY)

        return frame

    # ── Scene 5: Charts (28-36s, 240 frames) ─────────────────────────────

    def scene_charts(self, frame_num, t, length):
        frame = new_frame()

        if "charts" in self.screenshots:
            img = self.screenshots["charts"]
            cropped = ken_burns(img, t, 1.0, 1.3, (0.3, 0.5), (0.7, 0.5))
            fitted = fit_to_width(cropped, W - 40)
            x = (W - fitted.width) // 2
            y = (H - fitted.height) // 2
            frame.paste(fitted, (x, max(0, y)))

        draw = ImageDraw.Draw(frame, "RGBA")
        draw_dark_bar(draw, 0, 130)
        ft = load_font(FONT_BOLD, 42)
        draw_centered(draw, "Live Charts", 40, ft, WHITE)

        draw_dark_bar(draw, H - 220, 110)
        fc = load_font(FONT_REGULAR, 28)
        draw_centered(draw, "Historical trends & real-time data", H - 200, fc, GRAY)

        return frame

    # ── Scene 6: Anomaly Detection (36-44s, 240 frames) ──────────────────

    def scene_anomaly(self, frame_num, t, length):
        frame = new_frame()

        if "dashboard-hero" in self.screenshots:
            img = self.screenshots["dashboard-hero"]
            fitted = fit_to_width(img, W)
            y = (H - fitted.height) // 2 - 50
            frame.paste(fitted, (0, max(0, y)))

        draw = ImageDraw.Draw(frame, "RGBA")

        # Red pulse overlay
        pulse = math.sin(t * math.pi * 4) * 0.5 + 0.5
        red_a = int(50 * pulse)
        draw.rectangle([0, 0, W, H], fill=(255, 0, 0, red_a))

        # Alert banner
        by = 280
        draw.rectangle([0, by, W, by + 80], fill=(*RED, 220))
        fa = load_font(FONT_BOLD, 36)
        draw_centered(draw, "ANOMALY DETECTED", by + 18, fa, WHITE)

        # Telegram notification card
        if t > 0.25:
            nt = ease_in_out(min((t - 0.25) / 0.3, 1.0))
            slide_y = int((1 - nt) * 100)
            nx, ny = 80, 1150 + slide_y
            nw, nh = W - 160, 300

            draw.rounded_rectangle([nx, ny, nx + nw, ny + nh],
                                   radius=16, fill=(30, 34, 42, 240))

            # Telegram icon
            draw.rounded_rectangle([nx + 15, ny + 15, nx + 55, ny + 55],
                                   radius=8, fill=(*TELEGRAM_BLUE, 255))
            fi = load_font(FONT_BOLD, 20)
            draw.text((nx + 27, ny + 21), "T", fill=WHITE, font=fi)

            fn = load_font(FONT_BOLD, 22)
            fb = load_font(FONT_REGULAR, 20)
            draw.text((nx + 70, ny + 18), "DockProbe Alert", fill=WHITE, font=fn)

            alert_lines = [
                "nginx: CPU 89% (threshold: 80%)",
                "Memory spike: 128MB -> 412MB",
                "Auto-restart triggered",
            ]
            ay = ny + 70
            line_reveal = ease_in_out(min((t - 0.25) / 0.5, 1.0))
            for line in alert_lines:
                vis = int(len(line) * line_reveal)
                draw.text((nx + 30, ay), line[:vis], fill=WHITE, font=fb)
                ay += 36

        # Top bar
        draw_dark_bar(draw, 0, 130)
        ft = load_font(FONT_BOLD, 42)
        draw_centered(draw, "Smart Alerts", 40, ft, WHITE)

        return frame

    # ── Scene 7: Tech Stack (44-50s, 180 frames) ─────────────────────────

    def scene_tech_stack(self, frame_num, t, length):
        frame = new_frame()
        draw = ImageDraw.Draw(frame, "RGBA")

        ft = load_font(FONT_HEAVY, 50)
        draw_centered(draw, "Built With", 230, ft, WHITE)
        draw.rectangle([W // 2 - 80, 300, W // 2 + 80, 304], fill=ACCENT)

        items = [
            ("Python + FastAPI", "Lightning-fast API server"),
            ("Docker SDK", "Native container integration"),
            ("Chart.js", "Beautiful real-time charts"),
            ("Telegram Bot", "Instant mobile alerts"),
            ("Single HTML", "Zero build step, zero deps"),
            ("WebSocket", "Live updates, no polling"),
        ]

        fn = load_font(FONT_BOLD, 32)
        fd = load_font(FONT_REGULAR, 22)

        y_start = 400
        for i, (name, desc) in enumerate(items):
            item_t = max(0.0, min(1.0, (t * len(items) * 1.3) - i))
            if item_t <= 0:
                continue

            alpha = int(255 * ease_in_out(item_t))
            slide = int((1 - ease_in_out(item_t)) * 30)
            y = y_start + i * 160 + slide

            # Card
            draw.rounded_rectangle([70, y, W - 70, y + 130],
                                   radius=12, fill=(30, 34, 42, alpha))
            # Accent bar
            draw.rectangle([70, y, 78, y + 130], fill=(*ACCENT, alpha))

            draw.text((110, y + 20), name, fill=(*WHITE, alpha), font=fn)
            draw.text((110, y + 65), desc, fill=(*GRAY, alpha), font=fd)

        return frame

    # ── Scene 8: Why Different (50-57s, 210 frames) ──────────────────────

    def scene_why_different(self, frame_num, t, length):
        frame = new_frame()
        draw = ImageDraw.Draw(frame, "RGBA")

        ft = load_font(FONT_HEAVY, 46)
        draw_centered(draw, "Why DockProbe?", 200, ft, WHITE)
        draw.rectangle([W // 2 - 100, 268, W // 2 + 100, 272], fill=ACCENT)

        fh = load_font(FONT_BOLD, 30)
        fi = load_font(FONT_REGULAR, 25)

        col_l = 70
        col_r = W // 2 + 30
        hy = 350

        draw.text((col_l + 80, hy), "Others", fill=RED, font=fh)
        draw.text((col_r + 50, hy), "DockProbe", fill=ACCENT, font=fh)

        others = [
            "Complex setup",
            "Heavy resources",
            "Multiple services",
            "Steep learning curve",
            "Expensive licensing",
        ]
        dockprobe = [
            "One command setup",
            "~50MB memory",
            "Single container",
            "Zero config needed",
            "100% free & open",
        ]

        # Vertical divider
        mid = W // 2
        draw.line([(mid, hy + 50), (mid, hy + 50 + len(others) * 85)],
                  fill=(50, 55, 65), width=1)

        for i, (left, right) in enumerate(zip(others, dockprobe)):
            item_t = max(0.0, min(1.0, (t * len(others) * 1.3) - i))
            if item_t <= 0:
                continue

            alpha = int(255 * ease_in_out(item_t))
            slide = int((1 - ease_in_out(item_t)) * 20)
            y = hy + 65 + i * 85 + slide

            # X mark and check mark
            draw.text((col_l, y), "X  " + left,
                      fill=(*GRAY, alpha), font=fi)
            draw.text((col_r, y), "V  " + right,
                      fill=(*WHITE, alpha), font=fi)

        # Tagline
        if t > 0.7:
            tag_t = ease_in_out((t - 0.7) / 0.3)
            alpha = int(255 * tag_t)
            ftag = load_font(FONT_BOLD, 38)
            draw_centered(draw, "Simple. Powerful. Free.",
                          1500, ftag, (*ACCENT, alpha))

        return frame

    # ── Scene 9: CTA (57-60s, 90 frames) ─────────────────────────────────

    def scene_cta(self, frame_num, t, length):
        frame = new_frame()
        draw = ImageDraw.Draw(frame, "RGBA")

        # Logo
        appear = ease_in_out(min(t * 3, 1.0))
        alpha = int(255 * appear)

        fl = load_font(FONT_HEAVY, 72)
        draw_centered(draw, "DockProbe", 650, fl, (*WHITE, alpha))

        # Tagline
        fsub = load_font(FONT_REGULAR, 30)
        draw_centered(draw, "Docker Monitoring Dashboard", 740, fsub, (*GRAY, alpha))

        # GitHub URL
        if t > 0.15:
            url_a = int(255 * ease_in_out(min((t - 0.15) * 4, 1.0)))
            fu = load_font(FONT_MONO, 26)
            draw_centered(draw, "github.com/your-user/dockprobe",
                          870, fu, (*ACCENT, url_a))

        # Star button
        if t > 0.3:
            btn_a = int(255 * ease_in_out(min((t - 0.3) * 4, 1.0)))
            bw, bh = 320, 70
            bx = (W - bw) // 2
            by = 960

            draw.rounded_rectangle([bx, by, bx + bw, by + bh],
                                   radius=35, fill=(*ACCENT, btn_a))
            fb = load_font(FONT_BOLD, 28)
            txt = "Star on GitHub"
            bbox = draw.textbbox((0, 0), txt, font=fb)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, by + 19), txt,
                      fill=(13, 17, 23, btn_a), font=fb)

            # Glow pulse
            if t > 0.6:
                pulse = math.sin((t - 0.6) * math.pi * 8) * 0.5 + 0.5
                ga = int(60 * pulse)
                draw.rounded_rectangle(
                    [bx - 6, by - 6, bx + bw + 6, by + bh + 6],
                    radius=40, outline=(*ACCENT, ga), width=3)

        # Bottom text
        fsm = load_font(FONT_REGULAR, 24)
        draw_centered(draw, "Free & Open Source", 1150, fsm, GRAY)

        return frame


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("DockProbe YouTube Shorts Generator")
    print(f"  Output: {OUTPUT}")
    print(f"  Resolution: {W}x{H} @ {FPS}fps")
    print(f"  Duration: {DURATION}s ({TOTAL_FRAMES} frames)")
    print()

    # Find ffmpeg binary
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
            ffmpeg_bin = get_ffmpeg_exe()
        except ImportError:
            pass
    if not ffmpeg_bin:
        print("ERROR: ffmpeg not found.")
        print("  Install via: sudo apt-get install -y ffmpeg")
        print("  Or:          pip install imageio-ffmpeg")
        sys.exit(1)
    print(f"  ffmpeg: {ffmpeg_bin}")

    gen = VideoGenerator()

    ffmpeg_cmd = [
        ffmpeg_bin, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-i", "pipe:",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUTPUT),
    ]

    print("Starting ffmpeg encoder...")
    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("Generating frames...")
    try:
        for frame_num, frame in gen.generate_frames():
            if frame_num % FPS == 0:
                sec = frame_num // FPS
                pct = frame_num * 100 // TOTAL_FRAMES
                print(f"  [{pct:3d}%] Frame {frame_num:4d}/{TOTAL_FRAMES}"
                      f"  ({sec}s/{DURATION}s)", end="\r")
            proc.stdin.write(frame.tobytes())

        proc.stdin.close()
        proc.wait()
        stderr = proc.stderr.read()

        if proc.returncode != 0:
            print(f"\nffmpeg error:\n{stderr.decode()}")
            sys.exit(1)

        size_mb = OUTPUT.stat().st_size / (1024 * 1024)
        print(f"\nDone! Saved to {OUTPUT}")
        print(f"  File size: {size_mb:.1f} MB")

    except BrokenPipeError:
        _, stderr = proc.communicate()
        print(f"\nffmpeg pipe error:\n{stderr.decode()}")
        sys.exit(1)
    except KeyboardInterrupt:
        proc.kill()
        print("\nCancelled")
        sys.exit(1)


if __name__ == "__main__":
    main()
