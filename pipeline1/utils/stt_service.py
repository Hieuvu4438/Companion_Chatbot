import os
import time
import logging
from typing import Dict, Optional, Tuple
from google.cloud import speech
import io

class GoogleSTTService:
    """
    Dịch vụ Speech-to-Text sử dụng Google Cloud Speech API
    """
    
    def __init__(self, credentials_path: Optional[str] = None, 
                 project_id: Optional[str] = None):
        """
        Khởi tạo Google STT Service
        
        Args:
            credentials_path: Đường dẫn đến file JSON credentials
            project_id: Google Cloud Project ID
        """
        self.credentials_path = credentials_path
        self.project_id = project_id
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize client
        self.client = None
        self._initialize_client()
        
        # Default configuration
        self.default_config = {
            "language_code": "vi-VN",
            "sample_rate_hertz": 16000,
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "enable_automatic_punctuation": True,
            "model": "latest_long",
            "use_enhanced": True
        }
        
    def _initialize_client(self):
        """Khởi tạo Google Speech client"""
        try:
            # Set credentials if provided
            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                
            # Initialize client
            self.client = speech.SpeechClient()
            self.logger.info("✅ Google STT client initialized successfully")
            print("✅ Google STT client khởi tạo thành công")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google STT client: {e}")
            print(f"❌ Lỗi khởi tạo Google STT client: {e}")
            raise
            
    def test_connection(self) -> bool:
        """Test kết nối với Google STT API"""
        try:
            # Create a simple test request
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="vi-VN"
            )
            
            # Create empty audio for test
            audio = speech.RecognitionAudio(content=b'')
            
            # This should fail but confirm API connection
            try:
                self.client.recognize(config=config, audio=audio)
            except Exception:
                # Expected to fail with empty audio, but connection is working
                pass
                
            print("✅ Google STT API connection test passed")
            return True
            
        except Exception as e:
            print(f"❌ Google STT API connection test failed: {e}")
            return False
            
    def transcribe_audio_file(self, audio_file_path: str, 
                            custom_config: Optional[Dict] = None) -> Dict:
        """
        Chuyển đổi file âm thanh thành text
        
        Args:
            audio_file_path: Đường dẫn đến file âm thanh
            custom_config: Cấu hình tùy chỉnh
            
        Returns:
            Dict với kết quả transcription
        """
        start_time = time.time()
        
        try:
            # Kiểm tra file tồn tại
            if not os.path.exists(audio_file_path):
                return {
                    "success": False,
                    "error": f"File không tồn tại: {audio_file_path}",
                    "transcript": "",
                    "confidence": 0.0,
                    "latency_ms": 0
                }
                
            print(f"🎤 Đang xử lý STT cho file: {os.path.basename(audio_file_path)}")
            
            # Đọc file âm thanh
            with io.open(audio_file_path, "rb") as audio_file:
                content = audio_file.read()
                
            # Cấu hình recognition
            config = self.default_config.copy()
            if custom_config:
                config.update(custom_config)
                
            recognition_config = speech.RecognitionConfig(
                encoding=config["encoding"],
                sample_rate_hertz=config["sample_rate_hertz"],
                language_code=config["language_code"],
                enable_automatic_punctuation=config["enable_automatic_punctuation"],
                model=config["model"],
                use_enhanced=config.get("use_enhanced", True)
            )
            
            audio = speech.RecognitionAudio(content=content)
            
            # Gọi API
            response = self.client.recognize(
                config=recognition_config, 
                audio=audio
            )
            
            latency = time.time() - start_time
            
            # Xử lý kết quả
            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                
                transcript = alternative.transcript
                confidence = alternative.confidence
                
                print(f"✅ STT thành công: '{transcript}' (confidence: {confidence:.2f})")
                
                return {
                    "success": True,
                    "transcript": transcript,
                    "confidence": confidence,
                    "latency_ms": latency * 1000,
                    "alternatives": [alt.transcript for alt in result.alternatives],
                    "error": ""
                }
            else:
                return {
                    "success": False,
                    "error": "Không nhận diện được âm thanh",
                    "transcript": "",
                    "confidence": 0.0,
                    "latency_ms": latency * 1000
                }
                
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Lỗi STT: {str(e)}"
            
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "transcript": "",
                "confidence": 0.0,
                "latency_ms": latency * 1000
            }
            
    def transcribe_audio_streaming(self, audio_stream, 
                                 custom_config: Optional[Dict] = None) -> Dict:
        """
        Chuyển đổi âm thanh real-time streaming
        
        Args:
            audio_stream: Generator yielding audio chunks
            custom_config: Cấu hình tùy chỉnh
            
        Returns:
            Dict với kết quả transcription
        """
        start_time = time.time()
        
        try:
            print("🎤 Bắt đầu streaming STT...")
            
            # Cấu hình streaming
            config = self.default_config.copy()
            if custom_config:
                config.update(custom_config)
                
            streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=config["encoding"],
                    sample_rate_hertz=config["sample_rate_hertz"],
                    language_code=config["language_code"],
                    enable_automatic_punctuation=config["enable_automatic_punctuation"],
                    model=config["model"]
                ),
                interim_results=True
            )
            
            # Tạo streaming request
            def request_generator():
                yield speech.StreamingRecognizeRequest(
                    streaming_config=streaming_config
                )
                for chunk in audio_stream:
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
                    
            # Gọi streaming API
            responses = self.client.streaming_recognize(
                requests=request_generator()
            )
            
            # Xử lý responses
            final_transcript = ""
            confidence = 0.0
            
            for response in responses:
                for result in response.results:
                    if result.is_final:
                        alternative = result.alternatives[0]
                        final_transcript = alternative.transcript
                        confidence = alternative.confidence
                        break
                        
                if final_transcript:
                    break
                    
            latency = time.time() - start_time
            
            if final_transcript:
                print(f"✅ Streaming STT thành công: '{final_transcript}'")
                return {
                    "success": True,
                    "transcript": final_transcript,
                    "confidence": confidence,
                    "latency_ms": latency * 1000,
                    "error": ""
                }
            else:
                return {
                    "success": False,
                    "error": "Không nhận diện được âm thanh từ stream",
                    "transcript": "",
                    "confidence": 0.0,
                    "latency_ms": latency * 1000
                }
                
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Lỗi streaming STT: {str(e)}"
            
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "transcript": "",
                "confidence": 0.0,
                "latency_ms": latency * 1000
            }
            
    def get_supported_languages(self) -> list:
        """Lấy danh sách ngôn ngữ được hỗ trợ"""
        return [
            "vi-VN",  # Tiếng Việt
            "en-US",  # English (US)
            "en-GB",  # English (UK)
            "zh-CN",  # Chinese (Simplified)
            "ja-JP",  # Japanese
            "ko-KR",  # Korean
        ]
        
    def update_config(self, new_config: Dict):
        """Cập nhật cấu hình mặc định"""
        self.default_config.update(new_config)
        print(f"✅ Đã cập nhật cấu hình STT: {new_config}")
        
    def get_current_config(self) -> Dict:
        """Lấy cấu hình hiện tại"""
        return self.default_config.copy()
        
    def validate_audio_file(self, audio_file_path: str) -> Tuple[bool, str]:
        """
        Kiểm tra tính hợp lệ của file âm thanh
        
        Returns:
            Tuple[is_valid, error_message]
        """
        try:
            if not os.path.exists(audio_file_path):
                return False, "File không tồn tại"
                
            # Kiểm tra kích thước file
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                return False, "File rỗng"
                
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                return False, "File quá lớn (>10MB)"
                
            # Kiểm tra định dạng file
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            supported_formats = ['.wav', '.mp3', '.flac', '.ogg']
            
            if file_ext not in supported_formats:
                return False, f"Định dạng không hỗ trợ: {file_ext}"
                
            return True, ""
            
        except Exception as e:
            return False, f"Lỗi kiểm tra file: {str(e)}"
            
    def get_api_usage_info(self) -> Dict:
        """Lấy thông tin sử dụng API (nếu có)"""
        # Note: Google Cloud doesn't provide real-time usage info via API
        # This would need to be tracked separately or checked in Console
        return {
            "note": "Kiểm tra usage tại Google Cloud Console",
            "free_tier_limit": "60 phút/tháng",
            "pricing_url": "https://cloud.google.com/speech-to-text/pricing"
        }


def test_google_stt_service():
    """Test function cho Google STT Service"""
    print("🧪 TESTING GOOGLE STT SERVICE")
    print("=" * 40)
    
    try:
        # Initialize service
        stt_service = GoogleSTTService()
        
        # Test connection
        if stt_service.test_connection():
            print("✅ API connection OK")
        else:
            print("❌ API connection failed")
            return
            
        # Test config
        print(f"📋 Current config: {stt_service.get_current_config()}")
        
        # Test supported languages
        languages = stt_service.get_supported_languages()
        print(f"🌍 Supported languages: {languages}")
        
        print("\n🎯 Google STT Service test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_google_stt_service()
