"""
Large Language Model Module for Pipeline 3
Sử dụng Google Gemini AI
"""

import time
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config import GEMINI_API_KEY, GEMINI_CONFIG, SYSTEM_PROMPTS, TIMEOUT_CONFIG
from utils import Logger, MetricsCollector

class LLMModule:
    """Large Language Model module using Google Gemini"""
    
    def __init__(self):
        self.logger = Logger("llm")
        self.metrics = MetricsCollector()
        self.model = None
        
        # Validate and initialize
        self._validate_config()
        self._initialize_model()
        
    def _validate_config(self):
        """Validate LLM configuration"""
        errors = []
        
        if GEMINI_API_KEY == "your_gemini_api_key_here":
            errors.append("GEMINI_API_KEY chưa được cấu hình")
            
        if genai is None:
            errors.append("Google GenerativeAI library chưa được cài đặt (pip install google-generativeai)")
            
        if errors:
            self.logger.warning("Một số cấu hình LLM chưa sẵn sàng:")
            for error in errors:
                self.logger.warning(f"  - {error}")
    
    def _initialize_model(self):
        """Initialize Gemini model"""
        try:
            if genai is None:
                self.logger.error("Google GenerativeAI library không khả dụng")
                return
                
            if GEMINI_API_KEY == "your_gemini_api_key_here":
                self.logger.error("GEMINI_API_KEY chưa được cấu hình")
                return
            
            # Configure API key
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Initialize model
            self.model = genai.GenerativeModel(
                model_name=GEMINI_CONFIG["model"]
            )
            
            self.logger.success(f"Gemini model {GEMINI_CONFIG['model']} đã sẵn sàng")
            
        except Exception as e:
            self.logger.error(f"Không thể khởi tạo Gemini model: {e}")
            self.model = None
    
    def generate_response(
        self, 
        user_input: str, 
        system_prompt_type: str = "elder_assistant",
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using Gemini
        
        Args:
            user_input: Input text from user
            system_prompt_type: Type of system prompt to use
            custom_system_prompt: Custom system prompt (overrides type)
            
        Returns:
            Dict containing response, processing time, and metrics
        """
        self.logger.info(f"Tạo response cho input: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        
        if self.model is None:
            return {
                "success": False,
                "error": "Gemini model chưa được khởi tạo",
                "user_input": user_input
            }
        
        # Start timing
        start_time = time.time()
        self.metrics.start_timer("llm_processing")
        
        try:
            # Prepare system prompt
            if custom_system_prompt:
                system_prompt = custom_system_prompt
            else:
                system_prompt = SYSTEM_PROMPTS.get(system_prompt_type, SYSTEM_PROMPTS["general"])
            
            # Combine system prompt with user input
            full_prompt = f"{system_prompt}\n\nNgười dùng hỏi: {user_input}\n\nTrả lời:"
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=GEMINI_CONFIG["temperature"],
                    max_output_tokens=GEMINI_CONFIG["max_output_tokens"]
                ),
                safety_settings=GEMINI_CONFIG["safety_settings"]
            )
            
            # Extract response text
            if response.text:
                response_text = response.text.strip()
            else:
                # Handle cases where response might be blocked
                if response.candidates and response.candidates[0].finish_reason:
                    finish_reason = response.candidates[0].finish_reason
                    response_text = f"Tôi không thể trả lời câu hỏi này (lý do: {finish_reason}). Xin hãy thử hỏi cách khác."
                else:
                    response_text = "Tôi không thể tạo response cho câu hỏi này. Xin hãy thử lại."
            
            # Calculate metrics
            processing_time = self.metrics.end_timer("llm_processing")
            
            metrics = {
                "processing_time": processing_time,
                "input_length": len(user_input),
                "output_length": len(response_text),
                "model": GEMINI_CONFIG["model"],
                "system_prompt_type": system_prompt_type,
                "status": "success"
            }
            
            # Add safety ratings if available
            if response.candidates and response.candidates[0].safety_ratings:
                metrics["safety_ratings"] = {
                    rating.category.name: rating.probability.name 
                    for rating in response.candidates[0].safety_ratings
                }
            
            self.logger.success(f"LLM response tạo thành công ({processing_time:.3f}s)")
            self.logger.info(f"Response: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
            
            return {
                "success": True,
                "response": response_text,
                "user_input": user_input,
                "processing_time": processing_time,
                "metrics": metrics
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            error_msg = str(e)
            self.logger.error(f"LLM generation thất bại: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "user_input": user_input,
                "processing_time": processing_time,
                "metrics": {
                    "processing_time": processing_time,
                    "input_length": len(user_input),
                    "status": "error",
                    "error": error_msg
                }
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if self.model is None:
            return {
                "available": False,
                "error": "Model chưa được khởi tạo"
            }
        
        return {
            "available": True,
            "model_name": GEMINI_CONFIG["model"],
            "temperature": GEMINI_CONFIG["temperature"],
            "max_output_tokens": GEMINI_CONFIG["max_output_tokens"],
            "api_configured": GEMINI_API_KEY != "your_gemini_api_key_here"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Gemini API"""
        test_input = "Xin chào"
        
        self.logger.info("Testing Gemini API connection...")
        
        result = self.generate_response(
            test_input, 
            system_prompt_type="general"
        )
        
        if result["success"]:
            self.logger.success("Gemini API connection test thành công")
            return {
                "success": True,
                "response_time": result["processing_time"],
                "test_input": test_input,
                "test_response": result["response"]
            }
        else:
            self.logger.error(f"Gemini API connection test thất bại: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "test_input": test_input
            }

def test_llm_module():
    """Test function for LLM module"""
    print("=== TESTING LLM MODULE ===")
    
    llm = LLMModule()
    
    # Show model info
    info = llm.get_model_info()
    print(f"Model available: {info['available']}")
    if info['available']:
        print(f"Model: {info['model_name']}")
        print(f"Temperature: {info['temperature']}")
    
    # Test connection
    connection_test = llm.test_connection()
    if connection_test["success"]:
        print(f"\n✅ Connection test successful!")
        print(f"Response time: {connection_test['response_time']:.3f}s")
        print(f"Test response: {connection_test['test_response']}")
    else:
        print(f"\n❌ Connection test failed: {connection_test['error']}")
        return
    
    # Test with sample inputs
    test_cases = [
        {
            "input": "Tôi bị đau đầu, làm thế nào để giảm đau?",
            "prompt_type": "elder_assistant"
        },
        {
            "input": "Thời tiết hôm nay thế nào?",
            "prompt_type": "general"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {test_case['input']}")
        print(f"Prompt type: {test_case['prompt_type']}")
        
        result = llm.generate_response(
            test_case["input"],
            test_case["prompt_type"]
        )
        
        if result["success"]:
            print(f"✅ Success ({result['processing_time']:.3f}s)")
            print(f"Response: {result['response']}")
        else:
            print(f"❌ Failed: {result['error']}")

if __name__ == "__main__":
    test_llm_module()
