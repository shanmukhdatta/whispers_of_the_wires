"""Audio visualization utilities."""
import numpy as np
import base64
import io
from typing import Optional, Tuple
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import librosa
    import librosa.display
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


class AudioVisualizer:
    """Creates visual representations of audio."""

    def __init__(self, sample_rate: int = 32000):
        self.sample_rate = sample_rate

    def create_waveform(self, audio_path: str, width: int = 800, height: int = 200) -> str:
        """Create waveform visualization as base64 SVG."""
        try:
            # Load audio
            if HAS_LIBROSA:
                audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            else:
                # Fallback: try to load with scipy
                try:
                    from scipy.io import wavfile
                    sr, audio = wavfile.read(audio_path)
                    if audio.ndim > 1:
                        audio = audio.mean(axis=1)
                    audio = audio.astype(np.float32)
                    if audio.max() > 1.0:
                        audio = audio / 32768.0
                except:
                    return self._create_placeholder_waveform(width, height)

            # Downsample for visualization
            target_points = min(len(audio), 2000)
            if len(audio) > target_points:
                indices = np.linspace(0, len(audio) - 1, target_points, dtype=int)
                audio_vis = audio[indices]
            else:
                audio_vis = audio

            # Normalize
            audio_vis = audio_vis / (np.max(np.abs(audio_vis)) + 1e-8)

            # Create SVG
            svg = self._audio_to_svg_waveform(audio_vis, width, height)
            return svg

        except Exception as e:
            print(f"Waveform creation error: {e}")
            return self._create_placeholder_waveform(width, height)

    def create_spectrogram(self, audio_path: str, width: int = 800, height: int = 300) -> str:
        """Create spectrogram visualization as base64 image."""
        if not HAS_MATPLOTLIB or not HAS_LIBROSA:
            return self._create_placeholder_spectrogram(width, height)

        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)

            # Create figure
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            fig.patch.set_facecolor('#0F172A')
            ax.set_facecolor('#0F172A')

            # Compute spectrogram
            D = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)

            # Plot
            img = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='hz', 
                                            ax=ax, cmap='magma')
            ax.set_xlabel('Time (s)', color='white', fontsize=10)
            ax.set_ylabel('Frequency (Hz)', color='white', fontsize=10)
            ax.tick_params(colors='white')
            ax.set_title('Spectrogram', color='white', fontsize=12, fontweight='bold')

            # Colorbar
            cbar = plt.colorbar(img, ax=ax, format='%+2.0f dB')
            cbar.ax.tick_params(colors='white')

            # Save to buffer
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', facecolor='#0F172A', edgecolor='none')
            plt.close(fig)
            buf.seek(0)

            # Convert to base64
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"Spectrogram creation error: {e}")
            return self._create_placeholder_spectrogram(width, height)

    def create_mood_visualization(self, valence: float, arousal: float, 
                                   dominance: float, width: int = 300, height: int = 300) -> str:
        """Create mood wheel visualization."""
        if not HAS_MATPLOTLIB:
            return self._create_placeholder_mood_wheel(width, height)

        try:
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            fig.patch.set_facecolor('#1E293B')
            ax.set_facecolor('#1E293B')

            # Draw circle
            theta = np.linspace(0, 2*np.pi, 100)
            r = 1.0
            ax.plot(r * np.cos(theta), r * np.sin(theta), color='#334155', linewidth=2)

            # Draw crosshairs
            ax.plot([-1, 1], [0, 0], color='#334155', linewidth=1, linestyle='--')
            ax.plot([0, 0], [-1, 1], color='#334155', linewidth=1, linestyle='--')

            # Labels
            ax.text(0, 1.15, 'Positive', ha='center', va='bottom', color='#10B981', 
                   fontsize=10, fontweight='bold')
            ax.text(0, -1.15, 'Negative', ha='center', va='top', color='#EF4444', 
                   fontsize=10, fontweight='bold')
            ax.text(1.15, 0, 'Energetic', ha='left', va='center', color='#F59E0B', 
                   fontsize=10, fontweight='bold')
            ax.text(-1.15, 0, 'Calm', ha='right', va='center', color='#6366F1', 
                   fontsize=10, fontweight='bold')

            # Plot mood point
            x = arousal  # -1 to 1
            y = valence  # -1 to 1

            # Size based on dominance
            size = 200 + abs(dominance) * 300

            # Color based on valence and arousal
            if valence > 0 and arousal > 0:
                color = '#F59E0B'  # Happy/Energetic
            elif valence > 0 and arousal <= 0:
                color = '#10B981'  # Happy/Calm
            elif valence <= 0 and arousal > 0:
                color = '#EF4444'  # Sad/Energetic
            else:
                color = '#6366F1'  # Sad/Calm

            ax.scatter(x, y, s=size, c=color, alpha=0.8, edgecolors='white', linewidth=2, zorder=5)

            # Add glow effect
            ax.scatter(x, y, s=size*2, c=color, alpha=0.2, zorder=4)

            ax.set_xlim(-1.3, 1.3)
            ax.set_ylim(-1.3, 1.3)
            ax.set_aspect('equal')
            ax.axis('off')

            # Title
            ax.set_title('Mood Map', color='white', fontsize=14, fontweight='bold', pad=20)

            # Save
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', facecolor='#1E293B', edgecolor='none')
            plt.close(fig)
            buf.seek(0)

            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"Mood visualization error: {e}")
            return self._create_placeholder_mood_wheel(width, height)

    def _audio_to_svg_waveform(self, audio: np.ndarray, width: int, height: int) -> str:
        """Convert audio array to SVG waveform."""
        # Create points for the waveform
        n_points = len(audio)
        x_step = width / n_points

        center_y = height / 2
        amplitude = height / 2 * 0.9

        # Build path
        points_top = []
        points_bottom = []

        for i, sample in enumerate(audio):
            x = i * x_step
            y_offset = sample * amplitude
            points_top.append(f"{x:.2f},{center_y - y_offset:.2f}")
            points_bottom.append(f"{x:.2f},{center_y + y_offset:.2f}")

        # Create SVG
        path_data = f"M 0,{center_y} " + " ".join([f"L {p}" for p in points_top])
        path_data += f" L {width},{center_y} "
        path_data += " ".join([f"L {p}" for p in reversed(points_bottom)])
        path_data += " Z"

        svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="waveGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#6366F1;stop-opacity:0.8" />
                    <stop offset="50%" style="stop-color:#EC4899;stop-opacity:0.6" />
                    <stop offset="100%" style="stop-color:#6366F1;stop-opacity:0.2" />
                </linearGradient>
            </defs>
            <rect width="100%" height="100%" fill="#0F172A" rx="8"/>
            <path d="{path_data}" fill="url(#waveGrad)" stroke="#818CF8" stroke-width="1"/>
        </svg>"""

        return svg

    def _create_placeholder_waveform(self, width: int, height: int) -> str:
        """Create placeholder waveform."""
        svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#0F172A" rx="8"/>
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" 
                  fill="#64748B" font-size="14" font-family="sans-serif">
                Waveform visualization will appear here
            </text>
        </svg>"""
        return svg

    def _create_placeholder_spectrogram(self, width: int, height: int) -> str:
        """Create placeholder spectrogram."""
        svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#0F172A" rx="8"/>
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" 
                  fill="#64748B" font-size="14" font-family="sans-serif">
                Spectrogram will appear here
            </text>
        </svg>"""
        return svg

    def _create_placeholder_mood_wheel(self, width: int, height: int) -> str:
        """Create placeholder mood wheel."""
        svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#1E293B" rx="8"/>
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" 
                  fill="#64748B" font-size="14" font-family="sans-serif">
                Mood visualization will appear here
            </text>
        </svg>"""
        return svg


# Singleton
_visualizer = None

def get_visualizer() -> AudioVisualizer:
    """Get or create visualizer singleton."""
    global _visualizer
    if _visualizer is None:
        _visualizer = AudioVisualizer()
    return _visualizer
