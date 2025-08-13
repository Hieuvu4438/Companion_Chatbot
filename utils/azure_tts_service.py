import azure.cognitiveservices.speech as speechsdk
import os
import logging
import time
from typing import Optional, Tuple, Dict, Any
import tempfile
import wave

class AzureTTSService:
    """Azure Speech Services for Text-to-Speech conversion"""
    
    def __init__(self, subscription_key: str, region: str, voice_name: str = "vi-VN-HoaiMyNeural",
                 speech_rate: float = 0.8, pitch: int = 0, volume: int = 100):
        """
        Initialize Azure TTS service
        
        Args:
            subscription_key: Azure Speech Services API key
            region: Azure region (e.g., 'southeastasia')
            voice_name: Azure neural voice name
            speech_rate: Speech speed (0.5-2.0)
            pitch: Pitch adjustment in Hz
            volume: Volume level (0-100)
        """
        self.subscription_key = subscription_key
        self.region = region
        self.voice_name = voice_name
        self.speech_rate = speech_rate
        self.pitch = pitch
        self.volume = volume
        self.logger = logging.getLogger(__name__)
        
        # Initialize speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        
        # Set voice and output format
        self.speech_config.speech_synthesis_voice_name = voice_name
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        )
        
    def text_to_speech(self, text: str, output_path: str = None) -> Tuple[str, Dict[str, Any], bool]:
        """
        Convert text to speech using Azure TTS
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file (optional)
            
        Returns:
            Tuple of (audio_file_path, metadata, success)
        """
        try:
            if not text.strip():
                self.logger.error("Empty text provided for TTS")
                return "", {}, False
            
            self.logger.info(f"Converting text to speech: {text[:50]}...")
            
            # Generate output path if not provided
            if output_path is None:
                output_path = self._generate_temp_filename()
            
            # Create audio config for file output
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
            
            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Create SSML for better control
            ssml_text = self._create_ssml(text)
            
            # Synthesize speech
            result = speech_synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Get metadata
                metadata = self._extract_metadata(result, output_path, text)
                
                self.logger.info(f"TTS successful, saved to: {output_path}")
                return output_path, metadata, True
                
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                self.logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.error_details:
                    self.logger.error(f"Error details: {cancellation_details.error_details}")
                return "", {}, False
                
        except Exception as e:
            self.logger.error(f"TTS error: {str(e)}")
            return "", {}, False
    
    def text_to_speech_stream(self, text: str) -> Tuple[bytes, Dict[str, Any], bool]:
        """
        Convert text to speech and return audio data as bytes
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Tuple of (audio_bytes, metadata, success)
        """
        try:
            # Use temporary file approach
            temp_file, metadata, success = self.text_to_speech(text)
            
            if success and os.path.exists(temp_file):
                with open(temp_file, 'rb') as f:
                    audio_bytes = f.read()
                
                # Clean up temp file
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                return audio_bytes, metadata, True
            
            return b'', {}, False
            
        except Exception as e:
            self.logger.error(f"TTS stream error: {str(e)}")
            return b'', {}, False
    
    def synthesize_elder_response(self, response_text: str, output_path: str = None) -> Tuple[str, Dict[str, Any], bool]:
        """
        Synthesize speech optimized for elderly listening
        
        Args:
            response_text: AI response text to synthesize
            output_path: Path to save audio file
            
        Returns:
            Tuple of (audio_file_path, metadata, success)
        """
        try:
            # Optimize text for elderly comprehension
            optimized_text = self._optimize_text_for_elderly(response_text)
            
            # Use slower speed for better comprehension
            original_rate = self.speech_rate
            self.speech_rate = max(0.6, self.speech_rate - 0.2)  # Slower for elderly
            
            # Generate speech
            result = self.text_to_speech(optimized_text, output_path)
            
            # Restore original speed
            self.speech_rate = original_rate
            
            return result
            
        except Exception as e:
            self.logger.error(f"Elder TTS synthesis error: {str(e)}")
            return "", {}, False
    
    def _create_ssml(self, text: str) -> str:
        """
        Create SSML (Speech Synthesis Markup Language) for better control
        
        Args:
            text: Plain text to convert to SSML
            
        Returns:
            SSML formatted text
        """
        # Create SSML with prosody control
        ssml = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="vi-VN">
            <voice name="{self.voice_name}">
                <prosody rate="{self.speech_rate}" pitch="{self.pitch:+d}Hz" volume="{self.volume}">
                    {self._escape_ssml_text(text)}
                </prosody>
            </voice>
        </speak>
        '''
        
        return ssml.strip()
    
    def _escape_ssml_text(self, text: str) -> str:
        """Escape special characters for SSML"""
        # Replace special characters that might interfere with SSML
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        return text
    
    def _optimize_text_for_elderly(self, text: str) -> str:
        """
        Optimize text for better elderly comprehension
        
        Args:
            text: Original text
            
        Returns:
            Optimized text
        """
        # Add pauses for better comprehension
        optimized = text.replace('. ', '.<break time="500ms"/> ')
        optimized = optimized.replace('! ', '!<break time="500ms"/> ')
        optimized = optimized.replace('? ', '?<break time="500ms"/> ')
        optimized = optimized.replace(', ', ',<break time="200ms"/> ')
        
        # Add emphasis for important words
        important_words = ['cần', 'nên', 'quan trọng', 'chú ý', 'nhớ', 'khuyên']
        for word in important_words:
            optimized = optimized.replace(word, f'<emphasis level="moderate">{word}</emphasis>')
        
        return optimized
    
    def _generate_temp_filename(self) -> str:
        """Generate temporary filename for audio file"""
        temp_dir = tempfile.gettempdir()
        filename = f"azure_tts_output_{int(time.time())}_{os.getpid()}.wav"
        return os.path.join(temp_dir, filename)
    
    def _extract_metadata(self, result, audio_path: str, original_text: str) -> Dict[str, Any]:
        """Extract metadata from TTS result"""
        metadata = {
            "voice_name": self.voice_name,
            "speech_rate": self.speech_rate,
            "pitch": self.pitch,
            "volume": self.volume,
            "format": "wav",
            "character_count": len(original_text),
            "file_path": audio_path,
            "file_size": 0,
            "duration": 0.0
        }
        
        try:
            # Get file size and duration
            if os.path.exists(audio_path):
                metadata["file_size"] = os.path.getsize(audio_path)
                metadata["duration"] = self._get_wav_duration(audio_path)
            
            # Extract from result if available
            if hasattr(result, 'audio_duration'):
                metadata["result_duration"] = result.audio_duration.total_seconds()
        
        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {e}")
        
        return metadata
    
    def _get_wav_duration(self, wav_path: str) -> float:
        """Get duration of WAV file"""
        try:
            with wave.open(wav_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                return duration
        except Exception as e:
            self.logger.warning(f"Error getting WAV duration: {e}")
            return 0.0
    
    def test_connection(self) -> bool:
        """
        Test Azure TTS connection
        
        Returns:
            True if connection is successful
        """
        try:
            test_text = "Xin chào! Đây là test kết nối Azure TTS."
            
            # Create synthesizer for test
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )
            
            # Test synthesis (without saving to file)
            result = speech_synthesizer.speak_text_async(test_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.logger.info("Azure TTS connection test successful")
                return True
            else:
                self.logger.error(f"Azure TTS connection test failed: {result.reason}")
                return False
                
        except Exception as e:
            self.logger.error(f"Azure TTS connection test failed: {e}")
            return False
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available Vietnamese voices"""
        return {
            'vi-VN-HoaiMyNeural': 'Nữ - Hoài My (Thân thiện, phù hợp người cao tuổi)',
            'vi-VN-NamMinhNeural': 'Nam - Nam Minh (Rõ ràng, chuyên nghiệp)'
        }
    
    def change_voice(self, voice_name: str):
        """
        Change voice model
        
        Args:
            voice_name: New voice name to use
        """
        available_voices = self.get_available_voices()
        if voice_name in available_voices:
            self.voice_name = voice_name
            self.speech_config.speech_synthesis_voice_name = voice_name
            self.logger.info(f"Voice changed to: {voice_name}")
        else:
            self.logger.error(f"Invalid voice name: {voice_name}")
    
    def set_speech_rate(self, rate: float):
        """
        Set speech rate
        
        Args:
            rate: Speech rate (0.5-2.0)
        """
        if 0.5 <= rate <= 2.0:
            self.speech_rate = rate
            self.logger.info(f"Speech rate set to: {rate}")
        else:
            self.logger.error(f"Invalid speech rate: {rate} (must be 0.5-2.0)")
    
    def set_pitch(self, pitch: int):
        """
        Set speech pitch
        
        Args:
            pitch: Pitch adjustment in Hz (-200 to +200)
        """
        if -200 <= pitch <= 200:
            self.pitch = pitch
            self.logger.info(f"Speech pitch set to: {pitch}Hz")
        else:
            self.logger.error(f"Invalid pitch: {pitch} (must be -200 to +200)")
    
    def set_volume(self, volume: int):
        """
        Set speech volume
        
        Args:
            volume: Volume level (0-100)
        """
        if 0 <= volume <= 100:
            self.volume = volume
            self.logger.info(f"Speech volume set to: {volume}")
        else:
            self.logger.error(f"Invalid volume: {volume} (must be 0-100)")
    
    def play_audio_file(self, audio_path: str) -> bool:
        """
        Play audio file (Windows implementation)
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if playback started successfully
        """
        try:
            import winsound
            
            if os.path.exists(audio_path):
                winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                self.logger.info(f"Playing audio: {audio_path}")
                return True
            else:
                self.logger.error(f"Audio file not found: {audio_path}")
                return False
                
        except ImportError:
            self.logger.warning("winsound not available - cannot play audio")
            return False
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            return False
    
    def estimate_speech_duration(self, text: str) -> float:
        """
        Estimate speech duration based on text length
        
        Args:
            text: Text to estimate duration for
            
        Returns:
            Estimated duration in seconds
        """
        # Average Vietnamese speech rate: ~150-200 words per minute
        # Adjust for speed setting
        base_rate = 180  # words per minute
        adjusted_rate = base_rate * self.speech_rate
        
        # Estimate word count (Vietnamese: ~5 characters per word)
        word_count = len(text) / 5
        
        # Calculate duration in seconds
        duration = (word_count / adjusted_rate) * 60
        
        return max(duration, 1.0)  # Minimum 1 second
