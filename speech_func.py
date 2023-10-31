import speech_recognition as sr
import time
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk
import requests
import pygame
import threading 
import openai
import torch
import noisereduce as nr
import wave
from sounds import play_sound
import numpy as np
import base64
from gtts import gTTS
import os



# Set up Azure Speech-to-Text and Text-to-Speech credentials
speech_key = "71b49f1e9a8f444e80a1a74d9b87b79c"
recognized_text = "" 
service_region = "eastus"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_language = "en-NZ"

# Set up the voice configuration
speech_config.speech_synthesis_voice_name = "en-NZ-MollyNeural"
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

silence_limit = 3  # Silence limit in seconds  
timer = None  

class Speech:
    
    
    @staticmethod
    def transcribe_audio():
        recognizer = sr.Recognizer()
        mic = sr.Microphone() 
        recognizer.dynamic_energy_threshold = False
        recognizer.energy_threshold = 400
        recognizer.pause_threshold = 3

        with mic as source:
            print(" Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            audio = recognizer.listen(source)


        try:
            input_text = recognizer.recognize_google(audio, language="en-in")
            # input_text = recognizer.recognize_whisper_api(audio, api_key="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")
            return input_text.strip()
        except sr.UnknownValueError:
            return ""


    @staticmethod
    def text_to_speech_elevanlabs(text):
        CHUNK_SIZE = 1024

        emily = "LcfcDJNUP1GQjkzn1xUU"
        bella = "EXAVITQu4vr4xnSDxMaL"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{bella}/stream"

        headers = {
            "xi-api-key": "e77937045ed320adc9e6540a4d3600e1",
        }

        data = {
            "text": text,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        response = requests.post(url, json=data, headers=headers)

        output_filename = "reply.mp3"
        with open(output_filename, "wb") as output:
            output.write(response.content)

        # output_filename="output.wav"

        # # Decode the audio content from base64
        # audio_content = np.frombuffer(base64.b64decode(response), dtype=np.int16)

        # # Open the WAV file in write mode
        # with open(output_filename, 'wb') as wav_file:
        #     # Set the parameters
        #     sample_width = 2  # 16-bit audio
        #     sample_rate = 44100  # Replace with the appropriate sample rate
        #     num_channels = 1  # Mono audio

        #     wav_file.setparams((num_channels, sample_width, sample_rate, 0, 'NONE', 'not compressed'))

        #     # Write the audio data
        #     wav_file.writeframes(audio_content.tobytes())

        # Initialize pygame mixer
        pygame.mixer.init()
        try:
            # Load the audio file
            pygame.mixer.music.load(output_filename)

            # Play the audio
            pygame.mixer.music.play()

            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        except pygame.error as e:
            print("Error loading MP3 file:", str(e))

        finally:
            # Clean up and remove the temporary audio file
            pygame.mixer.quit()
            os.remove(output_filename)

    # Define the speech-to-text function
    @staticmethod
    def speech_to_text_azure():

        # Set up the audio configuration
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

        # Create a speech recognizer and start the recognition
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # # Set the end silence timeout to 5 seconds
        # property_bag = speechsdk.PropertyCollection(handle=speech_recognizer.properties)
        # property_bag.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "3000")
        # property_bag.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,"3000")

        print("Say something...")

        # speech_recognizer.properties = property_bag



        result = speech_recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "Sorry, I didn't catch that."
        elif result.reason == speechsdk.ResultReason.Canceled:
            return "Recognition canceled."
    
    # Define the text-to-speech function
    @staticmethod
    def text_to_speech_azure(text):
        try:
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("Text-to-speech conversion successful.")
                return True
            else:
                print(f"Error synthesizing audio: {result}")
                return False
        except Exception as ex:
            print(f"Error synthesizing audio: {ex}")
            return False

    @staticmethod
    def synthesize_and_play_speech(response_text):
        # Convert text to speech
        tts = gTTS(text=response_text, lang="en")
        tts.save("response.mp3")

        # Initialize pygame mixer
        pygame.mixer.init()

        try:
            # Load the audio file
            pygame.mixer.music.load("response.mp3")

            # Play the audio
            pygame.mixer.music.play()

            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        finally:
            # Clean up and remove the temporary audio file
            pygame.mixer.quit()
            os.remove("response.mp3")


  
    @staticmethod    
    def recognition():  
        global speech_recognizer  
        # Set up the audio configuration  
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)  
    
        # Create a speech recognizer and start the recognition    
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)         
    
        # Register the callbacks          
        speech_recognizer.recognizing.connect(Speech.handle_recognizing)    
        speech_recognizer.canceled.connect(Speech.handle_canceled)    
        speech_recognizer.session_stopped.connect(Speech.handle_session_stopped)  # Register the session_stopped event      
    
        # Start continuous recognition          
        speech_recognizer.start_continuous_recognition()      
    
        while True:          
            time.sleep(0.1)      
    
    @staticmethod    
    def handle_recognizing(evt):        
        global recognized_text  
        print("Recognized: ", evt.result.text)      
        recognized_text += " " + evt.result.text  
    
    @staticmethod    
    def handle_canceled(evt):        
        print("Canceled: ", evt.result.text)      
    
    @staticmethod    
    def handle_session_stopped(evt):     
        global speech_recognizer     
        print("Session stopped, the user has paused for a few seconds.")
        speech_recognizer.stop_continuous_recognition()     
        time.sleep(3)  # Wait for 3 more seconds to see if the user resumes speaking  
        if speech_recognizer is not None:    
            speech_recognizer.start_continuous_recognition()

    @staticmethod
    def whisper(audio):
        with open("speech.wav", "wb") as f:
            f.write(audio.get_wav_data())
        speech = open("speech.wav", "rb")
        wcompletion = openai.Audio.transcribe(model="whisper-1", file=speech)
        print(wcompletion)
        user_input = wcompletion["text"]
        print(user_input)
        return user_input

# @staticmethod
    # def transcribe_audio():
    #     recognizer = sr.Recognizer()
    #     mic = sr.Microphone(sample_rate=16000)  # Set the audio sampling rate to 16 kHz
    #     recognizer.dynamic_energy_threshold = False
    #     recognizer.energy_threshold = 200

    #     with mic as source:
    #         print(" Listening...")
    #         recognizer.adjust_for_ambient_noise(source, duration=1.0)
    #         audio = recognizer.listen(source,)

    #     # # Apply noise reduction using noisereduce
    #     # # audio_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
    #     # # Extract raw audio data from the audio object
    #     # audio_data = audio.frame_data

    #     # # Apply noise reduction using noisereduce
    #     # reduced_audio = nr.reduce_noise(y=audio_data, sr=16000)

    #     try:
    #         # Use the improved audio data for transcription
    #         # input_text = recognizer.recognize_google(audio, language="en-in")
    #         input_text = recognizer.recognize_whisper_api(audio, api_key="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")
    #         return input_text.strip()
    #     except sr.UnknownValueError:
    #         return ""