"""
Test riêng cho Azure STT Module - Pipeline 4
Kiểm tra độc lập chức năng Speech-to-Text với metrics chi tiết
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stt_module import AzureSTTModule
from utils import MetricsCollector, Logger, print_header, print_step, AudioUtils, ResponseTimeTracker
from config import get_config_status, validate_config

def test_stt_configuration():
    """Test STT configuration"""
    print_header("KIỂM TRA CẤU HÌNH AZURE STT")
    
    # Check configuration
    status = get_config_status()
    errors = validate_config()
    
    print("📋 Trạng thái cấu hình:")
    print(f"  ✅ Azure Speech configured: {status['azure_configured']}")
    
    if errors:
        print("\n❌ Lỗi cấu hình:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ Cấu hình hoàn tất!")
    return True

def test_stt_service():
    """Test Azure STT service"""
    print_header("KIỂM TRA DỊCH VỤ AZURE STT")
    
    stt = AzureSTTModule()
    
    # Get service status
    status = stt.get_service_status()
    
    print("🔧 Trạng thái dịch vụ:")
    for service_name, service_info in status.items():
        configured = service_info.get('configured', False)
        available = service_info.get('available', False)
        print(f"  {service_name.upper()}:")
        print(f"    - Configured: {'✅' if configured else '❌'}")
        print(f"    - Available: {'✅' if available else '❌'}")
        print(f"    - Region: {service_info.get('region', 'N/A')}")
        print(f"    - Language: {service_info.get('language', 'N/A')}")
    
    return status

def test_azure_connection():
    """Test Azure Speech Service connection"""
    print_header("KIỂM TRA KẾT NỐI AZURE SPEECH")
    
    stt = AzureSTTModule()
    
    print("🔗 Testing Azure Speech connection...")
    conn_result = stt.test_connection()
    
    if conn_result["success"]:
        print(f"  ✅ {conn_result['message']}")
        print(f"  📍 Region: {conn_result['region']}")
        print(f"  🗣️ Language: {conn_result['language']}")
        return True
    else:
        print(f"  ❌ Connection failed: {conn_result['error']}")
        return False

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

def create_test_audio_samples():
    """Create test audio samples if they don't exist"""
    print_header("TẠO FILE AUDIO MẪU")
    
    sample_dir = Path("audio_samples/input")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if we have any audio files
    audio_files = []
    for ext in ['.wav', '.mp3', '.m4a', '.flac']:
        audio_files.extend(sample_dir.glob(f"*{ext}"))
    
    if audio_files:
        print(f"✅ Đã có {len(audio_files)} file audio mẫu")
        return True
    
    print("📝 Không tìm thấy file audio mẫu. Tạo file silence để test...")
    
    # Create silence audio for testing
    test_files = [
        ("test_short.wav", 2.0),   # 2 seconds
        ("test_medium.wav", 5.0),  # 5 seconds
        ("test_long.wav", 10.0)    # 10 seconds
    ]
    
    created_files = []
    for filename, duration in test_files:
        filepath = sample_dir / filename
        success, message = AudioUtils.create_silence_audio(str(filepath), duration)
        
        if success:
            print(f"  ✅ Created: {filepath} ({duration}s)")
            created_files.append(filepath)
        else:
            print(f"  ❌ Failed to create {filepath}: {message}")
    
    if created_files:
        print(f"\n📝 Tạo thành công {len(created_files)} file test")
        print("⚠️  Lưu ý: Đây là file silence, kết quả STT sẽ là empty/no match")
        print("💡 Để test đầy đủ, hãy đặt file audio có giọng nói thật vào audio_samples/input/")
        return True
    else:
        print("❌ Không thể tạo file test audio")
        return False

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
        print("⚠️  Không tìm thấy file audio mẫu")
        if create_test_audio_samples():
            # Refresh file list
            for ext in ['.wav', '.mp3', '.m4a', '.flac']:
                audio_files.extend(sample_dir.glob(f"*{ext}"))
        
        if not audio_files:
            return False
    
    print(f"🎵 Tìm thấy {len(audio_files)} file audio:")
    for audio_file in audio_files:
        print(f"  - {audio_file.name}")
    
    # Initialize STT module
    stt = AzureSTTModule()
    metrics_collector = MetricsCollector()
    time_tracker = ResponseTimeTracker()
    
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
        
        print(f"  📊 Duration: {audio_info.get('duration_seconds', 'N/A'):.1f}s")
        print(f"  📦 File size: {audio_info['file_size_mb']:.2f}MB")
        if 'sample_rate' in audio_info:
            print(f"  🔊 Sample rate: {audio_info['sample_rate']}Hz")
            print(f"  📻 Channels: {audio_info['channels']}")
        
        # Test STT
        print_step(2, "Thử STT với Azure Speech")
        
        metrics_collector.start_timer("stt_processing_time")
        
        result = stt.transcribe(str(audio_file))
        
        processing_time = metrics_collector.end_timer("stt_processing_time")
        time_tracker.add_time("stt", processing_time)
        
        if result['success']:
            print(f"  ✅ Azure STT Success!")
            print(f"  ⏱️  Processing time: {result['processing_time']:.3f}s")
            print(f"  📝 Transcription: '{result['text']}'")
            print(f"  📊 Text length: {len(result['text'])} characters")
            print(f"  🎯 Confidence: {result.get('confidence', 'N/A')}")
            print(f"  🗣️ Language: {result.get('language', 'N/A')}")
            
            # Add to metrics
            metrics_collector.add_metric("azure_stt_success", True)
            metrics_collector.add_metric("azure_stt_processing_time", result['processing_time'])
            metrics_collector.add_metric("azure_stt_text_length", len(result['text']))
            metrics_collector.add_metric("azure_stt_confidence", result.get('confidence', 0))
            
            # Test continuous recognition if file is long enough
            if audio_info.get('duration_seconds', 0) > 5:
                print_step(3, "Thử Continuous Recognition")
                
                continuous_result = stt.transcribe(str(audio_file), use_continuous=True)
                
                if continuous_result['success']:
                    print(f"  ✅ Continuous Success!")
                    print(f"  ⏱️  Processing time: {continuous_result['processing_time']:.3f}s")
                    print(f"  📝 Text: '{continuous_result['text']}'")
                    print(f"  📊 Segments: {len(continuous_result.get('segments', []))}")
                else:
                    print(f"  ❌ Continuous Failed: {continuous_result['error']}")
            
        else:
            print(f"  ❌ Azure STT Failed: {result['error']}")
            metrics_collector.add_metric("azure_stt_success", False)
            metrics_collector.add_metric("azure_stt_error", result['error'])
        
        print()
    
    # Display overall metrics
    print_header("TỔNG KẾT METRICS STT")
    metrics_collector.display_metrics("Azure STT Test Results")
    
    # Display response time statistics
    time_tracker.display_all_stats()
    
    return True

def test_stt_performance():
    """Test STT performance with different scenarios"""
    print_header("KIỂM TRA HIỆU SUẤT STT")
    
    sample_dir = Path("audio_samples/input")
    audio_files = list(sample_dir.glob("*.wav")) + list(sample_dir.glob("*.mp3"))
    
    if not audio_files:
        print("⚠️  Cần file audio để test performance")
        return False
    
    stt = AzureSTTModule()
    performance_metrics = MetricsCollector()
    
    print(f"🔬 Testing với {len(audio_files)} files...")
    
    performance_metrics.start_timer("total_performance_test")
    
    successful_transcriptions = 0
    total_audio_duration = 0
    total_processing_time = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n🎵 Processing file {i}/{len(audio_files)}: {audio_file.name}")
        
        # Get audio duration
        audio_info = AudioUtils.get_audio_info(str(audio_file))
        
        if 'error' not in audio_info:
            duration = audio_info.get('duration_seconds', 0)
            total_audio_duration += duration
            
            # Transcribe
            result = stt.transcribe(str(audio_file))
            
            if result['success']:
                successful_transcriptions += 1
                total_processing_time += result['processing_time']
                
                # Calculate real-time factor
                if duration > 0:
                    rtf = result['processing_time'] / duration
                    print(f"  ✅ Success - RTF: {rtf:.2f}x (faster is better)")
                else:
                    print(f"  ✅ Success - Time: {result['processing_time']:.3f}s")
            else:
                print(f"  ❌ Failed: {result['error']}")
        else:
            print(f"  ⚠️  Cannot analyze audio: {audio_info['error']}")
    
    total_test_time = performance_metrics.end_timer("total_performance_test")
    
    # Calculate performance metrics
    success_rate = successful_transcriptions / len(audio_files) if audio_files else 0
    avg_processing_time = total_processing_time / successful_transcriptions if successful_transcriptions > 0 else 0
    overall_rtf = total_processing_time / total_audio_duration if total_audio_duration > 0 else 0
    
    performance_metrics.add_metric("success_rate", success_rate)
    performance_metrics.add_metric("avg_processing_time", avg_processing_time)
    performance_metrics.add_metric("overall_real_time_factor", overall_rtf)
    performance_metrics.add_metric("total_audio_duration", total_audio_duration)
    performance_metrics.add_metric("total_processing_time", total_processing_time)
    
    print(f"\n📊 Performance Summary:")
    print(f"  ✅ Success rate: {success_rate:.1%}")
    print(f"  ⏱️  Average processing time: {avg_processing_time:.3f}s")
    print(f"  🚀 Overall real-time factor: {overall_rtf:.2f}x")
    print(f"  📊 Total audio duration: {total_audio_duration:.1f}s")
    print(f"  ⏱️  Total processing time: {total_processing_time:.1f}s")
    
    # Display detailed metrics
    performance_metrics.display_metrics("STT Performance Metrics")
    
    return True

def main():
    """Main test function"""
    print_header("AZURE STT MODULE TEST SUITE - PIPELINE 4", 80)
    
    logger = Logger("azure_stt_test")
    overall_metrics = MetricsCollector()
    
    overall_metrics.start_timer("total_test_time")
    
    # Test steps
    test_results = {
        "configuration": False,
        "service": False,
        "connection": False,
        "validation": False,
        "sample_audio": False,
        "performance": False
    }
    
    try:
        # 1. Test configuration
        print_step(1, "Kiểm tra cấu hình Azure STT")
        test_results["configuration"] = test_stt_configuration()
        
        if not test_results["configuration"]:
            logger.error("Cấu hình Azure STT không hợp lệ. Dừng test.")
            return
        
        # 2. Test service
        print_step(2, "Kiểm tra trạng thái dịch vụ")
        status = test_stt_service()
        test_results["service"] = any(s.get('available', False) for s in status.values() if isinstance(s, dict))
        
        # 3. Test connection
        print_step(3, "Kiểm tra kết nối Azure Speech")
        test_results["connection"] = test_azure_connection()
        
        if not test_results["connection"]:
            logger.error("Không thể kết nối Azure Speech Service. Dừng test.")
            return
        
        # 4. Test validation
        print_step(4, "Kiểm tra validation file audio")
        test_results["validation"] = test_audio_file_validation()
        
        # 5. Test with sample audio
        print_step(5, "Kiểm tra STT với file audio mẫu")
        test_results["sample_audio"] = test_stt_with_sample_audio()
        
        # 6. Test performance (if sample audio available)
        if test_results["sample_audio"]:
            print_step(6, "Kiểm tra hiệu suất STT")
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
        logger.success("🎉 Tất cả Azure STT tests đều PASS!")
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} tests thất bại")
    
    print(f"\n📝 Ghi chú:")
    print(f"  - Logs được lưu trong thư mục logs/")
    print(f"  - Để test đầy đủ, hãy đặt file audio có giọng nói thật vào audio_samples/input/")
    print(f"  - Cấu hình Azure Speech API key trong config.py")
    print(f"  - File silence chỉ để test kết nối, không có nội dung transcribe")

if __name__ == "__main__":
    main()
