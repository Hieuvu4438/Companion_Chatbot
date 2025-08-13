"""
TTS Test - Test riêng cho Text-to-Speech với Azure Speech Services
Chạy: python tts_test.py
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
    log_file = os.path.join(LOGS_DIR, f'tts_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
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

def test_tts_connection():
    """Test TTS service connection"""
    print(f"\n{Fore.CYAN}🔍 Testing TTS Connection...{Style.RESET_ALL}")
    
    try:
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        
        if tts_service.test_connection():
            print(f"{Fore.GREEN}✅ TTS Connection: SUCCESS{Style.RESET_ALL}")
            return tts_service
        else:
            print(f"{Fore.RED}❌ TTS Connection: FAILED{Style.RESET_ALL}")
            return None
            
    except Exception as e:
        print(f"{Fore.RED}❌ TTS Connection Error: {e}{Style.RESET_ALL}")
        return None

def test_simple_tts():
    """Test simple text-to-speech conversion"""
    print(f"\n{Fore.CYAN}🔊 Testing Simple TTS...{Style.RESET_ALL}")
    
    try:
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        metrics_collector = MetricsCollector()
        
        # Test texts
        test_texts = [
            "Xin chào! Tôi là trợ lý AI hỗ trợ người cao tuổi.",
            "Hôm nay thời tiết thế nào? Bạn có cảm thấy khỏe không?",
            "Để giữ sức khỏe tốt, hãy nhớ uống đủ nước và vận động nhẹ nhàng mỗi ngày."
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n{Fore.YELLOW}📝 Test {i}: {text[:50]}...{Style.RESET_ALL}")
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"tts_test_{i}_{timestamp}.wav")
            
            # Convert text to speech
            start_time = metrics_collector.start_timer()
            audio_path, metadata, success = tts_service.text_to_speech(text, output_file)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                # Create TTS metrics
                tts_metrics = metrics_collector.create_tts_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    audio_duration=metadata.get('duration', 0.0),
                    character_count=len(text),
                    voice_model=AZURE_TTS_VOICE,
                    audio_format="wav",
                    file_size=metadata.get('file_size', 0),
                    success=True
                )
                
                # Display metrics
                metrics_collector.display_metrics(tts_metrics, f"TTS Test {i}")
                
                # Save metrics
                metrics_collector.save_metrics(tts_metrics)
                
                # Try to play audio (Windows)
                print(f"{Fore.GREEN}🎵 Playing audio...{Style.RESET_ALL}")
                tts_service.play_audio_file(audio_path)
                
                # Wait a bit before next test
                time.sleep(2)
            else:
                print(f"{Fore.RED}❌ TTS Test {i} failed{Style.RESET_ALL}")
                return False
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Simple TTS test error: {e}{Style.RESET_ALL}")
        return False

def test_manual_text_input():
    """Test TTS with manual text input - Main interactive function"""
    print(f"\n{Fore.CYAN}💬 MANUAL TEXT INPUT - TTS CONVERTER{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📝 Nhập văn bản để chuyển thành giọng nói{Style.RESET_ALL}")
    print(f"{Fore.GREEN}💡 Tips:{Style.RESET_ALL}")
    print(f"   - Nhập 'quit', 'exit', hoặc 'q' để thoát")
    print(f"   - Nhập 'help' để xem lệnh hỗ trợ")
    print(f"   - Nhập 'voices' để xem danh sách giọng nói")
    print(f"   - Nhập 'clear' để xóa màn hình")
    
    try:
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        metrics_collector = MetricsCollector()
        conversion_count = 0
        
        while True:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📝 Nhập văn bản (conversion #{conversion_count + 1}):{Style.RESET_ALL}")
            
            # Multi-line input support
            print(f"{Fore.GREEN}💭 Nhập text (Enter 2 lần để kết thúc, hoặc gõ lệnh):{Style.RESET_ALL}")
            lines = []
            while True:
                line = input("� ").strip()
                
                # Handle commands
                if line.lower() in ['quit', 'exit', 'q']:
                    print(f"{Fore.CYAN}👋 Tạm biệt! Đã chuyển đổi {conversion_count} đoạn text.{Style.RESET_ALL}")
                    return True
                
                elif line.lower() == 'help':
                    print(f"\n{Fore.MAGENTA}📋 LỆNH HỖ TRỢ:{Style.RESET_ALL}")
                    print(f"  quit/exit/q - Thoát chương trình")
                    print(f"  help - Hiển thị trợ giúp")
                    print(f"  voices - Xem danh sách giọng nói")
                    print(f"  clear - Xóa màn hình")
                    print(f"  stats - Xem thống kê")
                    break
                
                elif line.lower() == 'voices':
                    print(f"\n{Fore.MAGENTA}🎤 DANH SÁCH GIỌNG NÓI:{Style.RESET_ALL}")
                    try:
                        voices = tts_service.get_available_voices()
                        for voice_id, voice_name in voices.items():
                            current = "✅ ĐANG DÙNG" if voice_id == AZURE_TTS_VOICE else ""
                            print(f"  {voice_id}: {voice_name} {current}")
                    except:
                        print(f"  ⚠️ Không thể tải danh sách giọng nói")
                    break
                
                elif line.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    break
                
                elif line.lower() == 'stats':
                    print(f"\n{Fore.MAGENTA}📊 THỐNG KÊ:{Style.RESET_ALL}")
                    print(f"  🔢 Số lần chuyển đổi: {conversion_count}")
                    print(f"  🎙️ Giọng nói hiện tại: {AZURE_TTS_VOICE}")
                    print(f"  📁 File output: {AUDIO_OUTPUT_DIR}")
                    break
                
                elif line == "":
                    if lines:  # If we have content, process it
                        break
                    else:
                        print(f"{Fore.YELLOW}⚠️ Vui lòng nhập văn bản{Style.RESET_ALL}")
                        continue
                else:
                    lines.append(line)
            
            # Skip if it was a command
            if line.lower() in ['help', 'voices', 'clear', 'stats']:
                continue
            
            # Join lines to create full text
            user_text = "\n".join(lines).strip()
            
            if not user_text:
                print(f"{Fore.YELLOW}⚠️ Không có văn bản để chuyển đổi{Style.RESET_ALL}")
                continue
            
            # Show text preview
            preview_text = user_text[:100] + "..." if len(user_text) > 100 else user_text
            print(f"\n{Fore.CYAN}📄 Text preview: {preview_text}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Text length: {len(user_text)} characters{Style.RESET_ALL}")
            
            # Confirm if text is very long
            if len(user_text) > 500:
                confirm = input(f"{Fore.YELLOW}⚠️ Text dài ({len(user_text)} ký tự). Tiếp tục? (y/n): {Style.RESET_ALL}")
                if confirm.lower() not in ['y', 'yes']:
                    continue
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"manual_input_{timestamp}.wav")
            
            # Convert text to speech
            print(f"{Fore.CYAN}🔄 Đang chuyển đổi văn bản thành giọng nói...{Style.RESET_ALL}")
            start_time = metrics_collector.start_timer()
            audio_path, metadata, success = tts_service.text_to_speech(user_text, output_file)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                conversion_count += 1
                
                # Create and display metrics
                tts_metrics = metrics_collector.create_tts_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    audio_duration=metadata.get('duration', 0.0),
                    character_count=len(user_text),
                    voice_model=AZURE_TTS_VOICE,
                    audio_format="wav",
                    file_size=metadata.get('file_size', 0),
                    success=True
                )
                
                print(f"\n{Fore.GREEN}✅ CHUYỂN ĐỔI THÀNH CÔNG!{Style.RESET_ALL}")
                metrics_collector.display_metrics(tts_metrics, f"Manual Input #{conversion_count}")
                metrics_collector.save_metrics(tts_metrics)
                
                # Ask if user wants to play audio
                play_choice = input(f"{Fore.YELLOW}🎵 Phát âm thanh ngay? (y/n): {Style.RESET_ALL}")
                if play_choice.lower() in ['y', 'yes', '']:
                    print(f"{Fore.GREEN}🎵 Đang phát âm thanh...{Style.RESET_ALL}")
                    tts_service.play_audio_file(audio_path)
                
                print(f"{Fore.GREEN}📁 File saved: {audio_path}{Style.RESET_ALL}")
                
            else:
                print(f"{Fore.RED}❌ Chuyển đổi thất bại. Vui lòng thử lại.{Style.RESET_ALL}")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Chương trình bị ngắt bởi người dùng{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Đã chuyển đổi {conversion_count} đoạn text.{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi trong quá trình chuyển đổi: {e}{Style.RESET_ALL}")
        return False

def test_interactive_tts():
    """Legacy function - redirect to manual text input"""
    return test_manual_text_input()

def test_voice_models():
    """Test different voice models"""
    print(f"\n{Fore.CYAN}🎙️ Testing Different Voice Models...{Style.RESET_ALL}")
    
    try:
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        metrics_collector = MetricsCollector()
        
        available_voices = tts_service.get_available_voices()
        test_text = "Xin chào, tôi là trợ lý AI dành cho người cao tuổi. Rất vui được hỗ trợ bạn."
        
        print(f"{Fore.YELLOW}🎤 Testing {len(available_voices)} voice models...{Style.RESET_ALL}")
        
        for voice_id, voice_name in available_voices.items():
            print(f"\n{Fore.CYAN}🔄 Testing voice: {voice_name}{Style.RESET_ALL}")
            
            # Change voice
            tts_service.change_voice(voice_id)
            
            # Generate audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"voice_test_{voice_id}_{timestamp}.wav")
            
            start_time = metrics_collector.start_timer()
            audio_path, metadata, success = tts_service.text_to_speech(test_text, output_file)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                tts_metrics = metrics_collector.create_tts_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    audio_duration=metadata.get('duration', 0.0),
                    character_count=len(test_text),
                    voice_model=voice_id,
                    audio_format="wav",
                    file_size=metadata.get('file_size', 0),
                    success=True
                )
                
                metrics_collector.display_metrics(tts_metrics, f"Voice: {voice_name}")
                metrics_collector.save_metrics(tts_metrics)
                
                # Play audio
                print(f"{Fore.GREEN}🎵 Playing {voice_name}...{Style.RESET_ALL}")
                tts_service.play_audio_file(audio_path)
                time.sleep(3)  # Wait between voices
            else:
                print(f"{Fore.RED}❌ Failed to generate audio for {voice_name}{Style.RESET_ALL}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Voice models test error: {e}{Style.RESET_ALL}")
        return False

def test_elderly_optimized_tts():
    """Test elderly-optimized TTS features"""
    print(f"\n{Fore.CYAN}👴 Testing Elderly-Optimized TTS...{Style.RESET_ALL}")
    
    try:
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        metrics_collector = MetricsCollector()
        
        elderly_response = """
        Chào bạn! Để giữ sức khỏe tốt ở tuổi cao, tôi khuyên bạn nên:
        
        1. Uống đủ nước mỗi ngày, khoảng 1.5-2 lít.
        2. Vận động nhẹ nhàng như đi bộ 30 phút mỗi ngày.
        3. Ăn nhiều rau xanh và hoa quả tươi.
        4. Ngủ đủ giấc từ 7-8 tiếng mỗi đêm.
        5. Thường xuyên kiểm tra sức khỏe tại bệnh viện.
        
        Nhớ luôn giữ tinh thần thoải mái và vui vẻ nhé!
        """
        
        # Test elderly-optimized synthesis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(AUDIO_OUTPUT_DIR, f"elderly_optimized_{timestamp}.wav")
        
        print(f"{Fore.YELLOW}🔄 Generating elderly-optimized speech...{Style.RESET_ALL}")
        start_time = metrics_collector.start_timer()
        audio_path, metadata, success = tts_service.synthesize_elder_response(elderly_response, output_file)
        end_time, response_time = metrics_collector.end_timer(start_time)
        
        if success:
            tts_metrics = metrics_collector.create_tts_metrics(
                start_time=start_time,
                end_time=end_time,
                response_time=response_time,
                audio_duration=metadata.get('duration', 0.0),
                character_count=len(elderly_response),
                voice_model=AZURE_TTS_VOICE,
                audio_format="wav",
                file_size=metadata.get('file_size', 0),
                success=True
            )
            
            metrics_collector.display_metrics(tts_metrics, "Elderly-Optimized TTS")
            metrics_collector.save_metrics(tts_metrics)
            
            print(f"{Fore.GREEN}🎵 Playing elderly-optimized speech...{Style.RESET_ALL}")
            tts_service.play_audio_file(audio_path)
            
            return True
        else:
            print(f"{Fore.RED}❌ Elderly-optimized TTS failed{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Elderly-optimized TTS test error: {e}{Style.RESET_ALL}")
        return False

def display_tts_info():
    """Display TTS service information"""
    print(f"\n{Fore.MAGENTA}📋 TTS SERVICE INFORMATION{Style.RESET_ALL}")
    print(f"🔧 Service: Azure Speech Services")
    print(f"🌐 Region: {AZURE_SPEECH_REGION}")
    print(f"🎙️ Voice: {AZURE_TTS_VOICE}")
    print(f"⚡ Speech Rate: {AZURE_TTS_SPEECH_RATE}")
    print(f"🎵 Audio Format: wav")
    
    # Show available voices
    try:
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        voices = tts_service.get_available_voices()
        print(f"\n🎤 Available Voices ({len(voices)}):")
        for voice_id, voice_name in voices.items():
            status = "✅" if voice_id == AZURE_TTS_VOICE else "  "
            print(f"  {status} {voice_id}: {voice_name}")
    except:
        print(f"⚠️ Could not load voice list")

def main():
    """Main test function"""
    print(f"{Fore.BLUE}{'='*60}")
    print(f"🔊 TTS SERVICE TEST - AZURE SPEECH SERVICES")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting TTS service test")
    
    # Display service info
    display_tts_info()
    
    # Check API key
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print(f"\n{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("📋 Please configure Azure Speech Services in .env file:")
        print("   AZURE_SPEECH_KEY=your_azure_speech_key")
        print("   AZURE_SPEECH_REGION=your_azure_region")
        return False
    
    # Test connection first
    print(f"\n{Fore.CYAN}🔍 Checking TTS Connection...{Style.RESET_ALL}")
    tts_service = test_tts_connection()
    if not tts_service:
        print(f"\n{Fore.RED}❌ Cannot proceed without TTS connection{Style.RESET_ALL}")
        return False
    
    # Show menu options
    print(f"\n{Fore.MAGENTA}📋 TTS TEST OPTIONS:{Style.RESET_ALL}")
    print(f"  1. 💬 Manual Text Input (RECOMMENDED)")
    print(f"  2. 🧪 Quick Test Suite")
    print(f"  3. 🎙️ Voice Models Test")
    print(f"  4. 👴 Elderly-Optimized Test")
    print(f"  5. 🔄 Full Test Suite")
    
    while True:
        try:
            choice = input(f"\n{Fore.YELLOW}Choose option (1-5): {Style.RESET_ALL}").strip()
            
            if choice == "1":
                # Manual Text Input - MAIN FEATURE
                print(f"\n{Fore.CYAN}{'='*60}")
                print(f"💬 MANUAL TEXT INPUT MODE")
                print(f"{'='*60}{Style.RESET_ALL}")
                success = test_manual_text_input()
                
                print(f"\n{Fore.GREEN}✅ Manual text input completed!{Style.RESET_ALL}")
                print(f"📁 Audio files saved to: {AUDIO_OUTPUT_DIR}")
                print(f"📊 Logs saved to: {log_file}")
                return success
                
            elif choice == "2":
                # Quick Test Suite
                print(f"\n{Fore.CYAN}{'='*60}")
                print(f"🧪 QUICK TEST SUITE")
                print(f"{'='*60}{Style.RESET_ALL}")
                
                test_results = {}
                test_results['simple_tts'] = test_simple_tts()
                
                total_tests = len(test_results)
                passed_tests = sum(test_results.values())
                
                print(f"\n{Fore.BLUE}📊 QUICK TEST RESULTS:{Style.RESET_ALL}")
                print(f"📈 Result: {passed_tests}/{total_tests} tests passed")
                
                # Ask if user wants manual input
                manual_choice = input(f"\n{Fore.YELLOW}🤔 Test manual text input now? (y/n): {Style.RESET_ALL}")
                if manual_choice.lower() in ['y', 'yes']:
                    return test_manual_text_input()
                else:
                    return passed_tests == total_tests
                    
            elif choice == "3":
                # Voice Models Test
                print(f"\n{Fore.CYAN}{'='*60}")
                print(f"🎙️ VOICE MODELS TEST")
                print(f"{'='*60}{Style.RESET_ALL}")
                success = test_voice_models()
                
                # Ask if user wants manual input
                manual_choice = input(f"\n{Fore.YELLOW}🤔 Test manual text input now? (y/n): {Style.RESET_ALL}")
                if manual_choice.lower() in ['y', 'yes']:
                    return test_manual_text_input()
                else:
                    return success
                    
            elif choice == "4":
                # Elderly-Optimized Test
                print(f"\n{Fore.CYAN}{'='*60}")
                print(f"👴 ELDERLY-OPTIMIZED TEST")
                print(f"{'='*60}{Style.RESET_ALL}")
                success = test_elderly_optimized_tts()
                
                # Ask if user wants manual input
                manual_choice = input(f"\n{Fore.YELLOW}🤔 Test manual text input now? (y/n): {Style.RESET_ALL}")
                if manual_choice.lower() in ['y', 'yes']:
                    return test_manual_text_input()
                else:
                    return success
                    
            elif choice == "5":
                # Full Test Suite
                print(f"\n{Fore.CYAN}{'='*60}")
                print(f"🔄 FULL TEST SUITE")
                print(f"{'='*60}{Style.RESET_ALL}")
                
                test_results = {}
                
                print(f"\n{Fore.CYAN}TEST 1: SIMPLE TTS{Style.RESET_ALL}")
                test_results['simple_tts'] = test_simple_tts()
                
                print(f"\n{Fore.CYAN}TEST 2: VOICE MODELS{Style.RESET_ALL}")
                test_results['voice_models'] = test_voice_models()
                
                print(f"\n{Fore.CYAN}TEST 3: ELDERLY-OPTIMIZED{Style.RESET_ALL}")
                test_results['elderly_optimized'] = test_elderly_optimized_tts()
                
                # Summary
                print(f"\n{Fore.BLUE}{'='*60}")
                print(f"📊 FULL TEST SUMMARY")
                print(f"{'='*60}{Style.RESET_ALL}")
                
                total_tests = len(test_results)
                passed_tests = sum(test_results.values())
                
                for test_name, result in test_results.items():
                    status = f"{Fore.GREEN}✅ PASS" if result else f"{Fore.RED}❌ FAIL"
                    print(f"{test_name.replace('_', ' ').title()}: {status}{Style.RESET_ALL}")
                
                print(f"\n📈 Overall Result: {passed_tests}/{total_tests} tests passed")
                
                # Ask if user wants manual input
                manual_choice = input(f"\n{Fore.YELLOW}🤔 Test manual text input now? (y/n): {Style.RESET_ALL}")
                if manual_choice.lower() in ['y', 'yes']:
                    return test_manual_text_input()
                else:
                    return passed_tests == total_tests
                    
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please enter 1-5.{Style.RESET_ALL}")
                continue
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Test interrupted by user{Style.RESET_ALL}")
            return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)
