from __future__ import annotations

import numpy as np
import torch
from speechbrain.inference.speaker import EncoderClassifier

import config


class SpeakerDiarizer:
    def __init__(self):
        self._model = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
        self._centroids = []
        self._counts = []
        self._last_speaker = 1

    def reset(self):
        self._centroids.clear()
        self._counts.clear()
        self._last_speaker = 1

    @property
    def speaker_count(self):
        return len(self._centroids)

    def identify(self, audio):
        samples = np.asarray(audio, dtype=np.float32)[
            : config.SPEAKER_EMBED_SECONDS * config.SAMPLE_RATE
        ]
        if samples.size < config.MIN_SPEAKER_SAMPLES:
            return self._last_speaker

        waveform = torch.from_numpy(samples).unsqueeze(0)
        embedding = self._model.encode_batch(waveform).squeeze().numpy()
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return self._last_speaker
        embedding /= norm

        if not self._centroids:
            self._centroids.append(embedding.copy())
            self._counts.append(1)
            self._last_speaker = 1
            return 1

        similarities = np.array([float(np.dot(embedding, centroid)) for centroid in self._centroids])
        best = int(np.argmax(similarities))

        if similarities[best] >= config.SPEAKER_THRESHOLD or len(self._centroids) >= config.MAX_SPEAKERS:
            weight = self._counts[best]
            updated = (self._centroids[best] * weight + embedding) / (weight + 1)
            self._centroids[best] = updated / np.linalg.norm(updated)
            self._counts[best] += 1
            speaker = best + 1
        else:
            self._centroids.append(embedding.copy())
            self._counts.append(1)
            speaker = len(self._centroids)

        self._last_speaker = speaker
        return speaker
