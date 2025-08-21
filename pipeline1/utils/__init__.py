# utils/__init__.py
"""
Pipeline1 Utils Package

This package contains utility modules for the elderly care chatbot pipeline:
- STT (Speech-to-Text) using Google Cloud Speech Services
- LLM (Large Language Model) using Google Gemini
- TTS (Text-to-Speech) using Google Cloud Text-to-Speech
- Metrics for performance monitoring
"""

from .stt_service import GoogleSTTService
from .llm_service import GeminiLLMService  
from .tts_service import GoogleTTSService
from .metrics import MetricsCollector
from .audio_utils import AudioRecorder, AudioPlayer

__all__ = [
    'GoogleSTTService', 
    'GeminiLLMService', 
    'GoogleTTSService', 
    'MetricsCollector',
    'AudioRecorder',
    'AudioPlayer'
]

__version__ = '1.0.0'
__author__ = 'IEC Team - Pipeline1'
__description__ = 'Google Cloud based Voice Chatbot Pipeline for Elderly Care'
