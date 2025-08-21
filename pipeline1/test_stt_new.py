#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Google STT Service
=======================

Test riêng cho Google Cloud Speech-to-Text service
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import *
from utils import GoogleSTTService, AudioRecorder


def test_stt_comprehensive():
    """Test toàn diện STT service"""
    
    print("🧪 === COMPREHENSIVE STT TESTING ===")
    print("=" * 50)
    
    try:
        # Initialize services
        print("🔧 Khởi tạo STT service và audio recorder...")
        stt_service = GoogleSTTService(credentials_path=GOOGLE_APPLICATION_CREDENTIALS)
        audio_recorder = AudioRecorder()
        
        # Test 1: Connection
        print("\n📡 Test 1: API Connection")
        if stt_service.test_connection():
            print("✅ STT API connection thành công")
        else:
            print("❌ STT API connection thất bại")
            return
            
        # Test 2: Configuration
        print("\n⚙️  Test 2: Configuration")
        config = stt_service.get_current_config()
        print(f"Language: {config['language_code']}")
        print(f"Sample rate: {config['sample_rate_hertz']}Hz")
        print(f"Model: {config['model']}")
        
        # Test 3: Audio recording và transcription
        print("\n🎤 Test 3: Live Audio Recording + STT")
        print("Sẽ ghi âm 5 giây, hãy nói rõ ràng...")
        input("Nhấn Enter để bắt đầu ghi âm...")
        
        # Record audio
        success, audio_file, error = audio_recorder.record_audio(5.0)
        
        if not success:
            print(f"❌ Ghi âm thất bại: {error}")
            return
            
        print(f"✅ Đã ghi âm: {audio_file}")
        
        # Transcribe
        print("🔄 Đang transcribe...")
        result = stt_service.transcribe_audio_file(audio_file)
        
        if result["success"]:
            print("✅ STT thành công!")
            print(f"📝 Transcript: '{result['transcript']}'")
            print(f"🎯 Confidence: {result['confidence']:.2f}")
            print(f"⏱️  Latency: {result['latency_ms']:.1f}ms")
            
            if result.get("alternatives"):
                print(f"🔄 Alternatives: {result['alternatives']}")
        else:
            print(f"❌ STT thất bại: {result['error']}")
            
        # Cleanup
        if os.path.exists(audio_file):
            os.unlink(audio_file)
            
        # Test 4: Different configurations
        print("\n⚙️  Test 4: Different Model Configurations")
        
        configs = [
            {"model": "latest_short", "use_enhanced": True},
            {"model": "latest_long", "use_enhanced": True},
            {"enable_automatic_punctuation": False}
        ]
        
        for i, test_config in enumerate(configs, 1):
            print(f"\nConfig {i}: {test_config}")
            
            # Record another sample
            print("Ghi âm 3 giây nữa...")
            success, audio_file, error = audio_recorder.record_audio(3.0)
            
            if success:
                result = stt_service.transcribe_audio_file(audio_file, test_config)
                if result["success"]:
                    print(f"✅ Result: '{result['transcript'][:50]}...'")
                    print(f"   Confidence: {result['confidence']:.2f}")
                else:
                    print(f"❌ Error: {result['error']}")
                    
                os.unlink(audio_file)
            else:
                print(f"❌ Recording failed: {error}")
                
        # Test 5: Error handling
        print("\n🚨 Test 5: Error Handling")
        
        # Test with non-existent file
        result = stt_service.transcribe_audio_file("non_existent_file.wav")
        if not result["success"]:
            print("✅ Correctly handled non-existent file")
        else:
            print("❌ Should have failed with non-existent file")
            
        # Test 6: Performance metrics
        print("\n📊 Test 6: Performance Testing")
        
        latencies = []
        confidences = []
        
        for i in range(3):
            print(f"\nPerformance test {i+1}/3 - Ghi âm 3 giây...")
            success, audio_file, error = audio_recorder.record_audio(3.0)
            
            if success:
                result = stt_service.transcribe_audio_file(audio_file)
                if result["success"]:
                    latencies.append(result["latency_ms"])
                    confidences.append(result["confidence"])
                    print(f"✅ Latency: {result['latency_ms']:.1f}ms, Confidence: {result['confidence']:.2f}")
                else:
                    print(f"❌ Error: {result['error']}")
                    
                os.unlink(audio_file)
            else:
                print(f"❌ Recording failed: {error}")
                
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            avg_confidence = sum(confidences) / len(confidences)
            print(f"\n📈 PERFORMANCE SUMMARY:")
            print(f"   Average latency: {avg_latency:.1f}ms")
            print(f"   Average confidence: {avg_confidence:.2f}")
            print(f"   Min latency: {min(latencies):.1f}ms")
            print(f"   Max latency: {max(latencies):.1f}ms")
            
        print("\n🎯 STT comprehensive testing completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_stt_comprehensive()
