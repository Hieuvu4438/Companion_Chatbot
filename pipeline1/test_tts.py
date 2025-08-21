#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Google TTS Service
=======================

Test riêng cho Google Cloud Text-to-Speech service
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import *
from utils import GoogleTTSService, AudioPlayer


def test_tts_comprehensive():
    """Test toàn diện TTS service"""
    
    print("🧪 === COMPREHENSIVE TTS TESTING ===")
    print("=" * 50)
    
    try:
        # Initialize services
        print("🔧 Khởi tạo TTS service và audio player...")
        tts_service = GoogleTTSService(credentials_path=GOOGLE_APPLICATION_CREDENTIALS)
        audio_player = AudioPlayer()
        
        # Test 1: Connection
        print("\n📡 Test 1: API Connection")
        if tts_service.test_connection():
            print("✅ TTS API connection thành công")
        else:
            print("❌ TTS API connection thất bại")
            return
            
        # Test 2: Available voices
        print("\n🎵 Test 2: Available Voices")
        voices = tts_service.get_available_voices("vi-VN")
        if voices["success"]:
            print(f"✅ Found {voices['total_count']} Vietnamese voices")
            for voice in voices["voices"][:3]:  # Show first 3
                print(f"   - {voice['name']} ({voice['gender']})")
        else:
            print(f"❌ Failed to get voices: {voices['error']}")
            
        # Test 3: Elder-friendly voices
        print("\n👴 Test 3: Elder-friendly Voices")
        elder_voices = tts_service.get_elder_friendly_voices()
        for voice in elder_voices:
            recommended = "⭐" if voice["recommended"] else "  "
            print(f"  {recommended} {voice['name']} - {voice['description']}")
            
        # Test 4: Basic text synthesis
        print("\n🔊 Test 4: Basic Text Synthesis")
        test_texts = [
            "Xin chào, tôi là trợ lý AI hỗ trợ người cao tuổi.",
            "Hôm nay thời tiết thế nào? Bác có khỏe không?",
            "Nhớ uống thuốc đầy đủ và tập thể dục nhẹ nhàng nhé!"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\nSynthesizing text {i}: '{text[:30]}...'")
            
            result = tts_service.synthesize_speech(text)
            
            if result["success"]:
                print(f"✅ TTS thành công!")
                print(f"📁 File: {os.path.basename(result['audio_file'])}")
                print(f"📊 Characters: {result['character_count']}")
                print(f"⏱️  Latency: {result['latency_ms']:.1f}ms")
                print(f"💾 File size: {result['file_size_bytes']} bytes")
                print(f"🎵 Voice: {result['voice_used']}")
                
                # Play audio
                print("🔊 Đang phát âm thanh...")
                play_success, play_error = audio_player.play_audio_file(result["audio_file"])
                
                if play_success:
                    print("✅ Audio playback thành công")
                else:
                    print(f"❌ Audio playback thất bại: {play_error}")
                    
                # Cleanup
                if os.path.exists(result["audio_file"]):
                    os.unlink(result["audio_file"])
                    
            else:
                print(f"❌ TTS thất bại: {result['error']}")
                
        # Test 5: Different voice configurations
        print("\n🎭 Test 5: Different Voice Configurations")
        
        test_configs = [
            {
                "name": "Slow speech for elderly",
                "config": {
                    "voice_name": "vi-VN-Neural2-A",
                    "speaking_rate": 0.8,
                    "pitch": -2.0
                }
            },
            {
                "name": "Clear male voice",
                "config": {
                    "voice_name": "vi-VN-Neural2-D", 
                    "speaking_rate": 0.9,
                    "volume_gain_db": 2.0
                }
            }
        ]
        
        test_text = "Đây là bài test với các cấu hình giọng nói khác nhau."
        
        for config_test in test_configs:
            print(f"\n🔧 Testing: {config_test['name']}")
            
            result = tts_service.synthesize_speech(
                text=test_text,
                custom_config=config_test['config']
            )
            
            if result["success"]:
                print(f"✅ Config test successful: {result['latency_ms']:.1f}ms")
                
                # Quick playback
                play_success, _ = audio_player.play_audio_file(result["audio_file"])
                print(f"🔊 Playback: {'✅' if play_success else '❌'}")
                
                os.unlink(result["audio_file"])
            else:
                print(f"❌ Config test failed: {result['error']}")
                
        # Test 6: SSML synthesis
        print("\n🎵 Test 6: SSML Synthesis")
        
        ssml_text = tts_service.create_elder_friendly_ssml(
            text="Xin chào bác! Hôm nay bác có khỏe không? Nhớ uống thuốc đầy đủ nhé!",
            emphasis_words=["khỏe", "thuốc"],
            pause_duration="0.8s"
        )
        
        print("Generated SSML:")
        print(ssml_text[:200] + "...")
        
        result = tts_service.synthesize_with_ssml(ssml_text)
        
        if result["success"]:
            print(f"✅ SSML synthesis successful: {result['latency_ms']:.1f}ms")
            
            # Play SSML result
            play_success, _ = audio_player.play_audio_file(result["audio_file"])
            print(f"🔊 SSML Playback: {'✅' if play_success else '❌'}")
            
            os.unlink(result["audio_file"])
        else:
            print(f"❌ SSML synthesis failed: {result['error']}")
            
        # Test 7: Performance testing
        print("\n📊 Test 7: Performance Testing")
        
        performance_texts = [
            "Ngắn",
            "Câu này dài hơn một chút để test performance.",
            "Đây là một đoạn văn bản khá dài để kiểm tra hiệu suất của hệ thống Text-to-Speech. Chúng ta sẽ đo latency và chất lượng tổng hợp âm thanh."
        ]
        
        latencies = []
        char_counts = []
        
        for i, text in enumerate(performance_texts, 1):
            print(f"\nPerformance test {i}/3: {len(text)} characters")
            
            result = tts_service.synthesize_speech(text)
            
            if result["success"]:
                latencies.append(result["latency_ms"])
                char_counts.append(result["character_count"])
                
                chars_per_second = result["character_count"] / (result["latency_ms"] / 1000)
                print(f"✅ Latency: {result['latency_ms']:.1f}ms")
                print(f"   Speed: {chars_per_second:.1f} chars/second")
                
                os.unlink(result["audio_file"])
            else:
                print(f"❌ Performance test {i} failed: {result['error']}")
                
        # Performance summary
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            total_chars = sum(char_counts)
            total_time = sum(latencies) / 1000
            overall_speed = total_chars / total_time
            
            print(f"\n📈 PERFORMANCE SUMMARY:")
            print(f"   Average latency: {avg_latency:.1f}ms")
            print(f"   Overall speed: {overall_speed:.1f} chars/second")
            print(f"   Min latency: {min(latencies):.1f}ms")
            print(f"   Max latency: {max(latencies):.1f}ms")
            
        # Test 8: Error handling
        print("\n🚨 Test 8: Error Handling")
        
        # Test empty text
        result = tts_service.synthesize_speech("")
        if not result["success"]:
            print("✅ Correctly handled empty text")
        else:
            print("❌ Should have failed with empty text")
            
        # Test very long text
        long_text = "A" * 6000  # Over 5000 char limit
        result = tts_service.synthesize_speech(long_text)
        if not result["success"]:
            print("✅ Correctly handled overly long text")
        else:
            print("❌ Should have failed with long text")
            
        # Test 9: Text validation
        print("\n✅ Test 9: Text Validation")
        
        test_cases = [
            ("Valid text", "Đây là text hợp lệ", True),
            ("Empty text", "", False),
            ("Very long text", "A" * 6000, False),
            ("Normal length", "Text bình thường với độ dài vừa phải", True)
        ]
        
        for name, text, should_be_valid in test_cases:
            is_valid, error = tts_service.validate_text_input(text)
            
            if is_valid == should_be_valid:
                print(f"✅ {name}: {'Valid' if is_valid else 'Invalid'}")
            else:
                print(f"❌ {name}: Expected {'valid' if should_be_valid else 'invalid'}, got {'valid' if is_valid else 'invalid'}")
                
        # Test 10: Duration estimation
        print("\n⏰ Test 10: Duration Estimation")
        
        test_texts_duration = [
            "Ngắn",
            "Câu này dài hơn và sẽ mất nhiều thời gian hơn để nói",
            "Đây là một đoạn văn bản rất dài với nhiều từ và sẽ mất khá nhiều thời gian để đọc hoàn chỉnh khi được chuyển đổi thành âm thanh"
        ]
        
        for text in test_texts_duration:
            estimated_duration = tts_service.estimate_audio_duration(text)
            word_count = len(text.split())
            
            print(f"Text: '{text[:30]}...' ({word_count} words)")
            print(f"Estimated duration: {estimated_duration:.1f}s")
            
        print("\n🎯 TTS comprehensive testing completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_tts_comprehensive()
