"""
Utility functions for Pipeline 4
Các hàm tiện ích cho metrics, logging, audio processing
"""

import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import wave
import threading

class MetricsCollector:
    """Collector for performance metrics and statistics"""
    
    def __init__(self):
        self.metrics = {}
        self.timers = {}
        self.start_times = {}
        self.lock = threading.Lock()
    
    def start_timer(self, name: str):
        """Start a timer with given name"""
        with self.lock:
            self.start_times[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """End timer and return elapsed time"""
        with self.lock:
            if name in self.start_times:
                elapsed = time.time() - self.start_times[name]
                self.timers[name] = elapsed
                del self.start_times[name]
                return elapsed
            return 0.0
    
    def add_metric(self, name: str, value: Any):
        """Add a metric"""
        with self.lock:
            self.metrics[name] = value
    
    def get_metric(self, name: str, default=None):
        """Get a metric value"""
        return self.metrics.get(name, default)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self.lock:
            return {
                "metrics": self.metrics.copy(),
                "timers": self.timers.copy(),
                "collected_at": datetime.now().isoformat()
            }
    
    def display_metrics(self, title: str = "Performance Metrics"):
        """Display formatted metrics"""
        print(f"\n{'='*60}")
        print(f"📊 {title}")
        print(f"{'='*60}")
        
        if self.timers:
            print("⏱️  Timing Metrics:")
            for name, value in self.timers.items():
                print(f"  {name}: {value:.3f}s")
        
        if self.metrics:
            print("\n📈 General Metrics:")
            for name, value in self.metrics.items():
                if isinstance(value, float):
                    print(f"  {name}: {value:.3f}")
                elif isinstance(value, bool):
                    print(f"  {name}: {'✅' if value else '❌'}")
                else:
                    print(f"  {name}: {value}")
        
        print(f"{'='*60}")
    
    def save_to_file(self, filepath: str):
        """Save metrics to JSON file"""
        try:
            data = self.get_all_metrics()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving metrics to file: {e}")
    
    def reset(self):
        """Reset all metrics"""
        with self.lock:
            self.metrics.clear()
            self.timers.clear()
            self.start_times.clear()

class Logger:
    """Enhanced logger for pipeline components"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            # File handler
            log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def success(self, message: str):
        """Log success message (as info with special marker)"""
        self.logger.info(f"✅ {message}")

class AudioUtils:
    """Utility functions for audio processing"""
    
    @staticmethod
    def validate_audio_file(filepath: str) -> tuple[bool, str]:
        """Validate audio file"""
        if not os.path.exists(filepath):
            return False, "File không tồn tại"
        
        # Check file extension
        supported_formats = ['.wav', '.mp3', '.m4a', '.flac']
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext not in supported_formats:
            return False, f"Format không hỗ trợ. Chỉ hỗ trợ: {', '.join(supported_formats)}"
        
        # Check file size (max 25MB)
        file_size = os.path.getsize(filepath)
        max_size = 25 * 1024 * 1024  # 25MB
        
        if file_size > max_size:
            return False, f"File quá lớn ({format_file_size(file_size)}). Tối đa {format_file_size(max_size)}"
        
        if file_size < 1024:  # Less than 1KB
            return False, "File quá nhỏ, có thể bị lỗi"
        
        return True, "File hợp lệ"
    
    @staticmethod
    def get_audio_info(filepath: str) -> Dict[str, Any]:
        """Get audio file information"""
        try:
            if not os.path.exists(filepath):
                return {"error": "File không tồn tại"}
            
            file_size = os.path.getsize(filepath)
            file_ext = os.path.splitext(filepath)[1].lower()
            
            info = {
                "file_path": filepath,
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "file_extension": file_ext
            }
            
            # For WAV files, get detailed info
            if file_ext == '.wav':
                try:
                    with wave.open(filepath, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        duration = frames / sample_rate
                        
                        info.update({
                            "duration_seconds": duration,
                            "duration_minutes": duration / 60,
                            "sample_rate": sample_rate,
                            "channels": channels,
                            "frames": frames
                        })
                except Exception as e:
                    info["wav_info_error"] = str(e)
            else:
                # For other formats, estimate duration based on file size
                # This is a rough estimate
                estimated_duration = file_size / (32 * 1024)  # Rough estimate for compressed audio
                info.update({
                    "duration_seconds": estimated_duration,
                    "duration_minutes": estimated_duration / 60,
                    "estimated": True
                })
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def create_silence_audio(filepath: str, duration: float = 1.0, sample_rate: int = 16000):
        """Create a silent audio file for testing"""
        try:
            import numpy as np
            
            # Generate silence
            samples = int(duration * sample_rate)
            silence = np.zeros(samples, dtype=np.int16)
            
            # Save as WAV
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silence.tobytes())
            
            return True, f"Created silence audio: {duration}s"
        except Exception as e:
            return False, f"Error creating silence audio: {e}"

class ResponseTimeTracker:
    """Track response times for different components"""
    
    def __init__(self):
        self.times = {
            "stt_times": [],
            "llm_times": [],
            "tts_times": [],
            "total_times": []
        }
    
    def add_time(self, component: str, time_value: float):
        """Add a response time"""
        key = f"{component}_times"
        if key in self.times:
            self.times[key].append(time_value)
    
    def get_stats(self, component: str) -> Dict[str, float]:
        """Get statistics for a component"""
        key = f"{component}_times"
        times = self.times.get(key, [])
        
        if not times:
            return {"count": 0}
        
        return {
            "count": len(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "total": sum(times)
        }
    
    def display_all_stats(self):
        """Display statistics for all components"""
        print("\n📊 Response Time Statistics:")
        print("=" * 50)
        
        for component in ["stt", "llm", "tts", "total"]:
            stats = self.get_stats(component)
            if stats["count"] > 0:
                print(f"\n{component.upper()}:")
                print(f"  Count: {stats['count']}")
                print(f"  Average: {stats['avg']:.3f}s")
                print(f"  Min: {stats['min']:.3f}s")
                print(f"  Max: {stats['max']:.3f}s")
                print(f"  Total: {stats['total']:.3f}s")

# Utility functions

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def print_header(title: str, width: int = 60):
    """Print a formatted header"""
    print(f"\n{'='*width}")
    print(f"{title:^{width}}")
    print(f"{'='*width}")

def print_step(step_num: int, description: str):
    """Print a formatted step"""
    print(f"\n🔸 Step {step_num}: {description}")
    print("-" * 40)

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")

def save_json(data: Dict[str, Any], filepath: str) -> bool:
    """Save data to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print_error(f"Error saving JSON to {filepath}: {e}")
        return False

def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """Load data from JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print_error(f"Error loading JSON from {filepath}: {e}")
        return None

def get_timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_output_filename(prefix: str, extension: str = ".wav") -> str:
    """Create output filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}{extension}"

class PerformanceMonitor:
    """Monitor performance and alert on issues"""
    
    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds
        self.alerts = []
    
    def check_performance(self, component: str, response_time: float):
        """Check if performance is within acceptable limits"""
        threshold_key = f"{component}_max_time"
        if threshold_key in self.thresholds:
            max_time = self.thresholds[threshold_key]
            if response_time > max_time:
                alert = {
                    "component": component,
                    "response_time": response_time,
                    "threshold": max_time,
                    "timestamp": get_timestamp()
                }
                self.alerts.append(alert)
                print_warning(f"{component.upper()} slow response: {response_time:.3f}s (threshold: {max_time}s)")
                return False
        return True
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all performance alerts"""
        return self.alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()

if __name__ == "__main__":
    # Test utility functions
    print_header("TESTING UTILITY FUNCTIONS")
    
    # Test metrics collector
    metrics = MetricsCollector()
    metrics.start_timer("test_timer")
    time.sleep(0.1)
    elapsed = metrics.end_timer("test_timer")
    metrics.add_metric("test_metric", 123.45)
    metrics.add_metric("test_bool", True)
    
    metrics.display_metrics("Test Metrics")
    
    # Test logger
    logger = Logger("test_utils")
    logger.info("Testing logger functionality")
    logger.success("Logger test completed")
    
    # Test audio utils
    print_header("TESTING AUDIO UTILS")
    
    # Test validation with non-existent file
    valid, msg = AudioUtils.validate_audio_file("nonexistent.wav")
    print(f"Validation test: {valid} - {msg}")
    
    print_header("UTILITY TESTS COMPLETED")
