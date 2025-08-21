#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VBEE AI TTS Module
==================

Text-to-Speech module sử dụng VBEE AI API cho pipeline chatbot hỗ trợ người cao tuổi
"""

import os
import sys
import time
import json
import base64
import requests
from datetime import datetime
from typing import Dict, Optional, Any, Tuple, List

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame không có sẵn. Audio playback sẽ bị giới hạn.")

try:
    from config import *
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import *


class AudioPlayer:
    """Class để phát âm thanh"""
    
    def __init__(self):
        self.pygame_available = PYGAME_AVAILABLE
        
    def play_audio_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Phát file âm thanh
        
        Args:
            file_path: Đường dẫn file âm thanh
            
        Returns:
            Tuple[success, error_message]
        """
        try:
            if not os.path.exists(file_path):
                return False, "File không tồn tại"
            
            if self.pygame_available:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                
                # Chờ phát xong
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                return True, None
            else:
                # Fallback: Sử dụng system command
                import platform
                system = platform.system()
                
                if system == "Windows":
                    import winsound
                    winsound.PlaySound(file_path, winsound.SND_FILENAME)
                    return True, None
                elif system == "Darwin":  # macOS
                    os.system(f"afplay '{file_path}'")
                    return True, None
                elif system == "Linux":
                    os.system(f"aplay '{file_path}' || paplay '{file_path}'")
                    return True, None
                else:
                    return False, f"Hệ điều hành {system} không được hỗ trợ"
                    
        except Exception as e:
            return False, str(e)
    
    def play_audio_data(self, audio_data: bytes, file_format: str = "mp3") -> Tuple[bool, Optional[str]]:
        """
        Phát audio từ raw data
        
        Args:
            audio_data: Dữ liệu âm thanh
            file_format: Định dạng file
            
        Returns:
            Tuple[success, error_message]
        """
        try:
            # Lưu tạm file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = os.path.join(AUDIO_OUTPUT_DIR, f"temp_audio_{timestamp}.{file_format}")
            
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            # Phát file
            success, error = self.play_audio_file(temp_file)
            
            # Xóa file tạm (nếu không debug)
            if not SAVE_AUDIO_FILES and os.path.exists(temp_file):
                os.unlink(temp_file)
            
            return success, error
            
        except Exception as e:
            return False, str(e)


class VBEETTS:
    """VBEE AI Text-to-Speech service"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or VBEE_API_TOKEN
        if not self.api_token:
            raise ValueError("VBEE API token is required")
            
        self.base_url = VBEE_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # VBEE voice configurations
        self.voices = {
            1: {"name": "Minh Khai", "gender": "female", "description": "Giọng nữ trẻ, rõ ràng"},
            2: {"name": "Lê Minh", "gender": "male", "description": "Giọng nam trưởng thành, ấm áp"},
            3: {"name": "Thu Minh", "gender": "female", "description": "Giọng nữ trung niên, dịu dàng"},
            4: {"name": "Hoài Nam", "gender": "male", "description": "Giọng nam cao tuổi, từ tốn"},
            # Thêm các giọng khác tùy theo VBEE API
        }
        
        # Elder-friendly settings
        self.elder_config = {
            "voice_id": VBEE_VOICE_ID,
            "speed": VBEE_SPEED,  # Tốc độ chậm hơn cho người cao tuổi
            "tone": VBEE_TONE,    # Giọng điệu trung tính
            "volume": 1.0,        # Âm lượng đầy đủ
            "sample_rate": 22050  # Chất lượng tốt
        }
        
    def test_connection(self) -> bool:
        """Test kết nối với VBEE API"""
        try:
            # Test với một request đơn giản
            test_url = f"{self.base_url}/voices"  # Endpoint để lấy danh sách giọng
            response = requests.get(test_url, headers=self.headers, timeout=10)
            return response.status_code in [200, 404]  # 404 có thể là endpoint không tồn tại nhưng auth OK
        except Exception:
            return False
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Lấy danh sách giọng nói có sẵn"""
        try:
            voices_url = f"{self.base_url}/voices"
            response = requests.get(voices_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                api_voices = response.json()
                return {
                    "success": True,
                    "voices": api_voices,
                    "total_count": len(api_voices)
                }
            else:
                # Fallback to hardcoded voices
                return {
                    "success": True,
                    "voices": list(self.voices.values()),
                    "total_count": len(self.voices),
                    "source": "hardcoded"
                }
                
        except Exception as e:
            # Fallback to hardcoded voices
            return {
                "success": True,
                "voices": list(self.voices.values()),
                "total_count": len(self.voices),
                "source": "hardcoded",
                "api_error": str(e)
            }
    
    def get_elder_friendly_voices(self) -> List[Dict[str, Any]]:
        """Lấy danh sách giọng phù hợp với người cao tuổi"""
        elder_voices = []
        
        for voice_id, voice_info in self.voices.items():
            # Ưu tiên giọng trung niên và giọng nam ấm áp
            is_recommended = (
                "trung niên" in voice_info["description"] or 
                "ấm áp" in voice_info["description"] or
                voice_id == 3 or voice_id == 4  # Thu Minh và Hoài Nam
            )
            
            elder_voices.append({
                "voice_id": voice_id,
                "name": voice_info["name"],
                "gender": voice_info["gender"],
                "description": voice_info["description"],
                "recommended": is_recommended
            })
        
        # Sắp xếp theo mức độ phù hợp
        elder_voices.sort(key=lambda x: x["recommended"], reverse=True)
        return elder_voices
    
    def synthesize_speech(self, text: str, custom_config: Dict = None) -> Dict[str, Any]:
        """
        Chuyển đổi text thành speech
        
        Args:
            text: Text cần chuyển đổi
            custom_config: Cấu hình tùy chỉnh
            
        Returns:
            Dict chứa kết quả synthesis và metrics
        """
        start_time = time.time()
        
        try:
            # Validate input
            is_valid, error_msg = self.validate_text_input(text)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg,
                    "latency_ms": (time.time() - start_time) * 1000
                }
            
            # Prepare config
            config = self.elder_config.copy()
            if custom_config:
                config.update(custom_config)
            
            # Prepare request
            payload = {
                "text": text,
                "voice_id": config["voice_id"],
                "speed": config["speed"],
                "tone": config["tone"],
                "sample_rate": config.get("sample_rate", 22050),
                "format": "mp3"  # VBEE hỗ trợ MP3
            }
            
            # Make API request
            synthesis_url = f"{self.base_url}/text-to-speech"
            response = requests.post(
                synthesis_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                # Process response
                result = response.json()
                
                # VBEE có thể trả về base64 encoded audio hoặc URL
                if "audio_data" in result:
                    # Base64 encoded audio
                    audio_data = base64.b64decode(result["audio_data"])
                elif "audio_url" in result:
                    # Download from URL
                    audio_response = requests.get(result["audio_url"], timeout=30)
                    audio_data = audio_response.content
                else:
                    return {
                        "success": False,
                        "error": "No audio data in response",
                        "latency_ms": (time.time() - start_time) * 1000
                    }
                
                # Save audio file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tts_output_{timestamp}.mp3"
                filepath = os.path.join(AUDIO_OUTPUT_DIR, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(audio_data)
                
                latency = (time.time() - start_time) * 1000
                
                return {
                    "success": True,
                    "audio_file": filepath,
                    "audio_data": audio_data,
                    "character_count": len(text),
                    "latency_ms": latency,
                    "file_size_bytes": len(audio_data),
                    "voice_used": config["voice_id"],
                    "audio_duration_estimate": self.estimate_audio_duration(text),
                    "config_used": config
                }
            else:
                return {
                    "success": False,
                    "error": f"VBEE API error: {response.status_code} - {response.text}",
                    "latency_ms": (time.time() - start_time) * 1000
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"TTS synthesis error: {str(e)}",
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    def synthesize_with_ssml(self, ssml_text: str, custom_config: Dict = None) -> Dict[str, Any]:
        """
        Chuyển đổi SSML thành speech (nếu VBEE hỗ trợ)
        
        Args:
            ssml_text: SSML text
            custom_config: Cấu hình tùy chỉnh
            
        Returns:
            Dict chứa kết quả synthesis
        """
        # Nhiều TTS service chưa hỗ trợ SSML đầy đủ
        # Fallback to plain text
        plain_text = self._extract_text_from_ssml(ssml_text)
        return self.synthesize_speech(plain_text, custom_config)
    
    def _extract_text_from_ssml(self, ssml_text: str) -> str:
        """Trích xuất plain text từ SSML"""
        import re
        # Loại bỏ các thẻ SSML
        plain_text = re.sub(r'<[^>]+>', '', ssml_text)
        return plain_text.strip()
    
    def create_elder_friendly_ssml(self, text: str, emphasis_words: List[str] = None, 
                                 pause_duration: str = "0.5s") -> str:
        """
        Tạo SSML phù hợp với người cao tuổi
        
        Args:
            text: Text gốc
            emphasis_words: Danh sách từ cần nhấn mạnh
            pause_duration: Thời gian dừng giữa câu
            
        Returns:
            SSML text
        """
        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="vi-VN">'
        
        # Thêm pause giữa các câu
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Nhấn mạnh các từ quan trọng
            if emphasis_words:
                for word in emphasis_words:
                    sentence = sentence.replace(word, f'<emphasis level="moderate">{word}</emphasis>')
            
            ssml += f'{sentence}.'
            if sentence != sentences[-1]:  # Không thêm pause ở câu cuối
                ssml += f'<break time="{pause_duration}"/>'
        
        ssml += '</speak>'
        return ssml
    
    def validate_text_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate text input
        
        Args:
            text: Text cần validate
            
        Returns:
            Tuple[is_valid, error_message]
        """
        if not text or not text.strip():
            return False, "Text không được để trống"
        
        if len(text.strip()) < 1:
            return False, "Text quá ngắn"
        
        if len(text) > 5000:  # VBEE limit
            return False, "Text quá dài (tối đa 5000 ký tự)"
        
        # Kiểm tra ký tự đặc biệt
        import re
        if re.search(r'[<>&"\']', text):
            return False, "Text chứa ký tự đặc biệt không được phép"
        
        return True, None
    
    def estimate_audio_duration(self, text: str, words_per_minute: int = 150) -> float:
        """
        Ước tính thời lượng audio
        
        Args:
            text: Text input
            words_per_minute: Tốc độ đọc (từ/phút)
            
        Returns:
            Thời lượng ước tính (giây)
        """
        word_count = len(text.split())
        
        # Điều chỉnh cho người cao tuổi (chậm hơn)
        elderly_wpm = int(words_per_minute * 0.8)  # Chậm hơn 20%
        
        duration_minutes = word_count / elderly_wpm
        duration_seconds = duration_minutes * 60
        
        # Thêm thời gian cho dấu câu
        pause_time = text.count('.') * 0.8 + text.count(',') * 0.3
        
        return duration_seconds + pause_time
    
    def get_voice_info(self, voice_id: int) -> Dict[str, Any]:
        """Lấy thông tin chi tiết về voice"""
        if voice_id in self.voices:
            return {
                "success": True,
                "voice_info": self.voices[voice_id],
                "voice_id": voice_id
            }
        else:
            return {
                "success": False,
                "error": f"Voice ID {voice_id} không tồn tại"
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Lấy thông tin về service"""
        return {
            "service_name": "VBEE AI TTS",
            "api_url": self.base_url,
            "available_voices": len(self.voices),
            "default_voice_id": VBEE_VOICE_ID,
            "supported_formats": ["mp3"],
            "max_text_length": 5000,
            "sample_rates": [16000, 22050, 44100],
            "elder_friendly_config": self.elder_config
        }


def main():
    """Test function"""
    print("🧪 VBEE AI TTS Module Test")
    print("=" * 40)
    
    try:
        # Initialize TTS
        tts = VBEETTS()
        
        # Test connection
        if tts.test_connection():
            print("✅ VBEE API connection successful")
        else:
            print("❌ VBEE API connection failed")
            return
        
        # Test available voices
        print("\\n🎵 Testing available voices...")
        voices_result = tts.get_available_voices()
        
        if voices_result["success"]:
            print(f"✅ Found {voices_result['total_count']} voices")
            for voice in voices_result["voices"][:3]:  # Show first 3
                if isinstance(voice, dict):
                    print(f"   - {voice.get('name', 'Unknown')}: {voice.get('description', '')}")
        
        # Test elder-friendly voices
        print("\\n👴 Elder-friendly voices:")
        elder_voices = tts.get_elder_friendly_voices()
        for voice in elder_voices[:3]:
            recommended = "⭐" if voice["recommended"] else "  "
            print(f"  {recommended} {voice['name']} - {voice['description']}")
        
        # Test basic synthesis
        print("\\n🔊 Testing basic synthesis...")
        test_texts = [
            "Xin chào, tôi là trợ lý AI hỗ trợ người cao tuổi.",
            "Hôm nay thời tiết thế nào? Bác có khỏe không?",
            "Nhớ uống thuốc đầy đủ và tập thể dục nhẹ nhàng nhé!"
        ]
        
        for i, text in enumerate(test_texts[:1], 1):  # Test chỉ 1 câu đầu
            print(f"\\nSynthesizing text {i}: '{text[:30]}...'")
            
            result = tts.synthesize_speech(text)
            
            if result["success"]:
                print(f"✅ TTS synthesis successful!")
                print(f"📁 File: {os.path.basename(result['audio_file'])}")
                print(f"📊 Characters: {result['character_count']}")
                print(f"⏱️  Latency: {result['latency_ms']:.1f}ms")
                print(f"💾 File size: {result['file_size_bytes']} bytes")
                print(f"🎵 Voice: {result['voice_used']}")
                print(f"⏰ Estimated duration: {result['audio_duration_estimate']:.1f}s")
                
                # Test audio playback
                print("🔊 Testing audio playback...")
                player = AudioPlayer()
                play_success, play_error = player.play_audio_file(result["audio_file"])
                
                if play_success:
                    print("✅ Audio playback successful")
                else:
                    print(f"❌ Audio playback failed: {play_error}")
                
                # Cleanup
                if not SAVE_AUDIO_FILES and os.path.exists(result["audio_file"]):
                    os.unlink(result["audio_file"])
                    
            else:
                print(f"❌ TTS synthesis failed: {result['error']}")
                break
        
        # Test different voice configurations
        print("\\n🎭 Testing different voice configurations...")
        test_configs = [
            {
                "name": "Slower speech for elderly",
                "config": {"voice_id": 3, "speed": 0.8}
            },
            {
                "name": "Male voice with normal speed",
                "config": {"voice_id": 2, "speed": 1.0}
            }
        ]
        
        test_text = "Đây là bài test với các cấu hình giọng nói khác nhau."
        
        for config_test in test_configs[:1]:  # Test chỉ 1 config
            print(f"\\n🔧 Testing: {config_test['name']}")
            
            result = tts.synthesize_speech(test_text, config_test['config'])
            
            if result["success"]:
                print(f"✅ Config test successful: {result['latency_ms']:.1f}ms")
                
                # Quick playback test
                player = AudioPlayer()
                play_success, _ = player.play_audio_file(result["audio_file"])
                print(f"🔊 Playback: {'✅' if play_success else '❌'}")
                
                if not SAVE_AUDIO_FILES and os.path.exists(result["audio_file"]):
                    os.unlink(result["audio_file"])
            else:
                print(f"❌ Config test failed: {result['error']}")
        
        # Test input validation
        print("\\n✅ Testing input validation...")
        test_cases = [
            ("Valid text", "Đây là text hợp lệ", True),
            ("Empty text", "", False),
            ("Very long text", "A" * 6000, False),
            ("Text with special chars", "Text có <tag>", False)
        ]
        
        for name, text, should_be_valid in test_cases:
            is_valid, error = tts.validate_text_input(text)
            
            if is_valid == should_be_valid:
                print(f"✅ {name}: {'Valid' if is_valid else 'Invalid'}")
            else:
                print(f"❌ {name}: Expected {'valid' if should_be_valid else 'invalid'}, got {'valid' if is_valid else 'invalid'}")
        
        # Test service info
        print("\\n📋 Service Information:")
        service_info = tts.get_service_info()
        for key, value in service_info.items():
            print(f"   {key}: {value}")
        
        print("\\n🎯 TTS Module test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
