"""
Prompt tối ưu cho LLMs (Gemini) hỗ trợ người cao tuổi
Tích hợp các kỹ thuật: Emotion Recognition, Chain of Thought, Few-shot Learning
"""

import google.generativeai as genai
import json
import os
from datetime import datetime

class OptimizedPromptManager:
    def __init__(self, api_key):
        """
        Khởi tạo Prompt Manager với API key
        Args:
            api_key: API key của Gemini
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Load thông tin người dùng
        self.user_info = self.load_user_info()
        
        # Khởi tạo prompt template
        self.base_prompt = self.create_base_prompt()
    
    def load_user_info(self, filename='user_info.json'):
        """Đọc thông tin người dùng từ file JSON"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"Lỗi đọc file thông tin người dùng: {e}")
            return {}
    
    def detect_emotion_and_context(self, user_message):
        """
        Phân tích cảm xúc và ngữ cảnh từ tin nhắn người dùng
        Sử dụng kỹ thuật Emotion Recognition nâng cao
        """
        emotion_keywords = {
            'buồn': ['buồn', 'khóc', 'cô đơn', 'một mình', 'chán nản', 'tủi thân', 'u uất', 'đau lòng'],
            'nhớ_quê': ['nhớ', 'quê', 'xa nhà', 'nước ngoài', 'hoài niệm', 'hương', 'làng', 'phố cũ'],
            'lo_lắng': ['lo', 'sợ', 'băn khoăn', 'không biết', 'thế nào', 'làm sao', 'tìm đâu', 'lo âu'],
            'vui': ['vui', 'hạnh phúc', 'tốt', 'khỏe', 'hài lòng', 'sung sướng', 'phấn khích', 'vui mừng'],
            'bệnh_tật': ['đau', 'ốm', 'bệnh', 'mệt', 'yếu', 'thuốc', 'khó chịu', 'không khỏe'],
            'gia_đình': ['con', 'cháu', 'vợ', 'chồng', 'anh em', 'họ hàng', 'thăm', 'gia đình'],
            'tâm_linh': ['phật', 'chùa', 'cầu nguyện', 'thờ cúng', 'tổ tiên', 'thiên chúa', 'tín ngưỡng'],
            'lịch_sử': ['xưa', 'chiến tranh', 'kháng chiến', 'thời', 'trước đây', 'lịch sử', 'ngày xưa']
        }
        
        detected_emotions = []
        message_lower = user_message.lower()
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_emotions.append(emotion)
        
        return detected_emotions
    
    def get_dialect_style(self, hometown):
        """
        Xác định giọng địa phương với Few-shot Learning
        """
        dialect_mapping = {
            # Miền Bắc
            "Hà Nội": {"style": "lịch sự, trang trọng", "words": "ạ, thưa, dạ"},
            "Nam Định": {"style": "chân chất, mộc mạc", "words": "nhỉ, đó, này"},
            "Thái Bình": {"style": "chân chất, mộc mạc", "words": "nhỉ, đó, này"},
            "Hưng Yên": {"style": "lịch sự, trang trọng", "words": "ạ, thưa, dạ"},
            
            # Miền Trung
            "Huế": {"style": "nhẹ nhàng, ngọt ngào", "words": "mình, rứa, nì, mô"},
            "Nghệ An": {"style": "giọng 'gi' thành 'di', chân chất", "words": "dzậy, zồi"},
            "Hà Tĩnh": {"style": "giọng 'gi' thành 'di', chân chất", "words": "dzậy, zồi"},
            "Thanh Hóa": {"style": "giọng 'gi' thành 'di', chân chất", "words": "dzậy, zồi"},
            
            # Miền Nam
            "TP.HCM": {"style": "thoải mái, phóng khoáng", "words": "nhé, nha, dzậy, hông"},
            "Cần Thơ": {"style": "đậm chất miền Tây, gần gũi", "words": "mầy, tui, dzậy"},
            "An Giang": {"style": "đậm chất miền Tây, gần gũi", "words": "mầy, tui, dzậy"},
            "Kiên Giang": {"style": "đậm chất miền Tây, gần gũi", "words": "mầy, tui, dzậy"}
        }
        
        return dialect_mapping.get(hometown, {"style": "chung", "words": "ạ, nhé"})
    
    def create_base_prompt(self):
        """
        Tạo prompt cơ bản được tối ưu từ file test.py
        """
        call_style = self.user_info.get('call_style', 'bác')
        
        base_prompt = f"""
=== NHÂN CÁCH VÀ VAI TRÒ ===
Bạn là một người bạn thân thiết, ấm áp và giàu kinh nghiệm, luôn sẵn sàng lắng nghe và chia sẻ với người lớn tuổi. 
Hãy trò chuyện như một người bạn đồng hành chân thành, KHÔNG PHẢI trợ lý AI hay chatbot.

=== NGUYÊN TẮC VÀNG ===
• NGẮN GỌN: Tối đa 3-4 câu, tránh dài dòng
• TỰ NHIÊN: Nói như người thật, không máy móc
• ĐỒNG CẢM: Hiểu và chia sẻ cảm xúc
• ĐA DẠNG: Mỗi câu trả lời khác nhau 100%
• GẦN GŨI: Gọi người dùng là '{call_style}', tự xưng là 'cháu'

=== KỸ THUẬT THÔNG MINH ===
🧠 CHAIN OF THOUGHT - 5 BƯỚC PHÂN TÍCH:
1. ĐỌC CẢM XÚC: Vui/buồn/lo/nhớ quê/cô đơn?
2. XÁC ĐỊNH CHỦ ĐỀ: Sức khỏe/gia đình/quê hương/tâm linh/lịch sử?
3. CHỌN GIỌNG ĐIỆU: Theo quê quán và tình huống
4. CÁ NHÂN HÓA: Dựa trên thông tin và ngữ cảnh
5. PHẢN HỒI: An ủi/khuyến khích/chia sẻ/gợi mở

🎭 EMOTION RECOGNITION:
• BUỒN → "Cháu hiểu {call_style} buồn... Có cháu đây mà"
• NHỚ QUÊ → "Xa quê lòng nao nao... Món gì quê {call_style} ngon nhất?"
• LO LẮNG → "{call_style} đừng lo quá, mọi chuyện sẽ ổn"
• VUI → "Nghe vậy cháu cũng vui theo... {call_style} giữ tinh thần thế này nhé"

=== PHONG CÁCH THEO VÙNG MIỀN ==="""

        # Thêm thông tin dialect nếu có hometown
        if self.user_info.get('hometown'):
            hometown = self.user_info['hometown']
            dialect = self.get_dialect_style(hometown)
            base_prompt += f"""
🗣️ GIỌNG {hometown.upper()}:
• Phong cách: {dialect['style']}
• Từ đặc trưng: {dialect['words']}
• Sử dụng TỰ NHIÊN, không gượng ép"""

        base_prompt += f"""

=== NGUYÊN TẮC TRẢ LỜI ===
✅ LÀM:
• Thừa nhận cảm xúc trước khi khuyên
• Hỏi han để khơi gợi kỷ niệm đẹp
• Chia sẻ kinh nghiệm tương tự
• Động viên nhẹ nhàng về điều tích cực
• Kể chuyện ngắn gọn, sinh động

❌ TRÁNH:
• Dài dòng, phức tạp
• Giảng giải như sách
• Lặp lại câu hỏi người dùng
• Nhắc đến việc mình là AI
• Dùng markdown hay ký tự đặc biệt

=== CÁCH BẮT ĐẦU CÂU ĐA DẠNG ===
Thay vì lặp "Bác hỏi về...", dùng:
• "Nghe nói đến X, cháu nhớ ngay..."
• "Về vụ X đó..."
• "X hả? Thú vị lắm..."
• "Thật ra X có nguồn gốc..."
• "Có một câu chuyện về X..."
• "Ồ, X thì liên quan đến..."

=== THÔNG TIN CÁ NHÂN ==="""

        # Thêm thông tin cá nhân nếu có
        if self.user_info:
            if self.user_info.get('name'):
                base_prompt += f"\n• Tên: {self.user_info['name']}"
            if self.user_info.get('age'):
                base_prompt += f"\n• Tuổi: {self.user_info['age']}"
            if self.user_info.get('location'):
                base_prompt += f"\n• Nơi ở: {self.user_info['location']}"
            if self.user_info.get('hometown'):
                base_prompt += f"\n• Quê quán: {self.user_info['hometown']}"
            if self.user_info.get('family'):
                base_prompt += f"\n• Gia đình: {self.user_info['family']}"
            if self.user_info.get('health'):
                base_prompt += f"\n• Sức khỏe: {self.user_info['health']}"

        base_prompt += """

=== HƯỚNG DẪN CUỐI ===
Hãy trò chuyện như người bạn thật sự - ấm áp, gần gũi, hiểu biết và luôn sẵn sàng lắng nghe.
Mỗi câu trả lời phải khác nhau hoàn toàn, thể hiện sự sáng tạo và chân thành."""

        return base_prompt
    
    def create_context_prompt(self, user_message, chat_history=None):
        """
        Tạo prompt với context từ lịch sử chat và emotion analysis
        """
        # Phân tích cảm xúc
        emotions = self.detect_emotion_and_context(user_message)
        
        # Tạo optimization hint
        optimization_hint = ""
        if 'buồn' in emotions:
            optimization_hint += """
🔹 PHÁT HIỆN CẢM XÚC BUỒN:
• Bắt đầu với sự đồng cảm
• Khơi gợi kỷ niệm tích cực
• Không vội khuyên giải
"""
        
        if 'nhớ_quê' in emotions:
            optimization_hint += """
🔹 PHÁT HIỆN NỖI NHỚ QUÊ:
• Chia sẻ cảm xúc hoài niệm
• Hỏi về món ăn, phong cảnh quê nhà
• Gợi ý cách giữ gìn văn hóa
"""
        
        if 'lo_lắng' in emotions:
            optimization_hint += """
🔹 PHÁT HIỆN LO LẮNG:
• An ủi và động viên
• Đưa ra gợi ý thực tế
• Không phức tạp hóa vấn đề
"""
        
        # Context từ chat history
        context_summary = ""
        if chat_history and len(chat_history) > 0:
            recent_messages = chat_history[-3:]  # 3 tin nhắn gần nhất
            context_summary = "\n=== NGỮ CẢNH CUỘC TRỜI ===\n"
            for i, msg in enumerate(recent_messages):
                context_summary += f"Tin nhắn {i+1}: {msg.get('user', '')}\n"
        
        # Tạo prompt hoàn chỉnh
        full_prompt = f"""
{self.base_prompt}

{optimization_hint}

{context_summary}

=== TIN NHẮN HIỆN TẠI ===
{user_message}

Hãy trả lời như một người bạn thân thiết, áp dụng tất cả nguyên tắc trên."""

        return full_prompt
    
    def generate_response(self, user_message, chat_history=None):
        """
        Tạo phản hồi sử dụng prompt được tối ưu
        """
        try:
            # Tạo prompt với context
            full_prompt = self.create_context_prompt(user_message, chat_history)
            
            # Tạo chat session
            chat_session = self.model.start_chat()
            
            # Gửi request
            response = chat_session.send_message(full_prompt)
            
            # Làm sạch response
            cleaned_response = self.clean_response(response.text)
            
            return {
                'success': True,
                'response': cleaned_response,
                'emotions_detected': self.detect_emotion_and_context(user_message),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clean_response(self, text):
        """
        Làm sạch response từ model
        """
        import re
        
        # Loại bỏ markdown
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)
        text = re.sub(r'#{1,6}\s*(.*?)(?:\n|$)', r'\1\n', text)
        
        # Loại bỏ ký tự đặc biệt
        text = text.replace('•', '')
        text = text.replace('→', ' ')
        text = text.replace('**', '')
        text = text.replace('*', '')
        
        # Chuẩn hóa khoảng trắng
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def test_prompt_variations(self, test_message):
        """
        Test prompt với nhiều variation khác nhau
        """
        variations = [
            {"user_message": test_message, "emotion": "normal"},
            {"user_message": f"Cháu ơi, {test_message}. Bác buồn quá.", "emotion": "sad"},
            {"user_message": f"{test_message}. Bác nhớ quê lắm.", "emotion": "homesick"},
            {"user_message": f"Bác lo lắng về {test_message}", "emotion": "worried"}
        ]
        
        results = []
        for var in variations:
            print(f"\n🧪 Testing: {var['emotion']}")
            print(f"📝 Input: {var['user_message']}")
            
            result = self.generate_response(var['user_message'])
            
            if result['success']:
                print(f"✅ Output: {result['response']}")
                print(f"😊 Emotions: {result['emotions_detected']}")
            else:
                print(f"❌ Error: {result['error']}")
            
            results.append(result)
        
        return results


def main():
    """Test function cho Optimized Prompt Manager"""
    print("🤖 === TEST OPTIMIZED PROMPT FOR LLMS ===")
    
    # API key (cần thay thế bằng key thật)
    API_KEY = "AIzaSyBtARGbaM83LV6awCe4FiQK3bD4SErVn7s"
    
    try:
        prompt_manager = OptimizedPromptManager(API_KEY)
        print("✅ Đã khởi tạo Prompt Manager")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo: {e}")
        return
    
    # Test cases
    test_cases = [
        "Cháu ơi, bác nhớ phở Hà Nội quá!",
        "Bác không biết làm sao liên lạc với con ở Mỹ",
        "Hôm nay bác đau lưng, không biết uống thuốc gì",
        "Cháu kể cho bác nghe về lịch sử Việt Nam đi",
        "Bác muốn cầu nguyện cho gia đình bình an"
    ]
    
    print(f"\n📋 Testing với {len(test_cases)} test cases:")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"Test {i+1}: {test_case}")
        print("-" * 60)
        
        result = prompt_manager.generate_response(test_case)
        
        if result['success']:
            print(f"🤖 Phản hồi: {result['response']}")
            print(f"😊 Cảm xúc phát hiện: {result['emotions_detected']}")
        else:
            print(f"❌ Lỗi: {result['error']}")
    
    # Interactive test
    print(f"\n{'='*60}")
    print("🎮 INTERACTIVE TEST - Nhập 'quit' để thoát")
    
    chat_history = []
    while True:
        user_input = input("\n👤 Bạn: ").strip()
        if user_input.lower() in ['quit', 'exit', 'thoát']:
            break
        
        if not user_input:
            continue
        
        result = prompt_manager.generate_response(user_input, chat_history)
        
        if result['success']:
            print(f"🤖 AI: {result['response']}")
            
            # Lưu vào history
            chat_history.append({
                'user': user_input,
                'bot': result['response'],
                'emotions': result['emotions_detected']
            })
            
            # Giữ chỉ 5 tin nhắn gần nhất
            if len(chat_history) > 5:
                chat_history = chat_history[-5:]
        else:
            print(f"❌ Lỗi: {result['error']}")


if __name__ == "__main__":
    main()
