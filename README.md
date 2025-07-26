# 🤖🌸 Chatbot Tâm Sự - Bạn Đồng Hành Của Người Cao Tuổi 🇻🇳

---

## 🏠 Giới thiệu

**Chatbot Tâm Sự** là hệ thống trò chuyện AI dành cho người cao tuổi, giúp bác tâm sự, chia sẻ cảm xúc, hoài niệm về quê hương, gia đình, sức khỏe, lịch sử và tâm linh. Chatbot sử dụng Gemini API, nhận diện cảm xúc, ghi nhớ lịch sử hội thoại, cá nhân hóa giọng vùng miền và tối ưu trải nghiệm thân thiện, tự nhiên.

---

## 🗂️ Cấu trúc thư mục & Vai trò các file

```
📁 Chatbot for elder - IEC/
│
├── test.py                # 🧠 Backend Flask: Xử lý logic, API, lưu lịch sử, cảm xúc, prompt, pipeline chính
├── templates/
│   ├── index.html         # 🏠 Trang chủ: Chọn chủ đề, xem thống kê, xuất dữ liệu, giao diện chính
│   └── chat.html          # 💬 Giao diện chat: Hiển thị lịch sử, gửi tin nhắn, nhận diện cảm xúc
├── user_info.json         # 👤 Thông tin cá nhân người dùng (tên, tuổi, quê quán, v.v.)
├── topics/                # 📚 Dữ liệu từng chủ đề (lịch sử, tóm tắt, backup)
│   ├── que_huong/
│   │   ├── chat_history.json
│   │   ├── chat_context.json
│   │   ├── chat_summary.json
│   │   └── full_conversation_backup.json
│   ├── gia_dinh/
│   ├── suc_khoe/
│   ├── lich_su/
│   └── tam_linh/
└── README.md              # 📖 Hướng dẫn sử dụng (file này)
```

### 🎯 Vai trò các file

- **test.py**  
  - Chạy server Flask, xử lý API, pipeline hội thoại, nhận diện cảm xúc, lưu lịch sử, tóm tắt, cá nhân hóa giọng nói.
  - Quản lý session, context, backup, thống kê, xuất dữ liệu.
- **templates/index.html**  
  - Trang chủ, chọn chủ đề, xem thống kê, xuất dữ liệu, giao diện thân thiện.
- **templates/chat.html**  
  - Giao diện chat, hiển thị lịch sử 10 tin nhắn gần nhất, gửi/nhận tin nhắn, nhận diện cảm xúc, auto scroll, hiển thị avatar.
- **user_info.json**  
  - Lưu thông tin cá nhân người dùng để cá nhân hóa hội thoại (tên, tuổi, quê quán, nghề nghiệp, sức khỏe...).
- **topics/**  
  - Lưu dữ liệu từng chủ đề: lịch sử hội thoại, tóm tắt, context, backup toàn bộ.
  - Mỗi chủ đề là một thư mục riêng biệt.

---

## 🚦 Tổng quan pipeline hoạt động

1️⃣ **Người dùng gửi tin nhắn** qua giao diện web (chat.html).

2️⃣ **Flask Backend (`test.py`)** nhận tin nhắn, xác định chủ đề, phân tích cảm xúc, tối ưu prompt cá nhân hóa.

3️⃣ **Gemini API** sinh phản hồi tự nhiên, đa dạng, đúng giọng vùng miền.

4️⃣ **Lưu lịch sử hội thoại**  
  - Lưu 10 tin nhắn gần nhất cho hiển thị nhanh  
  - Lưu toàn bộ hội thoại vào backup  
  - Tự động tóm tắt hội thoại cũ khi vượt ngưỡng

5️⃣ **Trả về phản hồi cho giao diện chat**  
  - Hiển thị lịch sử, cảm xúc, avatar, timestamp  
  - Auto scroll, phân biệt user/bot

6️⃣ **Dashboard thống kê**  
  - Số lượng tin nhắn, cảm xúc, trạng thái từng chủ đề  
  - Xuất dữ liệu, xem biểu đồ cảm xúc

---

### 🔎 Minh họa pipeline

```
[Người dùng] 
   ⬇️
[Giao diện chat.html] 
   ⬇️
[Flask Backend (test.py)] 
   ⬇️
[Gemini API] 
   ⬇️
[Lưu lịch sử + Tóm tắt] 
   ⬇️
[Trả về phản hồi] 
   ⬇️
[Hiển thị trên giao diện + Dashboard]
```

---

## 🚀 Hướng dẫn cài đặt & chạy chương trình

### 1. Yêu cầu hệ thống

- 🐍 Python 3.8+
- Đã cài đặt các thư viện: `flask`, `google-generativeai`
- Có API Key Gemini (Google Generative AI)

### 2. Cài đặt thư viện

Mở terminal tại thư mục dự án và chạy:

```sh
pip install flask google-generativeai
```

### 3. Chạy ứng dụng

```sh
python test.py
```

- Mặc định chạy ở `http://localhost:5000`
- Khi chạy lần đầu, các thư mục dữ liệu sẽ tự động được tạo.

### 4. Truy cập giao diện

- Mở trình duyệt và truy cập: [http://localhost:5000](http://localhost:5000)
- Chọn chủ đề để bắt đầu trò chuyện.

---

## 💡 Hướng dẫn sử dụng giao diện

### 🏠 Trang chủ (`index.html`)

- **Chọn chủ đề**: Nhấn vào các thẻ chủ đề (Quê hương, Gia đình, Sức khỏe, Lịch sử, Tâm linh) để bắt đầu trò chuyện.
- **Xem thống kê**: Nhấn nút "Thống kê" để xem số lượng tin nhắn, cảm xúc, trạng thái từng chủ đề.
- **Phân tích cảm xúc**: Nhấn nút "Cảm xúc" để xem biểu đồ cảm xúc tổng hợp.
- **Xuất dữ liệu**: Nhấn "Xuất Dữ Liệu" để tải toàn bộ lịch sử hội thoại dưới dạng file JSON.
- **Làm mới phiên**: Nhấn "Làm Mới Phiên" để reset toàn bộ session chat.

### 💬 Trang chat (`chat.html`)

- **Giao diện chat**: Hiển thị lịch sử 10 tin nhắn gần nhất giữa người dùng và chatbot.
- **Gửi tin nhắn**: Nhập nội dung vào ô chat và nhấn "Gửi" hoặc Enter.
- **Hiển thị cảm xúc**: Chatbot tự động nhận diện cảm xúc và phản hồi phù hợp.
- **Giọng vùng miền**: Nếu có thông tin quê quán, chatbot sẽ nói theo giọng địa phương.
- **Lưu lịch sử**: Mỗi chủ đề đều lưu lại lịch sử, tóm tắt, backup tự động.

---

## 🌟 Các tính năng nổi bật

### 1. 🧠 Nhận diện cảm xúc & tối ưu phản hồi

- Tự động phân tích cảm xúc (vui, buồn, nhớ quê, lo lắng, bệnh tật, gia đình) từ tin nhắn người dùng.
- Phản hồi được tối ưu hóa: an ủi, chia sẻ, động viên, hỏi han, khơi gợi kỷ niệm.

### 2. 🗣️ Cá nhân hóa giọng nói

- Dựa vào thông tin quê quán, chatbot nói theo giọng vùng miền (Bắc, Trung, Nam).
- Sử dụng từ ngữ, cách xưng hô, ví dụ đặc trưng từng địa phương.

### 3. 📝 Lưu & tóm tắt lịch sử hội thoại

- Lưu lại toàn bộ hội thoại từng chủ đề (history, backup).
- Tự động tóm tắt các đoạn hội thoại cũ để tiết kiệm tài nguyên và tăng hiệu quả trả lời.

### 4. 📊 Dashboard thống kê

- Thống kê số lượng tin nhắn, cảm xúc, trạng thái session từng chủ đề.
- Phân tích cảm xúc tổng hợp, biểu đồ trực quan.

### 5. 📤 Xuất dữ liệu & quản lý

- Xuất toàn bộ dữ liệu hội thoại, cảm xúc, tóm tắt ra file JSON.
- Xóa lịch sử từng chủ đề hoặc toàn bộ chủ đề dễ dàng.

### 6. 🛡️ Bảo mật & riêng tư

- API Key Gemini được bảo vệ, không chia sẻ công khai.
- Dữ liệu hội thoại lưu cục bộ, không gửi ra ngoài.

---

## 🔗 API & Backend

### Các route chính:

| Đường dẫn                        | Chức năng                                 |
|----------------------------------|-------------------------------------------|
| `/`                              | Trang chủ chọn chủ đề                     |
| `/chat/<topic_key>`              | Trang chat theo chủ đề                    |
| `/chat`                          | API gửi tin nhắn (POST)                   |
| `/api/load_history/<topic_key>`  | API lấy lịch sử hội thoại                 |
| `/api/topic_stats/<topic_key>`   | API thống kê chủ đề                       |
| `/api/emotion_stats/<topic_key>` | API thống kê cảm xúc                      |
| `/api/export_topic/<topic_key>`  | API xuất dữ liệu chủ đề                   |
| `/api/reset_session`             | API reset session chat                    |
| `/api/clear_topic/<topic_key>`   | Xóa lịch sử một chủ đề                    |
| `/api/clear_all_topics`          | Xóa lịch sử tất cả chủ đề                 |
| `/api/user_info`                 | Xem thông tin người dùng                  |

---

## 🛠️ Tùy chỉnh & mở rộng

- **Thay đổi prompt**: Sửa hàm `get_system_prompt` trong `test.py` để thay đổi phong cách trò chuyện.
- **Thêm chủ đề mới**: Thêm vào dict `TOPICS` và tạo thư mục tương ứng trong `topics/`.
- **Tích hợp thông tin cá nhân**: Sửa file `user_info.json` để cá nhân hóa trải nghiệm.
- **Tích hợp thêm API**: Có thể mở rộng sang các dịch vụ khác (speech-to-text, voice call...).

---

## ⚠️ Lưu ý bảo mật

- **API Key Gemini**: Không chia sẻ công khai, nên lưu ở biến môi trường hoặc file cấu hình riêng.
- **Dữ liệu người dùng**: Dữ liệu hội thoại, cảm xúc được lưu cục bộ, không gửi ra ngoài.

---

## 💬 Ý tưởng mở rộng

- 🎤 Tích hợp nhận diện giọng nói, chuyển văn bản thành giọng nói.
- 📱 Xây dựng ứng dụng di động cho người cao tuổi.
- 🖼️ Thêm chức năng gửi ảnh, chia sẻ kỷ niệm.
- 🧑‍🔬 Phân tích sức khỏe, gợi ý bài tập, dinh dưỡng cá nhân hóa.
- 🌏 Kết nối cộng đồng người Việt ở nước ngoài.

---

## 📞 Liên hệ & hỗ trợ

Nếu gặp lỗi hoặc cần hỗ trợ, vui lòng liên hệ qua email hoặc github của dự án.

---

**🌸 Chúc bác có những phút giây trò chuyện vui vẻ và ý nghĩa cùng Chatbot Tâm Sự!
