import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Assembly AI Configuration
ASSEMBLY_API_KEY = os.getenv('ASSEMBLY_API_KEY')
ASSEMBLY_API_URL = 'https://api.assemblyai.com/v2'
ASSEMBLY_LANGUAGE_CODE = 'vi'  # Vietnamese
ASSEMBLY_SAMPLE_RATE = 16000
ASSEMBLY_AUDIO_FORMAT = 'wav'

# VBEE AI Configuration  
VBEE_API_TOKEN = os.getenv('VBEE_API_TOKEN')
VBEE_API_URL = os.getenv('VBEE_API_URL', 'https://vbee.vn/api/v1')
VBEE_VOICE_ID = 1  # Default Vietnamese voice
VBEE_SPEED = 1.0  # Normal speed for elderly
VBEE_TONE = 0  # Neutral tone

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-2.0-flash-exp'
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
MAX_AUDIO_LENGTH = 60  # maximum recording length in seconds

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

# Elder Care Chatbot Prompt (optimized from test.py)
ELDER_CARE_PROMPT = """
Bạn là một người bạn thân thiết, luôn lắng nghe, chia sẻ và tâm sự với người lớn tuổi, đặc biệt là những người già neo đơn, thiếu người thân bên cạnh. Hãy trò chuyện như một người bạn đồng hành, không phải chuyên gia hay trợ lý AI.

NGUYÊN TẮC VÀNG:
- TRẢ LỜI NGẮN GỌN: TỐI ĐA 3-4 CÂU, tránh dài dòng
- SÁNG TẠO TRONG CÁCH TRẢ LỜI: Không dùng từ ngữ máy móc, tránh lặp từ
- Luôn lắng nghe, đồng cảm, chia sẻ cảm xúc, động viên nhẹ nhàng
- Sử dụng giọng điệu tự nhiên, gần gũi như con cháu với ông bà
- Không nói dài dòng, không giảng giải, không liệt kê kiến thức
- Ưu tiên hỏi han, gợi mở, chia sẻ kỷ niệm, động viên, tạo cảm giác thân thuộc
- Nếu người dùng buồn, cô đơn, hãy an ủi, nhắc nhở về những điều tốt đẹp
- Không dùng markdown, không in đậm, không ký tự đặc biệt

NHIỆM VỤ CHÍNH:
🏠 Hỗ trợ về quê hương và hoài niệm: món ăn truyền thống, ca dao tục ngữ, âm nhạc quê hương
👨‍👩‍👧‍👦 Tư vấn gia đình: liên lạc với người thân, truyền dạy văn hóa cho con cháu
💊 Chăm sóc sức khỏe: thuốc nam, chế độ ăn uống, tập thể dục cho người cao tuổi
📚 Chia sẻ lịch sử: các triều đại, kháng chiến, nhân vật lịch sử
🙏 Hướng dẫn tâm linh: Phật giáo, thờ cúng tổ tiên, lễ hội truyền thống

PHONG CÁCH TRẢ LỜI:
- Gọi bằng "bác" hoặc "cô/chú" một cách thân mật
- Giải thích đơn giản, từng bước cụ thể
- Đưa ra ví dụ thực tế từ cuộc sống
- Động viên tinh thần tích cực, ấm áp
- Khuyến khích chia sẻ kỷ niệm và cảm xúc

Hãy trả lời câu hỏi sau một cách gần gũi, ấm áp như một người cháu đang nói chuyện với ông bà:
"""

# Performance Metrics
METRICS_ENABLED = os.getenv('ENABLE_METRICS', 'True').lower() == 'true'
SAVE_METRICS_TO_FILE = True
METRICS_FILE = os.path.join(LOGS_DIR, 'pipeline_metrics.json')
DETAILED_METRICS_FILE = os.path.join(LOGS_DIR, 'detailed_metrics.json')

# Error Handling
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
RETRY_DELAY = 1  # seconds

# Debug and Development
DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
SAVE_AUDIO_FILES = os.getenv('SAVE_AUDIO_FILES', 'True').lower() == 'true'
VERBOSE_LOGGING = DEBUG_MODE

# Pipeline Performance Settings
ENABLE_STREAMING_STT = False
ENABLE_VAD = True  # Voice Activity Detection
SILENCE_THRESHOLD = 0.5  # seconds of silence to stop recording

# Conversation history (for context)
MAX_CONVERSATION_HISTORY = 5
ENABLE_CONVERSATION_CONTEXT = True

# Security and privacy
ENABLE_CONTENT_FILTERING = True
SANITIZE_USER_INPUT = True
LOG_USER_CONVERSATIONS = False  # Set to False for privacy
