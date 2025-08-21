import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class MetricsCollector:
    """
    Lớp thu thập và quản lý metrics cho pipeline
    """
    
    def __init__(self, save_to_file: bool = True, metrics_file: str = None):
        self.save_to_file = save_to_file
        self.metrics_file = metrics_file or "pipeline_metrics.json"
        self.reset_metrics()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def reset_metrics(self):
        """Reset tất cả metrics về trạng thái ban đầu"""
        self.metrics = {
            "session_info": {
                "start_time": datetime.now().isoformat(),
                "total_conversations": 0,
                "session_duration": 0
            },
            "stt_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0.0,
                "average_latency": 0.0,
                "min_latency": float('inf'),
                "max_latency": 0.0,
                "confidence_scores": [],
                "average_confidence": 0.0,
                "transcription_accuracy": [],
                "errors": []
            },
            "llm_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0.0,
                "average_latency": 0.0,
                "min_latency": float('inf'),
                "max_latency": 0.0,
                "total_tokens": 0,
                "average_tokens_per_request": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "errors": []
            },
            "tts_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency": 0.0,
                "average_latency": 0.0,
                "min_latency": float('inf'),
                "max_latency": 0.0,
                "total_characters": 0,
                "average_characters_per_request": 0.0,
                "audio_generation_speed": [],  # chars per second
                "errors": []
            },
            "pipeline_metrics": {
                "total_pipeline_runs": 0,
                "successful_pipeline_runs": 0,
                "failed_pipeline_runs": 0,
                "total_end_to_end_latency": 0.0,
                "average_end_to_end_latency": 0.0,
                "min_end_to_end_latency": float('inf'),
                "max_end_to_end_latency": 0.0,
                "pipeline_errors": []
            },
            "audio_metrics": {
                "total_recordings": 0,
                "successful_recordings": 0,
                "failed_recordings": 0,
                "total_playbacks": 0,
                "successful_playbacks": 0,
                "failed_playbacks": 0,
                "average_audio_duration": 0.0,
                "audio_quality_scores": []
            }
        }
        
    def update_stt_metrics(self, latency: float, confidence: float, 
                          success: bool, error: str = None, 
                          transcription_length: int = 0):
        """Cập nhật STT metrics"""
        stt = self.metrics["stt_metrics"]
        stt["total_requests"] += 1
        
        if success:
            stt["successful_requests"] += 1
            stt["total_latency"] += latency
            stt["confidence_scores"].append(confidence)
            
            # Update latency stats
            stt["min_latency"] = min(stt["min_latency"], latency)
            stt["max_latency"] = max(stt["max_latency"], latency)
            stt["average_latency"] = stt["total_latency"] / stt["successful_requests"]
            stt["average_confidence"] = sum(stt["confidence_scores"]) / len(stt["confidence_scores"])
            
        else:
            stt["failed_requests"] += 1
            if error:
                stt["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error,
                    "latency": latency
                })
                
        self._auto_save()
        
    def update_llm_metrics(self, latency: float, tokens: int, 
                          success: bool, error: str = None,
                          prompt_tokens: int = 0, completion_tokens: int = 0):
        """Cập nhật LLM metrics"""
        llm = self.metrics["llm_metrics"]
        llm["total_requests"] += 1
        
        if success:
            llm["successful_requests"] += 1
            llm["total_latency"] += latency
            llm["total_tokens"] += tokens
            llm["prompt_tokens"] += prompt_tokens
            llm["completion_tokens"] += completion_tokens
            
            # Update stats
            llm["min_latency"] = min(llm["min_latency"], latency)
            llm["max_latency"] = max(llm["max_latency"], latency)
            llm["average_latency"] = llm["total_latency"] / llm["successful_requests"]
            llm["average_tokens_per_request"] = llm["total_tokens"] / llm["successful_requests"]
            
        else:
            llm["failed_requests"] += 1
            if error:
                llm["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error,
                    "latency": latency
                })
                
        self._auto_save()
        
    def update_tts_metrics(self, latency: float, char_count: int, 
                          success: bool, error: str = None,
                          audio_duration: float = 0):
        """Cập nhật TTS metrics"""
        tts = self.metrics["tts_metrics"]
        tts["total_requests"] += 1
        
        if success:
            tts["successful_requests"] += 1
            tts["total_latency"] += latency
            tts["total_characters"] += char_count
            
            # Calculate generation speed (chars per second)
            if latency > 0:
                gen_speed = char_count / latency
                tts["audio_generation_speed"].append(gen_speed)
            
            # Update stats
            tts["min_latency"] = min(tts["min_latency"], latency)
            tts["max_latency"] = max(tts["max_latency"], latency)
            tts["average_latency"] = tts["total_latency"] / tts["successful_requests"]
            tts["average_characters_per_request"] = tts["total_characters"] / tts["successful_requests"]
            
        else:
            tts["failed_requests"] += 1
            if error:
                tts["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error,
                    "latency": latency
                })
                
        self._auto_save()
        
    def update_pipeline_metrics(self, end_to_end_latency: float, 
                               success: bool, error: str = None):
        """Cập nhật pipeline metrics tổng thể"""
        pipeline = self.metrics["pipeline_metrics"]
        pipeline["total_pipeline_runs"] += 1
        
        if success:
            pipeline["successful_pipeline_runs"] += 1
            pipeline["total_end_to_end_latency"] += end_to_end_latency
            
            # Update stats
            pipeline["min_end_to_end_latency"] = min(
                pipeline["min_end_to_end_latency"], end_to_end_latency
            )
            pipeline["max_end_to_end_latency"] = max(
                pipeline["max_end_to_end_latency"], end_to_end_latency
            )
            pipeline["average_end_to_end_latency"] = (
                pipeline["total_end_to_end_latency"] / pipeline["successful_pipeline_runs"]
            )
            
            # Update conversation count
            self.metrics["session_info"]["total_conversations"] += 1
            
        else:
            pipeline["failed_pipeline_runs"] += 1
            if error:
                pipeline["pipeline_errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error,
                    "latency": end_to_end_latency
                })
                
        self._auto_save()
        
    def update_audio_metrics(self, recording_success: bool = None, 
                           playback_success: bool = None,
                           audio_duration: float = None,
                           quality_score: float = None):
        """Cập nhật audio metrics"""
        audio = self.metrics["audio_metrics"]
        
        if recording_success is not None:
            audio["total_recordings"] += 1
            if recording_success:
                audio["successful_recordings"] += 1
            else:
                audio["failed_recordings"] += 1
                
        if playback_success is not None:
            audio["total_playbacks"] += 1
            if playback_success:
                audio["successful_playbacks"] += 1
            else:
                audio["failed_playbacks"] += 1
                
        if audio_duration is not None:
            # Calculate average audio duration
            total_duration = (audio["average_audio_duration"] * 
                            (audio["successful_recordings"] - 1) + audio_duration)
            audio["average_audio_duration"] = total_duration / audio["successful_recordings"]
            
        if quality_score is not None:
            audio["audio_quality_scores"].append(quality_score)
            
        self._auto_save()
        
    def get_summary_report(self) -> Dict[str, Any]:
        """Tạo báo cáo tóm tắt metrics"""
        def safe_divide(a, b):
            return a / b if b > 0 else 0
            
        stt = self.metrics["stt_metrics"]
        llm = self.metrics["llm_metrics"]
        tts = self.metrics["tts_metrics"]
        pipeline = self.metrics["pipeline_metrics"]
        session = self.metrics["session_info"]
        
        report = {
            "📊 TỔNG QUAN SESSION": {
                "Thời gian bắt đầu": session["start_time"],
                "Tổng cuộc hội thoại": session["total_conversations"],
                "Thời gian session": f"{time.time() - time.mktime(datetime.fromisoformat(session['start_time']).timetuple()):.1f}s"
            },
            "🎤 STT PERFORMANCE": {
                "Tổng requests": stt["total_requests"],
                "Thành công": stt["successful_requests"],
                "Thất bại": stt["failed_requests"],
                "Tỷ lệ thành công": f"{safe_divide(stt['successful_requests'], stt['total_requests']) * 100:.1f}%",
                "Latency trung bình": f"{stt['average_latency'] * 1000:.1f}ms",
                "Confidence trung bình": f"{stt['average_confidence']:.2f}",
                "Latency min/max": f"{stt['min_latency'] * 1000:.1f}/{stt['max_latency'] * 1000:.1f}ms"
            },
            "🤖 LLM PERFORMANCE": {
                "Tổng requests": llm["total_requests"],
                "Thành công": llm["successful_requests"],
                "Thất bại": llm["failed_requests"],
                "Tỷ lệ thành công": f"{safe_divide(llm['successful_requests'], llm['total_requests']) * 100:.1f}%",
                "Latency trung bình": f"{llm['average_latency'] * 1000:.1f}ms",
                "Tokens trung bình": f"{llm['average_tokens_per_request']:.1f}",
                "Tổng tokens": llm["total_tokens"]
            },
            "🔊 TTS PERFORMANCE": {
                "Tổng requests": tts["total_requests"],
                "Thành công": tts["successful_requests"],
                "Thất bại": tts["failed_requests"],
                "Tỷ lệ thành công": f"{safe_divide(tts['successful_requests'], tts['total_requests']) * 100:.1f}%",
                "Latency trung bình": f"{tts['average_latency'] * 1000:.1f}ms",
                "Ký tự trung bình": f"{tts['average_characters_per_request']:.1f}",
                "Tốc độ gen âm thanh": f"{safe_divide(sum(tts['audio_generation_speed']), len(tts['audio_generation_speed'])):.1f} chars/s" if tts['audio_generation_speed'] else "N/A"
            },
            "⚡ PIPELINE OVERALL": {
                "Tổng pipeline runs": pipeline["total_pipeline_runs"],
                "Thành công": pipeline["successful_pipeline_runs"],
                "Thất bại": pipeline["failed_pipeline_runs"],
                "Tỷ lệ thành công": f"{safe_divide(pipeline['successful_pipeline_runs'], pipeline['total_pipeline_runs']) * 100:.1f}%",
                "End-to-end latency": f"{pipeline['average_end_to_end_latency'] * 1000:.1f}ms",
                "Latency min/max": f"{pipeline['min_end_to_end_latency'] * 1000:.1f}/{pipeline['max_end_to_end_latency'] * 1000:.1f}ms"
            }
        }
        
        return report
        
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Lấy toàn bộ metrics chi tiết"""
        return self.metrics.copy()
        
    def save_metrics(self, filename: str = None):
        """Lưu metrics vào file"""
        if not self.save_to_file:
            return
            
        filename = filename or self.metrics_file
        
        try:
            # Update session duration
            start_time = datetime.fromisoformat(self.metrics["session_info"]["start_time"])
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics["session_info"]["session_duration"] = duration
            
            save_data = {
                "metadata": {
                    "export_time": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "pipeline": "Pipeline1 - Google Cloud"
                },
                "summary_report": self.get_summary_report(),
                "detailed_metrics": self.metrics
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"📁 Đã lưu metrics vào {filename}")
            print(f"📁 Đã lưu metrics vào {filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi lưu metrics: {e}")
            print(f"❌ Lỗi khi lưu metrics: {e}")
            
    def _auto_save(self):
        """Tự động lưu metrics sau mỗi update (nếu được bật)"""
        if self.save_to_file and hasattr(self, '_last_save_time'):
            # Auto save every 30 seconds
            if time.time() - self._last_save_time > 30:
                self.save_metrics()
                self._last_save_time = time.time()
        elif self.save_to_file:
            self._last_save_time = time.time()
            
    def export_csv_report(self, filename: str = "metrics_report.csv"):
        """Xuất báo cáo metrics dạng CSV"""
        try:
            import csv
            
            report = self.get_summary_report()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Category', 'Metric', 'Value'])
                
                for category, metrics in report.items():
                    for metric, value in metrics.items():
                        writer.writerow([category, metric, value])
                        
            print(f"📊 Đã xuất CSV report: {filename}")
            
        except Exception as e:
            print(f"❌ Lỗi khi xuất CSV: {e}")
            
    def clear_error_logs(self):
        """Xóa tất cả error logs"""
        self.metrics["stt_metrics"]["errors"] = []
        self.metrics["llm_metrics"]["errors"] = []
        self.metrics["tts_metrics"]["errors"] = []
        self.metrics["pipeline_metrics"]["pipeline_errors"] = []
        print("🧹 Đã xóa tất cả error logs")
