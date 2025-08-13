"""
Full Pipeline - STT + LLMs + TTS
Chức năng đơn giản: Bấm Enter để ghi âm → Nhận diện giọng nói → LLMs phân tích → TTS phát âm thanh trực tiếp
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
    from utils.stt_service import STTService
    from utils.llm_service import LLMService
    from utils.azure_tts_service import AzureTTSService
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Please install required packages: pip install -r requirements.txt")
    sys.exit(1)

class SimpleChatbot:
    """Simple chatbot with STT → LLMs → TTS pipeline"""
    
    def __init__(self):
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        self.logger = logging.getLogger(__name__)
        
    def initialize_services(self):
        """Initialize all services"""
        try:
            print(f"{Fore.CYAN}🔧 Initializing services...{Style.RESET_ALL}")
            
            # Initialize STT service
            self.stt_service = STTService(
                AZURE_SPEECH_KEY, 
                AZURE_SPEECH_REGION, 
                AZURE_SPEECH_LANGUAGE
            )
            
            # Initialize LLM service
            self.llm_service = LLMService(
                GEMINI_API_KEY, 
                GEMINI_MODEL, 
                GEMINI_TEMPERATURE, 
                GEMINI_MAX_TOKENS
            )
            
            # Initialize TTS service
            self.tts_service = AzureTTSService(
                AZURE_SPEECH_KEY, 
                AZURE_SPEECH_REGION, 
                AZURE_TTS_VOICE,
                AZURE_TTS_SPEECH_RATE,
                AZURE_TTS_PITCH,
                AZURE_TTS_VOLUME
            )
            
            print(f"{Fore.GREEN}✅ All services initialized successfully!{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to initialize services: {e}{Style.RESET_ALL}")
            return False
    
    def test_connections(self):
        """Test all service connections"""
        print(f"{Fore.CYAN}🔍 Testing service connections...{Style.RESET_ALL}")
        
        # Test STT
        try:
            if self.stt_service.test_connection():
                print(f"{Fore.GREEN}✅ STT Service: Connected{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ STT Service: Failed{Style.RESET_ALL}")
                return False
        except:
            print(f"{Fore.RED}❌ STT Service: Error{Style.RESET_ALL}")
            return False
        
        # Test LLM
        try:
            if self.llm_service.test_connection():
                print(f"{Fore.GREEN}✅ LLM Service: Connected{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ LLM Service: Failed{Style.RESET_ALL}")
                return False
        except:
            print(f"{Fore.RED}❌ LLM Service: Error{Style.RESET_ALL}")
            return False
        
        # Test TTS
        try:
            if self.tts_service.test_connection():
                print(f"{Fore.GREEN}✅ TTS Service: Connected{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ TTS Service: Failed{Style.RESET_ALL}")
                return False
        except:
            print(f"{Fore.RED}❌ TTS Service: Error{Style.RESET_ALL}")
            return False
        
        return True
    
    def display_metrics_summary(self, stt_time, llm_time, tts_time, playback_time, total_time):
        """Display performance metrics summary"""
        print(f"\n{Fore.BLUE}{'='*50}")
        print(f"📊 PERFORMANCE METRICS SUMMARY")
        print(f"{'='*50}{Style.RESET_ALL}")
        
        print(f"🎤 STT (Speech Recognition): {Fore.CYAN}{stt_time:.3f}s{Style.RESET_ALL}")
        print(f"🧠 LLM (AI Processing):      {Fore.CYAN}{llm_time:.3f}s{Style.RESET_ALL}")
        print(f"🔊 TTS (Audio Generation):   {Fore.CYAN}{tts_time:.3f}s{Style.RESET_ALL}")
        print(f"🎵 Audio Playback:           {Fore.CYAN}{playback_time:.3f}s{Style.RESET_ALL}")
        print(f"{'-'*50}")
        print(f"⏱️ {Fore.YELLOW}TOTAL PIPELINE TIME:      {total_time:.3f}s{Style.RESET_ALL}")
        
        # Calculate percentages
        processing_time = stt_time + llm_time + tts_time  # Exclude playback from processing
        if processing_time > 0:
            stt_pct = (stt_time / processing_time) * 100
            llm_pct = (llm_time / processing_time) * 100
            tts_pct = (tts_time / processing_time) * 100
            
            print(f"\n📈 Processing Time Breakdown:")
            print(f"   STT: {stt_pct:.1f}% | LLM: {llm_pct:.1f}% | TTS: {tts_pct:.1f}%")
        
        # Performance indicators
        if total_time < 5:
            print(f"\n{Fore.GREEN}🚀 Excellent response time!{Style.RESET_ALL}")
        elif total_time < 10:
            print(f"\n{Fore.YELLOW}✅ Good response time{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️ Slow response time{Style.RESET_ALL}")
    
    def play_audio_with_fallback(self, audio_path):
        """Play audio with multiple fallback methods"""
        try:
            # Method 1: Use winsound for synchronous playback (Windows)
            try:
                import winsound
                if os.path.exists(audio_path):
                    # Use SND_FILENAME flag for synchronous playback (waits until done)
                    winsound.PlaySound(audio_path, winsound.SND_FILENAME)
                    return True
            except ImportError:
                pass
            except Exception as e:
                self.logger.warning(f"winsound playback failed: {e}")
            
            # Method 2: Try PowerShell for Windows  
            import subprocess
            import platform
            
            system = platform.system().lower()
            if system == 'windows':
                try:
                    # Use PowerShell Media.SoundPlayer for synchronous playback
                    subprocess.run([
                        'powershell', '-c', 
                        f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'
                    ], check=True, capture_output=True, timeout=30)
                    return True
                except subprocess.TimeoutExpired:
                    self.logger.warning("PowerShell playback timeout - audio may still be playing")
                    return True
                except Exception as e:
                    self.logger.warning(f"PowerShell playback failed: {e}")
            
            # Method 3: Try system default player (async - less reliable)
            try:
                if system == 'windows':
                    os.startfile(audio_path)
                    # Wait a bit for the audio to start playing
                    estimated_duration = self.tts_service.estimate_speech_duration("dummy text")
                    time.sleep(min(estimated_duration + 2, 10))  # Max 10 seconds wait
                elif system == 'darwin':  # macOS
                    subprocess.run(['afplay', audio_path], check=True)
                elif system == 'linux':
                    subprocess.run(['aplay', audio_path], check=True)
                return True
            except Exception as e:
                self.logger.warning(f"System player failed: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"All audio playback methods failed: {e}")
            return False
    
    def run_pipeline(self):
        """Run the main STT → LLMs → TTS pipeline with metrics"""
        # Start total pipeline timer
        pipeline_start_time = time.time()
        
        try:
            print(f"\n{Fore.YELLOW}🎤 STEP 1: SPEECH RECOGNITION{Style.RESET_ALL}")
            print(f"📝 Press Enter to start recording...")
            input()  # Wait for user to press Enter
            
            # Step 1: Speech-to-Text
            print(f"🎙️ Recording for {RECORD_DURATION} seconds... Please speak!")
            stt_start_time = time.time()
            recognized_text, confidence, stt_success = self.stt_service.recognize_from_microphone(RECORD_DURATION)
            stt_end_time = time.time()
            stt_duration = stt_end_time - stt_start_time
            
            if not stt_success or not recognized_text.strip():
                print(f"{Fore.RED}❌ Speech recognition failed or no speech detected{Style.RESET_ALL}")
                return False
            
            print(f"{Fore.GREEN}✅ Recognized: '{recognized_text}'{Style.RESET_ALL}")
            print(f"🎯 Confidence: {confidence:.2%}")
            print(f"⏱️ STT Time: {stt_duration:.3f}s")
            
            # Step 2: Language Model Processing
            print(f"\n{Fore.YELLOW}🧠 STEP 2: AI PROCESSING{Style.RESET_ALL}")
            llm_start_time = time.time()
            response_text, usage_info, llm_success = self.llm_service.get_emotion_optimized_response(recognized_text)
            llm_end_time = time.time()
            llm_duration = llm_end_time - llm_start_time
            
            if not llm_success or not response_text.strip():
                print(f"{Fore.RED}❌ AI processing failed{Style.RESET_ALL}")
                return False
            
            print(f"{Fore.GREEN}✅ AI Response: '{response_text}'{Style.RESET_ALL}")
            print(f"⏱️ LLM Time: {llm_duration:.3f}s")
            
            # Step 3: Text-to-Speech with direct playback
            print(f"\n{Fore.YELLOW}🔊 STEP 3: AUDIO RESPONSE{Style.RESET_ALL}")
            
            # Generate temporary audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_audio_file = os.path.join(AUDIO_OUTPUT_DIR, f"response_{timestamp}.wav")
            
            tts_start_time = time.time()
            audio_path, tts_metadata, tts_success = self.tts_service.text_to_speech(response_text, temp_audio_file)
            tts_end_time = time.time()
            tts_duration = tts_end_time - tts_start_time
            
            if not tts_success:
                print(f"{Fore.RED}❌ TTS failed{Style.RESET_ALL}")
                return False
            
            print(f"⏱️ TTS Generation Time: {tts_duration:.3f}s")
            
            # Play the audio file
            print(f"🎵 Playing audio response...")
            playback_start_time = time.time()
            if self.play_audio_with_fallback(audio_path):
                playback_end_time = time.time()
                playback_duration = playback_end_time - playback_start_time
                
                print(f"{Fore.GREEN}✅ Audio played successfully!{Style.RESET_ALL}")
                print(f"⏱️ Audio Playback Time: {playback_duration:.3f}s")
                
                # Calculate total pipeline time
                pipeline_end_time = time.time()
                total_duration = pipeline_end_time - pipeline_start_time
                
                # Display metrics summary
                self.display_metrics_summary(stt_duration, llm_duration, tts_duration, playback_duration, total_duration)
                
                # Clean up temporary file after a short delay
                time.sleep(2)
                try:
                    os.remove(audio_path)
                except:
                    pass
                
                return True
            else:
                print(f"{Fore.RED}❌ Audio playback failed{Style.RESET_ALL}")
                print(f"💡 Audio saved to: {audio_path}")
                return False
            
        except Exception as e:
            pipeline_end_time = time.time()
            total_duration = pipeline_end_time - pipeline_start_time
            print(f"{Fore.RED}❌ Pipeline error: {e}{Style.RESET_ALL}")
            print(f"⏱️ Time elapsed before error: {total_duration:.3f}s")
            return False
    
    def run_continuous(self):
        """Run chatbot in continuous mode"""
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"🤖 CHATBOT FOR ELDERLY - SIMPLE MODE")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}📋 Instructions:{Style.RESET_ALL}")
        print(f"• Press Enter to start talking")
        print(f"• Speak clearly for {RECORD_DURATION} seconds")
        print(f"• The AI will respond with voice")
        print(f"• Type 'quit' to exit")
        
        while True:
            print(f"\n{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
            user_input = input(f"{Fore.CYAN}Press Enter to talk (or 'quit' to exit): {Style.RESET_ALL}")
            
            if user_input.lower() in ['quit', 'exit', 'q', 'thoát']:
                print(f"{Fore.YELLOW}👋 Goodbye! Tạm biệt!{Style.RESET_ALL}")
                break
            
            # Run the pipeline
            success = self.run_pipeline()
            
            if success:
                print(f"{Fore.GREEN}✅ Conversation completed successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Conversation failed. Please try again.{Style.RESET_ALL}")
            
            time.sleep(1)  # Brief pause before next interaction

def check_configuration():
    """Check if all required configurations are set"""
    missing_configs = []
    
    if not AZURE_SPEECH_KEY:
        missing_configs.append("AZURE_SPEECH_KEY")
    if not AZURE_SPEECH_REGION:
        missing_configs.append("AZURE_SPEECH_REGION")
    if not GEMINI_API_KEY:
        missing_configs.append("GEMINI_API_KEY")
    
    if missing_configs:
        print(f"{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("Missing required environment variables:")
        for config in missing_configs:
            print(f"   - {config}")
        print(f"\n💡 Please check your .env file")
        return False
    
    return True

def main():
    """Main function"""
    print(f"{Fore.BLUE}{'='*60}")
    print(f"🤖 SIMPLE CHATBOT FOR ELDERLY")
    print(f"STT + LLMs + TTS Pipeline")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Check configuration
    if not check_configuration():
        return False
    
    # Create chatbot instance
    chatbot = SimpleChatbot()
    
    # Initialize services
    if not chatbot.initialize_services():
        print(f"{Fore.RED}❌ Failed to initialize services{Style.RESET_ALL}")
        return False
    
    # Test connections
    if not chatbot.test_connections():
        print(f"{Fore.RED}❌ Service connection tests failed{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.GREEN}🎉 All systems ready!{Style.RESET_ALL}")
    
    # Run continuous chatbot
    try:
        chatbot.run_continuous()
        return True
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Chatbot interrupted by user{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Program interrupted{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)
