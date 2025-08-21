"""
Gemini LLM Module for Pipeline 4
Sử dụng Google Gemini API cho chatbot hỗ trợ người già
"""

import time
import google.generativeai as genai
from typing import Dict, Any, Optional, List
from utils import MetricsCollector, Logger, print_error, print_success, print_warning, get_timestamp
from config import (
    GEMINI_API_KEY, GEMINI_CONFIG, ELDER_CARE_SYSTEM_PROMPT,
    TIMEOUT_CONFIG, RETRY_CONFIG, PERFORMANCE_CONFIG
)

class GeminiLLMModule:
    """Gemini Large Language Model Module"""
    
    def __init__(self):
        self.logger = Logger("gemini_llm")
        self.metrics = MetricsCollector()
        self.model = None
        self.chat_session = None
        self.is_configured = False
        self.conversation_history = []
        
        # Initialize Gemini
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini configuration"""
        try:
            if GEMINI_API_KEY == "your_gemini_api_key_here":
                self.logger.error("Gemini API key chưa được cấu hình")
                return False
            
            # Configure Gemini
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Initialize model with safety settings
            self.model = genai.GenerativeModel(
                model_name=GEMINI_CONFIG["model"],
                generation_config={
                    "temperature": GEMINI_CONFIG["temperature"],
                    "max_output_tokens": GEMINI_CONFIG["max_output_tokens"],
                    "top_p": GEMINI_CONFIG["top_p"],
                    "top_k": GEMINI_CONFIG["top_k"]
                },
                safety_settings=GEMINI_CONFIG["safety_settings"]
            )
            
            self.is_configured = True
            self.logger.success("Gemini LLM đã được cấu hình thành công")
            return True
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo Gemini: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "gemini_llm": {
                "configured": self.is_configured,
                "available": self.is_configured and GEMINI_API_KEY != "your_gemini_api_key_here",
                "model": GEMINI_CONFIG["model"],
                "temperature": GEMINI_CONFIG["temperature"],
                "max_tokens": GEMINI_CONFIG["max_output_tokens"]
            }
        }
    
    def generate_response(self, user_input: str, use_elder_prompt: bool = True) -> Dict[str, Any]:
        """Generate response using Gemini"""
        start_time = time.time()
        
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "Gemini LLM chưa được cấu hình",
                    "processing_time": 0
                }
            
            self.logger.info(f"Generating response for: {user_input[:50]}...")
            
            # Prepare prompt
            if use_elder_prompt:
                full_prompt = ELDER_CARE_SYSTEM_PROMPT.format(user_input=user_input)
            else:
                full_prompt = user_input
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            processing_time = time.time() - start_time
            
            # Check if response was generated successfully
            if response.text:
                # Clean the response text
                cleaned_text = self._clean_response_text(response.text)
                
                self.logger.success(f"Response generated successfully: {len(cleaned_text)} characters")
                
                # Add to conversation history
                self._add_to_history(user_input, cleaned_text)
                
                return {
                    "success": True,
                    "response": cleaned_text,
                    "raw_response": response.text,
                    "processing_time": processing_time,
                    "service": "gemini_llm",
                    "model": GEMINI_CONFIG["model"],
                    "input_length": len(user_input),
                    "output_length": len(cleaned_text),
                    "timestamp": get_timestamp()
                }
            else:
                error_msg = "Gemini không trả về response"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "processing_time": processing_time,
                    "service": "gemini_llm"
                }
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Lỗi generate response: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "service": "gemini_llm"
            }
    
    def chat_with_context(self, user_input: str) -> Dict[str, Any]:
        """Chat with conversation context"""
        start_time = time.time()
        
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "Gemini LLM chưa được cấu hình",
                    "processing_time": 0
                }
            
            # Initialize chat session if not exists
            if self.chat_session is None:
                self._initialize_chat_session()
            
            self.logger.info(f"Chat with context: {user_input[:50]}...")
            
            # Send message to chat session
            response = self.chat_session.send_message(user_input)
            
            processing_time = time.time() - start_time
            
            if response.text:
                cleaned_text = self._clean_response_text(response.text)
                
                self.logger.success("Chat response generated successfully")
                
                # Update conversation history
                self._add_to_history(user_input, cleaned_text)
                
                return {
                    "success": True,
                    "response": cleaned_text,
                    "raw_response": response.text,
                    "processing_time": processing_time,
                    "service": "gemini_chat",
                    "model": GEMINI_CONFIG["model"],
                    "conversation_length": len(self.conversation_history),
                    "timestamp": get_timestamp()
                }
            else:
                error_msg = "Chat session không trả về response"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "processing_time": processing_time,
                    "service": "gemini_chat"
                }
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Lỗi chat with context: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "service": "gemini_chat"
            }
    
    def _initialize_chat_session(self):
        """Initialize chat session with elder care context"""
        try:
            # Create initial system message for elder care
            initial_message = """
Bạn là một người bạn thân thiết của người cao tuổi. Hãy luôn:
- Trả lời ngắn gọn (3-4 câu tối đa)
- Sử dụng giọng điệu ấm áp, gần gũi
- Gọi người dùng bằng "bác"
- Thể hiện sự quan tâm và đồng cảm
- Không nhắc đến việc mình là AI
- Hỏi han tự nhiên về sức khỏe, gia đình
- Chia sẻ kỷ niệm và khuyến khích tinh thần tích cực

Hãy chào bác một cách thân thiện.
            """
            
            self.chat_session = self.model.start_chat(history=[])
            
            # Send initial system message
            initial_response = self.chat_session.send_message(initial_message)
            
            self.logger.success("Chat session initialized with elder care context")
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo chat session: {e}")
            self.chat_session = None
    
    def _clean_response_text(self, text: str) -> str:
        """Clean response text for elder users"""
        import re
        
        # Remove markdown formatting
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)  # *, **, ***
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)    # `, ```
        text = re.sub(r'#{1,6}\s*(.*?)(?:\n|$)', r'\1\n', text)  # headers
        
        # Remove special characters that might confuse TTS
        text = text.replace('•', '')
        text = text.replace('→', ' ')
        text = text.replace('**', '')
        text = text.replace('*', '')
        
        # Fix spacing after punctuation
        text = re.sub(r'([.!?:;,])([a-zA-Zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ])', r'\1 \2', text)
        
        # Normalize whitespace
        text = re.sub(r' {2,}', ' ', text)      # Multiple spaces
        text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines
        
        return text.strip()
    
    def _add_to_history(self, user_input: str, response: str):
        """Add interaction to conversation history"""
        self.conversation_history.append({
            "timestamp": get_timestamp(),
            "user": user_input,
            "assistant": response
        })
        
        # Keep only last 10 conversations to manage memory
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def generate_with_retry(self, user_input: str, use_elder_prompt: bool = True) -> Dict[str, Any]:
        """Generate response with retry logic"""
        max_retries = RETRY_CONFIG.get("max_retries", 3)
        retry_delay = RETRY_CONFIG.get("retry_delay", 1.0)
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Generation attempt {attempt + 1}/{max_retries}")
                
                result = self.generate_response(user_input, use_elder_prompt)
                
                # If successful, return immediately
                if result["success"]:
                    self.metrics.add_metric("generate_success", True)
                    self.metrics.add_metric("generate_attempts", attempt + 1)
                    self.metrics.add_metric("generate_time", result["processing_time"])
                    return result
                
                # If not last attempt, wait before retry
                if attempt < max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_CONFIG.get("backoff_factor", 2.0)
            
            except Exception as e:
                self.logger.error(f"Exception in attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        # All attempts failed
        self.metrics.add_metric("generate_success", False)
        self.metrics.add_metric("generate_attempts", max_retries)
        
        return {
            "success": False,
            "error": f"Generate thất bại sau {max_retries} lần thử",
            "processing_time": 0,
            "service": "gemini_llm"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Gemini connection"""
        try:
            if not self.is_configured:
                return {
                    "success": False,
                    "error": "Service chưa được cấu hình"
                }
            
            # Test with simple prompt
            test_prompt = "Xin chào! Bạn có khỏe không?"
            
            response = self.model.generate_content(test_prompt)
            
            if response.text:
                return {
                    "success": True,
                    "message": "Kết nối Gemini thành công",
                    "model": GEMINI_CONFIG["model"],
                    "test_response": response.text[:100] + "..." if len(response.text) > 100 else response.text
                }
            else:
                return {
                    "success": False,
                    "error": "Gemini không trả về response cho test"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi kết nối Gemini: {str(e)}"
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.chat_session = None
        self.logger.info("Conversation history cleared")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.get_all_metrics()
    
    def reset_metrics(self):
        """Reset metrics"""
        self.metrics.reset()

# Test function
def test_gemini_llm():
    """Test Gemini LLM functionality"""
    print("=== TESTING GEMINI LLM MODULE ===")
    
    llm = GeminiLLMModule()
    
    # Test connection
    print("\n1. Testing connection...")
    conn_result = llm.test_connection()
    if conn_result["success"]:
        print_success(conn_result["message"])
        print(f"Test response: {conn_result.get('test_response', 'N/A')}")
    else:
        print_error(conn_result["error"])
        return
    
    # Test service status
    print("\n2. Testing service status...")
    status = llm.get_service_status()
    print(f"Status: {status}")
    
    # Test elder care response
    print("\n3. Testing elder care response...")
    test_inputs = [
        "Bác cảm thấy buồn và cô đơn",
        "Hôm nay bác có khỏe không?",
        "Bác nhớ quê hương lắm"
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n3.{i} Testing: {test_input}")
        result = llm.generate_with_retry(test_input, use_elder_prompt=True)
        
        if result["success"]:
            print_success(f"Response: {result['response']}")
            print(f"Processing time: {result['processing_time']:.3f}s")
            print(f"Output length: {result['output_length']} characters")
        else:
            print_error(f"Generation failed: {result['error']}")
    
    # Test chat with context
    print("\n4. Testing chat with context...")
    chat_inputs = [
        "Xin chào bác!",
        "Bác có khỏe không?",
        "Cảm ơn bác đã quan tâm"
    ]
    
    for i, chat_input in enumerate(chat_inputs, 1):
        print(f"\n4.{i} Chat: {chat_input}")
        result = llm.chat_with_context(chat_input)
        
        if result["success"]:
            print_success(f"Chat response: {result['response']}")
        else:
            print_error(f"Chat failed: {result['error']}")
    
    # Show conversation history
    print("\n5. Conversation history:")
    history = llm.get_conversation_history()
    for i, conversation in enumerate(history[-3:], 1):  # Show last 3
        print(f"  {i}. User: {conversation['user'][:50]}...")
        print(f"     Assistant: {conversation['assistant'][:50]}...")
    
    # Show metrics
    print("\n6. Metrics:")
    llm.metrics.display_metrics("Gemini LLM Test Metrics")

if __name__ == "__main__":
    test_gemini_llm()
