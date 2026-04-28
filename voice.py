import pyttsx3
import speech_recognition as sr

class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "david" in voice.name.lower() or "male" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
                
        self.engine.setProperty('rate', 155)
        self.engine.setProperty('volume', 1.0)
        
        self.recognizer = sr.Recognizer()

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def acknowledge_command(self):
        self.speak("Roger that, sir.")

    def listen(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source)
            
        try:
            text = self.recognizer.recognize_google(audio)
            return text.lower()
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None