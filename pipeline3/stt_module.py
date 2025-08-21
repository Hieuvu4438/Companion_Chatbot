"""
Speech-to-Text Module for Pipeline 3
Hỗ trợ FPT.AI STT (primary) và OpenAI Whisper (backup)
"""

import os
import requests
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import tempfile

try:
    import openai
except ImportError:
    openai = None

from config import (
    FPT_API_KEY, FPT_STT_CONFIG, 
    OPENAI_API_KEY, OPENAI_STT_CONFIG,
    TIMEOUT_CONFIG, RETRY_CONFIG
)
from utils import Logger, MetricsCollector, AudioUtils

class STTModule:
    """Speech-to-Text module with FPT.AI primary and OpenAI Whisper backup"""
    
    def __init__(self):
        self.logger = Logger("stt")
        self.metrics = MetricsCollector()
        self.last_used_service = None
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self):
        """Validate STT configuration"""
        errors = []
        
        if FPT_API_KEY == "your_fpt_api_key_here":
            errors.append("FPT_API_KEY chưa được cấu hình")
            
        if OPENAI_API_KEY == "your_openai_api_key_here":
            errors.append("OPENAI_API_KEY chưa được cấu hình")
            
        if openai is None:
            errors.append("OpenAI library chưa được cài đặt (pip install openai)")
            
        if errors:
            self.logger.warning("Một số cấu hình STT chưa sẵn sàng:")
            for error in errors:
                self.logger.warning(f"  - {error}")
    
    def _prepare_audio_for_fpt(self, audio_path: str) -> str:
        """Prepare audio file for FPT.AI STT (convert to required format if needed)"""
        try:
            from pydub import AudioSegment
            
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Convert to FPT.AI requirements: 16kHz, mono, WAV
            audio = audio.set_frame_rate(FPT_STT_CONFIG["rate"])
            audio = audio.set_channels(1)  # Mono
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Export as WAV
            audio.export(temp_path, format="wav")
            
            return temp_path
            
        except Exception as e:
            self.logger.warning(f"Không thể convert audio: {e}")
            return audio_path  # Return original file if conversion fails
    
    def _stt_fpt_ai(self, audio_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Perform STT using FPT.AI"""
        start_time = time.time()
        
        try:
            # Prepare audio file
            prepared_audio = self._prepare_audio_for_fpt(audio_path)
            
            # Prepare request
            headers = {
                'api-key': FPT_API_KEY
            }
            
            # Read audio file
            with open(prepared_audio, 'rb') as audio_file:
                files = {
                    'file': ('audio.wav', audio_file, 'audio/wav')
                }
                
                # Make request
                response = requests.post(
                    FPT_STT_CONFIG["url"],
                    headers=headers,
                    files=files,
                    timeout=TIMEOUT_CONFIG["stt_timeout"]
                )
            
            # Clean up temporary file if created
            if prepared_audio != audio_path and os.path.exists(prepared_audio):
                os.unlink(prepared_audio)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                
                if result.get('return') == 0:  # Success
                    text = result.get('hypotheses', [{}])[0].get('utterance', '')
                    
                    processing_time = time.time() - start_time
                    metrics = {
                        "service": "fpt_ai",
                        "processing_time": processing_time,
                        "status": "success",
                        "text_length": len(text),
                        "confidence": result.get('hypotheses', [{}])[0].get('confidence', 0.0)
                    }
                    
                    return True, text, metrics
                else:
                    error_msg = result.get('message', 'Unknown FPT.AI error')
                    processing_time = time.time() - start_time
                    metrics = {
                        "service": "fpt_ai",
                        "processing_time": processing_time,
                        "status": "error",
                        "error": error_msg
                    }
                    return False, None, metrics
            else:
                error_msg = f"FPT.AI HTTP {response.status_code}: {response.text}"
                processing_time = time.time() - start_time
                metrics = {
                    "service": "fpt_ai", 
                    "processing_time": processing_time,
                    "status": "error",
                    "error": error_msg
                }
                return False, None, metrics
                
        except Exception as e:
            processing_time = time.time() - start_time
            metrics = {
                "service": "fpt_ai",
                "processing_time": processing_time,
                "status": "error", 
                "error": str(e)
            }
            return False, None, metrics
    
    def _stt_openai_whisper(self, audio_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Perform STT using OpenAI Whisper"""
        start_time = time.time()
        
        try:
            if openai is None:
                raise Exception("OpenAI library không được cài đặt")
                
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            # Open audio file
            with open(audio_path, "rb") as audio_file:
                # Call Whisper API
                response = client.audio.transcriptions.create(
                    model=OPENAI_STT_CONFIG["model"],
                    file=audio_file,
                    language=OPENAI_STT_CONFIG["language"],
                    response_format=OPENAI_STT_CONFIG["response_format"]
                )
            
            # Extract text
            if isinstance(response, str):
                text = response
            else:
                text = response.text
            
            processing_time = time.time() - start_time
            metrics = {
                "service": "openai_whisper",
                "processing_time": processing_time,
                "status": "success",
                "text_length": len(text)
            }
            
            return True, text, metrics
            
        except Exception as e:
            processing_time = time.time() - start_time
            metrics = {
                "service": "openai_whisper",
                "processing_time": processing_time,
                "status": "error",
                "error": str(e)
            }
            return False, None, metrics
    
    def transcribe(self, audio_path: str, force_service: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio to text with automatic fallback
        
        Args:
            audio_path: Path to audio file
            force_service: Force specific service ("fpt" or "openai")
            
        Returns:
            Dict containing result, text, service_used, metrics, etc.
        """
        self.logger.info(f"Bắt đầu STT cho file: {Path(audio_path).name}")
        
        # Validate audio file
        is_valid, validation_msg = AudioUtils.validate_audio_file(audio_path)
        if not is_valid:
            return {
                "success": False,
                "error": validation_msg,
                "audio_path": audio_path
            }
        
        # Get audio info
        audio_info = AudioUtils.get_audio_info(audio_path)
        self.logger.info(f"Audio info: {audio_info.get('duration_seconds', 0):.1f}s, {audio_info.get('file_size_mb', 0):.1f}MB")
        
        # Start total timing
        self.metrics.start_timer("total_stt_time")
        
        # Try services based on preference or force
        services_to_try = []
        
        if force_service == "fpt":
            services_to_try = ["fpt"]
        elif force_service == "openai":
            services_to_try = ["openai"]
        else:
            # Default: try FPT.AI first, then OpenAI as backup
            services_to_try = ["fpt", "openai"]
        
        last_error = None
        all_metrics = []
        
        for service in services_to_try:
            self.logger.info(f"Thử STT service: {service.upper()}")
            
            if service == "fpt":
                success, text, metrics = self._stt_fpt_ai(audio_path)
            elif service == "openai":
                success, text, metrics = self._stt_openai_whisper(audio_path)
            else:
                continue
            
            all_metrics.append(metrics)
            
            if success:
                self.last_used_service = service
                total_time = self.metrics.end_timer("total_stt_time")
                
                self.logger.success(f"STT thành công với {service.upper()}")
                self.logger.info(f"Text nhận dạng: {text[:100]}{'...' if len(text) > 100 else ''}")
                
                return {
                    "success": True,
                    "text": text,
                    "service_used": service,
                    "audio_info": audio_info,
                    "processing_time": total_time,
                    "service_metrics": metrics,
                    "all_attempts": all_metrics
                }
            else:
                self.logger.warning(f"STT thất bại với {service.upper()}: {metrics.get('error', 'Unknown error')}")
                last_error = metrics.get('error', 'Unknown error')
        
        # All services failed
        total_time = self.metrics.end_timer("total_stt_time")
        
        self.logger.error("Tất cả STT services đều thất bại")
        
        return {
            "success": False,
            "error": last_error or "Tất cả STT services thất bại",
            "audio_info": audio_info,
            "processing_time": total_time,
            "all_attempts": all_metrics
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of available STT services"""
        status = {
            "fpt_ai": {
                "configured": FPT_API_KEY != "your_fpt_api_key_here",
                "available": FPT_API_KEY != "your_fpt_api_key_here"
            },
            "openai_whisper": {
                "configured": OPENAI_API_KEY != "your_openai_api_key_here" and openai is not None,
                "available": OPENAI_API_KEY != "your_openai_api_key_here" and openai is not None
            },
            "last_used_service": self.last_used_service
        }
        
        return status

def test_stt_module():
    """Test function for STT module"""
    print("=== TESTING STT MODULE ===")
    
    stt = STTModule()
    
    # Show service status
    status = stt.get_service_status()
    print(f"FPT.AI available: {status['fpt_ai']['available']}")
    print(f"OpenAI Whisper available: {status['openai_whisper']['available']}")
    
    # Test with a sample audio file (you need to provide one)
    sample_audio = "audio_samples/input/test.wav"
    
    if os.path.exists(sample_audio):
        result = stt.transcribe(sample_audio)
        
        if result["success"]:
            print(f"\n✅ STT Success!")
            print(f"Service used: {result['service_used']}")
            print(f"Text: {result['text']}")
            print(f"Processing time: {result['processing_time']:.3f}s")
        else:
            print(f"\n❌ STT Failed: {result['error']}")
    else:
        print(f"\n⚠️  Sample audio file not found: {sample_audio}")
        print("Please create audio_samples/input/ directory and add test.wav file")

if __name__ == "__main__":
    test_stt_module()
