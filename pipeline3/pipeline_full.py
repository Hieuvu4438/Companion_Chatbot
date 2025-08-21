"""
Full Pipeline Module - Pipeline 3
Kết hợp STT, LLM và TTS thành pipeline hoàn chỉnh
"""

import os
import sys
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stt_module import STTModule
from llm_module import LLMModule
from tts_module import TTSModule
from utils import MetricsCollector, Logger, print_header, print_step, save_metrics_to_file, SystemMetrics
from config import get_config_status

class FullPipeline:
    """Complete chatbot pipeline with STT -> LLM -> TTS"""
    
    def __init__(self):
        self.logger = Logger("pipeline")
        self.metrics = MetricsCollector()
        
        # Initialize modules
        self.logger.info("Khởi tạo các modules...")
        self.stt = STTModule()
        self.llm = LLMModule()
        self.tts = TTSModule()
        
        # Track conversation history
        self.conversation_history = []
        
        self.logger.success("Pipeline đã sẵn sàng!")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of all pipeline components"""
        stt_status = self.stt.get_service_status()
        llm_status = self.llm.get_model_info()
        tts_status = self.tts.get_service_status()
        config_status = get_config_status()
        
        return {
            "stt": stt_status,
            "llm": llm_status,
            "tts": tts_status,
            "config": config_status,
            "overall_ready": (
                any(s.get('available', False) for s in stt_status.values() if isinstance(s, dict)) and
                llm_status.get('available', False) and
                any(s.get('available', False) for s in tts_status.values() if isinstance(s, dict))
            )
        }
    
    def process_audio_input(
        self,
        audio_path: str,
        system_prompt_type: str = "elder_assistant",
        custom_system_prompt: Optional[str] = None,
        output_audio_path: Optional[str] = None,
        conversation_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process audio input through complete pipeline
        
        Args:
            audio_path: Path to input audio file
            system_prompt_type: Type of system prompt for LLM
            custom_system_prompt: Custom system prompt (overrides type)
            output_audio_path: Path for output audio (auto-generated if None)
            conversation_context: Whether to include conversation history
            
        Returns:
            Dict containing complete pipeline results and metrics
        """
        self.logger.info(f"Bắt đầu xử lý audio: {Path(audio_path).name}")
        
        # Start total pipeline timing
        self.metrics.start_timer("total_pipeline_time")
        pipeline_start_time = time.time()
        
        # Initialize result structure
        result = {
            "success": False,
            "input_audio": audio_path,
            "steps": {},
            "metrics": {},
            "errors": []
        }
        
        try:
            # Step 1: Speech-to-Text
            print_step(1, "Speech-to-Text (STT)")
            self.logger.info("Bắt đầu STT...")
            
            self.metrics.start_timer("stt_step_time")
            stt_result = self.stt.transcribe(audio_path)
            stt_time = self.metrics.end_timer("stt_step_time")
            
            result["steps"]["stt"] = stt_result
            result["metrics"]["stt_time"] = stt_time
            
            if not stt_result["success"]:
                error_msg = f"STT thất bại: {stt_result['error']}"
                self.logger.error(error_msg)
                result["errors"].append(error_msg)
                return result
            
            transcribed_text = stt_result["text"]
            result["transcribed_text"] = transcribed_text
            
            self.logger.success(f"STT thành công: {transcribed_text[:100]}{'...' if len(transcribed_text) > 100 else ''}")
            
            # Step 2: Large Language Model
            print_step(2, "Large Language Model (LLM)")
            self.logger.info("Bắt đầu LLM...")
            
            # Prepare input for LLM (with conversation context if enabled)
            llm_input = transcribed_text
            if conversation_context and self.conversation_history:
                # Add recent conversation history (last 3 exchanges)
                recent_history = self.conversation_history[-3:]
                context_text = "\n".join([
                    f"User: {exchange['user']}\nAssistant: {exchange['assistant']}"
                    for exchange in recent_history
                ])
                llm_input = f"Lịch sử hội thoại gần đây:\n{context_text}\n\nCâu hỏi hiện tại: {transcribed_text}"
            
            self.metrics.start_timer("llm_step_time")
            llm_result = self.llm.generate_response(
                llm_input,
                system_prompt_type=system_prompt_type,
                custom_system_prompt=custom_system_prompt
            )
            llm_time = self.metrics.end_timer("llm_step_time")
            
            result["steps"]["llm"] = llm_result
            result["metrics"]["llm_time"] = llm_time
            
            if not llm_result["success"]:
                error_msg = f"LLM thất bại: {llm_result['error']}"
                self.logger.error(error_msg)
                result["errors"].append(error_msg)
                return result
            
            response_text = llm_result["response"]
            result["response_text"] = response_text
            
            self.logger.success(f"LLM thành công: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
            
            # Step 3: Text-to-Speech
            print_step(3, "Text-to-Speech (TTS)")
            self.logger.info("Bắt đầu TTS...")
            
            # Generate output path if not provided
            if output_audio_path is None:
                os.makedirs("audio_samples/output", exist_ok=True)
                timestamp = int(time.time())
                output_audio_path = f"audio_samples/output/pipeline_output_{timestamp}.wav"
            
            self.metrics.start_timer("tts_step_time")
            tts_result = self.tts.synthesize(response_text, output_audio_path)
            tts_time = self.metrics.end_timer("tts_step_time")
            
            result["steps"]["tts"] = tts_result
            result["metrics"]["tts_time"] = tts_time
            
            if not tts_result["success"]:
                error_msg = f"TTS thất bại: {tts_result['error']}"
                self.logger.error(error_msg)
                result["errors"].append(error_msg)
                return result
            
            result["output_audio"] = tts_result["output_path"]
            
            self.logger.success(f"TTS thành công: {tts_result['output_path']}")
            
            # Pipeline completed successfully
            total_pipeline_time = self.metrics.end_timer("total_pipeline_time")
            result["success"] = True
            result["metrics"]["total_pipeline_time"] = total_pipeline_time
            
            # Add conversation to history
            if conversation_context:
                self.conversation_history.append({
                    "user": transcribed_text,
                    "assistant": response_text,
                    "timestamp": time.time()
                })
                
                # Keep only last 10 exchanges
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
            
            # Collect additional metrics
            self._collect_additional_metrics(result)
            
            self.logger.success(f"Pipeline hoàn thành trong {total_pipeline_time:.3f}s")
            
            return result
            
        except Exception as e:
            total_pipeline_time = self.metrics.end_timer("total_pipeline_time")
            error_msg = f"Lỗi pipeline: {str(e)}"
            self.logger.error(error_msg)
            
            result["errors"].append(error_msg)
            result["metrics"]["total_pipeline_time"] = total_pipeline_time
            
            return result
    
    def _collect_additional_metrics(self, result: Dict[str, Any]):
        """Collect additional performance metrics"""
        try:
            # System metrics
            system_info = SystemMetrics.get_system_info()
            result["metrics"]["system"] = system_info
            
            # Service usage metrics
            services_used = {
                "stt_service": result["steps"]["stt"].get("service_used"),
                "llm_service": "gemini",
                "tts_service": result["steps"]["tts"].get("service_used")
            }
            result["metrics"]["services_used"] = services_used
            
            # Text/Audio metrics
            if "transcribed_text" in result:
                result["metrics"]["input_text_length"] = len(result["transcribed_text"])
            
            if "response_text" in result:
                result["metrics"]["output_text_length"] = len(result["response_text"])
            
            # Audio file metrics
            if "output_audio" in result and os.path.exists(result["output_audio"]):
                audio_size = os.path.getsize(result["output_audio"])
                result["metrics"]["output_audio_size"] = audio_size
            
            # Efficiency metrics
            total_time = result["metrics"].get("total_pipeline_time", 0)
            if total_time > 0:
                steps_time = (
                    result["metrics"].get("stt_time", 0) +
                    result["metrics"].get("llm_time", 0) +
                    result["metrics"].get("tts_time", 0)
                )
                result["metrics"]["efficiency_ratio"] = steps_time / total_time
                result["metrics"]["overhead_time"] = total_time - steps_time
            
        except Exception as e:
            self.logger.warning(f"Không thể thu thập additional metrics: {e}")
    
    def process_text_input(
        self,
        text: str,
        system_prompt_type: str = "elder_assistant",
        output_audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process text input (skip STT step)
        
        Args:
            text: Input text
            system_prompt_type: Type of system prompt for LLM
            output_audio_path: Path for output audio
            
        Returns:
            Dict containing LLM + TTS results
        """
        self.logger.info(f"Xử lý text input: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        self.metrics.start_timer("text_pipeline_time")
        
        result = {
            "success": False,
            "input_text": text,
            "steps": {},
            "metrics": {},
            "errors": []
        }
        
        try:
            # Step 1: LLM
            print_step(1, "Large Language Model (LLM)")
            
            self.metrics.start_timer("llm_step_time")
            llm_result = self.llm.generate_response(text, system_prompt_type)
            llm_time = self.metrics.end_timer("llm_step_time")
            
            result["steps"]["llm"] = llm_result
            result["metrics"]["llm_time"] = llm_time
            
            if not llm_result["success"]:
                error_msg = f"LLM thất bại: {llm_result['error']}"
                result["errors"].append(error_msg)
                return result
            
            response_text = llm_result["response"]
            result["response_text"] = response_text
            
            # Step 2: TTS
            print_step(2, "Text-to-Speech (TTS)")
            
            if output_audio_path is None:
                os.makedirs("audio_samples/output", exist_ok=True)
                timestamp = int(time.time())
                output_audio_path = f"audio_samples/output/text_pipeline_output_{timestamp}.wav"
            
            self.metrics.start_timer("tts_step_time")
            tts_result = self.tts.synthesize(response_text, output_audio_path)
            tts_time = self.metrics.end_timer("tts_step_time")
            
            result["steps"]["tts"] = tts_result
            result["metrics"]["tts_time"] = tts_time
            
            if not tts_result["success"]:
                error_msg = f"TTS thất bại: {tts_result['error']}"
                result["errors"].append(error_msg)
                return result
            
            result["output_audio"] = tts_result["output_path"]
            result["success"] = True
            
            total_time = self.metrics.end_timer("text_pipeline_time")
            result["metrics"]["total_pipeline_time"] = total_time
            
            self.logger.success(f"Text pipeline hoàn thành trong {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            total_time = self.metrics.end_timer("text_pipeline_time")
            error_msg = f"Lỗi text pipeline: {str(e)}"
            self.logger.error(error_msg)
            
            result["errors"].append(error_msg)
            result["metrics"]["total_pipeline_time"] = total_time
            
            return result
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.logger.info("Đã xóa lịch sử hội thoại")
    
    def display_pipeline_status(self):
        """Display pipeline status"""
        status = self.get_pipeline_status()
        
        print_header("PIPELINE STATUS")
        
        print("🎤 STT Services:")
        for service, info in status["stt"].items():
            if isinstance(info, dict):
                available = "✅" if info.get('available', False) else "❌"
                print(f"  {service}: {available}")
        
        print("\n🧠 LLM Service:")
        llm_available = "✅" if status["llm"].get('available', False) else "❌"
        print(f"  Gemini: {llm_available}")
        
        print("\n🔊 TTS Services:")
        for service, info in status["tts"].items():
            if isinstance(info, dict):
                available = "✅" if info.get('available', False) else "❌"
                print(f"  {service}: {available}")
        
        print(f"\n🚀 Overall Ready: {'✅' if status['overall_ready'] else '❌'}")
        
        return status

def main():
    """Main function to run the pipeline interactively"""
    print_header("FULL PIPELINE - PIPELINE 3", 80)
    
    # Initialize pipeline
    pipeline = FullPipeline()
    
    # Display status
    status = pipeline.display_pipeline_status()
    
    if not status['overall_ready']:
        print("\n❌ Pipeline chưa sẵn sàng. Kiểm tra cấu hình API keys trong config.py")
        return
    
    print("\n🎉 Pipeline sẵn sàng!")
    print("\n📝 Hướng dẫn sử dụng:")
    print("  1. Đặt file audio trong audio_samples/input/")
    print("  2. Chạy pipeline với file audio")
    print("  3. Kết quả sẽ được lưu trong audio_samples/output/")
    
    # Interactive mode
    while True:
        print("\n" + "="*60)
        print("MENU:")
        print("1. Xử lý file audio (Full pipeline)")
        print("2. Xử lý text input (LLM + TTS)")
        print("3. Xem lịch sử hội thoại")
        print("4. Xóa lịch sử hội thoại")
        print("5. Xem trạng thái pipeline")
        print("0. Thoát")
        
        try:
            choice = input("\nChọn option (0-5): ").strip()
            
            if choice == "0":
                print("👋 Tạm biệt!")
                break
            elif choice == "1":
                # Audio processing
                audio_dir = Path("audio_samples/input")
                audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3"))
                
                if not audio_files:
                    print("❌ Không tìm thấy file audio trong audio_samples/input/")
                    continue
                
                print("\n📁 File audio có sẵn:")
                for i, file in enumerate(audio_files, 1):
                    print(f"  {i}. {file.name}")
                
                try:
                    file_choice = int(input("Chọn file (số): ")) - 1
                    if 0 <= file_choice < len(audio_files):
                        selected_file = audio_files[file_choice]
                        
                        print(f"\n🎤 Xử lý file: {selected_file.name}")
                        result = pipeline.process_audio_input(str(selected_file))
                        
                        if result["success"]:
                            print(f"\n✅ Pipeline thành công!")
                            print(f"📝 Transcribed: {result['transcribed_text']}")
                            print(f"🤖 Response: {result['response_text']}")
                            print(f"🔊 Audio output: {result['output_audio']}")
                            print(f"⏱️  Total time: {result['metrics']['total_pipeline_time']:.3f}s")
                            
                            # Save metrics
                            save_metrics_to_file(result["metrics"])
                        else:
                            print(f"\n❌ Pipeline thất bại:")
                            for error in result["errors"]:
                                print(f"  - {error}")
                    else:
                        print("❌ Lựa chọn không hợp lệ")
                except ValueError:
                    print("❌ Vui lòng nhập số")
                    
            elif choice == "2":
                # Text processing
                text = input("\n📝 Nhập text: ").strip()
                if text:
                    print(f"\n🤖 Xử lý text: {text[:50]}{'...' if len(text) > 50 else ''}")
                    result = pipeline.process_text_input(text)
                    
                    if result["success"]:
                        print(f"\n✅ Text pipeline thành công!")
                        print(f"🤖 Response: {result['response_text']}")
                        print(f"🔊 Audio output: {result['output_audio']}")
                        print(f"⏱️  Total time: {result['metrics']['total_pipeline_time']:.3f}s")
                    else:
                        print(f"\n❌ Text pipeline thất bại:")
                        for error in result["errors"]:
                            print(f"  - {error}")
                else:
                    print("❌ Text không được để trống")
                    
            elif choice == "3":
                # View conversation history
                history = pipeline.get_conversation_history()
                if history:
                    print(f"\n📜 Lịch sử hội thoại ({len(history)} exchanges):")
                    for i, exchange in enumerate(history, 1):
                        print(f"\n--- Exchange {i} ---")
                        print(f"User: {exchange['user']}")
                        print(f"Assistant: {exchange['assistant']}")
                else:
                    print("\n📜 Chưa có lịch sử hội thoại")
                    
            elif choice == "4":
                # Clear conversation history
                pipeline.clear_conversation_history()
                print("\n✅ Đã xóa lịch sử hội thoại")
                
            elif choice == "5":
                # Show pipeline status
                pipeline.display_pipeline_status()
                
            else:
                print("❌ Lựa chọn không hợp lệ")
                
        except KeyboardInterrupt:
            print("\n\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")

if __name__ == "__main__":
    main()
