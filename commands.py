import os
import subprocess
import webbrowser

class CommandExecutor:
    def __init__(self, voice_engine):
        self.voice = voice_engine

    def execute(self, command_text):
        self.voice.acknowledge_command()

        if "open browser" in command_text or "open google" in command_text:
            webbrowser.open("https://www.google.com")
            
        elif "open youtube" in command_text:
            webbrowser.open("https://www.youtube.com")

        elif "open notepad" in command_text:
            subprocess.Popen(["notepad.exe"])
            
        elif "open calculator" in command_text:
            subprocess.Popen(["calc.exe"])
            
        elif "open paint" in command_text:
            subprocess.Popen(["mspaint.exe"])
            
        elif "open command prompt" in command_text or "open cmd" in command_text:
            os.system("start cmd")
            
        elif "open file explorer" in command_text or "open folder" in command_text:
            subprocess.Popen(["explorer.exe"])
            
        elif "open settings" in command_text:
            os.system("start ms-settings:")
            
        elif "open task manager" in command_text:
            subprocess.Popen(["taskmgr.exe"])
            
        elif "shutdown system" in command_text:
            os.system("shutdown /s /t 5")
            
        elif "restart system" in command_text:
            os.system("shutdown /r /t 5")
            
        else:
            self.voice.speak("System command not recognized.")