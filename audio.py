from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass

import numpy as np
import pyaudiowpatch as pyaudio
import torch
from silero_vad import load_silero_vad

import config


@dataclass
class State:
    target_language: str = config.DEFAULT_TARGET_LANGUAGE
    paused: bool = False
    reset_speakers: bool = False


@dataclass
class CaptureConfig:
    source_id: str
    name: str
    index: int
    rate: int
    channels: int


class StreamResampler:
    def __init__(self, source_rate, target_rate=config.SAMPLE_RATE):
        self.step = source_rate / target_rate
        self.next_position = 0.0
        self.total_input = 0
        self.previous_value = 0.0

    def process(self, chunk):
        start = self.total_input
        end = start + len(chunk)
        self.total_input = end

        positions = []
        position = self.next_position
        while position < end:
            positions.append(position)
            position += self.step
        self.next_position = position
        if not positions:
            return np.empty(0, dtype=np.float32)

        indexes = np.floor(np.asarray(positions)).astype(np.int64)
        fraction = np.asarray(positions) - indexes
        local = np.clip(indexes - start, 0, len(chunk) - 1)
        current = chunk[local]
        previous = np.where(local > 0, chunk[np.maximum(local - 1, 0)], self.previous_value)
        self.previous_value = float(chunk[-1])
        return (previous + (current - previous) * fraction).astype(np.float32)


class AudioCapture(threading.Thread):
    def __init__(self, capture_config, audio_queue, ui_queue, stop_event, state):
        super().__init__(daemon=True, name=f"capture-{capture_config.source_id}")
        self.config_device = capture_config
        self.audio_queue = audio_queue
        self.ui_queue = ui_queue
        self.stop_event = stop_event
        self.state = state
        self._vad = load_silero_vad()
        self._resampler = None
        if capture_config.rate != config.SAMPLE_RATE:
            self._resampler = StreamResampler(capture_config.rate)

    def run(self):
        audio = pyaudio.PyAudio()
        stream = None
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=self.config_device.channels,
                rate=self.config_device.rate,
                input=True,
                input_device_index=self.config_device.index,
                frames_per_buffer=max(config.FRAME_SAMPLES, self.config_device.rate // 25),
            )
            self._listen(stream)
        except Exception as exc:
            self.ui_queue.put(("error", f"No se pudo abrir {self.config_device.name}: {exc}"))
        finally:
            if stream is not None:
                stream.close()
            audio.terminate()

    def _listen(self, stream):
        preroll = deque(maxlen=config.PRE_SPEECH_FRAMES)
        active = []
        silence_frames = 0
        pending = np.empty(0, dtype=np.float32)
        max_frames = int(config.MAX_UTTERANCE_SECONDS * config.SAMPLE_RATE / config.FRAME_SAMPLES)
        min_frames = int(config.MIN_UTTERANCE_SECONDS * config.SAMPLE_RATE / config.FRAME_SAMPLES)
        block_frames = max(config.FRAME_SAMPLES, self.config_device.rate // 25)

        while not self.stop_event.is_set():
            raw = stream.read(block_frames, exception_on_overflow=False)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if self.config_device.channels > 1:
                samples = samples.reshape(-1, self.config_device.channels).mean(axis=1)
            if self._resampler is not None:
                samples = self._resampler.process(samples)

            pending = np.concatenate((pending, samples))
            while pending.size >= config.FRAME_SAMPLES:
                frame = pending[: config.FRAME_SAMPLES]
                pending = pending[config.FRAME_SAMPLES :]
                active, silence_frames = self._handle_frame(frame, preroll, active, silence_frames, min_frames, max_frames)

        if active:
            self._emit(active, min_frames)

    def _handle_frame(self, frame, preroll, active, silence_frames, min_frames, max_frames):
        if self.state.paused:
            return [], 0

        probability = self._vad(torch.from_numpy(frame), config.SAMPLE_RATE).item()

        if probability >= config.VAD_THRESHOLD:
            if not active:
                active = list(preroll)
            active.append(frame)
            return active, 0

        if active:
            active.append(frame)
            silence_frames += 1
            if silence_frames >= config.SILENCE_FRAMES or len(active) >= max_frames:
                self._emit(active, min_frames)
                return [], 0
            return active, silence_frames

        preroll.append(frame)
        return active, 0

    def _emit(self, frames, min_frames):
        if len(frames) < min_frames:
            return
        self.audio_queue.put((self.config_device.source_id, np.concatenate(frames)))


def _audio_client():
    return pyaudio.PyAudio()


def _find_loopback(name):
    audio = _audio_client()
    try:
        wasapi = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
        output = audio.get_device_info_by_index(wasapi["defaultOutputDevice"])
        if name:
            for index in range(audio.get_device_count()):
                device = audio.get_device_info_by_index(index)
                if name.casefold() in device["name"].casefold() and device.get("isLoopbackDevice"):
                    output = device
                    break
        if not output.get("isLoopbackDevice"):
            for loopback in audio.get_loopback_device_info_generator():
                if output["name"] in loopback["name"]:
                    output = loopback
                    break
        return CaptureConfig(
            "speaker",
            output["name"],
            output["index"],
            int(output["defaultSampleRate"]),
            int(output["maxInputChannels"]),
        )
    finally:
        audio.terminate()


def list_devices():
    audio = _audio_client()
    try:
        print("SALIDAS DE AUDIO (loopback WASAPI):")
        for device in audio.get_loopback_device_info_generator():
            print(f"  [{device['index']}] {device['name']}")
    finally:
        audio.terminate()


def find_speaker(name=None):
    return _find_loopback(name)
