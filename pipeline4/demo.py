"""
Demo thực tế Pipeline 4 - Elder Care Voice Assistant
Chạy chatbot thực tế cho người cao tuổi với giao diện đơn giản
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from full_pipeline import ElderCarePipeline
from utils import (
    MetricsCollector, Logger, print_header, print_step, print_success, 
    print_error, print_warning, print_info, get_timestamp
)
from config import get_config_status, validate_config

class ElderCareDemo:
    """Demo class for Elder Care Voice Assistant"""
    
    def __init__(self):
        self.pipeline = None
        self.logger = Logger("elder_care_demo")
        self.conversation_count = 0
        self.start_time = time.time()
        
    def initialize(self):
        """Initialize the demo"""
        print_header("ELDER CARE VOICE ASSISTANT - KHỞI ĐỘNG", 80)
        
        # Check configuration
        print_step(1, "Kiểm tra cấu hình hệ thống")
        config_errors = validate_config()
        
        if config_errors:
            print_error("Lỗi cấu hình:")
            for error in config_errors:
                print(f"  ❌ {error}")
            return False
        
        print_success("Cấu hình hệ thống OK")
        
        # Initialize pipeline
        print_step(2, "Khởi tạo voice pipeline")
        try:
            self.pipeline = ElderCarePipeline()
            
            if self.pipeline.is_initialized:
                print_success("Pipeline khởi tạo thành công!")
                
                # Test connectivity
                print_step(3, "Kiểm tra kết nối services")
                connectivity = self.pipeline.test_pipeline_connectivity()
                
                if connectivity["overall_status"]:
                    print_success("Tất cả services kết nối OK")
                    return True
                else:
                    print_warning("Một số services có vấn đề, demo có thể hoạt động hạn chế")
                    return True
            else:
                print_error("Pipeline khởi tạo thất bại")
                return False
                
        except Exception as e:
            print_error(f"Lỗi khởi tạo: {e}")
            return False
    
    def show_main_menu(self):
        """Show main menu options"""
        print("\n" + "="*60)
        print("🏠 ELDER CARE VOICE ASSISTANT - MENU CHÍNH")
        print("="*60)
        print("1. 🎤 Voice Conversation (Trò chuyện bằng giọng nói)")
        print("2. 💬 Text Conversation (Trò chuyện bằng text)")
        print("3. 📊 View Statistics (Xem thống kê)")
        print("4. 🎵 Play Recent Audio (Nghe lại audio gần nhất)")
        print("5. 📁 Show Audio Files (Xem file audio có sẵn)")
        print("6. ⚙️  System Status (Trạng thái hệ thống)")
        print("7. 📝 Conversation History (Lịch sử trò chuyện)")
        print("0. 🚪 Exit (Thoát)")
        print("="*60)
    
    def handle_voice_conversation(self):
        """Handle voice conversation"""
        print_header("VOICE CONVERSATION - TRẢI NGHIỆM GIỌNG NÓI")
        
        # Get available audio files
        audio_dir = Path("audio_samples/input")
        audio_files = []
        
        if audio_dir.exists():
            for ext in ['.wav', '.mp3', '.m4a', '.flac']:
                audio_files.extend(audio_dir.glob(f"*{ext}"))
        
        if not audio_files:
            print_warning("Không tìm thấy file audio trong audio_samples/input/")
            print_info("Hướng dẫn:")
            print("  1. Ghi âm giọng nói của bạn (định dạng .wav, .mp3, .m4a)")
            print("  2. Đặt file vào thư mục audio_samples/input/")
            print("  3. Quay lại menu này để test")
            return
        
        print(f"📁 Tìm thấy {len(audio_files)} file audio:")
        for i, audio_file in enumerate(audio_files, 1):
            print(f"  {i}. {audio_file.name}")
        
        try:
            choice = input("\n👤 Chọn file audio để test (nhập số): ").strip()
            
            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(audio_files):
                print_error("Lựa chọn không hợp lệ")
                return
            
            selected_file = audio_files[int(choice) - 1]
            
            print(f"\n🎤 Đang xử lý: {selected_file.name}")
            print("⏳ Vui lòng đợi...")
            
            start_time = time.time()
            result = self.pipeline.process_voice_conversation(str(selected_file))
            processing_time = time.time() - start_time
            
            if result["success"]:
                self.conversation_count += 1
                
                print_success("Voice conversation thành công!")
                print(f"\n{'='*60}")
                print(f"👤 Bạn nói: \"{result['user_text']}\"")
                print(f"🤖 Trợ lý: \"{result['assistant_text']}\"")
                print(f"{'='*60}")
                print(f"⏱️  Thời gian xử lý: {result['pipeline_time']:.2f}s")
                print(f"🎵 Audio trả lời: {Path(result['output_audio_path']).name}")
                
                # Offer to play audio
                play_choice = input("\n🔊 Bạn có muốn phát audio trả lời? (y/n): ").strip().lower()
                if play_choice == 'y':
                    self.play_audio_file(result['output_audio_path'])
                
                # Save conversation
                self.save_conversation_summary(result)
                
            else:
                print_error(f"Voice conversation thất bại: {result.get('error', 'Unknown error')}")
                
                # Show step details if available
                if "steps" in result:
                    print_info("Chi tiết các bước:")
                    for step_name, step_result in result["steps"].items():
                        status = "✅" if step_result.get("success") else "❌"
                        print(f"  {status} {step_name.upper()}: {step_result.get('message', 'No details')}")
                
        except KeyboardInterrupt:
            print_warning("\nĐã hủy voice conversation")
        except Exception as e:
            print_error(f"Lỗi không mong đợi: {e}")
    
    def handle_text_conversation(self):
        """Handle text conversation"""
        print_header("TEXT CONVERSATION - TRẢI NGHIỆM NHẮN TIN")
        
        print_info("💡 Gợi ý câu hỏi:")
        suggestions = [
            "Xin chào! Hôm nay bác có khỏe không?",
            "Bác cảm thấy mệt mỏi và đau đầu",
            "Bác muốn nghe kể chuyện để giải trí",
            "Hướng dẫn bác cách gọi điện cho con cháu",
            "Bác cảm thấy cô đơn và buồn",
            "Nhắc bác uống thuốc"
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        try:
            user_input = input("\n👤 Nhập tin nhắn của bạn (hoặc 'quit' để quay lại): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                return
            
            if not user_input:
                print_warning("Tin nhắn không được để trống")
                return
            
            print(f"\n💬 Đang xử lý: \"{user_input}\"")
            print("⏳ Vui lòng đợi...")
            
            start_time = time.time()
            result = self.pipeline.process_text_conversation(user_input)
            processing_time = time.time() - start_time
            
            if result["success"]:
                self.conversation_count += 1
                
                print_success("Text conversation thành công!")
                print(f"\n{'='*60}")
                print(f"👤 Bạn: {result['user_text']}")
                print(f"🤖 Trợ lý: {result['assistant_text']}")
                print(f"{'='*60}")
                print(f"⏱️  Thời gian xử lý: {result['pipeline_time']:.2f}s")
                print(f"🎵 Audio trả lời: {Path(result['output_audio_path']).name}")
                
                # Offer to play audio
                play_choice = input("\n🔊 Bạn có muốn nghe audio trả lời? (y/n): ").strip().lower()
                if play_choice == 'y':
                    self.play_audio_file(result['output_audio_path'])
                
                # Save conversation
                self.save_conversation_summary(result)
                
                # Continue conversation option
                continue_choice = input("\n💬 Tiếp tục trò chuyện? (y/n): ").strip().lower()
                if continue_choice == 'y':
                    self.handle_text_conversation()
                
            else:
                print_error(f"Text conversation thất bại: {result.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            print_warning("\nĐã hủy text conversation")
        except Exception as e:
            print_error(f"Lỗi không mong đợi: {e}")
    
    def show_statistics(self):
        """Show system statistics"""
        print_header("THỐNG KÊ HỆ THỐNG")
        
        # Session statistics
        session_duration = time.time() - self.start_time
        print("📊 Thống kê phiên làm việc:")
        print(f"  🕐 Thời gian hoạt động: {session_duration:.1f}s ({session_duration/60:.1f} phút)")
        print(f"  💬 Số cuộc trò chuyện: {self.conversation_count}")
        print(f"  ⚡ Trung bình/cuộc: {session_duration/max(1, self.conversation_count):.1f}s")
        
        # Pipeline statistics
        if self.pipeline:
            pipeline_status = self.pipeline.get_pipeline_status()
            print(f"\n🔧 Thống kê pipeline:")
            print(f"  📈 Total conversations: {pipeline_status['conversation_count']}")
            print(f"  ✅ Pipeline initialized: {pipeline_status['pipeline_initialized']}")
            
            # Get comprehensive metrics
            try:
                metrics = self.pipeline.get_comprehensive_metrics()
                
                print(f"\n⏱️ Response time statistics:")
                response_times = metrics["response_times"]
                for component, stats in response_times.items():
                    if stats["count"] > 0:
                        print(f"  {component.upper()}:")
                        print(f"    - Calls: {stats['count']}")
                        print(f"    - Avg: {stats['avg']:.3f}s")
                        print(f"    - Best: {stats['min']:.3f}s")
                        print(f"    - Worst: {stats['max']:.3f}s")
                
                # Performance alerts
                alerts = metrics.get("performance_alerts", [])
                if alerts:
                    print(f"\n⚠️  Performance alerts ({len(alerts)}):")
                    for alert in alerts[-3:]:  # Show last 3 alerts
                        print(f"  - {alert['component']}: {alert['response_time']:.3f}s")
                
            except Exception as e:
                print_warning(f"Cannot get detailed metrics: {e}")
        
        # File statistics
        output_dir = Path("audio_samples/output")
        if output_dir.exists():
            output_files = list(output_dir.glob("*.wav"))
            total_size = sum(f.stat().st_size for f in output_files) / (1024*1024)  # MB
            print(f"\n📁 File statistics:")
            print(f"  🎵 Audio files generated: {len(output_files)}")
            print(f"  💾 Total audio size: {total_size:.2f}MB")
    
    def play_recent_audio(self):
        """Play most recent generated audio"""
        print_header("PHÁT AUDIO GẦN NHẤT")
        
        output_dir = Path("audio_samples/output")
        if not output_dir.exists():
            print_warning("Thư mục output chưa tồn tại")
            return
        
        # Get all audio files sorted by modification time
        audio_files = []
        for ext in ['.wav', '.mp3', '.m4a']:
            audio_files.extend(output_dir.glob(f"*{ext}"))
        
        if not audio_files:
            print_warning("Không có file audio nào trong thư mục output")
            return
        
        # Sort by modification time (newest first)
        audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print(f"📁 Top 5 file audio gần nhất:")
        for i, audio_file in enumerate(audio_files[:5], 1):
            mod_time = datetime.fromtimestamp(audio_file.stat().st_mtime)
            file_size = audio_file.stat().st_size / 1024  # KB
            print(f"  {i}. {audio_file.name}")
            print(f"     ⏰ {mod_time.strftime('%H:%M:%S')} - 📦 {file_size:.1f}KB")
        
        try:
            choice = input("\n🔊 Chọn file để phát (nhập số, Enter để phát file mới nhất): ").strip()
            
            if not choice:
                selected_file = audio_files[0]
            elif choice.isdigit() and 1 <= int(choice) <= min(5, len(audio_files)):
                selected_file = audio_files[int(choice) - 1]
            else:
                print_error("Lựa chọn không hợp lệ")
                return
            
            self.play_audio_file(str(selected_file))
            
        except Exception as e:
            print_error(f"Lỗi phát audio: {e}")
    
    def show_audio_files(self):
        """Show available audio files"""
        print_header("DANH SÁCH FILE AUDIO")
        
        # Input files
        input_dir = Path("audio_samples/input")
        print("📥 File audio đầu vào:")
        if input_dir.exists():
            input_files = []
            for ext in ['.wav', '.mp3', '.m4a', '.flac']:
                input_files.extend(input_dir.glob(f"*{ext}"))
            
            if input_files:
                for i, audio_file in enumerate(input_files, 1):
                    file_size = audio_file.stat().st_size / 1024  # KB
                    print(f"  {i}. {audio_file.name} ({file_size:.1f}KB)")
            else:
                print("  📭 Không có file audio nào")
        else:
            print("  📭 Thư mục input chưa tồn tại")
        
        # Output files
        output_dir = Path("audio_samples/output")
        print("\n📤 File audio đầu ra:")
        if output_dir.exists():
            output_files = []
            for ext in ['.wav', '.mp3', '.m4a']:
                output_files.extend(output_dir.glob(f"*{ext}"))
            
            if output_files:
                # Sort by modification time
                output_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for i, audio_file in enumerate(output_files[:10], 1):  # Show top 10
                    mod_time = datetime.fromtimestamp(audio_file.stat().st_mtime)
                    file_size = audio_file.stat().st_size / 1024  # KB
                    print(f"  {i}. {audio_file.name} ({file_size:.1f}KB)")
                    print(f"     ⏰ {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if len(output_files) > 10:
                    print(f"  ... và {len(output_files) - 10} file khác")
            else:
                print("  📭 Chưa có file audio nào được tạo")
        else:
            print("  📭 Thư mục output chưa tồn tại")
    
    def show_system_status(self):
        """Show system status"""
        print_header("TRẠNG THÁI HỆ THỐNG")
        
        # Configuration status
        config_status = get_config_status()
        print("⚙️  Trạng thái cấu hình:")
        print(f"  🔑 Azure Speech: {'✅ OK' if config_status['azure_configured'] else '❌ Missing'}")
        print(f"  🔑 Gemini API: {'✅ OK' if config_status['gemini_configured'] else '❌ Missing'}")
        print(f"  🔑 VBEE API: {'✅ OK' if config_status['vbee_configured'] else '❌ Missing'}")
        
        # Pipeline status
        if self.pipeline:
            print(f"\n🔧 Pipeline status:")
            print(f"  ✅ Initialized: {self.pipeline.is_initialized}")
            
            # Test connectivity
            print(f"\n🌐 Service connectivity:")
            try:
                connectivity = self.pipeline.test_pipeline_connectivity()
                print(f"  🎤 STT (Azure): {'✅ OK' if connectivity['stt_connection'] else '❌ Failed'}")
                print(f"  🧠 LLM (Gemini): {'✅ OK' if connectivity['llm_connection'] else '❌ Failed'}")
                print(f"  🔊 TTS (VBEE): {'✅ OK' if connectivity['tts_connection'] else '❌ Failed'}")
                print(f"  🌐 Overall: {'✅ Ready' if connectivity['overall_status'] else '❌ Issues detected'}")
            except Exception as e:
                print_warning(f"Cannot test connectivity: {e}")
        else:
            print(f"\n🔧 Pipeline: ❌ Not initialized")
        
        # System resources
        print(f"\n💻 System info:")
        print(f"  🕐 Demo uptime: {time.time() - self.start_time:.1f}s")
        print(f"  💬 Conversations: {self.conversation_count}")
        
        # Directory status
        dirs_to_check = [
            "audio_samples/input",
            "audio_samples/output", 
            "logs"
        ]
        
        print(f"\n📁 Directory status:")
        for dir_path in dirs_to_check:
            path = Path(dir_path)
            if path.exists():
                files_count = len(list(path.iterdir()))
                print(f"  📂 {dir_path}: ✅ ({files_count} files)")
            else:
                print(f"  📂 {dir_path}: ❌ Not found")
    
    def show_conversation_history(self):
        """Show conversation history from logs"""
        print_header("LỊCH SỬ TRÒ CHUYỆN")
        
        # Look for conversation logs
        logs_dir = Path("logs")
        if not logs_dir.exists():
            print_warning("Thư mục logs chưa tồn tại")
            return
        
        # Find conversation log files
        log_files = list(logs_dir.glob("conversation_*.json"))
        
        if not log_files:
            print_warning("Không có log cuộc trò chuyện nào")
            return
        
        # Sort by modification time
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print(f"📚 Tìm thấy {len(log_files)} log cuộc trò chuyện:")
        
        for i, log_file in enumerate(log_files[:10], 1):  # Show top 10
            mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"  {i}. {log_file.name}")
            print(f"     ⏰ {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            choice = input("\n📖 Chọn log để xem (nhập số): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= min(10, len(log_files)):
                selected_log = log_files[int(choice) - 1]
                self.display_conversation_log(selected_log)
            else:
                print_error("Lựa chọn không hợp lệ")
                
        except Exception as e:
            print_error(f"Lỗi đọc log: {e}")
    
    def display_conversation_log(self, log_file):
        """Display content of a conversation log"""
        try:
            import json
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            print(f"\n{'='*60}")
            print(f"📖 LOG: {log_file.name}")
            print(f"{'='*60}")
            
            # Show conversation details
            print(f"⏰ Timestamp: {log_data.get('timestamp', 'N/A')}")
            print(f"💬 User: {log_data.get('user_text', 'N/A')}")
            print(f"🤖 Assistant: {log_data.get('assistant_text', 'N/A')}")
            
            if 'pipeline_time' in log_data:
                print(f"⏱️  Pipeline time: {log_data['pipeline_time']:.3f}s")
            
            if 'step_times' in log_data:
                print(f"\n📊 Step breakdown:")
                for step, step_time in log_data['step_times'].items():
                    print(f"  - {step.upper()}: {step_time:.3f}s")
            
            if 'audio_files' in log_data:
                print(f"\n🎵 Audio files:")
                for audio_type, audio_path in log_data['audio_files'].items():
                    print(f"  - {audio_type}: {Path(audio_path).name}")
            
        except Exception as e:
            print_error(f"Cannot read log file: {e}")
    
    def play_audio_file(self, audio_path):
        """Play audio file using system default player"""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(audio_path)
                print_success(f"🔊 Đang phát: {Path(audio_path).name}")
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", audio_path])
                print_success(f"🔊 Đang phát: {Path(audio_path).name}")
            else:  # Linux
                subprocess.run(["xdg-open", audio_path])
                print_success(f"🔊 Đang phát: {Path(audio_path).name}")
                
        except Exception as e:
            print_error(f"Không thể phát audio: {e}")
            print_info("Hãy mở file audio thủ công: " + audio_path)
    
    def save_conversation_summary(self, result):
        """Save conversation summary to logs"""
        try:
            os.makedirs("logs", exist_ok=True)
            
            summary = {
                "timestamp": get_timestamp(),
                "user_text": result.get("user_text", ""),
                "assistant_text": result.get("assistant_text", ""),
                "pipeline_time": result.get("pipeline_time", 0),
                "step_times": result.get("step_times", {}),
                "audio_files": {
                    "output": result.get("output_audio_path", "")
                }
            }
            
            # Add input audio if available
            if "input_audio_path" in result:
                summary["audio_files"]["input"] = result["input_audio_path"]
            
            log_file = f"logs/conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            import json
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Cannot save conversation summary: {e}")
    
    def run(self):
        """Run the demo"""
        if not self.initialize():
            print_error("Demo initialization failed. Exiting...")
            return
        
        print_success("🎉 Elder Care Voice Assistant đã sẵn sàng!")
        print_info("💡 Hướng dẫn sử dụng:")
        print("  - Voice: Đặt file audio vào audio_samples/input/ rồi chọn option 1")
        print("  - Text: Nhập tin nhắn trực tiếp với option 2")
        print("  - Audio được tạo sẽ lưu trong audio_samples/output/")
        
        while True:
            try:
                self.show_main_menu()
                choice = input("\n👤 Chọn chức năng (0-7): ").strip()
                
                if choice == "0":
                    print_info("👋 Cảm ơn bạn đã sử dụng Elder Care Voice Assistant!")
                    break
                elif choice == "1":
                    self.handle_voice_conversation()
                elif choice == "2":
                    self.handle_text_conversation()
                elif choice == "3":
                    self.show_statistics()
                elif choice == "4":
                    self.play_recent_audio()
                elif choice == "5":
                    self.show_audio_files()
                elif choice == "6":
                    self.show_system_status()
                elif choice == "7":
                    self.show_conversation_history()
                else:
                    print_error("Lựa chọn không hợp lệ. Vui lòng chọn 0-7.")
                
                # Pause before showing menu again
                input("\n📝 Nhấn Enter để tiếp tục...")
                
            except KeyboardInterrupt:
                print_warning("\n👋 Đang thoát demo...")
                break
            except Exception as e:
                print_error(f"Lỗi không mong đợi: {e}")
                self.logger.error(f"Demo error: {e}")
    
    def shutdown(self):
        """Cleanup demo resources"""
        if self.pipeline:
            self.pipeline.shutdown()
        
        session_duration = time.time() - self.start_time
        self.logger.info(f"Demo session ended. Duration: {session_duration:.1f}s, Conversations: {self.conversation_count}")

def main():
    """Main demo function"""
    demo = ElderCareDemo()
    
    try:
        demo.run()
    except KeyboardInterrupt:
        print_warning("\nDemo interrupted by user")
    except Exception as e:
        print_error(f"Demo error: {e}")
    finally:
        demo.shutdown()

if __name__ == "__main__":
    main()
