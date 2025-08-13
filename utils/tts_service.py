import requests
import base64
import json
import os
import logging
import time
from typing import Optional, Tuple, Dict, Any
import tempfile
import wave

class TTSService:
    """Vbee AI Text-to-Speech service"""
    
    def __init__(self, api_key: str, api_url: str, 
                 voice_id: str = "hn_female_xuanmai_casual",
                 speed: float = 1.0, audio_format: str = "wav"):
        """
        Initialize TTS service with Vbee AI
        
        Args:
            api_key: Vbee AI API key
            api_url: Vbee API endpoint URL
            voice_id: Voice model ID
            speed: Speech speed (0.5-2.0)
            audio_format: Output audio format
        """
        self.api_key = api_key
        self.api_url = api_url
        self.voice_id = voice_id
        self.speed = speed
        self.audio_format = audio_format
        self.logger = logging.getLogger(__name__)
        
        # Request headers
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'IEC-ElderCare-Chatbot/1.0'
        }
    
    def text_to_speech(self, text: str, output_path: str = None) -> Tuple[str, Dict[str, Any], bool]:
        """
        Convert text to speech using Vbee AI
        
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
            
            # Prepare request payload
            payload = {
                "text": text,
                "voice_id": self.voice_id,
                "speed": self.speed,
                "format": self.audio_format,
                "sample_rate": 22050,
                "bit_rate": 128
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract audio data
                if 'audio_data' in response_data:
                    audio_data = base64.b64decode(response_data['audio_data'])
                elif 'data' in response_data:
                    audio_data = base64.b64decode(response_data['data'])
                else:
                    # Fallback: try to get binary data directly
                    audio_data = response.content
                
                # Save audio file
                if output_path is None:
                    output_path = self._generate_temp_filename()
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                # Get metadata
                metadata = self._extract_metadata(response_data, output_path, text)
                
                self.logger.info(f"TTS successful, saved to: {output_path}")
                return output_path, metadata, True
            
            else:
                self.logger.error(f"TTS API error: {response.status_code} - {response.text}")
                return "", {}, False
                
        except requests.RequestException as e:
            self.logger.error(f"TTS request error: {str(e)}")
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
            original_speed = self.speed
            self.speed = max(0.8, self.speed - 0.2)  # Slower for elderly
            
            # Generate speech
            result = self.text_to_speech(optimized_text, output_path)
            
            # Restore original speed
            self.speed = original_speed
            
            return result
            
        except Exception as e:
            self.logger.error(f"Elder TTS synthesis error: {str(e)}")
            return "", {}, False
    
    def _optimize_text_for_elderly(self, text: str) -> str:
        """
        Optimize text for better elderly comprehension
        
        Args:
            text: Original text
            
        Returns:
            Optimized text
        """
        # Add pauses for better comprehension
        optimized = text.replace('. ', '. ... ')
        optimized = optimized.replace('! ', '! ... ')
        optimized = optimized.replace('? ', '? ... ')
        
        # Add emphasis for important words
        important_words = ['cần', 'nên', 'quan trọng', 'chú ý', 'nhớ', 'khuyên']
        for word in important_words:
            optimized = optimized.replace(word, f'*{word}*')
        
        return optimized
    
    def _generate_temp_filename(self) -> str:
        """Generate temporary filename for audio file"""
        temp_dir = tempfile.gettempdir()
        filename = f"tts_output_{int(time.time())}_{os.getpid()}.{self.audio_format}"
        return os.path.join(temp_dir, filename)
    
    def _extract_metadata(self, response_data: dict, audio_path: str, original_text: str) -> Dict[str, Any]:
        """Extract metadata from TTS response"""
        metadata = {
            "voice_id": self.voice_id,
            "speed": self.speed,
            "format": self.audio_format,
            "character_count": len(original_text),
            "file_path": audio_path,
            "file_size": 0,
            "duration": 0.0
        }
        
        try:
            # Get file size
            if os.path.exists(audio_path):
                metadata["file_size"] = os.path.getsize(audio_path)
                
                # Get audio duration
                if self.audio_format.lower() == 'wav':
                    metadata["duration"] = self._get_wav_duration(audio_path)
            
            # Extract from API response
            if isinstance(response_data, dict):
                metadata.update({
                    "sample_rate": response_data.get("sample_rate", 22050),
                    "bit_rate": response_data.get("bit_rate", 128),
                    "channels": response_data.get("channels", 1)
                })
        
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
        Test Vbee API connection
        
        Returns:
            True if connection is successful
        """
        try:
            test_text = "Xin chào! Đây là test kết nối Vbee AI."
            
            # Test with a simple request
            payload = {
                "text": test_text,
                "voice_id": self.voice_id,
                "speed": 1.0,
                "format": "wav"
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Vbee AI connection test successful")
                return True
            else:
                self.logger.error(f"Vbee AI connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Vbee AI connection test failed: {e}")
            return False
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available Vietnamese voices"""
        return {
            'hn_female_xuanmai_casual': 'Nữ Hà Nội - Xuân Mai (Thân thiện)',
            'hn_male_manhdung_casual': 'Nam Hà Nội - Mạnh Dũng (Thân thiện)',
            'hcm_female_thuminh_casual': 'Nữ TP.HCM - Thu Minh (Thân thiện)',
            'hcm_male_ngoclam_casual': 'Nam TP.HCM - Ngọc Lâm (Thân thiện)',
            'hn_female_maiphuong_news': 'Nữ Hà Nội - Mai Phương (Tin tức)',
            'hn_male_anhduy_news': 'Nam Hà Nội - Anh Duy (Tin tức)',
            'hn_female_diemmy_reading': 'Nữ Hà Nội - Diễm My (Đọc sách)',
            'hcm_male_hoanglong_reading': 'Nam TP.HCM - Hoàng Long (Đọc sách)'
        }
    
    def change_voice(self, voice_id: str):
        """
        Change voice model
        
        Args:
            voice_id: New voice ID to use
        """
        if voice_id in self.get_available_voices():
            self.voice_id = voice_id
            self.logger.info(f"Voice changed to: {voice_id}")
        else:
            self.logger.error(f"Invalid voice ID: {voice_id}")
    
    def set_speed(self, speed: float):
        """
        Set speech speed
        
        Args:
            speed: Speech speed (0.5-2.0)
        """
        if 0.5 <= speed <= 2.0:
            self.speed = speed
            self.logger.info(f"Speech speed set to: {speed}")
        else:
            self.logger.error(f"Invalid speed value: {speed} (must be 0.5-2.0)")
    
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
        adjusted_rate = base_rate * self.speed
        
        # Estimate word count (Vietnamese: ~5 characters per word)
        word_count = len(text) / 5
        
        # Calculate duration in seconds
        duration = (word_count / adjusted_rate) * 60
        
        return max(duration, 1.0)  # Minimum 1 second
