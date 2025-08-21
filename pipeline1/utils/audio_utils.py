import pyaudio
import wave
import time
import os
import tempfile
from typing import Optional, Tuple
import logging
import pygame
from pydub import AudioSegment
from pydub.playback import play

class AudioRecorder:
    """
    Lớp ghi âm sử dụng PyAudio
    """
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, 
                 chunk_size: int = 1024, audio_format=pyaudio.paInt16):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio_format = audio_format
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
    def list_devices(self):
        """Liệt kê tất cả audio devices"""
        print("📱 DANH SÁCH AUDIO DEVICES:")
        print("-" * 50)
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            print(f"Device {i}: {device_info['name']}")
            print(f"  Max input channels: {device_info['maxInputChannels']}")
            print(f"  Max output channels: {device_info['maxOutputChannels']}")
            print(f"  Default sample rate: {device_info['defaultSampleRate']}")
            print()
            
    def test_microphone(self, duration: float = 3.0, device_index: Optional[int] = None) -> bool:
        """Test microphone functionality"""
        print(f"🎤 Testing microphone for {duration} seconds...")
        
        try:
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            for _ in range(int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size)
                frames.append(data)
                
            stream.stop_stream()
            stream.close()
            
            print("✅ Microphone test successful!")
            return True
            
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False
            
    def record_audio(self, duration: float, device_index: Optional[int] = None,
                    output_file: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Ghi âm với thời gian xác định
        
        Returns:
            Tuple[success, audio_file_path, error_message]
        """
        
        if output_file is None:
            output_file = os.path.join(tempfile.gettempdir(), f"recording_{int(time.time())}.wav")
            
        try:
            print(f"🎤 Bắt đầu ghi âm trong {duration} giây...")
            print("🔴 Đang ghi âm... Hãy nói rõ ràng!")
            
            # Mở stream để ghi âm
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            start_time = time.time()
            
            # Ghi âm trong khoảng thời gian xác định
            while time.time() - start_time < duration:
                data = stream.read(self.chunk_size)
                frames.append(data)
                
                # Hiển thị progress
                elapsed = time.time() - start_time
                progress = int((elapsed / duration) * 20)
                print(f"\r🎤 [{'=' * progress}{'.' * (20 - progress)}] {elapsed:.1f}s/{duration}s", end='')
                
            print("\n✅ Hoàn thành ghi âm!")
            
            # Dừng và đóng stream
            stream.stop_stream()
            stream.close()
            
            # Lưu file WAV
            with wave.open(output_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
                
            self.logger.info(f"Audio recorded successfully: {output_file}")
            
            # Kiểm tra kích thước file
            file_size = os.path.getsize(output_file)
            print(f"📁 File đã lưu: {output_file} ({file_size} bytes)")
            
            return True, output_file, ""
            
        except Exception as e:
            error_msg = f"Lỗi ghi âm: {str(e)}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False, "", error_msg
            
    def record_with_silence_detection(self, max_duration: float = 60.0,
                                    silence_threshold: float = 0.5,
                                    device_index: Optional[int] = None,
                                    output_file: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Ghi âm với phát hiện im lặng để tự động dừng
        """
        
        if output_file is None:
            output_file = os.path.join(tempfile.gettempdir(), f"recording_vad_{int(time.time())}.wav")
            
        try:
            print(f"🎤 Ghi âm với Voice Activity Detection...")
            print(f"⏱️  Max duration: {max_duration}s, Silence threshold: {silence_threshold}s")
            print("🔴 Bắt đầu nói...")
            
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            start_time = time.time()
            last_sound_time = start_time
            silence_start = None
            
            while time.time() - start_time < max_duration:
                data = stream.read(self.chunk_size)
                frames.append(data)
                
                # Simple volume detection
                volume = max(data)
                current_time = time.time()
                
                if volume > 1000:  # Có âm thanh
                    last_sound_time = current_time
                    silence_start = None
                    print("🎵", end='', flush=True)
                else:  # Im lặng
                    if silence_start is None:
                        silence_start = current_time
                    elif current_time - silence_start > silence_threshold:
                        print(f"\n⏹️  Phát hiện im lặng {silence_threshold}s - Dừng ghi âm")
                        break
                    print(".", end='', flush=True)
                    
            print(f"\n✅ Hoàn thành ghi âm sau {time.time() - start_time:.1f}s")
            
            stream.stop_stream()
            stream.close()
            
            # Lưu file
            with wave.open(output_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
                
            return True, output_file, ""
            
        except Exception as e:
            error_msg = f"Lỗi ghi âm VAD: {str(e)}"
            print(f"❌ {error_msg}")
            return False, "", error_msg
            
    def __del__(self):
        """Cleanup PyAudio"""
        if hasattr(self, 'audio'):
            self.audio.terminate()


class AudioPlayer:
    """
    Lớp phát âm thanh hỗ trợ nhiều format
    """
    
    def __init__(self):
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        self.logger = logging.getLogger(__name__)
        
    def play_wav_file(self, file_path: str) -> Tuple[bool, str]:
        """Phát file WAV sử dụng pygame"""
        try:
            if not os.path.exists(file_path):
                return False, f"File không tồn tại: {file_path}"
                
            print(f"🔊 Đang phát âm thanh: {os.path.basename(file_path)}")
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Chờ phát xong
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            print("✅ Phát âm thanh hoàn thành!")
            return True, ""
            
        except Exception as e:
            error_msg = f"Lỗi phát âm thanh: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
            
    def play_mp3_file(self, file_path: str) -> Tuple[bool, str]:
        """Phát file MP3 sử dụng pydub"""
        try:
            if not os.path.exists(file_path):
                return False, f"File không tồn tại: {file_path}"
                
            print(f"🔊 Đang phát MP3: {os.path.basename(file_path)}")
            
            # Load and play MP3
            audio = AudioSegment.from_mp3(file_path)
            play(audio)
            
            print("✅ Phát MP3 hoàn thành!")
            return True, ""
            
        except Exception as e:
            error_msg = f"Lỗi phát MP3: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
            
    def play_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """Phát file âm thanh (tự động detect format)"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.wav':
                return self.play_wav_file(file_path)
            elif file_ext == '.mp3':
                return self.play_mp3_file(file_path)
            else:
                # Try pygame for other formats
                return self.play_wav_file(file_path)
                
        except Exception as e:
            error_msg = f"Lỗi phát âm thanh: {str(e)}"
            return False, error_msg
            
    def get_audio_info(self, file_path: str) -> dict:
        """Lấy thông tin file âm thanh"""
        try:
            if not os.path.exists(file_path):
                return {"error": "File không tồn tại"}
                
            file_ext = os.path.splitext(file_path)[1].lower()
            file_size = os.path.getsize(file_path)
            
            info = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_size,
                "format": file_ext
            }
            
            if file_ext == '.wav':
                with wave.open(file_path, 'rb') as wf:
                    info.update({
                        "channels": wf.getnchannels(),
                        "sample_rate": wf.getframerate(),
                        "frames": wf.getnframes(),
                        "duration": wf.getnframes() / wf.getframerate(),
                        "sample_width": wf.getsampwidth()
                    })
            elif file_ext == '.mp3':
                audio = AudioSegment.from_mp3(file_path)
                info.update({
                    "channels": audio.channels,
                    "sample_rate": audio.frame_rate,
                    "duration": len(audio) / 1000.0,  # convert to seconds
                    "frame_count": len(audio.raw_data)
                })
                
            return info
            
        except Exception as e:
            return {"error": f"Lỗi đọc thông tin: {str(e)}"}
            
    def convert_audio_format(self, input_file: str, output_file: str, 
                           target_format: str = "wav") -> Tuple[bool, str]:
        """Chuyển đổi format âm thanh"""
        try:
            print(f"🔄 Chuyển đổi {input_file} -> {output_file}")
            
            # Load audio file
            if input_file.endswith('.mp3'):
                audio = AudioSegment.from_mp3(input_file)
            elif input_file.endswith('.wav'):
                audio = AudioSegment.from_wav(input_file)
            else:
                audio = AudioSegment.from_file(input_file)
                
            # Export to target format
            if target_format.lower() == "wav":
                audio.export(output_file, format="wav")
            elif target_format.lower() == "mp3":
                audio.export(output_file, format="mp3")
            else:
                audio.export(output_file, format=target_format)
                
            print(f"✅ Chuyển đổi hoàn thành: {output_file}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Lỗi chuyển đổi: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg


# Utility functions
def cleanup_temp_audio_files(temp_dir: str = None):
    """Dọn dẹp các file âm thanh tạm thời"""
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
        
    try:
        for file_name in os.listdir(temp_dir):
            if (file_name.startswith("recording_") or file_name.startswith("tts_output_")) and \
               (file_name.endswith(".wav") or file_name.endswith(".mp3")):
                file_path = os.path.join(temp_dir, file_name)
                os.remove(file_path)
                print(f"🧹 Đã xóa: {file_name}")
                
        print("✅ Dọn dẹp hoàn thành!")
        
    except Exception as e:
        print(f"❌ Lỗi dọn dẹp: {e}")


def test_audio_system():
    """Test toàn bộ hệ thống âm thanh"""
    print("🧪 TESTING AUDIO SYSTEM")
    print("=" * 40)
    
    # Test microphone
    recorder = AudioRecorder()
    recorder.list_devices()
    
    if recorder.test_microphone(2.0):
        print("✅ Microphone OK")
    else:
        print("❌ Microphone có vấn đề")
        
    # Test audio player
    player = AudioPlayer()
    
    # Tạo file test âm thanh đơn giản
    try:
        import numpy as np
        
        # Generate a simple tone
        sample_rate = 16000
        duration = 1  # seconds
        frequency = 440  # Hz (A note)
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave_data = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Convert to 16-bit integers
        audio_data = (wave_data * 32767).astype(np.int16)
        
        # Save test file
        test_file = os.path.join(tempfile.gettempdir(), "test_tone.wav")
        with wave.open(test_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
            
        print(f"🔊 Testing audio playback...")
        success, error = player.play_audio_file(test_file)
        
        if success:
            print("✅ Audio playback OK")
        else:
            print(f"❌ Audio playback failed: {error}")
            
        # Cleanup
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        
    print("\n🎯 Audio system test completed!")
