"""
Test riêng cho TTS Module - Pipeline 3
Kiểm tra độc lập chức năng Text-to-Speech với metrics chi tiết
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tts_module import TTSModule
from utils import MetricsCollector, Logger, print_header, print_step, format_file_size
from config import get_config_status, validate_config

def test_tts_configuration():
    """Test TTS configuration"""
    print_header("KIỂM TRA CẤU HÌNH TTS")
    
    # Check configuration
    status = get_config_status()
    errors = validate_config()
    
    print("📋 Trạng thái cấu hình:")
    print(f"  ✅ FPT.AI configured: {status['fpt_configured']}")
    print(f"  ✅ Google Cloud configured: {status['google_cloud_configured']}")
    
    if errors:
        print("\n❌ Lỗi cấu hình:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ Cấu hình hoàn tất!")
    return True

def test_tts_services():
    """Test individual TTS services"""
    print_header("KIỂM TRA DỊCH VỤ TTS")
    
    tts = TTSModule()
    
    # Get service status
    status = tts.get_service_status()
    
    print("🔧 Trạng thái dịch vụ:")
    for service_name, service_info in status.items():
        if service_name != "last_used_service":
            configured = service_info.get('configured', False)
            available = service_info.get('available', False)
            print(f"  {service_name.upper()}:")
            print(f"    - Configured: {'✅' if configured else '❌'}")
            print(f"    - Available: {'✅' if available else '❌'}")
    
    return status

def test_text_validation():
    """Test text validation for TTS"""
    print_header("KIỂM TRA VALIDATION TEXT")
    
    test_cases = [
        {
            "name": "Text ngắn (bình thường)",
            "text": "Xin chào, tôi là trợ lý AI.",
            "should_pass": True
        },
        {
            "name": "Text trung bình",
            "text": "Đây là một đoạn text trung bình để test chức năng TTS. " * 10,
            "should_pass": True
        },
        {
            "name": "Text rất dài (vượt giới hạn)",
            "text": "Đây là text rất dài. " * 500,  # ~10,000 characters
            "should_pass": False
        },
        {
            "name": "Text rỗng",
            "text": "",
            "should_pass": False
        }
    ]
    
    tts = TTSModule()
    
    print("🧪 Test cases validation:")
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        print(f"  Text length: {len(test_case['text'])} characters")
        print(f"  Text preview: {test_case['text'][:50]}{'...' if len(test_case['text']) > 50 else ''}")
        
        # Test without actually calling TTS
        if len(test_case['text']) > 5000:
            is_valid = False
            message = "Text quá dài (tối đa 5000 ký tự)"
        elif len(test_case['text']) == 0:
            is_valid = False
            message = "Text rỗng"
        else:
            is_valid = True
            message = "Text hợp lệ"
        
        if test_case['should_pass']:
            if is_valid:
                print(f"  ✅ PASS: {message}")
            else:
                print(f"  ❌ FAIL: Expected pass but got: {message}")
        else:
            if not is_valid:
                print(f"  ✅ PASS: Correctly rejected - {message}")
            else:
                print(f"  ❌ FAIL: Expected rejection but passed")

def test_tts_with_sample_texts():
    """Test TTS with various sample texts"""
    print_header("KIỂM TRA TTS VỚI TEXT MẪU")
    
    # Sample texts for testing
    sample_texts = [
        {
            "name": "Chào hỏi đơn giản",
            "text": "Xin chào, tôi là trợ lý AI của bạn.",
            "expected_duration": 3  # seconds
        },
        {
            "name": "Câu hỏi về sức khỏe",
            "text": "Hôm nay bạn cảm thấy thế nào? Có cần tôi giúp gì không?",
            "expected_duration": 4
        },
        {
            "name": "Hướng dẫn ngắn",
            "text": "Để sử dụng ứng dụng này, bạn chỉ cần nói vào microphone và tôi sẽ trả lời.",
            "expected_duration": 6
        },
        {
            "name": "Text với số và ký tự đặc biệt",
            "text": "Hôm nay là ngày 12 tháng 8 năm 2025. Nhiệt độ là 25°C.",
            "expected_duration": 5
        },
        {
            "name": "Text dài",
            "text": "Trí tuệ nhân tạo là một lĩnh vực công nghệ đang phát triển rất nhanh. "
                    "Nó giúp chúng ta giải quyết nhiều vấn đề phức tạp trong cuộc sống hàng ngày. "
                    "Từ nhận dạng giọng nói đến xử lý ngôn ngữ tự nhiên, AI đã tạo ra những bước tiến vượt bậc.",
            "expected_duration": 15
        }
    ]
    
    # Initialize TTS module
    tts = TTSModule()
    metrics_collector = MetricsCollector()
    
    # Get service status
    status = tts.get_service_status()
    available_services = [name for name, info in status.items() 
                         if isinstance(info, dict) and info.get('available', False)]
    
    if not available_services:
        print("❌ Không có TTS service nào khả dụng")
        return False
    
    print(f"🔧 Services khả dụng: {', '.join(available_services)}")
    
    # Test each sample text
    for i, sample in enumerate(sample_texts, 1):
        print(f"\n{'='*60}")
        print(f"🗣️  TEST {i}/{len(sample_texts)}: {sample['name']}")
        print(f"{'='*60}")
        
        print_step(1, "Chuẩn bị text")
        print(f"  📝 Text: {sample['text']}")
        print(f"  📊 Length: {len(sample['text'])} characters")
        print(f"  ⏱️  Expected duration: ~{sample['expected_duration']}s")
        
        # Test with each available service
        for service in ["fpt", "google"]:
            if f"{service}_ai" in [s.replace("_", "_") for s in available_services] or \
               f"{service}_cloud" in [s.replace("_", "_") for s in available_services]:
                
                print_step(2, f"Thử TTS với {service.upper()}")
                
                metrics_collector.start_timer(f"tts_{service}_time")
                
                # Generate output path
                output_path = f"audio_samples/output/test_{service}_{i}.wav"
                
                result = tts.synthesize(
                    sample['text'], 
                    output_path=output_path,
                    force_service=service
                )
                
                processing_time = metrics_collector.end_timer(f"tts_{service}_time")
                
                if result['success']:
                    print(f"  ✅ {service.upper()} Success!")
                    print(f"  ⏱️  Processing time: {result['processing_time']:.3f}s")
                    print(f"  📁 Output file: {result['output_path']}")
                    
                    # Check if file exists and get info
                    if os.path.exists(result['output_path']):
                        file_size = os.path.getsize(result['output_path'])
                        print(f"  📦 File size: {format_file_size(file_size)}")
                        
                        # Estimate audio duration (rough calculation)
                        # For 16kHz, 16-bit, mono WAV: ~32KB per second
                        estimated_duration = file_size / (32 * 1024)
                        print(f"  🎵 Estimated duration: {estimated_duration:.1f}s")
                        
                        # Add to metrics
                        metrics_collector.add_metric(f"{service}_success", True)
                        metrics_collector.add_metric(f"{service}_processing_time", result['processing_time'])
                        metrics_collector.add_metric(f"{service}_file_size", file_size)
                        metrics_collector.add_metric(f"{service}_estimated_duration", estimated_duration)
                    else:
                        print(f"  ⚠️  File không tồn tại sau khi tạo")
                    
                    break  # Success, no need to try other services for this text
                else:
                    print(f"  ❌ {service.upper()} Failed: {result['error']}")
                    metrics_collector.add_metric(f"{service}_success", False)
                    metrics_collector.add_metric(f"{service}_error", result['error'])
        
        print()
    
    # Display overall metrics
    print_header("TỔNG KẾT METRICS TTS")
    metrics_collector.display_metrics("TTS Test Results")
    
    return True

def test_tts_performance():
    """Test TTS performance with different scenarios"""
    print_header("KIỂM TRA HIỆU SUẤT TTS")
    
    # Performance test texts
    perf_texts = [
        "Ngắn",
        "Text trung bình với nhiều từ hơn để test performance của hệ thống TTS.",
        "Text dài hơn nữa với rất nhiều từ và cụm từ phức tạp để kiểm tra khả năng xử lý của hệ thống text-to-speech trong điều kiện tải cao và text có độ phức tạp cao hơn bình thường trong cuộc sống hàng ngày."
    ]
    
    tts = TTSModule()
    performance_metrics = MetricsCollector()
    
    print("🔬 Testing performance scenarios:")
    
    # Test sequential processing
    print_step(1, "Sequential Processing")
    performance_metrics.start_timer("sequential_processing")
    
    successful_syntheses = 0
    total_characters = 0
    total_processing_time = 0
    
    for i, text in enumerate(perf_texts):
        total_characters += len(text)
        
        result = tts.synthesize(
            text, 
            output_path=f"audio_samples/output/perf_test_{i}.wav"
        )
        
        if result['success']:
            successful_syntheses += 1
            total_processing_time += result['processing_time']
            print(f"    ✅ Text {i+1}: {result['processing_time']:.3f}s ({len(text)} chars)")
        else:
            print(f"    ❌ Text {i+1}: Failed - {result['error']}")
    
    sequential_time = performance_metrics.end_timer("sequential_processing")
    
    # Calculate performance metrics
    if total_characters > 0:
        chars_per_second = total_characters / total_processing_time if total_processing_time > 0 else 0
        performance_metrics.add_metric("chars_per_second", chars_per_second)
    
    performance_metrics.add_metric("success_rate", successful_syntheses / len(perf_texts))
    performance_metrics.add_metric("total_sequential_time", sequential_time)
    performance_metrics.add_metric("avg_processing_time", total_processing_time / successful_syntheses if successful_syntheses > 0 else 0)
    
    print(f"  📊 Sequential results:")
    print(f"    ✅ Success: {successful_syntheses}/{len(perf_texts)}")
    print(f"    ⏱️  Total time: {sequential_time:.3f}s")
    print(f"    🚀 Avg processing: {total_processing_time / successful_syntheses:.3f}s" if successful_syntheses > 0 else "")
    if total_characters > 0 and total_processing_time > 0:
        print(f"    📈 Throughput: {chars_per_second:.1f} chars/sec")
    
    # Display performance metrics
    performance_metrics.display_metrics("TTS Performance Results")
    
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
    
    for audio_file in audio_files:
        file_size = audio_file.stat().st_size
        total_files += 1
        total_size += file_size
        
        print(f"  📁 {audio_file.name}")
        print(f"    📦 Size: {format_file_size(file_size)}")
        
        # Basic quality checks
        if file_size < 1024:  # Less than 1KB is suspicious
            print(f"    ⚠️  File rất nhỏ, có thể lỗi")
        elif file_size > 10 * 1024 * 1024:  # More than 10MB is suspicious
            print(f"    ⚠️  File rất lớn, kiểm tra lại")
        else:
            print(f"    ✅ File size bình thường")
    
    # Summary
    avg_size = total_size / total_files if total_files > 0 else 0
    print(f"\n📊 Tổng kết chất lượng:")
    print(f"  📁 Total files: {total_files}")
    print(f"  📦 Total size: {format_file_size(total_size)}")
    print(f"  📊 Average size: {format_file_size(avg_size)}")
    
    return True

def main():
    """Main test function"""
    print_header("TTS MODULE TEST SUITE - PIPELINE 3", 80)
    
    logger = Logger("tts_test")
    overall_metrics = MetricsCollector()
    
    overall_metrics.start_timer("total_test_time")
    
    # Test steps
    test_results = {
        "configuration": False,
        "services": False,
        "validation": False,
        "sample_texts": False,
        "performance": False,
        "output_quality": False
    }
    
    try:
        # 1. Test configuration
        print_step(1, "Kiểm tra cấu hình TTS")
        test_results["configuration"] = test_tts_configuration()
        
        if not test_results["configuration"]:
            logger.error("Cấu hình TTS không hợp lệ. Dừng test.")
            return
        
        # 2. Test services
        print_step(2, "Kiểm tra trạng thái dịch vụ")
        status = test_tts_services()
        test_results["services"] = any(s.get('available', False) for s in status.values() if isinstance(s, dict))
        
        # 3. Test validation
        print_step(3, "Kiểm tra validation text")
        test_results["validation"] = test_text_validation()
        
        # 4. Test with sample texts
        print_step(4, "Kiểm tra TTS với text mẫu")
        test_results["sample_texts"] = test_tts_with_sample_texts()
        
        # 5. Test performance (if sample texts successful)
        if test_results["sample_texts"]:
            print_step(5, "Kiểm tra hiệu suất TTS")
            test_results["performance"] = test_tts_performance()
        
        # 6. Test output quality
        print_step(6, "Kiểm tra chất lượng output")
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
        logger.success("🎉 Tất cả TTS tests đều PASS!")
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} tests thất bại")
    
    print(f"\n📝 Ghi chú:")
    print(f"  - Logs được lưu trong thư mục logs/")
    print(f"  - Audio output được lưu trong audio_samples/output/")
    print(f"  - Cấu hình API keys trong config.py để test các dịch vụ")

if __name__ == "__main__":
    main()
