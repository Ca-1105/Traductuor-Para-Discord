from __future__ import annotations

import numpy as np
import argostranslate.package as argos_package
import argostranslate.translate as argos_translate
from faster_whisper import WhisperModel

import config

PAIRS = (("es", "en"), ("en", "es"))


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

    def process(self, audio: np.ndarray, source_hint):
        kwargs = dict(
            beam_size=1,
            condition_on_previous_text=False,
            vad_filter=False,
        )
        if source_hint == "auto":
            segments, info = self.whisper.transcribe(audio, **kwargs)
            detected = info.language
        else:
            segments, info = self.whisper.transcribe(audio, language=source_hint, **kwargs)
            detected = source_hint

        if detected not in ("es", "en"):
            return None

        original = " ".join(
            segment.text.strip() for segment in segments if segment.avg_logprob > -0.85
        ).strip()
        if not original:
            return None

        target = "en" if detected == "es" else "es"
        return {
            "source": detected,
            "target": target,
            "original": original,
            "translated": self.translate(original, detected, target),
        }
