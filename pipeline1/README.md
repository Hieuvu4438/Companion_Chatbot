# Pipeline1 - Elder Care Voice Chatbot

Hệ thống chatbot giọng nói hỗ trợ người cao tuổi sử dụng Google Cloud Services.

## 🏗️ Kiến Trúc Hệ Thống

```
Pipeline1/
├── 📁 utils/                    # Utility modules  
│   ├── __init__.py             # Package initialization
│   ├── stt_service.py          # Google Cloud STT service
│   ├── llm_service.py          # Google Gemini LLM service  
│   ├── tts_service.py          # Google Cloud TTS service
│   ├── metrics.py              # Performance metrics collector
│   └── audio_utils.py          # Audio recording & playback
├── 📁 audio_samples/           # Audio files storage
│   ├── input/                  # Input audio recordings
│   └── output/                 # Generated TTS audio
├── 📁 logs/                    # Application logs
├── 📄 config.py                # Configuration management
├── 📄 .env                     # Environment variables
├── 📄 requirements.txt         # Python dependencies
├── 📄 main_pipeline.py         # Main pipeline application
├── 📄 test_stt_new.py          # STT testing module
├── 📄 test_tts_new.py          # TTS testing module
└── 📄 README.md                # This file
```

## 🎯 Tính Năng Chính

### 🎤 Speech-to-Text (STT)
- **Google Cloud Speech-to-Text API**
- Hỗ trợ tiếng Việt (vi-VN)
- Model: `latest_long` với enhanced quality
- Real-time transcription với confidence scoring
- Voice Activity Detection (VAD)

### 🤖 Large Language Model (LLM)  
- **Google Gemini 2.0 Flash**
- Prompt tối ưu cho người cao tuổi
- Context conversation memory
- Emotion analysis và tone adjustment
- Health advice với medical disclaimer

### 🔊 Text-to-Speech (TTS)
- **Google Cloud Text-to-Speech API**
- Neural2 Vietnamese voices (vi-VN-Neural2-A/D)
- Elder-friendly speaking rate (0.9x)
- SSML support với emphasis và pauses
- Multiple voice options

### 📊 Metrics & Monitoring
- Real-time performance tracking
- Latency monitoring cho từng component
- Success/failure rate statistics
- Detailed logging với JSON export
- Audio quality metrics

### 🎵 Audio Processing
- PyAudio cho recording với customizable duration
- Pygame + pydub cho playback
- Format conversion (WAV ↔ MP3)
- Voice Activity Detection
- Audio file cleanup

## ⚙️ Cài Đặt

### 1. Cài đặt Dependencies

```bash
cd pipeline1
pip install -r requirements.txt
```

**Lưu ý PyAudio trên Windows:**
```bash
# Nếu PyAudio gặp lỗi, dùng pipwin:
pip install pipwin
pipwin install pyaudio

# Hoặc từ wheel file:
pip install https://download.lfd.uci.edu/pythonlibs/archived/PyAudio-0.2.11-cp39-cp39-win_amd64.whl
```

### 2. Cấu Hình API Keys

Sao chép và cập nhật file `.env`:

```bash
# Copy template
cp .env.example .env

# Edit với API keys thực tế
notepad .env  # Windows
```

#### 🟡 Google Cloud Setup:

1. **Truy cập**: https://console.cloud.google.com/
2. **Tạo Project** hoặc chọn project có sẵn
3. **Enable APIs**:
   - Speech-to-Text API
   - Text-to-Speech API
4. **Tạo Service Account**:
   - IAM & Admin → Service Accounts → Create
   - Role: Project Editor hoặc Speech Admin
5. **Tạo Key**:
   - Service Account → Keys → Add Key → JSON
   - Download file JSON
6. **Update .env**:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
   ```

#### 🟢 Gemini API Setup:

1. **Truy cập**: https://aistudio.google.com/
2. **Login** với Google account
3. **Get API Key** → Create API key
4. **Update .env**:
   ```
   GEMINI_API_KEY=AIzaSy...your-api-key
   ```

### 3. Test Hệ Thống

```bash
# Test individual components
python test_stt_new.py
python test_tts_new.py

# Run main pipeline  
python main_pipeline.py
```

## 🚀 Sử Dụng

### Quick Start

```python
from main_pipeline import ElderVoiceChatbotPipeline

# Initialize pipeline
pipeline = ElderVoiceChatbotPipeline()

# Initialize all services
if pipeline.initialize():
    # Run full voice-to-voice pipeline
    result = pipeline.run_full_pipeline(recording_duration=5.0)
    
    if result["success"]:
        print(f"User: {result['user_text']}")
        print(f"AI: {result['ai_response']}")
        print(f"Latency: {result['pipeline_latency_ms']:.1f}ms")
```

### Interactive Menu

```bash
python main_pipeline.py
```

Menu options:
1. **🎤 Chạy pipeline hoàn chỉnh** - Voice-to-voice conversation
2. **🧪 Test components** - Individual STT/LLM/TTS testing  
3. **📊 View metrics** - Performance statistics
4. **💾 Save metrics** - Export to JSON
5. **🔄 Reset metrics** - Clear statistics
6. **⚙️ Pipeline status** - System health check
7. **🔧 Advanced config** - Voice selection, conversation history

### Module Usage

#### STT Service:
```python
from utils import GoogleSTTService

stt = GoogleSTTService(credentials_path="path/to/creds.json")
result = stt.transcribe_audio_file("audio.wav")

print(f"Transcript: {result['transcript']}")
print(f"Confidence: {result['confidence']}")
```

#### LLM Service:
```python
from utils import GeminiLLMService

llm = GeminiLLMService(api_key="your-gemini-key")
result = llm.generate_response("Tôi bị đau đầu, làm sao để giảm đau?")

print(f"Response: {result['response']}")
```

#### TTS Service:
```python
from utils import GoogleTTSService

tts = GoogleTTSService(credentials_path="path/to/creds.json")
result = tts.synthesize_speech("Xin chào bác!")

# Play audio
from utils import AudioPlayer
player = AudioPlayer()
player.play_audio_file(result['audio_file'])
```

## 📊 Performance Metrics

Hệ thống tracking detailed metrics:

### STT Metrics:
- **Latency**: Response time (ms)
- **Confidence**: Recognition accuracy (0-1)
- **Success Rate**: Successful transcriptions %
- **Error Tracking**: Failed requests với error details

### LLM Metrics:
- **Latency**: Generation time (ms)  
- **Token Count**: Input/output tokens
- **Success Rate**: Successful generations %
- **Conversation Context**: History tracking

### TTS Metrics:
- **Latency**: Synthesis time (ms)
- **Character Count**: Text length processed
- **Generation Speed**: Characters per second
- **Voice Quality**: Audio output metrics

### Pipeline Metrics:
- **End-to-End Latency**: Total processing time
- **Component Breakdown**: Individual latencies
- **Success Rate**: Overall pipeline success %
- **Audio Quality**: Recording/playback success

## 🔧 Cấu Hình Nâng Cao

### Audio Settings (`config.py`):
```python
AUDIO_SAMPLE_RATE = 16000      # Sample rate (Hz)
AUDIO_CHANNELS = 1             # Mono audio
RECORD_DURATION = 5            # Default recording (seconds)
SILENCE_THRESHOLD = 0.5        # VAD sensitivity
```

### STT Settings:
```python
GOOGLE_STT_LANGUAGE = 'vi-VN'               # Vietnamese
GOOGLE_STT_MODEL = 'latest_long'            # Conversation model
GOOGLE_STT_ENABLE_AUTOMATIC_PUNCTUATION = True
```

### TTS Settings:
```python
GOOGLE_TTS_VOICE_NAME = 'vi-VN-Neural2-A'   # Female neural voice
GOOGLE_TTS_SPEAKING_RATE = 0.9              # Slower for elderly
GOOGLE_TTS_PITCH = 0.0                      # Normal pitch
```

### LLM Settings:
```python
GEMINI_MODEL = 'gemini-2.0-flash-exp'       # Latest model
GEMINI_TEMPERATURE = 0.7                    # Balanced creativity
MAX_CONVERSATION_HISTORY = 5                # Context memory
```

## 🚨 Troubleshooting

### Common Issues:

#### 1. PyAudio Installation Error:
```bash
# Windows solution:
pip install pipwin
pipwin install pyaudio

# Or download wheel manually from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```

#### 2. Google Cloud Authentication:
```bash
# Set environment variable manually:
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\key.json

# Or in Python:
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/key.json"
```

#### 3. Audio Device Issues:
```python
# List available audio devices:
from utils import AudioRecorder
recorder = AudioRecorder()
recorder.list_devices()

# Use specific device:
recorder.record_audio(duration=5.0, device_index=1)
```

#### 4. API Quota Exceeded:
- Check Google Cloud Console for usage
- Verify billing account setup
- Monitor free tier limits:
  - Speech: 60 minutes/month free
  - TTS: 1M characters/month free
  - Gemini: 15 requests/minute free

### Debug Mode:
```python
# Enable in config.py:
DEBUG_MODE = True
SAVE_AUDIO_FILES = True    # Keep audio files for analysis
VERBOSE_LOGGING = True     # Detailed logs
```

## 📈 API Usage & Pricing

### Google Cloud Speech/TTS:
- **Free Tier**: 60 phút STT + 1M ký tự TTS/tháng
- **Paid**: $0.006/15s STT, $4/$16 per 1M chars TTS
- **Monitor**: Google Cloud Console → Billing

### Google Gemini:
- **Free Tier**: 15 requests/phút, 1500 requests/ngày  
- **Rate Limits**: Automatic retry với exponential backoff
- **Monitor**: AI Studio usage dashboard

## 🔒 Security & Privacy

### Data Protection:
- **Không lưu trữ** audio recordings (trừ debug mode)
- **Conversations** không log ra file (configurable)
- **API keys** trong .env (không commit vào Git)
- **Credentials** local file system only

### Privacy Settings:
```python
# In config.py:
LOG_USER_CONVERSATIONS = False      # No conversation logging
ENABLE_CONTENT_FILTERING = True     # Safe content only
SANITIZE_USER_INPUT = True          # Input validation
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Development Setup:
```bash
# Install dev dependencies:
pip install -r requirements-dev.txt

# Run tests:
python -m pytest tests/

# Code formatting:
black pipeline1/
flake8 pipeline1/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Credits

- **IEC Team** - Initial development
- **Google Cloud** - STT/TTS APIs
- **Google AI** - Gemini LLM
- **Community** - Elder care prompting techniques

## 📞 Support

- **Issues**: GitHub Issues tab
- **Documentation**: This README + inline code docs
- **Email**: support@iec-team.com

---

**Pipeline1 - Empowering elderly care through voice AI technology** 🎤🤖🔊
