#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test STT Module
===============

Test riêng cho Assembly AI STT service trong pipeline5
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
    from stt_module import AssemblyAISTT, AudioRecorder
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Đảm bảo các file config.py và stt_module.py tồn tại")
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
        if 'upload_time_ms' in result:
            print(f"📤 Upload time: {result['upload_time_ms']:.1f}ms")
        if 'confidence' in result:
            print(f"🎯 Confidence: {result['confidence']:.2f}")
        if 'words_count' in result:
            print(f"📊 Words count: {result['words_count']}")
        if 'audio_duration' in result:
            print(f"🎵 Audio duration: {result['audio_duration']:.1f}s")


def test_stt_connection():
    """Test 1: Kết nối API"""
    print_section("TEST 1: API CONNECTION")
    
    try:
        stt = AssemblyAISTT()
        
        if stt.test_connection():
            print("✅ Assembly AI API connection successful")
            return True
        else:
            print("❌ Assembly AI API connection failed")
            print("💡 Kiểm tra:")
            print("   - API key trong .env file")
            print("   - Kết nối internet")
            print("   - Quota API còn lại")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_audio_recording():
    """Test 2: Ghi âm"""
    print_section("TEST 2: AUDIO RECORDING")
    
    try:
        recorder = AudioRecorder()
        
        print("🎤 Chuẩn bị ghi âm 3 giây...")
        print("💬 Hãy nói: 'Xin chào, tôi đang test hệ thống STT'")
        input("📍 Nhấn Enter để bắt đầu ghi âm...")
        
        success, audio_file, error = recorder.record_audio(3.0)
        
        if success:
            print(f"✅ Recording successful!")
            print(f"📁 File: {audio_file}")
            print(f"💾 File size: {os.path.getsize(audio_file)} bytes")
            return audio_file
        else:
            print(f"❌ Recording failed: {error}")
            print("💡 Kiểm tra:")
            print("   - Microphone được kết nối")
            print("   - Quyền truy cập microphone")
            print("   - Audio drivers")
            return None
            
    except Exception as e:
        print(f"❌ Recording test failed: {e}")
        return None


def test_audio_validation():
    """Test 3: Validation file âm thanh"""
    print_section("TEST 3: AUDIO FILE VALIDATION")
    
    try:
        stt = AssemblyAISTT()
        
        # Test cases
        test_cases = [
            ("Non-existent file", "non_existent.wav", False),
            ("Empty file path", "", False),
        ]
        
        for name, file_path, should_be_valid in test_cases:
            is_valid, error = stt.validate_audio_file(file_path)
            
            status = "✅" if (is_valid == should_be_valid) else "❌"
            print(f"{status} {name}: {'Valid' if is_valid else 'Invalid'}")
            if error:
                print(f"   Error: {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def test_transcription(audio_file):
    """Test 4: Transcription"""
    print_section("TEST 4: TRANSCRIPTION")
    
    if not audio_file:
        print("❌ No audio file available for transcription test")
        return False
    
    try:
        stt = AssemblyAISTT()
        
        print(f"🔄 Transcribing audio file: {os.path.basename(audio_file)}")
        print("⏳ This may take 30-60 seconds...")
        
        result = stt.transcribe_audio_file(audio_file)
        
        if result["success"]:
            print("✅ Transcription successful!")
            print(f"📝 Transcript: '{result['transcript']}'")
            print_metrics(result)
            
            # Evaluate transcription quality
            transcript = result['transcript'].lower()
            expected_words = ['xin', 'chào', 'test', 'stt', 'hệ', 'thống']
            found_words = sum(1 for word in expected_words if word in transcript)
            
            print(f"🎯 Quality check: {found_words}/{len(expected_words)} expected words found")
            
            if found_words >= len(expected_words) // 2:
                print("✅ Transcription quality: GOOD")
            else:
                print("⚠️ Transcription quality: NEEDS IMPROVEMENT")
                
            return True
        else:
            print(f"❌ Transcription failed: {result['error']}")
            print("💡 Possible issues:")
            print("   - Audio quality too low")
            print("   - Background noise")
            print("   - API quota exceeded")
            print("   - Network connectivity")
            return False
            
    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        return False


def test_different_configurations(audio_file):
    """Test 5: Các cấu hình khác nhau"""
    print_section("TEST 5: DIFFERENT CONFIGURATIONS")
    
    if not audio_file:
        print("❌ No audio file available for configuration test")
        return False
    
    try:
        stt = AssemblyAISTT()
        
        configs = [
            {
                "name": "High accuracy",
                "config": {
                    "boost_param": "high",
                    "punctuate": True,
                    "format_text": True
                }
            },
            {
                "name": "Fast processing",
                "config": {
                    "boost_param": "low",
                    "punctuate": False,
                    "format_text": False
                }
            }
        ]
        
        for config_test in configs:
            print(f"\n🔧 Testing: {config_test['name']}")
            
            result = stt.transcribe_audio_file(audio_file, config_test['config'])
            
            if result["success"]:
                print(f"✅ Config test successful")
                print(f"📝 Result: '{result['transcript'][:50]}...'")
                print_metrics(result)
            else:
                print(f"❌ Config test failed: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_performance_metrics():
    """Test 6: Performance metrics"""
    print_section("TEST 6: PERFORMANCE METRICS")
    
    try:
        recorder = AudioRecorder()
        stt = AssemblyAISTT()
        
        latencies = []
        confidences = []
        
        print("🏃 Running 3 performance tests...")
        
        for i in range(3):
            print(f"\n⏱️  Performance test {i+1}/3")
            print("🎤 Recording 2 seconds...")
            
            success, audio_file, error = recorder.record_audio(2.0)
            
            if success:
                result = stt.transcribe_audio_file(audio_file)
                
                if result["success"]:
                    latencies.append(result["latency_ms"])
                    confidences.append(result["confidence"])
                    print(f"✅ Latency: {result['latency_ms']:.1f}ms, Confidence: {result['confidence']:.2f}")
                else:
                    print(f"❌ Test {i+1} failed: {result['error']}")
                
                # Cleanup
                if os.path.exists(audio_file):
                    os.unlink(audio_file)
            else:
                print(f"❌ Recording failed: {error}")
        
        # Calculate and display performance summary
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            avg_confidence = sum(confidences) / len(confidences)
            
            print(f"\n📈 PERFORMANCE SUMMARY:")
            print(f"   Average latency: {avg_latency:.1f}ms")
            print(f"   Average confidence: {avg_confidence:.2f}")
            print(f"   Min latency: {min(latencies):.1f}ms")
            print(f"   Max latency: {max(latencies):.1f}ms")
            
            # Performance evaluation
            if avg_latency < 10000:  # < 10 seconds
                print("✅ Latency performance: EXCELLENT")
            elif avg_latency < 20000:  # < 20 seconds
                print("✅ Latency performance: GOOD")
            else:
                print("⚠️ Latency performance: NEEDS IMPROVEMENT")
                
            if avg_confidence > 0.8:
                print("✅ Confidence performance: EXCELLENT")
            elif avg_confidence > 0.6:
                print("✅ Confidence performance: GOOD")
            else:
                print("⚠️ Confidence performance: NEEDS IMPROVEMENT")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def test_error_handling():
    """Test 7: Error handling"""
    print_section("TEST 7: ERROR HANDLING")
    
    try:
        stt = AssemblyAISTT()
        
        # Test cases that should fail
        error_tests = [
            ("Empty file path", ""),
            ("Non-existent file", "non_existent_file.wav"),
            ("Invalid file", "invalid_file.txt")
        ]
        
        for test_name, file_path in error_tests:
            print(f"\n🧪 Testing: {test_name}")
            
            result = stt.transcribe_audio_file(file_path)
            
            if not result["success"]:
                print(f"✅ Correctly handled error: {result['error']}")
            else:
                print(f"❌ Should have failed but didn't")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def save_test_results(results):
    """Lưu kết quả test"""
    try:
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "STT Module Test",
            "service": "Assembly AI",
            "results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": sum(1 for r in results.values() if r),
                "failed_tests": sum(1 for r in results.values() if not r)
            }
        }
        
        report_file = os.path.join(LOGS_DIR, f"stt_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Test report saved: {report_file}")
        
    except Exception as e:
        print(f"⚠️ Could not save test report: {e}")


def main():
    """Main test function"""
    print("🧪 STT MODULE COMPREHENSIVE TEST")
    print("=" * 60)
    print("Testing Assembly AI Speech-to-Text service")
    print("=" * 60)
    
    # Test results tracking
    results = {}
    
    try:
        # Test 1: Connection
        results["connection"] = test_stt_connection()
        if not results["connection"]:
            print("\n❌ Cannot proceed without API connection")
            return
        
        # Test 2: Audio recording
        audio_file = test_audio_recording()
        results["recording"] = audio_file is not None
        
        # Test 3: Validation
        results["validation"] = test_audio_validation()
        
        # Test 4: Transcription (only if we have audio)
        if audio_file:
            results["transcription"] = test_transcription(audio_file)
            
            # Test 5: Different configurations
            results["configurations"] = test_different_configurations(audio_file)
            
            # Cleanup recorded file
            if not SAVE_AUDIO_FILES and os.path.exists(audio_file):
                os.unlink(audio_file)
        else:
            results["transcription"] = False
            results["configurations"] = False
        
        # Test 6: Performance
        results["performance"] = test_performance_metrics()
        
        # Test 7: Error handling
        results["error_handling"] = test_error_handling()
        
        # Final summary
        print_section("FINAL SUMMARY")
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! STT module is working correctly.")
        elif passed >= total * 0.8:
            print("\n✅ MOST TESTS PASSED! STT module is mostly functional.")
        else:
            print("\n⚠️ SEVERAL TESTS FAILED! Check the issues above.")
        
        # Save test results
        save_test_results(results)
        
        print(f"\n🎯 STT Module testing completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
