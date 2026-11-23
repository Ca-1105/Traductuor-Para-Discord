from __future__ import annotations

import re
from collections import Counter

import numpy as np
import argostranslate.package as argos_package
import argostranslate.settings as argos_settings
import argostranslate.translate as argos_translate
from faster_whisper import WhisperModel

import config

argos_settings.compute_type = "float32"

PAIRS = (("es", "en"), ("en", "es"))


def other_language(language):
    return "en" if language == "es" else "es"


def is_bad_transcription(text):
    compact = re.sub(r"\s+", "", text.lower())
    if len(compact) > 1000:
        return True
    if len(compact) >= 18 and re.search(r"(.{2,12}?)\1{5,}", compact):
        return True
    words = re.findall(r"\w+", compact)
    if len(words) >= 8:
        _, times = Counter(words).most_common(1)[0]
        if times >= 8 and times > len(words) * 0.4:
            return True
    return False


class Translator:
    def __init__(self, model_size=config.WHISPER_MODEL):
        self._ensure_packages()
        self.whisper = WhisperModel(
            model_size,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
        self._cache = {}

    @staticmethod
    def _has_packages():
        languages = {language.code: language for language in argos_translate.get_installed_languages()}
        for source, target in PAIRS:
            if source not in languages or target not in languages:
                return False
            if languages[source].get_translation(languages[target]) is None:
                return False
        return True

    @classmethod
    def _ensure_packages(cls):
        if cls._has_packages():
            return
        argos_package.update_package_index()
        available = argos_package.get_available_packages()
        for package in available:
            if (package.from_code, package.to_code) in PAIRS:
                argos_package.install_from_path(package.download())

    def translate(self, text, source, target):
        key = (text, source, target)
        if key not in self._cache:
            self._cache[key] = argos_translate.translate(text, source, target)
        return self._cache[key]

    def warmup(self):
        argos_settings.compute_type = "float32"
        self.translate("Hola, ¿cómo estás?", "es", "en")
        argos_settings.compute_type = "int8"
        self.translate("Hello, how are you?", "en", "es")
        argos_settings.compute_type = "float32"
        self.process(np.zeros(config.SAMPLE_RATE, dtype=np.float32), "es")

    def process(self, audio: np.ndarray, target_hint):
        segments, info = self.whisper.transcribe(
            audio,
            beam_size=5,
            condition_on_previous_text=False,
            vad_filter=True,
            no_repeat_ngram_size=5,
            repetition_penalty=1.2,
            log_prob_threshold=-1.0,
        )
        detected = info.language
        if detected not in ("es", "en"):
            return None

        original = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.avg_logprob > -0.85 and segment.no_speech_prob < 0.6
        ).strip()
        if not original or is_bad_transcription(original):
            return None

        if target_hint in ("es", "en") and detected != target_hint:
            target = target_hint
        else:
            target = other_language(detected)

        return {
            "source": detected,
            "target": target,
            "original": original,
            "translated": self.translate(original, detected, target),
        }
