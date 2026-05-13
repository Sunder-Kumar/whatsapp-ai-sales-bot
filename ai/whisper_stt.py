import whisper
import os
import subprocess
from typing import Optional

class WhisperTranscriber:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None

    def load_model(self):
        """Loads the Whisper model into memory."""
        if self.model is None:
            print(f"Loading Whisper model ({self.model_size})...")
            self.model = whisper.load_model(self.model_size)
            print("Whisper model loaded.")

    def transcribe(self, audio_path: str) -> Optional[str]:
        """
        Transcribes an audio file.
        Converts to .wav first if necessary.
        """
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return None

        self.load_model()

        # Convert to .wav if it's .ogg or .opus
        wav_path = audio_path
        if not audio_path.endswith(".wav"):
            wav_path = audio_path.rsplit(".", 1)[0] + ".wav"
            try:
                # Using ffmpeg to convert
                subprocess.run([
                    "ffmpeg", "-i", audio_path, 
                    "-ar", "16000", "-ac", "1", 
                    "-c:a", "pcm_s16le", wav_path, 
                    "-y", "-loglevel", "quiet"
                ], check=True)
            except Exception as e:
                print(f"FFmpeg conversion failed: {e}")
                return None

        try:
            result = self.model.transcribe(wav_path)
            text = result.get("text", "").strip()
            
            # Cleanup temp wav if created
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
                
            return text
        except Exception as e:
            print(f"Transcription failed: {e}")
            return None

# Global instance
transcriber = WhisperTranscriber(model_size="base")
