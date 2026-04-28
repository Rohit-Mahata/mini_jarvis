import customtkinter as ctk
import pandas as pd
import os
import threading
from PIL import Image
from brain import UnifiedBrain
from trainer import Trainer
from voice import VoiceEngine
from commands import CommandExecutor

class FridayTypingIndicator(ctk.CTkProgressBar):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, 
            mode="indeterminate", 
            width=200, 
            height=3, 
            progress_color="#00FFFF", 
            **kwargs
        )
        self.set(0)

    def start_pulse(self):
        # Changed from grid() to pack()
        self.pack(pady=5, anchor="w", padx=20)
        self.start()

    def stop_pulse(self):
        self.stop()
        # Changed from grid_forget() to pack_forget()
        self.pack_forget()
class JarvisVisualizer(ctk.CTkLabel):
    def __init__(self, master, gif_path, **kwargs):
        super().__init__(master, text="", **kwargs)
        self.gif_path = gif_path
        self.frames = []
        self.current_frame = 0
        self.load_frames()
        self.animate()
        
    def load_frames(self):
        try:
            img = Image.open(self.gif_path)
            while True:
                frame = ctk.CTkImage(img.copy(), size=(300, 300))
                self.frames.append(frame)
                img.seek(len(self.frames))
        except EOFError:
            pass
        except FileNotFoundError:
            self.configure(text="[Jarvis Visualizer Missing]")
            
    def animate(self):
        if self.frames:
            self.configure(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.after(50, self.animate)

class AssistantUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Assistant")
        self.geometry("800x600")
        self.configure(fg_color="#121212")

        self.voice_engine = VoiceEngine()
        self.commander = CommandExecutor(self.voice_engine)
        self.brain = UnifiedBrain()
        self.trainer = Trainer(self.brain)
        
        self.base_data_frames = []
        self.load_initial_data()

        self.top_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self.top_frame.pack(fill="x", pady=10, padx=20)

        self.train_button = ctk.CTkButton(
            self.top_frame,
            text="Train Brain",
            width=100,
            command=self.open_train_mode,
            fg_color="#333333",
            hover_color="#555555"
        )
        self.train_button.pack(side="left")

        self.mode_switch = ctk.CTkSwitch(
            self.top_frame,
            text="FRIDAY",
            command=self.toggle_mode,
            progress_color="#00FFFF",
            button_color="#1f538d",
            button_hover_color="#14375e"
        )
        self.mode_switch.pack(side="right")

        self.friday_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.friday_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.chat_display = ctk.CTkTextbox(self.friday_frame, state="disabled", fg_color="#1e1e1e", text_color="white")
        self.chat_display.pack(fill="both", expand=True, pady=(0, 10))

        self.typing_indicator = FridayTypingIndicator(self.friday_frame)

        self.input_frame = ctk.CTkFrame(self.friday_frame, fg_color="transparent")
        self.input_frame.pack(fill="x")

        self.text_input = ctk.CTkEntry(self.input_frame, placeholder_text="Ask Friday...", fg_color="#1e1e1e", border_color="#333333")
        self.text_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.text_input.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.send_message, fg_color="#00FFFF", text_color="black")
        self.send_button.pack(side="right")

        self.jarvis_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.jarvis_visualizer = JarvisVisualizer(self.jarvis_frame, gif_path="jarvis_loop.gif")
        self.jarvis_visualizer.pack(expand=True)
        
        self.jarvis_listening = False

    def load_initial_data(self):
        files = ['data/science.csv', 'data/math.csv', 'data/general.csv']
        for file in files:
            if os.path.exists(file):
                self.base_data_frames.append(pd.read_csv(file))
        
        if os.path.exists('data/learned_knowledge.csv'):
            self.base_data_frames.append(pd.read_csv('data/learned_knowledge.csv'))
            
        if self.base_data_frames:
            self.brain.load_and_train(self.base_data_frames)

    def toggle_mode(self):
        if self.mode_switch.get() == 1:
            self.mode_switch.configure(text="JARVIS", progress_color="#FF4500")
            self.friday_frame.pack_forget()
            self.jarvis_frame.pack(fill="both", expand=True, padx=20, pady=10)
            self.jarvis_listening = True
            threading.Thread(target=self.jarvis_listen_loop, daemon=True).start()
        else:
            self.mode_switch.configure(text="FRIDAY", progress_color="#00FFFF")
            self.jarvis_frame.pack_forget()
            self.friday_frame.pack(fill="both", expand=True, padx=20, pady=10)
            self.jarvis_listening = False

    def jarvis_listen_loop(self):
        while self.jarvis_listening:
            command = self.voice_engine.listen()
            if command:
                if "open" in command or "shutdown" in command or "restart" in command:
                    self.commander.execute(command)
                else:
                    answer = self.brain.get_answer(command)
                    if answer:
                        self.voice_engine.speak(answer)
                    else:
                        self.voice_engine.speak("I don't have that information. Please train me.")

    def open_train_mode(self):
        train_window = ctk.CTkToplevel(self)
        train_window.title("Train Brain")
        train_window.geometry("400x350")
        train_window.attributes('-topmost', True)
        
        ctk.CTkLabel(train_window, text="Category:").pack(pady=(10, 0))
        category_entry = ctk.CTkEntry(train_window, width=300)
        category_entry.pack(pady=5)
        
        ctk.CTkLabel(train_window, text="Question:").pack(pady=(10, 0))
        question_entry = ctk.CTkEntry(train_window, width=300)
        question_entry.pack(pady=5)
        
        ctk.CTkLabel(train_window, text="Answer:").pack(pady=(10, 0))
        answer_entry = ctk.CTkEntry(train_window, width=300)
        answer_entry.pack(pady=5)
        
        def save_knowledge():
            cat = category_entry.get()
            q = question_entry.get()
            a = answer_entry.get()
            if cat and q and a:
                self.trainer.add_knowledge(cat, q, a, self.base_data_frames)
                train_window.destroy()
                
        ctk.CTkButton(train_window, text="Save", command=save_knowledge).pack(pady=20)

    def send_message(self, event=None):
        user_text = self.text_input.get()
        if not user_text:
            return

        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"You: {user_text}\n\n")
        self.chat_display.configure(state="disabled")
        self.text_input.delete(0, "end")

        self.typing_indicator.start_pulse()
        
        threading.Thread(target=self.process_friday_response, args=(user_text,), daemon=True).start()

    def process_friday_response(self, text):
        answer = self.brain.get_answer(text)
        self.after(500, self.display_friday_response, answer)

    def display_friday_response(self, answer):
        self.typing_indicator.stop_pulse()
        self.chat_display.configure(state="normal")
        if answer:
            self.chat_display.insert("end", f"Friday: {answer}\n\n")
        else:
            self.chat_display.insert("end", "Friday: I don't know that yet. Please use the Train Brain button.\n\n")
        self.chat_display.configure(state="disabled")

if __name__ == "__main__":
    app = AssistantUI()
    app.mainloop()