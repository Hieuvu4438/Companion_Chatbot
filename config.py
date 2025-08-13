import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Speech Services Configuration
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', 'southeastasia')
AZURE_SPEECH_LANGUAGE = 'vi-VN'  # Vietnamese
AZURE_SPEECH_FORMAT = 'wav'

# Azure TTS Configuration
AZURE_TTS_VOICE = 'vi-VN-NamMinhNeural'  # Female voice for elderly-friendly tone
AZURE_TTS_SPEECH_RATE = 1  # Slower speech for elderly comprehension
AZURE_TTS_PITCH = 0  # Normal pitch
AZURE_TTS_VOLUME = 100  # Full volume

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


GEMINI_MODEL = 'gemini-1.5-flash'
GEMINI_MAX_TOKENS = 1000
GEMINI_TEMPERATURE = 0.7

# Audio Configuration
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024
AUDIO_FORMAT = 'wav'
RECORD_DURATION = 5  # seconds

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

# Chatbot Configuration for Elder Care
ELDER_CARE_PROMPT = """
Bạn là một trợ lý AI chuyên hỗ trợ người cao tuổi tại Việt Nam. 
Hãy trả lời một cách:
- Thân thiện, lịch sự và dễ hiểu
- Sử dụng tiếng Việt đơn giản, tránh từ ngữ phức tạp
- Thông tin chính xác về sức khỏe, y tế
- Hỗ trợ các vấn đề đời sống hàng ngày
- Động viên tinh thần tích cực

Câu hỏi: {question}
Trả lời:
"""

# Performance Metrics
METRICS_ENABLED = True
SAVE_METRICS_TO_FILE = True
METRICS_FILE = os.path.join(LOGS_DIR, 'metrics.json')

# Error Handling
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# Azure TTS Voice Options (Vietnamese voices)
AZURE_TTS_VOICES = {
    'vi-VN-HoaiMyNeural': 'Nữ - Hoài My (Thân thiện, phù hợp người cao tuổi)',
    'vi-VN-NamMinhNeural': 'Nam - Nam Minh (Rõ ràng, chuyên nghiệp)'
}

# Health check endpoints
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_INTERVAL = 300  # seconds
