import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import customtkinter as ctk
import pandas as pd
import threading
import time

from brain import UnifiedBrain
from trainer import Trainer


class FridayApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FRIDAY")
        self.geometry("800x650")
        self.configure(fg_color="#0d0d0d")

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 800) // 2
        y = (sh - 650) // 2
        self.geometry(f"800x650+{x}+{y}")

        # ── Init brain ──
        self.brain = UnifiedBrain()
        self.trainer = Trainer(self.brain)
        self.base_data_frames = []
        self._load_data()

        # ── Top Bar ──
        self.top_bar = ctk.CTkFrame(self, fg_color="#111111", height=50, corner_radius=0)
        self.top_bar.pack(fill="x")
        self.top_bar.pack_propagate(False)

        self.back_btn = ctk.CTkButton(
            self.top_bar,
            text="←  Back",
            width=80,
            fg_color="transparent",
            hover_color="#222222",
            text_color="#888888",
            font=("Segoe UI", 13),
            command=self._go_back
        )
        self.back_btn.pack(side="left", padx=10)

        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="FRIDAY",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        )
        self.title_label.pack(side="left", padx=10)

        # Blinking active dot (canvas)
        self.dot_canvas = ctk.CTkCanvas(
            self.top_bar, width=16, height=16,
            bg="#111111", highlightthickness=0
        )
        self.dot_canvas.pack(side="left", padx=(2, 10), pady=0)
        self.dot_visible = True
        self._blink_dot()

        # Train button
        self.train_btn = ctk.CTkButton(
            self.top_bar,
            text="Train Brain",
            width=90,
            fg_color="#1a1a1a",
            hover_color="#333333",
            text_color="#00CCCC",
            font=("Segoe UI", 12),
            corner_radius=8,
            command=self._open_train_mode
        )
        self.train_btn.pack(side="right", padx=10)

        # ── Chat display ──
        self.chat_frame = ctk.CTkFrame(self, fg_color="#0d0d0d")
        self.chat_frame.pack(fill="both", expand=True, padx=15, pady=(10, 5))

        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            fg_color="#121212",
            text_color="#CCCCCC",
            font=("Segoe UI", 13),
            corner_radius=12,
            border_width=1,
            border_color="#1a1a1a",
            state="disabled",
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True)

        # Configure tags for colored text
        self.chat_display._textbox.tag_configure("user_name", foreground="#FFFFFF", font=("Segoe UI Semibold", 13))
        self.chat_display._textbox.tag_configure("user_msg", foreground="#DDDDDD", font=("Segoe UI", 13))
        self.chat_display._textbox.tag_configure("friday_name", foreground="#00FFFF", font=("Segoe UI Semibold", 13))
        self.chat_display._textbox.tag_configure("friday_msg", foreground="#00DDDD", font=("Segoe UI", 13))
        self.chat_display._textbox.tag_configure("system_msg", foreground="#555555", font=("Segoe UI Italic", 12))

        # ── Typing indicator ──
        self.typing_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 12),
            text_color="#00AAAA",
            fg_color="transparent"
        )
        self.typing_label.pack(anchor="w", padx=25)
        self.typing_dots = 0
        self.typing_active = False

        # ── Input bar ──
        self.input_frame = ctk.CTkFrame(self, fg_color="#0d0d0d", height=55)
        self.input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.text_input = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Ask Friday something...",
            fg_color="#1a1a1a",
            border_color="#252525",
            text_color="#FFFFFF",
            placeholder_text_color="#555555",
            font=("Segoe UI", 13),
            height=42,
            corner_radius=20
        )
        self.text_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.text_input.bind("<Return>", self._send_message)

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Send",
            width=80,
            height=42,
            fg_color="#00CCCC",
            hover_color="#00AAAA",
            text_color="#000000",
            font=("Segoe UI Semibold", 13),
            corner_radius=20,
            command=self._send_message
        )
        self.send_btn.pack(side="right")

        # ── Greet ──
        self.after(500, self._greet)

    # ──────────────── Data Loading ────────────────
    def _load_data(self):
        files = ['data/science.csv', 'data/math.csv', 'data/general.csv']
        for f in files:
            if os.path.exists(f):
                self.base_data_frames.append(pd.read_csv(f))
        if os.path.exists('data/learned_knowledge.csv'):
            self.base_data_frames.append(pd.read_csv('data/learned_knowledge.csv'))
        if self.base_data_frames:
            # Load in background to not freeze UI
            threading.Thread(target=self.brain.load_and_train, args=(self.base_data_frames,), daemon=True).start()

    # ──────────────── Blinking Dot ────────────────
    def _blink_dot(self):
        self.dot_canvas.delete("all")
        if self.dot_visible:
            self.dot_canvas.create_oval(4, 4, 12, 12, fill="#00FFFF", outline="")
        self.dot_visible = not self.dot_visible
        self.after(800, self._blink_dot)

    # ──────────────── Greeting ────────────────
    def _greet(self):
        self._add_friday_message("Hello. I'm Friday. How can I help you?")

    # ──────────────── Chat Methods ────────────────
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

    # ──────────────── Typing Indicator ────────────────
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

    # ──────────────── Send / Process ────────────────
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
        # Small delay so typing indicator is visible
        time.sleep(0.3)
        self.after(0, self._display_response, answer)

    def _display_response(self, answer):
        self._stop_typing()
        if answer:
            self._add_friday_message(answer)
        else:
            self._add_friday_message("I don't know that yet. You can teach me using Train Brain.")

    # ──────────────── Navigation ────────────────
    def _go_back(self):
        self.destroy()

    # ──────────────── Train Mode ────────────────
    def _open_train_mode(self):
        train_window = ctk.CTkToplevel(self)
        train_window.title("Train Brain")
        train_window.geometry("420x380")
        train_window.configure(fg_color="#111111")
        train_window.attributes('-topmost', True)

        ctk.CTkLabel(
            train_window, text="Teach Friday",
            font=("Segoe UI", 18, "bold"),
            text_color="#00CCCC"
        ).pack(pady=(20, 15))

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

        ctk.CTkButton(
            train_window, text="Save Knowledge",
            fg_color="#00CCCC", hover_color="#00AAAA",
            text_color="#000000", corner_radius=10,
            command=save
        ).pack(pady=10)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = FridayApp()
    app.mainloop()
