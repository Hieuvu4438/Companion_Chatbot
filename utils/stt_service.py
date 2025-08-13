import azure.cognitiveservices.speech as speechsdk
import pyaudio
import wave
import tempfile
import os
import logging
from typing import Optional, Tuple
import time

class STTService:
    """Azure Speech Services for Speech-to-Text conversion"""
    
    def __init__(self, subscription_key: str, region: str, language: str = "vi-VN"):
        """
        Initialize STT service with Azure credentials
        
        Args:
            subscription_key: Azure Speech Services API key
            region: Azure region (e.g., 'southeastasia')
            language: Speech recognition language (default: Vietnamese)
        """
        self.subscription_key = subscription_key
        self.region = region
        self.language = language
        self.logger = logging.getLogger(__name__)
        
        # Initialize speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        self.speech_config.speech_recognition_language = language
        
        # Audio configuration
        self.audio_config = None
        
    def recognize_from_microphone(self, duration: int = 5) -> Tuple[str, float, bool]:
        """
        Record audio from microphone and convert to text
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Tuple of (recognized_text, confidence_score, success)
        """
        try:
            self.logger.info(f"Starting microphone recording for {duration} seconds...")
            
            # Create audio config for microphone
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            print(f"🎤 Bắt đầu ghi âm trong {duration} giây... Hãy nói!")
            
            # Start recognition
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                confidence = self._get_confidence_score(result)
                self.logger.info(f"Recognition successful: {result.text}")
                return result.text, confidence, True
                
            elif result.reason == speechsdk.ResultReason.NoMatch:
                self.logger.warning("No speech could be recognized")
                return "", 0.0, False
                
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                self.logger.error(f"Speech Recognition canceled: {cancellation_details.reason}")
                if cancellation_details.error_details:
                    self.logger.error(f"Error details: {cancellation_details.error_details}")
                return "", 0.0, False
                
        except Exception as e:
            self.logger.error(f"Error in microphone recognition: {str(e)}")
            return "", 0.0, False
    
    def recognize_from_file(self, audio_file_path: str) -> Tuple[str, float, bool]:
        """
        Convert audio file to text
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Tuple of (recognized_text, confidence_score, success)
        """
        try:
            if not os.path.exists(audio_file_path):
                self.logger.error(f"Audio file not found: {audio_file_path}")
                return "", 0.0, False
            
            self.logger.info(f"Processing audio file: {audio_file_path}")
            
            # Create audio config for file
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Start recognition
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                confidence = self._get_confidence_score(result)
                self.logger.info(f"File recognition successful: {result.text}")
                return result.text, confidence, True
                
            elif result.reason == speechsdk.ResultReason.NoMatch:
                self.logger.warning("No speech could be recognized from file")
                return "", 0.0, False
                
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                self.logger.error(f"File Speech Recognition canceled: {cancellation_details.reason}")
                if cancellation_details.error_details:
                    self.logger.error(f"Error details: {cancellation_details.error_details}")
                return "", 0.0, False
                
        except Exception as e:
            self.logger.error(f"Error in file recognition: {str(e)}")
            return "", 0.0, False
    
    def record_audio_to_file(self, output_path: str, duration: int = 5, 
                           sample_rate: int = 16000, channels: int = 1) -> Tuple[str, float, bool]:
        """
        Record audio from microphone and save to file
        
        Args:
            output_path: Path to save audio file
            duration: Recording duration in seconds
            sample_rate: Audio sample rate
            channels: Number of audio channels
            
        Returns:
            Tuple of (file_path, audio_duration, success)
        """
        try:
            self.logger.info(f"Recording audio to {output_path} for {duration} seconds")
            
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            # Audio configuration
            chunk = 1024
            format = pyaudio.paInt16
            
            # Open stream
            stream = audio.open(
                format=format,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            print(f"🎤 Đang ghi âm... ({duration} giây)")
            
            frames = []
            for i in range(0, int(sample_rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)
            
            print("✅ Hoàn thành ghi âm!")
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save to WAV file
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(audio.get_sample_size(format))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
            
            self.logger.info(f"Audio saved to {output_path}")
            return output_path, duration, True
            
        except Exception as e:
            self.logger.error(f"Error recording audio: {str(e)}")
            return "", 0.0, False
    
    def _get_confidence_score(self, result) -> float:
        """
        Extract confidence score from recognition result
        
        Args:
            result: Azure speech recognition result
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            # Try to get confidence from detailed results
            if hasattr(result, 'properties'):
                confidence_str = result.properties.get(
                    speechsdk.PropertyId.SpeechServiceResponse_JsonResult
                )
                if confidence_str:
                    import json
                    json_result = json.loads(confidence_str)
                    if 'NBest' in json_result and len(json_result['NBest']) > 0:
                        return json_result['NBest'][0].get('Confidence', 0.8)
            
            # Default confidence score if not available
            return 0.8
            
        except Exception as e:
            self.logger.warning(f"Could not extract confidence score: {e}")
            return 0.8
    
    def test_connection(self) -> bool:
        """
        Test Azure Speech Services connection
        
        Returns:
            True if connection is successful
        """
        try:
            # Create a simple test recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config
            )
            self.logger.info("Azure Speech Services connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Azure Speech Services connection test failed: {e}")
            return False
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            "vi-VN",  # Vietnamese
            "en-US",  # English (US)
            "en-GB",  # English (UK)
            "ja-JP",  # Japanese
            "ko-KR",  # Korean
            "zh-CN",  # Chinese (Mandarin)
            "th-TH",  # Thai
        ]
    
    def change_language(self, language: str):
        """
        Change recognition language
        
        Args:
            language: Language code (e.g., 'vi-VN', 'en-US')
        """
        self.language = language
        self.speech_config.speech_recognition_language = language
        self.logger.info(f"Language changed to: {language}")
    
    def get_audio_duration(self, audio_file_path: str) -> float:
        """
        Get duration of audio file
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Audio duration in seconds
        """
        try:
            with wave.open(audio_file_path, 'rb') as wf:
                frames = wf.getnframes()
                sample_rate = wf.getframerate()
                duration = frames / float(sample_rate)
                return duration
        except Exception as e:
            self.logger.error(f"Error getting audio duration: {e}")
            return 0.0
