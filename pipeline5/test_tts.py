#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test TTS Module
===============

Test riêng cho VBEE AI TTS service trong pipeline5
"""

import os
import sys
import time
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import *
    from tts_module import VBEETTS, AudioPlayer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Đảm bảo các file config.py và tts_module.py tồn tại")
    sys.exit(1)


def print_section(title):
    """In header cho mỗi section test"""
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print('='*50)


def print_metrics(result):
    """In metrics của một operation"""
    if result.get("success"):
        print(f"⏱️  Latency: {result.get('latency_ms', 0):.1f}ms")
        if 'character_count' in result:
            print(f"📊 Characters: {result['character_count']}")
        if 'file_size_bytes' in result:
            print(f"💾 File size: {result['file_size_bytes']} bytes")
        if 'voice_used' in result:
            print(f"🎵 Voice: {result['voice_used']}")
        if 'audio_duration_estimate' in result:
            print(f"⏰ Estimated duration: {result['audio_duration_estimate']:.1f}s")


def test_tts_connection():
    """Test 1: Kết nối API"""
    print_section("TEST 1: API CONNECTION")
    
    try:
        tts = VBEETTS()
        
        if tts.test_connection():
            print("✅ VBEE AI API connection successful")
            return True
        else:
            print("❌ VBEE AI API connection failed")
            print("💡 Kiểm tra:")
            print("   - API token trong .env file")
            print("   - Kết nối internet") 
            print("   - VBEE API service status")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("💡 Possible issues:")
        print("   - Invalid API credentials")
        print("   - Network connectivity")
        print("   - Service temporarily unavailable")
        return False


def test_available_voices():
    """Test 2: Danh sách giọng nói"""
    print_section("TEST 2: AVAILABLE VOICES")
    
    try:
        tts = VBEETTS()
        
        # Test get available voices
        voices_result = tts.get_available_voices()
        
        if voices_result["success"]:
            print(f"✅ Found {voices_result['total_count']} voices")
            
            # Display voices
            voices = voices_result["voices"]
            for i, voice in enumerate(voices[:5], 1):  # Show max 5 voices
                if isinstance(voice, dict):
                    name = voice.get('name', f'Voice {i}')
                    description = voice.get('description', 'No description')
                    print(f"   {i}. {name}: {description}")
                else:
                    print(f"   {i}. Voice data: {voice}")
            
            # Test elder-friendly voices
            print("\n👴 Elder-friendly voices:")
            elder_voices = tts.get_elder_friendly_voices()
            
            for voice in elder_voices[:3]:  # Show top 3
                recommended = "⭐" if voice["recommended"] else "  "
                print(f"  {recommended} {voice['name']} - {voice['description']}")
            
            return True
        else:
            print(f"❌ Failed to get voices: {voices_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Voices test failed: {e}")
        return False


def test_input_validation():
    """Test 3: Validation input"""
    print_section("TEST 3: INPUT VALIDATION")
    
    try:
        tts = VBEETTS()
        
        # Test cases
        test_cases = [
            ("Valid text", "Đây là một câu text hợp lệ.", True),
            ("Empty text", "", False),
            ("Very short text", "A", True),
            ("Very long text", "A" * 6000, False),
            ("Text with HTML", "Text có <script>alert('test')</script>", False),
            ("Normal Vietnamese text", "Xin chào, tôi là trợ lý AI.", True),
            ("Text with numbers", "Hôm nay là ngày 15 tháng 12 năm 2024.", True)
        ]
        
        passed = 0
        total = len(test_cases)
        
        for name, text, should_be_valid in test_cases:
            is_valid, error = tts.validate_text_input(text)
            
            if is_valid == should_be_valid:
                status = "✅"
                passed += 1
            else:
                status = "❌"
            
            print(f"{status} {name}: {'Valid' if is_valid else 'Invalid'}")
            if error and not should_be_valid:
                print(f"   Error: {error}")
        
        print(f"\n📊 Validation results: {passed}/{total} tests passed")
        return passed == total
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def test_basic_synthesis():
    """Test 4: Synthesis cơ bản"""
    print_section("TEST 4: BASIC SYNTHESIS")
    
    try:
        tts = VBEETTS()
        
        # Test texts cho người cao tuổi
        test_texts = [
            "Xin chào, tôi là trợ lý AI hỗ trợ người cao tuổi.",
            "Hôm nay thời tiết thế nào? Bác có khỏe không?",
            "Nhớ uống thuốc đầy đủ và tập thể dục nhẹ nhàng nhé!"
        ]
        
        success_count = 0
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n🔊 Test {i}: '{text[:40]}...'")
            
            result = tts.synthesize_speech(text)
            
            if result["success"]:
                print(f"✅ Synthesis successful!")
                print(f"📁 File: {os.path.basename(result['audio_file'])}")
                print_metrics(result)
                
                # Test audio playback
                print("🔊 Testing playback...")
                player = AudioPlayer()
                play_success, play_error = player.play_audio_file(result["audio_file"])
                
                if play_success:
                    print("✅ Audio playback successful")
                    success_count += 1
                else:
                    print(f"⚠️ Audio playback failed: {play_error}")
                    success_count += 0.5  # Partial success
                
                # Cleanup (if not debugging)
                if not SAVE_AUDIO_FILES and os.path.exists(result["audio_file"]):
                    os.unlink(result["audio_file"])
                    
            else:
                print(f"❌ Synthesis failed: {result['error']}")
                print("💡 Possible issues:")
                print("   - API quota exceeded")
                print("   - Network connectivity")
                print("   - Invalid text input")
        
        print(f"\n📊 Synthesis results: {success_count}/{len(test_texts)} tests successful")
        return success_count >= len(test_texts) * 0.5  # At least 50% success
        
    except Exception as e:
        print(f"❌ Synthesis test failed: {e}")
        return False


def test_voice_configurations():
    """Test 5: Các cấu hình giọng nói"""
    print_section("TEST 5: VOICE CONFIGURATIONS")
    
    try:
        tts = VBEETTS()
        
        test_text = "Đây là bài test với các cấu hình giọng nói khác nhau cho người cao tuổi."
        
        # Test configs
        configs = [
            {
                "name": "Slow speech for elderly",
                "config": {
                    "voice_id": 3,  # Thu Minh - giọng nữ dịu dàng
                    "speed": 0.8,   # Chậm hơn 20%
                    "tone": 0
                }
            },
            {
                "name": "Male voice normal speed",
                "config": {
                    "voice_id": 2,  # Lê Minh - giọng nam ấm áp
                    "speed": 1.0,
                    "tone": 0
                }
            },
            {
                "name": "Elder-friendly female",
                "config": {
                    "voice_id": 1,  # Minh Khai - giọng nữ trẻ
                    "speed": 0.9,   # Hơi chậm
                    "tone": 0
                }
            }
        ]
        
        success_count = 0
        
        for config_test in configs:
            print(f"\n🎭 Testing: {config_test['name']}")
            print(f"   Config: {config_test['config']}")
            
            result = tts.synthesize_speech(test_text, config_test['config'])
            
            if result["success"]:
                print("✅ Config synthesis successful")
                print_metrics(result)
                
                # Quick playback test
                player = AudioPlayer()
                play_success, play_error = player.play_audio_file(result["audio_file"])
                
                if play_success:
                    print("✅ Playback successful")
                    success_count += 1
                else:
                    print(f"⚠️ Playback failed: {play_error}")
                    success_count += 0.5
                
                # Cleanup
                if not SAVE_AUDIO_FILES and os.path.exists(result["audio_file"]):
                    os.unlink(result["audio_file"])
                    
            else:
                print(f"❌ Config synthesis failed: {result['error']}")
        
        print(f"\n📊 Configuration results: {success_count}/{len(configs)} tests successful")
        return success_count >= len(configs) * 0.5
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_duration_estimation():
    """Test 6: Ước tính thời lượng"""
    print_section("TEST 6: DURATION ESTIMATION")
    
    try:
        tts = VBEETTS()
        
        test_cases = [
            ("Short text", "Xin chào."),
            ("Medium text", "Đây là một câu văn có độ dài trung bình để test thời lượng."),
            ("Long text", "Đây là một đoạn văn bản khá dài với nhiều từ ngữ và câu văn phức tạp để kiểm tra khả năng ước tính thời lượng âm thanh của hệ thống Text-to-Speech một cách chính xác và hiệu quả.")
        ]
        
        print("⏰ Testing duration estimation:")
        
        for name, text in test_cases:
            word_count = len(text.split())
            estimated_duration = tts.estimate_audio_duration(text)
            
            print(f"\n📝 {name}:")
            print(f"   Text: '{text[:50]}...'")
            print(f"   Words: {word_count}")
            print(f"   Estimated duration: {estimated_duration:.1f}s")
            print(f"   Rate: {word_count/estimated_duration*60:.1f} words/minute")
        
        return True
        
    except Exception as e:
        print(f"❌ Duration estimation test failed: {e}")
        return False


def test_performance_metrics():
    """Test 7: Performance metrics"""
    print_section("TEST 7: PERFORMANCE METRICS")
    
    try:
        tts = VBEETTS()
        
        # Performance test texts với độ dài khác nhau
        performance_texts = [
            "Ngắn",
            "Câu này dài hơn một chút để test performance của hệ thống.",
            "Đây là một đoạn văn bản khá dài để kiểm tra hiệu suất của hệ thống Text-to-Speech. Chúng ta sẽ đo latency, throughput và chất lượng tổng hợp âm thanh trong điều kiện thực tế."
        ]
        
        latencies = []
        throughputs = []  # chars per second
        
        print("🏃 Running performance tests...")
        
        for i, text in enumerate(performance_texts, 1):
            char_count = len(text)
            print(f"\n⏱️  Performance test {i}/3: {char_count} characters")
            
            result = tts.synthesize_speech(text)
            
            if result["success"]:
                latency = result["latency_ms"]
                throughput = char_count / (latency / 1000)  # chars per second
                
                latencies.append(latency)
                throughputs.append(throughput)
                
                print(f"✅ Latency: {latency:.1f}ms")
                print(f"📈 Throughput: {throughput:.1f} chars/second")
                
                # Cleanup
                if not SAVE_AUDIO_FILES and os.path.exists(result["audio_file"]):
                    os.unlink(result["audio_file"])
            else:
                print(f"❌ Performance test {i} failed: {result['error']}")
        
        # Performance summary
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            avg_throughput = sum(throughputs) / len(throughputs)
            
            print(f"\n📈 PERFORMANCE SUMMARY:")
            print(f"   Average latency: {avg_latency:.1f}ms")
            print(f"   Average throughput: {avg_throughput:.1f} chars/second")
            print(f"   Min latency: {min(latencies):.1f}ms")
            print(f"   Max latency: {max(latencies):.1f}ms")
            
            # Performance evaluation
            if avg_latency < 5000:  # < 5 seconds
                print("✅ Latency performance: EXCELLENT")
            elif avg_latency < 10000:  # < 10 seconds
                print("✅ Latency performance: GOOD")
            else:
                print("⚠️ Latency performance: NEEDS IMPROVEMENT")
                
            if avg_throughput > 50:  # > 50 chars/second
                print("✅ Throughput performance: EXCELLENT")
            elif avg_throughput > 20:  # > 20 chars/second
                print("✅ Throughput performance: GOOD")
            else:
                print("⚠️ Throughput performance: NEEDS IMPROVEMENT")
        
        return len(latencies) > 0
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def test_error_handling():
    """Test 8: Error handling"""
    print_section("TEST 8: ERROR HANDLING")
    
    try:
        tts = VBEETTS()
        
        # Test cases that should fail gracefully
        error_tests = [
            ("Empty text", ""),
            ("Very long text", "A" * 6000),
            ("Text with dangerous chars", "Text với <script>alert('xss')</script>"),
            ("Only special characters", "!@#$%^&*()"),
        ]
        
        success_count = 0
        
        for test_name, text in error_tests:
            print(f"\n🧪 Testing: {test_name}")
            
            result = tts.synthesize_speech(text)
            
            if not result["success"]:
                print(f"✅ Correctly handled error: {result['error']}")
                success_count += 1
            else:
                print(f"⚠️ Should have failed but succeeded: {result.get('audio_file', 'No file')}")
                # Cleanup unexpected success
                if 'audio_file' in result and os.path.exists(result['audio_file']):
                    os.unlink(result['audio_file'])
        
        print(f"\n📊 Error handling results: {success_count}/{len(error_tests)} tests handled correctly")
        return success_count >= len(error_tests) * 0.75  # 75% should handle errors correctly
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_service_info():
    """Test 9: Service information"""
    print_section("TEST 9: SERVICE INFORMATION")
    
    try:
        tts = VBEETTS()
        
        # Test service info
        service_info = tts.get_service_info()
        
        print("📋 Service Information:")
        for key, value in service_info.items():
            print(f"   {key}: {value}")
        
        # Test voice info
        print("\n🎵 Voice Information:")
        for voice_id in [1, 2, 3]:
            voice_info = tts.get_voice_info(voice_id)
            if voice_info["success"]:
                info = voice_info["voice_info"]
                print(f"   Voice {voice_id}: {info['name']} - {info['description']}")
            else:
                print(f"   Voice {voice_id}: {voice_info['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service info test failed: {e}")
        return False


def save_test_results(results):
    """Lưu kết quả test"""
    try:
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "TTS Module Test",
            "service": "VBEE AI",
            "results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": sum(1 for r in results.values() if r),
                "failed_tests": sum(1 for r in results.values() if not r)
            }
        }
        
        report_file = os.path.join(LOGS_DIR, f"tts_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Test report saved: {report_file}")
        
    except Exception as e:
        print(f"⚠️ Could not save test report: {e}")


def main():
    """Main test function"""
    print("🧪 TTS MODULE COMPREHENSIVE TEST")
    print("=" * 60)
    print("Testing VBEE AI Text-to-Speech service")
    print("=" * 60)
    
    # Test results tracking
    results = {}
    
    try:
        # Test 1: Connection
        results["connection"] = test_tts_connection()
        if not results["connection"]:
            print("\n❌ Cannot proceed without API connection")
            print("💡 Setup instructions:")
            print("   1. Get VBEE API token from https://vbee.vn")
            print("   2. Add VBEE_API_TOKEN to .env file")
            print("   3. Check internet connection")
            return
        
        # Test 2: Available voices
        results["voices"] = test_available_voices()
        
        # Test 3: Input validation
        results["validation"] = test_input_validation()
        
        # Test 4: Basic synthesis
        results["synthesis"] = test_basic_synthesis()
        
        # Test 5: Voice configurations
        results["configurations"] = test_voice_configurations()
        
        # Test 6: Duration estimation
        results["duration"] = test_duration_estimation()
        
        # Test 7: Performance
        results["performance"] = test_performance_metrics()
        
        # Test 8: Error handling
        results["error_handling"] = test_error_handling()
        
        # Test 9: Service info
        results["service_info"] = test_service_info()
        
        # Final summary
        print_section("FINAL SUMMARY")
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! TTS module is working perfectly.")
        elif passed >= total * 0.8:
            print("\n✅ MOST TESTS PASSED! TTS module is mostly functional.")
            print("   Minor issues can be addressed later.")
        elif passed >= total * 0.6:
            print("\n⚠️ SOME TESTS FAILED! TTS module has some issues.")
            print("   Check the failed tests and fix issues.")
        else:
            print("\n❌ MANY TESTS FAILED! TTS module needs significant fixes.")
            print("   Review API credentials and network connectivity.")
        
        # Save test results
        save_test_results(results)
        
        print(f"\n🎯 TTS Module testing completed!")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not results.get("connection"):
            print("   - Verify VBEE API credentials")
            print("   - Check VBEE service status")
        if not results.get("synthesis"):
            print("   - Test with shorter text inputs")
            print("   - Verify API quota and permissions")
        if not results.get("performance"):
            print("   - Monitor network latency")
            print("   - Consider caching for common phrases")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
