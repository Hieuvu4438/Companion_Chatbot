"""
Emotion Detection Demo - Kiểm tra khả năng nhận diện cảm xúc và tối ưu phản hồi
Chạy: python test_emotion_demo.py
"""

import os
import sys
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from config import *
    from utils.llm_service import LLMService
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Make sure to install required packages: pip install -r requirements.txt")
    sys.exit(1)

def display_emotion_result(text, emotion_result):
    """Display emotion detection result in a formatted way"""
    print(f"\n{Fore.WHITE}📝 Input: '{text}'{Style.RESET_ALL}")
    
    if emotion_result['has_emotion']:
        primary = emotion_result['primary_emotion']
        confidence = emotion_result['confidence_scores'].get(primary, 0)
        context = emotion_result['emotion_context']
        all_emotions = emotion_result['detected_emotions']
        
        print(f"🎭 Primary emotion: {Fore.YELLOW}{primary}{Style.RESET_ALL}")
        print(f"📊 Confidence: {Fore.GREEN}{confidence:.2f}{Style.RESET_ALL}")
        print(f"💡 Context: {context}")
        
        if len(all_emotions) > 1:
            print(f"📋 All detected: {', '.join(all_emotions)}")
            
        # Show confidence scores for all detected emotions
        if len(emotion_result['confidence_scores']) > 1:
            print(f"📈 Confidence scores:")
            for emotion, score in emotion_result['confidence_scores'].items():
                print(f"   - {emotion}: {score:.2f}")
    else:
        print(f"😐 No specific emotion detected")

def test_predefined_samples():
    """Test emotion detection with predefined samples"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"🧪 TESTING PREDEFINED EMOTION SAMPLES")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Initialize LLM service
    llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
    
    # Test samples categorized by emotion
    test_samples = {
        "Buồn & Cô đơn": [
            "Tôi cảm thấy buồn và cô đơn quá",
            "Hôm nay tôi khóc vì nhớ chồng đã mất",
            "Tôi thấy tủi thân, không ai hiểu tôi"
        ],
        "Nhớ quê": [
            "Tôi nhớ quê hương lắm",
            "Xa nhà này, tôi nhớ cố hương ghê",
            "Nhớ quê nhà và những ngày xưa"
        ],
        "Lo lắng": [
            "Tôi lo lắng về tương lai của con cháu",
            "Sức khỏe yếu, tôi sợ bị bệnh nặng",
            "Tôi hồi hộp không biết kết quả khám bệnh ra sao"
        ],
        "Vui vẻ": [
            "Hôm nay tôi rất vui vì được gặp cháu",
            "Tôi mừng lắm khi nghe tin con trai thăng chức",
            "Cảm thấy phấn khởi vì sức khỏe đỡ hơn"
        ],
        "Bệnh tật": [
            "Đầu tôi đau và cảm thấy chóng mặt",
            "Gần đây tôi hay mệt mỏi và không khỏe",
            "Bệnh tim của tôi tái phát, tôi lo lắm"
        ],
        "Gia đình": [
            "Con cháu tôi rất hiếu thảo",
            "Gia đình tôi sum vầy trong dịp Tết",
            "Cháu nội vừa sinh, tôi làm bà cố rồi"
        ]
    }
    
    for category, samples in test_samples.items():
        print(f"\n{Fore.CYAN}📂 Category: {category}{Style.RESET_ALL}")
        print("-" * 50)
        
        for i, sample in enumerate(samples, 1):
            emotion_result = llm_service.detect_emotion(sample)
            print(f"\n{Fore.MAGENTA}Sample {i}:{Style.RESET_ALL}")
            display_emotion_result(sample, emotion_result)

def test_mixed_emotions():
    """Test samples with mixed or complex emotions"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"🌈 TESTING MIXED/COMPLEX EMOTIONS")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
    
    mixed_samples = [
        "Tôi vui vì con cháu thăm nhưng cũng buồn vì họ phải đi",
        "Nhớ quê lắm nhưng ở đây con cháu chăm sóc tốt",
        "Lo lắng về bệnh tật nhưng gia đình luôn bên cạnh",
        "Đau ốm nhưng tôi vẫn cố gắng vui vẻ",
        "Hạnh phúc được làm bà nhưng sợ không biết chăm cháu"
    ]
    
    for i, sample in enumerate(mixed_samples, 1):
        emotion_result = llm_service.detect_emotion(sample)
        print(f"\n{Fore.MAGENTA}Mixed Sample {i}:{Style.RESET_ALL}")
        display_emotion_result(sample, emotion_result)

def test_response_optimization():
    """Test emotion-optimized responses"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"🤖 TESTING EMOTION-OPTIMIZED RESPONSES")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
    
    test_inputs = [
        "Tôi buồn vì cô đơn quá",
        "Lo lắng về sức khỏe của mình",
        "Hôm nay con cháu về thăm, tôi vui lắm",
        "Đầu tôi đau, không biết có sao không",
        "Nhớ quê nhà và những người thân"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n{Fore.CYAN}{'='*40}")
        print(f"Test Response {i}")
        print(f"{'='*40}{Style.RESET_ALL}")
        
        # Detect emotion
        emotion_result = llm_service.detect_emotion(user_input)
        display_emotion_result(user_input, emotion_result)
        
        # Get optimized response
        print(f"\n{Fore.YELLOW}🤖 Generating emotion-optimized response...{Style.RESET_ALL}")
        
        response, usage_info, success = llm_service.get_emotion_optimized_response(user_input)
        
        if success:
            print(f"\n{Fore.GREEN}✅ Response:{Style.RESET_ALL}")
            print(f"💬 '{response}'")
            
            # Show token usage
            tokens = usage_info.get('total_tokens', 'N/A')
            print(f"📊 Tokens used: {tokens}")
            print(f"📏 Response length: {len(response)} characters")
            
        else:
            print(f"\n{Fore.RED}❌ Failed to generate response{Style.RESET_ALL}")

def interactive_emotion_test():
    """Interactive emotion detection test"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"💬 INTERACTIVE EMOTION TEST")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    print(f"{Fore.YELLOW}Enter your own text to test emotion detection and response generation.")
    print(f"Type 'quit' to exit.{Style.RESET_ALL}")
    
    llm_service = LLMService(GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS)
    
    while True:
        user_input = input(f"\n{Fore.CYAN}👉 Your message: {Style.RESET_ALL}").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print(f"{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}")
            break
            
        if not user_input:
            print(f"{Fore.YELLOW}⚠️ Please enter some text{Style.RESET_ALL}")
            continue
        
        # Detect emotion
        emotion_result = llm_service.detect_emotion(user_input)
        display_emotion_result(user_input, emotion_result)
        
        # Ask if user wants response
        want_response = input(f"\n{Fore.YELLOW}🤖 Generate optimized response? (y/n): {Style.RESET_ALL}").strip().lower()
        
        if want_response in ['y', 'yes', 'có']:
            print(f"\n{Fore.YELLOW}Generating response...{Style.RESET_ALL}")
            
            response, usage_info, success = llm_service.get_emotion_optimized_response(user_input)
            
            if success:
                print(f"\n{Fore.GREEN}✅ Response:{Style.RESET_ALL}")
                print(f"💬 '{response}'")
                
                tokens = usage_info.get('total_tokens', 'N/A')
                print(f"\n📊 Response stats:")
                print(f"   - Tokens: {tokens}")
                print(f"   - Length: {len(response)} characters")
                print(f"   - Word count: {len(response.split())} words")
            else:
                print(f"\n{Fore.RED}❌ Failed to generate response{Style.RESET_ALL}")

def main():
    """Main function"""
    print(f"{Fore.BLUE}{'='*70}")
    print(f"🎭 EMOTION DETECTION & RESPONSE OPTIMIZATION DEMO")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    # Check configuration
    if not GEMINI_API_KEY:
        print(f"\n{Fore.RED}❌ CONFIGURATION ERROR{Style.RESET_ALL}")
        print("📋 Missing GEMINI_API_KEY in configuration")
        print("💡 Please check your .env file")
        return False
    
    print(f"\n{Fore.CYAN}🎯 SELECT TEST MODE:{Style.RESET_ALL}")
    print(f"1. Test Predefined Emotion Samples")
    print(f"2. Test Mixed/Complex Emotions")
    print(f"3. Test Response Optimization")
    print(f"4. Interactive Emotion Test")
    print(f"5. Run All Tests")
    
    while True:
        choice = input(f"\n{Fore.CYAN}👉 Enter choice (1-5): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            test_predefined_samples()
            break
        elif choice == "2":
            test_mixed_emotions()
            break
        elif choice == "3":
            test_response_optimization()
            break
        elif choice == "4":
            interactive_emotion_test()
            break
        elif choice == "5":
            test_predefined_samples()
            test_mixed_emotions()
            test_response_optimization()
            print(f"\n{Fore.GREEN}✅ All automated tests completed!{Style.RESET_ALL}")
            
            want_interactive = input(f"\n{Fore.YELLOW}🤔 Run interactive test too? (y/n): {Style.RESET_ALL}").strip().lower()
            if want_interactive in ['y', 'yes', 'có']:
                interactive_emotion_test()
            break
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please enter 1-5.{Style.RESET_ALL}")
    
    print(f"\n{Fore.BLUE}{'='*70}")
    print(f"📊 EMOTION DEMO COMPLETED")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}🎉 Demo finished successfully!{Style.RESET_ALL}")
    print(f"💡 Key features demonstrated:")
    print(f"   - Emotion keyword detection")
    print(f"   - Context-aware response generation")
    print(f"   - Optimized prompt engineering")
    print(f"   - Shortened response length")
    print(f"   - Elder-friendly communication style")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Demo interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)
