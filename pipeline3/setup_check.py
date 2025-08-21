"""
Setup Check Script for Pipeline 3
Kiểm tra và hướng dẫn cài đặt pipeline
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title, width=60):
    print(f"\n{'='*width}")
    print(f"{title.center(width)}")
    print(f"{'='*width}")

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    print(f"  Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ❌ Python 3.8+ required")
        return False
    else:
        print("  ✅ Python version OK")
        return True

def check_required_packages():
    """Check if required packages are installed"""
    print("\n📦 Checking required packages...")
    
    required_packages = [
        "requests",
        "openai",
        "google-generativeai",
        "google-cloud-texttospeech",
        "pydub",
        "librosa",
        "soundfile",
        "colorama",
        "tabulate",
        "tqdm",
        "psutil",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📝 To install missing packages, run:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    else:
        print("\n✅ All required packages are installed!")
        return True

def check_directory_structure():
    """Check if directory structure is correct"""
    print("\n📁 Checking directory structure...")
    
    required_dirs = [
        "audio_samples",
        "audio_samples/input",
        "audio_samples/output",
        "logs"
    ]
    
    required_files = [
        "config.py",
        "utils.py", 
        "stt_module.py",
        "llm_module.py",
        "tts_module.py",
        "pipeline_full.py",
        "test_stt.py",
        "test_tts.py",
        "test_full_pipeline.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_good = True
    
    # Check directories
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - MISSING")
            all_good = False
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"    📝 Created {dir_path}/")
            except:
                print(f"    ❌ Failed to create {dir_path}/")
    
    # Check files
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_good = False
    
    return all_good

def check_configuration():
    """Check API configuration"""
    print("\n🔑 Checking API configuration...")
    
    try:
        from config import get_config_status, validate_config
        
        status = get_config_status()
        errors = validate_config()
        
        print(f"  FPT.AI configured: {'✅' if status['fpt_configured'] else '❌'}")
        print(f"  OpenAI configured: {'✅' if status['openai_configured'] else '❌'}")
        print(f"  Gemini configured: {'✅' if status['gemini_configured'] else '❌'}")
        print(f"  Google Cloud configured: {'✅' if status['google_cloud_configured'] else '❌'}")
        
        if errors:
            print("\n❌ Configuration errors:")
            for error in errors:
                print(f"    - {error}")
            return False
        else:
            print("\n✅ Configuration is ready!")
            return True
            
    except ImportError as e:
        print(f"  ❌ Cannot import config module: {e}")
        return False

def run_basic_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test config
        print("  Testing config...")
        from config import validate_config
        errors = validate_config()
        if not errors:
            print("    ✅ Config test passed")
        else:
            print("    ❌ Config test failed")
            return False
        
        # Test utils
        print("  Testing utils...")
        from utils import MetricsCollector, Logger
        metrics = MetricsCollector()
        logger = Logger("test")
        print("    ✅ Utils test passed")
        
        # Test modules (basic import)
        print("  Testing modules...")
        from stt_module import STTModule
        from llm_module import LLMModule  
        from tts_module import TTSModule
        print("    ✅ Modules import test passed")
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"    ❌ Test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for setup"""
    print_header("NEXT STEPS")
    
    print("📝 To complete setup:")
    print()
    print("1. 📋 Configure API Keys:")
    print("   - Copy .env.example to .env")
    print("   - Edit config.py or .env file with your API keys:")
    print("     • FPT.AI API key (https://fpt.ai/)")
    print("     • OpenAI API key (https://platform.openai.com/)")
    print("     • Google Gemini API key (https://ai.google.dev/)")
    print("     • Google Cloud JSON file (https://console.cloud.google.com/)")
    print()
    print("2. 🎵 Add sample audio files:")
    print("   - Put sample audio files (.wav, .mp3) in audio_samples/input/")
    print("   - Use Vietnamese speech for best results")
    print()
    print("3. 🧪 Run tests:")
    print("   - python test_stt.py")
    print("   - python test_tts.py") 
    print("   - python test_full_pipeline.py")
    print()
    print("4. 🚀 Run the pipeline:")
    print("   - python pipeline_full.py")

def main():
    """Main setup check function"""
    print_header("PIPELINE 3 SETUP CHECK", 70)
    
    print("🔍 Checking Pipeline 3 setup...")
    
    checks = {
        "python_version": check_python_version(),
        "packages": check_required_packages(),
        "directory_structure": check_directory_structure(),
        "configuration": check_configuration(),
        "basic_tests": False  # Will be set later
    }
    
    # Only run basic tests if other checks pass
    if all([checks["python_version"], checks["packages"], checks["directory_structure"]]):
        checks["basic_tests"] = run_basic_tests()
    
    # Summary
    print_header("SETUP CHECK SUMMARY")
    
    passed_checks = sum(checks.values())
    total_checks = len(checks)
    
    print(f"📊 Setup progress: {passed_checks}/{total_checks} checks passed")
    print()
    
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        display_name = check_name.replace('_', ' ').title()
        print(f"  {display_name}: {status}")
    
    if passed_checks == total_checks:
        print("\n🎉 Setup is complete! Pipeline ready to use.")
    elif passed_checks >= 3:
        print("\n⚠️  Setup is mostly complete. Fix remaining issues.")
        show_next_steps()
    else:
        print("\n❌ Setup needs work. Please fix the issues above.")
        show_next_steps()

if __name__ == "__main__":
    main()
