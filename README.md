# Pipeline2 - Chatbot Hỗ Trợ Người Cao Tuổi với Nhận Diện Cảm Xúc

## 🎯 Tổng quan
Pipeline2 là hệ thống chatbot hoàn chỉnh với **khả năng nhận diện cảm xúc** và **tối ưu hóa phản hồi** cho người cao tuổi:
- **STT (Speech-to-Text)**: Azure Speech Services
- **LLM (Large Language Model)**: Google Gemini với emotion detection
- **TTS (Text-to-Speech)**: Azure Speech Services

## 🆕 Tính năng mới trong Pipeline2

### 🎭 Nhận diện cảm xúc thông minh
- **6 loại cảm xúc**: buồn, nhớ quê, lo lắng, vui vẻ, bệnh tật, gia đình
- **Phản hồi thích ứng**: Tone và nội dung phù hợp với cảm xúc
- **Hỗ trợ tâm lý**: Lời khuyên đặc biệt cho từng trạng thái

### 📝 Tối ưu hóa phản hồi
- **Câu trả lời ngắn gọn**: Tối đa 4-5 câu, dễ hiểu
- **Prompt engineering**: Áp dụng kỹ thuật Chain of Thought
- **Context awareness**: Hiểu ngữ cảnh hội thoại tốt hơn

## 🏗️ Kiến trúc hệ thống

```
🎤 STT: Azure Speech Services (vi-VN)
       ↓
🎭 Emotion Detection: Keyword-based analysis
       ↓
🧠 LLM: Gemini + Emotion-optimized prompts
       ↓
🔊 TTS: Azure Speech Services (vi-VN neural voices)
```

## 🎭 Cảm xúc được hỗ trợ

| Cảm xúc | Từ khóa | Phản hồi |
|---------|---------|----------|
| 😢 **Buồn** | buồn, khóc, cô đơn, tủi thân | An ủi nhẹ nhàng, động viên |
| 🏡 **Nhớ quê** | nhớ quê, quê hương, cố hương | Chia sẻ kỷ niệm, khuyến khích liên lạc |
| 😰 **Lo lắng** | lo lắng, sợ, bất an, hồi hộp | Trấn an, đưa giải pháp thực tế |
| 😊 **Vui vẻ** | vui, hạnh phúc, mừng, phấn khởi | Chia sẻ niềm vui, duy trì tích cực |
| 🏥 **Bệnh tật** | đau, bệnh, mệt, không khỏe | Tư vấn cẩn thận, khuyến khích khám bác sĩ |
| 👨‍👩‍👧‍👦 **Gia đình** | con cháu, gia đình, nhà | Lắng nghe, tư vấn mối quan hệ |

## 📋 Yêu cầu hệ thống

### Phần mềm cần thiết:
- Python 3.8+
- PyAudio (cho ghi âm)
- Microphone và Speaker

### API Keys cần thiết:
1. **Azure Speech Services API Key**
2. **Google Gemini API Key**

## 🔑 Cách lấy API Keys

### 1. Azure Speech Services
1. Truy cập [Azure Portal](https://portal.azure.com/)
2. Tạo tài khoản Azure (có free tier)
3. Tìm kiếm "Speech Services" 
4. Tạo resource mới:
   - Subscription: Chọn subscription của bạn
   - Resource group: Tạo mới hoặc chọn có sẵn
   - Region: Southeast Asia (Singapore) - gần Việt Nam nhất
   - Name: đặt tên cho service
   - Pricing tier: Free F0 (20,000 transactions/month) hoặc Standard S0
5. Sau khi tạo xong, vào resource và copy:
   - **Key 1** hoặc **Key 2** 
   - **Region/Location**

### 2. Google Gemini API
1. Truy cập [Google AI Studio](https://aistudio.google.com/)
2. Đăng nhập bằng Google account
3. Nhấn "Get API Key" 
4. Tạo API key mới
5. Copy API key (bắt đầu bằng "AIza...")

## ⚙️ Cài đặt

### 1. Clone và setup
```bash
cd "d:\PROJECTS\Chatbot for elder - IEC\pipeline2"
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu hình API Keys
Tạo file `.env` trong thư mục `pipeline2`:
```env
# Azure Speech Services
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=southeastasia

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

## 📁 Cấu trúc thư mục

```
pipeline2/
├── README.md                 # File hướng dẫn này
├── requirements.txt          # Dependencies Python
├── .env                     # File chứa API keys (tạo thủ công)
├── config.py                # Cấu hình chung
├── stt_test.py              # Test riêng STT
├── tts_test.py              # Test riêng TTS  
├── llm_test.py              # Test riêng LLM
├── pipeline_full_test.py    # Test full pipeline
├── utils/
│   ├── __init__.py
│   ├── stt_service.py       # Azure Speech Services (STT)
│   ├── llm_service.py       # Google Gemini
│   ├── azure_tts_service.py # Azure Speech Services (TTS)
│   └── metrics.py           # Đo lường performance
└── audio_samples/           # Thư mục chứa file audio test
    ├── input/               # Audio đầu vào
    └── output/              # Audio đầu ra
```

## 🧩 Vai trò từng file

### Core Files:
- **`config.py`**: Chứa tất cả cấu hình, API keys, và constants
- **`pipeline_full_test.py`**: File chính chạy full pipeline STT → LLM → TTS

### Services (utils/):
- **`stt_service.py`**: Xử lý Speech-to-Text bằng Azure
- **`llm_service.py`**: Xử lý chat với Gemini AI  
- **`azure_tts_service.py`**: Chuyển text thành speech bằng Azure TTS
- **`metrics.py`**: Đo lường thời gian, độ chính xác

### Test Files:
- **`stt_test.py`**: Test độc lập chức năng STT
- **`tts_test.py`**: Test độc lập chức năng TTS
- **`llm_test.py`**: Test độc lập chức năng LLM
- **`test_emotion_demo.py`**: Demo nhận diện cảm xúc và tối ưu phản hồi
- **`manual_tts.py`**: Test TTS với nhập text thủ công

## 🚀 Cách chạy

### 1. Test từng thành phần riêng lẻ:

#### Test STT (Speech-to-Text):
```bash
python stt_test.py
```
- Ghi âm 5 giây từ microphone
- Chuyển đổi thành text

#### Test Emotion Detection (MỚI!):
```bash
python test_emotion_demo.py
```
- Demo nhận diện cảm xúc từ text
- Test với mẫu câu định sẵn
- Test phản hồi tối ưu theo cảm xúc
- Chế độ interactive để thử nghiệm

#### Test Manual TTS:
```bash
python manual_tts.py
```
- Nhập text thủ công để chuyển thành speech
- Hỗ trợ multi-line input
- Thống kê usage
- Hiển thị kết quả và metrics

#### Test TTS (Text-to-Speech):
```bash
python tts_test.py
```
- Nhập text từ console
- Chuyển thành giọng nói
- Phát audio và lưu file
- Hiển thị metrics

#### Test LLM:
```bash
python llm_test.py
```
- Nhập câu hỏi từ console  
- Gửi đến Gemini AI
- Hiển thị response và metrics

### 2. Test Full Pipeline với Emotion Detection:
```bash
python pipeline_full_test.py
```

**5 chế độ test:**
1. **Full Pipeline**: STT → Emotion Detection → LLM → TTS
2. **Text Input Pipeline**: Text → Emotion Detection → LLM → TTS  
3. **Multiple Tests**: Chạy nhiều lần để đo performance
4. **Interactive Mode**: Chat liên tục với voice/text
5. **Emotion Detection Test**: Chỉ test nhận diện cảm xúc

**Tính năng mới:**
- 🎭 **Emotion Detection**: Tự động nhận diện cảm xúc từ input
- 📝 **Optimized Response**: Phản hồi ngắn gọn hơn (4-5 câu)
- 🎯 **Context Awareness**: Phản hồi phù hợp với trạng thái cảm xúc
- 📊 **Emotion Metrics**: Hiển thị cảm xúc phát hiện và confidence score

## 📊 Metrics được đo

### STT Metrics:
- **Response Time**: Thời gian xử lý STT
- **Confidence Score**: Độ tin cậy của kết quả
- **Word Count**: Số từ được nhận diện
- **Audio Duration**: Độ dài audio đầu vào

### LLM Metrics:
- **Response Time**: Thời gian xử lý LLM  
- **Token Usage**: Số token input/output
- **Response Length**: Độ dài câu trả lời
- **Model**: Model được sử dụng

### TTS Metrics:
- **Response Time**: Thời gian tạo audio
- **Audio Duration**: Độ dài audio đầu ra
- **Voice Model**: Giọng nói được sử dụng (Azure neural voice)
- **Audio Quality**: Chất lượng âm thanh

### Pipeline Metrics:
- **Total Time**: Tổng thời gian xử lý
- **STT Time**: Thời gian STT
- **LLM Time**: Thời gian LLM  
- **TTS Time**: Thời gian TTS
- **Success Rate**: Tỷ lệ thành công

## 🛠️ Troubleshooting

### Lỗi thường gặp:

#### 1. Lỗi PyAudio:
```bash
# Windows:
pip install pipwin
pipwin install pyaudio

# hoặc:
pip install --only-binary=all pyaudio
```

#### 2. Lỗi Azure Speech:
- Kiểm tra API key và region
- Đảm bảo có kết nối internet
- Kiểm tra quota/billing

#### 3. Lỗi Gemini API:
- Kiểm tra API key
- Đảm bảo API được enable
- Kiểm tra rate limit

#### 4. Lỗi Azure TTS:
- Kiểm tra API key và region
- Đảm bảo có kết nối internet
- Kiểm tra quota/billing

### Debug Mode:
Thêm vào đầu file để bật debug:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Tips

1. **Caching**: Cache kết quả LLM cho câu hỏi lặp lại
2. **Async**: Sử dụng async/await cho API calls
3. **Audio Quality**: Sử dụng format audio tối ưu
4. **Network**: Kiểm tra kết nối mạng ổn định

## 🔒 Bảo mật

- **Không commit file `.env`** lên git
- Sử dụng environment variables trong production
- Rotate API keys định kỳ
- Monitor API usage

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs trong thư mục `logs/`
2. Chạy từng test riêng lẻ để xác định lỗi
3. Kiểm tra API keys và network
4. Tham khảo documentation của từng service

---
**Phiên bản**: 1.0  
**Ngày cập nhật**: August 2025  
**Tác giả**: IEC Team
