"""
Azure Speech-to-Text Module for Pipeline 4
Sử dụng Azure Cognitive Services Speech SDK
"""

import os
import time
import json
from typing import Dict, Any, Optional
import azure.cognitiveservices.speech as speechsdk
from utils import MetricsCollector, Logger, print_error, print_success, print_warning, get_timestamp
from config import (
    AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_STT_CONFIG,
    TIMEOUT_CONFIG, RETRY_CONFIG, PERFORMANCE_CONFIG
)

class AzureSTTModule:
    """Azure Speech-to-Text Module"""
    
    def __init__(self):
        self.logger = Logger("azure_stt")
        self.metrics = MetricsCollector()
        self.speech_config = None
        self.is_configured = False
        
        # Initialize Azure Speech Config
        self._initialize_speech_config()
    
    def _initialize_speech_config(self):
        """Initialize Azure Speech configuration"""
        try:
            if AZURE_SPEECH_KEY == "your_azure_speech_key_here":
                self.logger.error("Azure Speech API key chưa được cấu hình")
                return False
            
            # Create speech config
            self.speech_config = speechsdk.SpeechConfig(
                subscription=AZURE_SPEECH_KEY, 
                region=AZURE_SPEECH_REGION
            )
            
            # Configure speech recognition settings
            self.speech_config.speech_recognition_language = AZURE_STT_CONFIG["language"]
            self.speech_config.enable_automatic_punctuation()
            
            # Set output format
            self.speech_config.output_format = speechsdk.OutputFormat.Detailed
            
            self.is_configured = True
            self.logger.success("Azure Speech STT đã được cấu hình thành công")
            return True
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo Azure Speech Config: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "azure_stt": {
                "configured": self.is_configured,
                "available": self.is_configured and AZURE_SPEECH_KEY != "your_azure_speech_key_here",
                "region": AZURE_SPEECH_REGION,
                "language": AZURE_STT_CONFIG["language"]
            }
        }
    
    def transcribe_from_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio from file"""
        start_time = time.time()
        
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "Azure STT chưa được cấu hình",
                    "processing_time": 0
                }
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                return {
                    "success": False,
                    "error": f"File không tồn tại: {audio_file_path}",
                    "processing_time": 0
                }
            
            self.logger.info(f"Bắt đầu transcribe file: {audio_file_path}")
            
            # Create audio config from file
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Perform recognition
            self.logger.info("Đang thực hiện nhận dạng giọng nói...")
            result = speech_recognizer.recognize_once_async().get()
            
            processing_time = time.time() - start_time
            
            # Process result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                self.logger.success(f"Nhận dạng thành công: {result.text}")
                
                # Try to get detailed results
                detailed_results = self._extract_detailed_results(result)
                
                return {
                    "success": True,
                    "text": result.text,
                    "confidence": detailed_results.get("confidence", 0.0),
                    "processing_time": processing_time,
                    "service": "azure_stt",
                    "language": AZURE_STT_CONFIG["language"],
                    "detailed_results": detailed_results,
                    "timestamp": get_timestamp()
                }
            
            elif result.reason == speechsdk.ResultReason.NoMatch:
                self.logger.warning("Không nhận dạng được giọng nói nào")
                return {
                    "success": False,
                    "error": "Không nhận dạng được giọng nói",
                    "processing_time": processing_time,
                    "service": "azure_stt"
                }
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_msg = f"Nhận dạng bị hủy: {cancellation_details.reason}"
                
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - Lỗi: {cancellation_details.error_details}"
                
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "processing_time": processing_time,
                    "service": "azure_stt"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Kết quả không mong muốn: {result.reason}",
                    "processing_time": processing_time,
                    "service": "azure_stt"
                }
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Lỗi trong quá trình transcribe: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "service": "azure_stt"
            }
    
    def _extract_detailed_results(self, result) -> Dict[str, Any]:
        """Extract detailed results from Azure response"""
        try:
            detailed = {}
            
            # Try to get confidence score
            if hasattr(result, 'json') and result.json:
                json_result = json.loads(result.json)
                
                # Extract confidence if available
                if 'NBest' in json_result and json_result['NBest']:
                    best_result = json_result['NBest'][0]
                    detailed['confidence'] = best_result.get('Confidence', 0.0)
                    
                    # Extract word-level details if available
                    if 'Words' in best_result:
                        words = []
                        for word_info in best_result['Words']:
                            words.append({
                                "word": word_info.get('Word', ''),
                                "confidence": word_info.get('Confidence', 0.0),
                                "offset": word_info.get('Offset', 0),
                                "duration": word_info.get('Duration', 0)
                            })
                        detailed['words'] = words
                
                detailed['display_text'] = json_result.get('DisplayText', '')
                detailed['lexical'] = json_result.get('Lexical', '')
            
            return detailed
            
        except Exception as e:
            self.logger.warning(f"Không thể trích xuất chi tiết kết quả: {e}")
            return {"confidence": 0.0}
    
    def transcribe_continuous(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio with continuous recognition (for longer audio)"""
        start_time = time.time()
        
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "Azure STT chưa được cấu hình",
                    "processing_time": 0
                }
            
            if not os.path.exists(audio_file_path):
                return {
                    "success": False,
                    "error": f"File không tồn tại: {audio_file_path}",
                    "processing_time": 0
                }
            
            self.logger.info(f"Bắt đầu continuous transcribe: {audio_file_path}")
            
            # Create audio config
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Storage for results
            all_results = []
            done = False
            
            def recognized_handler(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    all_results.append(evt.result.text)
            
            def session_stopped_handler(evt):
                nonlocal done
                done = True
            
            # Connect callbacks
            speech_recognizer.recognized.connect(recognized_handler)
            speech_recognizer.session_stopped.connect(session_stopped_handler)
            speech_recognizer.canceled.connect(session_stopped_handler)
            
            # Start continuous recognition
            speech_recognizer.start_continuous_recognition_async()
            
            # Wait for completion
            timeout = TIMEOUT_CONFIG.get("stt_timeout", 30)
            wait_time = 0
            while not done and wait_time < timeout:
                time.sleep(0.1)
                wait_time += 0.1
            
            # Stop recognition
            speech_recognizer.stop_continuous_recognition_async()
            
            processing_time = time.time() - start_time
            
            # Combine results
            combined_text = " ".join(all_results)
            
            if combined_text.strip():
                self.logger.success(f"Continuous recognition thành công: {len(all_results)} segments")
                return {
                    "success": True,
                    "text": combined_text,
                    "segments": all_results,
                    "processing_time": processing_time,
                    "service": "azure_stt_continuous",
                    "language": AZURE_STT_CONFIG["language"],
                    "timestamp": get_timestamp()
                }
            else:
                return {
                    "success": False,
                    "error": "Không nhận dạng được giọng nói nào",
                    "processing_time": processing_time,
                    "service": "azure_stt_continuous"
                }
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Lỗi continuous transcribe: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "service": "azure_stt_continuous"
            }
    
    def transcribe(self, audio_file_path: str, use_continuous: bool = False) -> Dict[str, Any]:
        """Main transcribe method with retry logic"""
        max_retries = RETRY_CONFIG.get("max_retries", 3)
        retry_delay = RETRY_CONFIG.get("retry_delay", 1.0)
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Transcribe attempt {attempt + 1}/{max_retries}")
                
                # Choose transcription method
                if use_continuous:
                    result = self.transcribe_continuous(audio_file_path)
                else:
                    result = self.transcribe_from_file(audio_file_path)
                
                # If successful, return immediately
                if result["success"]:
                    self.metrics.add_metric("transcribe_success", True)
                    self.metrics.add_metric("transcribe_attempts", attempt + 1)
                    self.metrics.add_metric("transcribe_time", result["processing_time"])
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
        self.metrics.add_metric("transcribe_success", False)
        self.metrics.add_metric("transcribe_attempts", max_retries)
        
        return {
            "success": False,
            "error": f"Transcribe thất bại sau {max_retries} lần thử",
            "processing_time": 0,
            "service": "azure_stt"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Azure Speech Service connection"""
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "Service chưa được cấu hình"
                }
            
            # Create a simple test recognizer
            test_config = speechsdk.SpeechConfig(
                subscription=AZURE_SPEECH_KEY,
                region=AZURE_SPEECH_REGION
            )
            
            # Test by creating recognizer (this validates credentials)
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=False)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=test_config,
                audio_config=audio_config
            )
            
            return {
                "success": True,
                "message": "Kết nối Azure Speech Service thành công",
                "region": AZURE_SPEECH_REGION,
                "language": AZURE_STT_CONFIG["language"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi kết nối Azure Speech Service: {str(e)}"
            }
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        # Common Vietnamese variants supported by Azure
        return [
            "vi-VN",  # Vietnamese (Vietnam)
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.get_all_metrics()
    
    def reset_metrics(self):
        """Reset metrics"""
        self.metrics.reset()

# Test function
def test_azure_stt():
    """Test Azure STT functionality"""
    print("=== TESTING AZURE STT MODULE ===")
    
    stt = AzureSTTModule()
    
    # Test connection
    print("\n1. Testing connection...")
    conn_result = stt.test_connection()
    if conn_result["success"]:
        print_success(conn_result["message"])
    else:
        print_error(conn_result["error"])
        return
    
    # Test service status
    print("\n2. Testing service status...")
    status = stt.get_service_status()
    print(f"Status: {status}")
    
    # Test with sample audio (if available)
    sample_audio = "audio_samples/input/sample.wav"
    if os.path.exists(sample_audio):
        print(f"\n3. Testing transcription with {sample_audio}...")
        result = stt.transcribe(sample_audio)
        
        if result["success"]:
            print_success(f"Transcription: {result['text']}")
            print(f"Processing time: {result['processing_time']:.3f}s")
            print(f"Confidence: {result.get('confidence', 'N/A')}")
        else:
            print_error(f"Transcription failed: {result['error']}")
    else:
        print_warning(f"Sample audio not found: {sample_audio}")
    
    # Show metrics
    print("\n4. Metrics:")
    stt.metrics.display_metrics("Azure STT Test Metrics")

if __name__ == "__main__":
    test_azure_stt()
