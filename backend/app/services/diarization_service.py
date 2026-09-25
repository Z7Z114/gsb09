from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class DiarizationService:
    def __init__(self):
        self.auth_token = os.getenv("PYANNOTE_AUTH_TOKEN")
        self.pipeline = None
        self.speaker_profiles = {}

    def load_pipeline(self):
        if self.pipeline is None and self.auth_token:
            try:
                from pyannote.audio import Pipeline
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.auth_token
                )
            except Exception as e:
                print(f"Failed to load pyannote pipeline: {e}")
                self.pipeline = None

    def diarize_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        self.load_pipeline()

        if self.pipeline is not None:
            return self._diarize_with_pyannote(audio_path)
        else:
            return self._diarize_simple(audio_path)

    def _diarize_with_pyannote(self, audio_path: str) -> List[Dict[str, Any]]:
        try:
            diarization = self.pipeline(audio_path)

            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "speaker_label": speaker,
                    "start_time": turn.start,
                    "end_time": turn.end,
                    "duration": turn.end - turn.start
                })

            return segments
        except Exception as e:
            print(f"Pyannote diarization failed: {e}")
            return self._diarize_simple(audio_path)

    def _diarize_simple(self, audio_path: str) -> List[Dict[str, Any]]:
        import librosa
        import numpy as np

        y, sr = librosa.load(audio_path, sr=16000)
        duration = len(y) / sr

        segments = []
        segment_duration = 30.0
        current_time = 0.0
        speaker_index = 0

        while current_time < duration:
            end_time = min(current_time + segment_duration, duration)
            segment_y = y[int(current_time * sr):int(end_time * sr)]

            if len(segment_y) > 0:
                rms = np.sqrt(np.mean(segment_y ** 2))
                if rms > 0.01:
                    segments.append({
                        "speaker_label": f"SPEAKER_{speaker_index % 3}",
                        "start_time": current_time,
                        "end_time": end_time,
                        "duration": end_time - current_time
                    })
                    speaker_index += 1

            current_time = end_time

        return segments

    def predict_school(self, transcript_text: str, speaker_label: str) -> Dict[str, Any]:
        schools = {
            "汉族传统弓": ["角弓", "筋角弓", "复合弓", "传统", "古法", "老样子"],
            "蒙古族角弓": ["蒙古", "游牧", "骑射", "短弓", "硬弓"],
            "满族清弓": ["清弓", "满族", "长梢", "重弓", "大拉距"],
            "藏族牛角弓": ["藏弓", "藏族", "高原", "牦牛", "牛角"],
            "彝族竹弓": ["彝弓", "彝族", "竹弓", "竹木", "云南"]
        }

        scores = {}
        for school, keywords in schools.items():
            score = sum(1 for kw in keywords if kw in transcript_text)
            scores[school] = score

        total = sum(scores.values())
        if total > 0:
            predicted_school = max(scores, key=scores.get)
            confidence = scores[predicted_school] / total
        else:
            predicted_school = "未知流派"
            confidence = 0.0

        return {
            "speaker_label": speaker_label,
            "predicted_school": predicted_school,
            "confidence": confidence,
            "scores": scores
        }

    def merge_diarization_and_transcript(self, diarization_segments: List[Dict[str, Any]],
                                         transcript_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged = []

        for t_seg in transcript_segments:
            t_start = t_seg["start"]
            t_end = t_seg["end"]

            best_speaker = None
            best_overlap = 0

            for d_seg in diarization_segments:
                d_start = d_seg["start_time"]
                d_end = d_seg["end_time"]

                overlap_start = max(t_start, d_start)
                overlap_end = min(t_end, d_end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = d_seg["speaker_label"]

            merged.append({
                "start_time": t_start,
                "end_time": t_end,
                "text": t_seg["text"],
                "speaker_label": best_speaker or "UNKNOWN"
            })

        return merged


diarization_service = DiarizationService()
