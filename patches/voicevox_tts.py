import os
import urllib.request
import urllib.parse
from loguru import logger
from .tts_interface import TTSInterface


class TTSEngine(TTSInterface):
    def __init__(self, base_url="http://localhost:50021", speaker_id=8):
        self.base_url = base_url.rstrip("/")
        self.speaker_id = int(speaker_id)
        self.file_extension = "wav"
        self.new_audio_dir = "cache"
        logger.info(f"VoicevoxTTS initialized: base_url={self.base_url}, speaker_id={self.speaker_id}")
        if not os.path.exists(self.new_audio_dir):
            os.makedirs(self.new_audio_dir)

    def generate_audio(self, text, file_name_no_ext=None):
        logger.info(f"VoicevoxTTS generating audio: speaker={self.speaker_id}, text={text[:20]}")
        file_name = self.generate_cache_file_name(file_name_no_ext, self.file_extension)
        try:
            url1 = f"{self.base_url}/audio_query?text={urllib.parse.quote(text)}&speaker={self.speaker_id}"
            req1 = urllib.request.Request(url1, method="POST")
            with urllib.request.urlopen(req1) as r:
                query_json = r.read()
            url2 = f"{self.base_url}/synthesis?speaker={self.speaker_id}"
            req2 = urllib.request.Request(url2, data=query_json, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req2) as r:
                wav_data = r.read()
            with open(file_name, "wb") as f:
                f.write(wav_data)
            logger.info(f"VoicevoxTTS success: {len(wav_data)} bytes")
        except Exception as e:
            logger.critical(f"VOICEVOX TTS error: {e}")
            return None
        return file_name
