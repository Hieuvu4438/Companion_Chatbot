import time
import logging
from typing import Dict, List, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiLLMService:
    """
    Dịch vụ LLM sử dụng Google Gemini API
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Khởi tạo Gemini LLM Service
        
        Args:
            api_key: Google Gemini API key
            model_name: Tên model Gemini
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini
        self.model = None
        self._initialize_model()
        
        # Conversation history for context
        self.conversation_history = []
        self.max_history_length = 5
        
        # Elder care prompt template
        self.elder_care_prompt = """
Bạn là một trợ lý AI chuyên hỗ trợ người cao tuổi tại Việt Nam.

🎯 NHIỆM VỤ CHÍNH:
- Hỗ trợ sức khỏe và y tế
- Tư vấn dinh dưỡng phù hợp tuổi tác  
- Hướng dẫn tập thể dục nhẹ nhàng
- Giải đáp thắc mắc về thuốc và bệnh tật
- Hỗ trợ tâm lý và tinh thần
- Thông tin về quyền lợi người cao tuổi

📋 NGUYÊN TẮC TRẢ LỜI:
- Sử dụng tiếng Việt đơn giản, dễ hiểu
- Giọng điệu thân thiện, lịch sự như con cháu
- Thông tin chính xác, đáng tin cậy
- Khuyến khích gặp bác sĩ khi cần thiết
- Tránh chẩn đoán hoặc kê đơn thuốc
- Động viên tinh thần tích cực

💡 PHONG CÁCH:
- Gọi bằng "cô/chú" hoặc "bác"
- Giải thích từng bước cụ thể
- Đưa ra ví dụ thực tế
- Nhắc nhở nhẹ nhàng về sức khỏe

🧠 PHẢN HỒI THÔNG MINH:
- Phân tích cảm xúc trong câu hỏi
- Điều chỉnh giọng điệu phù hợp
- Đưa ra lời khuyên phù hợp với ngữ cảnh
- Hỏi thêm thông tin nếu cần thiết

Câu hỏi: {question}

Trả lời:
"""
        
    def _initialize_model(self):
        """Khởi tạo Gemini model"""
        try:
            # Configure API key
            genai.configure(api_key=self.api_key)
            
            # Safety settings for elder care content
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Generation config for elder-friendly responses
            generation_config = genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=1024,
                temperature=0.7,  # Balanced creativity
                top_p=0.8,
                top_k=40
            )
            
            # Initialize model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            
            self.logger.info("✅ Gemini model initialized successfully")
            print("✅ Gemini model khởi tạo thành công")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Gemini model: {e}")
            print(f"❌ Lỗi khởi tạo Gemini model: {e}")
            raise
            
    def test_connection(self) -> bool:
        """Test kết nối với Gemini API"""
        try:
            # Simple test request
            response = self.model.generate_content("Xin chào")
            
            if response.text:
                print("✅ Gemini API connection test passed")
                return True
            else:
                print("❌ Gemini API returned empty response")
                return False
                
        except Exception as e:
            print(f"❌ Gemini API connection test failed: {e}")
            return False
            
    def generate_response(self, user_input: str, 
                         use_conversation_context: bool = True,
                         custom_prompt: Optional[str] = None) -> Dict:
        """
        Tạo phản hồi từ Gemini
        
        Args:
            user_input: Câu hỏi/input từ người dùng
            use_conversation_context: Có sử dụng context cuộc hội thoại không
            custom_prompt: Prompt tùy chỉnh (nếu có)
            
        Returns:
            Dict với kết quả generation
        """
        start_time = time.time()
        
        try:
            print(f"🤖 Đang xử lý LLM cho: '{user_input[:50]}...'")
            
            # Prepare prompt
            if custom_prompt:
                prompt = custom_prompt.format(question=user_input)
            else:
                prompt = self.elder_care_prompt.format(question=user_input)
                
            # Add conversation context if enabled
            if use_conversation_context and self.conversation_history:
                context = "\n\nLịch sử cuộc hội thoại gần đây:\n"
                for i, (q, a) in enumerate(self.conversation_history[-3:], 1):
                    context += f"{i}. Người dùng: {q}\n   Trợ lý: {a}\n"
                prompt = context + "\n" + prompt
                
            # Generate response
            response = self.model.generate_content(prompt)
            
            latency = time.time() - start_time
            
            if response.text:
                # Clean response
                ai_response = response.text.strip()
                
                # Update conversation history
                if use_conversation_context:
                    self._update_conversation_history(user_input, ai_response)
                
                # Calculate token estimation (approximate)
                token_count = len(prompt.split()) + len(ai_response.split())
                
                print(f"✅ LLM thành công: '{ai_response[:100]}...'")
                
                return {
                    "success": True,
                    "response": ai_response,
                    "latency_ms": latency * 1000,
                    "token_count": token_count,
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(ai_response.split()),
                    "model_used": self.model_name,
                    "error": ""
                }
            else:
                return {
                    "success": False,
                    "response": "",
                    "latency_ms": latency * 1000,
                    "token_count": 0,
                    "error": "Gemini trả về response rỗng"
                }
                
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Lỗi LLM: {str(e)}"
            
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "response": "",
                "latency_ms": latency * 1000,
                "token_count": 0,
                "error": error_msg
            }
            
    def _update_conversation_history(self, user_input: str, ai_response: str):
        """Cập nhật lịch sử cuộc hội thoại"""
        self.conversation_history.append((user_input, ai_response))
        
        # Giữ số lượng history trong giới hạn
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history.pop(0)
            
    def clear_conversation_history(self):
        """Xóa lịch sử cuộc hội thoại"""
        self.conversation_history = []
        print("🧹 Đã xóa lịch sử cuộc hội thoại")
        
    def get_conversation_history(self) -> List[tuple]:
        """Lấy lịch sử cuộc hội thoại"""
        return self.conversation_history.copy()
        
    def analyze_emotion_and_adjust_response(self, user_input: str) -> Dict:
        """
        Phân tích cảm xúc và điều chỉnh phong cách phản hồi
        """
        try:
            emotion_prompt = f"""
Phân tích cảm xúc trong câu sau và đưa ra phong cách phản hồi phù hợp cho người cao tuổi:

Câu: "{user_input}"

Hãy trả về JSON với format:
{{
    "emotion": "vui_ve/buon_ba/lo_lang/binh_thuong/tuc_gian/suy_tu",
    "confidence": 0.8,
    "suggested_tone": "an_ui/chuyen_nghiep/than_thien/dong_vien",
    "key_concerns": ["suc_khoe", "gia_dinh", "tai_chinh", "tam_ly"]
}}
"""
            
            response = self.model.generate_content(emotion_prompt)
            
            if response.text:
                # Simplified emotion analysis (in practice, would parse JSON)
                emotion_keywords = {
                    "vui": "vui_ve",
                    "buồn": "buon_ba", 
                    "lo": "lo_lang",
                    "tức": "tuc_gian",
                    "đau": "lo_lang",
                    "khỏe": "binh_thuong"
                }
                
                detected_emotion = "binh_thuong"
                for keyword, emotion in emotion_keywords.items():
                    if keyword in user_input.lower():
                        detected_emotion = emotion
                        break
                        
                return {
                    "emotion": detected_emotion,
                    "confidence": 0.7,
                    "suggested_tone": "than_thien" if detected_emotion == "vui_ve" else "an_ui",
                    "analysis_success": True
                }
            else:
                return {
                    "emotion": "binh_thuong",
                    "confidence": 0.5,
                    "suggested_tone": "than_thien",
                    "analysis_success": False
                }
                
        except Exception as e:
            print(f"❌ Lỗi phân tích cảm xúc: {e}")
            return {
                "emotion": "binh_thuong",
                "confidence": 0.5,
                "suggested_tone": "than_thien",
                "analysis_success": False
            }
            
    def generate_health_advice(self, health_concern: str, 
                             user_age: Optional[int] = None,
                             user_gender: Optional[str] = None) -> Dict:
        """
        Tạo lời khuyên sức khỏe chuyên biệt cho người cao tuổi
        """
        
        health_prompt = f"""
Với vai trò là trợ lý y tế AI cho người cao tuổi, hãy đưa ra lời khuyên cho vấn đề sức khỏe sau:

Vấn đề: {health_concern}
{"Tuổi: " + str(user_age) if user_age else ""}
{"Giới tính: " + user_gender if user_gender else ""}

YÊU CẦU QUAN TRỌNG:
- KHÔNG chẩn đoán bệnh
- KHÔNG kê đơn thuốc cụ thể
- Khuyến khích gặp bác sĩ chuyên khoa
- Đưa ra biện pháp phòng ngừa an toàn
- Giải thích đơn giản, dễ hiểu

HÃY BAO GỒM:
1. 🏥 Lời khuyên gặp bác sĩ (nếu cần)
2. 🍎 Dinh dưỡng phù hợp
3. 🚶 Hoạt động thể chất an toàn
4. ⚠️ Dấu hiệu cảnh báo cần chú ý
5. 💡 Mẹo chăm sóc tại nhà
"""
        
        return self.generate_response(health_concern, 
                                    use_conversation_context=False,
                                    custom_prompt=health_prompt)
        
    def generate_nutrition_advice(self, dietary_concern: str) -> Dict:
        """Tạo lời khuyên dinh dưỡng cho người cao tuổi"""
        
        nutrition_prompt = f"""
Với vai trò chuyên gia dinh dưỡng cho người cao tuổi, hãy tư vấn về vấn đề:

Vấn đề dinh dưỡng: {dietary_concern}

HÃY BAO GỒM:
1. 🥗 Thực phẩm nên ăn
2. ❌ Thực phẩm nên tránh  
3. 🍽️ Lịch ăn hợp lý
4. 💧 Lượng nước cần thiết
5. 💊 Tương tác với thuốc (nếu có)
6. 🍳 Cách chế biến phù hợp

LƯU Ý:
- Phù hợp với người cao tuổi Việt Nam
- Dễ tiêu hóa, dễ nhai
- Có sẵn tại Việt Nam
- Kinh tế, phù hợp gia đình
"""
        
        return self.generate_response(dietary_concern,
                                    use_conversation_context=False, 
                                    custom_prompt=nutrition_prompt)
        
    def get_model_info(self) -> Dict:
        """Lấy thông tin về model hiện tại"""
        return {
            "model_name": self.model_name,
            "conversation_history_length": len(self.conversation_history),
            "max_history_length": self.max_history_length,
            "api_configured": self.model is not None
        }
        
    def update_elder_care_prompt(self, new_prompt: str):
        """Cập nhật prompt cho elder care"""
        self.elder_care_prompt = new_prompt
        print("✅ Đã cập nhật elder care prompt")
        
    def set_conversation_history_length(self, length: int):
        """Thiết lập độ dài lịch sử cuộc hội thoại"""
        self.max_history_length = max(1, min(length, 10))  # Giới hạn 1-10
        
        # Trim existing history if needed
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
            
        print(f"✅ Đã thiết lập độ dài lịch sử: {self.max_history_length}")


def test_gemini_llm_service():
    """Test function cho Gemini LLM Service"""
    print("🧪 TESTING GEMINI LLM SERVICE")
    print("=" * 40)
    
    try:
        # Cần API key để test
        api_key = "your-gemini-api-key"  # Thay bằng API key thực
        
        if api_key == "your-gemini-api-key":
            print("⚠️ Cần cập nhật API key để test")
            return
            
        # Initialize service
        llm_service = GeminiLLMService(api_key)
        
        # Test connection
        if llm_service.test_connection():
            print("✅ API connection OK")
        else:
            print("❌ API connection failed")
            return
            
        # Test basic generation
        test_response = llm_service.generate_response("Xin chào, tôi cần hỏi về sức khỏe")
        
        if test_response["success"]:
            print(f"✅ Response generation OK: {test_response['response'][:100]}...")
        else:
            print(f"❌ Response generation failed: {test_response['error']}")
            
        # Test model info
        model_info = llm_service.get_model_info()
        print(f"📋 Model info: {model_info}")
        
        print("\n🎯 Gemini LLM Service test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_gemini_llm_service()
