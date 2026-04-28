import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import customtkinter as ctk
import pandas as pd
import threading
import time
import random
import math
from PIL import Image, ImageEnhance

from brain import UnifiedBrain
from trainer import Trainer
from voice import VoiceEngine
from commands import CommandExecutor

class AssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("A.I. ASSISTANT")
        self.geometry("900x700")
        self.configure(fg_color="#000000")
        
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 900) // 2
        y = (sh - 700) // 2
        self.geometry(f"900x700+{x}+{y}")

        self.brain = UnifiedBrain()
        self.trainer = Trainer(self.brain)
        self.voice = VoiceEngine()
        self.commander = CommandExecutor(self.voice)
        self.base_data_frames = []

        self.home_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.friday_frame = ctk.CTkFrame(self, fg_color="#0d0d0d")
        self.jarvis_frame = ctk.CTkFrame(self, fg_color="#000000")

        self.glow_phase = 0.0
        self.friday_hover = False
        self.jarvis_hover = False

        self.dot_visible = True
        self.typing_dots = 0
        self.typing_active = False

        self.jarvis_active = False
        self.jarvis_state = "idle"
        self.jarvis_is_speaking = False
        self.ring_positions = []
        self.eq_bars = [0.3] * 7
        self.scale_phase = 0.0
        self.typewriter_text = ""
        self.typewriter_index = 0
        self.status_blink_phase = 0
        self.frames = []
        self.dim_frames = []
        self.current_frame = 0

        self.build_home_screen()
        self.build_friday_screen()
        self.build_jarvis_screen()

        self.home_frame.pack(fill="both", expand=True)

        self._load_data()
        self._load_gif_frames()
        self._animate_home_glow()

    def _load_data(self):
        files = ['data/science.csv', 'data/math.csv', 'data/general.csv']
        for f in files:
            if os.path.exists(f):
                self.base_data_frames.append(pd.read_csv(f))
        if os.path.exists('data/learned_knowledge.csv'):
            self.base_data_frames.append(pd.read_csv('data/learned_knowledge.csv'))
        if self.base_data_frames:
            threading.Thread(target=self.brain.load_and_train, args=(self.base_data_frames,), daemon=True).start()

    def show_home(self):
        self.jarvis_active = False
        self.friday_frame.pack_forget()
        self.jarvis_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)

    def show_friday(self):
        self.home_frame.pack_forget()
        self.jarvis_frame.pack_forget()
        self.friday_frame.pack(fill="both", expand=True)
        self._blink_dot()
        self.after(500, lambda: self._add_friday_message("Hello. I'm Friday. How can I help you?"))

    def show_jarvis(self):
        self.home_frame.pack_forget()
        self.friday_frame.pack_forget()
        self.jarvis_frame.pack(fill="both", expand=True)
        self.jarvis_active = True
        self.jarvis_state = "idle"
        self._start_jarvis_animation()
        threading.Thread(target=self._wake_word_loop, daemon=True).start()

    def build_home_screen(self):
        title_label = ctk.CTkLabel(self.home_frame, text="A.I. ASSISTANT", font=("Segoe UI Light", 28, "bold"), text_color="#FFD700")
        title_label.pack(pady=(100, 0))
        subtitle = ctk.CTkLabel(self.home_frame, text="Select Your Interface", font=("Segoe UI Light", 14), text_color="#666666")
        subtitle.pack(pady=(5, 50))

        button_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        button_frame.pack(expand=True)

        self.friday_canvas = ctk.CTkCanvas(button_frame, width=240, height=240, bg="#000000", highlightthickness=0)
        self.friday_canvas.grid(row=0, column=0, padx=40)
        self.jarvis_canvas = ctk.CTkCanvas(button_frame, width=240, height=240, bg="#000000", highlightthickness=0)
        self.jarvis_canvas.grid(row=0, column=1, padx=40)

        self.friday_canvas.bind("<Enter>", lambda e: setattr(self, 'friday_hover', True))
        self.friday_canvas.bind("<Leave>", lambda e: setattr(self, 'friday_hover', False))
        self.jarvis_canvas.bind("<Enter>", lambda e: setattr(self, 'jarvis_hover', True))
        self.jarvis_canvas.bind("<Leave>", lambda e: setattr(self, 'jarvis_hover', False))

        self.friday_canvas.bind("<Button-1>", lambda e: self.show_friday())
        self.jarvis_canvas.bind("<Button-1>", lambda e: self.show_jarvis())

    def _draw_glowing_button(self, canvas, label, base_color_rgb, glow_intensity, is_hover):
        canvas.delete("all")
        w, h = 240, 240
        cx, cy = w // 2, h // 2
        r, g, b = base_color_rgb
        intensity = 0.4 + 0.3 * glow_intensity
        if is_hover:
            intensity = min(1.0, intensity + 0.3)

        for i in range(8, 0, -1):
            radius = 60 + i * 8
            alpha = intensity * (1.0 - i / 10.0) * 0.4
            color = f"#{int(r * alpha):02x}{int(g * alpha):02x}{int(b * alpha):02x}"
            canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=2)

        btn_r = 55
        fill_alpha = 0.15 if not is_hover else 0.3
        fill_color = f"#{max(int(r * fill_alpha),1):02x}{max(int(g * fill_alpha),1):02x}{max(int(b * fill_alpha),1):02x}"
        border_alpha = 0.7 if not is_hover else 1.0
        border_color = f"#{int(min(255, r * border_alpha)):02x}{int(min(255, g * border_alpha)):02x}{int(min(255, b * border_alpha)):02x}"
        
        canvas.create_oval(cx - btn_r, cy - btn_r, cx + btn_r, cy + btn_r, fill=fill_color, outline=border_color, width=2)

        text_alpha = 0.8 if not is_hover else 1.0
        text_color = f"#{max(int(min(255, r * text_alpha)),1):02x}{max(int(min(255, g * text_alpha)),1):02x}{max(int(min(255, b * text_alpha)),1):02x}"
        
        canvas.create_text(cx, cy, text=label, font=("Segoe UI", 20, "bold"), fill=text_color)
        sub_text = "Text Chat" if label == "FRIDAY" else "Voice Control"
        canvas.create_text(cx, cy + 80, text=sub_text, font=("Segoe UI Light", 11), fill="#555555")

    def _animate_home_glow(self):
        self.glow_phase += 0.05
        glow = (math.sin(self.glow_phase) + 1) / 2
        self._draw_glowing_button(self.friday_canvas, "FRIDAY", (0, 255, 255), glow, self.friday_hover)
        self._draw_glowing_button(self.jarvis_canvas, "JARVIS", (255, 215, 0), glow, self.jarvis_hover)
        self.after(50, self._animate_home_glow)

    def build_friday_screen(self):
        top_bar = ctk.CTkFrame(self.friday_frame, fg_color="#111111", height=50, corner_radius=0)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        ctk.CTkButton(top_bar, text="←  Back", width=80, fg_color="transparent", hover_color="#222222", text_color="#888888", font=("Segoe UI", 13), command=self.show_home).pack(side="left", padx=10)
        ctk.CTkLabel(top_bar, text="FRIDAY", font=("Segoe UI", 18, "bold"), text_color="#FFFFFF").pack(side="left", padx=10)
        
        self.dot_canvas = ctk.CTkCanvas(top_bar, width=16, height=16, bg="#111111", highlightthickness=0)
        self.dot_canvas.pack(side="left", padx=(2, 10), pady=0)
        
        ctk.CTkButton(top_bar, text="Train Brain", width=90, fg_color="#1a1a1a", hover_color="#333333", text_color="#00CCCC", font=("Segoe UI", 12), corner_radius=8, command=self._open_train_mode).pack(side="right", padx=10)

        chat_frame = ctk.CTkFrame(self.friday_frame, fg_color="#0d0d0d")
        chat_frame.pack(fill="both", expand=True, padx=15, pady=(10, 5))

        self.chat_display = ctk.CTkTextbox(chat_frame, fg_color="#121212", text_color="#CCCCCC", font=("Segoe UI", 13), corner_radius=12, border_width=1, border_color="#1a1a1a", state="disabled", wrap="word")
        self.chat_display.pack(fill="both", expand=True)

        self.chat_display._textbox.tag_configure("user_name", foreground="#FFFFFF", font=("Segoe UI Semibold", 13))
        self.chat_display._textbox.tag_configure("user_msg", foreground="#DDDDDD", font=("Segoe UI", 13))
        self.chat_display._textbox.tag_configure("friday_name", foreground="#00FFFF", font=("Segoe UI Semibold", 13))
        self.chat_display._textbox.tag_configure("friday_msg", foreground="#00DDDD", font=("Segoe UI", 13))

        self.typing_label = ctk.CTkLabel(self.friday_frame, text="", font=("Segoe UI", 12), text_color="#00AAAA", fg_color="transparent")
        self.typing_label.pack(anchor="w", padx=25)

        input_frame = ctk.CTkFrame(self.friday_frame, fg_color="#0d0d0d", height=55)
        input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.text_input = ctk.CTkEntry(input_frame, placeholder_text="Ask Friday something...", fg_color="#1a1a1a", border_color="#252525", text_color="#FFFFFF", font=("Segoe UI", 13), height=42, corner_radius=20)
        self.text_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.text_input.bind("<Return>", self._send_message)

        ctk.CTkButton(input_frame, text="Send", width=80, height=42, fg_color="#00CCCC", hover_color="#00AAAA", text_color="#000000", font=("Segoe UI Semibold", 13), corner_radius=20, command=self._send_message).pack(side="right")

    def _blink_dot(self):
        if not self.friday_frame.winfo_ismapped():
            return
        self.dot_canvas.delete("all")
        if self.dot_visible:
            self.dot_canvas.create_oval(4, 4, 12, 12, fill="#00FFFF", outline="")
        self.dot_visible = not self.dot_visible
        self.after(800, self._blink_dot)

    def _add_user_message(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.insert("end", "  You  ", "user_name")
        self.chat_display._textbox.insert("end", f"\n  {text}\n\n", "user_msg")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _add_friday_message(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.insert("end", "  Friday  ", "friday_name")
        self.chat_display._textbox.insert("end", f"\n  {text}\n\n", "friday_msg")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _start_typing(self):
        self.typing_active = True
        self.typing_dots = 0
        self._animate_typing()

    def _animate_typing(self):
        if not self.typing_active:
            self.typing_label.configure(text="")
            return
        dots = "." * (self.typing_dots % 4)
        self.typing_label.configure(text=f"  Friday is thinking{dots}")
        self.typing_dots += 1
        self.after(400, self._animate_typing)

    def _stop_typing(self):
        self.typing_active = False
        self.typing_label.configure(text="")

    def _send_message(self, event=None):
        user_text = self.text_input.get().strip()
        if not user_text:
            return
        self._add_user_message(user_text)
        self.text_input.delete(0, "end")
        self._start_typing()
        threading.Thread(target=self._process_response, args=(user_text,), daemon=True).start()

    def _process_response(self, text):
        answer = self.brain.get_answer(text)
        time.sleep(0.3)
        self.after(0, self._display_response, answer)

    def _display_response(self, answer):
        self._stop_typing()
        if answer:
            self._add_friday_message(answer)
        else:
            self._add_friday_message("I don't know that yet. You can teach me using Train Brain.")

    def _open_train_mode(self):
        train_window = ctk.CTkToplevel(self)
        train_window.title("Train Brain")
        train_window.geometry("420x380")
        train_window.configure(fg_color="#111111")
        train_window.attributes('-topmost', True)

        ctk.CTkLabel(train_window, text="Teach Friday", font=("Segoe UI", 18, "bold"), text_color="#00CCCC").pack(pady=(20, 15))
        ctk.CTkLabel(train_window, text="Category:", text_color="#888888").pack(anchor="w", padx=30)
        cat_entry = ctk.CTkEntry(train_window, width=340, fg_color="#1a1a1a", border_color="#252525")
        cat_entry.pack(pady=(0, 10), padx=30)
        ctk.CTkLabel(train_window, text="Question:", text_color="#888888").pack(anchor="w", padx=30)
        q_entry = ctk.CTkEntry(train_window, width=340, fg_color="#1a1a1a", border_color="#252525")
        q_entry.pack(pady=(0, 10), padx=30)
        ctk.CTkLabel(train_window, text="Answer:", text_color="#888888").pack(anchor="w", padx=30)
        a_entry = ctk.CTkEntry(train_window, width=340, fg_color="#1a1a1a", border_color="#252525")
        a_entry.pack(pady=(0, 15), padx=30)

        def save():
            c, q, a = cat_entry.get(), q_entry.get(), a_entry.get()
            if c and q and a:
                self.trainer.add_knowledge(c, q, a, self.base_data_frames)
                train_window.destroy()

        ctk.CTkButton(train_window, text="Save Knowledge", fg_color="#00CCCC", hover_color="#00AAAA", text_color="#000000", corner_radius=10, command=save).pack(pady=10)

    def build_jarvis_screen(self):
        ctk.CTkButton(self.jarvis_frame, text="←  Back", width=80, fg_color="transparent", hover_color="#1a1a1a", text_color="#888888", font=("Segoe UI", 13), command=self.show_home).place(x=15, y=15)
        
        self.jarvis_canvas = ctk.CTkCanvas(self.jarvis_frame, bg="#000000", highlightthickness=0)
        self.jarvis_canvas.pack(fill="both", expand=True)

        self.status_label = ctk.CTkLabel(self.jarvis_frame, text="Say 'Hey Jarvis' to wake me...", font=("Segoe UI Light", 16), text_color="#665500")
        self.status_label.place(relx=0.5, rely=0.92, anchor="center")

    def _load_gif_frames(self):
        gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_loop.gif")
        try:
            img = Image.open(gif_path)
            frame_idx = 0
            while True:
                frame = img.copy().convert("RGBA")
                self.frames.append(ctk.CTkImage(frame, size=(400, 400)))
                dimmed = ImageEnhance.Brightness(frame).enhance(0.45)
                self.dim_frames.append(ctk.CTkImage(dimmed, size=(400, 400)))
                frame_idx += 1
                img.seek(frame_idx)
        except (EOFError, FileNotFoundError):
            pass

    def _start_jarvis_animation(self):
        if not self.jarvis_active:
            return
        self.jarvis_canvas.delete("all")
        w = self.jarvis_canvas.winfo_width()
        h = self.jarvis_canvas.winfo_height()
        if w > 10 and h > 10:
            cx, cy = w // 2, h // 2 - 30
            self.glow_phase += 0.04

            if self.jarvis_state == "idle":
                self._draw_idle_glow(cx, cy)
            elif self.jarvis_state == "listening":
                self._draw_listening_rings(cx, cy)
            elif self.jarvis_state == "speaking":
                self._draw_speaking_effects(cx, cy)

            if self.frames:
                frame_img = self.dim_frames[self.current_frame % len(self.dim_frames)] if self.jarvis_state == "idle" and self.dim_frames else self.frames[self.current_frame % len(self.frames)]
                self.jarvis_canvas.create_image(cx, cy, image=frame_img._light_image, anchor="center")
                self.current_frame = (self.current_frame + 1) % len(self.frames)

            self._update_status_animation()
        self.after(50, self._start_jarvis_animation)

    def _draw_idle_glow(self, cx, cy):
        intensity = (math.sin(self.glow_phase) + 1) / 2
        for i in range(6):
            radius = 210 + i * 12
            alpha = intensity * 0.12 * (1 - i / 7)
            r = int(255 * alpha)
            g = int(180 * alpha)
            self.jarvis_canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=f"#{max(r,1):02x}{max(g,1):02x}01", width=2)

    def _draw_listening_rings(self, cx, cy):
        if len(self.ring_positions) < 5:
            if not self.ring_positions or self.ring_positions[-1][0] > 240:
                self.ring_positions.append([210, 1.0])
        new_rings = []
        for ring in self.ring_positions:
            ring[0] += 3
            ring[1] -= 0.015
            if ring[1] > 0:
                new_rings.append(ring)
                radius = ring[0]
                alpha = ring[1]
                self.jarvis_canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=f"#{max(int(255*alpha),1):02x}{max(int(215*alpha),1):02x}{max(int(50*alpha),1):02x}", width=3)
        self.ring_positions = new_rings
        for i in range(4):
            radius = 205 + i * 5
            self.jarvis_canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=f"#{max(int(255*0.2*(1-i/5)),1):02x}{max(int(200*0.2*(1-i/5)),1):02x}01", width=2)

    def _draw_speaking_effects(self, cx, cy):
        self.scale_phase += 0.08
        intensity = 0.6 + 0.2 * math.sin(self.scale_phase)
        for i in range(8):
            radius = 210 + i * 10
            alpha = intensity * 0.2 * (1 - i / 9)
            self.jarvis_canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=f"#{max(int(255*alpha),1):02x}{max(int(200*alpha),1):02x}{max(int(50*alpha),1):02x}", width=2)

        bar_width, bar_gap, bar_count = 12, 6, 7
        start_x = cx - (bar_count * (bar_width + bar_gap) - bar_gap) // 2
        bar_y = cy + 230
        for i in range(bar_count):
            target = random.uniform(0.2, 1.0)
            self.eq_bars[i] += (target - self.eq_bars[i]) * 0.3
            bar_h = int(self.eq_bars[i] * 60)
            alpha = 0.5 + 0.5 * self.eq_bars[i]
            self.jarvis_canvas.create_rectangle(start_x + i * (bar_width + bar_gap), bar_y - bar_h, start_x + i * (bar_width + bar_gap) + bar_width, bar_y, fill=f"#{int(255*alpha):02x}{max(int(180*alpha),1):02x}01", outline="")

    def _update_status_animation(self):
        if self.jarvis_state == "idle":
            self.status_blink_phase += 1
            self.status_label.configure(text="Say 'Hey Jarvis' to wake me...", text_color="#665500" if self.status_blink_phase % 40 < 30 else "#332a00")
        elif self.jarvis_state == "listening":
            self.status_blink_phase += 1
            self.status_label.configure(text="Listening...", text_color="#FFD700" if self.status_blink_phase % 20 < 15 else "#CC9900")
        elif self.jarvis_state == "speaking":
            if self.typewriter_index < len(self.typewriter_text):
                self.typewriter_index += 1
            display_text = self.typewriter_text[:self.typewriter_index]
            self.status_label.configure(text="..." + display_text[-77:] if len(display_text) > 80 else display_text, text_color="#FFD700")

    def _wake_word_loop(self):
        while self.jarvis_active:
            if self.jarvis_state != "idle":
                time.sleep(0.5)
                continue
            try:
                text = self.voice.listen()
                if text and ("hey jarvis" in text or "jarvis" in text):
                    self.jarvis_state = "listening"
                    self.ring_positions = []
                    self._speak_text("Hello sir, how can I help you?")
                    self._listen_for_command()
            except Exception:
                time.sleep(1)

    def _listen_for_command(self):
        self.jarvis_state = "listening"
        self.ring_positions = []
        try:
            command = self.voice.listen()
            if command:
                if any(kw in command for kw in ["open", "shutdown", "restart", "close"]):
                    self._speak_text("Roger that, sir.")
                    self.commander.execute(command)
                else:
                    answer = self.brain.get_answer(command)
                    self._speak_text(answer if answer else "I don't have that information yet, sir. Please train me.")
            self.jarvis_state = "idle"
        except Exception:
            self.jarvis_state = "idle"

    def _speak_text(self, text):
        self.jarvis_state = "speaking"
        self.typewriter_text = text
        self.typewriter_index = 0
        self.jarvis_is_speaking = True

        def speak_worker():
            self.voice.speak(text)
            self.jarvis_is_speaking = False
            time.sleep(0.3)
            if self.jarvis_state == "speaking":
                self.jarvis_state = "idle"

        threading.Thread(target=speak_worker, daemon=True).start()
        while self.jarvis_is_speaking:
            time.sleep(0.1)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = AssistantApp()
    app.mainloop()