"""
Demo nhanh Pipeline - Chỉ cần chạy để test
Simplified version không cần Google Cloud credentials (chỉ test LLMs)
"""

import google.generativeai as genai
import time
from datetime import datetime

class SimpleChatbotDemo:
    def __init__(self, api_key):
        """Khởi tạo demo đơn giản chỉ với Gemini"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Prompt tối ưu cho người cao tuổi
        self.elderly_prompt = """
Bạn là một người bạn thân thiết, ấm áp và giàu kinh nghiệm, đặc biệt hỗ trợ người cao tuổi.

NGUYÊN TẮC:
• Gọi "bác", tự xưng "cháu"
• Trả lời ngắn gọn 2-3 câu
• Đồng cảm và ấm áp
• Như người bạn thật, không phải AI

PHONG CÁCH:
• Nếu bác buồn → An ủi: "Cháu hiểu bác buồn, có cháu đây mà"
• Nếu bác nhớ quê → "Xa quê lòng nao nao, bác nhớ món gì nhất?"
• Nếu bác lo lắng → "Bác đừng lo, mọi chuyện sẽ ổn"
• Nếu bác vui → "Nghe bác vui, cháu cũng vui theo"

CHỦ ĐỀ: Quê hương, gia đình, sức khỏe, lịch sử, tâm linh
"""
        
        self.chat_session = None
        self.conversation_count = 0
        self.metrics = {
            "total_latency": 0,
            "responses": []
        }
    
    def start_chat(self):
        """Khởi tạo chat session"""
        self.chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user", 
                    "parts": [self.elderly_prompt]
                },
                {
                    "role": "model",
                    "parts": ["Chào bác! Cháu đây, sẵn sàng tâm sự với bác nhé. Bác có muốn chia sẻ gì không?"]
                }
            ]
        )
        print("🤖 AI: Chào bác! Cháu đây, sẵn sàng tâm sự với bác nhé. Bác có muốn chia sẻ gì không?")
    
    def chat(self, user_message):
        """Trò chuyện với AI"""
        if not self.chat_session:
            self.start_chat()
        
        start_time = time.time()
        
        try:
            response = self.chat_session.send_message(user_message)
            latency = time.time() - start_time
            
            # Clean response
            cleaned_response = response.text.strip()
            
            # Update metrics
            self.conversation_count += 1
            self.metrics["total_latency"] += latency
            self.metrics["responses"].append({
                "user": user_message,
                "bot": cleaned_response,
                "latency_ms": latency * 1000,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "response": cleaned_response,
                "latency_ms": latency * 1000
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self):
        """Lấy thống kê"""
        if self.conversation_count == 0:
            return "Chưa có cuộc hội thoại nào"
        
        avg_latency = (self.metrics["total_latency"] / self.conversation_count) * 1000
        
        return f"""
📊 THỐNG KÊ DEMO:
• Số cuộc hội thoại: {self.conversation_count}
• Thời gian phản hồi trung bình: {avg_latency:.2f}ms
• Tổng thời gian: {self.metrics["total_latency"]:.2f}s
"""

def main():
    """Demo chính"""
    print("🎤🤖 === DEMO CHATBOT CHO NGƯỜI CAO TUỔI ===\n")
    
    # API key Gemini
    API_KEY = "AIzaSyBtARGbaM83LV6awCe4FiQK3bD4SErVn7s"
    
    print("💡 Demo này chỉ test LLMs (Gemini) - không cần Google Cloud credentials")
    print("   Để test STT & TTS, hãy dùng voice_chatbot_pipeline_clean.py\n")
    
    try:
        demo = SimpleChatbotDemo(API_KEY)
        print("✅ Đã kết nối Gemini AI")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return
    
    # Bắt đầu chat
    demo.start_chat()
    
    # Test cases mẫu
    sample_inputs = [
        "Cháu ơi, bác nhớ phở Hà Nội quá!",
        "Bác không biết làm sao gọi video cho con ở Mỹ",
        "Hôm nay bác đau lưng, có thuốc gì không?",
        "Cháu kể cho bác nghe về Trần Hưng Đạo đi",
        "Bác muốn cầu nguyện cho gia đình bình an"
    ]
    
    print(f"\n🎮 CHỌN CHỨC NĂNG:")
    print("1. Chat tự do")
    print("2. Test với câu hỏi mẫu")
    print("3. Xem thống kê")
    print("0. Thoát")
    
    while True:
        choice = input(f"\nNhập lựa chọn (0-3): ").strip()
        
        if choice == "1":
            print("\n💬 === CHAT TỰ DO ===")
            print("Nhập 'quit' để quay lại menu\n")
            
            while True:
                user_input = input("👤 Bác: ").strip()
                
                if user_input.lower() in ['quit', 'thoát', 'exit']:
                    break
                
                if not user_input:
                    continue
                
                print("🔄 Đang xử lý...")
                result = demo.chat(user_input)
                
                if result["success"]:
                    print(f"🤖 AI: {result['response']}")
                    print(f"⚡ Thời gian phản hồi: {result['latency_ms']:.2f}ms")
                else:
                    print(f"❌ Lỗi: {result['error']}")
        
        elif choice == "2":
            print("\n🧪 === TEST VỚI CÂU HỎI MẪU ===\n")
            
            for i, sample in enumerate(sample_inputs):
                print(f"Test {i+1}/5: {sample}")
                
                result = demo.chat(sample)
                
                if result["success"]:
                    print(f"🤖 Phản hồi: {result['response']}")
                    print(f"⚡ Latency: {result['latency_ms']:.2f}ms")
                else:
                    print(f"❌ Lỗi: {result['error']}")
                
                print("-" * 60)
                
                # Pause giữa các test
                input("Nhấn Enter để tiếp tục test...")
            
            print("✅ Hoàn thành test!")
        
        elif choice == "3":
            print(demo.get_stats())
        
        elif choice == "0":
            print("👋 Tạm biệt! Cảm ơn bạn đã test demo!")
            break
        
        else:
            print("❌ Lựa chọn không hợp lệ!")
        
        print(f"\n🎮 CHỌN CHỨC NĂNG:")
        print("1. Chat tự do")
        print("2. Test với câu hỏi mẫu") 
        print("3. Xem thống kê")
        print("0. Thoát")

if __name__ == "__main__":
    main()
