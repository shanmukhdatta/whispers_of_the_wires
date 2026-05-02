"""Music generation engine using free/open-source models.

This module provides two generation modes:
1. AI Mode (MusicGen) - Meta's free model from Hugging Face, downloads automatically
2. Procedural Mode - Custom numpy-based synthesis, always works offline

MusicGen Details:
- Model: facebook/musicgen-small (300M params, ~1.2GB download)
- License: MIT (code), CC-BY-NC 4.0 (weights)
- No API key required - downloads from Hugging Face automatically
- Works on CPU (slower) or GPU (faster)
- Source: https://huggingface.co/facebook/musicgen-small

Reference: Copet et al. (2023) - Simple and Controllable Music Generation
"""
import os
import io
import base64
import random
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import warnings
warnings.filterwarnings("ignore")

# Try to import optional dependencies
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    from scipy.io import wavfile
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import pretty_midi
    HAS_PRETTY_MIDI = True
except ImportError:
    HAS_PRETTY_MIDI = False


class MusicGenerator:
    """Generates music using various free techniques.

    Features:
    - AI Generation: Meta MusicGen via Hugging Face (free, no API key)
    - Procedural Generation: Custom numpy synthesis (offline, always works)
    - MIDI Export: pretty_midi integration
    - Multi-track: Melody, Harmony, Bass, Rhythm
    """

    # Musical constants
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    SCALES = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'dorian': [0, 2, 3, 5, 7, 9, 10],
        'phrygian': [0, 1, 3, 5, 7, 8, 10],
        'lydian': [0, 2, 4, 6, 7, 9, 11],
        'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    }

    CHORD_PROGRESSIONS = {
        'major': [
            [0, 4, 5, 3],   # I-V-vi-IV
            [0, 5, 3, 4],   # I-V-IV-vi
            [0, 3, 4, 0],   # I-vi-IV-I
            [0, 4, 0, 5],   # I-V-I-V
            [0, 2, 3, 5],   # I-iii-vi-V
        ],
        'minor': [
            [0, 3, 4, 0],   # i-vi-VII-i
            [0, 5, 3, 4],   # i-V-vi-VII
            [0, 4, 5, 0],   # i-VII-V-i
            [0, 3, 0, 5],   # i-vi-i-V
        ],
    }

    def __init__(self, sample_rate: int = 32000):
        self.sample_rate = sample_rate
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
        self._model_loaded = False
        self._musicgen_model = None
        self._processor = None

    def _load_musicgen(self):
        """Lazy load MusicGen model from Hugging Face (FREE - no API key needed).

        The model downloads automatically on first use:
        - facebook/musicgen-small: ~1.2GB, 300M parameters
        - Cached at: ~/.cache/huggingface/

        Reference: https://huggingface.co/facebook/musicgen-small
        """
        if self._model_loaded:
            return self._musicgen_model

        try:
            from transformers import AutoProcessor, MusicgenForConditionalGeneration
            import torch

            print("Loading MusicGen model (free from Hugging Face)...")
            print("This will download ~1.2GB on first use. Please wait...")
            model_name = "facebook/musicgen-small"

            self._processor = AutoProcessor.from_pretrained(model_name)
            self._musicgen_model = MusicgenForConditionalGeneration.from_pretrained(model_name)

            # Move to GPU if available
            if torch.cuda.is_available():
                self._musicgen_model = self._musicgen_model.to("cuda")
                print("Using CUDA for faster generation")
            else:
                print("Using CPU (slower but works everywhere)")

            self._model_loaded = True
            print("MusicGen model loaded successfully!")
            return self._musicgen_model

        except Exception as e:
            print(f"Could not load MusicGen: {e}")
            print("Falling back to procedural generation (works offline)")
            return None

    def generate(self, params: Dict, use_ai: bool = True) -> Dict:
        """Generate music based on parameters.

        Args:
            params: Dictionary with generation parameters
            use_ai: Whether to try AI generation first

        Returns:
            Dictionary with generation results
        """
        generation_id = f"gen_{random.randint(100000, 999999)}"

        try:
            if use_ai:
                # Try AI generation first (MusicGen - free from Hugging Face)
                result = self._generate_with_ai(params, generation_id)
                if result:
                    return result

            # Fallback to procedural generation (always works)
            return self._generate_procedural(params, generation_id)

        except Exception as e:
            print(f"Generation error: {e}")
            return self._generate_procedural(params, generation_id)

    def _generate_with_ai(self, params: Dict, generation_id: str) -> Optional[Dict]:
        """Generate using MusicGen (free Hugging Face model - no API key).

        Uses Meta's MusicGen model:
        - Paper: Simple and Controllable Music Generation (Copet et al., 2023)
        - Model: facebook/musicgen-small (300M params)
        - License: MIT (code), CC-BY-NC 4.0 (weights)
        """
        model = self._load_musicgen()
        if model is None:
            return None

        try:
            import torch

            # Build prompt from parameters
            genre = params.get("genre", "ambient")
            mood_desc = self._get_mood_description(params)
            prompt = f"{mood_desc} {genre} music, high quality"

            # Prepare inputs
            inputs = self._processor(
                text=[prompt],
                padding=True,
                return_tensors="pt",
            )

            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            # Generate
            duration = min(params.get("duration", 10), 30)  # Max 30s for free tier
            max_length = int(duration * self.sample_rate / 256)  # Approximate

            with torch.no_grad():
                audio_values = model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    do_sample=True,
                    guidance_scale=3.0,
                )

            # Convert to numpy
            audio = audio_values[0, 0].cpu().numpy()

            # Normalize
            audio = audio / np.max(np.abs(audio))

            # Save
            output_path = self.output_dir / f"{generation_id}.wav"
            if HAS_SOUNDFILE:
                sf.write(str(output_path), audio, self.sample_rate)
            elif HAS_SCIPY:
                wavfile.write(str(output_path), self.sample_rate, (audio * 32767).astype(np.int16))

            return {
                "generation_id": generation_id,
                "status": "completed",
                "audio_path": str(output_path),
                "duration": duration,
                "sample_rate": self.sample_rate,
                "method": "musicgen_ai",
                "prompt": prompt,
                "params": params,
            }

        except Exception as e:
            print(f"AI generation failed: {e}")
            return None

    def _generate_procedural(self, params: Dict, generation_id: str) -> Dict:
        """Generate music procedurally using numpy (offline, always works).

        Uses custom synthesis engine with:
        - ADSR envelopes
        - Multi-track mixing
        - Chord progressions
        - Reverb effects
        """
        duration = params.get("duration", 10)
        tempo = params.get("tempo", 120)
        key = params.get("key", "C_major")
        genre = params.get("genre", "ambient")

        # Parse key
        root_note, scale_type = self._parse_key(key)
        scale = self.SCALES.get(scale_type, self.SCALES['major'])

        # Generate audio
        audio = self._synthesize_music(
            duration=duration,
            tempo=tempo,
            root_note=root_note,
            scale=scale,
            genre=genre,
            params=params,
        )

        # Save
        output_path = self.output_dir / f"{generation_id}.wav"
        if HAS_SOUNDFILE:
            sf.write(str(output_path), audio, self.sample_rate)
        elif HAS_SCIPY:
            wavfile.write(str(output_path), self.sample_rate, (audio * 32767).astype(np.int16))
        else:
            # Raw numpy save as fallback
            np.save(str(output_path).replace('.wav', '.npy'), audio)
            output_path = str(output_path).replace('.wav', '.npy')

        # Generate MIDI
        midi_path = self._generate_midi(params, generation_id)

        return {
            "generation_id": generation_id,
            "status": "completed",
            "audio_path": str(output_path),
            "midi_path": str(midi_path) if midi_path else None,
            "duration": duration,
            "sample_rate": self.sample_rate,
            "method": "procedural",
            "params": params,
        }

    def _synthesize_music(self, duration: int, tempo: int, root_note: int, 
                          scale: List[int], genre: str, params: Dict) -> np.ndarray:
        """Synthesize music using numpy arrays.

        Creates 4 tracks:
        1. Melody - Lead instrument
        2. Harmony - Chord progressions
        3. Bass - Low frequency foundation
        4. Rhythm - Drums (if high arousal)
        """
        num_samples = int(duration * self.sample_rate)
        audio = np.zeros(num_samples, dtype=np.float32)

        # Calculate beat timing
        beat_duration = 60.0 / tempo
        samples_per_beat = int(beat_duration * self.sample_rate)

        # Get chord progression
        progression = self._get_chord_progression(scale_type='major' if 'major' in params.get('key', '') else 'minor')

        # Generate multiple tracks
        tracks = []

        # Track 1: Melody
        melody = self._generate_melody_track(
            num_samples, samples_per_beat, root_note, scale, progression, params
        )
        tracks.append(melody * 0.4)

        # Track 2: Harmony/Chords
        harmony = self._generate_harmony_track(
            num_samples, samples_per_beat, root_note, scale, progression, params
        )
        tracks.append(harmony * 0.3)

        # Track 3: Bass
        bass = self._generate_bass_track(
            num_samples, samples_per_beat, root_note, scale, progression, params
        )
        tracks.append(bass * 0.2)

        # Track 4: Rhythm/Drums (if high arousal)
        if params.get('arousal', 0) > 0:
            rhythm = self._generate_rhythm_track(
                num_samples, samples_per_beat, params
            )
            tracks.append(rhythm * 0.15)

        # Mix tracks
        for track in tracks:
            audio += track

        # Normalize
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.8

        # Apply simple reverb effect
        audio = self._apply_reverb(audio)

        return audio

    def _generate_melody_track(self, num_samples: int, samples_per_beat: int,
                                root_note: int, scale: List[int], progression: List[int],
                                params: Dict) -> np.ndarray:
        """Generate a melody track with ADSR envelopes."""
        track = np.zeros(num_samples, dtype=np.float32)

        # Note durations in beats
        durations = [0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 2.0]

        current_sample = 0
        note_idx = 0

        while current_sample < num_samples - samples_per_beat:
            # Pick a note from the scale
            scale_degree = random.choice(scale)
            octave = random.choice([0, 1, 2])
            midi_note = root_note + scale_degree + (octave * 12)

            # Get frequency
            freq = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

            # Note duration
            duration_beats = random.choice(durations)
            note_samples = int(duration_beats * samples_per_beat)
            note_samples = min(note_samples, num_samples - current_sample)

            # Generate note with envelope
            t = np.arange(note_samples) / self.sample_rate

            # Use different waveforms based on genre
            if params.get('genre') in ['piano', 'acoustic', 'classical']:
                # Piano-like: mix of sine and harmonics
                wave = (0.6 * np.sin(2 * np.pi * freq * t) +
                        0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                        0.1 * np.sin(2 * np.pi * freq * 3 * t))
            elif params.get('genre') in ['electronic', 'edm', 'synthwave']:
                # Synth: sawtooth-like
                wave = self._sawtooth(2 * np.pi * freq * t)
            else:
                # Default: sine with slight harmonics
                wave = (0.8 * np.sin(2 * np.pi * freq * t) +
                        0.2 * np.sin(2 * np.pi * freq * 2 * t))

            # ADSR envelope
            envelope = self._adsr_envelope(note_samples, self.sample_rate)
            wave = wave * envelope

            # Add to track
            end_idx = min(current_sample + note_samples, num_samples)
            track[current_sample:end_idx] += wave[:end_idx - current_sample]

            current_sample += note_samples
            note_idx += 1

        return track

    def _generate_harmony_track(self, num_samples: int, samples_per_beat: int,
                                 root_note: int, scale: List[int], progression: List[int],
                                 params: Dict) -> np.ndarray:
        """Generate a harmony/chord track."""
        track = np.zeros(num_samples, dtype=np.float32)

        chord_duration = samples_per_beat * 4  # 4 beats per chord

        for i, chord_degree in enumerate(progression):
            start_sample = i * chord_duration
            if start_sample >= num_samples:
                break

            end_sample = min(start_sample + chord_duration, num_samples)
            chord_samples = end_sample - start_sample

            # Build chord (root, third, fifth)
            chord_notes = [
                root_note + scale[chord_degree % len(scale)],
                root_note + scale[(chord_degree + 2) % len(scale)],
                root_note + scale[(chord_degree + 4) % len(scale)],
            ]

            t = np.arange(chord_samples) / self.sample_rate
            chord_wave = np.zeros(chord_samples, dtype=np.float32)

            for note in chord_notes:
                freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
                # Lower octave for harmony
                freq = freq / 2
                chord_wave += 0.3 * np.sin(2 * np.pi * freq * t)

            # Soft envelope
            envelope = self._adsr_envelope(chord_samples, self.sample_rate, 
                                            attack=0.1, decay=0.2, sustain=0.6, release=0.5)
            chord_wave = chord_wave * envelope

            track[start_sample:end_sample] += chord_wave

        return track

    def _generate_bass_track(self, num_samples: int, samples_per_beat: int,
                              root_note: int, scale: List[int], progression: List[int],
                              params: Dict) -> np.ndarray:
        """Generate a bass track."""
        track = np.zeros(num_samples, dtype=np.float32)

        # Bass plays on beats 1 and 3
        for beat in range(0, num_samples, samples_per_beat):
            if beat >= num_samples:
                break

            # Simple bass pattern
            chord_idx = (beat // (samples_per_beat * 4)) % len(progression)
            bass_note = root_note + scale[progression[chord_idx] % len(scale)] - 24  # 2 octaves down

            freq = 440.0 * (2.0 ** ((bass_note - 69) / 12.0))

            note_samples = min(samples_per_beat // 2, num_samples - beat)
            t = np.arange(note_samples) / self.sample_rate

            # Sine wave for clean bass
            wave = np.sin(2 * np.pi * freq * t)
            envelope = self._adsr_envelope(note_samples, self.sample_rate, 
                                            attack=0.01, decay=0.1, sustain=0.5, release=0.1)

            track[beat:beat + note_samples] += wave * envelope * 0.8

        return track

    def _generate_rhythm_track(self, num_samples: int, samples_per_beat: int,
                                params: Dict) -> np.ndarray:
        """Generate a simple rhythm track."""
        track = np.zeros(num_samples, dtype=np.float32)

        # Kick on beat 1
        for beat in range(0, num_samples, samples_per_beat):
            if beat >= num_samples:
                break
            kick_samples = min(int(0.1 * self.sample_rate), num_samples - beat)
            t = np.arange(kick_samples) / self.sample_rate
            # Sine sweep for kick
            freq = 100 * np.exp(-t * 30)
            kick = np.sin(2 * np.pi * freq * t) * np.exp(-t * 10)
            track[beat:beat + kick_samples] += kick * 0.5

        # Hi-hat on off-beats
        for beat in range(samples_per_beat // 2, num_samples, samples_per_beat):
            if beat >= num_samples:
                break
            hat_samples = min(int(0.05 * self.sample_rate), num_samples - beat)
            t = np.arange(hat_samples) / self.sample_rate
            # Noise for hi-hat
            hat = np.random.randn(hat_samples) * np.exp(-t * 50)
            track[beat:beat + hat_samples] += hat * 0.15

        return track

    def _sawtooth(self, x: np.ndarray) -> np.ndarray:
        """Generate sawtooth wave."""
        return 2 * (x / (2 * np.pi) - np.floor(x / (2 * np.pi) + 0.5))

    def _adsr_envelope(self, num_samples: int, sample_rate: int,
                        attack: float = 0.05, decay: float = 0.1, 
                        sustain: float = 0.7, release: float = 0.2) -> np.ndarray:
        """Generate ADSR envelope.

        Args:
            num_samples: Number of samples
            sample_rate: Sample rate
            attack: Attack time in seconds
            decay: Decay time in seconds
            sustain: Sustain level (0-1)
            release: Release time in seconds
        """
        envelope = np.zeros(num_samples)

        attack_samples = int(attack * sample_rate)
        decay_samples = int(decay * sample_rate)
        release_samples = int(release * sample_rate)
        sustain_samples = num_samples - attack_samples - decay_samples - release_samples

        if sustain_samples < 0:
            sustain_samples = 0
            release_samples = num_samples - attack_samples - decay_samples

        # Attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Decay
        if decay_samples > 0:
            start = attack_samples
            end = attack_samples + decay_samples
            envelope[start:end] = np.linspace(1, sustain, decay_samples)

        # Sustain
        if sustain_samples > 0:
            start = attack_samples + decay_samples
            end = start + sustain_samples
            envelope[start:end] = sustain

        # Release
        if release_samples > 0:
            start = num_samples - release_samples
            envelope[start:] = np.linspace(envelope[start] if start < num_samples else sustain, 0, release_samples)

        return envelope

    def _apply_reverb(self, audio: np.ndarray, decay: float = 0.5, 
                       delay_ms: float = 50) -> np.ndarray:
        """Apply simple reverb effect."""
        delay_samples = int(delay_ms * self.sample_rate / 1000)

        if delay_samples >= len(audio):
            return audio

        reverb = np.zeros_like(audio)
        reverb[delay_samples:] = audio[:-delay_samples] * decay

        # Multiple reflections
        for i in range(1, 4):
            offset = delay_samples * i
            if offset < len(audio):
                end = len(audio) - offset
                reverb[offset:] += audio[:end] * (decay ** i) * 0.5

        return audio + reverb * 0.3

    def _parse_key(self, key: str) -> Tuple[int, str]:
        """Parse key string to MIDI note number and scale type."""
        parts = key.split('_')
        note_name = parts[0]
        scale_type = parts[1] if len(parts) > 1 else 'major'

        # Convert note name to MIDI number (C4 = 60)
        note_idx = self.NOTES.index(note_name) if note_name in self.NOTES else 0
        midi_note = 48 + note_idx  # C3 as base

        return midi_note, scale_type

    def _get_chord_progression(self, scale_type: str = 'major') -> List[int]:
        """Get a random chord progression."""
        progressions = self.CHORD_PROGRESSIONS.get(scale_type, self.CHORD_PROGRESSIONS['major'])
        return random.choice(progressions)

    def _get_mood_description(self, params: Dict) -> str:
        """Convert parameters to text description for MusicGen prompt."""
        valence = params.get('valence', 0)
        arousal = params.get('arousal', 0)

        descriptions = []

        if valence > 0.5:
            descriptions.append("happy")
        elif valence > 0.2:
            descriptions.append("pleasant")
        elif valence < -0.5:
            descriptions.append("sad")
        elif valence < -0.2:
            descriptions.append("melancholic")

        if arousal > 0.5:
            descriptions.append("energetic")
        elif arousal > 0.2:
            descriptions.append("moderate")
        elif arousal < -0.5:
            descriptions.append("calm")
        elif arousal < -0.2:
            descriptions.append("relaxing")

        genre = params.get('genre', 'music')
        descriptions.append(genre)

        return " ".join(descriptions) if descriptions else "music"

    def _generate_midi(self, params: Dict, generation_id: str) -> Optional[Path]:
        """Generate MIDI file from parameters."""
        if not HAS_PRETTY_MIDI:
            return None

        try:
            midi = pretty_midi.PrettyMIDI()

            # Create instruments
            piano = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano

            # Parse key
            root_note, scale_type = self._parse_key(params.get("key", "C_major"))
            scale = self.SCALES.get(scale_type, self.SCALES['major'])
            progression = self._get_chord_progression(scale_type)

            tempo = params.get("tempo", 120)
            duration = params.get("duration", 10)

            # Generate melody notes
            beat_time = 60.0 / tempo
            current_time = 0.0

            while current_time < duration:
                scale_degree = random.choice(scale)
                octave = random.choice([0, 1])
                note_num = root_note + scale_degree + (octave * 12)

                note_duration = random.choice([0.25, 0.5, 0.5, 1.0]) * beat_time

                note = pretty_midi.Note(
                    velocity=random.randint(60, 100),
                    pitch=min(127, max(0, note_num)),
                    start=current_time,
                    end=min(current_time + note_duration, duration)
                )
                piano.notes.append(note)

                current_time += note_duration

            midi.instruments.append(piano)

            # Save
            midi_path = self.output_dir / f"{generation_id}.mid"
            midi.write(str(midi_path))

            return midi_path

        except Exception as e:
            print(f"MIDI generation failed: {e}")
            return None

    def get_audio_bytes(self, audio_path: str) -> bytes:
        """Read audio file as bytes."""
        with open(audio_path, 'rb') as f:
            return f.read()

    def get_audio_base64(self, audio_path: str) -> str:
        """Get audio as base64 string."""
        audio_bytes = self.get_audio_bytes(audio_path)
        return base64.b64encode(audio_bytes).decode('utf-8')


# Singleton instance
_generator = None

def get_generator() -> MusicGenerator:
    """Get or create the music generator singleton."""
    global _generator
    if _generator is None:
        _generator = MusicGenerator()
    return _generator
