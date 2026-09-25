from __future__ import annotations
import os
from typing import Tuple, Dict, Any
import tempfile

try:  # 重型音频依赖可选：缺失时模块仍可导入，只是无法做真实降噪/提取
    import librosa
    import soundfile as sf
    import numpy as np
    AUDIO_DEPS_AVAILABLE = True
except ImportError:
    librosa = None
    sf = None
    np = None
    AUDIO_DEPS_AVAILABLE = False


def _require_audio_deps():
    if not AUDIO_DEPS_AVAILABLE:
        raise RuntimeError(
            "音频依赖未安装（librosa/soundfile/numpy）：请安装 requirements-ml.txt"
        )


class AudioProcessor:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.noise_reduction_strength = 0.3

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        _require_audio_deps()
        y, sr = librosa.load(file_path, sr=self.sample_rate)
        return y, sr

    def save_audio(self, y: np.ndarray, output_path: str, sr: int = None):
        _require_audio_deps()
        if sr is None:
            sr = self.sample_rate
        sf.write(output_path, y, sr)

    def preserve_workshop_ambience(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        env_feature = librosa.feature.spectral_centroid(y=y, sr=sr)
        env_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        env_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)
        zcr = librosa.feature.zero_crossing_rate(y)

        ambience_profile = {
            "avg_spectral_centroid": float(np.mean(env_feature)),
            "avg_spectral_bandwidth": float(np.mean(env_bandwidth)),
            "spectral_contrast": np.mean(env_contrast, axis=1).tolist(),
            "avg_rms": float(np.mean(rms)),
            "avg_zcr": float(np.mean(zcr)),
            "duration": float(len(y) / sr)
        }

        return ambience_profile

    def reduce_noise_simple(self, y: np.ndarray, sr: int) -> np.ndarray:
        noise_sample = y[:int(sr * 0.5)]
        noise_fft = np.fft.rfft(noise_sample)
        noise_mag = np.abs(noise_fft)
        noise_threshold = np.percentile(noise_mag, 75) * self.noise_reduction_strength

        y_fft = np.fft.rfft(y)
        y_mag = np.abs(y_fft)
        y_phase = np.angle(y_fft)

        mask = y_mag > noise_threshold
        y_mag_filtered = y_mag * mask
        y_fft_filtered = y_mag_filtered * np.exp(1j * y_phase)
        y_filtered = np.fft.irfft(y_fft_filtered)

        return y_filtered

    def process_audio_for_transcription(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        y, sr = self.load_audio(input_path)

        ambience_profile = self.preserve_workshop_ambience(y, sr)

        y_enhanced = self.reduce_noise_simple(y, sr)

        filename = os.path.basename(input_path)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}_enhanced.wav")

        self.save_audio(y_enhanced, output_path, sr)

        return {
            "original_path": input_path,
            "processed_path": output_path,
            "duration": float(len(y) / sr),
            "ambience_profile": ambience_profile,
            "sample_rate": sr
        }

    def extract_segments(self, audio_path: str, start_time: float, end_time: float) -> np.ndarray:
        y, sr = self.load_audio(audio_path)
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        return y[start_sample:end_sample]


audio_processor = AudioProcessor()
