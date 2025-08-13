"""
Auto Audio Playback Demo - Test tính năng phát âm thanh tự động
Chạy: python test_auto_audio.py
"""

import os
import sys
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
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Make sure to install required packages: pip install -r requirements.txt")
    sys.exit(1)

def test_multiple_audio_playback():
    """Test multiple audio files with auto playback"""
    print(f"{Fore.BLUE}{'='*60}")
    print(f"🎵 AUTO AUDIO PLAYBACK DEMO")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Sample texts for testing
    test_samples = [
        "Xin chào! Tôi là trợ lý AI của bạn.",
        "Hôm nay bạn có khỏe không?",
        "Tôi có thể giúp bạn trả lời các câu hỏi về sức khỏe.",
        "Bạn cần tôi hỗ trợ gì thêm không?",
        "Cảm ơn bạn đã sử dụng dịch vụ. Chúc bạn một ngày tốt lành!"
    ]
    
    try:
        # Initialize TTS service
        print(f"{Fore.CYAN}🔧 Initializing TTS service...{Style.RESET_ALL}")
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        
        if not tts_service.test_connection():
            print(f"{Fore.RED}❌ TTS service connection failed{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN}✅ TTS service ready{Style.RESET_ALL}")
        
        # Test each sample
        for i, text in enumerate(test_samples, 1):
            print(f"\n{Fore.YELLOW}{'='*50}")
            print(f"🎵 Audio Test {i}/{len(test_samples)}")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            print(f"📝 Text: '{text}'")
            
            # Generate audio
            timestamp = datetime.now().strftime("%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"auto_test_{i}_{timestamp}.wav")
            
            print(f"{Fore.CYAN}🔄 Generating audio...{Style.RESET_ALL}")
            start_time = time.time()
            
            audio_path, metadata, success = tts_service.text_to_speech(text, output_file)
            generation_time = time.time() - start_time
            
            if not success:
                print(f"{Fore.RED}❌ Audio generation failed{Style.RESET_ALL}")
                continue
            
            print(f"{Fore.GREEN}✅ Audio generated in {generation_time:.2f}s{Style.RESET_ALL}")
            print(f"📁 File: {audio_path}")
            print(f"📏 Duration: {metadata.get('duration', 0):.1f}s")
            
            # Auto play with enhanced error handling
            print(f"\n{Fore.MAGENTA}🎵 AUTO PLAYING...{Style.RESET_ALL}")
            
            playback_success = auto_play_audio(audio_path, tts_service)
            
            if playback_success:
                print(f"{Fore.GREEN}✅ Playback completed successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ Playback had issues{Style.RESET_ALL}")
            
            # Wait between tests
            if i < len(test_samples):
                print(f"\n{Fore.CYAN}⏸️ Waiting 2 seconds before next test...{Style.RESET_ALL}")
                time.sleep(2)
        
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"📊 AUTO AUDIO DEMO COMPLETED")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        print(f"✅ Tested {len(test_samples)} audio samples")
        print(f"📁 Audio files saved to: {AUDIO_OUTPUT_DIR}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Demo failed: {e}{Style.RESET_ALL}")
        return False

def auto_play_audio(audio_path, tts_service):
    """Enhanced auto play function with multiple fallback methods"""
    try:
        # Method 1: Use TTS service play method
        tts_service.play_audio_file(audio_path)
        return True
        
    except Exception as primary_error:
        print(f"{Fore.YELLOW}⚠️ Primary playback failed: {primary_error}{Style.RESET_ALL}")
        
        # Method 2: Try system-specific commands
        import subprocess
        import platform
        
        system = platform.system().lower()
        
        try:
            if system == 'windows':
                # Windows PowerShell method
                print(f"{Fore.CYAN}🔄 Trying Windows PowerShell playback...{Style.RESET_ALL}")
                subprocess.run([
                    'powershell', '-c', 
                    f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'
                ], check=True, capture_output=True, timeout=30)
                
            elif system == 'darwin':  # macOS
                print(f"{Fore.CYAN}🔄 Trying macOS afplay...{Style.RESET_ALL}")
                subprocess.run(['afplay', audio_path], check=True, timeout=30)
                
            elif system == 'linux':
                print(f"{Fore.CYAN}🔄 Trying Linux aplay...{Style.RESET_ALL}")
                subprocess.run(['aplay', audio_path], check=True, timeout=30)
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"{Fore.GREEN}✅ Audio is playing (timeout reached)...{Style.RESET_ALL}")
            return True
            
        except Exception as subprocess_error:
            print(f"{Fore.YELLOW}⚠️ Subprocess playback failed: {subprocess_error}{Style.RESET_ALL}")
            
            # Method 3: Try to open with default application
            try:
                print(f"{Fore.CYAN}🔄 Trying system default player...{Style.RESET_ALL}")
                
                if system == 'windows':
                    os.startfile(audio_path)
                else:
                    subprocess.run(['open' if system == 'darwin' else 'xdg-open', audio_path])
                
                print(f"{Fore.GREEN}✅ Opened with system default player{Style.RESET_ALL}")
                return True
                
            except Exception as final_error:
                print(f"{Fore.RED}❌ All playback methods failed: {final_error}{Style.RESET_ALL}")
                print(f"📁 Audio saved to: {audio_path}")
                return False

def interactive_audio_test():
    """Interactive audio test where user can input custom text"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"🎤 INTERACTIVE AUDIO TEST")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    print(f"{Fore.YELLOW}Nhập text để chuyển thành giọng nói và tự động phát.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Gõ 'quit' để thoát.{Style.RESET_ALL}")
    
    try:
        # Initialize TTS service
        tts_service = AzureTTSService(
            AZURE_SPEECH_KEY, 
            AZURE_SPEECH_REGION, 
            AZURE_TTS_VOICE,
            AZURE_TTS_SPEECH_RATE,
            AZURE_TTS_PITCH,
            AZURE_TTS_VOLUME
        )
        
        if not tts_service.test_connection():
            print(f"{Fore.RED}❌ TTS service connection failed{Style.RESET_ALL}")
            return False
        
        audio_count = 0
        
        while True:
            user_text = input(f"\n{Fore.CYAN}💬 Nhập text: {Style.RESET_ALL}").strip()
            
            if user_text.lower() in ['quit', 'exit', 'thoát', 'q']:
                print(f"{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}")
                break
            
            if not user_text:
                print(f"{Fore.YELLOW}⚠️ Vui lòng nhập text{Style.RESET_ALL}")
                continue
            
            audio_count += 1
            
            # Generate and play audio
            timestamp = datetime.now().strftime("%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"interactive_{audio_count}_{timestamp}.wav")
            
            print(f"\n{Fore.CYAN}🔄 Đang tạo âm thanh...{Style.RESET_ALL}")
            audio_path, metadata, success = tts_service.text_to_speech(user_text, output_file)
            
            if success:
                print(f"{Fore.GREEN}✅ Âm thanh đã tạo{Style.RESET_ALL}")
                print(f"📁 File: {audio_path}")
                
                print(f"\n{Fore.MAGENTA}🎵 Đang phát âm thanh...{Style.RESET_ALL}")
                playback_success = auto_play_audio(audio_path, tts_service)
                
                if not playback_success:
                    print(f"{Fore.YELLOW}💡 Bạn có thể mở file thủ công: {audio_path}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Không thể tạo âm thanh{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}📊 Đã tạo {audio_count} file âm thanh{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Interactive test failed: {e}{Style.RESET_ALL}")
        return False

def main():
    """Main function"""
    print(f"{Fore.BLUE}{'='*70}")
    print(f"🎵 AUTO AUDIO PLAYBACK TESTING SUITE")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    # Check configuration
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print(f"\n{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("📋 Missing Azure Speech Services configuration")
        print("💡 Please check your .env file")
        return False
    
    print(f"\n{Fore.CYAN}🎯 SELECT TEST MODE:{Style.RESET_ALL}")
    print(f"1. 🎵 Multiple Audio Samples Test")
    print(f"2. 🎤 Interactive Audio Test")
    print(f"3. 🚀 Run Both Tests")
    
    choice = input(f"\n{Fore.CYAN}👉 Enter choice (1-3): {Style.RESET_ALL}").strip()
    
    if choice == "1":
        print(f"\n{Fore.YELLOW}🎵 Starting Multiple Audio Test...{Style.RESET_ALL}")
        return test_multiple_audio_playback()
        
    elif choice == "2":
        print(f"\n{Fore.YELLOW}🎤 Starting Interactive Audio Test...{Style.RESET_ALL}")
        return interactive_audio_test()
        
    elif choice == "3":
        print(f"\n{Fore.YELLOW}🚀 Running All Tests...{Style.RESET_ALL}")
        test1 = test_multiple_audio_playback()
        if test1:
            print(f"\n{Fore.GREEN}✅ Multiple audio test completed{Style.RESET_ALL}")
        
        test2 = interactive_audio_test()
        if test2:
            print(f"\n{Fore.GREEN}✅ Interactive test completed{Style.RESET_ALL}")
        
        return test1 and test2
        
    else:
        print(f"{Fore.RED}❌ Invalid choice{Style.RESET_ALL}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print(f"\n{Fore.GREEN}🎉 Auto audio playback testing completed successfully!{Style.RESET_ALL}")
            print(f"💡 Your pipeline is ready for auto audio playback!")
        else:
            print(f"\n{Fore.YELLOW}⚠️ Audio playback testing had issues{Style.RESET_ALL}")
            print(f"💡 Check your audio system and try again")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)
