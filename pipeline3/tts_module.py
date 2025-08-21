"""
Text-to-Speech Module for Pipeline 3
Hỗ trợ FPT.AI TTS (primary) và Google Cloud TTS (backup)
"""

import os
import requests
import time
import base64
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import tempfile

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None

from config import (
    FPT_API_KEY, FPT_TTS_CONFIG,
    GOOGLE_CLOUD_JSON_PATH, GOOGLE_TTS_CONFIG,
    TIMEOUT_CONFIG, RETRY_CONFIG
)
from utils import Logger, MetricsCollector, CostCalculator

class TTSModule:
    """Text-to-Speech module with FPT.AI primary and Google Cloud TTS backup"""
    
    def __init__(self):
        self.logger = Logger("tts")
        self.metrics = MetricsCollector()
        self.last_used_service = None
        self.google_client = None
        
        # Validate configuration and initialize
        self._validate_config()
        self._initialize_google_client()
        
    def _validate_config(self):
        """Validate TTS configuration"""
        errors = []
        
        if FPT_API_KEY == "your_fpt_api_key_here":
            errors.append("FPT_API_KEY chưa được cấu hình")
            
        if GOOGLE_CLOUD_JSON_PATH == "path/to/your/service-account.json":
            errors.append("GOOGLE_CLOUD_JSON_PATH chưa được cấu hình")
        elif not os.path.exists(GOOGLE_CLOUD_JSON_PATH):
            errors.append(f"Google Cloud JSON file không tồn tại: {GOOGLE_CLOUD_JSON_PATH}")
            
        if texttospeech is None:
            errors.append("Google Cloud TTS library chưa được cài đặt (pip install google-cloud-texttospeech)")
            
        if errors:
            self.logger.warning("Một số cấu hình TTS chưa sẵn sàng:")
            for error in errors:
                self.logger.warning(f"  - {error}")
    
    def _initialize_google_client(self):
        """Initialize Google Cloud TTS client"""
        try:
            if texttospeech is None:
                self.logger.warning("Google Cloud TTS library không khả dụng")
                return
                
            if not os.path.exists(GOOGLE_CLOUD_JSON_PATH):
                self.logger.warning("Google Cloud JSON file không tồn tại")
                return
            
            # Set environment variable for authentication
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CLOUD_JSON_PATH
            
            # Initialize client
            self.google_client = texttospeech.TextToSpeechClient()
            
            self.logger.success("Google Cloud TTS client đã sẵn sàng")
            
        except Exception as e:
            self.logger.warning(f"Không thể khởi tạo Google Cloud TTS client: {e}")
            self.google_client = None
    
    def _tts_fpt_ai(self, text: str, output_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Perform TTS using FPT.AI"""
        start_time = time.time()
        
        try:
            # Prepare request
            headers = {
                'api-key': FPT_API_KEY,
                'speed': FPT_TTS_CONFIG["speed"],
                'voice': FPT_TTS_CONFIG["voice"]
            }
            
            data = {
                'text': text
            }
            
            # Make request
            response = requests.post(
                FPT_TTS_CONFIG["url"],
                headers=headers,
                data=data,
                timeout=TIMEOUT_CONFIG["tts_timeout"]
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                
                if result.get('error') == 0:  # Success
                    # Get audio data
                    audio_url = result.get('async')
                    
                    if audio_url:
                        # Download audio file
                        audio_response = requests.get(audio_url, timeout=30)
                        
                        if audio_response.status_code == 200:
                            # Save audio file
                            with open(output_path, 'wb') as f:
                                f.write(audio_response.content)
                            
                            processing_time = time.time() - start_time
                            file_size = len(audio_response.content)
                            
                            metrics = {
                                "service": "fpt_ai",
                                "processing_time": processing_time,
                                "status": "success",
                                "text_length": len(text),
                                "audio_file_size": file_size,
                                "output_path": output_path
                            }
                            
                            return True, metrics
                        else:
                            error_msg = f"Không thể tải audio từ FPT.AI: HTTP {audio_response.status_code}"
                    else:
                        error_msg = "FPT.AI không trả về URL audio"
                else:
                    error_msg = result.get('message', 'Unknown FPT.AI TTS error')
            else:
                error_msg = f"FPT.AI TTS HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            error_msg = str(e)
        
        # Return error
        processing_time = time.time() - start_time
        metrics = {
            "service": "fpt_ai",
            "processing_time": processing_time,
            "status": "error",
            "text_length": len(text),
            "error": error_msg
        }
        return False, metrics
    
    def _tts_google_cloud(self, text: str, output_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Perform TTS using Google Cloud"""
        start_time = time.time()
        
        try:
            if self.google_client is None:
                raise Exception("Google Cloud TTS client chưa được khởi tạo")
            
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=GOOGLE_TTS_CONFIG["language_code"],
                name=GOOGLE_TTS_CONFIG["name"],
                ssml_gender=texttospeech.SsmlVoiceGender[GOOGLE_TTS_CONFIG["ssml_gender"]]
            )
            
            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding[GOOGLE_TTS_CONFIG["audio_encoding"]],
                sample_rate_hertz=GOOGLE_TTS_CONFIG["sample_rate"]
            )
            
            # Perform the text-to-speech request
            response = self.google_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save the audio file
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            processing_time = time.time() - start_time
            file_size = len(response.audio_content)
            
            metrics = {
                "service": "google_cloud",
                "processing_time": processing_time,
                "status": "success",
                "text_length": len(text),
                "audio_file_size": file_size,
                "output_path": output_path,
                "estimated_cost": CostCalculator.calculate_tts_cost(len(text), "google")
            }
            
            return True, metrics
            
        except Exception as e:
            processing_time = time.time() - start_time
            metrics = {
                "service": "google_cloud",
                "processing_time": processing_time,
                "status": "error",
                "text_length": len(text),
                "error": str(e)
            }
            return False, metrics
    
    def synthesize(
        self, 
        text: str, 
        output_path: Optional[str] = None,
        force_service: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert text to speech with automatic fallback
        
        Args:
            text: Text to convert to speech
            output_path: Output audio file path (auto-generated if None)
            force_service: Force specific service ("fpt" or "google")
            
        Returns:
            Dict containing result, output_path, service_used, metrics, etc.
        """
        self.logger.info(f"Bắt đầu TTS cho text: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # Generate output path if not provided
        if output_path is None:
            os.makedirs("audio_samples/output", exist_ok=True)
            timestamp = int(time.time())
            output_path = f"audio_samples/output/tts_output_{timestamp}.wav"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Validate text length
        if len(text) > 5000:
            return {
                "success": False,
                "error": "Text quá dài (tối đa 5000 ký tự)",
                "text": text,
                "text_length": len(text)
            }
        
        # Start total timing
        self.metrics.start_timer("total_tts_time")
        
        # Try services based on preference or force
        services_to_try = []
        
        if force_service == "fpt":
            services_to_try = ["fpt"]
        elif force_service == "google":
            services_to_try = ["google"]
        else:
            # Default: try FPT.AI first, then Google Cloud as backup
            services_to_try = ["fpt", "google"]
        
        last_error = None
        all_metrics = []
        
        for service in services_to_try:
            self.logger.info(f"Thử TTS service: {service.upper()}")
            
            if service == "fpt":
                success, metrics = self._tts_fpt_ai(text, output_path)
            elif service == "google":
                success, metrics = self._tts_google_cloud(text, output_path)
            else:
                continue
            
            all_metrics.append(metrics)
            
            if success:
                self.last_used_service = service
                total_time = self.metrics.end_timer("total_tts_time")
                
                # Get audio file info
                audio_info = {}
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    audio_info = {
                        "file_size_bytes": file_size,
                        "file_size_mb": file_size / (1024 * 1024),
                        "file_path": output_path
                    }
                
                self.logger.success(f"TTS thành công với {service.upper()}")
                self.logger.info(f"Audio file saved: {output_path}")
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "service_used": service,
                    "text": text,
                    "text_length": len(text),
                    "audio_info": audio_info,
                    "processing_time": total_time,
                    "service_metrics": metrics,
                    "all_attempts": all_metrics
                }
            else:
                self.logger.warning(f"TTS thất bại với {service.upper()}: {metrics.get('error', 'Unknown error')}")
                last_error = metrics.get('error', 'Unknown error')
        
        # All services failed
        total_time = self.metrics.end_timer("total_tts_time")
        
        self.logger.error("Tất cả TTS services đều thất bại")
        
        return {
            "success": False,
            "error": last_error or "Tất cả TTS services thất bại",
            "text": text,
            "text_length": len(text),
            "processing_time": total_time,
            "all_attempts": all_metrics
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of available TTS services"""
        status = {
            "fpt_ai": {
                "configured": FPT_API_KEY != "your_fpt_api_key_here",
                "available": FPT_API_KEY != "your_fpt_api_key_here"
            },
            "google_cloud": {
                "configured": (
                    os.path.exists(GOOGLE_CLOUD_JSON_PATH) and 
                    texttospeech is not None
                ),
                "available": self.google_client is not None
            },
            "last_used_service": self.last_used_service
        }
        
        return status

def test_tts_module():
    """Test function for TTS module"""
    print("=== TESTING TTS MODULE ===")
    
    tts = TTSModule()
    
    # Show service status
    status = tts.get_service_status()
    print(f"FPT.AI available: {status['fpt_ai']['available']}")
    print(f"Google Cloud available: {status['google_cloud']['available']}")
    
    # Test with sample texts
    test_cases = [
        "Xin chào, tôi là trợ lý AI của bạn.",
        "Hôm nay là một ngày đẹp trời. Bạn có kế hoạch gì không?",
        "Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi."
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Text: {test_text}")
        
        result = tts.synthesize(test_text)
        
        if result["success"]:
            print(f"✅ TTS Success!")
            print(f"Service used: {result['service_used']}")
            print(f"Output file: {result['output_path']}")
            print(f"Processing time: {result['processing_time']:.3f}s")
            print(f"File size: {result['audio_info'].get('file_size_mb', 0):.2f}MB")
        else:
            print(f"❌ TTS Failed: {result['error']}")

if __name__ == "__main__":
    test_tts_module()
