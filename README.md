# Companion Chatbot for Elderly

Một hệ thống chatbot AI được thiết kế đặc biệt để hỗ trợ người cao tuổi với các tính năng nhận diện giọng nói, xử lý ngôn ngữ tự nhiên và tổng hợp giọng nói.

## Cấu trúc dự án

Dự án được tổ chức thành các pipeline độc lập:

- **pipeline1/**: Pipeline cơ bản với voice chatbot
- **pipeline3/**: Pipeline đầy đủ với các module STT, LLM, TTS
- **pipeline4/**: Pipeline tối ưu với demo và quick start
- **pipeline5/**: Pipeline hoàn chỉnh với đầy đủ tính năng

## Yêu cầu hệ thống

- Python 3.8+
- Các dependencies được liệt kê trong file `requirements.txt` của từng pipeline

## Cài đặt và sử dụng

1. Clone repository:
```bash
git clone https://github.com/Hieuvu4438/Companion_Chatbot.git
cd Companion_Chatbot
```

2. Chọn pipeline phù hợp và làm theo hướng dẫn trong README của pipeline đó.

3. Mỗi pipeline có file `requirements.txt` riêng, cài đặt dependencies:
```bash
cd pipeline[X]
pip install -r requirements.txt
```

## Tính năng chính

- 🎤 **Nhận diện giọng nói** (STT - Speech to Text)
- 🧠 **Xử lý ngôn ngữ tự nhiên** với AI models
- 🔊 **Tổng hợp giọng nói** (TTS - Text to Speech)
- 👥 **Tối ưu cho người cao tuổi** với giao diện thân thiện
- 🔧 **Modular design** cho dễ dàng bảo trì và mở rộng

## Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo issue hoặc pull request.

## License

[Thêm thông tin license nếu cần]
