"""
Configuration file for Pipeline 3
Chứa tất cả API keys và settings cần thiết
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if exists
load_dotenv()

# =============================================================================
# API KEYS - Điền các API keys đã lấy vào đây
# =============================================================================

# FPT.AI API Key (STT + TTS primary)
FPT_API_KEY = os.getenv("FPT_API_KEY", "your_fpt_api_key_here")

# OpenAI API Key (STT backup - Whisper)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# Google Gemini API Key (LLM)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")

# Google Cloud Service Account JSON path (TTS backup)
GOOGLE_CLOUD_JSON_PATH = os.getenv("GOOGLE_CLOUD_JSON_PATH", "path/to/your/service-account.json")

# =============================================================================
# FPT.AI SETTINGS
# =============================================================================

# FPT.AI STT Settings
FPT_STT_CONFIG = {
    "url": "https://api.fpt.ai/hmi/asr/general",
    "format": "S16LE",
    "rate": 16000,
    "language": "vi"  # Vietnamese
}

# FPT.AI TTS Settings  
FPT_TTS_CONFIG = {
    "url": "https://api.fpt.ai/hmi/tts/v5",
    "voice": "banmai",  # Giọng nữ miền Bắc tự nhiên
    "speed": "0",       # Tốc độ bình thường
    "format": "wav"
}

# =============================================================================
# OPENAI SETTINGS (Backup STT)
# =============================================================================

OPENAI_STT_CONFIG = {
    "model": "whisper-1",
    "language": "vi",  # Vietnamese
    "response_format": "text"
}

# =============================================================================
# GOOGLE GEMINI SETTINGS (LLM)
# =============================================================================

GEMINI_CONFIG = {
    "model": "gemini-1.5-flash",  # Free tier model
    "temperature": 0.7,
    "max_output_tokens": 1000,
    "safety_settings": [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
}

# =============================================================================
# GOOGLE CLOUD TTS SETTINGS (Backup TTS)
# =============================================================================

GOOGLE_TTS_CONFIG = {
    "language_code": "vi-VN",
    "name": "vi-VN-Neural2-A",  # Giọng nữ tự nhiên
    "ssml_gender": "FEMALE",
    "audio_encoding": "LINEAR16",
    "sample_rate": 24000
}

# =============================================================================
# PIPELINE SETTINGS
# =============================================================================

# Audio settings
AUDIO_CONFIG = {
    "supported_formats": [".wav", ".mp3", ".m4a", ".flac"],
    "max_file_size_mb": 25,
    "sample_rate": 16000,
    "channels": 1  # Mono
}

# Timeout settings (seconds)
TIMEOUT_CONFIG = {
    "stt_timeout": 30,
    "llm_timeout": 20,
    "tts_timeout": 30,
    "total_timeout": 120
}

# Retry settings
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1.0,  # seconds
    "backoff_factor": 2.0
}

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_dir": "logs",
    "max_log_files": 30,  # Keep 30 days of logs
    "log_file_prefix": {
        "stt": "stt_logs",
        "llm": "llm_logs", 
        "tts": "tts_logs",
        "pipeline": "pipeline_logs"
    }
}

# =============================================================================
# QUOTA TRACKING (Optional - for monitoring usage)
# =============================================================================

QUOTA_LIMITS = {
    "fpt_stt_minutes_per_month": 60,
    "fpt_tts_chars_per_month": 100000,
    "openai_whisper_minutes_per_month": 1000,  # Paid tier limit
    "google_tts_chars_per_month": 1000000  # Free tier limit
}

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

PERFORMANCE_CONFIG = {
    "enable_metrics": True,
    "enable_detailed_timing": True,
    "enable_cost_tracking": True,
    "metrics_file": "pipeline_metrics.json"
}

# =============================================================================
# SYSTEM PROMPTS FOR LLM
# =============================================================================

SYSTEM_PROMPTS = {
    "elder_assistant": """Bạn là trợ lý AI thân thiện dành cho người cao tuổi. 
Hãy trả lời một cách rõ ràng, từ tốn và dễ hiểu. 
Sử dụng ngôn ngữ lịch sự và tôn trọng.
Nếu có thông tin y tế, hãy khuyên họ tham khảo ý kiến bác sĩ.""",
    
    "general": """Bạn là trợ lý AI hữu ích. 
Hãy trả lời câu hỏi một cách chính xác và hữu ích."""
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_config():
    """Kiểm tra tính hợp lệ của configuration"""
    errors = []
    
    # Check API keys
    if FPT_API_KEY == "your_fpt_api_key_here":
        errors.append("FPT_API_KEY chưa được cấu hình")
    
    if OPENAI_API_KEY == "your_openai_api_key_here":
        errors.append("OPENAI_API_KEY chưa được cấu hình")
        
    if GEMINI_API_KEY == "your_gemini_api_key_here":
        errors.append("GEMINI_API_KEY chưa được cấu hình")
        
    if GOOGLE_CLOUD_JSON_PATH == "path/to/your/service-account.json":
        errors.append("GOOGLE_CLOUD_JSON_PATH chưa được cấu hình")
    
    # Check if Google Cloud JSON file exists
    if GOOGLE_CLOUD_JSON_PATH != "path/to/your/service-account.json":
        if not os.path.exists(GOOGLE_CLOUD_JSON_PATH):
            errors.append(f"Google Cloud JSON file không tồn tại: {GOOGLE_CLOUD_JSON_PATH}")
    
    return errors

def get_config_status():
    """Trả về trạng thái cấu hình"""
    errors = validate_config()
    
    status = {
        "fpt_configured": FPT_API_KEY != "your_fpt_api_key_here",
        "openai_configured": OPENAI_API_KEY != "your_openai_api_key_here", 
        "gemini_configured": GEMINI_API_KEY != "your_gemini_api_key_here",
        "google_cloud_configured": (
            GOOGLE_CLOUD_JSON_PATH != "path/to/your/service-account.json" and 
            os.path.exists(GOOGLE_CLOUD_JSON_PATH)
        ),
        "errors": errors,
        "ready": len(errors) == 0
    }
    
    return status

if __name__ == "__main__":
    # Test configuration when run directly
    print("=== PIPELINE 3 CONFIGURATION STATUS ===")
    status = get_config_status()
    
    print(f"FPT.AI configured: {'✅' if status['fpt_configured'] else '❌'}")
    print(f"OpenAI configured: {'✅' if status['openai_configured'] else '❌'}")
    print(f"Gemini configured: {'✅' if status['gemini_configured'] else '❌'}")
    print(f"Google Cloud configured: {'✅' if status['google_cloud_configured'] else '❌'}")
    
    if status['errors']:
        print("\n❌ Errors found:")
        for error in status['errors']:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration is ready!")
