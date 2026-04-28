import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import customtkinter as ctk
import pandas as pd
import threading
import time
import random
import math
from PIL import Image

from brain import UnifiedBrain
from trainer import Trainer
from voice import VoiceEngine
from commands import CommandExecutor


class JarvisApp(ctk.CTk):
    """Full-screen voice-controlled JARVIS interface with animated GIF orb."""

    # ── Animation States ──
    STATE_IDLE = "idle"
    STATE_LISTENING = "listening"
    STATE_SPEAKING = "speaking"

    def __init__(self):
        super().__init__()
        self.title("JARVIS")
        self.configure(fg_color="#000000")
        self.attributes("-fullscreen", True)

        # ── Engine init ──
        self.voice = VoiceEngine()
        self.commander = CommandExecutor(self.voice)
        self.brain = UnifiedBrain()
        self.trainer = Trainer(self.brain)
        self.base_data_frames = []

        # ── State ──
        self.state = self.STATE_IDLE
        self.running = True
        self.is_speaking = False
        self.spoken_text = ""

        # ── GIF Frames ──
        self.gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_loop.gif")
        self.frames = []
        self.dim_frames = []
        self.current_frame = 0
        self._load_gif_frames()

        # ── Layout ──
        # Close button (top right)
        self.close_btn = ctk.CTkButton(
            self,
            text="✕",
            width=40, height=40,
            fg_color="transparent",
            hover_color="#1a1a1a",
            text_color="#555555",
            font=("Segoe UI", 18),
            corner_radius=8,
            command=self._close
        )
        self.close_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-15, y=15)

        # Main canvas for GIF + animations
        self.canvas = ctk.CTkCanvas(
            self,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Status text at bottom
        self.status_label = ctk.CTkLabel(
            self,
            text="Say 'Hey Jarvis' to wake me...",
            font=("Segoe UI Light", 16),
            text_color="#665500"
        )
        self.status_label.place(relx=0.5, rely=0.92, anchor="center")

        # ── Animation vars ──
        self.glow_phase = 0.0
        self.ring_positions = []  # list of (radius, alpha) for expanding rings
        self.eq_bars = [0.3] * 7  # equalizer bar heights
        self.scale_phase = 0.0
        self.typewriter_text = ""
        self.typewriter_index = 0
        self.status_blink_phase = 0

        # ── Load data ──
        self._load_data()

        # ── Start systems ──
        self.after(100, self._start_animation)
        self.after(500, self._start_wake_word_listener)

        # Bind escape key
        self.bind("<Escape>", lambda e: self._close())

    # ──────────────── GIF Loading ────────────────
    def _load_gif_frames(self):
        try:
            img = Image.open(self.gif_path)
            frame_idx = 0
            while True:
                frame = img.copy().convert("RGBA")
                # Full brightness frame
                full_frame = ctk.CTkImage(frame, size=(400, 400))
                self.frames.append(full_frame)

                # Dimmed frame (50% brightness)
                from PIL import ImageEnhance
                dimmed = ImageEnhance.Brightness(frame).enhance(0.45)
                dim_frame = ctk.CTkImage(dimmed, size=(400, 400))
                self.dim_frames.append(dim_frame)

                frame_idx += 1
                img.seek(frame_idx)
        except EOFError:
            pass
        except FileNotFoundError:
            pass

    # ──────────────── Data Loading ────────────────
    def _load_data(self):
        files = ['data/science.csv', 'data/math.csv', 'data/general.csv']
        for f in files:
            if os.path.exists(f):
                self.base_data_frames.append(pd.read_csv(f))
        if os.path.exists('data/learned_knowledge.csv'):
            self.base_data_frames.append(pd.read_csv('data/learned_knowledge.csv'))
        if self.base_data_frames:
            threading.Thread(target=self.brain.load_and_train, args=(self.base_data_frames,), daemon=True).start()

    # ──────────────── Animation Engine ────────────────
    def _start_animation(self):
        if not self.running:
            return
        self._render_frame()
        self.after(50, self._start_animation)

    def _render_frame(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w // 2, h // 2 - 30

        # ── Draw glow behind orb ──
        self.glow_phase += 0.04

        if self.state == self.STATE_IDLE:
            self._draw_idle_glow(cx, cy)
        elif self.state == self.STATE_LISTENING:
            self._draw_listening_rings(cx, cy)
        elif self.state == self.STATE_SPEAKING:
            self._draw_speaking_effects(cx, cy, w, h)

        # ── Draw GIF frame ──
        if self.frames:
            if self.state == self.STATE_IDLE and self.dim_frames:
                frame_img = self.dim_frames[self.current_frame % len(self.dim_frames)]
            else:
                frame_img = self.frames[self.current_frame % len(self.frames)]

            self.canvas.create_image(cx, cy, image=frame_img._light_image, anchor="center")
            self.current_frame = (self.current_frame + 1) % len(self.frames)

        # ── Update status text animation ──
        self._update_status_animation()

    def _draw_idle_glow(self, cx, cy):
        """Dim gold outer glow that pulses gently."""
        intensity = (math.sin(self.glow_phase) + 1) / 2  # 0..1
        for i in range(6):
            radius = 210 + i * 12
            alpha = intensity * 0.12 * (1 - i / 7)
            r = int(255 * alpha)
            g = int(180 * alpha)
            b = int(0 * alpha)
            if r < 1: r = 1
            if g < 1: g = 1
            color = f"#{r:02x}{g:02x}{max(b,1):02x}"
            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=color, width=2
            )

    def _draw_listening_rings(self, cx, cy):
        """Concentric gold rings expanding outward and fading."""
        # Add new ring periodically
        if len(self.ring_positions) < 5:
            if not self.ring_positions or self.ring_positions[-1][0] > 240:
                self.ring_positions.append([210, 1.0])

        # Update rings
        new_rings = []
        for ring in self.ring_positions:
            ring[0] += 3  # expand
            ring[1] -= 0.015  # fade
            if ring[1] > 0:
                new_rings.append(ring)
                radius = ring[0]
                alpha = ring[1]
                r = int(min(255, 255 * alpha))
                g = int(min(255, 215 * alpha))
                b = int(min(255, 50 * alpha))
                color = f"#{max(r,1):02x}{max(g,1):02x}{max(b,1):02x}"
                self.canvas.create_oval(
                    cx - radius, cy - radius, cx + radius, cy + radius,
                    outline=color, width=3
                )
        self.ring_positions = new_rings

        # Bright inner glow
        for i in range(4):
            radius = 205 + i * 5
            r_val = int(255 * 0.2 * (1 - i/5))
            g_val = int(200 * 0.2 * (1 - i/5))
            color = f"#{max(r_val,1):02x}{max(g_val,1):02x}#01"
            try:
                self.canvas.create_oval(
                    cx - radius, cy - radius, cx + radius, cy + radius,
                    outline=f"#{max(r_val,1):02x}{max(g_val,1):02x}{1:02x}", width=2
                )
            except Exception:
                pass

    def _draw_speaking_effects(self, cx, cy, w, h):
        """Intense glow + equalizer bars below orb."""
        # Intense glow
        self.scale_phase += 0.08
        intensity = 0.6 + 0.2 * math.sin(self.scale_phase)

        for i in range(8):
            radius = 210 + i * 10
            alpha = intensity * 0.2 * (1 - i / 9)
            r = int(min(255, 255 * alpha))
            g = int(min(255, 200 * alpha))
            b = int(min(255, 50 * alpha))
            color = f"#{max(r,1):02x}{max(g,1):02x}{max(b,1):02x}"
            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=color, width=2
            )

        # ── Equalizer bars ──
        bar_count = 7
        bar_width = 12
        bar_gap = 6
        total_w = bar_count * (bar_width + bar_gap) - bar_gap
        start_x = cx - total_w // 2
        bar_y = cy + 230

        for i in range(bar_count):
            # Randomize target heights
            target = random.uniform(0.2, 1.0)
            self.eq_bars[i] += (target - self.eq_bars[i]) * 0.3
            bar_h = int(self.eq_bars[i] * 60)

            x1 = start_x + i * (bar_width + bar_gap)
            y1 = bar_y - bar_h
            x2 = x1 + bar_width
            y2 = bar_y

            # Gold gradient feel
            alpha = 0.5 + 0.5 * self.eq_bars[i]
            r = int(255 * alpha)
            g = int(180 * alpha)
            color = f"#{r:02x}{g:02x}#01"
            try:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=f"#{r:02x}{max(g,1):02x}{1:02x}",
                    outline=""
                )
            except Exception:
                pass

    def _update_status_animation(self):
        """Update the status label based on current state."""
        if self.state == self.STATE_IDLE:
            self.status_blink_phase += 1
            if self.status_blink_phase % 40 < 30:
                self.status_label.configure(
                    text="Say 'Hey Jarvis' to wake me...",
                    text_color="#665500"
                )
            else:
                self.status_label.configure(
                    text="Say 'Hey Jarvis' to wake me...",
                    text_color="#332a00"
                )
        elif self.state == self.STATE_LISTENING:
            self.status_blink_phase += 1
            if self.status_blink_phase % 20 < 15:
                self.status_label.configure(text="Listening...", text_color="#FFD700")
            else:
                self.status_label.configure(text="Listening...", text_color="#CC9900")
        elif self.state == self.STATE_SPEAKING:
            # Typewriter effect for spoken text
            if self.typewriter_index < len(self.typewriter_text):
                self.typewriter_index += 1
            display_text = self.typewriter_text[:self.typewriter_index]
            # Truncate if too long
            if len(display_text) > 80:
                display_text = "..." + display_text[-77:]
            self.status_label.configure(text=display_text, text_color="#FFD700")

    # ──────────────── Wake Word Listener ────────────────
    def _start_wake_word_listener(self):
        threading.Thread(target=self._wake_word_loop, daemon=True).start()

    def _wake_word_loop(self):
        """Continuously listen for 'hey jarvis' or 'jarvis' wake word."""
        while self.running:
            if self.state != self.STATE_IDLE:
                time.sleep(0.5)
                continue

            try:
                text = self.voice.listen()
                if text and ("hey jarvis" in text or "jarvis" in text):
                    self._on_wake()
            except Exception:
                time.sleep(1)

    def _on_wake(self):
        """Triggered when wake word is detected."""
        self.state = self.STATE_LISTENING
        self.ring_positions = []

        # Greeting
        self._speak_text("Hello sir, how can I help you?")

        # Now listen for the actual command
        self._listen_for_command()

    def _listen_for_command(self):
        """Listen for the user's actual question after wake."""
        self.state = self.STATE_LISTENING
        self.ring_positions = []

        try:
            command = self.voice.listen()
            if command:
                self._process_command(command)
            else:
                self.state = self.STATE_IDLE
        except Exception:
            self.state = self.STATE_IDLE

    def _process_command(self, command):
        """Route command to commands.py or brain."""
        # Check if it's a system command
        cmd_keywords = ["open", "shutdown", "restart", "close"]
        if any(kw in command for kw in cmd_keywords):
            self._speak_text("Roger that, sir.")
            self.commander.execute(command)
            self.state = self.STATE_IDLE
            return

        # Check brain (CSV + Ollama fallback)
        answer = self.brain.get_answer(command)
        if answer:
            self._speak_text(answer)
        else:
            self._speak_text("I don't have that information yet, sir. Please train me.")

        self.state = self.STATE_IDLE

    def _speak_text(self, text):
        """Speak text with speaking animation state."""
        self.state = self.STATE_SPEAKING
        self.typewriter_text = text
        self.typewriter_index = 0
        self.is_speaking = True

        # Speak in a sub-thread so animation keeps running
        def speak_worker():
            self.voice.speak(text)
            self.is_speaking = False
            # Small delay to let animation finish
            time.sleep(0.3)
            if self.state == self.STATE_SPEAKING:
                self.state = self.STATE_IDLE

        threading.Thread(target=speak_worker, daemon=True).start()

        # Wait for speaking to finish
        while self.is_speaking:
            time.sleep(0.1)

    # ──────────────── Close ────────────────
    def _close(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = JarvisApp()
    app.mainloop()
