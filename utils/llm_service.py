import google.generativeai as genai
import logging
import time
from typing import Optional, Tuple, Dict, Any
import json

class LLMService:
    """Google Gemini AI service for natural language processing"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", 
                 temperature: float = 0.7, max_tokens: int = 1000):
        """
        Initialize LLM service with Gemini API
        
        Args:
            api_key: Google Gemini API key
            model_name: Model to use (default: gemini-1.5-flash)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response length
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(model_name)
        
        # Generation config optimized for elder care (shorter responses)
        self.generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=min(max_tokens, 500),  # Limit for brevity
            candidate_count=1
        )
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> Tuple[str, Dict[str, Any], bool]:
        """
        Generate response using Gemini AI
        
        Args:
            prompt: User input text
            system_prompt: System/context prompt
            
        Returns:
            Tuple of (response_text, usage_info, success)
        """
        try:
            # Combine system prompt and user prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
            else:
                full_prompt = prompt
            
            self.logger.info(f"Generating response for prompt: {prompt[:100]}...")
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )
            
            # Extract response text
            if response.candidates and len(response.candidates) > 0:
                response_text = response.candidates[0].content.parts[0].text
                
                # Get usage information
                usage_info = self._extract_usage_info(response)
                
                self.logger.info("Response generated successfully")
                return response_text, usage_info, True
            else:
                self.logger.warning("No response candidates generated")
                return "", {}, False
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "", {}, False
    
    def detect_emotion(self, text: str) -> Dict[str, Any]:
        """
        Detect emotion from user text using keyword analysis
        
        Args:
            text: User input text
            
        Returns:
            Dictionary with emotion info and context
        """
        text_lower = text.lower()
        
        # Emotion keywords based on test.py analysis
        emotion_keywords = {
            'buồn': ['buồn', 'khóc', 'đau lòng', 'tủi thân', 'cô đơn', 'u sầu'],
            'nhớ_quê': ['nhớ quê', 'nhớ nhà', 'quê hương', 'cố hương', 'xa quê'],
            'lo_lắng': ['lo lắng', 'lo âu', 'hồi hộp', 'bất an', 'sợ', 'nghĩ ngợi'],
            'vui': ['vui', 'hạnh phúc', 'vừa lòng', 'thích', 'mừng', 'phấn khởi'],
            'bệnh_tật': ['đau', 'bệnh', 'khó chịu', 'mệt', 'yếu', 'không khỏe'],
            'gia_đình': ['con cháu', 'gia đình', 'nhà', 'bà', 'ông', 'cháu']
        }
        
        detected_emotions = []
        confidence_scores = {}
        
        for emotion, keywords in emotion_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                confidence = min(matches / len(keywords), 1.0)
                detected_emotions.append(emotion)
                confidence_scores[emotion] = confidence
        
        # Determine primary emotion
        primary_emotion = None
        emotion_context = ""
        
        if detected_emotions:
            primary_emotion = max(confidence_scores, key=confidence_scores.get)
            
            # Generate emotion-specific context
            if primary_emotion == 'buồn':
                emotion_context = "Người dùng đang buồn - cần an ủi, động viên nhẹ nhàng"
            elif primary_emotion == 'nhớ_quê':
                emotion_context = "Người dùng nhớ quê - chia sẻ kỷ niệm, khuyến khích liên lạc gia đình"
            elif primary_emotion == 'lo_lắng':
                emotion_context = "Người dùng lo lắng - trấn an, đưa giải pháp thực tế"
            elif primary_emotion == 'vui':
                emotion_context = "Người dùng vui vẻ - chia sẻ niềm vui, duy trì tâm trạng tích cực"
            elif primary_emotion == 'bệnh_tật':
                emotion_context = "Vấn đề sức khỏe - tư vấn cẩn thận, khuyến khích khám bác sĩ"
            elif primary_emotion == 'gia_đình':
                emotion_context = "Vấn đề gia đình - lắng nghe, tư vấn mối quan hệ"
        
        return {
            'detected_emotions': detected_emotions,
            'primary_emotion': primary_emotion,
            'emotion_context': emotion_context,
            'confidence_scores': confidence_scores,
            'has_emotion': len(detected_emotions) > 0
        }

    def chat_with_context(self, user_input: str, conversation_history: list = None) -> Tuple[str, Dict[str, Any], bool]:
        """
        Generate response with conversation context and emotion awareness for elderly care
        
        Args:
            user_input: Current user message
            conversation_history: Previous conversation messages
            
        Returns:
            Tuple of (response_text, usage_info, success)
        """
        try:
            # Detect emotion from user input
            emotion_info = self.detect_emotion(user_input)
            
            # Build conversation context
            context_messages = []
            
            if conversation_history:
                for msg in conversation_history[-3:]:  # Keep last 3 messages (reduced for brevity)
                    context_messages.append(msg)
            
            # Add current user input
            context_messages.append({"role": "user", "content": user_input})
            
            # Create elder care system prompt with emotion context
            system_prompt = self._get_elder_care_prompt(emotion_info.get('emotion_context', ''))
            
            # Build optimized conversation prompt
            conversation_text = self._build_optimized_conversation_prompt(
                context_messages, 
                system_prompt, 
                emotion_info
            )
            
            # Generate response with optimized settings for brevity
            original_max_tokens = self.max_tokens
            self.update_generation_config(max_tokens=300)  # Limit response length
            
            response, usage_info, success = self.generate_response(conversation_text)
            
            # Restore original settings
            self.update_generation_config(max_tokens=original_max_tokens)
            
            # Add emotion info to usage_info
            usage_info['emotion_detected'] = emotion_info
            
            return response, usage_info, success
            
        except Exception as e:
            self.logger.error(f"Error in chat with context: {str(e)}")
            return "", {}, False
    
    def _get_elder_care_prompt(self, emotion_context: str = "") -> str:
        """Get specialized prompt for elderly care chatbot with emotion awareness"""
        base_prompt = """Bạn là trợ lý AI thân thiện cho người cao tuổi Việt Nam.

NGUYÊN TẮC GIAO TIẾP:
- Thân thiện, kiên nhẫn, dễ hiểu
- Tiếng Việt đơn giản, tránh thuật ngữ
- TRẢ LỜI NGẮN GỌN: TỐI ĐA 4-5 CÂU
- Luôn động viên, tích cực

HỖ TRỢ: Sức khỏe, dinh dưỡng, tâm lý, gia đình, công nghệ đơn giản"""

        # Add emotion-specific guidance
        if emotion_context:
            base_prompt += f"\n\nCẢM XÚC PHÁT HIỆN: {emotion_context}"
            
        base_prompt += "\n\nLưu ý: Khuyến khích đi khám bác sĩ khi cần thiết."
        
        return base_prompt
    
    def _build_optimized_conversation_prompt(self, messages: list, system_prompt: str, emotion_info: Dict) -> str:
        """Build optimized conversation prompt with emotion awareness"""
        prompt_parts = [system_prompt]
        
        # Add emotion-specific instruction if detected
        if emotion_info.get('has_emotion'):
            primary_emotion = emotion_info.get('primary_emotion')
            if primary_emotion == 'buồn':
                prompt_parts.append("Hướng dẫn: An ủi nhẹ nhàng, đưa lời khuyên tích cực.")
            elif primary_emotion == 'lo_lắng':
                prompt_parts.append("Hướng dẫn: Trấn an, đưa giải pháp cụ thể và thực tế.")
            elif primary_emotion == 'bệnh_tật':
                prompt_parts.append("Hướng dẫn: Tư vấn cẩn thận, khuyến khích đi khám bác sĩ.")
            elif primary_emotion == 'vui':
                prompt_parts.append("Hướng dẫn: Chia sẻ niềm vui, duy trì tâm trạng tích cực.")
        
        # Add conversation context (shorter format)
        prompt_parts.append("\n--- CUỘC TRÒ CHUYỆN ---")
        
        # Only include the most recent relevant messages
        for msg in messages[-2:]:  # Last 2 messages only
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                prompt_parts.append(f"Người dùng: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Trợ lý: {content}")
        
        # Add response format instruction
        prompt_parts.append("\nTrả lời ngắn gọn (tối đa 4-5 câu), thân thiện:\nTrợ lý:")
        
        return "\n".join(prompt_parts)
    
    def _extract_usage_info(self, response) -> Dict[str, Any]:
        """Extract token usage and other info from response"""
        usage_info = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            # Try to extract usage metadata
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                usage_info["input_tokens"] = getattr(usage, 'prompt_token_count', 0)
                usage_info["output_tokens"] = getattr(usage, 'candidates_token_count', 0)
                usage_info["total_tokens"] = getattr(usage, 'total_token_count', 0)
            
            # Estimate if not available
            if usage_info["total_tokens"] == 0:
                # Rough estimation: 1 token ≈ 4 characters
                if response.candidates and len(response.candidates) > 0:
                    response_text = response.candidates[0].content.parts[0].text
                    usage_info["output_tokens"] = len(response_text) // 4
                    usage_info["total_tokens"] = usage_info["input_tokens"] + usage_info["output_tokens"]
        
        except Exception as e:
            self.logger.warning(f"Could not extract usage info: {e}")
        
        return usage_info
    
    def test_connection(self) -> bool:
        """
        Test Gemini API connection
        
        Returns:
            True if connection is successful
        """
        try:
            test_response = self.model.generate_content(
                "Xin chào! Đây là test kết nối.",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10,
                    temperature=0
                )
            )
            
            if test_response.candidates and len(test_response.candidates) > 0:
                self.logger.info("Gemini API connection test successful")
                return True
            else:
                self.logger.error("Gemini API connection test failed: No response")
                return False
                
        except Exception as e:
            self.logger.error(f"Gemini API connection test failed: {e}")
            return False
    
    def get_available_models(self) -> list:
        """Get list of available Gemini models"""
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model.name)
            return models
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return [self.model_name]
    
    def change_model(self, model_name: str):
        """
        Change the Gemini model
        
        Args:
            model_name: New model name to use
        """
        try:
            self.model_name = model_name
            self.model = genai.GenerativeModel(model_name)
            self.logger.info(f"Model changed to: {model_name}")
        except Exception as e:
            self.logger.error(f"Error changing model: {e}")
    
    def update_generation_config(self, temperature: float = None, 
                                max_tokens: int = None):
        """
        Update generation configuration
        
        Args:
            temperature: New temperature value
            max_tokens: New max tokens value
        """
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
            
        self.generation_config = genai.types.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            candidate_count=1
        )
        
        self.logger.info(f"Generation config updated: temp={self.temperature}, max_tokens={self.max_tokens}")
    
    def get_health_advice(self, symptom_or_question: str) -> Tuple[str, Dict[str, Any], bool]:
        """
        Get health-related advice for elderly
        
        Args:
            symptom_or_question: Health question or symptom description
            
        Returns:
            Tuple of (advice_text, usage_info, success)
        """
        health_prompt = f"""
Bạn là chuyên gia tư vấn sức khỏe cho người cao tuổi. Hãy trả lời câu hỏi sau một cách:
- An toàn và thận trọng
- Dễ hiểu với người cao tuổi
- Luôn khuyến khích đi khám bác sĩ khi cần thiết
- Đưa ra lời khuyên thực tế, khả thi

Câu hỏi về sức khỏe: {symptom_or_question}

Lưu ý: Đây chỉ là thông tin tham khảo, không thay thế ý kiến chuyên môn của bác sĩ.
"""
        
        return self.generate_response(health_prompt)
    
    def get_daily_tips(self) -> Tuple[str, Dict[str, Any], bool]:
        """
        Get daily health and lifestyle tips for elderly
        
        Returns:
            Tuple of (tips_text, usage_info, success)
        """
        tips_prompt = """
Hãy đưa ra 3-5 lời khuyên hữu ích cho người cao tuổi trong ngày hôm nay về:
- Sức khỏe và chăm sóc bản thân
- Dinh dưỡng
- Vận động nhẹ nhàng
- Tinh thần tích cực

Mỗi lời khuyên nên ngắn gọn, dễ thực hiện và phù hợp với người Việt Nam cao tuổi.
"""
        
        return self.generate_response(tips_prompt)
    
    def test_emotion_detection(self, test_inputs: list = None) -> Dict[str, Any]:
        """
        Test emotion detection with sample inputs
        
        Args:
            test_inputs: List of test strings (optional)
            
        Returns:
            Dictionary with test results
        """
        if test_inputs is None:
            test_inputs = [
                "Tôi thấy buồn và cô đơn quá",
                "Con cháu xa xôi, tôi nhớ quê lắm",
                "Tôi lo lắng về sức khỏe của mình",
                "Hôm nay tôi rất vui vẻ",
                "Đầu tôi đau, cảm thấy mệt mỏi",
                "Gia đình tôi rất hạnh phúc"
            ]
        
        test_results = {}
        
        for i, text in enumerate(test_inputs):
            emotion_result = self.detect_emotion(text)
            test_results[f"test_{i+1}"] = {
                "input": text,
                "emotion_result": emotion_result
            }
        
        return test_results
    
    def get_emotion_optimized_response(self, user_input: str) -> Tuple[str, Dict[str, Any], bool]:
        """
        Get response optimized for detected emotion
        
        Args:
            user_input: User message
            
        Returns:
            Tuple of (response_text, usage_info, success)
        """
        # Detect emotion
        emotion_info = self.detect_emotion(user_input)
        
        # Build emotion-specific prompt
        if emotion_info.get('has_emotion'):
            emotion_context = emotion_info.get('emotion_context', '')
            system_prompt = self._get_elder_care_prompt(emotion_context)
            
            # Create optimized prompt
            full_prompt = f"{system_prompt}\n\nNgười dùng: {user_input}\n\nTrả lời ngắn gọn, thấu hiểu:\nTrợ lý:"
        else:
            # Standard prompt for neutral messages
            system_prompt = self._get_elder_care_prompt()
            full_prompt = f"{system_prompt}\n\nNgười dùng: {user_input}\n\nTrả lời ngắn gọn:\nTrợ lý:"
        
        # Generate response with emotion context
        response, usage_info, success = self.generate_response(full_prompt)
        
        # Add emotion info to usage
        usage_info['emotion_detected'] = emotion_info
        
        return response, usage_info, success
