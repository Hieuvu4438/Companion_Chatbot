"""
Test riêng cho VBEE TTS Module - Pipeline 4
Kiểm tra độc lập chức năng Text-to-Speech với metrics chi tiết
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tts_module import VBEETTSModule
from utils import MetricsCollector, Logger, print_header, print_step, format_file_size, ResponseTimeTracker
from config import get_config_status, validate_config

def test_tts_configuration():
    """Test TTS configuration"""
    print_header("KIỂM TRA CẤU HÌNH VBEE TTS")
    
    # Check configuration
    status = get_config_status()
    errors = validate_config()
    
    print("📋 Trạng thái cấu hình:")
    print(f"  ✅ VBEE configured: {status['vbee_configured']}")
    
    if errors:
        print("\n❌ Lỗi cấu hình:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ Cấu hình hoàn tất!")
    return True

def test_tts_service():
    """Test VBEE TTS service"""
    print_header("KIỂM TRA DỊCH VỤ VBEE TTS")
    
    tts = VBEETTSModule()
    
    # Get service status
    status = tts.get_service_status()
    
    print("🔧 Trạng thái dịch vụ:")
    for service_name, service_info in status.items():
        configured = service_info.get('configured', False)
        available = service_info.get('available', False)
        print(f"  {service_name.upper()}:")
        print(f"    - Configured: {'✅' if configured else '❌'}")
        print(f"    - Available: {'✅' if available else '❌'}")
        print(f"    - Voice: {service_info.get('voice', 'N/A')}")
        print(f"    - Description: {service_info.get('voice_description', 'N/A')}")
        print(f"    - Speed: {service_info.get('speed', 'N/A')}")
        print(f"    - Format: {service_info.get('format', 'N/A')}")
    
    return status

def test_vbee_connection():
    """Test VBEE API connection"""
    print_header("KIỂM TRA KẾT NỐI VBEE API")
    
    tts = VBEETTSModule()
    
    print("🔗 Testing VBEE API connection...")
    conn_result = tts.test_connection()
    
    if conn_result["success"]:
        print(f"  ✅ {conn_result['message']}")
        print(f"  🗣️ Voice: {conn_result['voice']}")
        print(f"  ⏱️ Test duration: {conn_result['test_duration']:.3f}s")
        return True
    else:
        print(f"  ❌ Connection failed: {conn_result['error']}")
        return False

def test_available_voices():
    """Test available voice options"""
    print_header("KIỂM TRA GIỌNG NÓI KHẢ DỤNG")
    
    tts = VBEETTSModule()
    
    voices = tts.get_available_voices()
    
    print(f"🗣️ Có {len(voices)} giọng nói khả dụng:")
    
    from config import VBEE_TTS_CONFIG
    current_voice = VBEE_TTS_CONFIG["voice_code"]
    
    for voice_code, description in voices.items():
        current_marker = " (ĐANG SỬ DỤNG)" if voice_code == current_voice else ""
        print(f"  - {voice_code}: {description}{current_marker}")
    
    return True

def test_text_validation():
    """Test text validation for TTS"""
    print_header("KIỂM TRA VALIDATION TEXT")
    
    test_cases = [
        {
            "name": "Text ngắn (bình thường)",
            "text": "Xin chào bác, cháu là trợ lý AI.",
            "should_pass": True
        },
        {
            "name": "Text trung bình",
            "text": "Hôm nay là một ngày đẹp trời. Bác có dự định gì đặc biệt không? Cháu mong bác luôn vui vẻ và khỏe mạnh.",
            "should_pass": True
        },
        {
            "name": "Text có ký tự đặc biệt",
            "text": "Nhiệt độ hôm nay là 25°C. Thời gian hiện tại: 14:30. Tỷ lệ: 50%.",
            "should_pass": True
        },
        {
            "name": "Text rất dài (vượt giới hạn)",
            "text": "Đây là text rất dài để test giới hạn của VBEE TTS. " * 200,  # ~10,000 characters
            "should_pass": False
        },
        {
            "name": "Text rỗng",
            "text": "",
            "should_pass": False
        },
        {
            "name": "Text chỉ có space",
            "text": "   ",
            "should_pass": False
        }
    ]
    
    tts = VBEETTSModule()
    
    print("🧪 Test cases validation:")
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        print(f"  Text length: {len(test_case['text'])} characters")
        print(f"  Text preview: {test_case['text'][:50]}{'...' if len(test_case['text']) > 50 else ''}")
        
        validation = tts.validate_text(test_case['text'])
        
        if test_case['should_pass']:
            if validation['valid']:
                print(f"  ✅ PASS: Text hợp lệ")
                print(f"      Estimated duration: {validation.get('estimated_duration', 0):.1f}s")
            else:
                print(f"  ❌ FAIL: Expected pass but got: {validation['error']}")
        else:
            if not validation['valid']:
                print(f"  ✅ PASS: Correctly rejected - {validation['error']}")
            else:
                print(f"  ❌ FAIL: Expected rejection but passed")

def test_tts_with_sample_texts():
    """Test TTS with various sample texts"""
    print_header("KIỂM TRA TTS VỚI TEXT MẪU")
    
    # Sample texts for elder care chatbot
    sample_texts = [
        {
            "name": "Chào hỏi thân thiện",
            "text": "Xin chào bác! Cháu là trợ lý AI, sẵn sàng tâm sự với bác.",
            "category": "greeting"
        },
        {
            "name": "Hỏi han sức khỏe",
            "text": "Hôm nay bác cảm thấy thế nào? Có khỏe mạnh không bác?",
            "category": "health_inquiry"
        },
        {
            "name": "An ủi động viên",
            "text": "Bác đừng buồn nhé. Cháu luôn ở đây lắng nghe và chia sẻ với bác.",
            "category": "comfort"
        },
        {
            "name": "Hướng dẫn y tế",
            "text": "Bác nên uống đủ nước, ăn nhiều rau xanh và nghỉ ngơi hợp lý.",
            "category": "health_advice"
        },
        {
            "name": "Chia sẻ về quê hương",
            "text": "Quê hương là nơi có nhiều kỷ niệm đẹp. Bác nhớ món ăn gì ở quê nhất?",
            "category": "hometown"
        },
        {
            "name": "Text dài - kể chuyện",
            "text": "Ngày xưa, ở một làng nhỏ bên sông, có một cụ già sống một mình. Mỗi sáng, cụ đều ngồi bên hiên nhà ngắm sông nước mênh mông. Cụ thường kể cho trẻ con nghe những câu chuyện cổ tích đầy ý nghĩa về lòng hiếu thảo và tình yêu thương.",
            "category": "storytelling"
        }
    ]
    
    # Initialize TTS module
    tts = VBEETTSModule()
    metrics_collector = MetricsCollector()
    time_tracker = ResponseTimeTracker()
    
    # Check if TTS is available
    status = tts.get_service_status()
    if not status.get("vbee_tts", {}).get("available", False):
        print("❌ VBEE TTS không khả dụng")
        return False
    
    print(f"🔧 Service sẵn sàng với voice: {status['vbee_tts']['voice']}")
    
    # Test each sample text
    for i, sample in enumerate(sample_texts, 1):
        print(f"\n{'='*70}")
        print(f"🗣️  TEST {i}/{len(sample_texts)}: {sample['name']}")
        print(f"{'='*70}")
        
        print_step(1, "Chuẩn bị text")
        print(f"  📝 Text: {sample['text']}")
        print(f"  📊 Length: {len(sample['text'])} characters")
        print(f"  🏷️ Category: {sample['category']}")
        
        # Validate text first
        validation = tts.validate_text(sample['text'])
        if not validation['valid']:
            print(f"  ❌ Text validation failed: {validation['error']}")
            continue
        
        print(f"  ⏱️ Estimated duration: {validation['estimated_duration']:.1f}s")
        
        print_step(2, "Thực hiện TTS synthesis")
        
        # Generate output path
        output_path = os.path.join("audio_samples", "output", f"test_vbee_{i}_{sample['category']}.wav")
        
        metrics_collector.start_timer(f"tts_synthesis_{i}")
        
        result = tts.synthesize_with_retry(sample['text'], output_path)
        
        processing_time = metrics_collector.end_timer(f"tts_synthesis_{i}")
        time_tracker.add_time("tts", processing_time)
        
        if result["success"]:
            print(f"  ✅ TTS Success!")
            print(f"  ⏱️  Processing time: {result['processing_time']:.3f}s")
            print(f"  📁 Output file: {result['output_path']}")
            print(f"  📦 File size: {format_file_size(result['file_size'])}")
            print(f"  🗣️ Voice: {result['voice_code']}")
            
            # Calculate efficiency metrics
            chars_per_second = len(sample['text']) / result['processing_time'] if result['processing_time'] > 0 else 0
            print(f"  📈 Efficiency: {chars_per_second:.1f} chars/second")
            
            # Add to metrics
            metrics_collector.add_metric(f"vbee_success_{i}", True)
            metrics_collector.add_metric(f"vbee_processing_time_{i}", result['processing_time'])
            metrics_collector.add_metric(f"vbee_file_size_{i}", result['file_size'])
            metrics_collector.add_metric(f"vbee_efficiency_{i}", chars_per_second)
            
            # Verify file exists and is valid
            if os.path.exists(result['output_path']):
                file_size = os.path.getsize(result['output_path'])
                if file_size > 1024:  # At least 1KB
                    print(f"  ✅ Audio file created successfully")
                else:
                    print(f"  ⚠️  Audio file seems too small ({file_size} bytes)")
            else:
                print(f"  ❌ Audio file not found")
            
        else:
            print(f"  ❌ TTS Failed: {result['error']}")
            metrics_collector.add_metric(f"vbee_success_{i}", False)
            metrics_collector.add_metric(f"vbee_error_{i}", result['error'])
        
        print()
    
    # Display overall metrics
    print_header("TỔNG KẾT METRICS TTS")
    metrics_collector.display_metrics("VBEE TTS Test Results")
    
    # Display response time statistics
    time_tracker.display_all_stats()
    
    return True

def test_tts_performance():
    """Test TTS performance with different scenarios"""
    print_header("KIỂM TRA HIỆU SUẤT TTS")
    
    # Performance test texts of different lengths
    perf_texts = [
        ("Ngắn", "Text ngắn"),
        ("Trung bình", "Text trung bình với nhiều từ hơn để kiểm tra hiệu suất xử lý của hệ thống TTS trong điều kiện bình thường."),
        ("Dài", "Text dài hơn nữa với rất nhiều từ và cụm từ phức tạp để kiểm tra khả năng xử lý của hệ thống text-to-speech trong điều kiện tải cao và text có độ phức tạp cao hơn bình thường trong cuộc sống hàng ngày của người cao tuổi.")
    ]
    
    tts = VBEETTSModule()
    performance_metrics = MetricsCollector()
    
    print("🔬 Testing performance scenarios:")
    
    # Test sequential processing
    print_step(1, "Sequential Processing Test")
    performance_metrics.start_timer("sequential_processing")
    
    successful_syntheses = 0
    total_characters = 0
    total_processing_time = 0
    
    for i, (name, text) in enumerate(perf_texts, 1):
        print(f"\n  Testing {name} text ({len(text)} chars)...")
        total_characters += len(text)
        
        output_path = os.path.join("audio_samples", "output", f"perf_test_{i}_{name}.wav")
        
        result = tts.synthesize_text(text, output_path)
        
        if result['success']:
            successful_syntheses += 1
            total_processing_time += result['processing_time']
            
            chars_per_sec = len(text) / result['processing_time'] if result['processing_time'] > 0 else 0
            print(f"    ✅ Success: {result['processing_time']:.3f}s ({chars_per_sec:.1f} chars/sec)")
        else:
            print(f"    ❌ Failed: {result['error']}")
    
    sequential_time = performance_metrics.end_timer("sequential_processing")
    
    # Calculate performance metrics
    success_rate = successful_syntheses / len(perf_texts) if perf_texts else 0
    avg_processing_time = total_processing_time / successful_syntheses if successful_syntheses > 0 else 0
    overall_chars_per_sec = total_characters / total_processing_time if total_processing_time > 0 else 0
    
    performance_metrics.add_metric("success_rate", success_rate)
    performance_metrics.add_metric("avg_processing_time", avg_processing_time)
    performance_metrics.add_metric("overall_chars_per_second", overall_chars_per_sec)
    performance_metrics.add_metric("total_characters", total_characters)
    performance_metrics.add_metric("total_processing_time", total_processing_time)
    performance_metrics.add_metric("sequential_time", sequential_time)
    
    print(f"\n📊 Performance Summary:")
    print(f"  ✅ Success rate: {success_rate:.1%}")
    print(f"  ⏱️  Average processing time: {avg_processing_time:.3f}s")
    print(f"  📈 Overall throughput: {overall_chars_per_sec:.1f} chars/sec")
    print(f"  📊 Total characters: {total_characters}")
    print(f"  ⏱️  Total processing time: {total_processing_time:.3f}s")
    print(f"  🕐 Sequential test time: {sequential_time:.3f}s")
    
    # Display detailed metrics
    performance_metrics.display_metrics("TTS Performance Metrics")
    
    return True

def test_output_quality():
    """Test output audio quality"""
    print_header("KIỂM TRA CHẤT LƯỢNG OUTPUT")
    
    # Check output directory
    output_dir = Path("audio_samples/output")
    audio_files = list(output_dir.glob("*.wav"))
    
    if not audio_files:
        print("⚠️  Không tìm thấy file audio output để kiểm tra")
        print("📝 Chạy test TTS trước để tạo file output")
        return False
    
    print(f"🎵 Tìm thấy {len(audio_files)} file audio output:")
    
    total_files = 0
    total_size = 0
    size_distribution = {"small": 0, "medium": 0, "large": 0, "too_small": 0}
    
    for audio_file in audio_files:
        file_size = audio_file.stat().st_size
        total_files += 1
        total_size += file_size
        
        print(f"\n  📁 {audio_file.name}")
        print(f"    📦 Size: {format_file_size(file_size)}")
        
        # Categorize file size
        if file_size < 1024:  # Less than 1KB
            print(f"    ⚠️  File rất nhỏ, có thể lỗi")
            size_distribution["too_small"] += 1
        elif file_size < 100 * 1024:  # Less than 100KB
            print(f"    ✅ File size nhỏ (text ngắn)")
            size_distribution["small"] += 1
        elif file_size < 1024 * 1024:  # Less than 1MB
            print(f"    ✅ File size trung bình")
            size_distribution["medium"] += 1
        else:  # 1MB or larger
            print(f"    ✅ File size lớn (text dài)")
            size_distribution["large"] += 1
        
        # Try to get more info for WAV files
        if audio_file.suffix.lower() == '.wav':
            try:
                import wave
                with wave.open(str(audio_file), 'rb') as wav_file:
                    duration = wav_file.getnframes() / wav_file.getframerate()
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    
                    print(f"    🎵 Duration: {duration:.1f}s")
                    print(f"    🔊 Sample rate: {sample_rate}Hz")
                    print(f"    📻 Channels: {channels}")
                    
                    # Quality checks
                    if sample_rate < 16000:
                        print(f"    ⚠️  Sample rate thấp")
                    if duration < 0.5:
                        print(f"    ⚠️  Duration rất ngắn")
                    
            except Exception as e:
                print(f"    ⚠️  Cannot read WAV info: {e}")
    
    # Summary
    avg_size = total_size / total_files if total_files > 0 else 0
    
    print(f"\n📊 Tổng kết chất lượng:")
    print(f"  📁 Total files: {total_files}")
    print(f"  📦 Total size: {format_file_size(total_size)}")
    print(f"  📊 Average size: {format_file_size(avg_size)}")
    print(f"  📈 Size distribution:")
    print(f"    - Too small (< 1KB): {size_distribution['too_small']}")
    print(f"    - Small (1KB-100KB): {size_distribution['small']}")
    print(f"    - Medium (100KB-1MB): {size_distribution['medium']}")
    print(f"    - Large (> 1MB): {size_distribution['large']}")
    
    # Quality assessment
    quality_score = (size_distribution['small'] + size_distribution['medium'] + size_distribution['large']) / total_files if total_files > 0 else 0
    
    if quality_score >= 0.9:
        print(f"  ✅ Output quality: Excellent ({quality_score:.1%})")
    elif quality_score >= 0.7:
        print(f"  ✅ Output quality: Good ({quality_score:.1%})")
    elif quality_score >= 0.5:
        print(f"  ⚠️  Output quality: Fair ({quality_score:.1%})")
    else:
        print(f"  ❌ Output quality: Poor ({quality_score:.1%})")
    
    return True

def main():
    """Main test function"""
    print_header("VBEE TTS MODULE TEST SUITE - PIPELINE 4", 80)
    
    logger = Logger("vbee_tts_test")
    overall_metrics = MetricsCollector()
    
    overall_metrics.start_timer("total_test_time")
    
    # Test steps
    test_results = {
        "configuration": False,
        "service": False,
        "connection": False,
        "voices": False,
        "validation": False,
        "sample_texts": False,
        "performance": False,
        "output_quality": False
    }
    
    try:
        # 1. Test configuration
        print_step(1, "Kiểm tra cấu hình VBEE TTS")
        test_results["configuration"] = test_tts_configuration()
        
        if not test_results["configuration"]:
            logger.error("Cấu hình VBEE TTS không hợp lệ. Dừng test.")
            return
        
        # 2. Test service
        print_step(2, "Kiểm tra trạng thái dịch vụ")
        status = test_tts_service()
        test_results["service"] = any(s.get('available', False) for s in status.values() if isinstance(s, dict))
        
        # 3. Test connection
        print_step(3, "Kiểm tra kết nối VBEE API")
        test_results["connection"] = test_vbee_connection()
        
        if not test_results["connection"]:
            logger.error("Không thể kết nối VBEE API. Dừng test.")
            return
        
        # 4. Test available voices
        print_step(4, "Kiểm tra giọng nói khả dụng")
        test_results["voices"] = test_available_voices()
        
        # 5. Test validation
        print_step(5, "Kiểm tra validation text")
        test_results["validation"] = test_text_validation()
        
        # 6. Test with sample texts
        print_step(6, "Kiểm tra TTS với text mẫu")
        test_results["sample_texts"] = test_tts_with_sample_texts()
        
        # 7. Test performance (if sample texts successful)
        if test_results["sample_texts"]:
            print_step(7, "Kiểm tra hiệu suất TTS")
            test_results["performance"] = test_tts_performance()
        
        # 8. Test output quality
        print_step(8, "Kiểm tra chất lượng output")
        test_results["output_quality"] = test_output_quality()
        
    except KeyboardInterrupt:
        logger.warning("Test bị ngắt bởi người dùng")
    except Exception as e:
        logger.error(f"Lỗi trong quá trình test: {e}")
    
    # Calculate total time
    total_test_time = overall_metrics.end_timer("total_test_time")
    
    # Final results
    print_header("KẾT QUẢ CUỐI CÙNG", 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"📊 Tổng quan test:")
    print(f"  ✅ Passed: {passed_tests}/{total_tests}")
    print(f"  ⏱️  Total time: {total_test_time:.3f}s")
    print()
    
    print("📋 Chi tiết kết quả:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        logger.success("🎉 Tất cả VBEE TTS tests đều PASS!")
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} tests thất bại")
    
    print(f"\n📝 Ghi chú:")
    print(f"  - Logs được lưu trong thư mục logs/")
    print(f"  - Audio output được lưu trong audio_samples/output/")
    print(f"  - Cấu hình VBEE API key trong config.py")
    print(f"  - Có thể thay đổi giọng nói trong config.py (VBEE_TTS_CONFIG)")

if __name__ == "__main__":
    main()
