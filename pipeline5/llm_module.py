#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini LLMs Module
==================

Large Language Model module sử dụng Google Gemini API cho pipeline chatbot hỗ trợ người cao tuổi
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Optional, List, Any, Tuple

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai không được cài đặt. Chạy: pip install google-generativeai")
    sys.exit(1)

try:
    from config import *
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import *


class GeminiLLM:
    """Google Gemini Language Model service"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required")
            
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Conversation history for context
        self.conversation_history = []
        self.max_history = MAX_CONVERSATION_HISTORY
        
        # Generation config
        self.generation_config = {
            "temperature": GEMINI_TEMPERATURE,
            "top_p": GEMINI_TOP_P,
            "top_k": GEMINI_TOP_K,
            "max_output_tokens": GEMINI_MAX_TOKENS,
        }
        
        # Safety settings (relaxed for elder care context)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    
    def test_connection(self) -> bool:
        """Test kết nối với Gemini API"""
        try:
            # Simple test prompt
            response = self.model.generate_content(
                "Xin chào",
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            return response.text is not None
        except Exception:
            return False
    
    def get_elder_care_prompt(self, user_input: str) -> str:
        """
        Tạo prompt tối ưu cho việc hỗ trợ người cao tuổi
        
        Args:
            user_input: Input từ người dùng
            
        Returns:
            Prompt đã được tối ưu
        """
        # Base prompt từ config
        base_prompt = ELDER_CARE_PROMPT
        
        # Thêm context từ conversation history
        context = ""
        if self.conversation_history:
            context = "\\n\\nNGỮ CẢNH CUỘC TRƯỚC:\\n"
            for exchange in self.conversation_history[-3:]:  # Chỉ lấy 3 lượt cuối
                context += f"Người dùng: {exchange['user']}\\n"
                context += f"Bạn: {exchange['assistant']}\\n"
        
        # Phân tích cảm xúc đơn giản
        emotion_context = self._detect_emotion_keywords(user_input)
        
        full_prompt = f"""{base_prompt}

{context}

{emotion_context}

Câu hỏi hiện tại: {user_input}

Hãy trả lời một cách ấm áp, gần gũi như một người cháu đang nói chuyện với ông bà:"""

        return full_prompt
    
    def _detect_emotion_keywords(self, text: str) -> str:
        """Phát hiện từ khóa cảm xúc đơn giản"""
        text_lower = text.lower()
        
        emotion_context = ""
        
        # Cảm xúc buồn
        sad_keywords = ["buồn", "khóc", "cô đơn", "một mình", "chán nản", "tủi thân"]
        if any(keyword in text_lower for keyword in sad_keywords):
            emotion_context += "\\n⚠️ NGƯỜI DÙNG CÓ VẺ BUỒN - Hãy an ủi nhẹ nhàng và động viên tích cực."
        
        # Nhớ quê
        homesick_keywords = ["nhớ", "quê", "xa nhà", "hoài niệm", "xa xứ"]
        if any(keyword in text_lower for keyword in homesick_keywords):
            emotion_context += "\\n🏠 NGƯỜI DÙNG NHỚ QUÊ - Chia sẻ về quê hương và văn hóa truyền thống."
        
        # Lo lắng
        worry_keywords = ["lo", "sợ", "băn khoăn", "không biết", "thế nào"]
        if any(keyword in text_lower for keyword in worry_keywords):
            emotion_context += "\\n😟 NGƯỜI DÙNG LO LẮNG - Đưa ra lời khuyên thực tế và động viên."
        
        # Vui vẻ
        happy_keywords = ["vui", "hạnh phúc", "tốt", "khỏe", "vui mừng"]
        if any(keyword in text_lower for keyword in happy_keywords):
            emotion_context += "\\n😊 NGƯỜI DÙNG VUI VẺ - Chia vui và khuyến khích duy trì tinh thần tích cực."
        
        # Sức khỏe
        health_keywords = ["đau", "ốm", "bệnh", "mệt", "thuốc", "khó chịu"]
        if any(keyword in text_lower for keyword in health_keywords):
            emotion_context += "\\n💊 VẤN ĐỀ SỨC KHỎE - Quan tâm và khuyên nên gặp bác sĩ nếu cần."
        
        return emotion_context
    
    def generate_response(self, user_input: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Tạo response từ Gemini
        
        Args:
            user_input: Input từ người dùng
            custom_prompt: Prompt tùy chỉnh (optional)
            
        Returns:
            Dict chứa response và metrics
        """
        start_time = time.time()
        
        try:
            # Sanitize input
            if SANITIZE_USER_INPUT:
                user_input = self._sanitize_input(user_input)
            
            # Tạo prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self.get_elder_care_prompt(user_input)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            latency = (time.time() - start_time) * 1000
            
            # Process response
            if response.text:
                response_text = self._clean_response(response.text)
                
                # Cập nhật conversation history
                if ENABLE_CONVERSATION_CONTEXT:
                    self._update_conversation_history(user_input, response_text)
                
                return {
                    "success": True,
                    "response": response_text,
                    "latency_ms": latency,
                    "prompt_tokens": len(prompt.split()),
                    "response_tokens": len(response_text.split()),
                    "model_used": GEMINI_MODEL,
                    "safety_ratings": getattr(response, 'safety_ratings', []),
                    "finish_reason": getattr(response, 'finish_reason', 'STOP')
                }
            else:
                return {
                    "success": False,
                    "error": "Empty response from Gemini",
                    "latency_ms": latency,
                    "safety_ratings": getattr(response, 'safety_ratings', [])
                }
                
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "latency_ms": latency
            }
    
    def _sanitize_input(self, text: str) -> str:
        """Làm sạch input từ người dùng"""
        # Loại bỏ ký tự đặc biệt nguy hiểm
        import re
        text = re.sub(r'[<>"\']', '', text)
        
        # Giới hạn độ dài
        if len(text) > 500:
            text = text[:500] + "..."
        
        return text.strip()
    
    def _clean_response(self, text: str) -> str:
        """Làm sạch response từ Gemini"""
        import re
        
        # Loại bỏ markdown cơ bản
        text = re.sub(r'\\*{1,3}(.*?)\\*{1,3}', r'\\1', text)  # Bold, italic
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\\1', text)      # Code
        text = re.sub(r'#{1,6}\\s*(.*?)(?:\\n|$)', r'\\1\\n', text)  # Headers
        
        # Loại bỏ một số ký tự markdown
        text = text.replace('**', '')
        text = text.replace('*', '')
        text = text.replace('`', '')
        
        # Chuẩn hóa khoảng trắng
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\\n{3,}', '\\n\\n', text)
        
        return text.strip()
    
    def _update_conversation_history(self, user_input: str, assistant_response: str):
        """Cập nhật lịch sử hội thoại"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response
        })
        
        # Giới hạn số lượng lịch sử
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def clear_conversation_history(self):
        """Xóa lịch sử hội thoại"""
        self.conversation_history = []
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Lấy tóm tắt cuộc hội thoại"""
        if not self.conversation_history:
            return {
                "success": True,
                "total_exchanges": 0,
                "summary": "Chưa có cuộc hội thoại nào"
            }
        
        try:
            # Tạo prompt tóm tắt
            summary_prompt = "Hãy tóm tắt ngắn gọn cuộc hội thoại sau đây:\\n\\n"
            
            for exchange in self.conversation_history:
                summary_prompt += f"Người dùng: {exchange['user']}\\n"
                summary_prompt += f"Trợ lý: {exchange['assistant']}\\n\\n"
            
            summary_prompt += "Tóm tắt chủ đề chính và những điểm quan trọng trong cuộc hội thoại (tối đa 100 từ):"
            
            # Generate summary
            response = self.model.generate_content(
                summary_prompt,
                generation_config={"temperature": 0.3, "max_output_tokens": 200}
            )
            
            if response.text:
                return {
                    "success": True,
                    "total_exchanges": len(self.conversation_history),
                    "summary": response.text.strip(),
                    "first_exchange_time": self.conversation_history[0]["timestamp"],
                    "last_exchange_time": self.conversation_history[-1]["timestamp"]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate summary"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Summary generation failed: {str(e)}"
            }
    
    def validate_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate input text
        
        Args:
            text: Text cần validate
            
        Returns:
            Tuple[is_valid, error_message]
        """
        if not text or not text.strip():
            return False, "Input không được để trống"
        
        if len(text.strip()) < 2:
            return False, "Input quá ngắn"
        
        if len(text) > 1000:
            return False, "Input quá dài (tối đa 1000 ký tự)"
        
        # Kiểm tra content filtering
        if ENABLE_CONTENT_FILTERING:
            blocked_words = ["spam", "advertisement", "phishing"]  # Có thể mở rộng
            text_lower = text.lower()
            for word in blocked_words:
                if word in text_lower:
                    return False, f"Input chứa nội dung không phù hợp: {word}"
        
        return True, None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về model đang sử dụng"""
        return {
            "model_name": GEMINI_MODEL,
            "max_tokens": GEMINI_MAX_TOKENS,
            "temperature": GEMINI_TEMPERATURE,
            "top_p": GEMINI_TOP_P,
            "top_k": GEMINI_TOP_K,
            "conversation_history_enabled": ENABLE_CONVERSATION_CONTEXT,
            "max_conversation_history": self.max_history,
            "current_history_length": len(self.conversation_history)
        }


def main():
    """Test function"""
    print("🧪 Gemini LLM Module Test")
    print("=" * 40)
    
    try:
        # Initialize LLM
        llm = GeminiLLM()
        
        # Test connection
        if llm.test_connection():
            print("✅ Gemini API connection successful")
        else:
            print("❌ Gemini API connection failed")
            return
        
        # Test basic response
        print("\\n🤖 Testing basic response...")
        test_input = "Xin chào, tôi đang cảm thấy hơi buồn hôm nay"
        
        result = llm.generate_response(test_input)
        
        if result["success"]:
            print(f"✅ Response generation successful!")
            print(f"📝 Input: '{test_input}'")
            print(f"🤖 Response: '{result['response'][:100]}...'")
            print(f"⏱️  Latency: {result['latency_ms']:.1f}ms")
            print(f"📊 Tokens - Prompt: {result['prompt_tokens']}, Response: {result['response_tokens']}")
        else:
            print(f"❌ Response generation failed: {result['error']}")
        
        # Test conversation context
        print("\\n💬 Testing conversation context...")
        second_input = "Cảm ơn bạn, bạn có thể cho tôi lời khuyên về việc chăm sóc sức khỏe không?"
        
        result2 = llm.generate_response(second_input)
        
        if result2["success"]:
            print(f"✅ Context-aware response successful!")
            print(f"📝 Input: '{second_input}'")
            print(f"🤖 Response: '{result2['response'][:100]}...'")
        
        # Test conversation summary
        print("\\n📋 Testing conversation summary...")
        summary = llm.get_conversation_summary()
        
        if summary["success"]:
            print(f"✅ Summary generation successful!")
            print(f"📊 Total exchanges: {summary['total_exchanges']}")
            print(f"📝 Summary: {summary['summary'][:100]}...")
        
        # Test model info
        print("\\n📋 Model Information:")
        model_info = llm.get_model_info()
        for key, value in model_info.items():
            print(f"   {key}: {value}")
        
        print("\\n🎯 LLM Module test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
