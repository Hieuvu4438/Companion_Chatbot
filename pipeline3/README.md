# Pipeline Chatbot Cân Bằng STT-LLM-TTS

Pipeline này được thiết kế để cân bằng chi phí và hiệu suất với 2 tiêu chí chính:
- **Tiết kiệm chi phí**: Sử dụng FPT.AI cho STT/TTS với quota miễn phí
- **Backup đáng tin cậy**: OpenAI Whisper và Google Cloud TTS làm phương án dự phòng

## 🏗️ Kiến Trúc Pipeline

```
🎤 STT: FPT.AI STT (60 phút/tháng) + OpenAI Whisper (backup)
    ↓
🧠 LLM: Gemini (Đã có)
    ↓
🔊 TTS: FPT.AI TTS (100k ký tự/tháng) + Google Cloud (backup)
```

## 📁 Cấu Trúc Thư Mục

```
pipeline3/
├── README.md                 # File hướng dẫn này
├── requirements.txt          # Danh sách thư viện cần thiết
├── config.py                # Cấu hình API keys và settings
├── stt_module.py            # Module Speech-to-Text
├── llm_module.py            # Module Large Language Model
├── tts_module.py            # Module Text-to-Speech
├── pipeline_full.py         # Pipeline hoàn chỉnh
├── test_stt.py              # Test riêng STT
├── test_tts.py              # Test riêng TTS
├── test_full_pipeline.py    # Test toàn bộ pipeline
├── utils.py                 # Các hàm tiện ích
└── audio_samples/           # Thư mục chứa file audio mẫu
    ├── input/               # Audio input để test
    └── output/              # Audio output từ TTS
```

## 🔑 Cách Lấy API Keys

### 1. FPT.AI (STT + TTS)
1. Truy cập: https://fpt.ai/
2. Đăng ký tài khoản
3. Vào Dashboard → API Management
4. Tạo API Key cho:
   - **Speech to Text**: 60 phút/tháng miễn phí
   - **Text to Speech**: 100,000 ký tự/tháng miễn phí
5. Copy API Key và lưu vào file `config.py`

### 2. OpenAI (Whisper - Backup STT)
1. Truy cập: https://platform.openai.com/
2. Đăng ký/Đăng nhập
3. Vào API Keys → Create new secret key
4. Copy key và lưu vào `config.py`

### 3. Google Gemini (LLM)
1. Truy cập: https://ai.google.dev/
2. Đăng nhập với Google Account
3. Tạo API Key mới
4. Copy key và lưu vào `config.py`

### 4. Google Cloud (TTS - Backup)
1. Truy cập: https://console.cloud.google.com/
2. Tạo project mới hoặc chọn project hiện có
3. Enable Text-to-Speech API
4. Tạo Service Account Key (JSON)
5. Download file JSON và đặt trong thư mục pipeline3
6. Set đường dẫn trong `config.py`

## ⚙️ Cài Đặt

### 1. Kiểm tra setup (Khuyến nghị chạy đầu tiên)
```bash
python setup_check.py
```
Script này sẽ kiểm tra:
- Phiên bản Python
- Các package cần thiết
- Cấu trúc thư mục
- Cấu hình API keys
- Test cơ bản

### 2. Cài đặt Python packages
```bash
pip install -r requirements.txt
```

### 3. Cấu hình API Keys
**Cách 1: Sử dụng file .env (Khuyến nghị)**
```bash
cp .env.example .env
# Chỉnh sửa file .env và điền API keys
```

**Cách 2: Chỉnh sửa trực tiếp config.py**
Chỉnh sửa file `config.py` và điền các API keys đã lấy:

```python
# FPT.AI API Keys
FPT_API_KEY = "your_fpt_api_key_here"

# OpenAI API Key
OPENAI_API_KEY = "your_openai_api_key_here"

# Google Gemini API Key
GEMINI_API_KEY = "your_gemini_api_key_here"

# Google Cloud Service Account JSON path
GOOGLE_CLOUD_JSON_PATH = "path/to/your/service-account.json"
```

## 🎯 Vai Trò Từng File

### Core Modules
- **`stt_module.py`**: Xử lý Speech-to-Text với FPT.AI primary và OpenAI Whisper backup
- **`llm_module.py`**: Xử lý Large Language Model với Google Gemini
- **`tts_module.py`**: Xử lý Text-to-Speech với FPT.AI primary và Google Cloud backup
- **`pipeline_full.py`**: Kết hợp cả 3 modules thành pipeline hoàn chỉnh

### Configuration & Utils
- **`config.py`**: Chứa tất cả API keys và cấu hình
- **`utils.py`**: Các hàm tiện ích như timing, logging, file handling

### Test Files
- **`test_stt.py`**: Test độc lập STT module với metrics thời gian
- **`test_tts.py`**: Test độc lập TTS module với metrics thời gian
- **`test_full_pipeline.py`**: Test toàn bộ pipeline với metrics chi tiết

## 🚀 Cách Chạy

### 1. Test riêng STT
```bash
python test_stt.py
```
- Input: File audio (.wav, .mp3, .m4a)
- Output: Text được nhận dạng + metrics thời gian

### 2. Test riêng TTS
```bash
python test_tts.py
```
- Input: Text cần chuyển đổi
- Output: File audio + metrics thời gian

### 3. Test Full Pipeline
```bash
python test_full_pipeline.py
```
- Input: File audio
- Output: Audio response + metrics từng bước

### 4. Chạy Pipeline Hoàn Chỉnh
```bash
python pipeline_full.py
```

## 📊 Metrics Hiển Thị

Mỗi test sẽ hiển thị:
- **Thời gian xử lý từng bước**
- **Tổng thời gian pipeline**
- **Trạng thái API (primary/backup)**
- **Kích thước file input/output**
- **Độ dài text/audio**
- **Chi phí ước tính (nếu có)**

## 🔄 Logic Backup

### STT Backup Logic
1. Thử FPT.AI STT trước
2. Nếu lỗi hoặc vượt quota → chuyển sang OpenAI Whisper
3. Log việc chuyển đổi để theo dõi

### TTS Backup Logic
1. Thử FPT.AI TTS trước
2. Nếu lỗi hoặc vượt quota → chuyển sang Google Cloud TTS
3. Log việc chuyển đổi để theo dõi

## 🛠️ Troubleshooting

### Lỗi API Key
- Kiểm tra API keys trong `config.py`
- Đảm bảo keys không hết hạn
- Kiểm tra quota còn lại

### Lỗi Audio Format
- STT chỉ hỗ trợ: WAV, MP3, M4A
- TTS output: WAV format
- Kiểm tra kích thước file không quá 25MB

### Lỗi Network
- Kiểm tra kết nối internet
- Thử lại sau vài phút nếu API tạm thời không khả dụng

## 📝 Logs

Tất cả logs được lưu trong thư mục `logs/` với format:
- `stt_logs_YYYYMMDD.log`
- `llm_logs_YYYYMMDD.log`
- `tts_logs_YYYYMMDD.log`
- `pipeline_logs_YYYYMMDD.log`

## 💡 Tips Tối Ưu

1. **Giám sát quota**: Theo dõi usage FPT.AI để tránh vượt quota
2. **Cache responses**: LLM responses có thể cache để tiết kiệm
3. **Audio quality**: STT hoạt động tốt hơn với audio chất lượng cao
4. **Text length**: TTS hoạt động tốt với đoạn text ngắn (< 1000 ký tự)

## 📞 Hỗ Trợ

Nếu gặp vấn đề, kiểm tra:
1. File logs để xem lỗi chi tiết
2. API status của từng service
3. Network connectivity
4. File format và size limits
