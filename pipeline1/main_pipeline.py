#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline1 - Google Cloud Voice Chatbot for Elderly Care
=======================================================

Main pipeline integrating:
- Google Cloud Speech-to-Text (STT)
- Google Gemini LLM
- Google Cloud Text-to-Speech (TTS)
- Comprehensive metrics tracking
- Audio recording and playback

Author: IEC Team
Version: 1.0.0
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from config import *

# Import utility modules
from utils import (
    GoogleSTTService,
    GeminiLLMService, 
    GoogleTTSService,
    MetricsCollector,
    AudioRecorder,
    AudioPlayer
)


class ElderVoiceChatbotPipeline:
    """
    Pipeline chính cho chatbot hỗ trợ người cao tuổi
    """
    
    def __init__(self):
        """Khởi tạo pipeline"""
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.stt_service = None
        self.llm_service = None  
        self.tts_service = None
        self.metrics = MetricsCollector(
            save_to_file=SAVE_METRICS_TO_FILE,
            metrics_file=METRICS_FILE
        )
        self.audio_recorder = AudioRecorder(
            sample_rate=AUDIO_SAMPLE_RATE,
            channels=AUDIO_CHANNELS,
            chunk_size=AUDIO_CHUNK_SIZE
        )
        self.audio_player = AudioPlayer()
        
        # Pipeline state
        self.is_initialized = False
        self.conversation_count = 0
        
        print("🚀 Elder Voice Chatbot Pipeline khởi tạo...")
        
    def _setup_logging(self):
        """Thiết lập logging"""
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT,
            handlers=[
                logging.FileHandler(
                    os.path.join(LOGS_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"),
                    encoding='utf-8'
                ),
                logging.StreamHandler()
            ]
        )
        
    def initialize(self) -> bool:
        """
        Khởi tạo tất cả services
        
        Returns:
            bool: True nếu khởi tạo thành công
        """
        try:
            print("🔧 Đang khởi tạo các services...")
            
            # Kiểm tra credentials và API keys
            if not self._validate_credentials():
                return False
                
            # Initialize STT Service
            print("🎤 Khởi tạo Google STT Service...")
            self.stt_service = GoogleSTTService(
                credentials_path=GOOGLE_APPLICATION_CREDENTIALS
            )
            
            # Initialize LLM Service  
            print("🤖 Khởi tạo Gemini LLM Service...")
            self.llm_service = GeminiLLMService(
                api_key=GEMINI_API_KEY,
                model_name=GEMINI_MODEL
            )
            
            # Initialize TTS Service
            print("🔊 Khởi tạo Google TTS Service...")
            self.tts_service = GoogleTTSService(
                credentials_path=GOOGLE_APPLICATION_CREDENTIALS
            )
            
            # Test connections
            print("🧪 Testing service connections...")
            
            if not self.stt_service.test_connection():
                print("❌ STT service connection failed")
                return False
                
            if not self.llm_service.test_connection():
                print("❌ LLM service connection failed") 
                return False
                
            if not self.tts_service.test_connection():
                print("❌ TTS service connection failed")
                return False
                
            self.is_initialized = True
            print("✅ Tất cả services đã khởi tạo thành công!")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi khởi tạo pipeline: {e}")
            print(f"❌ Lỗi khởi tạo pipeline: {e}")
            return False
            
    def _validate_credentials(self) -> bool:
        """Kiểm tra credentials và API keys"""
        
        # Check Google Cloud credentials
        if not GOOGLE_APPLICATION_CREDENTIALS or not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
            print("❌ Google Cloud credentials không tồn tại!")
            print(f"   Cần file: {GOOGLE_APPLICATION_CREDENTIALS}")
            return False
            
        # Check Gemini API key
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key":
            print("❌ Gemini API key chưa được cấu hình!")
            print("   Cần update GEMINI_API_KEY trong .env")
            return False
            
        return True
        
    def run_full_pipeline(self, recording_duration: float = 5.0,
                         use_voice_detection: bool = False) -> Dict:
        """
        Chạy pipeline hoàn chỉnh: STT -> LLM -> TTS -> Audio Playback
        
        Args:
            recording_duration: Thời gian ghi âm (giây)
            use_voice_detection: Sử dụng voice activity detection
            
        Returns:
            Dict với kết quả pipeline
        """
        
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Pipeline chưa được khởi tạo",
                "pipeline_latency_ms": 0
            }
            
        pipeline_start_time = time.time()
        print(f"\n🚀 === BẮT ĐẦU PIPELINE #{self.conversation_count + 1} ===")
        
        try:
            # Step 1: Audio Recording
            print("\n🎤 BƯỚC 1: GHI ÂM")
            if use_voice_detection:
                success, audio_file, error = self.audio_recorder.record_with_silence_detection(
                    max_duration=recording_duration,
                    silence_threshold=SILENCE_THRESHOLD
                )
            else:
                success, audio_file, error = self.audio_recorder.record_audio(
                    duration=recording_duration
                )
                
            if not success:
                self.metrics.update_audio_metrics(recording_success=False)
                return {
                    "success": False,
                    "error": f"Lỗi ghi âm: {error}",
                    "pipeline_latency_ms": (time.time() - pipeline_start_time) * 1000
                }
                
            self.metrics.update_audio_metrics(recording_success=True)
            
            # Step 2: Speech-to-Text
            print("\n🎤 BƯỚC 2: SPEECH-TO-TEXT")
            stt_result = self.stt_service.transcribe_audio_file(audio_file)
            
            self.metrics.update_stt_metrics(
                latency=stt_result["latency_ms"] / 1000,
                confidence=stt_result["confidence"],
                success=stt_result["success"],
                error=stt_result["error"]
            )
            
            if not stt_result["success"]:
                self._cleanup_temp_file(audio_file)
                return {
                    "success": False,
                    "error": f"Lỗi STT: {stt_result['error']}",
                    "stt_result": stt_result,
                    "pipeline_latency_ms": (time.time() - pipeline_start_time) * 1000
                }
                
            user_text = stt_result["transcript"]
            print(f"👤 Người dùng nói: '{user_text}'")
            
            # Step 3: LLM Processing
            print("\n🤖 BƯỚC 3: LLM PROCESSING")
            llm_result = self.llm_service.generate_response(
                user_input=user_text,
                use_conversation_context=ENABLE_CONVERSATION_CONTEXT
            )
            
            self.metrics.update_llm_metrics(
                latency=llm_result["latency_ms"] / 1000,
                tokens=llm_result["token_count"],
                success=llm_result["success"],
                error=llm_result["error"]
            )
            
            if not llm_result["success"]:
                self._cleanup_temp_file(audio_file)
                return {
                    "success": False,
                    "error": f"Lỗi LLM: {llm_result['error']}",
                    "stt_result": stt_result,
                    "llm_result": llm_result,
                    "pipeline_latency_ms": (time.time() - pipeline_start_time) * 1000
                }
                
            ai_response = llm_result["response"]
            print(f"🤖 AI phản hồi: '{ai_response[:100]}...'")
            
            # Step 4: Text-to-Speech
            print("\n🔊 BƯỚC 4: TEXT-TO-SPEECH")
            
            # Create elder-friendly SSML if needed
            if len(ai_response) > 100:  # Longer responses get SSML treatment
                ssml_text = self.tts_service.create_elder_friendly_ssml(
                    text=ai_response,
                    emphasis_words=["quan trọng", "lưu ý", "nên", "cần"],
                    pause_duration="0.7s"
                )
                tts_result = self.tts_service.synthesize_with_ssml(ssml_text)
            else:
                tts_result = self.tts_service.synthesize_speech(ai_response)
                
            self.metrics.update_tts_metrics(
                latency=tts_result["latency_ms"] / 1000,
                char_count=tts_result["character_count"],
                success=tts_result["success"],
                error=tts_result["error"]
            )
            
            if not tts_result["success"]:
                self._cleanup_temp_file(audio_file)
                return {
                    "success": False,
                    "error": f"Lỗi TTS: {tts_result['error']}",
                    "stt_result": stt_result,
                    "llm_result": llm_result,
                    "tts_result": tts_result,
                    "pipeline_latency_ms": (time.time() - pipeline_start_time) * 1000
                }
                
            # Step 5: Audio Playback
            print("\n🔊 BƯỚC 5: PHÁT ÂM THANH")
            playback_success, playback_error = self.audio_player.play_audio_file(
                tts_result["audio_file"]
            )
            
            self.metrics.update_audio_metrics(playback_success=playback_success)
            
            # Calculate total pipeline latency
            pipeline_latency = time.time() - pipeline_start_time
            
            # Update pipeline metrics
            self.metrics.update_pipeline_metrics(
                end_to_end_latency=pipeline_latency,
                success=True
            )
            
            # Cleanup temporary files
            self._cleanup_temp_file(audio_file)
            if not SAVE_AUDIO_FILES:  # Only cleanup if not saving for debug
                self._cleanup_temp_file(tts_result["audio_file"])
                
            self.conversation_count += 1
            
            print(f"\n✅ === PIPELINE HOÀN THÀNH #{self.conversation_count} ===")
            print(f"⏱️  Tổng thời gian: {pipeline_latency * 1000:.1f}ms")
            
            return {
                "success": True,
                "user_text": user_text,
                "ai_response": ai_response,
                "stt_result": stt_result,
                "llm_result": llm_result,
                "tts_result": tts_result,
                "audio_played": playback_success,
                "playback_error": playback_error,
                "pipeline_latency_ms": pipeline_latency * 1000,
                "conversation_id": self.conversation_count
            }
            
        except Exception as e:
            pipeline_latency = time.time() - pipeline_start_time
            error_msg = f"Lỗi pipeline: {str(e)}"
            
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            
            # Update failed pipeline metrics
            self.metrics.update_pipeline_metrics(
                end_to_end_latency=pipeline_latency,
                success=False,
                error=error_msg
            )
            
            return {
                "success": False,
                "error": error_msg,
                "pipeline_latency_ms": pipeline_latency * 1000
            }
            
    def test_individual_components(self):
        """Test từng component riêng biệt"""
        print("\n🧪 === TESTING INDIVIDUAL COMPONENTS ===")
        
        if not self.is_initialized:
            print("❌ Pipeline chưa được khởi tạo!")
            return
            
        # Test STT
        print("\n🎤 Testing STT Component...")
        print("Ghi âm 3 giây để test STT...")
        success, audio_file, error = self.audio_recorder.record_audio(3.0)
        
        if success:
            stt_result = self.stt_service.transcribe_audio_file(audio_file)
            if stt_result["success"]:
                print(f"✅ STT: '{stt_result['transcript']}'")
                print(f"   Confidence: {stt_result['confidence']:.2f}")
                print(f"   Latency: {stt_result['latency_ms']:.1f}ms")
            else:
                print(f"❌ STT failed: {stt_result['error']}")
            self._cleanup_temp_file(audio_file)
        else:
            print(f"❌ Recording failed: {error}")
            
        # Test LLM
        print("\n🤖 Testing LLM Component...")
        test_question = "Tôi bị đau đầu, làm sao để giảm đau?"
        llm_result = self.llm_service.generate_response(test_question)
        
        if llm_result["success"]:
            print(f"✅ LLM Response: '{llm_result['response'][:100]}...'")
            print(f"   Tokens: {llm_result['token_count']}")
            print(f"   Latency: {llm_result['latency_ms']:.1f}ms")
        else:
            print(f"❌ LLM failed: {llm_result['error']}")
            
        # Test TTS
        print("\n🔊 Testing TTS Component...")
        test_text = "Xin chào, tôi là trợ lý AI hỗ trợ người cao tuổi."
        tts_result = self.tts_service.synthesize_speech(test_text)
        
        if tts_result["success"]:
            print(f"✅ TTS: Generated {os.path.basename(tts_result['audio_file'])}")
            print(f"   Characters: {tts_result['character_count']}")
            print(f"   Latency: {tts_result['latency_ms']:.1f}ms")
            
            # Test playback
            playback_success, playback_error = self.audio_player.play_audio_file(
                tts_result["audio_file"]
            )
            if playback_success:
                print("✅ Audio playback successful")
            else:
                print(f"❌ Audio playback failed: {playback_error}")
                
            self._cleanup_temp_file(tts_result["audio_file"])
        else:
            print(f"❌ TTS failed: {tts_result['error']}")
            
        print("\n🎯 Component testing completed!")
        
    def get_pipeline_status(self) -> Dict:
        """Lấy trạng thái pipeline"""
        return {
            "initialized": self.is_initialized,
            "conversation_count": self.conversation_count,
            "stt_ready": self.stt_service is not None,
            "llm_ready": self.llm_service is not None,
            "tts_ready": self.tts_service is not None,
            "metrics_enabled": METRICS_ENABLED,
            "debug_mode": DEBUG_MODE
        }
        
    def get_metrics_report(self) -> Dict:
        """Lấy báo cáo metrics"""
        return self.metrics.get_summary_report()
        
    def save_metrics(self, filename: Optional[str] = None):
        """Lưu metrics ra file"""
        self.metrics.save_metrics(filename)
        
    def reset_metrics(self):
        """Reset metrics"""
        self.metrics.reset_metrics()
        self.conversation_count = 0
        
    def _cleanup_temp_file(self, file_path: str):
        """Dọn dẹp file tạm thời"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            self.logger.warning(f"Could not cleanup temp file {file_path}: {e}")


def main():
    """Hàm main để chạy pipeline"""
    print("🎤🤖🔊 === ELDER VOICE CHATBOT PIPELINE ===\n")
    print("Chatbot hỗ trợ người cao tuổi sử dụng Google Cloud Services")
    print("=" * 60)
    
    # Hiển thị thông tin cấu hình
    print(f"📋 CẤU HÌNH HIỆN TẠI:")
    print(f"   STT: Google Cloud Speech ({GOOGLE_STT_LANGUAGE})")
    print(f"   LLM: {GEMINI_MODEL}")
    print(f"   TTS: Google Cloud TTS ({GOOGLE_TTS_VOICE_NAME})")
    print(f"   Audio: {AUDIO_SAMPLE_RATE}Hz, {AUDIO_CHANNELS} channel(s)")
    print()
    
    # Khởi tạo pipeline
    pipeline = ElderVoiceChatbotPipeline()
    
    print("🔧 Đang khởi tạo pipeline...")
    if not pipeline.initialize():
        print("❌ Không thể khởi tạo pipeline! Kiểm tra cấu hình.")
        return
        
    print("✅ Pipeline sẵn sàng!")
    
    while True:
        print("\n" + "=" * 60)
        print("MENU CHÍNH:")
        print("1. 🎤 Chạy pipeline hoàn chỉnh (Voice-to-Voice)")
        print("2. 🧪 Test từng component riêng")
        print("3. 📊 Xem báo cáo metrics")
        print("4. 💾 Lưu metrics ra file")
        print("5. 🔄 Reset metrics")
        print("6. ⚙️  Xem trạng thái pipeline")
        print("7. 🔧 Cấu hình nâng cao")
        print("0. 🚪 Thoát")
        
        choice = input("\nNhập lựa chọn (0-7): ").strip()
        
        if choice == "1":
            # Chạy pipeline hoàn chỉnh
            duration = input("Thời gian ghi âm (giây, mặc định 5): ").strip()
            duration = float(duration) if duration.replace('.', '').isdigit() else 5.0
            
            use_vad = input("Sử dụng Voice Activity Detection? (y/N): ").strip().lower() == 'y'
            
            print(f"\n🚀 Chuẩn bị pipeline với {duration}s ghi âm...")
            print("Nhấn Enter khi sẵn sàng...")
            input()
            
            result = pipeline.run_full_pipeline(
                recording_duration=duration,
                use_voice_detection=use_vad
            )
            
            if result["success"]:
                print(f"\n🎉 === KẾT QUẢ THÀNH CÔNG ===")
                print(f"👤 Người dùng: {result['user_text']}")
                print(f"🤖 AI: {result['ai_response']}")
                print(f"\n📈 PERFORMANCE:")
                print(f"   STT: {result['stt_result']['latency_ms']:.1f}ms")
                print(f"   LLM: {result['llm_result']['latency_ms']:.1f}ms") 
                print(f"   TTS: {result['tts_result']['latency_ms']:.1f}ms")
                print(f"   🏁 Tổng: {result['pipeline_latency_ms']:.1f}ms")
            else:
                print(f"\n💥 === LỖI PIPELINE ===")
                print(f"❌ {result['error']}")
                print(f"⏱️  Thời gian: {result['pipeline_latency_ms']:.1f}ms")
                
        elif choice == "2":
            # Test components
            pipeline.test_individual_components()
            
        elif choice == "3":
            # Xem metrics
            print("\n📊 === BÁO CÁO METRICS ===")
            report = pipeline.get_metrics_report()
            for section, data in report.items():
                print(f"\n{section}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                    
        elif choice == "4":
            # Lưu metrics
            filename = input("Tên file (Enter = mặc định): ").strip()
            pipeline.save_metrics(filename if filename else None)
            
        elif choice == "5":
            # Reset metrics
            confirm = input("Xác nhận reset metrics? (y/N): ").strip().lower()
            if confirm == 'y':
                pipeline.reset_metrics()
                print("✅ Đã reset metrics")
            else:
                print("Hủy reset")
                
        elif choice == "6":
            # Trạng thái pipeline
            status = pipeline.get_pipeline_status()
            print(f"\n⚙️  === TRẠNG THÁI PIPELINE ===")
            for key, value in status.items():
                print(f"  {key}: {'✅' if value else '❌'}")
                
        elif choice == "7":
            # Cấu hình nâng cao
            print("\n🔧 === CẤU HÌNH NÂNG CAO ===")
            print("1. Thay đổi giọng nói TTS")
            print("2. Cấu hình conversation history")
            print("3. Xem thông tin API usage")
            
            config_choice = input("Chọn (1-3): ").strip()
            
            if config_choice == "1":
                voices = pipeline.tts_service.get_elder_friendly_voices()
                print("\n🎵 GIỌNG NÓI CÓ SẴN:")
                for i, voice in enumerate(voices, 1):
                    recommended = "⭐" if voice["recommended"] else "  "
                    print(f"  {i}.{recommended} {voice['name']} - {voice['description']}")
                    
            elif config_choice == "2":
                current_length = pipeline.llm_service.max_history_length
                print(f"Độ dài conversation history hiện tại: {current_length}")
                new_length = input("Độ dài mới (1-10): ").strip()
                if new_length.isdigit():
                    pipeline.llm_service.set_conversation_history_length(int(new_length))
                    
            elif config_choice == "3":
                pricing = pipeline.tts_service.get_pricing_info()
                print("\n💰 THÔNG TIN PRICING:")
                for category, info in pricing.items():
                    if isinstance(info, dict):
                        print(f"  {category}:")
                        for key, value in info.items():
                            print(f"    {key}: {value}")
                    else:
                        print(f"  {category}: {info}")
                        
        elif choice == "0":
            print("\n👋 Đang lưu metrics và thoát...")
            pipeline.save_metrics()
            print("✅ Cảm ơn bạn đã sử dụng Elder Voice Chatbot Pipeline!")
            break
            
        else:
            print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    main()
