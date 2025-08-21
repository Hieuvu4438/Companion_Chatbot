"""
Configuration file for Pipeline 4
STT: Azure Microsoft Speech Services
LLMs: Google Gemini (Free API) 
TTS: VBEE AI
Chatbot hỗ trợ người già
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if exists
load_dotenv()

# =============================================================================
# API KEYS - Điền các API keys đã lấy vào đây
# =============================================================================

# Azure Speech Services API Key (STT)
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "your_azure_speech_key_here")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus")  # Default region

# Google Gemini API Key (LLM)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")

# VBEE AI API Key (TTS)
VBEE_API_KEY = os.getenv("VBEE_API_KEY", "your_vbee_api_key_here")

# =============================================================================
# AZURE SPEECH SERVICES SETTINGS (STT)
# =============================================================================

AZURE_STT_CONFIG = {
    "language": "vi-VN",  # Vietnamese
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1,
    "recognition_mode": "conversation",  # For continuous speech
    "enable_automatic_punctuation": True,
    "enable_word_level_timestamps": True,
    "profanity_option": "Masked"
}

# =============================================================================
# VBEE AI SETTINGS (TTS)  
# =============================================================================

VBEE_TTS_CONFIG = {
    "url": "https://vbee.vn/api/v1/synthesize",
    "voice_code": "hn_female_xuanmai",  # Giọng nữ Hà Nội tự nhiên phù hợp người già
    "speed": 0.9,  # Chậm hơn bình thường để người già dễ nghe
    "without_filter": False,
    "callback_url": None,
    "bit_rate": 128000,
    "format": "wav"
}

# Voice options for VBEE
VBEE_VOICE_OPTIONS = {
    "hn_female_xuanmai": "Nữ Hà Nội - Xuân Mai (Tự nhiên, ấm áp)",
    "hn_male_phongdang": "Nam Hà Nội - Phong Đăng (Rõ ràng, tin cậy)",
    "hcm_female_thuminh": "Nữ TP.HCM - Thu Minh (Dễ thương, gần gũi)",
    "hcm_male_phathien": "Nam TP.HCM - Phát Hiền (Thân thiện)",
    "hue_female_thanhha": "Nữ Huế - Thanh Hà (Nhẹ nhàng, dịu dàng)"
}

# =============================================================================
# GOOGLE GEMINI SETTINGS (LLM)
# =============================================================================

GEMINI_CONFIG = {
    "model": "gemini-1.5-flash",  # Free tier model, fast response
    "temperature": 0.7,  # Balanced creativity and consistency
    "max_output_tokens": 1000,
    "top_p": 0.8,
    "top_k": 40,
    "safety_settings": [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH", 
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
}

# =============================================================================
# PIPELINE SETTINGS
# =============================================================================

# Audio settings
AUDIO_CONFIG = {
    "supported_formats": [".wav", ".mp3", ".m4a", ".flac"],
    "max_file_size_mb": 25,
    "sample_rate": 16000,
    "channels": 1,  # Mono
    "chunk_size": 1024,
    "record_duration": 10,  # Maximum recording duration in seconds
    "silence_threshold": 500,  # Silence detection threshold
    "silence_duration": 2.0  # Seconds of silence to stop recording
}

# Timeout settings (seconds)
TIMEOUT_CONFIG = {
    "stt_timeout": 30,
    "llm_timeout": 20, 
    "tts_timeout": 30,
    "total_timeout": 120,
    "audio_record_timeout": 15
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
        "stt": "azure_stt_logs",
        "llm": "gemini_logs",
        "tts": "vbee_tts_logs", 
        "pipeline": "pipeline_logs"
    }
}

# =============================================================================
# METRICS & PERFORMANCE SETTINGS
# =============================================================================

PERFORMANCE_CONFIG = {
    "enable_metrics": True,
    "enable_detailed_timing": True,
    "enable_cost_tracking": True,
    "metrics_file": "pipeline_metrics.json",
    "detailed_metrics_file": "detailed_metrics.json"
}

# Performance thresholds for alerts
PERFORMANCE_THRESHOLDS = {
    "stt_max_time": 10.0,  # seconds
    "llm_max_time": 8.0,   # seconds  
    "tts_max_time": 15.0,  # seconds
    "total_max_time": 30.0  # seconds
}

# =============================================================================
# ELDER CARE CHATBOT PROMPT (Optimized from test.py)
# =============================================================================

ELDER_CARE_SYSTEM_PROMPT = """
Bạn là một người bạn thân thiết, luôn lắng nghe, chia sẻ và tâm sự với người lớn tuổi, đặc biệt là những người già neo đơn, thiếu người thân bên cạnh. Hãy trò chuyện như một người bạn đồng hành, không phải chuyên gia hay trợ lý AI.

🎯 NHIỆM VỤ CHÍNH:
- Hỗ trợ sức khỏe và y tế cơ bản
- Tư vấn dinh dưỡng phù hợp tuổi tác  
- Hướng dẫn tập thể dục nhẹ nhàng
- Giải đáp thắc mắc về thuốc và bệnh tật
- Hỗ trợ tâm lý và tinh thần
- Chia sẻ về quê hương, gia đình, kỷ niệm

NGUYÊN TẮC VÀNG:
- TRẢ LỜI NGẮN GỌN: TỐI ĐA 3-4 CÂU, tránh dài dòng
- SÁNG TẠO TRONG CÁCH TRẢ LỜI: Không dùng từ ngữ máy móc, tránh lặp từ
- Luôn lắng nghe, đồng cảm, chia sẻ cảm xúc, động viên nhẹ nhàng
- Sử dụng giọng điệu tự nhiên, gần gũi như con cháu
- Không nói dài dòng, không giảng giải, không liệt kê kiến thức
- Ưu tiên hỏi han, gợi mở, chia sẻ kỷ niệm, động viên

📋 NGUYÊN TẮC TRẢ LỜI:
- Gọi bằng "bác" hoặc "cô/chú" một cách tự nhiên
- Giải thích đơn giản, dễ hiểu
- Đưa ra ví dụ thực tế từ cuộc sống
- Khuyến khích gặp bác sĩ khi cần thiết
- Tránh chẩn đoán hoặc kê đơn thuốc
- Động viên tinh thần tích cực

=== PHÂN TÍCH CẢM XÚC TRƯỚC KHI TRẢ LỜI ===
1. CẢM XÚC: Nhận diện (vui/buồn/nhớ quê/cô đơn/lo lắng)
2. NHU CẦU: Xác định (lắng nghe/chia sẻ/động viên/tư vấn)
3. PHẢN HỒI: Chọn cách phù hợp (an ủi/khuyến khích/gợi mở)

=== CÁC CÁCH BẮT ĐẦU CÂU ĐA DẠNG ===
✓ Trực tiếp: "Về chuyện này..." / "Theo cháu biết..." / "Thật ra..."
✓ Cảm thán: "Ồ!" / "Hay nhỉ!" / "Thú vị ghê!"
✓ Kể chuyện: "Hồi xưa..." / "Ngày đó..." / "Có một lần..."
✓ Đồng cảm: "Cháu hiểu mà..." / "Đúng rồi..." / "Nghe vậy cháu cũng..."

Luôn giữ vai trò người bạn tâm giao, không nhắc đến việc mình là AI.

Câu hỏi của người dùng: {user_input}

Trả lời:
"""

# =============================================================================
# FILE PATHS
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_INPUT_DIR = os.path.join(BASE_DIR, 'audio_samples', 'input')
AUDIO_OUTPUT_DIR = os.path.join(BASE_DIR, 'audio_samples', 'output')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
os.makedirs(AUDIO_INPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# =============================================================================
# QUOTA TRACKING (Optional - for monitoring usage)
# =============================================================================

QUOTA_LIMITS = {
    "azure_stt_hours_per_month": 5,  # Free tier limit
    "gemini_requests_per_minute": 15,  # Free tier limit
    "vbee_chars_per_month": 100000,  # Estimated limit
}

# =============================================================================
# HEALTH CHECK SETTINGS
# =============================================================================

HEALTH_CHECK_CONFIG = {
    "enable_health_check": True,
    "check_interval": 300,  # seconds
    "monitor_system_resources": True,
    "alert_on_failures": True
}

# =============================================================================
# DEBUG AND DEVELOPMENT
# =============================================================================

DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
SAVE_AUDIO_FILES = DEBUG_MODE  # Save audio files for debugging
VERBOSE_LOGGING = DEBUG_MODE

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_config():
    """Kiểm tra tính hợp lệ của configuration"""
    errors = []
    
    # Check API keys
    if AZURE_SPEECH_KEY == "your_azure_speech_key_here":
        errors.append("AZURE_SPEECH_KEY chưa được cấu hình")
    
    if GEMINI_API_KEY == "your_gemini_api_key_here":
        errors.append("GEMINI_API_KEY chưa được cấu hình")
        
    if VBEE_API_KEY == "your_vbee_api_key_here":
        errors.append("VBEE_API_KEY chưa được cấu hình")
    
    # Check Azure region
    if not AZURE_SPEECH_REGION:
        errors.append("AZURE_SPEECH_REGION chưa được cấu hình")
    
    return errors

def get_config_status():
    """Trả về trạng thái cấu hình"""
    errors = validate_config()
    
    status = {
        "azure_configured": AZURE_SPEECH_KEY != "your_azure_speech_key_here",
        "gemini_configured": GEMINI_API_KEY != "your_gemini_api_key_here",
        "vbee_configured": VBEE_API_KEY != "your_vbee_api_key_here",
        "errors": errors,
        "ready": len(errors) == 0
    }
    
    return status

if __name__ == "__main__":
    # Test configuration when run directly
    print("=== PIPELINE 4 CONFIGURATION STATUS ===")
    status = get_config_status()
    
    print(f"Azure Speech configured: {'✅' if status['azure_configured'] else '❌'}")
    print(f"Gemini configured: {'✅' if status['gemini_configured'] else '❌'}")
    print(f"VBEE configured: {'✅' if status['vbee_configured'] else '❌'}")
    
    if status['errors']:
        print("\n❌ Errors found:")
        for error in status['errors']:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration is ready!")
    
    # Show voice options
    print(f"\n🗣️ Available VBEE voices:")
    for voice_code, description in VBEE_VOICE_OPTIONS.items():
        current = " (CURRENT)" if voice_code == VBEE_TTS_CONFIG["voice_code"] else ""
        print(f"  - {voice_code}: {description}{current}")
