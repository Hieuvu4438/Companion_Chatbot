"""
Manual TTS - Chương trình chuyển văn bản thành giọng nói
Chạy: python manual_tts.py
"""

import os
import sys
import logging
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from config import *
    from utils.azure_tts_service import AzureTTSService
    from utils.metrics import MetricsCollector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Make sure to install required packages: pip install -r requirements.txt")
    sys.exit(1)

def setup_logging():
    """Setup logging configuration"""
    log_file = os.path.join(LOGS_DIR, f'manual_tts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return log_file

def show_help():
    """Show help information"""
    print(f"\n{Fore.MAGENTA}📋 HƯỚNG DẪN SỬ DỤNG:{Style.RESET_ALL}")
    print(f"  📝 Nhập văn bản để chuyển thành giọng nói")
    print(f"  🔄 Nhấn Enter 2 lần để kết thúc nhập text")
    print(f"  📱 Hỗ trợ văn bản nhiều dòng")
    print(f"\n{Fore.CYAN}🎛️ CÁC LỆNH:{Style.RESET_ALL}")
    print(f"  quit/exit/q - Thoát chương trình")
    print(f"  help - Hiển thị trợ giúp")
    print(f"  voices - Xem danh sách giọng nói")
    print(f"  clear - Xóa màn hình")
    print(f"  stats - Xem thống kê")
    print(f"  settings - Xem cài đặt hiện tại")
    print(f"\n{Fore.GREEN}💡 TIPS:{Style.RESET_ALL}")
    print(f"  • Văn bản dài (>500 ký tự) sẽ cần xác nhận")
    print(f"  • File audio được lưu trong {AUDIO_OUTPUT_DIR}")
    print(f"  • Hỗ trợ dấu câu và ký tự đặc biệt")

def show_voices(tts_service):
    """Show available voices"""
    print(f"\n{Fore.MAGENTA}🎤 DANH SÁCH GIỌNG NÓI:{Style.RESET_ALL}")
    try:
        voices = tts_service.get_available_voices()
        print(f"📊 Tổng cộng: {len(voices)} giọng nói")
        print("-" * 60)
        for voice_id, voice_name in voices.items():
            current = f"{Fore.GREEN}✅ ĐANG DÙNG{Style.RESET_ALL}" if voice_id == AZURE_TTS_VOICE else ""
            print(f"  {voice_id}: {voice_name} {current}")
    except Exception as e:
        print(f"  ⚠️ Không thể tải danh sách giọng nói: {e}")

def show_stats(conversion_count, total_chars, total_duration):
    """Show conversion statistics"""
    print(f"\n{Fore.MAGENTA}📊 THỐNG KÊ CHUYỂN ĐỔI:{Style.RESET_ALL}")
    print("-" * 40)
    print(f"  🔢 Số lần chuyển đổi: {conversion_count}")
    print(f"  📝 Tổng ký tự: {total_chars:,}")
    print(f"  ⏱️ Tổng thời gian: {total_duration:.2f} giây")
    print(f"  📊 Trung bình: {total_chars/conversion_count:.0f} ký tự/lần" if conversion_count > 0 else "")
    print(f"  🚀 Tốc độ: {total_chars/total_duration:.0f} ký tự/giây" if total_duration > 0 else "")

def show_settings():
    """Show current settings"""
    print(f"\n{Fore.MAGENTA}⚙️ CÀI ĐẶT HIỆN TẠI:{Style.RESET_ALL}")
    print("-" * 40)
    print(f"  🔧 Service: Azure Speech Services")
    print(f"  🌍 Region: {AZURE_SPEECH_REGION}")
    print(f"  🎙️ Voice: {AZURE_TTS_VOICE}")
    print(f"  ⚡ Speech Rate: {AZURE_TTS_SPEECH_RATE}")
    print(f"  🎵 Pitch: {AZURE_TTS_PITCH}")
    print(f"  🔊 Volume: {AZURE_TTS_VOLUME}")
    print(f"  📁 Output Directory: {AUDIO_OUTPUT_DIR}")

def main():
    """Main manual TTS function"""
    print(f"{Fore.BLUE}{'='*60}")
    print(f"🗣️ MANUAL TEXT-TO-SPEECH CONVERTER")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting manual TTS converter")
    
    # Check configuration
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print(f"\n{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("📋 Please configure Azure Speech Services in .env file:")
        print("   AZURE_SPEECH_KEY=your_azure_speech_key")
        print("   AZURE_SPEECH_REGION=your_azure_region")
        return False
    
    # Initialize services
    try:
        print(f"\n{Fore.CYAN}🔧 Initializing TTS service...{Style.RESET_ALL}")
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        
        # Test connection
        if not tts_service.test_connection():
            print(f"{Fore.RED}❌ Cannot connect to TTS service{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN}✅ TTS service ready!{Style.RESET_ALL}")
        
        metrics_collector = MetricsCollector()
        
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to initialize TTS service: {e}{Style.RESET_ALL}")
        return False
    
    # Show initial information
    show_settings()
    show_help()
    
    # Main conversion loop
    conversion_count = 0
    total_chars = 0
    total_duration = 0.0
    
    print(f"\n{Fore.GREEN}🚀 TTS Converter đã sẵn sàng!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Gõ 'help' để xem hướng dẫn chi tiết{Style.RESET_ALL}")
    
    try:
        while True:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📝 Nhập văn bản (#{conversion_count + 1}):{Style.RESET_ALL}")
            print(f"{Fore.GREEN}💭 (Enter 2 lần để kết thúc, hoặc gõ lệnh){Style.RESET_ALL}")
            
            # Multi-line input
            lines = []
            while True:
                try:
                    line = input("📝 ").strip()
                except EOFError:
                    line = "quit"
                
                # Handle commands
                if line.lower() in ['quit', 'exit', 'q']:
                    print(f"{Fore.CYAN}👋 Tạm biệt!{Style.RESET_ALL}")
                    if conversion_count > 0:
                        show_stats(conversion_count, total_chars, total_duration)
                        print(f"{Fore.GREEN}📁 Logs saved to: {log_file}{Style.RESET_ALL}")
                    return True
                
                elif line.lower() == 'help':
                    show_help()
                    break
                
                elif line.lower() == 'voices':
                    show_voices(tts_service)
                    break
                
                elif line.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    break
                
                elif line.lower() == 'stats':
                    show_stats(conversion_count, total_chars, total_duration)
                    break
                
                elif line.lower() == 'settings':
                    show_settings()
                    break
                
                elif line == "":
                    if lines:  # If we have content, process it
                        break
                    else:
                        print(f"{Fore.YELLOW}⚠️ Vui lòng nhập văn bản hoặc lệnh{Style.RESET_ALL}")
                        continue
                else:
                    lines.append(line)
            
            # Skip if it was a command
            if line.lower() in ['help', 'voices', 'clear', 'stats', 'settings']:
                continue
            
            # Join lines to create full text
            user_text = "\n".join(lines).strip()
            
            if not user_text:
                print(f"{Fore.YELLOW}⚠️ Không có văn bản để chuyển đổi{Style.RESET_ALL}")
                continue
            
            # Show text preview
            char_count = len(user_text)
            word_count = len(user_text.split())
            preview_text = user_text[:100] + "..." if char_count > 100 else user_text
            
            print(f"\n{Fore.CYAN}📄 Text preview:{Style.RESET_ALL}")
            print(f"   {preview_text}")
            print(f"\n{Fore.CYAN}📊 Text info:{Style.RESET_ALL}")
            print(f"   📝 Characters: {char_count}")
            print(f"   📖 Words: {word_count}")
            print(f"   ⏱️ Estimated duration: ~{char_count * 0.1:.1f} seconds")
            
            # Confirm if text is very long
            if char_count > 500:
                confirm = input(f"\n{Fore.YELLOW}⚠️ Text dài ({char_count} ký tự). Tiếp tục? (y/n): {Style.RESET_ALL}")
                if confirm.lower() not in ['y', 'yes', '']:
                    continue
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"manual_tts_{timestamp}.wav")
            
            # Convert text to speech
            print(f"\n{Fore.CYAN}🔄 Đang chuyển đổi văn bản thành giọng nói...{Style.RESET_ALL}")
            start_time = metrics_collector.start_timer()
            audio_path, metadata, success = tts_service.text_to_speech(user_text, output_file)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                conversion_count += 1
                total_chars += char_count
                total_duration += response_time
                
                # Create and display metrics
                tts_metrics = metrics_collector.create_tts_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    audio_duration=metadata.get('duration', 0.0),
                    character_count=char_count,
                    voice_model=AZURE_TTS_VOICE,
                    audio_format="wav",
                    file_size=metadata.get('file_size', 0),
                    success=True
                )
                
                print(f"\n{Fore.GREEN}✅ CHUYỂN ĐỔI THÀNH CÔNG!{Style.RESET_ALL}")
                metrics_collector.display_metrics(tts_metrics, f"Conversion #{conversion_count}")
                metrics_collector.save_metrics(tts_metrics)
                
                print(f"{Fore.GREEN}📁 File saved: {audio_path}{Style.RESET_ALL}")
                
                # Ask if user wants to play audio
                play_choice = input(f"\n{Fore.YELLOW}🎵 Phát âm thanh ngay? (y/n/Enter=yes): {Style.RESET_ALL}")
                if play_choice.lower() in ['y', 'yes', '']:
                    print(f"{Fore.GREEN}🎵 Đang phát âm thanh...{Style.RESET_ALL}")
                    try:
                        tts_service.play_audio_file(audio_path)
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️ Không thể phát âm thanh: {e}{Style.RESET_ALL}")
                        print(f"📁 Bạn có thể mở file: {audio_path}")
                
            else:
                print(f"{Fore.RED}❌ Chuyển đổi thất bại. Vui lòng thử lại.{Style.RESET_ALL}")
                print(f"💡 Kiểm tra kết nối internet và API key")
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️ Chương trình bị ngắt bởi người dùng{Style.RESET_ALL}")
        if conversion_count > 0:
            show_stats(conversion_count, total_chars, total_duration)
            print(f"{Fore.GREEN}📁 Logs saved to: {log_file}{Style.RESET_ALL}")
        return True
    
    except Exception as e:
        print(f"\n{Fore.RED}❌ Lỗi không mong muốn: {e}{Style.RESET_ALL}")
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Critical error: {e}{Style.RESET_ALL}")
        sys.exit(1)
