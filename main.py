import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import customtkinter as ctk
import subprocess
import sys
import math

class ModeSelector(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("A.I. ASSISTANT")
        self.geometry("700x500")
        self.configure(fg_color="#000000")
        self.resizable(False, False)

        # Center window on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 700) // 2
        y = (sh - 500) // 2
        self.geometry(f"700x500+{x}+{y}")

        # ── Title ──
        self.title_label = ctk.CTkLabel(
            self,
            text="A.I. ASSISTANT",
            font=("Segoe UI Light", 28, "bold"),
            text_color="#FFD700"
        )
        self.title_label.pack(pady=(40, 0))

        self.subtitle = ctk.CTkLabel(
            self,
            text="Select Your Interface",
            font=("Segoe UI Light", 14),
            text_color="#666666"
        )
        self.subtitle.pack(pady=(5, 0))

        # ── Button Container ──
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(expand=True)

        # ── FRIDAY Button (Canvas-based glow) ──
        self.friday_canvas = ctk.CTkCanvas(
            self.button_frame,
            width=240, height=240,
            bg="#000000", highlightthickness=0
        )
        self.friday_canvas.grid(row=0, column=0, padx=40)

        # ── JARVIS Button (Canvas-based glow) ──
        self.jarvis_canvas = ctk.CTkCanvas(
            self.button_frame,
            width=240, height=240,
            bg="#000000", highlightthickness=0
        )
        self.jarvis_canvas.grid(row=0, column=1, padx=40)

        # Glow animation state
        self.glow_phase = 0.0
        self.friday_hover = False
        self.jarvis_hover = False

        # Bind hover events
        self.friday_canvas.bind("<Enter>", lambda e: self._set_hover("friday", True))
        self.friday_canvas.bind("<Leave>", lambda e: self._set_hover("friday", False))
        self.jarvis_canvas.bind("<Enter>", lambda e: self._set_hover("jarvis", True))
        self.jarvis_canvas.bind("<Leave>", lambda e: self._set_hover("jarvis", False))

        # Bind clicks
        self.friday_canvas.bind("<Button-1>", lambda e: self.launch_friday())
        self.jarvis_canvas.bind("<Button-1>", lambda e: self.launch_jarvis())

        # Start animation
        self._animate_glow()

    def _set_hover(self, target, state):
        if target == "friday":
            self.friday_hover = state
        else:
            self.jarvis_hover = state

    def _draw_glowing_button(self, canvas, label, base_color_rgb, glow_intensity, is_hover):
        canvas.delete("all")
        w, h = 240, 240
        cx, cy = w // 2, h // 2

        r, g, b = base_color_rgb
        intensity = 0.4 + 0.3 * glow_intensity
        if is_hover:
            intensity = min(1.0, intensity + 0.3)

        # Draw outer glow rings
        for i in range(8, 0, -1):
            radius = 60 + i * 8
            alpha = intensity * (1.0 - i / 10.0) * 0.4
            cr = int(r * alpha)
            cg = int(g * alpha)
            cb = int(b * alpha)
            color = f"#{cr:02x}{cg:02x}{cb:02x}"
            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=color, width=2
            )

        # Main button circle
        btn_r = 55
        fill_alpha = 0.15 if not is_hover else 0.3
        fr = int(r * fill_alpha)
        fg_ = int(g * fill_alpha)
        fb = int(b * fill_alpha)
        fill_color = f"#{max(fr,1):02x}{max(fg_,1):02x}{max(fb,1):02x}"

        border_alpha = 0.7 if not is_hover else 1.0
        br = int(min(255, r * border_alpha))
        bg_ = int(min(255, g * border_alpha))
        bb = int(min(255, b * border_alpha))
        border_color = f"#{br:02x}{bg_:02x}{bb:02x}"

        canvas.create_oval(
            cx - btn_r, cy - btn_r, cx + btn_r, cy + btn_r,
            fill=fill_color, outline=border_color, width=2
        )

        # Label text
        text_alpha = 0.8 if not is_hover else 1.0
        tr = int(min(255, r * text_alpha))
        tg = int(min(255, g * text_alpha))
        tb = int(min(255, b * text_alpha))
        text_color = f"#{max(tr,1):02x}{max(tg,1):02x}{max(tb,1):02x}"

        canvas.create_text(
            cx, cy,
            text=label,
            font=("Segoe UI", 20, "bold"),
            fill=text_color
        )

        # Subtitle
        sub_text = "Text Chat" if label == "FRIDAY" else "Voice Control"
        canvas.create_text(
            cx, cy + 80,
            text=sub_text,
            font=("Segoe UI Light", 11),
            fill="#555555"
        )

    def _animate_glow(self):
        self.glow_phase += 0.05
        glow = (math.sin(self.glow_phase) + 1) / 2  # 0..1

        # FRIDAY = cyan (0, 255, 255)
        self._draw_glowing_button(
            self.friday_canvas, "FRIDAY",
            (0, 255, 255), glow, self.friday_hover
        )

        # JARVIS = gold (255, 215, 0)
        self._draw_glowing_button(
            self.jarvis_canvas, "JARVIS",
            (255, 215, 0), glow, self.jarvis_hover
        )

        self.after(50, self._animate_glow)

    def launch_friday(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "friday.py")
        env = os.environ.copy()
        env['OPENBLAS_NUM_THREADS'] = '1'
        env['OMP_NUM_THREADS'] = '1'
        subprocess.Popen([sys.executable, script_path], env=env)

    def launch_jarvis(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis.py")
        env = os.environ.copy()
        env['OPENBLAS_NUM_THREADS'] = '1'
        env['OMP_NUM_THREADS'] = '1'
        subprocess.Popen([sys.executable, script_path], env=env)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = ModeSelector()
    app.mainloop()