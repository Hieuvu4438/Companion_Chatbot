"""
VBEE AI Text-to-Speech Module for Pipeline 4
Sử dụng VBEE AI API cho giọng nói tiếng Việt tự nhiên
"""

import os
import time
import requests
import json
from typing import Dict, Any, Optional
from utils import MetricsCollector, Logger, print_error, print_success, print_warning, get_timestamp, format_file_size
from config import (
    VBEE_API_KEY, VBEE_TTS_CONFIG, VBEE_VOICE_OPTIONS,
    TIMEOUT_CONFIG, RETRY_CONFIG, PERFORMANCE_CONFIG, AUDIO_OUTPUT_DIR
)

class VBEETTSModule:
    """VBEE AI Text-to-Speech Module"""
    
    def __init__(self):
        self.logger = Logger("vbee_tts")
        self.metrics = MetricsCollector()
        self.is_configured = False
        self.session = requests.Session()
        
        # Setup session headers
        self._setup_session()
        
        # Validate configuration
        self._validate_config()
    
    def _setup_session(self):
        """Setup requests session with headers"""
        try:
            if VBEE_API_KEY != "your_vbee_api_key_here":
                self.session.headers.update({
                    'Authorization': f'Bearer {VBEE_API_KEY}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })
                self.logger.info("VBEE session headers configured")
            else:
                self.logger.warning("VBEE API key chưa được cấu hình")
        except Exception as e:
            self.logger.error(f"Lỗi setup session: {e}")
    
    def _validate_config(self):
        """Validate VBEE configuration"""
        try:
            if VBEE_API_KEY == "your_vbee_api_key_here":
                self.logger.error("VBEE API key chưa được cấu hình")
                return False
            
            # Check if voice exists
            selected_voice = VBEE_TTS_CONFIG["voice_code"]
            if selected_voice not in VBEE_VOICE_OPTIONS:
                self.logger.warning(f"Voice code {selected_voice} không có trong danh sách")
            
            self.is_configured = True
            self.logger.success("VBEE TTS đã được cấu hình thành công")
            return True
            
        except Exception as e:
            self.logger.error(f"Lỗi validate config: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "vbee_tts": {
                "configured": self.is_configured,
                "available": self.is_configured and VBEE_API_KEY != "your_vbee_api_key_here",
                "voice": VBEE_TTS_CONFIG["voice_code"],
                "voice_description": VBEE_VOICE_OPTIONS.get(VBEE_TTS_CONFIG["voice_code"], "Unknown"),
                "speed": VBEE_TTS_CONFIG["speed"],
                "format": VBEE_TTS_CONFIG["format"]
            }
        }
    
    def synthesize_text(self, text: str, output_path: Optional[str] = None, 
                       voice_code: Optional[str] = None) -> Dict[str, Any]:
        """Synthesize text to speech using VBEE API"""
        start_time = time.time()
        
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "VBEE TTS chưa được cấu hình",
                    "processing_time": 0
                }
            
            # Validate text
            if not text or not text.strip():
                return {
                    "success": False,
                    "error": "Text không được để trống",
                    "processing_time": 0
                }
            
            # Check text length (VBEE has limits)
            if len(text) > 5000:
                return {
                    "success": False,
                    "error": f"Text quá dài ({len(text)} ký tự). Tối đa 5000 ký tự",
                    "processing_time": 0
                }
            
            self.logger.info(f"Synthesizing text: {len(text)} characters")
            
            # Prepare output path
            if output_path is None:
                timestamp = int(time.time())
                output_path = os.path.join(AUDIO_OUTPUT_DIR, f"vbee_output_{timestamp}.wav")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Prepare request data
            request_data = {
                "text": text.strip(),
                "voice_code": voice_code or VBEE_TTS_CONFIG["voice_code"],
                "speed": VBEE_TTS_CONFIG["speed"],
                "without_filter": VBEE_TTS_CONFIG["without_filter"],
                "bit_rate": VBEE_TTS_CONFIG["bit_rate"],
                "format": VBEE_TTS_CONFIG["format"]
            }
            
            # Add callback URL if specified
            if VBEE_TTS_CONFIG.get("callback_url"):
                request_data["callback_url"] = VBEE_TTS_CONFIG["callback_url"]
            
            self.logger.info(f"Sending TTS request to VBEE API...")
            
            # Make API request
            timeout = TIMEOUT_CONFIG.get("tts_timeout", 30)
            response = self.session.post(
                VBEE_TTS_CONFIG["url"],
                json=request_data,
                timeout=timeout
            )
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if response_data.get("success"):
                # Get audio URL or data
                audio_url = response_data.get("audio_url")
                audio_data = response_data.get("audio_data")  # Base64 encoded
                
                if audio_url:
                    # Download audio from URL
                    audio_response = self.session.get(audio_url, timeout=timeout)
                    audio_response.raise_for_status()
                    
                    # Save audio file
                    with open(output_path, 'wb') as f:
                        f.write(audio_response.content)
                    
                elif audio_data:
                    # Decode base64 audio data
                    import base64
                    audio_bytes = base64.b64decode(audio_data)
                    
                    # Save audio file
                    with open(output_path, 'wb') as f:
                        f.write(audio_bytes)
                else:
                    return {
                        "success": False,
                        "error": "VBEE API không trả về audio data",
                        "processing_time": time.time() - start_time
                    }
                
                processing_time = time.time() - start_time
                
                # Verify file was created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    
                    self.logger.success(f"TTS thành công: {output_path} ({format_file_size(file_size)})")
                    
                    return {
                        "success": True,
                        "output_path": output_path,
                        "file_size": file_size,
                        "text_length": len(text),
                        "processing_time": processing_time,
                        "service": "vbee_tts",
                        "voice_code": voice_code or VBEE_TTS_CONFIG["voice_code"],
                        "timestamp": get_timestamp(),
                        "response_data": response_data
                    }
                else:
                    return {
                        "success": False,
                        "error": "File audio không được tạo",
                        "processing_time": processing_time
                    }
            else:
                error_msg = response_data.get("message", "VBEE API trả về lỗi")
                self.logger.error(f"VBEE API error: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "processing_time": time.time() - start_time,
                    "service": "vbee_tts"
                }
        
        except requests.exceptions.Timeout:
            processing_time = time.time() - start_time
            error_msg = f"VBEE API timeout sau {timeout}s"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "service": "vbee_tts"
            }
        
        except requests.exceptions.RequestException as e:
            processing_time = time.time() - start_time
            error_msg = f"VBEE API request error: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "service": "vbee_tts"
            }
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Lỗi TTS synthesis: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "service": "vbee_tts"
            }
    
    def synthesize_with_retry(self, text: str, output_path: Optional[str] = None, 
                             voice_code: Optional[str] = None) -> Dict[str, Any]:
        """Synthesize with retry logic"""
        max_retries = RETRY_CONFIG.get("max_retries", 3)
        retry_delay = RETRY_CONFIG.get("retry_delay", 1.0)
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"TTS attempt {attempt + 1}/{max_retries}")
                
                result = self.synthesize_text(text, output_path, voice_code)
                
                # If successful, return immediately
                if result["success"]:
                    self.metrics.add_metric("synthesize_success", True)
                    self.metrics.add_metric("synthesize_attempts", attempt + 1)
                    self.metrics.add_metric("synthesize_time", result["processing_time"])
                    return result
                
                # If not last attempt, wait before retry
                if attempt < max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_CONFIG.get("backoff_factor", 2.0)
            
            except Exception as e:
                self.logger.error(f"Exception in attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        # All attempts failed
        self.metrics.add_metric("synthesize_success", False)
        self.metrics.add_metric("synthesize_attempts", max_retries)
        
        return {
            "success": False,
            "error": f"TTS synthesis thất bại sau {max_retries} lần thử",
            "processing_time": 0,
            "service": "vbee_tts"
        }
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available voice options"""
        return VBEE_VOICE_OPTIONS.copy()
    
    def test_connection(self) -> Dict[str, Any]:
        """Test VBEE API connection"""
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "Service chưa được cấu hình"
                }
            
            # Test with short text
            test_text = "Xin chào, đây là test kết nối VBEE."
            
            # Create temporary output path
            test_output = os.path.join(AUDIO_OUTPUT_DIR, "vbee_connection_test.wav")
            
            result = self.synthesize_text(test_text, test_output)
            
            if result["success"]:
                # Clean up test file
                if os.path.exists(test_output):
                    os.remove(test_output)
                
                return {
                    "success": True,
                    "message": "Kết nối VBEE API thành công",
                    "voice": VBEE_TTS_CONFIG["voice_code"],
                    "test_duration": result["processing_time"]
                }
            else:
                return {
                    "success": False,
                    "error": f"VBEE test failed: {result['error']}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi test kết nối VBEE: {str(e)}"
            }
    
    def validate_text(self, text: str) -> Dict[str, Any]:
        """Validate text for TTS"""
        if not text or not text.strip():
            return {
                "valid": False,
                "error": "Text không được để trống"
            }
        
        if len(text) > 5000:
            return {
                "valid": False,
                "error": f"Text quá dài ({len(text)} ký tự). Tối đa 5000 ký tự"
            }
        
        return {
            "valid": True,
            "length": len(text),
            "estimated_duration": len(text) / 20  # Rough estimate: 20 chars per second
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.get_all_metrics()
    
    def reset_metrics(self):
        """Reset metrics"""
        self.metrics.reset()

# Test function
def test_vbee_tts():
    """Test VBEE TTS functionality"""
    print("=== TESTING VBEE TTS MODULE ===")
    
    tts = VBEETTSModule()
    
    # Test connection
    print("\n1. Testing connection...")
    conn_result = tts.test_connection()
    if conn_result["success"]:
        print_success(conn_result["message"])
        print(f"Voice: {conn_result['voice']}")
        print(f"Test duration: {conn_result['test_duration']:.3f}s")
    else:
        print_error(conn_result["error"])
        return
    
    # Test service status
    print("\n2. Testing service status...")
    status = tts.get_service_status()
    print(f"Status: {status}")
    
    # Test available voices
    print("\n3. Available voices:")
    voices = tts.get_available_voices()
    for voice_code, description in voices.items():
        current = " (CURRENT)" if voice_code == VBEE_TTS_CONFIG["voice_code"] else ""
        print(f"  - {voice_code}: {description}{current}")
    
    # Test text validation
    print("\n4. Testing text validation...")
    test_texts = [
        "Xin chào bác!",  # Valid short text
        "",  # Empty text
        "A" * 6000  # Too long text
    ]
    
    for i, test_text in enumerate(test_texts, 1):
        validation = tts.validate_text(test_text)
        print(f"  4.{i} Text length {len(test_text)}: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        if not validation['valid']:
            print(f"      Error: {validation['error']}")
        else:
            print(f"      Estimated duration: {validation['estimated_duration']:.1f}s")
    
    # Test TTS synthesis
    print("\n5. Testing TTS synthesis...")
    test_sentences = [
        "Chào bác! Cháu là trợ lý AI của bác.",
        "Hôm nay bác có khỏe không? Cháu mong bác luôn mạnh khỏe.",
        "Xa quê nhà có buồn không bác? Cháu hiểu lắm những ngày nhớ quê hương."
    ]
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n5.{i} Synthesizing: {sentence}")
        
        output_path = os.path.join(AUDIO_OUTPUT_DIR, f"test_vbee_{i}.wav")
        result = tts.synthesize_with_retry(sentence, output_path)
        
        if result["success"]:
            print_success(f"TTS successful: {result['output_path']}")
            print(f"      File size: {format_file_size(result['file_size'])}")
            print(f"      Processing time: {result['processing_time']:.3f}s")
            print(f"      Voice: {result['voice_code']}")
        else:
            print_error(f"TTS failed: {result['error']}")
    
    # Show metrics
    print("\n6. Metrics:")
    tts.metrics.display_metrics("VBEE TTS Test Metrics")

if __name__ == "__main__":
    test_vbee_tts()
