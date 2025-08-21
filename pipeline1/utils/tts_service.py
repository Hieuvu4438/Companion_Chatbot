import os
import time
import tempfile
import logging
from typing import Dict, Optional, Tuple
from google.cloud import texttospeech

class GoogleTTSService:
    """
    Dịch vụ Text-to-Speech sử dụng Google Cloud Text-to-Speech API
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Khởi tạo Google TTS Service
        
        Args:
            credentials_path: Đường dẫn đến file JSON credentials
        """
        self.credentials_path = credentials_path
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize client
        self.client = None
        self._initialize_client()
        
        # Default configuration cho người cao tuổi
        self.default_config = {
            "language_code": "vi-VN",
            "voice_name": "vi-VN-Neural2-A",  # Giọng nữ tự nhiên
            "voice_gender": texttospeech.SsmlVoiceGender.FEMALE,
            "audio_encoding": texttospeech.AudioEncoding.MP3,
            "speaking_rate": 0.9,  # Chậm hơn để người cao tuổi nghe rõ
            "pitch": 0.0,  # Giọng bình thường
            "volume_gain_db": 0.0  # Âm lượng bình thường
        }
        
    def _initialize_client(self):
        """Khởi tạo Google TTS client"""
        try:
            # Set credentials if provided
            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                
            # Initialize client
            self.client = texttospeech.TextToSpeechClient()
            self.logger.info("✅ Google TTS client initialized successfully")
            print("✅ Google TTS client khởi tạo thành công")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google TTS client: {e}")
            print(f"❌ Lỗi khởi tạo Google TTS client: {e}")
            raise
            
    def test_connection(self) -> bool:
        """Test kết nối với Google TTS API"""
        try:
            # List available voices để test connection
            voices = self.client.list_voices()
            
            if voices.voices:
                print("✅ Google TTS API connection test passed")
                return True
            else:
                print("❌ Google TTS API returned no voices")
                return False
                
        except Exception as e:
            print(f"❌ Google TTS API connection test failed: {e}")
            return False
            
    def synthesize_speech(self, text: str, 
                         output_file: Optional[str] = None,
                         custom_config: Optional[Dict] = None) -> Dict:
        """
        Chuyển đổi text thành âm thanh
        
        Args:
            text: Text cần chuyển đổi
            output_file: Đường dẫn file output (nếu None sẽ tạo tự động)
            custom_config: Cấu hình tùy chỉnh
            
        Returns:
            Dict với kết quả synthesis
        """
        start_time = time.time()
        
        try:
            if not text.strip():
                return {
                    "success": False,
                    "error": "Text rỗng",
                    "audio_file": "",
                    "latency_ms": 0,
                    "character_count": 0
                }
                
            print(f"🔊 Đang xử lý TTS cho: '{text[:50]}...'")
            
            # Tạo output file nếu chưa có
            if output_file is None:
                output_file = os.path.join(
                    tempfile.gettempdir(), 
                    f"tts_output_{int(time.time())}.mp3"
                )
                
            # Cấu hình synthesis
            config = self.default_config.copy()
            if custom_config:
                config.update(custom_config)
                
            # Prepare input text
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Voice selection
            voice = texttospeech.VoiceSelectionParams(
                language_code=config["language_code"],
                name=config["voice_name"],
                ssml_gender=config["voice_gender"]
            )
            
            # Audio config
            audio_config = texttospeech.AudioConfig(
                audio_encoding=config["audio_encoding"],
                speaking_rate=config["speaking_rate"],
                pitch=config["pitch"],
                volume_gain_db=config["volume_gain_db"]
            )
            
            # Gọi API
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Lưu file âm thanh
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
                
            latency = time.time() - start_time
            character_count = len(text)
            file_size = os.path.getsize(output_file)
            
            print(f"✅ TTS thành công: {os.path.basename(output_file)} ({file_size} bytes)")
            
            return {
                "success": True,
                "audio_file": output_file,
                "latency_ms": latency * 1000,
                "character_count": character_count,
                "file_size_bytes": file_size,
                "voice_used": config["voice_name"],
                "audio_format": config["audio_encoding"].name,
                "error": ""
            }
            
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Lỗi TTS: {str(e)}"
            
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "audio_file": "",
                "latency_ms": latency * 1000,
                "character_count": len(text) if text else 0
            }
            
    def synthesize_with_ssml(self, ssml_text: str,
                           output_file: Optional[str] = None,
                           custom_config: Optional[Dict] = None) -> Dict:
        """
        Chuyển đổi SSML thành âm thanh (hỗ trợ markup nâng cao)
        
        Args:
            ssml_text: SSML markup text
            output_file: Đường dẫn file output
            custom_config: Cấu hình tùy chỉnh
        """
        start_time = time.time()
        
        try:
            print(f"🎵 Đang xử lý SSML TTS...")
            
            if output_file is None:
                output_file = os.path.join(
                    tempfile.gettempdir(), 
                    f"tts_ssml_{int(time.time())}.mp3"
                )
                
            # Cấu hình
            config = self.default_config.copy()
            if custom_config:
                config.update(custom_config)
                
            # SSML input
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            
            # Voice và audio config
            voice = texttospeech.VoiceSelectionParams(
                language_code=config["language_code"],
                name=config["voice_name"],
                ssml_gender=config["voice_gender"]
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=config["audio_encoding"],
                speaking_rate=config["speaking_rate"],
                pitch=config["pitch"],
                volume_gain_db=config["volume_gain_db"]
            )
            
            # Synthesize
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
                
            latency = time.time() - start_time
            
            print(f"✅ SSML TTS thành công: {os.path.basename(output_file)}")
            
            return {
                "success": True,
                "audio_file": output_file,
                "latency_ms": latency * 1000,
                "character_count": len(ssml_text),
                "file_size_bytes": os.path.getsize(output_file),
                "error": ""
            }
            
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Lỗi SSML TTS: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "audio_file": "",
                "latency_ms": latency * 1000,
                "character_count": len(ssml_text) if ssml_text else 0
            }
            
    def create_elder_friendly_ssml(self, text: str, 
                                  emphasis_words: list = None,
                                  pause_duration: str = "0.5s") -> str:
        """
        Tạo SSML thân thiện với người cao tuổi
        
        Args:
            text: Text gốc
            emphasis_words: Danh sách từ cần nhấn mạnh
            pause_duration: Thời gian pause giữa câu
        """
        
        # Clean text
        text = text.strip()
        
        # Thêm emphasis cho các từ quan trọng
        if emphasis_words:
            for word in emphasis_words:
                text = text.replace(word, f'<emphasis level="moderate">{word}</emphasis>')
                
        # Thêm pause sau dấu chấm và dấu phẩy
        text = text.replace(". ", f". <break time='{pause_duration}'/> ")
        text = text.replace(", ", f", <break time='0.3s'/> ")
        
        # Tạo SSML hoàn chỉnh
        ssml = f"""
<speak>
    <prosody rate="0.9" pitch="0st" volume="medium">
        {text}
    </prosody>
</speak>
""".strip()
        
        return ssml
        
    def get_available_voices(self, language_code: str = "vi-VN") -> Dict:
        """Lấy danh sách giọng nói có sẵn"""
        try:
            voices = self.client.list_voices(language_code=language_code)
            
            voice_list = []
            for voice in voices.voices:
                if language_code in voice.language_codes:
                    voice_info = {
                        "name": voice.name,
                        "gender": voice.ssml_gender.name,
                        "natural_sample_rate": voice.natural_sample_rate_hertz,
                        "language_codes": list(voice.language_codes)
                    }
                    voice_list.append(voice_info)
                    
            return {
                "success": True,
                "voices": voice_list,
                "total_count": len(voice_list)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi lấy danh sách giọng nói: {str(e)}",
                "voices": []
            }
            
    def get_elder_friendly_voices(self) -> list:
        """Lấy danh sách giọng nói phù hợp cho người cao tuổi"""
        return [
            {
                "name": "vi-VN-Neural2-A",
                "description": "Giọng nữ Neural2 - Tự nhiên nhất, phù hợp người cao tuổi",
                "gender": "FEMALE",
                "recommended": True
            },
            {
                "name": "vi-VN-Neural2-D", 
                "description": "Giọng nam Neural2 - Rõ ràng, dễ nghe",
                "gender": "MALE",
                "recommended": True
            },
            {
                "name": "vi-VN-Standard-A",
                "description": "Giọng nữ Standard - Ổn định, đáng tin cậy",
                "gender": "FEMALE",
                "recommended": False
            },
            {
                "name": "vi-VN-Standard-B",
                "description": "Giọng nam Standard - Chuyên nghiệp",
                "gender": "MALE", 
                "recommended": False
            }
        ]
        
    def update_config(self, new_config: Dict):
        """Cập nhật cấu hình mặc định"""
        self.default_config.update(new_config)
        print(f"✅ Đã cập nhật cấu hình TTS: {new_config}")
        
    def get_current_config(self) -> Dict:
        """Lấy cấu hình hiện tại"""
        return self.default_config.copy()
        
    def validate_text_input(self, text: str) -> Tuple[bool, str]:
        """
        Kiểm tra tính hợp lệ của text input
        
        Returns:
            Tuple[is_valid, error_message]
        """
        try:
            if not text or not text.strip():
                return False, "Text rỗng"
                
            if len(text) > 5000:  # Google TTS limit
                return False, "Text quá dài (>5000 ký tự)"
                
            # Kiểm tra ký tự đặc biệt
            if any(ord(char) > 1114111 for char in text):
                return False, "Chứa ký tự không hợp lệ"
                
            return True, ""
            
        except Exception as e:
            return False, f"Lỗi kiểm tra text: {str(e)}"
            
    def estimate_audio_duration(self, text: str, speaking_rate: float = 0.9) -> float:
        """
        Ước tính thời lượng âm thanh (giây)
        
        Args:
            text: Text cần ước tính
            speaking_rate: Tốc độ nói
            
        Returns:
            Thời lượng ước tính (giây)
        """
        try:
            # Ước tính: ~150 từ/phút với speaking_rate = 1.0
            words_per_minute = 150 * speaking_rate
            word_count = len(text.split())
            
            duration_minutes = word_count / words_per_minute
            duration_seconds = duration_minutes * 60
            
            return max(1.0, duration_seconds)  # Tối thiểu 1 giây
            
        except Exception:
            return 5.0  # Default fallback
            
    def get_pricing_info(self) -> Dict:
        """Lấy thông tin pricing (tham khảo)"""
        return {
            "standard_voices": {
                "price_per_1m_chars": "$4.00",
                "free_tier": "1 triệu ký tự/tháng"
            },
            "neural2_voices": {
                "price_per_1m_chars": "$16.00", 
                "free_tier": "1 triệu ký tự/tháng"
            },
            "pricing_url": "https://cloud.google.com/text-to-speech/pricing",
            "note": "Giá có thể thay đổi, kiểm tra trang chính thức"
        }


def test_google_tts_service():
    """Test function cho Google TTS Service"""
    print("🧪 TESTING GOOGLE TTS SERVICE")
    print("=" * 40)
    
    try:
        # Initialize service
        tts_service = GoogleTTSService()
        
        # Test connection
        if tts_service.test_connection():
            print("✅ API connection OK")
        else:
            print("❌ API connection failed")
            return
            
        # Test voice listing
        voices = tts_service.get_available_voices("vi-VN")
        if voices["success"]:
            print(f"✅ Found {voices['total_count']} Vietnamese voices")
        else:
            print(f"❌ Failed to get voices: {voices['error']}")
            
        # Test elder-friendly voices
        elder_voices = tts_service.get_elder_friendly_voices()
        print(f"👴 Elder-friendly voices: {len(elder_voices)}")
        
        # Test text validation
        is_valid, error = tts_service.validate_text_input("Xin chào")
        print(f"✅ Text validation: {is_valid}")
        
        # Test duration estimation
        duration = tts_service.estimate_audio_duration("Xin chào, tôi là trợ lý AI")
        print(f"⏱️ Estimated duration: {duration:.1f}s")
        
        print("\n🎯 Google TTS Service test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_google_tts_service()
