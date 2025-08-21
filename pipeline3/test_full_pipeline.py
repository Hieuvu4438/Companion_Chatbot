"""
Test Full Pipeline - Pipeline 3
Kiểm tra toàn bộ pipeline STT -> LLM -> TTS với metrics chi tiết
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline_full import FullPipeline
from utils import MetricsCollector, Logger, print_header, print_step, save_metrics_to_file, AudioUtils
from config import get_config_status, validate_config

def test_pipeline_configuration():
    """Test pipeline configuration"""
    print_header("KIỂM TRA CẤU HÌNH PIPELINE")
    
    # Check configuration
    status = get_config_status()
    errors = validate_config()
    
    print("📋 Trạng thái cấu hình tổng thể:")
    print(f"  ✅ FPT.AI configured: {status['fpt_configured']}")
    print(f"  ✅ OpenAI configured: {status['openai_configured']}")
    print(f"  ✅ Gemini configured: {status['gemini_configured']}")
    print(f"  ✅ Google Cloud configured: {status['google_cloud_configured']}")
    print(f"  🚀 Overall ready: {status['ready']}")
    
    if errors:
        print("\n❌ Lỗi cấu hình:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ Cấu hình hoàn tất!")
    return True

def test_pipeline_components():
    """Test individual pipeline components"""
    print_header("KIỂM TRA CÁC THÀNH PHẦN PIPELINE")
    
    pipeline = FullPipeline()
    status = pipeline.get_pipeline_status()
    
    print("🔧 Trạng thái thành phần:")
    
    # STT status
    print("\n🎤 STT Services:")
    stt_available = False
    for service_name, service_info in status["stt"].items():
        if isinstance(service_info, dict):
            available = service_info.get('available', False)
            if available:
                stt_available = True
            print(f"  {service_name}: {'✅' if available else '❌'}")
    
    # LLM status
    print("\n🧠 LLM Service:")
    llm_available = status["llm"].get('available', False)
    print(f"  Gemini: {'✅' if llm_available else '❌'}")
    
    # TTS status
    print("\n🔊 TTS Services:")
    tts_available = False
    for service_name, service_info in status["tts"].items():
        if isinstance(service_info, dict):
            available = service_info.get('available', False)
            if available:
                tts_available = True
            print(f"  {service_name}: {'✅' if available else '❌'}")
    
    overall_ready = stt_available and llm_available and tts_available
    print(f"\n🚀 Pipeline Ready: {'✅' if overall_ready else '❌'}")
    
    return overall_ready, status

def test_text_only_pipeline():
    """Test text-only pipeline (LLM + TTS)"""
    print_header("KIỂM TRA TEXT-ONLY PIPELINE")
    
    pipeline = FullPipeline()
    
    # Test cases for text-only pipeline
    test_cases = [
        {
            "name": "Câu hỏi đơn giản",
            "text": "Xin chào, bạn có khỏe không?",
            "expected_success": True
        },
        {
            "name": "Câu hỏi về sức khỏe",
            "text": "Tôi bị đau đầu, nên làm gì?",
            "expected_success": True
        },
        {
            "name": "Câu hỏi phức tạp",
            "text": "Bạn có thể giải thích về tác hại của việc thức khuya đối với người cao tuổi không?",
            "expected_success": True
        }
    ]
    
    metrics_collector = MetricsCollector()
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TEST {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'='*60}")
        
        print_step(1, "Chuẩn bị input")
        print(f"  📝 Input text: {test_case['text']}")
        print(f"  📊 Text length: {len(test_case['text'])} characters")
        
        print_step(2, "Chạy text-only pipeline")
        
        metrics_collector.start_timer(f"test_{i}_time")
        
        result = pipeline.process_text_input(
            test_case['text'],
            system_prompt_type="elder_assistant"
        )
        
        test_time = metrics_collector.end_timer(f"test_{i}_time")
        
        if result['success']:
            print(f"  ✅ Pipeline Success!")
            print(f"  🤖 Response: {result['response_text'][:100]}{'...' if len(result['response_text']) > 100 else ''}")
            print(f"  🔊 Audio output: {result['output_audio']}")
            print(f"  ⏱️  Total time: {result['metrics']['total_pipeline_time']:.3f}s")
            print(f"    - LLM time: {result['metrics']['llm_time']:.3f}s")
            print(f"    - TTS time: {result['metrics']['tts_time']:.3f}s")
            
            # Verify output file exists
            if os.path.exists(result['output_audio']):
                file_size = os.path.getsize(result['output_audio'])
                print(f"  📦 Output file size: {file_size} bytes")
            
            successful_tests += 1
            
            # Add to metrics
            metrics_collector.add_metric(f"test_{i}_success", True)
            metrics_collector.add_metric(f"test_{i}_llm_time", result['metrics']['llm_time'])
            metrics_collector.add_metric(f"test_{i}_tts_time", result['metrics']['tts_time'])
            metrics_collector.add_metric(f"test_{i}_total_time", result['metrics']['total_pipeline_time'])
            
        else:
            print(f"  ❌ Pipeline Failed!")
            for error in result['errors']:
                print(f"    - {error}")
            
            metrics_collector.add_metric(f"test_{i}_success", False)
            metrics_collector.add_metric(f"test_{i}_errors", result['errors'])
        
        print()
    
    # Summary
    print_header("KẾT QUẢ TEXT-ONLY PIPELINE")
    print(f"📊 Tổng kết: {successful_tests}/{len(test_cases)} tests thành công")
    
    metrics_collector.add_metric("total_text_tests", len(test_cases))
    metrics_collector.add_metric("successful_text_tests", successful_tests)
    metrics_collector.add_metric("text_success_rate", successful_tests / len(test_cases))
    
    metrics_collector.display_metrics("Text-Only Pipeline Results")
    
    return successful_tests == len(test_cases)

def test_full_audio_pipeline():
    """Test full audio pipeline (STT + LLM + TTS)"""
    print_header("KIỂM TRA FULL AUDIO PIPELINE")
    
    # Look for sample audio files
    sample_dir = Path("audio_samples/input")
    audio_files = []
    
    # Find audio files
    for ext in ['.wav', '.mp3', '.m4a', '.flac']:
        audio_files.extend(sample_dir.glob(f"*{ext}"))
    
    if not audio_files:
        print("⚠️  Không tìm thấy file audio mẫu trong audio_samples/input/")
        print("📝 Hướng dẫn:")
        print("  1. Tạo file audio ngắn (5-30 giây) có nội dung tiếng Việt")
        print("  2. Đặt vào thư mục audio_samples/input/")
        print("  3. Chạy lại test này")
        return False
    
    print(f"🎵 Tìm thấy {len(audio_files)} file audio:")
    for audio_file in audio_files:
        print(f"  - {audio_file.name}")
    
    pipeline = FullPipeline()
    metrics_collector = MetricsCollector()
    successful_tests = 0
    
    # Test with each audio file
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n{'='*70}")
        print(f"🎤 FULL PIPELINE TEST {i}/{len(audio_files)}: {audio_file.name}")
        print(f"{'='*70}")
        
        # Get audio info
        print_step(1, "Phân tích file audio")
        audio_info = AudioUtils.get_audio_info(str(audio_file))
        
        if 'error' in audio_info:
            print(f"❌ Không thể phân tích audio: {audio_info['error']}")
            continue
        
        print(f"  📊 Duration: {audio_info['duration_seconds']:.1f}s")
        print(f"  📦 File size: {audio_info['file_size_mb']:.2f}MB")
        print(f"  🔊 Sample rate: {audio_info['sample_rate']}Hz")
        
        print_step(2, "Chạy full pipeline (STT -> LLM -> TTS)")
        
        metrics_collector.start_timer(f"full_test_{i}_time")
        
        # Run full pipeline
        result = pipeline.process_audio_input(
            str(audio_file),
            system_prompt_type="elder_assistant",
            conversation_context=True
        )
        
        full_test_time = metrics_collector.end_timer(f"full_test_{i}_time")
        
        if result['success']:
            print(f"  ✅ Full Pipeline Success!")
            print(f"  🎤 STT Result: {result['transcribed_text']}")
            print(f"  🤖 LLM Response: {result['response_text'][:150]}{'...' if len(result['response_text']) > 150 else ''}")
            print(f"  🔊 TTS Output: {result['output_audio']}")
            
            # Timing breakdown
            stt_time = result['metrics']['stt_time']
            llm_time = result['metrics']['llm_time']
            tts_time = result['metrics']['tts_time']
            total_time = result['metrics']['total_pipeline_time']
            
            print(f"  ⏱️  Timing breakdown:")
            print(f"    - STT: {stt_time:.3f}s ({stt_time/total_time*100:.1f}%)")
            print(f"    - LLM: {llm_time:.3f}s ({llm_time/total_time*100:.1f}%)")
            print(f"    - TTS: {tts_time:.3f}s ({tts_time/total_time*100:.1f}%)")
            print(f"    - Total: {total_time:.3f}s")
            
            # Service information
            services_used = result['metrics'].get('services_used', {})
            print(f"  🔧 Services used:")
            print(f"    - STT: {services_used.get('stt_service', 'unknown')}")
            print(f"    - LLM: {services_used.get('llm_service', 'unknown')}")
            print(f"    - TTS: {services_used.get('tts_service', 'unknown')}")
            
            # Verify output file
            if os.path.exists(result['output_audio']):
                output_size = os.path.getsize(result['output_audio'])
                print(f"  📦 Output audio size: {output_size} bytes")
            
            successful_tests += 1
            
            # Add to metrics
            metrics_collector.add_metric(f"full_test_{i}_success", True)
            metrics_collector.add_metric(f"full_test_{i}_stt_time", stt_time)
            metrics_collector.add_metric(f"full_test_{i}_llm_time", llm_time)
            metrics_collector.add_metric(f"full_test_{i}_tts_time", tts_time)
            metrics_collector.add_metric(f"full_test_{i}_total_time", total_time)
            metrics_collector.add_metric(f"full_test_{i}_input_duration", audio_info['duration_seconds'])
            
            # Real-time factor for audio processing
            if audio_info['duration_seconds'] > 0:
                rtf = total_time / audio_info['duration_seconds']
                metrics_collector.add_metric(f"full_test_{i}_real_time_factor", rtf)
                print(f"  🚀 Real-time factor: {rtf:.2f}x")
            
        else:
            print(f"  ❌ Full Pipeline Failed!")
            for error in result['errors']:
                print(f"    - {error}")
            
            metrics_collector.add_metric(f"full_test_{i}_success", False)
            metrics_collector.add_metric(f"full_test_{i}_errors", result['errors'])
        
        print()
    
    # Summary
    print_header("KẾT QUẢ FULL AUDIO PIPELINE")
    print(f"📊 Tổng kết: {successful_tests}/{len(audio_files)} tests thành công")
    
    if successful_tests > 0:
        # Calculate average metrics
        total_stt_time = sum(metrics_collector.metrics.get(f"full_test_{i}_stt_time", 0) for i in range(1, successful_tests + 1))
        total_llm_time = sum(metrics_collector.metrics.get(f"full_test_{i}_llm_time", 0) for i in range(1, successful_tests + 1))
        total_tts_time = sum(metrics_collector.metrics.get(f"full_test_{i}_tts_time", 0) for i in range(1, successful_tests + 1))
        
        avg_stt_time = total_stt_time / successful_tests
        avg_llm_time = total_llm_time / successful_tests
        avg_tts_time = total_tts_time / successful_tests
        
        metrics_collector.add_metric("avg_stt_time", avg_stt_time)
        metrics_collector.add_metric("avg_llm_time", avg_llm_time)
        metrics_collector.add_metric("avg_tts_time", avg_tts_time)
        
        print(f"⏱️  Thời gian trung bình:")
        print(f"  - STT: {avg_stt_time:.3f}s")
        print(f"  - LLM: {avg_llm_time:.3f}s")
        print(f"  - TTS: {avg_tts_time:.3f}s")
    
    metrics_collector.add_metric("total_audio_tests", len(audio_files))
    metrics_collector.add_metric("successful_audio_tests", successful_tests)
    metrics_collector.add_metric("audio_success_rate", successful_tests / len(audio_files) if audio_files else 0)
    
    metrics_collector.display_metrics("Full Audio Pipeline Results")
    
    return successful_tests == len(audio_files)

def test_conversation_context():
    """Test conversation context functionality"""
    print_header("KIỂM TRA CONVERSATION CONTEXT")
    
    pipeline = FullPipeline()
    
    # Test conversation sequence
    conversation_sequence = [
        "Tôi tên là Nam",
        "Tôi bao nhiêu tuổi?",  # Should ask for age since we don't know
        "Tôi 65 tuổi",
        "Tôi tên gì?"  # Should remember the name
    ]
    
    print("🗣️  Test conversation sequence:")
    for i, text in enumerate(conversation_sequence, 1):
        print(f"  {i}. {text}")
    
    print("\n" + "="*60)
    
    successful_conversations = 0
    
    for i, text in enumerate(conversation_sequence, 1):
        print(f"\n💬 Conversation Step {i}: {text}")
        
        result = pipeline.process_text_input(text, system_prompt_type="elder_assistant")
        
        if result['success']:
            print(f"  🤖 Response: {result['response_text']}")
            successful_conversations += 1
        else:
            print(f"  ❌ Failed: {', '.join(result['errors'])}")
    
    # Check conversation history
    history = pipeline.get_conversation_history()
    print(f"\n📜 Conversation history length: {len(history)}")
    
    if history:
        print("📋 History entries:")
        for i, entry in enumerate(history, 1):
            print(f"  {i}. User: {entry['user'][:50]}{'...' if len(entry['user']) > 50 else ''}")
            print(f"     Assistant: {entry['assistant'][:50]}{'...' if len(entry['assistant']) > 50 else ''}")
    
    # Clear history test
    pipeline.clear_conversation_history()
    history_after_clear = pipeline.get_conversation_history()
    
    print(f"\n🧹 After clearing history: {len(history_after_clear)} entries")
    
    success_rate = successful_conversations / len(conversation_sequence)
    print(f"\n📊 Conversation success rate: {success_rate*100:.1f}%")
    
    return success_rate >= 0.75  # At least 75% success

def test_performance_benchmarks():
    """Test performance benchmarks"""
    print_header("KIỂM TRA PERFORMANCE BENCHMARKS")
    
    pipeline = FullPipeline()
    
    # Performance test scenarios
    scenarios = [
        {
            "name": "Quick Response Test",
            "text": "Xin chào",
            "max_time": 10.0  # seconds
        },
        {
            "name": "Medium Text Test", 
            "text": "Bạn có thể cho tôi lời khuyên về việc tập thể dục cho người cao tuổi không?",
            "max_time": 15.0
        },
        {
            "name": "Complex Question Test",
            "text": "Tôi muốn biết về các phương pháp phòng ngừa bệnh tim mạch ở người trên 60 tuổi, bao gồm chế độ ăn uống và lối sống.",
            "max_time": 20.0
        }
    ]
    
    performance_results = []
    
    for scenario in scenarios:
        print(f"\n🏃 Testing: {scenario['name']}")
        print(f"  📝 Text: {scenario['text']}")
        print(f"  ⏱️  Max time: {scenario['max_time']}s")
        
        start_time = time.time()
        result = pipeline.process_text_input(scenario['text'])
        actual_time = time.time() - start_time
        
        passed = result['success'] and actual_time <= scenario['max_time']
        
        performance_results.append({
            "name": scenario['name'],
            "success": result['success'],
            "time": actual_time,
            "max_time": scenario['max_time'],
            "passed": passed
        })
        
        if passed:
            print(f"  ✅ PASS: {actual_time:.3f}s (under {scenario['max_time']}s)")
        else:
            if not result['success']:
                print(f"  ❌ FAIL: Pipeline failed")
            else:
                print(f"  ❌ FAIL: {actual_time:.3f}s (over {scenario['max_time']}s)")
    
    # Summary
    passed_tests = sum(1 for r in performance_results if r['passed'])
    print(f"\n📊 Performance summary: {passed_tests}/{len(scenarios)} tests passed")
    
    for result in performance_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {result['name']}: {status} ({result['time']:.3f}s)")
    
    return passed_tests == len(scenarios)

def main():
    """Main test function"""
    print_header("FULL PIPELINE TEST SUITE - PIPELINE 3", 80)
    
    logger = Logger("full_pipeline_test")
    overall_metrics = MetricsCollector()
    
    overall_metrics.start_timer("total_test_time")
    
    # Test results tracking
    test_results = {
        "configuration": False,
        "components": False,
        "text_pipeline": False,
        "audio_pipeline": False,
        "conversation_context": False,
        "performance": False
    }
    
    try:
        # 1. Test configuration
        print_step(1, "Kiểm tra cấu hình pipeline")
        test_results["configuration"] = test_pipeline_configuration()
        
        if not test_results["configuration"]:
            logger.error("Cấu hình pipeline không hợp lệ. Dừng test.")
            return
        
        # 2. Test components
        print_step(2, "Kiểm tra thành phần pipeline")
        components_ready, status = test_pipeline_components()
        test_results["components"] = components_ready
        
        if not components_ready:
            logger.error("Các thành phần pipeline chưa sẵn sàng. Dừng test.")
            return
        
        # 3. Test text-only pipeline
        print_step(3, "Kiểm tra text-only pipeline")
        test_results["text_pipeline"] = test_text_only_pipeline()
        
        # 4. Test full audio pipeline (if text pipeline works)
        if test_results["text_pipeline"]:
            print_step(4, "Kiểm tra full audio pipeline")
            test_results["audio_pipeline"] = test_full_audio_pipeline()
        
        # 5. Test conversation context
        print_step(5, "Kiểm tra conversation context")
        test_results["conversation_context"] = test_conversation_context()
        
        # 6. Test performance benchmarks
        print_step(6, "Kiểm tra performance benchmarks")
        test_results["performance"] = test_performance_benchmarks()
        
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
    
    # Overall assessment
    if passed_tests == total_tests:
        logger.success("🎉 Tất cả FULL PIPELINE tests đều PASS!")
        print("\n🚀 Pipeline sẵn sàng để production!")
    elif passed_tests >= total_tests * 0.8:
        logger.warning(f"⚠️  Pipeline hoạt động tốt nhưng cần cải thiện một số thành phần")
    else:
        logger.error(f"❌ Pipeline cần sửa chữa trước khi sử dụng")
    
    # Save overall metrics
    final_metrics = {
        "test_results": test_results,
        "total_test_time": total_test_time,
        "success_rate": passed_tests / total_tests,
        "timestamp": time.time()
    }
    
    save_metrics_to_file(final_metrics, "full_pipeline_test_metrics.json")
    
    print(f"\n📝 Ghi chú:")
    print(f"  - Logs được lưu trong thư mục logs/")
    print(f"  - Metrics được lưu trong full_pipeline_test_metrics.json")
    print(f"  - Audio output được lưu trong audio_samples/output/")
    print(f"  - Để test đầy đủ, hãy đặt file audio mẫu trong audio_samples/input/")

if __name__ == "__main__":
    main()
