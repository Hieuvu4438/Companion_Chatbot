"""
Utility functions for Pipeline 3
Các hàm tiện ích cho logging, timing, file handling, etc.
"""

import os
import json
import time
import logging
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from colorama import init, Fore, Back, Style
from tabulate import tabulate

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class MetricsCollector:
    """Collect and display performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
        
    def end_timer(self, operation: str) -> float:
        """End timing and return duration"""
        if operation not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        self.metrics[operation] = duration
        del self.start_times[operation]
        return duration
        
    def add_metric(self, key: str, value: Any):
        """Add a custom metric"""
        self.metrics[key] = value
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.metrics.copy()
        
    def display_metrics(self, title: str = "Performance Metrics"):
        """Display metrics in a nice table format"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}{title}")
        print(f"{Fore.CYAN}{'='*50}")
        
        if not self.metrics:
            print(f"{Fore.YELLOW}No metrics collected")
            return
            
        # Prepare data for table
        table_data = []
        for key, value in self.metrics.items():
            if isinstance(value, float) and 'time' in key.lower():
                # Format timing metrics
                formatted_value = f"{value:.3f}s"
                color = Fore.GREEN if value < 1.0 else Fore.YELLOW if value < 5.0 else Fore.RED
            elif isinstance(value, (int, float)):
                formatted_value = f"{value}"
                color = Fore.WHITE
            else:
                formatted_value = str(value)
                color = Fore.WHITE
                
            table_data.append([key, f"{color}{formatted_value}{Style.RESET_ALL}"])
            
        print(tabulate(table_data, headers=["Metric", "Value"], tablefmt="grid"))
        print()

class Logger:
    """Enhanced logging with file rotation and colored output"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler with date
        today = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"{name}_{today}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(console_handler)
        
    def info(self, message: str):
        """Log info message with green color"""
        colored_msg = f"{Fore.GREEN}[INFO] {message}{Style.RESET_ALL}"
        print(colored_msg)
        self.logger.info(message)
        
    def warning(self, message: str):
        """Log warning message with yellow color"""
        colored_msg = f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}"
        print(colored_msg)
        self.logger.warning(message)
        
    def error(self, message: str):
        """Log error message with red color"""
        colored_msg = f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}"
        print(colored_msg)
        self.logger.error(message)
        
    def success(self, message: str):
        """Log success message with bright green color"""
        colored_msg = f"{Fore.LIGHTGREEN_EX}[SUCCESS] {message}{Style.RESET_ALL}"
        print(colored_msg)
        self.logger.info(f"SUCCESS: {message}")

class AudioUtils:
    """Utilities for audio file handling"""
    
    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, Any]:
        """Get audio file information"""
        try:
            from pydub import AudioSegment
            import librosa
            
            # Basic file info
            file_size = os.path.getsize(file_path)
            file_ext = Path(file_path).suffix.lower()
            
            # Audio properties using pydub
            audio = AudioSegment.from_file(file_path)
            duration_ms = len(audio)
            duration_sec = duration_ms / 1000.0
            sample_rate = audio.frame_rate
            channels = audio.channels
            
            # More detailed analysis with librosa
            try:
                y, sr = librosa.load(file_path, sr=None)
                rms_energy = float(librosa.feature.rms(y=y).mean())
                zero_crossing_rate = float(librosa.feature.zero_crossing_rate(y).mean())
            except:
                rms_energy = None
                zero_crossing_rate = None
            
            return {
                "file_path": file_path,
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "format": file_ext,
                "duration_seconds": duration_sec,
                "duration_minutes": duration_sec / 60.0,
                "sample_rate": sample_rate,
                "channels": channels,
                "rms_energy": rms_energy,
                "zero_crossing_rate": zero_crossing_rate
            }
            
        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e),
                "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }
    
    @staticmethod
    def validate_audio_file(file_path: str, max_size_mb: int = 25) -> tuple[bool, str]:
        """Validate audio file format and size"""
        if not os.path.exists(file_path):
            return False, "File không tồn tại"
            
        # Check file extension
        supported_formats = ['.wav', '.mp3', '.m4a', '.flac']
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in supported_formats:
            return False, f"Format không được hỗ trợ. Chỉ hỗ trợ: {', '.join(supported_formats)}"
            
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"File quá lớn ({file_size_mb:.1f}MB). Tối đa {max_size_mb}MB"
            
        return True, "OK"

class SystemMetrics:
    """Collect system performance metrics"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get current system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_used_gb": memory.used / (1024**3),
                "memory_percent": memory.percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_used_gb": disk.used / (1024**3),
                "disk_percent": (disk.used / disk.total) * 100
            }
        except:
            return {"error": "Could not collect system metrics"}

class CostCalculator:
    """Calculate estimated costs for API usage"""
    
    # Pricing information (as of 2024)
    PRICING = {
        "openai_whisper": {
            "per_minute": 0.006  # $0.006 per minute
        },
        "google_tts": {
            "per_char": 0.000016  # $16.00 per 1M characters
        }
    }
    
    @staticmethod
    def calculate_stt_cost(duration_minutes: float, service: str = "openai") -> float:
        """Calculate STT cost"""
        if service == "openai":
            return duration_minutes * CostCalculator.PRICING["openai_whisper"]["per_minute"]
        return 0.0  # FPT.AI is free up to quota
    
    @staticmethod
    def calculate_tts_cost(text_length: int, service: str = "google") -> float:
        """Calculate TTS cost"""
        if service == "google":
            return text_length * CostCalculator.PRICING["google_tts"]["per_char"]
        return 0.0  # FPT.AI is free up to quota

def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"

def format_file_size(bytes_size: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"

def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Create a simple progress bar"""
    if total == 0:
        return "█" * width
    
    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percentage = progress * 100
    return f"[{bar}] {percentage:.1f}%"

def save_metrics_to_file(metrics: Dict[str, Any], filename: str = "pipeline_metrics.json"):
    """Save metrics to JSON file with timestamp"""
    metrics_with_timestamp = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics
    }
    
    # Load existing metrics if file exists
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            if not isinstance(existing_data, list):
                existing_data = [existing_data]
        except:
            existing_data = []
    else:
        existing_data = []
    
    # Append new metrics
    existing_data.append(metrics_with_timestamp)
    
    # Keep only last 100 entries
    if len(existing_data) > 100:
        existing_data = existing_data[-100:]
    
    # Save back to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

def print_header(title: str, width: int = 60):
    """Print a nice header"""
    print(f"\n{Fore.CYAN}{'='*width}")
    print(f"{Fore.CYAN}{title.center(width)}")
    print(f"{Fore.CYAN}{'='*width}")

def print_step(step_number: int, description: str, status: str = ""):
    """Print a pipeline step"""
    if status:
        print(f"{Fore.BLUE}Step {step_number}: {description} {status}")
    else:
        print(f"{Fore.BLUE}Step {step_number}: {description}")

if __name__ == "__main__":
    # Test utilities
    print_header("Testing Pipeline 3 Utilities")
    
    # Test metrics collector
    metrics = MetricsCollector()
    metrics.start_timer("test_operation")
    time.sleep(0.1)  # Simulate work
    metrics.end_timer("test_operation")
    metrics.add_metric("test_value", 42)
    metrics.display_metrics("Test Metrics")
    
    # Test logger
    logger = Logger("test")
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.success("This is a success message")
    
    # Test system metrics
    sys_metrics = SystemMetrics.get_system_info()
    print(f"\n{Fore.GREEN}System Info:")
    for key, value in sys_metrics.items():
        print(f"  {key}: {value}")
    
    print(f"\n{Fore.GREEN}Utilities test completed!")
