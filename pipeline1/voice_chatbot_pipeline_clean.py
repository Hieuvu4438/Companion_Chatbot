"""
Pipeline hoàn chỉnh: STT + LLMs + TTS
Voice-to-Voice Chatbot cho người cao tuổi với real-time metrics
"""

import os
import time
import json
import tempfile
import threading
import wave
from datetime import datetime
import logging

# Import các components
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️  PyAudio không có - Sẽ không thể ghi âm real-time")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

# Google Cloud APIs
from google.cloud import speech
from google.cloud import texttospeech
import google.generativeai as genai

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceChatbotPipeline:
    def __init__(self, gemini_api_key, google_credentials_path=None):
        """
        Khởi tạo pipeline hoàn chỉnh
        Args:
            gemini_api_key: API key của Gemini
            google_credentials_path: Đường dẫn credentials Google Cloud
        """
        print("🚀 Khởi tạo Voice Chatbot Pipeline...")
        
        # Cấu hình Google Cloud
        if google_credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credentials_path
        
        # Khởi tạo clients
        try:
            self.stt_client = speech.SpeechClient()
            self.tts_client = texttospeech.TextToSpeechClient()
            print("✅ Đã kết nối Google Cloud STT & TTS")
        except Exception as e:
            print(f"❌ Lỗi kết nối Google Cloud: {e}")
            raise
        
        # Khởi tạo Gemini
        try:
            genai.configure(api_key=gemini_api_key)
            self.llm_model = genai.GenerativeModel("gemini-2.0-flash-exp")
            print("✅ Đã kết nối Gemini LLMs")
        except Exception as e:
            print(f"❌ Lỗi kết nối Gemini: {e}")
            raise
        
        # Cấu hình STT
        self.stt_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="vi-VN",
            enable_automatic_punctuation=True,
            enable_word_confidence=True,
            model="latest_long"
        )
        
        # Cấu hình TTS
        self.tts_voice = texttospeech.VoiceSelectionParams(
            language_code="vi-VN",
            name="vi-VN-Neural2-A"  # Giọng nữ Neural2 chất lượng cao
        )
        
        self.tts_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
            volume_gain_db=0.0,
            effects_profile_id=["headphone-class-device"]
        )
        
        # Khởi tạo audio player
        self.setup_audio_player()
        
        # Load prompt cho người cao tuổi (từ file test.py)
        self.setup_elderly_prompt()
        
        # Khởi tạo chat session
        self.chat_session = None
        
        # Metrics tracking
        self.metrics = {
            "total_conversations": 0,
            "stt_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0,
                "confidence_scores": []
            },
            "llm_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0,
                "total_tokens": 0
            },
            "tts_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0,
                "total_characters": 0
            },
            "pipeline_metrics": {
                "total_end_to_end_latency": 0,
                "average_response_time": 0
            }
        }
        
        print("🎉 Pipeline đã sẵn sàng!")
    
    def setup_audio_player(self):
        """Thiết lập audio player"""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.audio_player = "pygame"
                print("🔊 Audio player: Pygame")
            except:
                self.audio_player = "playsound" if PLAYSOUND_AVAILABLE else None
        else:
            self.audio_player = "playsound" if PLAYSOUND_AVAILABLE else None
        
        if not self.audio_player:
            print("⚠️  Không có audio player - Chỉ lưu file âm thanh")
    
    def setup_elderly_prompt(self):
        """Thiết lập prompt tối ưu cho người cao tuổi"""
        self.elderly_prompt = """
Bạn là một người bạn thân thiết, ấm áp và giàu kinh nghiệm, đặc biệt được thiết kế để hỗ trợ và tâm sự với người cao tuổi.

NGUYÊN TẮC VÀNG:
• TRẢ LỜI NGẮN GỌN: Tối đa 2-3 câu, dễ hiểu
• GIỌNG ĐIỆU ẤM ÁP: Gọi "bác", tự xưng "cháu"  
• ĐỒNG CẢM VÀ LẮNG NGHE: Hiểu cảm xúc, chia sẻ
• THÂN THIỆN: Như người bạn tâm giao, không phải AI
• TRÁNH PHỨC TẠP: Không dùng thuật ngữ khó hiểu

PHONG CÁCH TRẢ LỜI:
• Nếu bác buồn → An ủi: "Cháu hiểu bác buồn, có cháu đây mà"
• Nếu bác nhớ quê → Chia sẻ: "Xa quê lòng nao nao, bác nhớ món gì nhất?"
• Nếu bác lo lắng → Động viên: "Bác đừng lo, mọi chuyện sẽ ổn"
• Nếu bác vui → Hưởng ứng: "Nghe bác vui, cháu cũng vui theo"

CHỦ ĐỀ HỖ TRỢ:
🏠 Quê hương: Món ăn, phong cảnh, hoài niệm
👨‍👩‍👧‍👦 Gia đình: Liên lạc con cháu, truyền thống
💊 Sức khỏe: Thuốc nam, bài tập, chế độ ăn
📚 Lịch sử: Kể chuyện, nhân vật, sự kiện  
🙏 Tâm linh: Phật giáo, thờ cúng, lễ hội

QUAN TRỌNG: Luôn trả lời như người bạn thật, không nhắc đến việc mình là AI.
"""
    
    def record_audio(self, duration=5, filename=None):
        """
        Ghi âm từ microphone
        Args:
            duration: Thời gian ghi âm (giây)
            filename: Tên file (nếu None sẽ tạo tự động)
        Returns:
            str: Đường dẫn file audio
        """
        if not PYAUDIO_AVAILABLE:
            raise Exception("PyAudio không có - Không thể ghi âm")
        
        if filename is None:
            filename = f"recorded_audio_{int(time.time())}.wav"
        
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        print(f"🎤 Ghi âm trong {duration} giây... HÃY NÓI!")
        
        audio = pyaudio.PyAudio()
        
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        print("✅ Hoàn thành ghi âm!")
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Lưu file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        return filename
    
    def speech_to_text(self, audio_file_path):
        """
        Chuyển đổi speech thành text
        Args:
            audio_file_path: Đường dẫn file audio
        Returns:
            dict: Kết quả STT với metrics
        """
        start_time = time.time()
        
        try:
            # Đọc file audio
            with open(audio_file_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Gửi request
            response = self.stt_client.recognize(config=self.stt_config, audio=audio)
            
            latency = time.time() - start_time
            
            if response.results:
                result = response.results[0]
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence
                
                # Cập nhật metrics
                self.update_stt_metrics(latency, confidence, True)
                
                return {
                    'success': True,
                    'transcript': transcript,
                    'confidence': confidence,
                    'latency_ms': latency * 1000
                }
            else:
                self.update_stt_metrics(latency, 0, False)
                return {
                    'success': False,
                    'error': 'Không nhận diện được giọng nói',
                    'latency_ms': latency * 1000
                }
                
        except Exception as e:
            latency = time.time() - start_time
            self.update_stt_metrics(latency, 0, False)
            logger.error(f"STT Error: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'latency_ms': latency * 1000
            }
    
    def generate_llm_response(self, user_text):
        """
        Tạo phản hồi từ LLMs (Gemini)
        Args:
            user_text: Text từ người dùng
        Returns:
            dict: Kết quả LLM với metrics
        """
        start_time = time.time()
        
        try:
            # Khởi tạo chat session nếu chưa có
            if self.chat_session is None:
                self.chat_session = self.llm_model.start_chat(
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
            
            # Gửi message
            response = self.chat_session.send_message(user_text)
            
            latency = time.time() - start_time
            
            # Làm sạch response
            cleaned_response = self.clean_response(response.text)
            
            # Ước tính tokens (rough)
            estimated_tokens = len(user_text.split()) + len(cleaned_response.split())
            
            # Cập nhật metrics
            self.update_llm_metrics(latency, estimated_tokens, True)
            
            return {
                'success': True,
                'response': cleaned_response,
                'latency_ms': latency * 1000,
                'estimated_tokens': estimated_tokens
            }
            
        except Exception as e:
            latency = time.time() - start_time
            self.update_llm_metrics(latency, 0, False)
            logger.error(f"LLM Error: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'latency_ms': latency * 1000
            }
    
    def text_to_speech(self, text, output_file=None):
        """
        Chuyển đổi text thành speech
        Args:
            text: Text cần chuyển đổi
            output_file: File output (nếu None sẽ tạo tự động)
        Returns:
            dict: Kết quả TTS với metrics
        """
        start_time = time.time()
        
        try:
            # Tạo synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Gửi request
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.tts_voice,
                audio_config=self.tts_config
            )
            
            latency = time.time() - start_time
            
            # Lưu audio
            if output_file is None:
                output_file = f"tts_output_{int(time.time())}.mp3"
            
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            
            # Cập nhật metrics
            self.update_tts_metrics(latency, len(text), True)
            
            return {
                'success': True,
                'audio_file': output_file,
                'text': text,
                'latency_ms': latency * 1000,
                'character_count': len(text)
            }
            
        except Exception as e:
            latency = time.time() - start_time
            self.update_tts_metrics(latency, len(text), False)
            logger.error(f"TTS Error: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'latency_ms': latency * 1000
            }
    
    def play_audio(self, audio_file_path):
        """Phát audio"""
        try:
            if self.audio_player == "pygame":
                pygame.mixer.music.load(audio_file_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
            elif self.audio_player == "playsound":
                playsound(audio_file_path)
            else:
                print(f"⚠️  Không thể phát audio. File: {audio_file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            return False
    
    def run_full_pipeline(self, record_duration=5):
        """
        Chạy pipeline hoàn chỉnh: STT → LLM → TTS → Play
        Args:
            record_duration: Thời gian ghi âm (giây)
        Returns:
            dict: Kết quả pipeline với metrics
        """
        pipeline_start_time = time.time()
        
        print("🔄 === BẮT ĐẦU PIPELINE ===")
        
        # Bước 1: Ghi âm + STT
        print("📝 Bước 1: Ghi âm và nhận diện giọng nói...")
        
        try:
            audio_file = self.record_audio(record_duration)
            stt_result = self.speech_to_text(audio_file)
            
            if not stt_result['success']:
                return {
                    'success': False,
                    'error': f"STT failed: {stt_result['error']}",
                    'pipeline_latency_ms': (time.time() - pipeline_start_time) * 1000
                }
            
            user_text = stt_result['transcript']
            print(f"👤 Người dùng nói: \"{user_text}\"")
            print(f"🎯 Confidence: {stt_result['confidence']:.2f}")
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Audio recording failed: {e}",
                'pipeline_latency_ms': (time.time() - pipeline_start_time) * 1000
            }
        
        # Bước 2: LLM Response
        print("🤖 Bước 2: Tạo phản hồi từ AI...")
        
        llm_result = self.generate_llm_response(user_text)
        
        if not llm_result['success']:
            return {
                'success': False,
                'error': f"LLM failed: {llm_result['error']}",
                'stt_result': stt_result,
                'pipeline_latency_ms': (time.time() - pipeline_start_time) * 1000
            }
        
        ai_response = llm_result['response']
        print(f"🤖 AI phản hồi: \"{ai_response}\"")
        
        # Bước 3: TTS + Play
        print("🔊 Bước 3: Chuyển đổi thành giọng nói và phát...")
        
        tts_result = self.text_to_speech(ai_response)
        
        if not tts_result['success']:
            return {
                'success': False,
                'error': f"TTS failed: {tts_result['error']}",
                'stt_result': stt_result,
                'llm_result': llm_result,
                'pipeline_latency_ms': (time.time() - pipeline_start_time) * 1000
            }
        
        # Phát âm thanh
        play_success = self.play_audio(tts_result['audio_file'])
        
        # Tính tổng thời gian pipeline
        total_pipeline_time = time.time() - pipeline_start_time
        
        # Cập nhật metrics tổng thể
        self.metrics["total_conversations"] += 1
        self.metrics["pipeline_metrics"]["total_end_to_end_latency"] += total_pipeline_time
        self.metrics["pipeline_metrics"]["average_response_time"] = (
            self.metrics["pipeline_metrics"]["total_end_to_end_latency"] / 
            self.metrics["total_conversations"]
        )
        
        print("✅ Pipeline hoàn thành!")
        
        # Cleanup files
        try:
            os.unlink(audio_file)
            os.unlink(tts_result['audio_file'])
        except:
            pass
        
        return {
            'success': True,
            'user_text': user_text,
            'ai_response': ai_response,
            'stt_result': stt_result,
            'llm_result': llm_result,
            'tts_result': tts_result,
            'audio_played': play_success,
            'pipeline_latency_ms': total_pipeline_time * 1000,
            'timestamp': datetime.now().isoformat()
        }
    
    def clean_response(self, text):
        """Làm sạch response từ LLM"""
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
    
    def update_stt_metrics(self, latency, confidence, success):
        """Cập nhật STT metrics"""
        stt = self.metrics["stt_metrics"]
        stt["total_requests"] += 1
        stt["total_latency"] += latency
        
        if success:
            stt["successful_requests"] += 1
            stt["confidence_scores"].append(confidence)
        else:
            stt["failed_requests"] += 1
    
    def update_llm_metrics(self, latency, tokens, success):
        """Cập nhật LLM metrics"""
        llm = self.metrics["llm_metrics"]
        llm["total_requests"] += 1
        llm["total_latency"] += latency
        
        if success:
            llm["successful_requests"] += 1
            llm["total_tokens"] += tokens
        else:
            llm["failed_requests"] += 1
    
    def update_tts_metrics(self, latency, char_count, success):
        """Cập nhật TTS metrics"""
        tts = self.metrics["tts_metrics"]
        tts["total_requests"] += 1
        tts["total_latency"] += latency
        tts["total_characters"] += char_count
        
        if success:
            tts["successful_requests"] += 1
        else:
            tts["failed_requests"] += 1
    
    def get_metrics_report(self):
        """Tạo báo cáo metrics chi tiết"""
        def safe_divide(a, b):
            return a / b if b > 0 else 0
        
        stt = self.metrics["stt_metrics"]
        llm = self.metrics["llm_metrics"]
        tts = self.metrics["tts_metrics"]
        pipeline = self.metrics["pipeline_metrics"]
        
        report = {
            "📊 TỔNG QUAN PIPELINE": {
                "Tổng số cuộc hội thoại": self.metrics["total_conversations"],
                "Thời gian phản hồi trung bình": f"{pipeline['average_response_time'] * 1000:.2f}ms"
            },
            "🎤 STT METRICS": {
                "Tổng requests": stt["total_requests"],
                "Thành công": stt["successful_requests"],
                "Thất bại": stt["failed_requests"],
                "Tỷ lệ thành công": f"{safe_divide(stt['successful_requests'], stt['total_requests']) * 100:.1f}%",
                "Latency trung bình": f"{safe_divide(stt['total_latency'], stt['total_requests']) * 1000:.2f}ms",
                "Confidence trung bình": f"{safe_divide(sum(stt['confidence_scores']), len(stt['confidence_scores'])):.2f}" if stt['confidence_scores'] else "N/A"
            },
            "🤖 LLM METRICS": {
                "Tổng requests": llm["total_requests"],
                "Thành công": llm["successful_requests"],
                "Thất bại": llm["failed_requests"],
                "Tỷ lệ thành công": f"{safe_divide(llm['successful_requests'], llm['total_requests']) * 100:.1f}%",
                "Latency trung bình": f"{safe_divide(llm['total_latency'], llm['total_requests']) * 1000:.2f}ms",
                "Tokens trung bình": f"{safe_divide(llm['total_tokens'], llm['successful_requests']):.1f}" if llm['successful_requests'] > 0 else "N/A"
            },
            "🔊 TTS METRICS": {
                "Tổng requests": tts["total_requests"],
                "Thành công": tts["successful_requests"],
                "Thất bại": tts["failed_requests"],
                "Tỷ lệ thành công": f"{safe_divide(tts['successful_requests'], tts['total_requests']) * 100:.1f}%",
                "Latency trung bình": f"{safe_divide(tts['total_latency'], tts['total_requests']) * 1000:.2f}ms",
                "Ký tự trung bình": f"{safe_divide(tts['total_characters'], tts['total_requests']):.1f}"
            }
        }
        
        return report
    
    def save_metrics(self, filename="pipeline_metrics.json"):
        """Lưu metrics ra file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'raw_metrics': self.metrics,
                'report': self.get_metrics_report(),
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        print(f"📁 Đã lưu metrics vào {filename}")
    
    def reset_metrics(self):
        """Reset tất cả metrics"""
        self.metrics = {
            "total_conversations": 0,
            "stt_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0,
                "confidence_scores": []
            },
            "llm_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0,
                "total_tokens": 0
            },
            "tts_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0,
                "total_characters": 0
            },
            "pipeline_metrics": {
                "total_end_to_end_latency": 0,
                "average_response_time": 0
            }
        }
        print("🔄 Đã reset tất cả metrics")


def main():
    """Hàm main để chạy pipeline"""
    print("🎤🤖🔊 === VOICE CHATBOT PIPELINE FOR ELDERLY ===\n")
    
    # API keys và credentials
    GEMINI_API_KEY = "AIzaSyBtARGbaM83LV6awCe4FiQK3bD4SErVn7s"
    GOOGLE_CREDENTIALS_PATH = None  # Thay đổi nếu cần
    
    print("⚠️  LƯU Ý QUAN TRỌNG:")
    print("   1. Cần cài đặt Google Cloud credentials")
    print("   2. Cần microphone để ghi âm")
    print("   3. Cần speakers/headphones để nghe")
    print("   4. Kết nối internet ổn định\n")
    
    # Khởi tạo pipeline
    try:
        pipeline = VoiceChatbotPipeline(GEMINI_API_KEY, GOOGLE_CREDENTIALS_PATH)
    except Exception as e:
        print(f"❌ Lỗi khởi tạo pipeline: {e}")
        print("   Vui lòng kiểm tra API keys và credentials")
        return
    
    while True:
        print("\n" + "="*60)
        print("CHỌN CHỨC NĂNG:")
        print("1. 🎤 Chạy pipeline hoàn chỉnh (Voice-to-Voice)")
        print("2. 📊 Xem metrics hiện tại")
        print("3. 💾 Lưu metrics ra file")
        print("4. 🔄 Reset metrics")
        print("5. ⚙️  Test từng component riêng")
        print("0. 🚪 Thoát")
        
        choice = input("\nNhập lựa chọn (0-5): ").strip()
        
        if choice == "1":
            # Chạy pipeline hoàn chỉnh
            duration = input("Thời gian ghi âm (giây, mặc định 5): ").strip()
            duration = int(duration) if duration.isdigit() else 5
            
            print(f"\n🚀 Chuẩn bị chạy pipeline với {duration}s ghi âm...")
            print("Sẵn sàng chưa? (Enter để tiếp tục)")
            input()
            
            result = pipeline.run_full_pipeline(duration)
            
            if result['success']:
                print(f"\n✅ === KẾT QUẢ PIPELINE ===\n")
                print(f"👤 Người dùng: {result['user_text']}")
                print(f"🤖 AI phản hồi: {result['ai_response']}")
                print(f"\n📊 METRICS:")
                print(f"   STT Latency: {result['stt_result']['latency_ms']:.2f}ms")
                print(f"   STT Confidence: {result['stt_result']['confidence']:.2f}")
                print(f"   LLM Latency: {result['llm_result']['latency_ms']:.2f}ms")
                print(f"   TTS Latency: {result['tts_result']['latency_ms']:.2f}ms")
                print(f"   📈 Tổng thời gian: {result['pipeline_latency_ms']:.2f}ms")
                print(f"   🔊 Phát audio: {'✅' if result['audio_played'] else '❌'}")
            else:
                print(f"\n❌ LỖI PIPELINE: {result['error']}")
                print(f"   Thời gian xử lý: {result['pipeline_latency_ms']:.2f}ms")
        
        elif choice == "2":
            # Xem metrics
            print("\n📊 === METRICS REPORT ===\n")
            report = pipeline.get_metrics_report()
            for section, data in report.items():
                print(f"{section}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                print()
        
        elif choice == "3":
            # Lưu metrics
            filename = input("Tên file (mặc định pipeline_metrics.json): ").strip()
            filename = filename if filename else "pipeline_metrics.json"
            pipeline.save_metrics(filename)
        
        elif choice == "4":
            # Reset metrics
            confirm = input("Xác nhận reset metrics? (y/N): ").strip().lower()
            if confirm == 'y':
                pipeline.reset_metrics()
            else:
                print("Hủy reset")
        
        elif choice == "5":
            # Test từng component
            print("\n🔧 TEST COMPONENT RIÊNG:")
            print("1. Test STT")
            print("2. Test LLM")
            print("3. Test TTS")
            
            component_choice = input("Chọn component (1-3): ").strip()
            
            if component_choice == "1":
                # Test STT
                duration = int(input("Thời gian ghi âm (giây): ") or "5")
                
                try:
                    audio_file = pipeline.record_audio(duration)
                    result = pipeline.speech_to_text(audio_file)
                    
                    if result['success']:
                        print(f"✅ STT: {result['transcript']} (Confidence: {result['confidence']:.2f})")
                    else:
                        print(f"❌ STT Error: {result['error']}")
                    
                    os.unlink(audio_file)
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif component_choice == "2":
                # Test LLM
                text = input("Nhập text để test LLM: ").strip()
                if text:
                    result = pipeline.generate_llm_response(text)
                    
                    if result['success']:
                        print(f"✅ LLM: {result['response']}")
                    else:
                        print(f"❌ LLM Error: {result['error']}")
            
            elif component_choice == "3":
                # Test TTS
                text = input("Nhập text để test TTS: ").strip()
                if text:
                    result = pipeline.text_to_speech(text)
                    
                    if result['success']:
                        print(f"✅ TTS: File {result['audio_file']}")
                        pipeline.play_audio(result['audio_file'])
                        os.unlink(result['audio_file'])
                    else:
                        print(f"❌ TTS Error: {result['error']}")
        
        elif choice == "0":
            print("👋 Tạm biệt! Cảm ơn bạn đã sử dụng Voice Chatbot Pipeline!")
            break
        
        else:
            print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    main()
