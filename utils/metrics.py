import time
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

@dataclass
class STTMetrics:
    """Metrics for Speech-to-Text operation"""
    start_time: float
    end_time: float
    response_time: float
    confidence_score: float
    word_count: int
    audio_duration: float
    recognized_text: str
    language: str
    success: bool
    error_message: Optional[str] = None

@dataclass 
class LLMMetrics:
    """Metrics for Large Language Model operation"""
    start_time: float
    end_time: float
    response_time: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_length: int
    model_name: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class TTSMetrics:
    """Metrics for Text-to-Speech operation"""
    start_time: float
    end_time: float
    response_time: float
    audio_duration: float
    character_count: int
    voice_model: str
    audio_format: str
    file_size: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class PipelineMetrics:
    """Overall pipeline metrics"""
    session_id: str
    start_time: float
    end_time: float
    total_time: float
    stt_metrics: Optional[STTMetrics]
    llm_metrics: Optional[LLMMetrics] 
    tts_metrics: Optional[TTSMetrics]
    success: bool
    error_stage: Optional[str] = None
    error_message: Optional[str] = None

class MetricsCollector:
    """Collects and manages performance metrics for the pipeline"""
    
    def __init__(self, save_to_file: bool = True, log_metrics: bool = True):
        self.save_to_file = save_to_file
        self.log_metrics = log_metrics
        self.logger = logging.getLogger(__name__)
        self.metrics_history = []
        
    def create_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def start_timer(self) -> float:
        """Start timing operation"""
        return time.time()
    
    def end_timer(self, start_time: float) -> tuple:
        """End timing operation and return end_time, response_time"""
        end_time = time.time()
        response_time = end_time - start_time
        return end_time, response_time
    
    def create_stt_metrics(self, start_time: float, end_time: float, 
                          response_time: float, confidence_score: float,
                          word_count: int, audio_duration: float,
                          recognized_text: str, language: str,
                          success: bool, error_message: str = None) -> STTMetrics:
        """Create STT metrics object"""
        return STTMetrics(
            start_time=start_time,
            end_time=end_time,
            response_time=response_time,
            confidence_score=confidence_score,
            word_count=word_count,
            audio_duration=audio_duration,
            recognized_text=recognized_text,
            language=language,
            success=success,
            error_message=error_message
        )
    
    def create_llm_metrics(self, start_time: float, end_time: float,
                          response_time: float, input_tokens: int,
                          output_tokens: int, total_tokens: int,
                          response_length: int, model_name: str,
                          success: bool, error_message: str = None) -> LLMMetrics:
        """Create LLM metrics object"""
        return LLMMetrics(
            start_time=start_time,
            end_time=end_time,
            response_time=response_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            response_length=response_length,
            model_name=model_name,
            success=success,
            error_message=error_message
        )
    
    def create_tts_metrics(self, start_time: float, end_time: float,
                          response_time: float, audio_duration: float,
                          character_count: int, voice_model: str,
                          audio_format: str, file_size: int,
                          success: bool, error_message: str = None) -> TTSMetrics:
        """Create TTS metrics object"""
        return TTSMetrics(
            start_time=start_time,
            end_time=end_time,
            response_time=response_time,
            audio_duration=audio_duration,
            character_count=character_count,
            voice_model=voice_model,
            audio_format=audio_format,
            file_size=file_size,
            success=success,
            error_message=error_message
        )
    
    def create_pipeline_metrics(self, session_id: str, start_time: float,
                               end_time: float, total_time: float,
                               stt_metrics: STTMetrics = None,
                               llm_metrics: LLMMetrics = None,
                               tts_metrics: TTSMetrics = None,
                               success: bool = True,
                               error_stage: str = None,
                               error_message: str = None) -> PipelineMetrics:
        """Create complete pipeline metrics"""
        return PipelineMetrics(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            total_time=total_time,
            stt_metrics=stt_metrics,
            llm_metrics=llm_metrics,
            tts_metrics=tts_metrics,
            success=success,
            error_stage=error_stage,
            error_message=error_message
        )
    
    def display_metrics(self, metrics: Any, title: str = "Metrics"):
        """Display metrics in a formatted way"""
        print(f"\n{'='*50}")
        print(f"📊 {title}")
        print(f"{'='*50}")
        
        if isinstance(metrics, STTMetrics):
            self._display_stt_metrics(metrics)
        elif isinstance(metrics, LLMMetrics):
            self._display_llm_metrics(metrics)
        elif isinstance(metrics, TTSMetrics):
            self._display_tts_metrics(metrics)
        elif isinstance(metrics, PipelineMetrics):
            self._display_pipeline_metrics(metrics)
        
        print(f"{'='*50}\n")
    
    def _display_stt_metrics(self, metrics: STTMetrics):
        """Display STT metrics"""
        status = "✅ SUCCESS" if metrics.success else "❌ FAILED"
        print(f"🎤 STT METRICS {status}")
        print(f"⏱️  Response Time: {metrics.response_time:.3f}s")
        print(f"🎯 Confidence: {metrics.confidence_score:.2%}")
        print(f"📝 Words Recognized: {metrics.word_count}")
        print(f"🎵 Audio Duration: {metrics.audio_duration:.2f}s")
        print(f"🌍 Language: {metrics.language}")
        print(f"💬 Text: '{metrics.recognized_text[:100]}{'...' if len(metrics.recognized_text) > 100 else ''}'")
        if not metrics.success and metrics.error_message:
            print(f"❌ Error: {metrics.error_message}")
    
    def _display_llm_metrics(self, metrics: LLMMetrics):
        """Display LLM metrics"""
        status = "✅ SUCCESS" if metrics.success else "❌ FAILED"
        print(f"🧠 LLM METRICS {status}")
        print(f"⏱️  Response Time: {metrics.response_time:.3f}s")
        print(f"🔤 Input Tokens: {metrics.input_tokens:,}")
        print(f"🔤 Output Tokens: {metrics.output_tokens:,}")
        print(f"🔤 Total Tokens: {metrics.total_tokens:,}")
        print(f"📏 Response Length: {metrics.response_length} chars")
        print(f"🤖 Model: {metrics.model_name}")
        if not metrics.success and metrics.error_message:
            print(f"❌ Error: {metrics.error_message}")
    
    def _display_tts_metrics(self, metrics: TTSMetrics):
        """Display TTS metrics"""
        status = "✅ SUCCESS" if metrics.success else "❌ FAILED"
        print(f"🔊 TTS METRICS {status}")
        print(f"⏱️  Response Time: {metrics.response_time:.3f}s")
        print(f"🎵 Audio Duration: {metrics.audio_duration:.2f}s")
        print(f"📝 Characters: {metrics.character_count:,}")
        print(f"🎙️  Voice: {metrics.voice_model}")
        print(f"🎵 Format: {metrics.audio_format}")
        print(f"💾 File Size: {metrics.file_size:,} bytes")
        if not metrics.success and metrics.error_message:
            print(f"❌ Error: {metrics.error_message}")
    
    def _display_pipeline_metrics(self, metrics: PipelineMetrics):
        """Display complete pipeline metrics"""
        status = "✅ SUCCESS" if metrics.success else "❌ FAILED"
        print(f"🔄 PIPELINE METRICS {status}")
        print(f"🆔 Session: {metrics.session_id}")
        print(f"⏱️  Total Time: {metrics.total_time:.3f}s")
        
        if metrics.stt_metrics:
            print(f"🎤 STT Time: {metrics.stt_metrics.response_time:.3f}s")
        if metrics.llm_metrics:
            print(f"🧠 LLM Time: {metrics.llm_metrics.response_time:.3f}s")
        if metrics.tts_metrics:
            print(f"🔊 TTS Time: {metrics.tts_metrics.response_time:.3f}s")
            
        if not metrics.success:
            print(f"❌ Failed at: {metrics.error_stage}")
            print(f"❌ Error: {metrics.error_message}")
    
    def save_metrics(self, metrics: Any, filename: str = None):
        """Save metrics to JSON file"""
        if not self.save_to_file:
            return
            
        try:
            from config import METRICS_FILE, LOGS_DIR
            
            if filename is None:
                filename = METRICS_FILE
            
            # Convert metrics to dict
            metrics_dict = asdict(metrics)
            metrics_dict['timestamp'] = datetime.now().isoformat()
            
            # Load existing metrics
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    all_metrics = json.load(f)
            else:
                all_metrics = []
            
            # Add new metrics
            all_metrics.append(metrics_dict)
            
            # Save back to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_metrics, f, indent=2, ensure_ascii=False)
                
            if self.log_metrics:
                self.logger.info(f"Metrics saved to {filename}")
                
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
    
    def get_average_metrics(self, metric_type: str = "pipeline") -> Dict[str, float]:
        """Get average metrics from history"""
        if not self.metrics_history:
            return {}
        
        # Implementation for calculating averages
        # This would aggregate metrics from self.metrics_history
        # Return average response times, success rates, etc.
        pass
    
    def export_metrics_csv(self, filename: str):
        """Export metrics to CSV format"""
        # Implementation for CSV export
        pass
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        summary = {
            "total_sessions": len(self.metrics_history),
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "fastest_session": 0.0,
            "slowest_session": 0.0
        }
        
        if self.metrics_history:
            successful = [m for m in self.metrics_history if m.get('success', False)]
            summary["success_rate"] = len(successful) / len(self.metrics_history) * 100
            
            if successful:
                times = [m.get('total_time', 0) for m in successful]
                summary["average_response_time"] = sum(times) / len(times)
                summary["fastest_session"] = min(times)
                summary["slowest_session"] = max(times)
        
        return summary
