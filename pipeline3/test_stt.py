"""
Test riêng cho STT Module - Pipeline 3
Kiểm tra độc lập chức năng Speech-to-Text với metrics chi tiết
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stt_module import STTModule
from utils import MetricsCollector, Logger, print_header, print_step, AudioUtils
from config import get_config_status, validate_config

def test_stt_configuration():
    """Test STT configuration"""
    print_header("KIỂM TRA CÂU HỨC STT")
    
    # Check configuration
    status = get_config_status()
    errors = validate_config()
    
    print("📋 Trạng thái cấu hình:")
    print(f"  ✅ FPT.AI configured: {status['fpt_configured']}")
    print(f"  ✅ OpenAI configured: {status['openai_configured']}")
    
    if errors:
        print("\n❌ Lỗi cấu hình:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ Cấu hình hoàn tất!")
    return True

def test_stt_services():
    """Test individual STT services"""
    print_header("KIỂM TRA DỊCH VỤ STT")
    
    stt = STTModule()
    
    # Get service status
    status = stt.get_service_status()
    
    print("🔧 Trạng thái dịch vụ:")
    for service_name, service_info in status.items():
        if service_name != "last_used_service":
            configured = service_info.get('configured', False)
            available = service_info.get('available', False)
            print(f"  {service_name.upper()}:")
            print(f"    - Configured: {'✅' if configured else '❌'}")
            print(f"    - Available: {'✅' if available else '❌'}")
    
    return status

def test_audio_file_validation():
    """Test audio file validation"""
    print_header("KIỂM TRA VALIDATION FILE AUDIO")
    
    # Test cases for validation
    test_cases = [
        {
            "name": "File không tồn tại",
            "path": "nonexistent.wav",
            "should_pass": False
        },
        {
            "name": "File format không hỗ trợ",
            "path": "test.txt",
            "should_pass": False
        }
    ]
    
    print("🧪 Test cases validation:")
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        print(f"  Path: {test_case['path']}")
        
        is_valid, message = AudioUtils.validate_audio_file(test_case['path'])
        
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

def test_stt_with_sample_audio():
    """Test STT with sample audio files"""
    print_header("KIỂM TRA STT VỚI FILE AUDIO MẪU")
    
    # Look for sample audio files
    sample_dir = Path("audio_samples/input")
    audio_files = []
    
    # Find audio files
    for ext in ['.wav', '.mp3', '.m4a', '.flac']:
        audio_files.extend(sample_dir.glob(f"*{ext}"))
    
    if not audio_files:
        print("⚠️  Không tìm thấy file audio mẫu trong audio_samples/input/")
        print("📝 Hướng dẫn:")
        print("  1. Tạo thư mục audio_samples/input/ (đã tạo)")
        print("  2. Đặt file audio mẫu (.wav, .mp3, .m4a) vào thư mục này")
        print("  3. Chạy lại test này")
        return False
    
    print(f"🎵 Tìm thấy {len(audio_files)} file audio:")
    for audio_file in audio_files:
        print(f"  - {audio_file.name}")
    
    # Initialize STT module
    stt = STTModule()
    metrics_collector = MetricsCollector()
    
    # Test each audio file
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n{'='*60}")
        print(f"🎤 TEST {i}/{len(audio_files)}: {audio_file.name}")
        print(f"{'='*60}")
        
        # Get audio info first
        print_step(1, "Phân tích file audio")
        audio_info = AudioUtils.get_audio_info(str(audio_file))
        
        if 'error' in audio_info:
            print(f"❌ Không thể phân tích audio: {audio_info['error']}")
            continue
        
        print(f"  📊 Duration: {audio_info['duration_seconds']:.1f}s ({audio_info['duration_minutes']:.2f} phút)")
        print(f"  📦 File size: {audio_info['file_size_mb']:.2f}MB")
        print(f"  🔊 Sample rate: {audio_info['sample_rate']}Hz")
        print(f"  📻 Channels: {audio_info['channels']}")
        
        # Test with FPT.AI first (if available)
        services_to_test = ["fpt", "openai"]
        
        for service in services_to_test:
            print_step(2, f"Thử STT với {service.upper()}")
            
            metrics_collector.start_timer(f"stt_{service}_time")
            
            result = stt.transcribe(str(audio_file), force_service=service)
            
            processing_time = metrics_collector.end_timer(f"stt_{service}_time")
            
            if result['success']:
                print(f"  ✅ {service.upper()} Success!")
                print(f"  ⏱️  Processing time: {result['processing_time']:.3f}s")
                print(f"  📝 Transcription: {result['text']}")
                print(f"  📊 Text length: {len(result['text'])} characters")
                
                # Add to metrics
                metrics_collector.add_metric(f"{service}_success", True)
                metrics_collector.add_metric(f"{service}_processing_time", result['processing_time'])
                metrics_collector.add_metric(f"{service}_text_length", len(result['text']))
                
                break  # Success, no need to try other services
            else:
                print(f"  ❌ {service.upper()} Failed: {result['error']}")
                metrics_collector.add_metric(f"{service}_success", False)
                metrics_collector.add_metric(f"{service}_error", result['error'])
        
        print()
    
    # Display overall metrics
    print_header("TỔNG KẾT METRICS STT")
    metrics_collector.display_metrics("STT Test Results")
    
    return True

def test_stt_performance():
    """Test STT performance with different scenarios"""
    print_header("KIỂM TRA HIỆU SUẤT STT")
    
    sample_dir = Path("audio_samples/input")
    audio_files = list(sample_dir.glob("*.wav")) + list(sample_dir.glob("*.mp3"))
    
    if not audio_files:
        print("⚠️  Cần file audio để test performance")
        return False
    
    stt = STTModule()
    performance_metrics = MetricsCollector()
    
    # Test scenarios
    scenarios = [
        {"name": "Sequential Processing", "parallel": False},
    ]
    
    for scenario in scenarios:
        print(f"\n🔬 Testing: {scenario['name']}")
        
        performance_metrics.start_timer(f"scenario_{scenario['name']}")
        
        successful_transcriptions = 0
        total_audio_duration = 0
        total_processing_time = 0
        
        for audio_file in audio_files[:3]:  # Test with first 3 files
            audio_info = AudioUtils.get_audio_info(str(audio_file))
            
            if 'error' not in audio_info:
                total_audio_duration += audio_info['duration_seconds']
                
                result = stt.transcribe(str(audio_file))
                
                if result['success']:
                    successful_transcriptions += 1
                    total_processing_time += result['processing_time']
        
        scenario_time = performance_metrics.end_timer(f"scenario_{scenario['name']}")
        
        # Calculate metrics
        if total_audio_duration > 0:
            real_time_factor = total_processing_time / total_audio_duration
            performance_metrics.add_metric(f"{scenario['name']}_real_time_factor", real_time_factor)
        
        performance_metrics.add_metric(f"{scenario['name']}_success_rate", 
                                     successful_transcriptions / len(audio_files[:3]) if audio_files else 0)
        performance_metrics.add_metric(f"{scenario['name']}_total_time", scenario_time)
        
        print(f"  ✅ Completed: {successful_transcriptions}/{len(audio_files[:3])} successful")
        print(f"  ⏱️  Total time: {scenario_time:.3f}s")
        if total_audio_duration > 0:
            print(f"  🚀 Real-time factor: {real_time_factor:.2f}x")
    
    # Display performance metrics
    performance_metrics.display_metrics("STT Performance Results")
    
    return True

def main():
    """Main test function"""
    print_header("STT MODULE TEST SUITE - PIPELINE 3", 80)
    
    logger = Logger("stt_test")
    overall_metrics = MetricsCollector()
    
    overall_metrics.start_timer("total_test_time")
    
    # Test steps
    test_results = {
        "configuration": False,
        "services": False,
        "validation": False,
        "sample_audio": False,
        "performance": False
    }
    
    try:
        # 1. Test configuration
        print_step(1, "Kiểm tra cấu hình STT")
        test_results["configuration"] = test_stt_configuration()
        
        if not test_results["configuration"]:
            logger.error("Cấu hình STT không hợp lệ. Dừng test.")
            return
        
        # 2. Test services
        print_step(2, "Kiểm tra trạng thái dịch vụ")
        status = test_stt_services()
        test_results["services"] = any(s.get('available', False) for s in status.values() if isinstance(s, dict))
        
        # 3. Test validation
        print_step(3, "Kiểm tra validation file audio")
        test_results["validation"] = test_audio_file_validation()
        
        # 4. Test with sample audio
        print_step(4, "Kiểm tra STT với file audio mẫu")
        test_results["sample_audio"] = test_stt_with_sample_audio()
        
        # 5. Test performance (if sample audio available)
        if test_results["sample_audio"]:
            print_step(5, "Kiểm tra hiệu suất STT")
            test_results["performance"] = test_stt_performance()
        
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
        logger.success("🎉 Tất cả STT tests đều PASS!")
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} tests thất bại")
    
    print(f"\n📝 Ghi chú:")
    print(f"  - Logs được lưu trong thư mục logs/")
    print(f"  - Để test đầy đủ, hãy đặt file audio mẫu trong audio_samples/input/")
    print(f"  - Cấu hình API keys trong config.py để test các dịch vụ")

if __name__ == "__main__":
    main()
