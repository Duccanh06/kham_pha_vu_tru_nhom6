"""Sound manager — procedural synth sounds using pygame mixer"""
import pygame
import numpy as np
import random
import math


def generate_tone(freq=440, duration=0.15, volume=0.4, wave='sine',
                  fade_out=True, sample_rate=22050):
    """Generate a simple waveform tone as pygame Sound."""
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    if wave == 'sine':
        data = np.sin(2 * np.pi * freq * t)
    elif wave == 'square':
        data = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == 'sawtooth':
        data = 2 * (t * freq - np.floor(t * freq + 0.5))
    elif wave == 'noise':
        data = np.random.uniform(-1, 1, n)
    else:
        data = np.sin(2 * np.pi * freq * t)

    if fade_out:
        fade = np.linspace(1, 0, n)
        data *= fade

    data = (data * volume * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)


def generate_laser():
    """Descending laser chirp."""
    sample_rate = 22050
    duration = 0.18
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n)
    freq = np.linspace(900, 300, n)
    data = np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
    fade = np.linspace(1, 0, n)
    data = (data * fade * 0.5 * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)


def generate_explosion(big=False):
    """Rumbling explosion noise."""
    sample_rate = 22050
    duration = 0.6 if big else 0.35
    n = int(sample_rate * duration)
    noise = np.random.uniform(-1, 1, n)
    # Low-pass: average over 8 samples
    kernel = np.ones(8) / 8
    noise = np.convolve(noise, kernel, mode='same')
    fade = np.exp(-5 * np.linspace(0, 1, n))
    vol = 0.7 if big else 0.5
    data = (noise * fade * vol * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)


def generate_pickup():
    """Rising arpeggio for collecting resources."""
    sample_rate = 22050
    freqs = [440, 550, 660, 880]
    seg = int(sample_rate * 0.07)
    chunks = []
    for f in freqs:
        t = np.linspace(0, 0.07, seg)
        d = np.sin(2 * np.pi * f * t)
        fade = np.linspace(1, 0, seg)
        chunks.append(d * fade)
    data = np.concatenate(chunks)
    data = (data * 0.45 * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)


def generate_alert():
    """Warning beeps."""
    sample_rate = 22050
    seg = int(sample_rate * 0.1)
    t = np.linspace(0, 0.1, seg)
    beep = np.sin(2 * np.pi * 880 * t)
    silence = np.zeros(seg // 2)
    data = np.concatenate([beep, silence, beep, silence])
    data = (data * 0.5 * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)


def generate_engine_hum():
    """Continuous engine hum loop."""
    sample_rate = 22050
    duration = 1.0
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n)
    # Two oscillators detuned
    d = (np.sin(2 * np.pi * 80 * t) * 0.5
         + np.sin(2 * np.pi * 83 * t) * 0.3
         + np.sin(2 * np.pi * 160 * t) * 0.15)
    data = (d * 0.25 * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)


def generate_ambient_space():
    """Low atmospheric drone."""
    sample_rate = 22050
    duration = 3.0
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n)
    d = (np.sin(2 * np.pi * 40 * t) * 0.4
         + np.sin(2 * np.pi * 60 * t) * 0.2
         + np.random.uniform(-0.05, 0.05, n))
    # Slow volume modulation
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t)
    data = (d * lfo * 0.3 * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)


class SoundManager:
    def __init__(self):
        self.enabled = True
        self.volume = 0.7
        self.sounds = {}
        self._init()

    def _init(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sounds['laser']     = generate_laser()
            self.sounds['explosion'] = generate_explosion(big=False)
            self.sounds['big_exp']   = generate_explosion(big=True)
            self.sounds['pickup']    = generate_pickup()
            self.sounds['alert']     = generate_alert()
            self.sounds['engine']    = generate_engine_hum()
            self.sounds['ambient']   = generate_ambient_space()
            self.sounds['hit']       = generate_tone(200, 0.1, 0.3, 'noise')
            self.sounds['shield']    = generate_tone(600, 0.12, 0.35, 'sawtooth')
            self.sounds['warp']      = generate_tone(120, 0.8, 0.5, 'sawtooth')
            # Start ambient
            self.sounds['ambient'].set_volume(0.2)
            self.sounds['ambient'].play(-1)
            print("[Sound] Procedural audio initialized OK")
        except Exception as e:
            self.enabled = False
            print(f"[Sound] Audio disabled: {e}")

    def play(self, name, volume=None):
        if not self.enabled or name not in self.sounds:
            return
        s = self.sounds[name]
        vol = (volume if volume is not None else self.volume)
        s.set_volume(min(1.0, vol))
        s.play()

    def stop(self, name):
        if name in self.sounds:
            self.sounds[name].stop()

    def set_master_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
