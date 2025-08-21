#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Hoàn Chỉnh
==================

Pipeline hoàn chỉnh STT (Assembly AI) + LLMs (Gemini) + TTS (VBEE AI)
cho chatbot hỗ trợ người cao tuổi
"""

import os
import sys
import time
import json
import threading
from datetime import datetime
from typing import Dict, Optional, Any, Tuple

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import *
    from stt_module import AssemblyAISTT, AudioRecorder
    from llm_module import GeminiLLM
    from tts_module import VBEETTS, AudioPlayer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Đảm bảo tất cả các module (stt_module.py, llm_module.py, tts_module.py) tồn tại")
    sys.exit(1)


class ElderCarePipeline:
    """Pipeline hoàn chỉnh cho chatbot hỗ trợ người cao tuổi"""
    
    def __init__(self):
        """Khởi tạo pipeline"""
        self.stt = None
        self.llm = None
        self.tts = None
        self.audio_recorder = None
        self.audio_player = None
        
        # Metrics tracking
        self.metrics = {
            "total_conversations": 0,
            "successful_conversations": 0,
            "failed_conversations": 0,
            "average_response_time": 0.0,
            "stt_metrics": {"total_calls": 0, "successful_calls": 0, "average_latency": 0.0},
            "llm_metrics": {"total_calls": 0, "successful_calls": 0, "average_latency": 0.0},
            "tts_metrics": {"total_calls": 0, "successful_calls": 0, "average_latency": 0.0}
        }
        
        # Conversation context
        self.conversation_history = []
        
        # Status
        self.is_initialized = False
        self.is_listening = False
        
    def initialize(self) -> Dict[str, Any]:
        """
        Khởi tạo tất cả các components
        
        Returns:
            Dict chứa status khởi tạo
        """
        init_start = time.time()
        
        try:
            print("🔧 Initializing Elder Care Pipeline...")
            
            # Initialize STT
            print("📤 Initializing Assembly AI STT...")
            self.stt = AssemblyAISTT()
            if not self.stt.test_connection():
                return {
                    "success": False,
                    "error": "STT connection failed",
                    "component": "AssemblyAI"
                }
            print("✅ STT initialized successfully")
            
            # Initialize LLM
            print("🤖 Initializing Gemini LLM...")
            self.llm = GeminiLLM()
            if not self.llm.test_connection():
                return {
                    "success": False,
                    "error": "LLM connection failed",
                    "component": "Gemini"
                }
            print("✅ LLM initialized successfully")
            
            # Initialize TTS
            print("🔊 Initializing VBEE AI TTS...")
            self.tts = VBEETTS()
            if not self.tts.test_connection():
                return {
                    "success": False,
                    "error": "TTS connection failed",
                    "component": "VBEE"
                }
            print("✅ TTS initialized successfully")
            
            # Initialize Audio components
            print("🎤 Initializing Audio components...")
            self.audio_recorder = AudioRecorder()
            self.audio_player = AudioPlayer()
            print("✅ Audio components initialized")
            
            # Mark as initialized
            self.is_initialized = True
            
            init_time = (time.time() - init_start) * 1000
            
            return {
                "success": True,
                "initialization_time_ms": init_time,
                "components": ["AssemblyAI STT", "Gemini LLM", "VBEE TTS", "Audio I/O"],
                "message": "Pipeline initialized successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "initialization_time_ms": (time.time() - init_start) * 1000
            }
    
    def process_voice_input(self, record_duration: float = 5.0) -> Dict[str, Any]:
        """
        Xử lý input giọng nói hoàn chỉnh: STT -> LLM -> TTS -> Audio playback
        
        Args:
            record_duration: Thời gian ghi âm (giây)
            
        Returns:
            Dict chứa kết quả pipeline và metrics
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Pipeline not initialized. Call initialize() first."
            }
        
        pipeline_start = time.time()
        conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            print(f"\\n🎙️ Starting voice conversation {conversation_id}")
            print("=" * 50)
            
            # Step 1: Record audio
            print(f"🎤 Recording audio for {record_duration} seconds...")
            print("💬 Please speak clearly about your question or concern...")
            
            record_success, audio_file, record_error = self.audio_recorder.record_audio(record_duration)
            
            if not record_success:
                return {
                    "success": False,
                    "error": f"Audio recording failed: {record_error}",
                    "stage": "recording",
                    "conversation_id": conversation_id
                }
            
            print(f"✅ Audio recorded: {os.path.basename(audio_file)}")
            
            # Step 2: Speech-to-Text
            print("\\n🔄 Converting speech to text...")
            stt_result = self.stt.transcribe_audio_file(audio_file)
            
            # Update STT metrics
            self.metrics["stt_metrics"]["total_calls"] += 1
            if stt_result["success"]:
                self.metrics["stt_metrics"]["successful_calls"] += 1
                self.metrics["stt_metrics"]["average_latency"] = (
                    self.metrics["stt_metrics"]["average_latency"] * (self.metrics["stt_metrics"]["successful_calls"] - 1) +
                    stt_result["latency_ms"]
                ) / self.metrics["stt_metrics"]["successful_calls"]
            
            if not stt_result["success"]:
                return {
                    "success": False,
                    "error": f"STT failed: {stt_result['error']}",
                    "stage": "stt",
                    "conversation_id": conversation_id,
                    "audio_file": audio_file
                }
            
            user_text = stt_result["transcript"]
            print(f"✅ Transcribed: '{user_text}'")
            print(f"🎯 Confidence: {stt_result['confidence']:.2f}")
            
            # Step 3: Generate LLM response
            print("\\n🤖 Generating AI response...")
            llm_result = self.llm.generate_response(user_text)
            
            # Update LLM metrics
            self.metrics["llm_metrics"]["total_calls"] += 1
            if llm_result["success"]:
                self.metrics["llm_metrics"]["successful_calls"] += 1
                self.metrics["llm_metrics"]["average_latency"] = (
                    self.metrics["llm_metrics"]["average_latency"] * (self.metrics["llm_metrics"]["successful_calls"] - 1) +
                    llm_result["latency_ms"]
                ) / self.metrics["llm_metrics"]["successful_calls"]
            
            if not llm_result["success"]:
                return {
                    "success": False,
                    "error": f"LLM failed: {llm_result['error']}",
                    "stage": "llm",
                    "conversation_id": conversation_id,
                    "user_input": user_text,
                    "audio_file": audio_file
                }
            
            ai_response = llm_result["response"]
            print(f"✅ AI Response: '{ai_response[:100]}...'")
            
            # Step 4: Text-to-Speech
            print("\\n🔊 Converting AI response to speech...")
            tts_result = self.tts.synthesize_speech(ai_response)
            
            # Update TTS metrics
            self.metrics["tts_metrics"]["total_calls"] += 1
            if tts_result["success"]:
                self.metrics["tts_metrics"]["successful_calls"] += 1
                self.metrics["tts_metrics"]["average_latency"] = (
                    self.metrics["tts_metrics"]["average_latency"] * (self.metrics["tts_metrics"]["successful_calls"] - 1) +
                    tts_result["latency_ms"]
                ) / self.metrics["tts_metrics"]["successful_calls"]
            
            if not tts_result["success"]:
                return {
                    "success": False,
                    "error": f"TTS failed: {tts_result['error']}",
                    "stage": "tts",
                    "conversation_id": conversation_id,
                    "user_input": user_text,
                    "ai_response": ai_response,
                    "audio_file": audio_file
                }
            
            print(f"✅ Audio synthesized: {os.path.basename(tts_result['audio_file'])}")
            
            # Step 5: Play audio response
            print("\\n🔊 Playing AI response...")
            play_success, play_error = self.audio_player.play_audio_file(tts_result["audio_file"])
            
            if not play_success:
                print(f"⚠️ Audio playback failed: {play_error}")
                # Don't fail the entire pipeline for playback issues
            else:
                print("✅ Audio playback completed")
            
            # Calculate total pipeline time
            total_pipeline_time = (time.time() - pipeline_start) * 1000
            
            # Update conversation metrics
            self.metrics["total_conversations"] += 1
            if play_success:
                self.metrics["successful_conversations"] += 1
            else:
                self.metrics["failed_conversations"] += 1
            
            self.metrics["average_response_time"] = (
                self.metrics["average_response_time"] * (self.metrics["total_conversations"] - 1) +
                total_pipeline_time
            ) / self.metrics["total_conversations"]
            
            # Store conversation
            conversation = {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "user_input": user_text,
                "ai_response": ai_response,
                "stt_confidence": stt_result["confidence"],
                "pipeline_time_ms": total_pipeline_time,
                "stages": {
                    "stt_time_ms": stt_result["latency_ms"],
                    "llm_time_ms": llm_result["latency_ms"],
                    "tts_time_ms": tts_result["latency_ms"]
                }
            }
            
            self.conversation_history.append(conversation)
            
            # Cleanup audio files (if not debugging)
            if not SAVE_AUDIO_FILES:
                for file_path in [audio_file, tts_result["audio_file"]]:
                    if os.path.exists(file_path):
                        try:
                            os.unlink(file_path)
                        except:
                            pass
            
            print("\\n🎉 Voice conversation completed successfully!")
            print(f"⏱️  Total pipeline time: {total_pipeline_time:.1f}ms")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "user_input": user_text,
                "ai_response": ai_response,
                "pipeline_time_ms": total_pipeline_time,
                "playback_success": play_success,
                "stages": {
                    "recording": {"success": True, "file": audio_file},
                    "stt": {"success": True, "latency_ms": stt_result["latency_ms"], "confidence": stt_result["confidence"]},
                    "llm": {"success": True, "latency_ms": llm_result["latency_ms"]},
                    "tts": {"success": True, "latency_ms": tts_result["latency_ms"], "file": tts_result["audio_file"]},
                    "playback": {"success": play_success, "error": play_error if not play_success else None}
                },
                "metrics": self.get_current_metrics()
            }
            
        except Exception as e:
            self.metrics["failed_conversations"] += 1
            return {
                "success": False,
                "error": f"Pipeline error: {str(e)}",
                "conversation_id": conversation_id,
                "pipeline_time_ms": (time.time() - pipeline_start) * 1000
            }
    
    def process_text_input(self, user_text: str) -> Dict[str, Any]:
        """
        Xử lý input text (bỏ qua STT): Text -> LLM -> TTS -> Audio playback
        
        Args:
            user_text: Text input từ người dùng
            
        Returns:
            Dict chứa kết quả pipeline và metrics
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Pipeline not initialized. Call initialize() first."
            }
        
        pipeline_start = time.time()
        conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            print(f"\\n💬 Processing text input: '{user_text[:50]}...'")
            print("=" * 50)
            
            # Step 1: Generate LLM response
            print("🤖 Generating AI response...")
            llm_result = self.llm.generate_response(user_text)
            
            if not llm_result["success"]:
                return {
                    "success": False,
                    "error": f"LLM failed: {llm_result['error']}",
                    "stage": "llm",
                    "conversation_id": conversation_id,
                    "user_input": user_text
                }
            
            ai_response = llm_result["response"]
            print(f"✅ AI Response: '{ai_response[:100]}...'")
            
            # Step 2: Text-to-Speech
            print("🔊 Converting response to speech...")
            tts_result = self.tts.synthesize_speech(ai_response)
            
            if not tts_result["success"]:
                return {
                    "success": False,
                    "error": f"TTS failed: {tts_result['error']}",
                    "stage": "tts",
                    "conversation_id": conversation_id,
                    "user_input": user_text,
                    "ai_response": ai_response
                }
            
            # Step 3: Play audio response
            print("🔊 Playing AI response...")
            play_success, play_error = self.audio_player.play_audio_file(tts_result["audio_file"])
            
            total_pipeline_time = (time.time() - pipeline_start) * 1000
            
            if play_success:
                print("✅ Text conversation completed successfully!")
            else:
                print(f"⚠️ Audio playback failed: {play_error}")
            
            print(f"⏱️  Total pipeline time: {total_pipeline_time:.1f}ms")
            
            # Cleanup
            if not SAVE_AUDIO_FILES and os.path.exists(tts_result["audio_file"]):
                os.unlink(tts_result["audio_file"])
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "user_input": user_text,
                "ai_response": ai_response,
                "pipeline_time_ms": total_pipeline_time,
                "playback_success": play_success,
                "stages": {
                    "llm": {"success": True, "latency_ms": llm_result["latency_ms"]},
                    "tts": {"success": True, "latency_ms": tts_result["latency_ms"]},
                    "playback": {"success": play_success, "error": play_error if not play_success else None}
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Pipeline error: {str(e)}",
                "conversation_id": conversation_id,
                "pipeline_time_ms": (time.time() - pipeline_start) * 1000
            }
    
    def start_continuous_conversation(self, max_turns: int = 10):
        """
        Bắt đầu cuộc hội thoại liên tục với người dùng
        
        Args:
            max_turns: Số lượt hội thoại tối đa
        """
        if not self.is_initialized:
            print("❌ Pipeline not initialized. Call initialize() first.")
            return
        
        print("\\n🗣️  Starting continuous conversation mode")
        print("=" * 60)
        print("💡 Instructions:")
        print("   - Speak clearly when prompted")
        print("   - Say 'stop' or 'exit' to end conversation") 
        print("   - Press Ctrl+C to interrupt anytime")
        print("=" * 60)
        
        try:
            for turn in range(1, max_turns + 1):
                print(f"\\n🔄 Conversation Turn {turn}/{max_turns}")
                print("-" * 30)
                
                # Get voice input
                result = self.process_voice_input(record_duration=5.0)
                
                if not result["success"]:
                    print(f"❌ Turn {turn} failed: {result['error']}")
                    continue
                
                user_input = result["user_input"].lower()
                
                # Check for exit commands
                if any(exit_word in user_input for exit_word in ["stop", "exit", "quit", "goodbye", "tạm biệt", "dừng"]):
                    print("\\n👋 Conversation ended by user. Goodbye!")
                    break
                
                print(f"✅ Turn {turn} completed successfully")
                
                # Brief pause between turns
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\\n⚠️ Conversation interrupted by user")
        except Exception as e:
            print(f"\\n❌ Conversation error: {e}")
        
        print("\\n📊 Conversation session ended")
        self.print_session_summary()
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Lấy metrics hiện tại"""
        return self.metrics.copy()
    
    def print_session_summary(self):
        """In tóm tắt session"""
        print("\\n📊 SESSION SUMMARY")
        print("=" * 40)
        print(f"Total conversations: {self.metrics['total_conversations']}")
        print(f"Successful: {self.metrics['successful_conversations']}")
        print(f"Failed: {self.metrics['failed_conversations']}")
        if self.metrics['total_conversations'] > 0:
            success_rate = (self.metrics['successful_conversations'] / self.metrics['total_conversations']) * 100
            print(f"Success rate: {success_rate:.1f}%")
            print(f"Average response time: {self.metrics['average_response_time']:.1f}ms")
        
        print("\\nComponent Performance:")
        for component, metrics in [("STT", self.metrics['stt_metrics']), 
                                  ("LLM", self.metrics['llm_metrics']), 
                                  ("TTS", self.metrics['tts_metrics'])]:
            if metrics['total_calls'] > 0:
                success_rate = (metrics['successful_calls'] / metrics['total_calls']) * 100
                print(f"  {component}: {success_rate:.1f}% success, {metrics['average_latency']:.1f}ms avg")
    
    def save_session_log(self) -> str:
        """Lưu log session"""
        try:
            session_log = {
                "session_timestamp": datetime.now().isoformat(),
                "metrics": self.metrics,
                "conversation_history": self.conversation_history,
                "summary": {
                    "total_conversations": len(self.conversation_history),
                    "pipeline_initialized": self.is_initialized
                }
            }
            
            log_file = os.path.join(LOGS_DIR, f"pipeline_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(session_log, f, ensure_ascii=False, indent=2)
            
            print(f"\\n💾 Session log saved: {log_file}")
            return log_file
            
        except Exception as e:
            print(f"⚠️ Could not save session log: {e}")
            return None
    
    def cleanup(self):
        """Dọn dẹp resources"""
        print("\\n🧹 Cleaning up pipeline resources...")
        
        # Clear conversation history to free memory
        if hasattr(self.llm, 'clear_conversation_history'):
            self.llm.clear_conversation_history()
        
        # Save final session log
        self.save_session_log()
        
        print("✅ Pipeline cleanup completed")


def main():
    """Demo function"""
    print("🚀 ELDER CARE PIPELINE DEMO")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = ElderCarePipeline()
    
    init_result = pipeline.initialize()
    
    if not init_result["success"]:
        print(f"❌ Pipeline initialization failed: {init_result['error']}")
        print("💡 Make sure all API keys are configured in .env file")
        return
    
    print(f"✅ Pipeline initialized in {init_result['initialization_time_ms']:.1f}ms")
    
    try:
        while True:
            print("\\n" + "="*60)
            print("🎛️  PIPELINE OPTIONS")
            print("="*60)
            print("1. Voice conversation (STT -> LLM -> TTS)")
            print("2. Text conversation (Text -> LLM -> TTS)")
            print("3. Continuous voice conversation")
            print("4. Show current metrics")
            print("5. Exit")
            
            choice = input("\\n👆 Choose an option (1-5): ").strip()
            
            if choice == "1":
                result = pipeline.process_voice_input(record_duration=5.0)
                if result["success"]:
                    print(f"\\n🎉 Voice conversation successful!")
                    print(f"📝 You said: '{result['user_input']}'")
                    print(f"🤖 AI responded: '{result['ai_response'][:100]}...'")
                    print(f"⏱️  Total time: {result['pipeline_time_ms']:.1f}ms")
                else:
                    print(f"\\n❌ Voice conversation failed: {result['error']}")
            
            elif choice == "2":
                user_text = input("\\n💬 Enter your text: ").strip()
                if user_text:
                    result = pipeline.process_text_input(user_text)
                    if result["success"]:
                        print(f"\\n🎉 Text conversation successful!")
                        print(f"🤖 AI responded: '{result['ai_response'][:100]}...'")
                        print(f"⏱️  Total time: {result['pipeline_time_ms']:.1f}ms")
                    else:
                        print(f"\\n❌ Text conversation failed: {result['error']}")
                else:
                    print("❌ Please enter some text")
            
            elif choice == "3":
                max_turns = input("\\n🔄 How many conversation turns? (default 5): ").strip()
                try:
                    max_turns = int(max_turns) if max_turns else 5
                except ValueError:
                    max_turns = 5
                
                pipeline.start_continuous_conversation(max_turns)
            
            elif choice == "4":
                pipeline.print_session_summary()
            
            elif choice == "5":
                print("\\n👋 Exiting pipeline demo...")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-5.")
    
    except KeyboardInterrupt:
        print("\\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\\n❌ Demo error: {e}")
    finally:
        pipeline.cleanup()
        print("\\n🎯 Pipeline demo completed!")


if __name__ == "__main__":
    main()
