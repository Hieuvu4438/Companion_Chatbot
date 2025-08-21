"""
Test hoàn chỉnh Pipeline 4 - Elder Care Voice Assistant
Kiểm tra toàn bộ pipeline STT + LLM + TTS với metrics và demo
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from full_pipeline import ElderCarePipeline
from utils import (
    MetricsCollector, Logger, print_header, print_step, print_success, 
    print_error, print_warning, print_info, AudioUtils, get_timestamp
)
from config import get_config_status, validate_config

def test_pipeline_configuration():
    """Test pipeline configuration"""
    print_header("KIỂM TRA CẤU HÌNH PIPELINE")
    
    # Check configuration
    status = get_config_status()
    errors = validate_config()
    
    print("📋 Trạng thái cấu hình:")
    print(f"  ✅ Azure Speech configured: {status['azure_configured']}")
    print(f"  ✅ Gemini configured: {status['gemini_configured']}")
    print(f"  ✅ VBEE configured: {status['vbee_configured']}")
    
    if errors:
        print("\n❌ Lỗi cấu hình:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ Tất cả cấu hình đều sẵn sàng!")
    return True

def test_pipeline_initialization():
    """Test pipeline initialization"""
    print_header("KIỂM TRA KHỞI TẠO PIPELINE")
    
    print("🚀 Khởi tạo Elder Care Pipeline...")
    pipeline = ElderCarePipeline()
    
    if pipeline.is_initialized:
        print_success("Pipeline khởi tạo thành công!")
        
        # Get status details
        status = pipeline.get_pipeline_status()
        print(f"\n📊 Chi tiết pipeline:")
        print(f"  🕐 Session start: {time.strftime('%H:%M:%S', time.localtime(status['session_start_time']))}")
        print(f"  💬 Conversations: {status['conversation_count']}")
        
        # Show module status
        print(f"\n🔧 Trạng thái modules:")
        for module_name, module_info in status['modules'].items():
            for service_name, service_details in module_info.items():
                available = service_details.get('available', False)
                configured = service_details.get('configured', False)
                print(f"  {service_name}: {'✅' if available and configured else '❌'}")
        
        return pipeline
    else:
        print_error("Pipeline khởi tạo thất bại!")
        return None

def test_pipeline_connectivity(pipeline):
    """Test pipeline connectivity"""
    print_header("KIỂM TRA KẾT NỐI PIPELINE")
    
    connectivity = pipeline.test_pipeline_connectivity()
    
    success_count = sum(connectivity[key] for key in ["stt_connection", "llm_connection", "tts_connection"])
    total_count = 3
    
    print(f"\n📊 Kết quả connectivity: {success_count}/{total_count}")
    
    if connectivity["overall_status"]:
        print_success("✅ Tất cả services đều kết nối thành công!")
        return True
    else:
        print_warning("⚠️  Một số services có vấn đề kết nối")
        return False

def create_sample_audio():
    """Create sample audio for testing"""
    print_header("TẠO FILE AUDIO MẪU")
    
    sample_dir = Path("audio_samples/input")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if we have any real audio files
    real_audio_files = []
    for ext in ['.wav', '.mp3', '.m4a']:
        real_audio_files.extend(sample_dir.glob(f"*{ext}"))
    
    if real_audio_files:
        print_success(f"Tìm thấy {len(real_audio_files)} file audio thật")
        return list(real_audio_files)
    
    print_info("Không tìm thấy file audio thật, tạo file silence để test...")
    
    # Create test audio files
    test_files = [
        ("greeting.wav", 3.0),
        ("question.wav", 5.0),
        ("story.wav", 8.0)
    ]
    
    created_files = []
    for filename, duration in test_files:
        filepath = sample_dir / filename
        success, message = AudioUtils.create_silence_audio(str(filepath), duration)
        
        if success:
            print_success(f"Created: {filename} ({duration}s)")
            created_files.append(filepath)
        else:
            print_error(f"Failed to create {filename}: {message}")
    
    if created_files:
        print_warning("⚠️  Lưu ý: File silence chỉ để test kết nối, STT sẽ trả về empty")
        print_info("💡 Để test đầy đủ, hãy đặt file audio có giọng nói thật vào audio_samples/input/")
    
    return created_files

def test_text_conversations(pipeline):
    """Test pipeline with text input (LLM + TTS only)"""
    print_header("KIỂM TRA CUỘC HỘI THOẠI TEXT")
    
    # Elder care conversation samples
    test_conversations = [
        {
            "name": "Chào hỏi thân thiện",
            "text": "Xin chào! Hôm nay bác có khỏe không?",
            "expected_response_type": "greeting"
        },
        {
            "name": "Hỏi về sức khỏe",
            "text": "Bác cảm thấy mệt mỏi và đau đầu",
            "expected_response_type": "health_advice"
        },
        {
            "name": "Tâm sự buồn",
            "text": "Bác cảm thấy cô đơn và nhớ quê hương",
            "expected_response_type": "comfort"
        },
        {
            "name": "Hỏi về gia đình",
            "text": "Bác muốn gọi điện cho con cháu nhưng không biết làm sao",
            "expected_response_type": "guidance"
        }
    ]
    
    successful_conversations = 0
    total_time = 0
    
    for i, conversation in enumerate(test_conversations, 1):
        print(f"\n{'='*60}")
        print(f"💬 TEST {i}/{len(test_conversations)}: {conversation['name']}")
        print(f"{'='*60}")
        
        print_step(1, f"Xử lý text: '{conversation['text']}'")
        
        start_time = time.time()
        result = pipeline.process_text_conversation(conversation['text'])
        processing_time = time.time() - start_time
        
        total_time += processing_time
        
        if result["success"]:
            successful_conversations += 1
            
            print_success("Cuộc hội thoại thành công!")
            print(f"  👤 User: {result['user_text']}")
            print(f"  🤖 Assistant: {result['assistant_text']}")
            print(f"  🎵 Audio output: {Path(result['output_audio_path']).name}")
            print(f"  ⏱️  Pipeline time: {result['pipeline_time']:.3f}s")
            
            # Show step times if available
            if "step_times" in result:
                print(f"  📊 Step breakdown:")
                for step, step_time in result.get("step_times", {}).items():
                    print(f"    - {step.upper()}: {step_time:.3f}s")
            
            # Analyze response quality
            response_length = len(result['assistant_text'])
            if response_length > 200:
                print_warning("    Response khá dài, có thể cần rút gọn")
            elif response_length < 20:
                print_warning("    Response khá ngắn")
            else:
                print_info("    Response length phù hợp")
                
        else:
            print_error(f"Cuộc hội thoại thất bại: {result['error']}")
            
        print()
    
    # Summary
    success_rate = successful_conversations / len(test_conversations)
    avg_time = total_time / successful_conversations if successful_conversations > 0 else 0
    
    print(f"📊 Tổng kết Text Conversations:")
    print(f"  ✅ Success rate: {success_rate:.1%} ({successful_conversations}/{len(test_conversations)})")
    print(f"  ⏱️  Average time: {avg_time:.3f}s")
    print(f"  🕐 Total time: {total_time:.3f}s")
    
    return successful_conversations > 0

def test_voice_conversations(pipeline, audio_files):
    """Test pipeline with voice input (full STT + LLM + TTS)"""
    print_header("KIỂM TRA CUỘC HỘI THOẠI GIỌNG NÓI")
    
    if not audio_files:
        print_warning("Không có file audio để test")
        return False
    
    successful_conversations = 0
    total_time = 0
    
    for i, audio_file in enumerate(audio_files[:3], 1):  # Test max 3 files
        print(f"\n{'='*60}")
        print(f"🎤 TEST {i}/{min(3, len(audio_files))}: {audio_file.name}")
        print(f"{'='*60}")
        
        # Get audio info
        audio_info = AudioUtils.get_audio_info(str(audio_file))
        if 'error' in audio_info:
            print_error(f"Cannot analyze audio: {audio_info['error']}")
            continue
        
        print_step(1, "Thông tin audio")
        print(f"  📊 Duration: {audio_info.get('duration_seconds', 'N/A'):.1f}s")
        print(f"  📦 File size: {audio_info['file_size_mb']:.2f}MB")
        
        print_step(2, "Xử lý full voice pipeline")
        
        start_time = time.time()
        result = pipeline.process_voice_conversation(
            str(audio_file),
            use_continuous_stt=(audio_info.get('duration_seconds', 0) > 5)
        )
        processing_time = time.time() - start_time
        
        total_time += processing_time
        
        if result["success"]:
            successful_conversations += 1
            
            print_success("Voice conversation thành công!")
            print(f"  🎤 STT Result: '{result['user_text']}'")
            print(f"  🤖 LLM Response: '{result['assistant_text'][:100]}...'")
            print(f"  🎵 TTS Output: {Path(result['output_audio_path']).name}")
            print(f"  ⏱️  Total time: {result['pipeline_time']:.3f}s")
            
            # Show detailed step times
            step_times = result.get("step_times", {})
            print(f"  📊 Step breakdown:")
            for step, step_time in step_times.items():
                print(f"    - {step.upper()}: {step_time:.3f}s")
            
            # Calculate real-time factor
            audio_duration = audio_info.get('duration_seconds', 0)
            if audio_duration > 0:
                rtf = result['pipeline_time'] / audio_duration
                print(f"  🚀 Real-time factor: {rtf:.2f}x")
            
            # Save conversation log
            pipeline.save_conversation_log(result)
            
        else:
            print_error(f"Voice conversation thất bại: {result['error']}")
            
            # Show partial results
            if result.get("steps"):
                print_info("Partial results:")
                for step_name, step_result in result["steps"].items():
                    if step_result.get("success"):
                        print(f"  ✅ {step_name.upper()}: Success")
                    else:
                        print(f"  ❌ {step_name.upper()}: {step_result.get('error', 'Failed')}")
        
        print()
    
    # Summary
    success_rate = successful_conversations / min(3, len(audio_files))
    avg_time = total_time / successful_conversations if successful_conversations > 0 else 0
    
    print(f"📊 Tổng kết Voice Conversations:")
    print(f"  ✅ Success rate: {success_rate:.1%} ({successful_conversations}/{min(3, len(audio_files))})")
    print(f"  ⏱️  Average time: {avg_time:.3f}s")
    print(f"  🕐 Total time: {total_time:.3f}s")
    
    return successful_conversations > 0

def test_performance_metrics(pipeline):
    """Test and display performance metrics"""
    print_header("KIỂM TRA PERFORMANCE METRICS")
    
    # Get comprehensive metrics
    metrics = pipeline.get_comprehensive_metrics()
    
    print("📊 Pipeline Information:")
    pipeline_info = metrics["pipeline_info"]
    print(f"  🕐 Session duration: {pipeline_info['session_duration']:.1f}s")
    print(f"  💬 Total conversations: {pipeline_info['conversation_count']}")
    print(f"  ✅ Initialized: {pipeline_info['is_initialized']}")
    
    print("\n⏱️ Response Time Statistics:")
    response_times = metrics["response_times"]
    for component, stats in response_times.items():
        if stats["count"] > 0:
            print(f"  {component.upper()}:")
            print(f"    - Count: {stats['count']}")
            print(f"    - Average: {stats['avg']:.3f}s")
            print(f"    - Min: {stats['min']:.3f}s")
            print(f"    - Max: {stats['max']:.3f}s")
    
    # Performance alerts
    alerts = metrics["performance_alerts"]
    if alerts:
        print(f"\n⚠️ Performance Alerts ({len(alerts)}):")
        for alert in alerts[-5:]:  # Show last 5 alerts
            print(f"  - {alert['component']}: {alert['response_time']:.3f}s (threshold: {alert['threshold']}s)")
    else:
        print("\n✅ No performance alerts")
    
    # Module metrics summary
    print(f"\n🔧 Module Metrics Summary:")
    module_metrics = metrics["module_metrics"]
    for module, module_data in module_metrics.items():
        if "metrics" in module_data:
            module_stats = module_data["metrics"]
            print(f"  {module.upper()}: {len(module_stats)} metrics recorded")
    
    return metrics

def generate_test_report(pipeline, metrics, test_results):
    """Generate comprehensive test report"""
    print_header("TẠO BÁO CÁO TEST")
    
    report = {
        "test_info": {
            "timestamp": get_timestamp(),
            "pipeline_version": "Pipeline 4",
            "test_duration": time.time() - test_results.get("start_time", time.time())
        },
        "configuration": test_results.get("configuration", False),
        "connectivity": test_results.get("connectivity", False),
        "text_conversations": test_results.get("text_conversations", False),
        "voice_conversations": test_results.get("voice_conversations", False),
        "metrics": metrics,
        "overall_success": False
    }
    
    # Calculate overall success
    critical_tests = [
        report["configuration"],
        report["connectivity"],
        report["text_conversations"]
    ]
    
    report["overall_success"] = all(critical_tests)
    
    # Save report
    report_file = f"logs/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        os.makedirs("logs", exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print_success(f"Test report saved: {report_file}")
    except Exception as e:
        print_error(f"Cannot save test report: {e}")
    
    return report

def main():
    """Main test function"""
    print_header("PIPELINE 4 - ELDER CARE VOICE ASSISTANT", 80)
    print_header("COMPREHENSIVE TEST SUITE", 80)
    
    logger = Logger("pipeline_test")
    start_time = time.time()
    
    # Test results tracking
    test_results = {
        "start_time": start_time,
        "configuration": False,
        "initialization": False,
        "connectivity": False,
        "text_conversations": False,
        "voice_conversations": False
    }
    
    pipeline = None
    metrics = None
    
    try:
        # 1. Test configuration
        print_step(1, "Kiểm tra cấu hình pipeline")
        test_results["configuration"] = test_pipeline_configuration()
        
        if not test_results["configuration"]:
            logger.error("Configuration test failed. Stopping tests.")
            return
        
        # 2. Test initialization
        print_step(2, "Khởi tạo pipeline")
        pipeline = test_pipeline_initialization()
        test_results["initialization"] = pipeline is not None
        
        if not test_results["initialization"]:
            logger.error("Initialization failed. Stopping tests.")
            return
        
        # 3. Test connectivity
        print_step(3, "Kiểm tra kết nối")
        test_results["connectivity"] = test_pipeline_connectivity(pipeline)
        
        if not test_results["connectivity"]:
            logger.warning("Connectivity issues detected. Some tests may fail.")
        
        # 4. Create/find audio samples
        print_step(4, "Chuẩn bị file audio mẫu")
        audio_files = create_sample_audio()
        
        # 5. Test text conversations
        print_step(5, "Test cuộc hội thoại text")
        test_results["text_conversations"] = test_text_conversations(pipeline)
        
        # 6. Test voice conversations (if audio available)
        print_step(6, "Test cuộc hội thoại giọng nói")
        test_results["voice_conversations"] = test_voice_conversations(pipeline, audio_files)
        
        # 7. Performance metrics
        print_step(7, "Thu thập performance metrics")
        metrics = test_performance_metrics(pipeline)
        
        # 8. Generate report
        print_step(8, "Tạo báo cáo test")
        report = generate_test_report(pipeline, metrics, test_results)
        
    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    
    finally:
        # Cleanup
        if pipeline:
            pipeline.shutdown()
    
    # Final results
    total_test_time = time.time() - start_time
    
    print_header("KẾT QUẢ CUỐI CÙNG", 80)
    
    passed_tests = sum(test_results.values()) - 1  # Exclude start_time
    total_tests = len(test_results) - 1
    
    print(f"📊 Tổng quan test:")
    print(f"  ✅ Passed: {passed_tests}/{total_tests}")
    print(f"  ⏱️  Total time: {total_test_time:.3f}s")
    print()
    
    print("📋 Chi tiết kết quả:")
    for test_name, result in test_results.items():
        if test_name != "start_time":
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        logger.success("🎉 Tất cả tests đều PASS! Pipeline sẵn sàng sử dụng!")
    elif passed_tests >= total_tests - 1:
        logger.success("🎉 Hầu hết tests đều PASS! Pipeline có thể sử dụng!")
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} tests thất bại. Cần kiểm tra lại.")
    
    print(f"\n📝 Hướng dẫn sử dụng:")
    print(f"  1. Đảm bảo tất cả API keys đã được cấu hình trong config.py")
    print(f"  2. Đặt file audio có giọng nói thật vào audio_samples/input/ để test đầy đủ")
    print(f"  3. Check logs/ folder để xem chi tiết logs và reports")
    print(f"  4. Audio output được lưu trong audio_samples/output/")
    print(f"  5. Sử dụng full_pipeline.py để tích hợp vào ứng dụng")

if __name__ == "__main__":
    main()
