"""
LLM Test - Test riêng cho Large Language Model với Google Gemini
Chạy: python llm_test.py
"""

import os
import sys
import logging
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from config import *
    from utils.llm_service import LLMService
    from utils.metrics import MetricsCollector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Make sure to install required packages: pip install -r requirements.txt")
    sys.exit(1)

def setup_logging():
    """Setup logging configuration"""
    log_file = os.path.join(LOGS_DIR, f'llm_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return log_file

def test_llm_connection():
    """Test LLM service connection"""
    print(f"\n{Fore.CYAN}🔍 Testing LLM Connection...{Style.RESET_ALL}")
    
    try:
        llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
        
        if llm_service.test_connection():
            print(f"{Fore.GREEN}✅ LLM Connection: SUCCESS{Style.RESET_ALL}")
            return llm_service
        else:
            print(f"{Fore.RED}❌ LLM Connection: FAILED{Style.RESET_ALL}")
            return None
            
    except Exception as e:
        print(f"{Fore.RED}❌ LLM Connection Error: {e}{Style.RESET_ALL}")
        return None

def test_basic_conversation():
    """Test basic conversation capabilities"""
    print(f"\n{Fore.CYAN}💬 Testing Basic Conversation...{Style.RESET_ALL}")
    
    try:
        llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
        metrics_collector = MetricsCollector()
        
        # Test conversations for elderly care
        test_questions = [
            "Xin chào, bạn có thể giúp tôi không?",
            "Tôi bị đau đầu, tôi nên làm gì?",
            "Người cao tuổi nên ăn gì để có sức khỏe tốt?",
            "Tôi cảm thấy cô đơn, bạn có lời khuyên gì không?",
            "Làm thế nào để ngủ ngon giấc ở tuổi già?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{Fore.YELLOW}❓ Test {i}: {question}{Style.RESET_ALL}")
            
            # Generate response
            start_time = metrics_collector.start_timer()
            response, usage_info, success = llm_service.generate_response(question, ELDER_CARE_PROMPT)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                # Create LLM metrics
                llm_metrics = metrics_collector.create_llm_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    input_tokens=usage_info.get('input_tokens', len(question) // 4),
                    output_tokens=usage_info.get('output_tokens', len(response) // 4),
                    total_tokens=usage_info.get('total_tokens', 0),
                    response_length=len(response),
                    model_name=GEMINI_MODEL,
                    success=True
                )
                
                # Display response
                print(f"{Fore.GREEN}🤖 Response:{Style.RESET_ALL}")
                print(f"   {response[:200]}{'...' if len(response) > 200 else ''}")
                
                # Display metrics
                metrics_collector.display_metrics(llm_metrics, f"LLM Test {i}")
                
                # Save metrics
                metrics_collector.save_metrics(llm_metrics)
                
            else:
                print(f"{Fore.RED}❌ LLM Test {i} failed{Style.RESET_ALL}")
                return False
            
            time.sleep(1)  # Brief pause between requests
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Basic conversation test error: {e}{Style.RESET_ALL}")
        return False

def test_health_advice():
    """Test health advice functionality"""
    print(f"\n{Fore.CYAN}🏥 Testing Health Advice...{Style.RESET_ALL}")
    
    try:
        llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
        metrics_collector = MetricsCollector()
        
        # Health-related questions
        health_questions = [
            "Tôi bị đau lưng, có cách nào giảm đau không?",
            "Người cao tuổi có nên uống thuốc bổ không?",
            "Tôi hay quên, đây có phải là dấu hiệu bệnh không?",
            "Bài tập nào phù hợp với người 70 tuổi?",
            "Tôi bị mất ngủ, nên làm gì?"
        ]
        
        for i, question in enumerate(health_questions, 1):
            print(f"\n{Fore.YELLOW}🏥 Health Question {i}: {question}{Style.RESET_ALL}")
            
            start_time = metrics_collector.start_timer()
            response, usage_info, success = llm_service.get_health_advice(question)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                llm_metrics = metrics_collector.create_llm_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    input_tokens=usage_info.get('input_tokens', len(question) // 4),
                    output_tokens=usage_info.get('output_tokens', len(response) // 4),
                    total_tokens=usage_info.get('total_tokens', 0),
                    response_length=len(response),
                    model_name=GEMINI_MODEL,
                    success=True
                )
                
                print(f"{Fore.GREEN}💊 Health Advice:{Style.RESET_ALL}")
                print(f"   {response[:300]}{'...' if len(response) > 300 else ''}")
                
                metrics_collector.display_metrics(llm_metrics, f"Health Advice {i}")
                metrics_collector.save_metrics(llm_metrics)
                
            else:
                print(f"{Fore.RED}❌ Health advice {i} failed{Style.RESET_ALL}")
                return False
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Health advice test error: {e}{Style.RESET_ALL}")
        return False

def test_conversational_context():
    """Test conversation with context maintenance"""
    print(f"\n{Fore.CYAN}🧠 Testing Conversational Context...{Style.RESET_ALL}")
    
    try:
        llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
        metrics_collector = MetricsCollector()
        
        # Simulate a conversation with context
        conversation_history = []
        
        conversation_turns = [
            "Xin chào, tôi tên là Bà Lan, 75 tuổi.",
            "Tôi có vấn đề về giấc ngủ, thường xuyên mất ngủ.",
            "Vậy tôi nên uống thuốc ngủ không?",
            "Cảm ơn bạn. Còn về chế độ ăn uống thì sao?",
            "Tôi có nên tập thể dục không ở tuổi này?"
        ]
        
        for i, user_input in enumerate(conversation_turns, 1):
            print(f"\n{Fore.YELLOW}👤 Turn {i}: {user_input}{Style.RESET_ALL}")
            
            start_time = metrics_collector.start_timer()
            response, usage_info, success = llm_service.chat_with_context(user_input, conversation_history)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                # Add to conversation history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})
                
                llm_metrics = metrics_collector.create_llm_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    input_tokens=usage_info.get('input_tokens', len(user_input) // 4),
                    output_tokens=usage_info.get('output_tokens', len(response) // 4),
                    total_tokens=usage_info.get('total_tokens', 0),
                    response_length=len(response),
                    model_name=GEMINI_MODEL,
                    success=True
                )
                
                print(f"{Fore.GREEN}🤖 Response:{Style.RESET_ALL}")
                print(f"   {response[:250]}{'...' if len(response) > 250 else ''}")
                
                metrics_collector.display_metrics(llm_metrics, f"Context Turn {i}")
                metrics_collector.save_metrics(llm_metrics)
                
            else:
                print(f"{Fore.RED}❌ Context turn {i} failed{Style.RESET_ALL}")
                return False
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Conversational context test error: {e}{Style.RESET_ALL}")
        return False

def test_daily_tips():
    """Test daily tips generation"""
    print(f"\n{Fore.CYAN}💡 Testing Daily Tips Generation...{Style.RESET_ALL}")
    
    try:
        llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
        metrics_collector = MetricsCollector()
        
        print(f"{Fore.YELLOW}🌅 Generating daily tips for elderly care...{Style.RESET_ALL}")
        
        start_time = metrics_collector.start_timer()
        tips, usage_info, success = llm_service.get_daily_tips()
        end_time, response_time = metrics_collector.end_timer(start_time)
        
        if success:
            llm_metrics = metrics_collector.create_llm_metrics(
                start_time=start_time,
                end_time=end_time,
                response_time=response_time,
                input_tokens=usage_info.get('input_tokens', 50),
                output_tokens=usage_info.get('output_tokens', len(tips) // 4),
                total_tokens=usage_info.get('total_tokens', 0),
                response_length=len(tips),
                model_name=GEMINI_MODEL,
                success=True
            )
            
            print(f"{Fore.GREEN}💡 Daily Tips:{Style.RESET_ALL}")
            print(f"   {tips}")
            
            metrics_collector.display_metrics(llm_metrics, "Daily Tips Generation")
            metrics_collector.save_metrics(llm_metrics)
            
            return True
        else:
            print(f"{Fore.RED}❌ Daily tips generation failed{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Daily tips test error: {e}{Style.RESET_ALL}")
        return False

def test_interactive_chat():
    """Test interactive chat mode"""
    print(f"\n{Fore.CYAN}💬 Testing Interactive Chat Mode...{Style.RESET_ALL}")
    
    try:
        llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
        metrics_collector = MetricsCollector()
        
        conversation_history = []
        
        print(f"{Fore.YELLOW}🤖 Interactive chat started. Type 'quit' to exit.{Style.RESET_ALL}")
        print(f"💡 Try asking questions like:")
        print(f"   - 'Tôi bị đau đầu, nên làm gì?'")
        print(f"   - 'Chế độ ăn uống cho người cao tuổi?'")
        print(f"   - 'Làm sao để giữ tinh thần thoải mái?'")
        
        while True:
            print(f"\n{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
            user_input = input(f"{Fore.YELLOW}👤 Bạn: {Style.RESET_ALL}").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q', 'thoát']:
                print(f"{Fore.CYAN}👋 Cảm ơn bạn đã sử dụng dịch vụ!{Style.RESET_ALL}")
                break
            
            if not user_input:
                print(f"{Fore.YELLOW}⚠️ Vui lòng nhập câu hỏi{Style.RESET_ALL}")
                continue
            
            print(f"{Fore.CYAN}🤔 Đang suy nghĩ...{Style.RESET_ALL}")
            
            start_time = metrics_collector.start_timer()
            response, usage_info, success = llm_service.chat_with_context(user_input, conversation_history)
            end_time, response_time = metrics_collector.end_timer(start_time)
            
            if success:
                # Update conversation history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})
                
                # Keep only last 10 exchanges
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
                
                llm_metrics = metrics_collector.create_llm_metrics(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    input_tokens=usage_info.get('input_tokens', len(user_input) // 4),
                    output_tokens=usage_info.get('output_tokens', len(response) // 4),
                    total_tokens=usage_info.get('total_tokens', 0),
                    response_length=len(response),
                    model_name=GEMINI_MODEL,
                    success=True
                )
                
                print(f"{Fore.GREEN}🤖 Trợ lý AI: {response}{Style.RESET_ALL}")
                
                # Show quick metrics
                print(f"{Fore.BLUE}⚡ Response time: {response_time:.2f}s | Tokens: {usage_info.get('total_tokens', 'N/A')}{Style.RESET_ALL}")
                
                metrics_collector.save_metrics(llm_metrics)
                
            else:
                print(f"{Fore.RED}❌ Xin lỗi, tôi không thể trả lời câu hỏi này. Vui lòng thử lại.{Style.RESET_ALL}")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Interactive chat interrupted{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Interactive chat test error: {e}{Style.RESET_ALL}")
        return False

def display_llm_info():
    """Display LLM service information"""
    print(f"\n{Fore.MAGENTA}📋 LLM SERVICE INFORMATION{Style.RESET_ALL}")
    print(f"🔧 Service: Google Gemini")
    print(f"🤖 Model: {GEMINI_MODEL}")
    print(f"🌡️ Temperature: {GEMINI_TEMPERATURE}")
    print(f"🔢 Max Tokens: {GEMINI_MAX_TOKENS}")
    
    # Show available models
    try:
        llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
        models = llm_service.get_available_models()
        print(f"\n🤖 Available Models ({len(models)}):")
        for model in models[:5]:  # Show first 5
            status = "✅" if model.endswith(GEMINI_MODEL) else "  "
            print(f"  {status} {model}")
        if len(models) > 5:
            print(f"  ... and {len(models) - 5} more")
    except:
        print(f"⚠️ Could not load model list")

def main():
    """Main test function"""
    print(f"{Fore.BLUE}{'='*60}")
    print(f"🧠 LLM SERVICE TEST - GOOGLE GEMINI")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting LLM service test")
    
    # Display service info
    display_llm_info()
    
    # Check API key
    if not GEMINI_API_KEY:
        print(f"\n{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("📋 Please configure Google Gemini in .env file:")
        print("   GEMINI_API_KEY=your_gemini_api_key")
        return False
    
    test_results = {}
    
    # Test 1: Connection
    llm_service = test_llm_connection()
    test_results['connection'] = llm_service is not None
    
    if not llm_service:
        print(f"\n{Fore.RED}❌ Cannot proceed without LLM connection{Style.RESET_ALL}")
        return False
    
    # Test 2: Basic conversation
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 1: BASIC CONVERSATION")
    print(f"{'='*50}{Style.RESET_ALL}")
    test_results['basic_conversation'] = test_basic_conversation()
    
    # Test 3: Health advice
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 2: HEALTH ADVICE")
    print(f"{'='*50}{Style.RESET_ALL}")
    test_results['health_advice'] = test_health_advice()
    
    # Test 4: Conversational context
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 3: CONVERSATIONAL CONTEXT")
    print(f"{'='*50}{Style.RESET_ALL}")
    test_results['conversational_context'] = test_conversational_context()
    
    # Test 5: Daily tips
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 4: DAILY TIPS GENERATION")
    print(f"{'='*50}{Style.RESET_ALL}")
    test_results['daily_tips'] = test_daily_tips()
    
    # Test 6: Interactive chat (optional)
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"TEST 5: INTERACTIVE CHAT (OPTIONAL)")
    print(f"{'='*50}{Style.RESET_ALL}")
    
    choice = input(f"{Fore.YELLOW}🤔 Do you want to test interactive chat? (y/n): {Style.RESET_ALL}").lower()
    if choice in ['y', 'yes']:
        test_results['interactive_chat'] = test_interactive_chat()
    else:
        test_results['interactive_chat'] = True  # Skip
        print(f"{Fore.CYAN}⏭️ Skipping interactive chat test{Style.RESET_ALL}")
    
    # Summary
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = f"{Fore.GREEN}✅ PASS" if result else f"{Fore.RED}❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}{Style.RESET_ALL}")
    
    print(f"\n📈 Overall Result: {passed_tests}/{total_tests} tests passed")
    print(f"📁 Logs saved to: {log_file}")
    
    if passed_tests == total_tests:
        print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED! LLM service is working correctly.{Style.RESET_ALL}")
        return True
    else:
        print(f"\n{Fore.YELLOW}⚠️ Some tests failed. Check logs for details.{Style.RESET_ALL}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)
