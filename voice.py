import pyttsx3
import speech_recognition as sr

class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        
        # Set male voice (David)
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "david" in voice.name.lower() or "male" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
                
        self.engine.setProperty('rate', 155)
        self.engine.setProperty('volume', 1.0)
        
        self.recognizer = sr.Recognizer()
        self.is_speaking = False

    def speak(self, text):
        """Speak text with state tracking for UI animations."""
        self.is_speaking = True
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        finally:
            self.is_speaking = False

    def acknowledge_command(self):
        self.speak("Roger that, sir.")

    def listen(self):
        """Listen for speech and return recognized text."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
                
            text = self.recognizer.recognize_google(audio)
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None
        except Exception:
            return None

    def listen_for_wake_word(self):
        """Continuously listen for 'hey jarvis' or 'jarvis' wake word.
        Returns True when wake word is detected."""
        while True:
            text = self.listen()
            if text and ("hey jarvis" in text or "jarvis" in text):
                return True