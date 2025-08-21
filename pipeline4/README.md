# Pipeline 4 - Elder Care Voice Assistant

Hệ thống chatbot giọng nói dành cho người cao tuổi, tích hợp STT (Azure Speech) + LLM (Gemini) + TTS (VBEE AI).

## 🎯 Tính năng chính

- **🎤 Speech-to-Text**: Azure Cognitive Services (tiếng Việt)
- **🧠 Large Language Model**: Google Gemini với prompt tối ưu cho người cao tuổi
- **🔊 Text-to-Speech**: VBEE AI với giọng nói tiếng Việt tự nhiên
- **📊 Metrics & Monitoring**: Theo dõi hiệu suất và response time
- **🎮 Interactive Demo**: Giao diện demo thân thiện
- **📝 Conversation Logging**: Lưu trữ lịch sử trò chuyện

## 🚀 Quick Start

### 1. Cài đặt Dependencies
```bash
pip install azure-cognitiveservices-speech google-generativeai requests python-dotenv
```

### 2. Cấu hình API Keys
Chỉnh sửa `config.py` hoặc tạo file `.env`:
```python
# config.py
AZURE_SPEECH_KEY = "your_azure_speech_key"
AZURE_SPEECH_REGION = "eastus"  # hoặc region khác
GEMINI_API_KEY = "your_gemini_api_key"
VBEE_API_KEY = "your_vbee_api_key"
```

### 3. Chạy Quick Start
```bash
python quick_start.py
```

### 4. Chạy Demo
```bash
python demo.py
```

## 📁 Cấu trúc Project

```
pipeline4/
├── 🎮 demo.py                    # Demo tương tác với menu
├── 🔬 test_full_pipeline.py      # Test toàn diện tất cả chức năng
├── 🎯 quick_start.py             # Hướng dẫn và kiểm tra nhanh
├── 🔧 full_pipeline.py           # Pipeline chính (STT+LLM+TTS)
├── ⚙️ config.py                  # Cấu hình API keys và settings
├── 🛠️ utils.py                   # Utilities: logging, metrics, audio
├── 🎤 stt_module.py              # Azure Speech-to-Text module
├── 🧠 llm_module.py              # Gemini LLM module  
├── 🔊 tts_module.py              # VBEE Text-to-Speech module
├── 🎤 test_stt.py                # Test riêng STT module
├── 🔊 test_tts.py                # Test riêng TTS module
├── 📂 audio_samples/
│   ├── 📥 input/                 # File audio đầu vào (để test STT)
│   └── 📤 output/                # File audio đầu ra (từ TTS)
├── 📂 logs/                      # Logs, metrics, conversation history
└── 📖 README.md                  # File này
```

## 🔧 Cách sử dụng

### Option 1: Demo tương tác (Khuyến nghị)
```bash
python demo.py
```
- Giao diện menu đơn giản
- Test cả voice và text conversation
- Quản lý audio files
- Xem thống kê và lịch sử

### Option 2: Test toàn diện
```bash
python test_full_pipeline.py
```
- Kiểm tra tất cả modules
- Performance metrics chi tiết
- Tạo báo cáo test

### Option 3: Test từng module
```bash
python test_stt.py      # Test Azure Speech STT
python test_tts.py      # Test VBEE TTS
```

### Option 4: Tích hợp vào code
```python
from full_pipeline import ElderCarePipeline

# Khởi tạo pipeline
pipeline = ElderCarePipeline()

# Text conversation
result = pipeline.process_text_conversation("Hôm nay bác có khỏe không?")
print(f"Response: {result['assistant_text']}")

# Voice conversation (cần file audio)
result = pipeline.process_voice_conversation("path/to/audio.wav")
```

## 🎤 Voice Conversation Workflow

1. **Audio Input** → Đặt file audio vào `audio_samples/input/`
2. **STT** → Azure Speech chuyển audio thành text
3. **LLM** → Gemini tạo response phù hợp với người cao tuổi
4. **TTS** → VBEE tạo audio tiếng Việt tự nhiên
5. **Audio Output** → Lưu vào `audio_samples/output/`

## 📊 Metrics & Monitoring

Pipeline tự động track:
- **Response Times**: STT, LLM, TTS processing time
- **Success Rates**: Tỷ lệ thành công từng bước
- **Performance Alerts**: Cảnh báo khi response time quá chậm
- **Conversation Logs**: Lưu chi tiết từng cuộc trò chuyện

## 🎯 Elder Care Optimizations

### Prompt Engineering
- **Ngôn ngữ thân thiện**: Xưng hô "bác", "cháu"
- **Phản hồi ngắn gọn**: Tránh phức tạp
- **Tâm lý tích cực**: Khuyến khích, an ủi
- **Hướng dẫn cụ thể**: Từng bước rõ ràng

### Voice Settings
- **Tốc độ chậm**: Dễ nghe với người cao tuổi  
- **Giọng nữ**: Thân thiện, dễ chịu
- **Volume cao**: Phù hợp với khả năng nghe

### Interface Design
- **Menu đơn giản**: Lựa chọn rõ ràng
- **Feedback visual**: Icon và màu sắc
- **Error handling**: Thông báo dễ hiểu

## 🔧 Configuration Options

### Azure Speech (STT)
```python
AZURE_SPEECH_CONFIG = {
    "language": "vi-VN",           # Tiếng Việt
    "continuous_mode": True,       # Nhận diện liên tục
    "confidence_threshold": 0.7    # Ngưỡng tin cậy
}
```

### Gemini LLM
```python
GEMINI_CONFIG = {
    "model": "gemini-pro",
    "temperature": 0.7,            # Cân bằng creativity/accuracy
    "max_tokens": 150,             # Giới hạn độ dài response
    "safety_settings": "block_few" # An toàn cho người cao tuổi
}
```

### VBEE TTS
```python
VBEE_CONFIG = {
    "voice": "nu_mien_bac_01",     # Giọng nữ miền Bắc
    "speed": 0.8,                  # Tốc độ chậm
    "pitch": 1.0,                  # Cao độ chuẩn
    "volume": 1.2                  # Âm lượng cao
}
```

## 🐛 Troubleshooting

### Lỗi thường gặp:

**1. ModuleNotFoundError**
```bash
pip install azure-cognitiveservices-speech google-generativeai requests
```

**2. API Key errors**
- Kiểm tra `config.py` đã điền đúng keys
- Verify keys trên Azure/Google/VBEE portals

**3. Audio issues**
- Đảm bảo file audio format: .wav, .mp3, .m4a
- Check file không bị corrupt
- Sample rate khuyến nghị: 16kHz

**4. Network connectivity**
- Test internet connection
- Check firewall settings
- Verify API endpoints accessible

### Debug tips:
- Check `logs/` folder cho chi tiết errors
- Chạy `python quick_start.py` để diagnosis
- Test từng module riêng lẻ
- Enable debug logging trong config

## 📈 Performance Tips

### Optimal Settings:
- **Audio files**: 16kHz WAV, < 30s duration
- **Text input**: < 200 characters
- **Batch processing**: Tránh call API liên tục

### Speed Optimization:
- Pre-warm API connections
- Cache TTS audio cho responses phổ biến
- Use continuous STT cho audio dài
- Parallel processing khi có thể

## 🔮 Future Enhancements

- [ ] **Emotion Recognition**: Phát hiện cảm xúc trong giọng nói
- [ ] **Voice Cloning**: Clone giọng người thân
- [ ] **Health Monitoring**: Tích hợp theo dõi sức khỏe
- [ ] **Video Call**: Hỗ trợ gọi video với gia đình
- [ ] **Smart Home**: Điều khiển thiết bị thông minh
- [ ] **Medicine Reminder**: Nhắc nhở uống thuốc
- [ ] **Emergency Detection**: Phát hiện tình huống khẩn cấp

## 📞 Support

- **Logs**: Check `logs/` folder
- **Debug**: Chạy với verbose logging
- **Test**: Sử dụng individual test files
- **Documentation**: Comments trong source code

---

*Pipeline 4 được thiết kế đặc biệt cho người cao tuổi tại Việt Nam với interface thân thiện và tối ưu hóa trải nghiệm người dùng.*
