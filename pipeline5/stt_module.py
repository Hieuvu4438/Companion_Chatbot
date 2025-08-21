#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assembly AI STT Module
======================

Speech-to-Text module sử dụng Assembly AI API cho pipeline chatbot hỗ trợ người cao tuổi
"""

import os
import sys
import time
import json
import wave
import pyaudio
import requests
import threading
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

try:
    from config import *
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import *


class AudioRecorder:
    """Class để ghi âm từ microphone"""
    
    def __init__(self):
        self.chunk = AUDIO_CHUNK_SIZE
        self.format = pyaudio.paInt16
        self.channels = AUDIO_CHANNELS
        self.rate = AUDIO_SAMPLE_RATE
        self.recording = False
        self.frames = []
        
    def record_audio(self, duration: float = 5.0) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Ghi âm từ microphone
        
        Args:
            duration: Thời gian ghi âm (giây)
            
        Returns:
            Tuple[success, audio_file_path, error_message]
        """
        try:
            audio = pyaudio.PyAudio()
            
            # Mở stream
            stream = audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print(f"🎤 Đang ghi âm trong {duration} giây...")
            
            frames = []
            for i in range(int(self.rate / self.chunk * duration)):
                data = stream.read(self.chunk)
                frames.append(data)
                
            print("🔴 Kết thúc ghi âm")
            
            # Dọn dẹp
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Lưu file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            filepath = os.path.join(AUDIO_INPUT_DIR, filename)
            
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return True, filepath, None
            
        except Exception as e:
            return False, None, str(e)
    
    def start_continuous_recording(self):
        """Bắt đầu ghi âm liên tục"""
        self.recording = True
        self.frames = []
        
        def record_loop():
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            while self.recording:
                data = stream.read(self.chunk)
                self.frames.append(data)
                
            stream.stop_stream()
            stream.close()
            audio.terminate()
        
        self.record_thread = threading.Thread(target=record_loop)
        self.record_thread.start()
    
    def stop_continuous_recording(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Dừng ghi âm liên tục và lưu file"""
        if not self.recording:
            return False, None, "Không có recording nào đang chạy"
            
        self.recording = False
        self.record_thread.join()
        
        if not self.frames:
            return False, None, "Không có dữ liệu âm thanh"
            
        try:
            # Lưu file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"continuous_recording_{timestamp}.wav"
            filepath = os.path.join(AUDIO_INPUT_DIR, filename)
            
            audio = pyaudio.PyAudio()
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            audio.terminate()
            
            self.frames = []
            return True, filepath, None
            
        except Exception as e:
            return False, None, str(e)


class AssemblyAISTT:
    """Assembly AI Speech-to-Text service"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ASSEMBLY_API_KEY
        if not self.api_key:
            raise ValueError("Assembly AI API key is required")
            
        self.base_url = ASSEMBLY_API_URL
        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
        
    def test_connection(self) -> bool:
        """Test kết nối với Assembly AI API"""
        try:
            response = requests.get(
                f"{self.base_url}/transcript",
                headers=self.headers,
                timeout=10
            )
            return response.status_code in [200, 404]  # 404 is expected for empty transcript list
        except Exception:
            return False
    
    def upload_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload file âm thanh lên Assembly AI
        
        Args:
            file_path: Đường dẫn file âm thanh
            
        Returns:
            Dict chứa upload_url hoặc error
        """
        try:
            start_time = time.time()
            
            def read_file(filename):
                with open(filename, 'rb') as f:
                    while True:
                        data = f.read(5242880)  # 5MB chunks
                        if not data:
                            break
                        yield data
            
            response = requests.post(
                f"{self.base_url}/upload",
                headers={"authorization": self.api_key},
                data=read_file(file_path)
            )
            
            upload_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "upload_url": result["upload_url"],
                    "upload_time_ms": upload_time
                }
            else:
                return {
                    "success": False,
                    "error": f"Upload failed: {response.status_code} - {response.text}",
                    "upload_time_ms": upload_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload error: {str(e)}",
                "upload_time_ms": 0
            }
    
    def submit_transcription(self, audio_url: str, config: Dict = None) -> Dict[str, Any]:
        """
        Gửi yêu cầu transcription đến Assembly AI
        
        Args:
            audio_url: URL của file âm thanh đã upload
            config: Cấu hình transcription tùy chọn
            
        Returns:
            Dict chứa transcript_id hoặc error
        """
        try:
            # Cấu hình mặc định
            transcript_config = {
                "audio_url": audio_url,
                "language_code": ASSEMBLY_LANGUAGE_CODE,
                "punctuate": True,
                "format_text": True,
                "disfluencies": False,  # Loại bỏ "um", "uh" 
                "filter_profanity": True,
                "boost_param": "low"  # Tối ưu cho âm thanh chất lượng thấp
            }
            
            # Merge với config tùy chọn
            if config:
                transcript_config.update(config)
            
            response = requests.post(
                f"{self.base_url}/transcript",
                headers=self.headers,
                json=transcript_config
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "transcript_id": result["id"],
                    "status": result["status"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Transcription submission failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Transcription submission error: {str(e)}"
            }
    
    def get_transcription_result(self, transcript_id: str) -> Dict[str, Any]:
        """
        Lấy kết quả transcription
        
        Args:
            transcript_id: ID của transcription job
            
        Returns:
            Dict chứa kết quả transcription
        """
        try:
            response = requests.get(
                f"{self.base_url}/transcript/{transcript_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result["status"] == "completed":
                    return {
                        "success": True,
                        "status": "completed",
                        "transcript": result["text"],
                        "confidence": result.get("confidence", 0.0),
                        "words": result.get("words", []),
                        "audio_duration": result.get("audio_duration", 0)
                    }
                elif result["status"] == "error":
                    return {
                        "success": False,
                        "status": "error",
                        "error": result.get("error", "Transcription failed")
                    }
                else:
                    return {
                        "success": True,
                        "status": result["status"],  # processing, queued, etc.
                        "transcript": None
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get transcription result: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Get transcription error: {str(e)}"
            }
    
    def wait_for_transcription(self, transcript_id: str, max_wait_time: int = 120) -> Dict[str, Any]:
        """
        Chờ transcription hoàn thành
        
        Args:
            transcript_id: ID của transcription job  
            max_wait_time: Thời gian chờ tối đa (giây)
            
        Returns:
            Dict chứa kết quả final transcription
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            result = self.get_transcription_result(transcript_id)
            
            if not result["success"]:
                return result
                
            if result["status"] == "completed":
                return result
            elif result["status"] == "error":
                return result
            
            # Chờ 2 giây trước khi check lại
            time.sleep(2)
            print(f"⏳ Transcription status: {result['status']}")
        
        return {
            "success": False,
            "error": f"Transcription timeout after {max_wait_time} seconds"
        }
    
    def transcribe_audio_file(self, file_path: str, config: Dict = None) -> Dict[str, Any]:
        """
        Transcribe file âm thanh hoàn chỉnh (upload + transcribe + wait)
        
        Args:
            file_path: Đường dẫn file âm thanh
            config: Cấu hình transcription tùy chọn
            
        Returns:
            Dict chứa kết quả transcription và metrics
        """
        start_time = time.time()
        
        try:
            # Step 1: Upload file
            print("📤 Uploading audio file...")
            upload_result = self.upload_audio_file(file_path)
            
            if not upload_result["success"]:
                return {
                    "success": False,
                    "error": upload_result["error"],
                    "latency_ms": (time.time() - start_time) * 1000
                }
            
            # Step 2: Submit transcription
            print("🔄 Submitting transcription job...")
            transcription_result = self.submit_transcription(
                upload_result["upload_url"], 
                config
            )
            
            if not transcription_result["success"]:
                return {
                    "success": False,
                    "error": transcription_result["error"],
                    "latency_ms": (time.time() - start_time) * 1000
                }
            
            # Step 3: Wait for completion
            print(f"⏳ Waiting for transcription {transcription_result['transcript_id']}...")
            final_result = self.wait_for_transcription(transcription_result["transcript_id"])
            
            total_latency = (time.time() - start_time) * 1000
            
            if final_result["success"] and final_result["status"] == "completed":
                return {
                    "success": True,
                    "transcript": final_result["transcript"],
                    "confidence": final_result["confidence"],
                    "latency_ms": total_latency,
                    "upload_time_ms": upload_result["upload_time_ms"],
                    "audio_duration": final_result.get("audio_duration", 0),
                    "words_count": len(final_result.get("words", [])),
                    "transcript_id": transcription_result["transcript_id"]
                }
            else:
                return {
                    "success": False,
                    "error": final_result.get("error", "Transcription failed"),
                    "latency_ms": total_latency
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Transcription process error: {str(e)}",
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file âm thanh trước khi transcribe
        
        Args:
            file_path: Đường dẫn file âm thanh
            
        Returns:
            Tuple[is_valid, error_message]
        """
        try:
            if not os.path.exists(file_path):
                return False, "File không tồn tại"
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "File rỗng"
                
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                return False, "File quá lớn (> 100MB)"
            
            # Kiểm tra định dạng file
            file_ext = os.path.splitext(file_path)[1].lower()
            supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
            
            if file_ext not in supported_formats:
                return False, f"Định dạng file không được hỗ trợ: {file_ext}"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """Lấy danh sách ngôn ngữ được hỗ trợ"""
        return {
            "success": True,
            "languages": {
                "vi": "Vietnamese (Tiếng Việt)",
                "en": "English",
                "zh": "Chinese (Mandarin)",
                "ja": "Japanese",
                "ko": "Korean",
                # Assembly AI hỗ trợ nhiều ngôn ngữ khác
            },
            "current_language": ASSEMBLY_LANGUAGE_CODE
        }


def main():
    """Test function"""
    print("🧪 Assembly AI STT Module Test")
    print("=" * 40)
    
    try:
        # Test connection
        stt = AssemblyAISTT()
        
        if stt.test_connection():
            print("✅ Assembly AI connection successful")
        else:
            print("❌ Assembly AI connection failed")
            return
        
        # Test audio recording
        recorder = AudioRecorder()
        print("\n🎤 Testing audio recording...")
        print("Speak something for 5 seconds...")
        
        success, audio_file, error = recorder.record_audio(5.0)
        
        if success:
            print(f"✅ Recording successful: {audio_file}")
            
            # Test transcription
            print("\n🔄 Testing transcription...")
            result = stt.transcribe_audio_file(audio_file)
            
            if result["success"]:
                print(f"✅ Transcription successful!")
                print(f"📝 Text: '{result['transcript']}'")
                print(f"🎯 Confidence: {result['confidence']:.2f}")
                print(f"⏱️  Latency: {result['latency_ms']:.1f}ms")
                print(f"📊 Words: {result['words_count']}")
            else:
                print(f"❌ Transcription failed: {result['error']}")
            
            # Cleanup
            if SAVE_AUDIO_FILES and os.path.exists(audio_file):
                os.unlink(audio_file)
                
        else:
            print(f"❌ Recording failed: {error}")
            
        print("\n🎯 STT Module test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()
