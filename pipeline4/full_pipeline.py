"""
Pipeline hoàn chỉnh STT + LLM + TTS - Pipeline 4
Azure Speech (STT) + Gemini (LLM) + VBEE (TTS)
Chatbot hỗ trợ người già với đầu vào giọng nói và đầu ra âm thanh
"""

import os
import time
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import modules
from stt_module import AzureSTTModule
from llm_module import GeminiLLMModule
from tts_module import VBEETTSModule
from utils import (
    MetricsCollector, Logger, print_header, print_step, print_success, 
    print_error, print_warning, print_info, ResponseTimeTracker,
    PerformanceMonitor, get_timestamp, format_file_size
)
from config import (
    PERFORMANCE_THRESHOLDS, PERFORMANCE_CONFIG, TIMEOUT_CONFIG,
    AUDIO_OUTPUT_DIR, get_config_status
)

class ElderCarePipeline:
    """Complete Elder Care Voice Pipeline"""
    
    def __init__(self):
        self.logger = Logger("elder_care_pipeline")
        self.metrics = MetricsCollector()
        self.time_tracker = ResponseTimeTracker()
        self.performance_monitor = PerformanceMonitor(PERFORMANCE_THRESHOLDS)
        
        # Initialize modules
        self.stt_module = None
        self.llm_module = None
        self.tts_module = None
        
        # Pipeline state
        self.is_initialized = False
        self.conversation_count = 0
        self.session_start_time = None
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize all pipeline modules"""
        try:
            self.logger.info("Khởi tạo Elder Care Pipeline...")
            
            # Check configuration first
            config_status = get_config_status()
            if not config_status["ready"]:
                self.logger.error("Cấu hình không đầy đủ:")
                for error in config_status["errors"]:
                    self.logger.error(f"  - {error}")
                return False
            
            # Initialize STT module
            print_step(1, "Khởi tạo Azure STT Module")
            self.stt_module = AzureSTTModule()
            if not self.stt_module.is_configured:
                self.logger.error("Không thể khởi tạo STT module")
                return False
            print_success("Azure STT Module sẵn sàng")
            
            # Initialize LLM module
            print_step(2, "Khởi tạo Gemini LLM Module")
            self.llm_module = GeminiLLMModule()
            if not self.llm_module.is_configured:
                self.logger.error("Không thể khởi tạo LLM module")
                return False
            print_success("Gemini LLM Module sẵn sàng")
            
            # Initialize TTS module
            print_step(3, "Khởi tạo VBEE TTS Module")
            self.tts_module = VBEETTSModule()
            if not self.tts_module.is_configured:
                self.logger.error("Không thể khởi tạo TTS module")
                return False
            print_success("VBEE TTS Module sẵn sàng")
            
            self.is_initialized = True
            self.session_start_time = time.time()
            
            self.logger.success("Elder Care Pipeline khởi tạo thành công!")
            return True
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo pipeline: {e}")
            return False
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        status = {
            "pipeline_initialized": self.is_initialized,
            "session_start_time": self.session_start_time,
            "conversation_count": self.conversation_count,
            "modules": {}
        }
        
        if self.stt_module:
            status["modules"]["stt"] = self.stt_module.get_service_status()
        
        if self.llm_module:
            status["modules"]["llm"] = self.llm_module.get_service_status()
        
        if self.tts_module:
            status["modules"]["tts"] = self.tts_module.get_service_status()
        
        return status
    
    def process_voice_conversation(self, audio_file_path: str, 
                                  output_audio_path: Optional[str] = None,
                                  use_continuous_stt: bool = False) -> Dict[str, Any]:
        """
        Xử lý hoàn chỉnh cuộc hội thoại giọng nói
        Input: File audio giọng nói
        Output: File audio phản hồi + transcript + metrics
        """
        
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Pipeline chưa được khởi tạo",
                "pipeline_time": 0
            }
        
        # Start pipeline timer
        pipeline_start = time.time()
        self.metrics.start_timer("pipeline_total_time")
        
        self.conversation_count += 1
        conversation_id = f"conv_{self.conversation_count}_{int(time.time())}"
        
        self.logger.info(f"Bắt đầu xử lý conversation {conversation_id}")
        
        result = {
            "success": False,
            "conversation_id": conversation_id,
            "steps": {},
            "error": None,
            "pipeline_time": 0,
            "timestamp": get_timestamp()
        }
        
        try:
            # Step 1: Speech-to-Text
            print_step(1, f"STT - Nhận dạng giọng nói từ {Path(audio_file_path).name}")
            
            self.metrics.start_timer("stt_time")
            stt_result = self.stt_module.transcribe(audio_file_path, use_continuous_stt)
            stt_time = self.metrics.end_timer("stt_time")
            
            self.time_tracker.add_time("stt", stt_time)
            self.performance_monitor.check_performance("stt", stt_time)
            
            result["steps"]["stt"] = stt_result
            
            if not stt_result["success"]:
                result["error"] = f"STT failed: {stt_result['error']}"
                self.logger.error(result["error"])
                return result
            
            user_text = stt_result["text"]
            print_success(f"STT thành công: '{user_text}'")
            print_info(f"STT time: {stt_time:.3f}s, Confidence: {stt_result.get('confidence', 'N/A')}")
            
            # Step 2: LLM - Generate Response
            print_step(2, "LLM - Tạo phản hồi từ Gemini")
            
            self.metrics.start_timer("llm_time")
            llm_result = self.llm_module.chat_with_context(user_text)
            llm_time = self.metrics.end_timer("llm_time")
            
            self.time_tracker.add_time("llm", llm_time)
            self.performance_monitor.check_performance("llm", llm_time)
            
            result["steps"]["llm"] = llm_result
            
            if not llm_result["success"]:
                result["error"] = f"LLM failed: {llm_result['error']}"
                self.logger.error(result["error"])
                return result
            
            assistant_text = llm_result["response"]
            print_success(f"LLM thành công: '{assistant_text[:100]}...'")
            print_info(f"LLM time: {llm_time:.3f}s, Length: {len(assistant_text)} chars")
            
            # Step 3: Text-to-Speech
            print_step(3, "TTS - Chuyển phản hồi thành giọng nói")
            
            # Prepare output path
            if output_audio_path is None:
                output_audio_path = os.path.join(
                    AUDIO_OUTPUT_DIR, 
                    f"response_{conversation_id}.wav"
                )
            
            self.metrics.start_timer("tts_time")
            tts_result = self.tts_module.synthesize_with_retry(assistant_text, output_audio_path)
            tts_time = self.metrics.end_timer("tts_time")
            
            self.time_tracker.add_time("tts", tts_time)
            self.performance_monitor.check_performance("tts", tts_time)
            
            result["steps"]["tts"] = tts_result
            
            if not tts_result["success"]:
                result["error"] = f"TTS failed: {tts_result['error']}"
                self.logger.error(result["error"])
                return result
            
            print_success(f"TTS thành công: {tts_result['output_path']}")
            print_info(f"TTS time: {tts_time:.3f}s, File size: {format_file_size(tts_result['file_size'])}")
            
            # Calculate total pipeline time
            pipeline_time = self.metrics.end_timer("pipeline_total_time")
            self.time_tracker.add_time("total", pipeline_time)
            self.performance_monitor.check_performance("total", pipeline_time)
            
            # Success!
            result.update({
                "success": True,
                "user_text": user_text,
                "assistant_text": assistant_text,
                "output_audio_path": tts_result["output_path"],
                "pipeline_time": pipeline_time,
                "step_times": {
                    "stt": stt_time,
                    "llm": llm_time,
                    "tts": tts_time
                }
            })
            
            # Add comprehensive metrics
            self.metrics.add_metric("conversation_success", True)
            self.metrics.add_metric("user_text_length", len(user_text))
            self.metrics.add_metric("assistant_text_length", len(assistant_text))
            self.metrics.add_metric("total_pipeline_time", pipeline_time)
            
            self.logger.success(f"Pipeline hoàn thành conversation {conversation_id} trong {pipeline_time:.3f}s")
            
            # Auto-play audio if possible (commented out for server environment)
            # self._play_audio_output(tts_result["output_path"])
            
            return result
            
        except Exception as e:
            pipeline_time = time.time() - pipeline_start
            error_msg = f"Lỗi trong pipeline: {str(e)}"
            
            result.update({
                "error": error_msg,
                "pipeline_time": pipeline_time
            })
            
            self.logger.error(error_msg)
            self.metrics.add_metric("conversation_success", False)
            
            return result
    
    def _play_audio_output(self, audio_path: str):
        """Play audio output (for local testing)"""
        try:
            # This would require additional audio libraries
            # For now, just log the path
            self.logger.info(f"🔊 Audio output ready: {audio_path}")
            print_info(f"🔊 Phát audio: {Path(audio_path).name}")
        except Exception as e:
            self.logger.warning(f"Không thể phát audio: {e}")
    
    def process_text_conversation(self, user_text: str, 
                                 output_audio_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Xử lý cuộc hội thoại từ text input (bỏ qua STT)
        Useful for testing LLM + TTS
        """
        
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Pipeline chưa được khởi tạo",
                "pipeline_time": 0
            }
        
        pipeline_start = time.time()
        self.conversation_count += 1
        conversation_id = f"text_conv_{self.conversation_count}_{int(time.time())}"
        
        self.logger.info(f"Xử lý text conversation {conversation_id}")
        
        result = {
            "success": False,
            "conversation_id": conversation_id,
            "steps": {},
            "error": None,
            "pipeline_time": 0,
            "timestamp": get_timestamp()
        }
        
        try:
            # Skip STT, go directly to LLM
            print_step(1, f"LLM - Xử lý text: '{user_text[:50]}...'")
            
            llm_result = self.llm_module.chat_with_context(user_text)
            result["steps"]["llm"] = llm_result
            
            if not llm_result["success"]:
                result["error"] = f"LLM failed: {llm_result['error']}"
                return result
            
            assistant_text = llm_result["response"]
            print_success(f"LLM response: '{assistant_text[:100]}...'")
            
            # TTS
            print_step(2, "TTS - Chuyển phản hồi thành giọng nói")
            
            if output_audio_path is None:
                output_audio_path = os.path.join(
                    AUDIO_OUTPUT_DIR, 
                    f"text_response_{conversation_id}.wav"
                )
            
            tts_result = self.tts_module.synthesize_with_retry(assistant_text, output_audio_path)
            result["steps"]["tts"] = tts_result
            
            if not tts_result["success"]:
                result["error"] = f"TTS failed: {tts_result['error']}"
                return result
            
            pipeline_time = time.time() - pipeline_start
            
            result.update({
                "success": True,
                "user_text": user_text,
                "assistant_text": assistant_text,
                "output_audio_path": tts_result["output_path"],
                "pipeline_time": pipeline_time
            })
            
            self.logger.success(f"Text pipeline hoàn thành trong {pipeline_time:.3f}s")
            return result
            
        except Exception as e:
            pipeline_time = time.time() - pipeline_start
            result.update({
                "error": f"Lỗi text pipeline: {str(e)}",
                "pipeline_time": pipeline_time
            })
            return result
    
    def test_pipeline_connectivity(self) -> Dict[str, Any]:
        """Test connectivity of all pipeline components"""
        print_header("KIỂM TRA KẾT NỐI PIPELINE")
        
        test_results = {
            "stt_connection": False,
            "llm_connection": False,
            "tts_connection": False,
            "overall_status": False
        }
        
        # Test STT
        print_step(1, "Testing Azure STT connection")
        if self.stt_module:
            stt_test = self.stt_module.test_connection()
            test_results["stt_connection"] = stt_test["success"]
            if stt_test["success"]:
                print_success(stt_test["message"])
            else:
                print_error(stt_test["error"])
        
        # Test LLM
        print_step(2, "Testing Gemini LLM connection")
        if self.llm_module:
            llm_test = self.llm_module.test_connection()
            test_results["llm_connection"] = llm_test["success"]
            if llm_test["success"]:
                print_success(llm_test["message"])
            else:
                print_error(llm_test["error"])
        
        # Test TTS
        print_step(3, "Testing VBEE TTS connection")
        if self.tts_module:
            tts_test = self.tts_module.test_connection()
            test_results["tts_connection"] = tts_test["success"]
            if tts_test["success"]:
                print_success(tts_test["message"])
            else:
                print_error(tts_test["error"])
        
        # Overall status
        test_results["overall_status"] = all([
            test_results["stt_connection"],
            test_results["llm_connection"],
            test_results["tts_connection"]
        ])
        
        if test_results["overall_status"]:
            print_success("✅ Tất cả modules đều kết nối thành công!")
        else:
            print_warning("⚠️  Một số modules có vấn đề kết nối")
        
        return test_results
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline metrics"""
        metrics = {
            "pipeline_info": {
                "session_duration": time.time() - self.session_start_time if self.session_start_time else 0,
                "conversation_count": self.conversation_count,
                "is_initialized": self.is_initialized
            },
            "response_times": {},
            "performance_alerts": self.performance_monitor.get_alerts(),
            "module_metrics": {}
        }
        
        # Get response time statistics
        for component in ["stt", "llm", "tts", "total"]:
            metrics["response_times"][component] = self.time_tracker.get_stats(component)
        
        # Get module-specific metrics
        if self.stt_module:
            metrics["module_metrics"]["stt"] = self.stt_module.get_metrics()
        
        if self.llm_module:
            metrics["module_metrics"]["llm"] = self.llm_module.get_metrics()
        
        if self.tts_module:
            metrics["module_metrics"]["tts"] = self.tts_module.get_metrics()
        
        # Get pipeline metrics
        metrics["pipeline_metrics"] = self.metrics.get_all_metrics()
        
        return metrics
    
    def save_conversation_log(self, conversation_result: Dict[str, Any], 
                             log_file: Optional[str] = None):
        """Save conversation result to log file"""
        try:
            if log_file is None:
                log_file = os.path.join("logs", f"conversations_{datetime.now().strftime('%Y%m%d')}.json")
            
            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Load existing conversations or create new list
            conversations = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        conversations = json.load(f)
                except:
                    conversations = []
            
            # Add new conversation
            conversations.append(conversation_result)
            
            # Save back to file
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Conversation log saved to {log_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving conversation log: {e}")
    
    def reset_session(self):
        """Reset pipeline session"""
        self.conversation_count = 0
        self.session_start_time = time.time()
        
        # Reset metrics
        self.metrics.reset()
        self.performance_monitor.clear_alerts()
        
        # Reset module states
        if self.llm_module:
            self.llm_module.clear_conversation_history()
        
        self.logger.info("Pipeline session reset")
    
    def shutdown(self):
        """Graceful shutdown of pipeline"""
        self.logger.info("Shutting down Elder Care Pipeline...")
        
        # Save final metrics if enabled
        if PERFORMANCE_CONFIG.get("enable_metrics", True):
            try:
                metrics_file = PERFORMANCE_CONFIG.get("metrics_file", "final_metrics.json")
                final_metrics = self.get_comprehensive_metrics()
                
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(final_metrics, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"Final metrics saved to {metrics_file}")
            except Exception as e:
                self.logger.error(f"Error saving final metrics: {e}")
        
        self.is_initialized = False
        self.logger.success("Pipeline shutdown complete")

# Test functions
def test_pipeline_basic():
    """Basic pipeline test"""
    print_header("BASIC PIPELINE TEST", 80)
    
    # Initialize pipeline
    pipeline = ElderCarePipeline()
    
    if not pipeline.is_initialized:
        print_error("Pipeline initialization failed")
        return False
    
    # Test connectivity
    connectivity = pipeline.test_pipeline_connectivity()
    if not connectivity["overall_status"]:
        print_error("Connectivity test failed")
        return False
    
    # Test with sample text (skip STT for basic test)
    print_step(1, "Testing text conversation")
    test_text = "Xin chào! Bác có khỏe không?"
    
    result = pipeline.process_text_conversation(test_text)
    
    if result["success"]:
        print_success(f"Text conversation successful!")
        print_info(f"User: {result['user_text']}")
        print_info(f"Assistant: {result['assistant_text'][:100]}...")
        print_info(f"Audio output: {result['output_audio_path']}")
        print_info(f"Pipeline time: {result['pipeline_time']:.3f}s")
        return True
    else:
        print_error(f"Text conversation failed: {result['error']}")
        return False

if __name__ == "__main__":
    test_pipeline_basic()
