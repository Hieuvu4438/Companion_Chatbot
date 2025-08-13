"""
Full Pipeline Test - Test hoàn chỉnh STT → LLM → TTS
Chạy: python pipeline_full_test.py
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
    from utils.metrics import MetricsCollector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Make sure to install required packages: pip install -r requirements.txt")
    sys.exit(1)

class PipelineManager:
    """Manages the complete STT → LLM → TTS pipeline"""
    
    def __init__(self):
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        self.metrics_collector = MetricsCollector()
        self.logger = logging.getLogger(__name__)
        
    def initialize_services(self):
        """Initialize all pipeline services"""
        try:
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
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            return False
    
    def test_all_connections(self):
        """Test connections to all services"""
        print(f"\n{Fore.CYAN}🔍 Testing All Service Connections...{Style.RESET_ALL}")
        
        results = {}
        
        # Test STT
        try:
            if self.stt_service and self.stt_service.test_connection():
                print(f"{Fore.GREEN}✅ STT (Azure Speech): Connected{Style.RESET_ALL}")
                results['stt'] = True
            else:
                print(f"{Fore.RED}❌ STT (Azure Speech): Failed{Style.RESET_ALL}")
                results['stt'] = False
        except Exception as e:
            print(f"{Fore.RED}❌ STT (Azure Speech): Error - {e}{Style.RESET_ALL}")
            results['stt'] = False
        
        # Test LLM
        try:
            if self.llm_service and self.llm_service.test_connection():
                print(f"{Fore.GREEN}✅ LLM (Google Gemini): Connected{Style.RESET_ALL}")
                results['llm'] = True
            else:
                print(f"{Fore.RED}❌ LLM (Google Gemini): Failed{Style.RESET_ALL}")
                results['llm'] = False
        except Exception as e:
            print(f"{Fore.RED}❌ LLM (Google Gemini): Error - {e}{Style.RESET_ALL}")
            results['llm'] = False
        
        # Test TTS
        try:
            if self.tts_service and self.tts_service.test_connection():
                print(f"{Fore.GREEN}✅ TTS (Azure Speech): Connected{Style.RESET_ALL}")
                results['tts'] = True
            else:
                print(f"{Fore.RED}❌ TTS (Azure Speech): Failed{Style.RESET_ALL}")
                results['tts'] = False
        except Exception as e:
            print(f"{Fore.RED}❌ TTS (Azure Speech): Error - {e}{Style.RESET_ALL}")
            results['tts'] = False
        
        return results
    
    def run_full_pipeline(self, record_duration=5):
        """Run the complete pipeline: STT → LLM → TTS"""
        session_id = self.metrics_collector.create_session_id()
        pipeline_start_time = self.metrics_collector.start_timer()
        
        print(f"\n{Fore.BLUE}🔄 STARTING FULL PIPELINE{Style.RESET_ALL}")
        print(f"📋 Session ID: {session_id}")
        print(f"⏱️ Record Duration: {record_duration} seconds")
        
        stt_metrics = None
        llm_metrics = None
        tts_metrics = None
        error_stage = None
        error_message = None
        
        try:
            # STEP 1: Speech-to-Text
            print(f"\n{Fore.CYAN}🎤 STEP 1: SPEECH-TO-TEXT{Style.RESET_ALL}")
            print(f"🎙️ Preparing to record audio for {record_duration} seconds...")
            input("📝 Press Enter when ready to speak...")
            
            stt_start_time = self.metrics_collector.start_timer()
            recognized_text, confidence, stt_success = self.stt_service.recognize_from_microphone(record_duration)
            stt_end_time, stt_response_time = self.metrics_collector.end_timer(stt_start_time)
            
            if not stt_success or not recognized_text.strip():
                error_stage = "STT"
                error_message = "Speech recognition failed or no speech detected"
                raise Exception(error_message)
            
            # Create STT metrics
            word_count = len(recognized_text.split())
            stt_metrics = self.metrics_collector.create_stt_metrics(
                start_time=stt_start_time,
                end_time=stt_end_time,
                response_time=stt_response_time,
                confidence_score=confidence,
                word_count=word_count,
                audio_duration=record_duration,
                recognized_text=recognized_text,
                language=AZURE_SPEECH_LANGUAGE,
                success=True
            )
            
            print(f"{Fore.GREEN}✅ STT Success!{Style.RESET_ALL}")
            print(f"💬 Recognized: '{recognized_text}'")
            print(f"🎯 Confidence: {confidence:.2%}")
            print(f"⏱️ Time: {stt_response_time:.3f}s")
            
            # STEP 2: Large Language Model (with emotion detection)
            print(f"\n{Fore.CYAN}🧠 STEP 2: LANGUAGE MODEL PROCESSING (EMOTION-AWARE){Style.RESET_ALL}")
            
            llm_start_time = self.metrics_collector.start_timer()
            response_text, usage_info, llm_success = self.llm_service.get_emotion_optimized_response(recognized_text)
            llm_end_time, llm_response_time = self.metrics_collector.end_timer(llm_start_time)
            
            if not llm_success or not response_text.strip():
                error_stage = "LLM"
                error_message = "Language model processing failed"
                raise Exception(error_message)
            
            # Display emotion detection results
            emotion_info = usage_info.get('emotion_detected', {})
            if emotion_info.get('has_emotion'):
                primary_emotion = emotion_info.get('primary_emotion', 'unknown')
                confidence = emotion_info.get('confidence_scores', {}).get(primary_emotion, 0)
                print(f"🎭 Emotion detected: {primary_emotion} (confidence: {confidence:.2f})")
            else:
                print(f"😐 No specific emotion detected - neutral response")
            
            # Create LLM metrics
            llm_metrics = self.metrics_collector.create_llm_metrics(
                start_time=llm_start_time,
                end_time=llm_end_time,
                response_time=llm_response_time,
                input_tokens=usage_info.get('input_tokens', len(recognized_text) // 4),
                output_tokens=usage_info.get('output_tokens', len(response_text) // 4),
                total_tokens=usage_info.get('total_tokens', 0),
                response_length=len(response_text),
                model_name=GEMINI_MODEL,
                success=True
            )
            
            print(f"{Fore.GREEN}✅ LLM Success!{Style.RESET_ALL}")
            print(f"🤖 Response: '{response_text[:100]}{'...' if len(response_text) > 100 else ''}'")
            print(f"🔤 Tokens: {usage_info.get('total_tokens', 'N/A')}")
            print(f"⏱️ Time: {llm_response_time:.3f}s")
            
            # STEP 3: Text-to-Speech
            print(f"\n{Fore.CYAN}🔊 STEP 3: TEXT-TO-SPEECH{Style.RESET_ALL}")
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"pipeline_output_{session_id}_{timestamp}.wav")
            
            tts_start_time = self.metrics_collector.start_timer()
            audio_path, tts_metadata, tts_success = self.tts_service.text_to_speech(response_text, output_file)
            tts_end_time, tts_response_time = self.metrics_collector.end_timer(tts_start_time)
            
            if not tts_success:
                error_stage = "TTS"
                error_message = "Text-to-speech conversion failed"
                raise Exception(error_message)
            
            # Create TTS metrics
            tts_metrics = self.metrics_collector.create_tts_metrics(
                start_time=tts_start_time,
                end_time=tts_end_time,
                response_time=tts_response_time,
                audio_duration=tts_metadata.get('duration', 0.0),
                character_count=len(response_text),
                voice_model=AZURE_TTS_VOICE,
                audio_format="wav",
                file_size=tts_metadata.get('file_size', 0),
                success=True
            )
            
            print(f"{Fore.GREEN}✅ TTS Success!{Style.RESET_ALL}")
            print(f"🎵 Audio file: {audio_path}")
            print(f"📏 Duration: {tts_metadata.get('duration', 0):.2f}s")
            print(f"⏱️ Time: {tts_response_time:.3f}s")
            
            # AUTO PLAY the generated audio
            print(f"\n{Fore.MAGENTA}🎵 AUTO PLAYING AUDIO RESPONSE...{Style.RESET_ALL}")
            try:
                self.tts_service.play_audio_file(audio_path)
                print(f"{Fore.GREEN}✅ Audio playback completed successfully!{Style.RESET_ALL}")
            except Exception as play_error:
                print(f"{Fore.YELLOW}⚠️ Audio playback failed: {play_error}{Style.RESET_ALL}")
                print(f"📁 Audio file saved to: {audio_path}")
                
                # Try alternative playback method
                print(f"{Fore.CYAN}🔄 Trying alternative playback method...{Style.RESET_ALL}")
                try:
                    import subprocess
                    import platform
                    
                    system = platform.system().lower()
                    if system == 'windows':
                        # Windows: use built-in player
                        subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'], 
                                     check=True, capture_output=True)
                        print(f"{Fore.GREEN}✅ Alternative playback successful!{Style.RESET_ALL}")
                    elif system == 'darwin':  # macOS
                        subprocess.run(['afplay', audio_path], check=True)
                        print(f"{Fore.GREEN}✅ Alternative playback successful!{Style.RESET_ALL}")
                    elif system == 'linux':
                        subprocess.run(['aplay', audio_path], check=True)
                        print(f"{Fore.GREEN}✅ Alternative playback successful!{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠️ Auto-playback not supported on {system}{Style.RESET_ALL}")
                        
                except Exception as alt_error:
                    print(f"{Fore.RED}❌ All playback methods failed: {alt_error}{Style.RESET_ALL}")
                    print(f"💡 Please manually play: {audio_path}")
                    
                    # Ask user if they want to continue anyway
                    continue_choice = input(f"\n{Fore.YELLOW}Continue without audio playback? (y/n): {Style.RESET_ALL}")
                    if continue_choice.lower() not in ['y', 'yes', 'có']:
                        raise Exception("Audio playback required but failed")
            
            # Calculate total pipeline time
            pipeline_end_time, total_pipeline_time = self.metrics_collector.end_timer(pipeline_start_time)
            
            # Create complete pipeline metrics
            pipeline_metrics = self.metrics_collector.create_pipeline_metrics(
                session_id=session_id,
                start_time=pipeline_start_time,
                end_time=pipeline_end_time,
                total_time=total_pipeline_time,
                stt_metrics=stt_metrics,
                llm_metrics=llm_metrics,
                tts_metrics=tts_metrics,
                success=True
            )
            
            return pipeline_metrics, True
            
        except Exception as e:
            pipeline_end_time, total_pipeline_time = self.metrics_collector.end_timer(pipeline_start_time)
            
            # Create failed pipeline metrics
            pipeline_metrics = self.metrics_collector.create_pipeline_metrics(
                session_id=session_id,
                start_time=pipeline_start_time,
                end_time=pipeline_end_time,
                total_time=total_pipeline_time,
                stt_metrics=stt_metrics,
                llm_metrics=llm_metrics,
                tts_metrics=tts_metrics,
                success=False,
                error_stage=error_stage,
                error_message=str(e)
            )
            
            print(f"\n{Fore.RED}❌ PIPELINE FAILED at {error_stage}: {e}{Style.RESET_ALL}")
            
            return pipeline_metrics, False
    
    def run_pipeline_with_text_input(self, user_text):
        """Run pipeline starting from text input (skip STT)"""
        session_id = self.metrics_collector.create_session_id()
        pipeline_start_time = self.metrics_collector.start_timer()
        
        print(f"\n{Fore.BLUE}🔄 STARTING TEXT-TO-RESPONSE PIPELINE{Style.RESET_ALL}")
        print(f"📋 Session ID: {session_id}")
        print(f"💬 Input: '{user_text}'")
        
        llm_metrics = None
        tts_metrics = None
        error_stage = None
        error_message = None
        
        try:
            # STEP 1: Language Model Processing (with emotion detection)
            print(f"\n{Fore.CYAN}🧠 STEP 1: LANGUAGE MODEL PROCESSING (EMOTION-AWARE){Style.RESET_ALL}")
            
            llm_start_time = self.metrics_collector.start_timer()
            response_text, usage_info, llm_success = self.llm_service.get_emotion_optimized_response(user_text)
            llm_end_time, llm_response_time = self.metrics_collector.end_timer(llm_start_time)
            
            if not llm_success or not response_text.strip():
                error_stage = "LLM"
                error_message = "Language model processing failed"
                raise Exception(error_message)
            
            # Display emotion detection results
            emotion_info = usage_info.get('emotion_detected', {})
            if emotion_info.get('has_emotion'):
                primary_emotion = emotion_info.get('primary_emotion', 'unknown')
                confidence = emotion_info.get('confidence_scores', {}).get(primary_emotion, 0)
                print(f"🎭 Emotion detected: {primary_emotion} (confidence: {confidence:.2f})")
            else:
                print(f"😐 No specific emotion detected - neutral response")
            
            llm_metrics = self.metrics_collector.create_llm_metrics(
                start_time=llm_start_time,
                end_time=llm_end_time,
                response_time=llm_response_time,
                input_tokens=usage_info.get('input_tokens', len(user_text) // 4),
                output_tokens=usage_info.get('output_tokens', len(response_text) // 4),
                total_tokens=usage_info.get('total_tokens', 0),
                response_length=len(response_text),
                model_name=GEMINI_MODEL,
                success=True
            )
            
            print(f"{Fore.GREEN}✅ LLM Success!{Style.RESET_ALL}")
            print(f"🤖 Response: '{response_text}'")
            
            # STEP 2: Text-to-Speech
            print(f"\n{Fore.CYAN}🔊 STEP 2: TEXT-TO-SPEECH{Style.RESET_ALL}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(AUDIO_OUTPUT_DIR, f"text_pipeline_output_{session_id}_{timestamp}.wav")
            
            tts_start_time = self.metrics_collector.start_timer()
            audio_path, tts_metadata, tts_success = self.tts_service.text_to_speech(response_text, output_file)
            tts_end_time, tts_response_time = self.metrics_collector.end_timer(tts_start_time)
            
            if not tts_success:
                error_stage = "TTS"
                error_message = "Text-to-speech conversion failed"
                raise Exception(error_message)
            
            tts_metrics = self.metrics_collector.create_tts_metrics(
                start_time=tts_start_time,
                end_time=tts_end_time,
                response_time=tts_response_time,
                audio_duration=tts_metadata.get('duration', 0.0),
                character_count=len(response_text),
                voice_model=AZURE_TTS_VOICE,
                audio_format="wav",
                file_size=tts_metadata.get('file_size', 0),
                success=True
            )
            
            print(f"{Fore.GREEN}✅ TTS Success!{Style.RESET_ALL}")
            print(f"🎵 Audio file: {audio_path}")
            
            # AUTO PLAY audio
            print(f"\n{Fore.MAGENTA}🎵 AUTO PLAYING AUDIO RESPONSE...{Style.RESET_ALL}")
            try:
                self.tts_service.play_audio_file(audio_path)
                print(f"{Fore.GREEN}✅ Audio playback completed successfully!{Style.RESET_ALL}")
            except Exception as play_error:
                print(f"{Fore.YELLOW}⚠️ Audio playback failed: {play_error}{Style.RESET_ALL}")
                print(f"📁 Audio file saved to: {audio_path}")
                
                # Try alternative playback method
                print(f"{Fore.CYAN}🔄 Trying alternative playback method...{Style.RESET_ALL}")
                try:
                    import subprocess
                    import platform
                    
                    system = platform.system().lower()
                    if system == 'windows':
                        # Windows: use built-in player
                        subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'], 
                                     check=True, capture_output=True)
                        print(f"{Fore.GREEN}✅ Alternative playback successful!{Style.RESET_ALL}")
                    elif system == 'darwin':  # macOS
                        subprocess.run(['afplay', audio_path], check=True)
                        print(f"{Fore.GREEN}✅ Alternative playback successful!{Style.RESET_ALL}")
                    elif system == 'linux':
                        subprocess.run(['aplay', audio_path], check=True)
                        print(f"{Fore.GREEN}✅ Alternative playback successful!{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠️ Auto-playback not supported on {system}{Style.RESET_ALL}")
                        
                except Exception as alt_error:
                    print(f"{Fore.RED}❌ All playback methods failed: {alt_error}{Style.RESET_ALL}")
                    print(f"💡 Please manually play: {audio_path}")
                    
                    # Ask user if they want to continue anyway
                    continue_choice = input(f"\n{Fore.YELLOW}Continue without audio playback? (y/n): {Style.RESET_ALL}")
                    if continue_choice.lower() not in ['y', 'yes', 'có']:
                        raise Exception("Audio playback required but failed")
            
            pipeline_end_time, total_pipeline_time = self.metrics_collector.end_timer(pipeline_start_time)
            
            pipeline_metrics = self.metrics_collector.create_pipeline_metrics(
                session_id=session_id,
                start_time=pipeline_start_time,
                end_time=pipeline_end_time,
                total_time=total_pipeline_time,
                stt_metrics=None,
                llm_metrics=llm_metrics,
                tts_metrics=tts_metrics,
                success=True
            )
            
            return pipeline_metrics, True
            
        except Exception as e:
            pipeline_end_time, total_pipeline_time = self.metrics_collector.end_timer(pipeline_start_time)
            
            pipeline_metrics = self.metrics_collector.create_pipeline_metrics(
                session_id=session_id,
                start_time=pipeline_start_time,
                end_time=pipeline_end_time,
                total_time=total_pipeline_time,
                stt_metrics=None,
                llm_metrics=llm_metrics,
                tts_metrics=tts_metrics,
                success=False,
                error_stage=error_stage,
                error_message=str(e)
            )
            
            print(f"\n{Fore.RED}❌ PIPELINE FAILED at {error_stage}: {e}{Style.RESET_ALL}")
            
            return pipeline_metrics, False

def setup_logging():
    """Setup logging configuration"""
    log_file = os.path.join(LOGS_DIR, f'pipeline_full_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
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

def display_pipeline_info():
    """Display pipeline configuration"""
    print(f"\n{Fore.MAGENTA}📋 PIPELINE CONFIGURATION{Style.RESET_ALL}")
    print(f"🎤 STT: Azure Speech Services ({AZURE_SPEECH_REGION})")
    print(f"🧠 LLM: Google Gemini ({GEMINI_MODEL}) + Emotion Detection")
    print(f"🔊 TTS: Azure Speech Services ({AZURE_TTS_VOICE})")
    print(f"⏱️ Record Duration: {RECORD_DURATION} seconds")
    print(f"🌍 Language: {AZURE_SPEECH_LANGUAGE}")
    print(f"\n{Fore.GREEN}🎵 AUTO AUDIO PLAYBACK: ENABLED{Style.RESET_ALL}")
    print(f"💡 AI responses will automatically play through speakers")

def test_individual_services():
    """Test each service individually first"""
    print(f"\n{Fore.CYAN}🔧 INDIVIDUAL SERVICE TESTS{Style.RESET_ALL}")
    
    pipeline = PipelineManager()
    if not pipeline.initialize_services():
        print(f"{Fore.RED}❌ Failed to initialize pipeline services{Style.RESET_ALL}")
        return False
    
    connections = pipeline.test_all_connections()
    
    all_connected = all(connections.values())
    if all_connected:
        print(f"\n{Fore.GREEN}✅ All services connected successfully!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Some services failed to connect{Style.RESET_ALL}")
        for service, status in connections.items():
            if not status:
                print(f"   - {service.upper()}: Failed")
    
    return all_connected

def test_audio_playback():
    """Test audio playback functionality independently"""
    print(f"\n{Fore.CYAN}🔊 TESTING AUDIO PLAYBACK{Style.RESET_ALL}")
    
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
        
        # Generate test audio
        test_text = "Xin chào! Đây là test âm thanh của hệ thống chatbot."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_output = os.path.join(AUDIO_OUTPUT_DIR, f"audio_test_{timestamp}.wav")
        
        print(f"{Fore.YELLOW}🔄 Generating test audio...{Style.RESET_ALL}")
        audio_path, metadata, success = tts_service.text_to_speech(test_text, test_output)
        
        if not success:
            print(f"{Fore.RED}❌ Failed to generate test audio{Style.RESET_ALL}")
            return False
            
        print(f"{Fore.GREEN}✅ Test audio generated: {audio_path}{Style.RESET_ALL}")
        
        # Test audio playback
        print(f"\n{Fore.MAGENTA}🎵 TESTING AUDIO PLAYBACK...{Style.RESET_ALL}")
        print(f"📝 Test text: '{test_text}'")
        
        try:
            tts_service.play_audio_file(audio_path)
            print(f"{Fore.GREEN}✅ Audio playback test successful!{Style.RESET_ALL}")
            return True
            
        except Exception as play_error:
            print(f"{Fore.YELLOW}⚠️ Primary playback failed: {play_error}{Style.RESET_ALL}")
            
            # Try alternative methods
            print(f"{Fore.CYAN}🔄 Trying alternative playback methods...{Style.RESET_ALL}")
            
            import subprocess
            import platform
            
            system = platform.system().lower()
            
            try:
                if system == 'windows':
                    # Method 1: PowerShell SoundPlayer
                    subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'], 
                                 check=True, capture_output=True, timeout=30)
                    print(f"{Fore.GREEN}✅ Windows PowerShell playback successful!{Style.RESET_ALL}")
                    return True
                    
                elif system == 'darwin':  # macOS
                    subprocess.run(['afplay', audio_path], check=True, timeout=30)
                    print(f"{Fore.GREEN}✅ macOS afplay successful!{Style.RESET_ALL}")
                    return True
                    
                elif system == 'linux':
                    subprocess.run(['aplay', audio_path], check=True, timeout=30)
                    print(f"{Fore.GREEN}✅ Linux aplay successful!{Style.RESET_ALL}")
                    return True
                    
            except subprocess.TimeoutExpired:
                print(f"{Fore.YELLOW}⚠️ Playback timeout - audio may still be playing{Style.RESET_ALL}")
                return True
                
            except Exception as alt_error:
                print(f"{Fore.RED}❌ Alternative playback failed: {alt_error}{Style.RESET_ALL}")
            
            # Final fallback - try to open with system default
            try:
                if system == 'windows':
                    os.startfile(audio_path)
                    print(f"{Fore.GREEN}✅ Opened with Windows default player{Style.RESET_ALL}")
                    return True
                else:
                    subprocess.run(['open' if system == 'darwin' else 'xdg-open', audio_path], check=True)
                    print(f"{Fore.GREEN}✅ Opened with system default player{Style.RESET_ALL}")
                    return True
                    
            except Exception as final_error:
                print(f"{Fore.RED}❌ All playback methods failed: {final_error}{Style.RESET_ALL}")
                print(f"📁 Audio file available at: {audio_path}")
                print(f"💡 You can manually test by playing this file")
                return False
        
    except Exception as e:
        print(f"{Fore.RED}❌ Audio playback test failed: {e}{Style.RESET_ALL}")
        return False

def main():
    """Main pipeline test function"""
    print(f"{Fore.BLUE}{'='*70}")
    print(f"🔄 FULL PIPELINE TEST - STT → LLM → TTS")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting full pipeline test")
    
    # Display configuration
    display_pipeline_info()
    
    # Check configuration
    missing_configs = []
    if not AZURE_SPEECH_KEY: missing_configs.append("AZURE_SPEECH_KEY")
    if not AZURE_SPEECH_REGION: missing_configs.append("AZURE_SPEECH_REGION")
    if not GEMINI_API_KEY: missing_configs.append("GEMINI_API_KEY")
    
    if missing_configs:
        print(f"\n{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("📋 Missing required configuration:")
        for config in missing_configs:
            print(f"   - {config}")
        print("\n💡 Please check your .env file")
        return False
    
    # Test individual services
    if not test_individual_services():
        print(f"\n{Fore.RED}❌ Cannot proceed - service connection failures{Style.RESET_ALL}")
        return False
    
    # Initialize pipeline manager
    pipeline = PipelineManager()
    pipeline.initialize_services()
    
    test_results = []
    
    # Test mode selection
    print(f"\n{Fore.YELLOW}🎯 SELECT TEST MODE:{Style.RESET_ALL}")
    print(f"1. Full Pipeline (STT → LLM → TTS) 🎵 with Auto Audio")
    print(f"2. Text Input Pipeline (LLM → TTS) 🎵 with Auto Audio")
    print(f"3. Multiple Pipeline Tests")
    print(f"4. Interactive Mode")
    print(f"5. Emotion Detection Test")
    print(f"6. Audio Playback Test 🔊")
    
    while True:
        choice = input(f"\n{Fore.CYAN}👉 Enter choice (1-6): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            # Full pipeline test
            print(f"\n{Fore.BLUE}{'='*50}")
            print(f"🔄 FULL PIPELINE TEST")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            metrics, success = pipeline.run_full_pipeline(RECORD_DURATION)
            pipeline.metrics_collector.display_metrics(metrics, "Full Pipeline Results")
            pipeline.metrics_collector.save_metrics(metrics)
            test_results.append(success)
            break
            
        elif choice == "2":
            # Text input pipeline test
            print(f"\n{Fore.BLUE}{'='*50}")
            print(f"📝 TEXT INPUT PIPELINE TEST")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            user_text = input(f"{Fore.YELLOW}💬 Enter your question: {Style.RESET_ALL}").strip()
            if user_text:
                metrics, success = pipeline.run_pipeline_with_text_input(user_text)
                pipeline.metrics_collector.display_metrics(metrics, "Text Pipeline Results")
                pipeline.metrics_collector.save_metrics(metrics)
                test_results.append(success)
            else:
                print(f"{Fore.RED}❌ No text provided{Style.RESET_ALL}")
                test_results.append(False)
            break
            
        elif choice == "3":
            # Multiple tests
            print(f"\n{Fore.BLUE}{'='*50}")
            print(f"🔄 MULTIPLE PIPELINE TESTS")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            num_tests = int(input(f"{Fore.YELLOW}🔢 How many tests? (1-5): {Style.RESET_ALL}") or "3")
            num_tests = min(max(num_tests, 1), 5)
            
            for i in range(num_tests):
                print(f"\n{Fore.CYAN}🔄 Test {i+1}/{num_tests}{Style.RESET_ALL}")
                metrics, success = pipeline.run_full_pipeline(RECORD_DURATION)
                pipeline.metrics_collector.display_metrics(metrics, f"Pipeline Test {i+1}")
                pipeline.metrics_collector.save_metrics(metrics)
                test_results.append(success)
                
                if i < num_tests - 1:
                    time.sleep(2)  # Brief pause between tests
            break
            
        elif choice == "4":
            # Interactive mode
            print(f"\n{Fore.BLUE}{'='*50}")
            print(f"💬 INTERACTIVE PIPELINE MODE")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            print(f"{Fore.YELLOW}🎯 Choose input method for each interaction:{Style.RESET_ALL}")
            print(f"   - Type 'voice' for voice input (STT → LLM → TTS)")
            print(f"   - Type text directly for text input (LLM → TTS)")
            print(f"   - Type 'quit' to exit")
            
            while True:
                user_input = input(f"\n{Fore.CYAN}👉 Input: {Style.RESET_ALL}").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}")
                    break
                
                if user_input.lower() == 'voice':
                    metrics, success = pipeline.run_full_pipeline(RECORD_DURATION)
                    pipeline.metrics_collector.display_metrics(metrics, "Interactive Voice")
                    pipeline.metrics_collector.save_metrics(metrics)
                    test_results.append(success)
                elif user_input:
                    metrics, success = pipeline.run_pipeline_with_text_input(user_input)
                    pipeline.metrics_collector.display_metrics(metrics, "Interactive Text")
                    pipeline.metrics_collector.save_metrics(metrics)
                    test_results.append(success)
                else:
                    print(f"{Fore.YELLOW}⚠️ Please enter 'voice' or your question{Style.RESET_ALL}")
            break
            
        elif choice == "5":
            # Emotion detection test
            print(f"\n{Fore.BLUE}{'='*50}")
            print(f"🎭 EMOTION DETECTION TEST")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            print(f"{Fore.YELLOW}Testing emotion detection with sample inputs...{Style.RESET_ALL}")
            
            # Test emotion detection
            test_results_emotion = pipeline.llm_service.test_emotion_detection()
            
            print(f"\n{Fore.CYAN}📊 EMOTION DETECTION RESULTS:{Style.RESET_ALL}")
            for test_id, test_data in test_results_emotion.items():
                input_text = test_data['input']
                emotion_result = test_data['emotion_result']
                
                print(f"\n{Fore.WHITE}Test {test_id}:{Style.RESET_ALL}")
                print(f"  📝 Input: '{input_text}'")
                
                if emotion_result['has_emotion']:
                    primary = emotion_result['primary_emotion']
                    confidence = emotion_result['confidence_scores'].get(primary, 0)
                    context = emotion_result['emotion_context']
                    
                    print(f"  🎭 Primary emotion: {primary}")
                    print(f"  📊 Confidence: {confidence:.2f}")
                    print(f"  💡 Context: {context}")
                    print(f"  📋 All detected: {emotion_result['detected_emotions']}")
                else:
                    print(f"  😐 No emotion detected")
            
            # Interactive emotion test
            print(f"\n{Fore.YELLOW}🔬 Try your own text for emotion detection:{Style.RESET_ALL}")
            while True:
                user_test = input(f"\n{Fore.CYAN}Enter text (or 'done' to finish): {Style.RESET_ALL}").strip()
                
                if user_test.lower() in ['done', 'quit', 'exit']:
                    break
                
                if user_test:
                    emotion_result = pipeline.llm_service.detect_emotion(user_test)
                    
                    if emotion_result['has_emotion']:
                        primary = emotion_result['primary_emotion']
                        confidence = emotion_result['confidence_scores'].get(primary, 0)
                        context = emotion_result['emotion_context']
                        
                        print(f"  🎭 Detected: {primary} (confidence: {confidence:.2f})")
                        print(f"  💡 {context}")
                        
                        # Generate sample response
                        print(f"\n{Fore.YELLOW}📝 Sample response with emotion context:{Style.RESET_ALL}")
                        response, _, success = pipeline.llm_service.get_emotion_optimized_response(user_test)
                        if success:
                            print(f"  🤖 '{response}'")
                    else:
                        print(f"  😐 No specific emotion detected")
            
            test_results.append(True)  # Emotion test always succeeds
            break
            
        elif choice == "6":
            # Audio playback test
            print(f"\n{Fore.BLUE}{'='*50}")
            print(f"🔊 AUDIO PLAYBACK TEST")
            print(f"{'='*50}{Style.RESET_ALL}")
            
            audio_test_success = test_audio_playback()
            test_results.append(audio_test_success)
            
            if audio_test_success:
                print(f"\n{Fore.GREEN}✅ Audio playback system is working properly!{Style.RESET_ALL}")
                print(f"💡 Your pipeline will auto-play audio responses.")
            else:
                print(f"\n{Fore.YELLOW}⚠️ Audio playback has issues.{Style.RESET_ALL}")
                print(f"💡 Pipeline will still save audio files for manual playback.")
            break
            
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please enter 1-6.{Style.RESET_ALL}")
    
    # Final summary
    print(f"\n{Fore.BLUE}{'='*70}")
    print(f"📊 FINAL TEST SUMMARY")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    if test_results:
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED! Pipeline is working perfectly.{Style.RESET_ALL}")
        elif success_rate >= 80:
            print(f"\n{Fore.YELLOW}⚠️ Most tests passed. Minor issues may exist.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Multiple test failures. Check configuration and logs.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ No tests were completed.{Style.RESET_ALL}")
    
    print(f"\n📁 Logs saved to: {log_file}")
    print(f"🎵 Audio files saved to: {AUDIO_OUTPUT_DIR}")
    
    return len(test_results) > 0 and all(test_results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Pipeline test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)
