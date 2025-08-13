"""
STT Test - Test riêng cho Speech-to-Text với Azure Speech Services
Chạy: python stt_test.py
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
    from utils.metrics import MetricsCollector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Make sure to install required packages: pip install -r requirements.txt")
    sys.exit(1)

def setup_logging():
    """Setup logging configuration"""
    log_file = os.path.join(LOGS_DIR, f'stt_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
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

def test_stt_connection():
    """Test STT service connection"""
    print(f"\n{Fore.CYAN}🔍 Testing STT Connection...{Style.RESET_ALL}")
    
    try:
        stt_service = STTService(AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_SPEECH_LANGUAGE)
        
        if stt_service.test_connection():
            print(f"{Fore.GREEN}✅ STT Connection: SUCCESS{Style.RESET_ALL}")
            return stt_service
        else:
            print(f"{Fore.RED}❌ STT Connection: FAILED{Style.RESET_ALL}")
            return None
            
    except Exception as e:
        print(f"{Fore.RED}❌ STT Connection Error: {e}{Style.RESET_ALL}")
        return None

def test_microphone_recording():
    """Test microphone recording functionality"""
    print(f"\n{Fore.CYAN}🎤 Testing Microphone Recording...{Style.RESET_ALL}")
    
    try:
        stt_service = STTService(AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_SPEECH_LANGUAGE)
        metrics_collector = MetricsCollector()
        
        # Test audio recording
        print(f"{Fore.YELLOW}📹 Sẽ ghi âm trong {RECORD_DURATION} giây...{Style.RESET_ALL}")
        input("📝 Nhấn Enter để bắt đầu ghi âm (hãy chuẩn bị nói gì đó...)")
        
        # Record audio to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = os.path.join(AUDIO_INPUT_DIR, f"test_recording_{timestamp}.wav")
        
        start_time = metrics_collector.start_timer()
        audio_path, duration, success = stt_service.record_audio_to_file(
            audio_file, 
            RECORD_DURATION, 
            AUDIO_SAMPLE_RATE, 
            AUDIO_CHANNELS
        )
        
        if success:
            print(f"{Fore.GREEN}✅ Recording saved: {audio_path}{Style.RESET_ALL}")
            print(f"🎵 Duration: {duration:.2f} seconds")
            
            # Test recognition from recorded file
            print(f"\n{Fore.CYAN}🔄 Converting recorded audio to text...{Style.RESET_ALL}")
            
            recognized_text, confidence, recognition_success = stt_service.recognize_from_file(audio_path)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            # Create metrics
            word_count = len(recognized_text.split()) if recognized_text else 0
            audio_duration = stt_service.get_audio_duration(audio_path)
            
            stt_metrics = metrics_collector.create_stt_metrics(
                start_time=start_time,
                end_time=end_time,
                response_time=response_time,
                confidence_score=confidence,
                word_count=word_count,
                audio_duration=audio_duration,
                recognized_text=recognized_text,
                language=AZURE_SPEECH_LANGUAGE,
                success=recognition_success
            )
            
            # Display metrics
            metrics_collector.display_metrics(stt_metrics, "STT Recording Test Results")
            
            # Save metrics
            metrics_collector.save_metrics(stt_metrics)
            
            return recognition_success
        else:
            print(f"{Fore.RED}❌ Recording failed{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Microphone test error: {e}{Style.RESET_ALL}")
        return False

def test_live_recognition():
    """Test live microphone recognition"""
    print(f"\n{Fore.CYAN}🎙️ Testing Live Voice Recognition...{Style.RESET_ALL}")
    
    try:
        stt_service = STTService(AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_SPEECH_LANGUAGE)
        metrics_collector = MetricsCollector()
        
        print(f"{Fore.YELLOW}🎤 Chuẩn bị nói trong {RECORD_DURATION} giây...{Style.RESET_ALL}")
        input("📝 Nhấn Enter để bắt đầu nhận diện giọng nói...")
        
        start_time = metrics_collector.start_timer()
        recognized_text, confidence, success = stt_service.recognize_from_microphone(RECORD_DURATION)
        end_time, response_time = metrics_collector.end_timer(start_time)
        
        # Create metrics
        word_count = len(recognized_text.split()) if recognized_text else 0
        
        stt_metrics = metrics_collector.create_stt_metrics(
            start_time=start_time,
            end_time=end_time,
            response_time=response_time,
            confidence_score=confidence,
            word_count=word_count,
            audio_duration=RECORD_DURATION,
            recognized_text=recognized_text,
            language=AZURE_SPEECH_LANGUAGE,
            success=success
        )
        
        # Display metrics
        metrics_collector.display_metrics(stt_metrics, "STT Live Recognition Results")
        
        # Save metrics
        metrics_collector.save_metrics(stt_metrics)
        
        return success
        
    except Exception as e:
        print(f"{Fore.RED}❌ Live recognition error: {e}{Style.RESET_ALL}")
        return False

def test_sample_audio_files():
    """Test with sample audio files if available"""
    print(f"\n{Fore.CYAN}📁 Testing Sample Audio Files...{Style.RESET_ALL}")
    
    try:
        # Look for sample files in input directory
        sample_files = []
        if os.path.exists(AUDIO_INPUT_DIR):
            for file in os.listdir(AUDIO_INPUT_DIR):
                if file.lower().endswith(('.wav', '.mp3', '.flac')):
                    sample_files.append(os.path.join(AUDIO_INPUT_DIR, file))
        
        if not sample_files:
            print(f"{Fore.YELLOW}⚠️ No sample audio files found in {AUDIO_INPUT_DIR}{Style.RESET_ALL}")
            return True
        
        stt_service = STTService(AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_SPEECH_LANGUAGE)
        metrics_collector = MetricsCollector()
        
        for audio_file in sample_files[:3]:  # Test first 3 files
            print(f"\n{Fore.CYAN}🔄 Processing: {os.path.basename(audio_file)}{Style.RESET_ALL}")
            
            start_time = metrics_collector.start_timer()
            recognized_text, confidence, success = stt_service.recognize_from_file(audio_file)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            word_count = len(recognized_text.split()) if recognized_text else 0
            audio_duration = stt_service.get_audio_duration(audio_file)
            
            stt_metrics = metrics_collector.create_stt_metrics(
                start_time=start_time,
                end_time=end_time,
                response_time=response_time,
                confidence_score=confidence,
                word_count=word_count,
                audio_duration=audio_duration,
                recognized_text=recognized_text,
                language=AZURE_SPEECH_LANGUAGE,
                success=success
            )
            
            metrics_collector.display_metrics(stt_metrics, f"File: {os.path.basename(audio_file)}")
            metrics_collector.save_metrics(stt_metrics)
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Sample files test error: {e}{Style.RESET_ALL}")
        return False

def display_stt_info():
    """Display STT service information"""
    print(f"\n{Fore.MAGENTA}📋 STT SERVICE INFORMATION{Style.RESET_ALL}")
    print(f"🔧 Service: Azure Speech Services")
    print(f"🌍 Region: {AZURE_SPEECH_REGION}")
    print(f"🗣️ Language: {AZURE_SPEECH_LANGUAGE}")
    print(f"🎵 Audio Format: {AZURE_SPEECH_FORMAT}")
    print(f"⏱️ Record Duration: {RECORD_DURATION} seconds")
    print(f"📊 Sample Rate: {AUDIO_SAMPLE_RATE} Hz")
    print(f"🔊 Channels: {AUDIO_CHANNELS}")

def main():
    """Main test function"""
    print(f"{Fore.BLUE}{'='*60}")
    print(f"🎤 STT SERVICE TEST - AZURE SPEECH SERVICES")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting STT service test")
    
    # Display service info
    display_stt_info()
    
    # Check API key
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print(f"\n{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("📋 Please configure Azure Speech Services in .env file:")
        print("   AZURE_SPEECH_KEY=your_azure_speech_key")
        print("   AZURE_SPEECH_REGION=your_azure_region")
        return False
    
    test_results = {}
    
    # Test 1: Connection
    stt_service = test_stt_connection()
    test_results['connection'] = stt_service is not None
    
    if not stt_service:
        print(f"\n{Fore.RED}❌ Cannot proceed without STT connection{Style.RESET_ALL}")
        return False
    
    # Test 2: Live recognition
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 1: LIVE VOICE RECOGNITION")
    print(f"{'='*50}{Style.RESET_ALL}")
    test_results['live_recognition'] = test_live_recognition()
    
    # Test 3: Recording + Recognition
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 2: MICROPHONE RECORDING")
    print(f"{'='*50}{Style.RESET_ALL}")
    test_results['recording'] = test_microphone_recording()
    
    # Test 4: Sample files
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 3: SAMPLE AUDIO FILES")
    print(f"{'='*50}{Style.RESET_ALL}")
    test_results['sample_files'] = test_sample_audio_files()
    
    # Summary
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = f"{Fore.GREEN}✅ PASS" if result else f"{Fore.RED}❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}{Style.RESET_ALL}")
    
    print(f"\n📈 Overall Result: {passed_tests}/{total_tests} tests passed")
    print(f"📁 Logs saved to: {log_file}")
    
    if passed_tests == total_tests:
        print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED! STT service is working correctly.{Style.RESET_ALL}")
        return True
    else:
        print(f"\n{Fore.YELLOW}⚠️ Some tests failed. Check logs for details.{Style.RESET_ALL}")
        return False

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
