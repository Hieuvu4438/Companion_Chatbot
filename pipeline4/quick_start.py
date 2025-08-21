"""
Quick Start Guide - Pipeline 4: Elder Care Voice Assistant
Hướng dẫn nhanh để bắt đầu với chatbot cho người cao tuổi
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import print_header, print_step, print_success, print_error, print_warning, print_info
from config import get_config_status, validate_config

def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("KIỂM TRA DEPENDENCIES")
    
    required_packages = [
        ("azure.cognitiveservices.speech", "Azure Speech SDK"),
        ("google.generativeai", "Google Generative AI"),
        ("requests", "HTTP Requests Library"),
        ("python-dotenv", "Environment Variables (optional)"),
        ("json", "JSON (built-in)"),
        ("wave", "Audio Processing (built-in)"),
        ("pathlib", "Path utilities (built-in)")
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            if "." in package:
                # Handle nested imports
                main_package = package.split(".")[0]
                __import__(main_package)
            else:
                __import__(package)
            print_success(f"✅ {description}")
        except ImportError:
            missing_packages.append((package, description))
            print_error(f"❌ {description} - Not installed")
    
    if missing_packages:
        print_warning(f"\n⚠️  {len(missing_packages)} packages cần cài đặt:")
        print("Chạy lệnh sau để cài đặt:")
        print("pip install azure-cognitiveservices-speech google-generativeai requests python-dotenv")
        return False
    else:
        print_success("\n🎉 Tất cả dependencies đã được cài đặt!")
        return True

def check_directory_structure():
    """Check if required directories exist and create them"""
    print_header("KIỂM TRA CẤU TRÚC THU MỤC")
    
    required_dirs = [
        "audio_samples",
        "audio_samples/input",
        "audio_samples/output", 
        "logs"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print_success(f"✅ {dir_path}")
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                print_success(f"✅ {dir_path} (đã tạo)")
            except Exception as e:
                print_error(f"❌ Không thể tạo {dir_path}: {e}")
                return False
    
    print_success("\n🎉 Cấu trúc thư mục OK!")
    return True

def check_configuration():
    """Check API configuration"""
    print_header("KIỂM TRA CẤU HÌNH API")
    
    status = get_config_status()
    errors = validate_config()
    
    print("📋 Trạng thái API Keys:")
    print(f"  🔑 Azure Speech: {'✅ Configured' if status['azure_configured'] else '❌ Missing'}")
    print(f"  🔑 Gemini API: {'✅ Configured' if status['gemini_configured'] else '❌ Missing'}")
    print(f"  🔑 VBEE API: {'✅ Configured' if status['vbee_configured'] else '❌ Missing'}")
    
    if errors:
        print_warning("\n⚠️  Lỗi cấu hình:")
        for error in errors:
            print(f"  - {error}")
        
        print_info("\n💡 Hướng dẫn cấu hình:")
        print("1. Mở file config.py")
        print("2. Điền các API keys:")
        print("   - AZURE_SPEECH_KEY: Azure Cognitive Services key")
        print("   - AZURE_SPEECH_REGION: Azure region (vd: eastus)")
        print("   - GEMINI_API_KEY: Google Gemini API key")
        print("   - VBEE_API_KEY: VBEE API key")
        print("3. Hoặc tạo file .env với các biến trên")
        return False
    else:
        print_success("\n🎉 Tất cả API keys đã được cấu hình!")
        return True

def test_basic_functionality():
    """Test basic pipeline functionality"""
    print_header("KIỂM TRA CHỨC NĂNG CƠ BẢN")
    
    try:
        from full_pipeline import ElderCarePipeline
        
        print_step(1, "Khởi tạo pipeline")
        pipeline = ElderCarePipeline()
        
        if not pipeline.is_initialized:
            print_error("Pipeline khởi tạo thất bại")
            return False
        
        print_success("Pipeline khởi tạo thành công")
        
        print_step(2, "Test connectivity") 
        connectivity = pipeline.test_pipeline_connectivity()
        
        if connectivity["overall_status"]:
            print_success("Tất cả services kết nối OK")
        else:
            print_warning("Một số services có vấn đề kết nối")
            for service, status in connectivity.items():
                if service != "overall_status":
                    print(f"  {service}: {'✅' if status else '❌'}")
        
        print_step(3, "Test text conversation")
        result = pipeline.process_text_conversation("Xin chào! Hôm nay có khỏe không?")
        
        if result["success"]:
            print_success("Text conversation OK")
            print(f"  Response: {result['assistant_text'][:100]}...")
        else:
            print_error(f"Text conversation failed: {result.get('error', 'Unknown')}")
        
        pipeline.shutdown()
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False

def show_usage_guide():
    """Show usage guide"""
    print_header("HƯỚNG DẪN SỬ DỤNG")
    
    print("🚀 Các cách chạy Pipeline 4:")
    print()
    
    print("1. 🎮 Demo tương tác (Khuyến nghị):")
    print("   python demo.py")
    print("   - Giao diện menu đơn giản")
    print("   - Hỗ trợ cả voice và text")
    print("   - Thống kê và quản lý audio")
    print()
    
    print("2. 🔬 Test toàn diện:")
    print("   python test_full_pipeline.py")
    print("   - Kiểm tra tất cả chức năng")
    print("   - Performance metrics")
    print("   - Báo cáo chi tiết")
    print()
    
    print("3. 🎤 Test STT riêng lẻ:")
    print("   python test_stt.py")
    print("   - Kiểm tra Azure Speech Services")
    print("   - Test với file audio")
    print()
    
    print("4. 🔊 Test TTS riêng lẻ:")
    print("   python test_tts.py")
    print("   - Kiểm tra VBEE Text-to-Speech")
    print("   - Test các giọng nói")
    print()
    
    print("5. 🔧 Tích hợp vào code:")
    print("   from full_pipeline import ElderCarePipeline")
    print("   pipeline = ElderCarePipeline()")
    print("   result = pipeline.process_text_conversation('Your text')")
    print()
    
    print("📁 Cấu trúc file:")
    print("  📂 pipeline4/")
    print("    ├── 🎮 demo.py           # Demo tương tác")
    print("    ├── 🔬 test_full_pipeline.py  # Test toàn diện")
    print("    ├── 🎤 test_stt.py       # Test STT module")
    print("    ├── 🔊 test_tts.py       # Test TTS module")
    print("    ├── 🔧 full_pipeline.py  # Main pipeline")
    print("    ├── ⚙️  config.py        # Configuration")
    print("    ├── 🛠️  utils.py         # Utilities")
    print("    ├── 🎯 *_module.py       # Individual modules")
    print("    ├── 📂 audio_samples/    # Audio files")
    print("    └── 📂 logs/             # Logs và reports")
    print()
    
    print("💡 Tips:")
    print("  - Đặt file audio có giọng nói thật vào audio_samples/input/")
    print("  - Check logs/ để debug và xem chi tiết")
    print("  - Audio output được lưu trong audio_samples/output/")
    print("  - Sử dụng demo.py để trải nghiệm đầy đủ")

def main():
    """Main quick start function"""
    print_header("PIPELINE 4 - ELDER CARE VOICE ASSISTANT", 80)
    print_header("QUICK START GUIDE", 80)
    
    print_info("🎯 Mục tiêu: Chatbot giọng nói cho người cao tuổi")
    print_info("🔧 Stack: Azure STT + Gemini LLM + VBEE TTS")
    print()
    
    all_checks_passed = True
    
    # Step 1: Check dependencies
    print_step(1, "Kiểm tra dependencies")
    if not check_dependencies():
        all_checks_passed = False
        print_warning("⚠️  Cần cài đặt dependencies trước khi tiếp tục")
    
    # Step 2: Check directory structure
    print_step(2, "Kiểm tra cấu trúc thư mục")
    if not check_directory_structure():
        all_checks_passed = False
    
    # Step 3: Check configuration
    print_step(3, "Kiểm tra cấu hình API")
    if not check_configuration():
        all_checks_passed = False
        print_warning("⚠️  Cần cấu hình API keys trước khi test")
    
    # Step 4: Test functionality (only if all previous checks passed)
    if all_checks_passed:
        print_step(4, "Test chức năng cơ bản")
        if test_basic_functionality():
            print_success("🎉 Pipeline hoạt động bình thường!")
        else:
            all_checks_passed = False
            print_warning("⚠️  Pipeline có vấn đề, check logs để debug")
    
    # Step 5: Show usage guide
    print_step(5, "Hướng dẫn sử dụng")
    show_usage_guide()
    
    # Final summary
    print_header("TÓM TẮT", 60)
    
    if all_checks_passed:
        print_success("✅ PIPELINE SẴN SÀNG SỬ DỤNG!")
        print_info("🎮 Khuyến nghị: Chạy 'python demo.py' để bắt đầu")
    else:
        print_warning("⚠️  PIPELINE CHƯA SẴN SÀNG")
        print_info("🔧 Hãy khắc phục các vấn đề trên rồi chạy lại quick_start.py")
    
    print()
    print("📞 Hỗ trợ:")
    print("  - Check logs/ để xem chi tiết lỗi")
    print("  - Đọc comments trong các file .py")
    print("  - Test từng module riêng nếu có lỗi")

if __name__ == "__main__":
    main()
