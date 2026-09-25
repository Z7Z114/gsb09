from __future__ import annotations
import os
from typing import List, Dict, Any, Optional

try:  # 重型语音依赖可选：缺失时模块仍可导入
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False


class TranscriptionService:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self.device = "cuda" if (TORCH_AVAILABLE and torch.cuda.is_available()) else "cpu"

    def load_model(self):
        if self.model is None:
            if not WHISPER_AVAILABLE:
                raise RuntimeError(
                    "Whisper 未安装：请安装 requirements-ml.txt 后再做真实转写"
                )
            self.model = whisper.load_model(self.model_size, device=self.device)

    def transcribe_audio(self, audio_path: str, language: str = "zh") -> Dict[str, Any]:
        self.load_model()

        result = self.model.transcribe(
            audio_path,
            language=language,
            verbose=False,
            word_timestamps=True
        )

        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
                "confidence": seg.get("avg_logprob", 0)
            })

        return {
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "segments": segments,
            "duration": segments[-1]["end"] if segments else 0
        }

    def transcribe_segment(self, audio_path: str, start_time: float, end_time: float,
                          language: str = "zh") -> Dict[str, Any]:
        self.load_model()

        result = self.model.transcribe(
            audio_path,
            language=language,
            verbose=False,
            initial_prompt=f"这段录音是关于传统弓箭制作工艺的，包含胎角比例、训弓技巧等专业术语。",
            word_timestamps=True
        )

        filtered_segments = []
        for seg in result.get("segments", []):
            if seg["start"] >= start_time and seg["start"] <= end_time:
                filtered_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                })

        full_text = " ".join([s["text"] for s in filtered_segments])

        return {
            "text": full_text,
            "segments": filtered_segments,
            "language": result.get("language", language)
        }

    def extract_keywords(self, transcript_text: str) -> List[Dict[str, str]]:
        keywords = []
        craft_keywords = [
            "胎角", "角弓", "训弓", "弓胎", "弓角", "筋角",
            "木材", "纹理", "桦木", "橡木", "榆木", "桑木",
            "牛筋", "牛角", "鹿角", "鱼鳔", "胶水",
            "刨削", "打磨", "上漆", "校直", "弯曲",
            "比例", "尺寸", "重量", "拉力", "磅数",
            "流派", "手艺", "传承", "古法", "传统"
        ]

        for kw in craft_keywords:
            if kw in transcript_text:
                category = "材料" if kw in ["桦木", "橡木", "榆木", "桑木", "牛筋", "牛角", "鹿角", "鱼鳔"] else \
                          "工艺" if kw in ["刨削", "打磨", "上漆", "校直", "弯曲"] else \
                          "结构" if kw in ["胎角", "角弓", "弓胎", "弓角", "筋角"] else \
                          "技术" if kw in ["训弓", "比例", "尺寸", "重量", "拉力", "磅数"] else "其他"
                keywords.append({"keyword": kw, "category": category})

        return keywords


transcription_service = TranscriptionService()
