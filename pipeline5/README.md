# Pipeline5: Elder Care Voice Chatbot

## Tổng quan

Pipeline5 là một hệ thống chatbot hoàn chỉnh được thiết kế đặc biệt để hỗ trợ người cao tuổi, sử dụng các API tốt nhất hiện có:

- **STT (Speech-to-Text)**: Assembly AI - Độ chính xác cao cho tiếng Việt
- **LLMs (Large Language Models)**: Google Gemini - Miễn phí với khả năng hiểu tiếng Việt tốt
- **TTS (Text-to-Speech)**: VBEE AI - Giọng nói tự nhiên tiếng Việt

## Tính năng chính

### 🎯 Pipeline hoàn chỉnh
- **Voice Input → AI Response → Voice Output**: Người dùng nói → AI hiểu → AI trả lời bằng giọng nói
- **Real-time Processing**: Xử lý theo thời gian thực với metrics chi tiết
- **Elder-friendly**: Tối ưu đặc biệt cho người cao tuổi (giọng chậm, nội dung phù hợp)

### 📊 Metrics và Monitoring
- **Response Time**: Đo thời gian phản hồi từng component và tổng thể
- **Success Rate**: Tỷ lệ thành công của từng service
- **Quality Metrics**: Confidence score cho STT, latency cho tất cả services
- **Conversation Tracking**: Lưu trữ và phân tích lịch sử hội thoại

### 🤖 AI Chatbot thông minh
- **Elder Care Focused**: Prompt được tối ưu từ file `test.py` gốc
- **Emotion Detection**: Nhận diện cảm xúc từ giọng nói và phản hồi phù hợp
- **Context Aware**: Nhớ và sử dụng ngữ cảnh cuộc hội thoại
- **Vietnamese Culture**: Hiểu và phản hồi về văn hóa, quê hương, gia đình Việt

## Cấu trúc thư mục

```
pipeline5/
├── config.py                 # Cấu hình tất cả APIs và settings
├── stt_module.py             # Assembly AI Speech-to-Text
├── llm_module.py             # Google Gemini LLM  
├── tts_module.py             # VBEE AI Text-to-Speech
├── full_pipeline.py          # Pipeline hoàn chỉnh STT+LLM+TTS
├── test_stt.py              # Test riêng STT module
├── test_tts.py              # Test riêng TTS module
├── requirements.txt         # Dependencies
├── .env.example            # Template cho environment variables
├── audio_samples/          # Folder chứa audio files
│   ├── input/             # Audio input (recorded)
│   └── output/            # Audio output (synthesized)
├── logs/                  # Logs và metrics
└── utils/                 # Utilities (future expansion)
```

## Setup và Cài đặt

### 1. Cài đặt Dependencies

```bash
cd pipeline5
pip install -r requirements.txt
```

### 2. Cấu hình API Keys

Tạo file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Điền thông tin API keys:

```env
# Assembly AI API Configuration
ASSEMBLY_API_KEY=your_assembly_api_key_here

# Gemini API Configuration  
GEMINI_API_KEY=your_gemini_api_key_here

# VBEE AI API Configuration
VBEE_API_TOKEN=your_vbee_api_token_here
VBEE_API_URL=https://vbee.vn/api/v1

# Debug Mode
DEBUG=False
ENABLE_METRICS=True
SAVE_AUDIO_FILES=True
```

### 3. Lấy API Keys

#### Assembly AI (STT)
1. Đăng ký tại: https://www.assemblyai.com/
2. Lấy API key từ dashboard
3. Free tier: 5 giờ transcription/tháng

#### Google Gemini (LLM) 
1. Truy cập: https://ai.google.dev/
2. Tạo API key miễn phí
3. Free tier: 60 requests/phút

#### VBEE AI (TTS)
1. Đăng ký tại: https://vbee.vn/
2. Lấy API token từ dashboard
3. Free tier: 10,000 ký tự/tháng

## Sử dụng

### Test từng module riêng lẻ

```bash
# Test STT (Assembly AI)
python test_stt.py

# Test TTS (VBEE AI)  
python test_tts.py
```

### Chạy Pipeline hoàn chỉnh

```bash
python full_pipeline.py
```

### Sử dụng trong code

```python
from full_pipeline import ElderCarePipeline

# Khởi tạo pipeline
pipeline = ElderCarePipeline()
result = pipeline.initialize()

if result["success"]:
    # Voice conversation
    result = pipeline.process_voice_input(record_duration=5.0)
    
    # Text conversation
    result = pipeline.process_text_input("Xin chào, tôi cần hỗ trợ")
    
    # Continuous conversation
    pipeline.start_continuous_conversation(max_turns=5)
```

## API Reference

### ElderCarePipeline Class

#### Methods

**`initialize()`** - Khởi tạo tất cả components
- Returns: `Dict[str, Any]` - Status và thời gian khởi tạo

**`process_voice_input(record_duration=5.0)`** - Xử lý voice input hoàn chỉnh
- Args: `record_duration` (float) - Thời gian ghi âm
- Returns: `Dict[str, Any]` - Kết quả và metrics chi tiết

**`process_text_input(user_text)`** - Xử lý text input 
- Args: `user_text` (str) - Text từ người dùng
- Returns: `Dict[str, Any]` - Kết quả và metrics

**`start_continuous_conversation(max_turns=10)`** - Cuộc hội thoại liên tục
- Args: `max_turns` (int) - Số lượt tối đa

**`get_current_metrics()`** - Lấy metrics hiện tại
- Returns: `Dict[str, Any]` - Metrics đầy đủ

## Metrics và Monitoring

### Pipeline Metrics
```json
{
  "total_conversations": 10,
  "successful_conversations": 9, 
  "failed_conversations": 1,
  "average_response_time": 5250.5,
  "stt_metrics": {
    "total_calls": 10,
    "successful_calls": 10,
    "average_latency": 2100.0
  },
  "llm_metrics": {
    "total_calls": 10, 
    "successful_calls": 9,
    "average_latency": 1200.5
  },
  "tts_metrics": {
    "total_calls": 9,
    "successful_calls": 9,
    "average_latency": 1950.0
  }
}
```

### Response Time Breakdown
- **STT (Assembly AI)**: 1-3 giây (tùy độ dài audio)
- **LLM (Gemini)**: 0.5-2 giây (tùy độ phức tạp câu hỏi)  
- **TTS (VBEE)**: 1-3 giây (tùy độ dài response)
- **Total Pipeline**: 3-8 giây trung bình

## Tối ưu cho người cao tuổi

### Prompt Engineering
- Được tối ưu từ `test.py` gốc với focus vào người cao tuổi
- Ngôn ngữ đơn giản, gần gũi, thân thiết
- Nội dung phù hợp: sức khỏe, gia đình, quê hương, tâm linh

### Audio Settings
- **TTS Speed**: 0.8-0.9 (chậm hơn bình thường 10-20%)
- **Voice Selection**: Ưu tiên giọng trung niên, ấm áp
- **Audio Quality**: 22050Hz sampling rate cho chất lượng tốt

### Content Focus
- 🏠 Quê hương và hoài niệm
- 👨‍👩‍👧‍👦 Gia đình và người thân
- 💊 Sức khỏe và chăm sóc
- 📚 Lịch sử và văn hóa Việt Nam
- 🙏 Tâm linh và truyền thống

## Troubleshooting

### Lỗi thường gặp

**1. Import Error - Missing dependencies**
```bash
pip install -r requirements.txt
```

**2. API Connection Failed**
- Kiểm tra API keys trong `.env`
- Kiểm tra kết nối internet
- Verify API quotas

**3. Audio Recording Issues**
- Kiểm tra microphone permissions
- Test với `test_stt.py`
- Verify audio drivers

**4. Audio Playback Issues** 
- Install pygame: `pip install pygame`
- Check system audio settings
- Test với `test_tts.py`

### Performance Issues

**High Latency**
- Kiểm tra kết nối mạng
- Reduce audio recording duration
- Monitor API response times

**Low STT Confidence**
- Nói rõ ràng hơn, giảm noise
- Tăng recording duration
- Check microphone quality

## Development

### Thêm tính năng mới

1. **Emotion Detection nâng cao**: Mở rộng từ khóa cảm xúc
2. **Voice Selection**: Cho phép người dùng chọn giọng nói
3. **Conversation Memory**: Lưu trữ dài hạn cuộc hội thoại
4. **Health Monitoring**: Theo dõi sức khỏe qua giọng nói

### Testing

```bash
# Test từng component
python test_stt.py      # Assembly AI
python test_tts.py      # VBEE AI

# Test pipeline hoàn chỉnh
python full_pipeline.py # Choose option 4 for metrics
```

## Liên hệ và Hỗ trợ

- **Documentation**: README này
- **Issues**: Báo cáo lỗi qua Git issues
- **Logs**: Check trong folder `logs/`
- **Metrics**: Sử dụng `get_current_metrics()` để debug

---

**Elder Care Pipeline v1.0** - Được thiết kế với ❤️ cho người cao tuổi Việt Nam
