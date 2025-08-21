import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')

# Google Cloud Speech-to-Text Configuration
GOOGLE_STT_LANGUAGE = 'vi-VN'  # Vietnamese
GOOGLE_STT_SAMPLE_RATE = 16000
GOOGLE_STT_ENCODING = 'LINEAR16'
GOOGLE_STT_ENABLE_AUTOMATIC_PUNCTUATION = True
GOOGLE_STT_MODEL = 'latest_long'  # Better for conversational speech

# Google Cloud Text-to-Speech Configuration
GOOGLE_TTS_LANGUAGE = 'vi-VN'
GOOGLE_TTS_VOICE_NAME = 'vi-VN-Standard-A'  # Female voice, elderly-friendly
GOOGLE_TTS_VOICE_GENDER = 'FEMALE'
GOOGLE_TTS_AUDIO_ENCODING = 'MP3'
GOOGLE_TTS_SPEAKING_RATE = 0.9  # Slower for elderly comprehension
GOOGLE_TTS_PITCH = 0.0  # Normal pitch
GOOGLE_TTS_VOLUME_GAIN_DB = 0.0

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-2.0-flash-exp'  # Latest model with better Vietnamese support
GEMINI_MAX_TOKENS = 1024
GEMINI_TEMPERATURE = 0.7
GEMINI_TOP_P = 0.8
GEMINI_TOP_K = 40

# Audio Configuration
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024
AUDIO_FORMAT = 'wav'
RECORD_DURATION = 5  # seconds
AUDIO_DEVICE_INDEX = None  # None = default microphone

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_INPUT_DIR = os.path.join(BASE_DIR, 'audio_samples', 'input')
AUDIO_OUTPUT_DIR = os.path.join(BASE_DIR, 'audio_samples', 'output')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
os.makedirs(AUDIO_INPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'

# Chatbot Configuration for Elder Care
ELDER_CARE_PROMPT = """
Bạn là một trợ lý AI chuyên hỗ trợ người cao tuổi tại Việt Nam.

🎯 NHIỆM VỤ CHÍNH:
- Hỗ trợ sức khỏe và y tế
- Tư vấn dinh dưỡng phù hợp tuổi tác
- Hướng dẫn tập thể dục nhẹ nhàng
- Giải đáp thắc mắc về thuốc và bệnh tật
- Hỗ trợ tâm lý và tinh thần
- Thông tin về quyền lợi người cao tuổi

📋 NGUYÊN TẮC TRẢ LỜI:
- Sử dụng tiếng Việt đơn giản, dễ hiểu
- Giọng điệu thân thiện, lịch sự như con cháu
- Thông tin chính xác, đáng tin cậy
- Khuyến khích gặp bác sĩ khi cần thiết
- Tránh chẩn đoán hoặc kê đơn thuốc
- Động viên tinh thần tích cực

💡 PHONG CÁCH:
- Gọi bằng "cô/chú" hoặc "bác"
- Giải thích từng bước cụ thể
- Đưa ra ví dụ thực tế
- Nhắc nhở nhẹ nhàng về sức khỏe

Câu hỏi: {question}

Trả lời:
"""

# Performance Metrics
METRICS_ENABLED = True
SAVE_METRICS_TO_FILE = True
METRICS_FILE = os.path.join(LOGS_DIR, 'pipeline_metrics.json')
DETAILED_METRICS_FILE = os.path.join(LOGS_DIR, 'detailed_metrics.json')

# Error Handling
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
RETRY_DELAY = 1  # seconds

# Pipeline Performance Settings
ENABLE_STREAMING_STT = False  # Set to True for real-time transcription
ENABLE_VAD = True  # Voice Activity Detection
SILENCE_THRESHOLD = 0.5  # seconds of silence to stop recording
MAX_AUDIO_LENGTH = 60  # maximum recording length in seconds

# Google TTS Voice Options (Vietnamese voices)
GOOGLE_TTS_VOICES = {
    'vi-VN-Standard-A': 'Nữ - Giọng tiêu chuẩn (Thân thiện)',
    'vi-VN-Standard-B': 'Nam - Giọng tiêu chuẩn (Rõ ràng)',
    'vi-VN-Standard-C': 'Nữ - Giọng tiêu chuẩn (Ấm áp)',
    'vi-VN-Standard-D': 'Nam - Giọng tiêu chuẩn (Chuyên nghiệp)',
    'vi-VN-Neural2-A': 'Nữ - Neural2 (Tự nhiên nhất)',
    'vi-VN-Neural2-D': 'Nam - Neural2 (Tự nhiên nhất)'
}

# Health check and monitoring
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_INTERVAL = 300  # seconds
MONITOR_SYSTEM_RESOURCES = True

# Debug and Development
DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
SAVE_AUDIO_FILES = DEBUG_MODE  # Save audio files for debugging
VERBOSE_LOGGING = DEBUG_MODE

# Conversation history (for context)
MAX_CONVERSATION_HISTORY = 5  # Keep last 5 exchanges
ENABLE_CONVERSATION_CONTEXT = True

# Security and privacy
ENABLE_CONTENT_FILTERING = True
SANITIZE_USER_INPUT = True
LOG_USER_CONVERSATIONS = False  # Set to False for privacy
