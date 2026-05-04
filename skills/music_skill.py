import threading
import yt_dlp
import vlc
import time
from skills.base import BaseSkill
from loguru import logger

class MusicSkill(BaseSkill):

    TRIGGERS = [
        "play", "play song", "play music", "put on",
        "i want to listen", "can you play", "play some",
        "song", "music", "put some music", "pause music",
        "resume music", "stop music", "stop the song",
        "pause the song", "next song", "skip song"
    ]

    # Singleton VLC instance shared across all plays
    _vlc_instance  = None
    _vlc_player    = None
    _current_song  = None
    _is_playing    = False

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()
        return any(t in text for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        text = user_input.lower().strip()

        # ── Playback controls ──
        if any(w in text for w in ["pause", "pause music", "pause the song"]):
            return self._pause()

        if any(w in text for w in ["resume", "continue", "unpause"]):
            return self._resume()

        if any(w in text for w in [
            "stop music", "stop the song", "stop playing",
            "turn off music", "enough music"
        ]):
            return self._stop()

        # ── Play request ──
        query = self._extract_query(text)
        if not query:
            return "What song would you like me to play boss?"

        # Run in background thread so FRIDAY stays responsive
        thread = threading.Thread(
            target=self._play_song,
            args=(query,),
            daemon=True
        )
        thread.start()

        return f"Finding and playing {query} for you boss. One moment."

    # ── Internal playback ──────────────────────────────────────────────────────

    def _play_song(self, query: str):
        """Search YouTube, get stream URL, play with VLC."""
        try:
            logger.info(f"Searching YouTube for: {query}")

            # yt-dlp options — audio only, no download, best quality
            ydl_opts = {
                "format":           "bestaudio/best",
                "quiet":            True,
                "no_warnings":      True,
                "extract_flat":     False,
                "noplaylist":       True,
                "default_search":   "ytsearch1:",  # search top 1 result
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)

                # Pull first result from search
                if "entries" in info:
                    info = info["entries"][0]

                # Get the best audio URL
                stream_url = None
                if "url" in info:
                    stream_url = info["url"]
                else:
                    # Find best audio format
                    for fmt in info.get("formats", []):
                        if fmt.get("acodec") != "none":
                            stream_url = fmt["url"]
                            break

                if not stream_url:
                    logger.error("No stream URL found")
                    return

                title = info.get("title", query)
                logger.success(f"Found: {title}")
                MusicSkill._current_song = title

            # ── Play with VLC ──
            if MusicSkill._vlc_instance is None:
                MusicSkill._vlc_instance = vlc.Instance(
                    "--no-xlib",
                    "--quiet",
                    "--no-video"      # audio only
                )

            # Stop anything currently playing
            if MusicSkill._vlc_player:
                MusicSkill._vlc_player.stop()

            MusicSkill._vlc_player = MusicSkill._vlc_instance.media_player_new()
            media = MusicSkill._vlc_instance.media_new(stream_url)
            MusicSkill._vlc_player.set_media(media)
            MusicSkill._vlc_player.play()
            MusicSkill._is_playing = True

            logger.success(f"Now playing: {title}")

            # Announce what's playing via FRIDAY's voice
            from voice.speaker import speak
            from ui.window import signals
            signals.friday_replied.emit(f"♪ Now playing — {title}")
            speak(f"Now playing {title} boss.")

        except Exception as e:
            logger.error(f"Music playback error: {e}")
            from voice.speaker import speak
            speak("I had trouble playing that song boss. Try again.")

    def _pause(self) -> str:
        if MusicSkill._vlc_player and MusicSkill._is_playing:
            MusicSkill._vlc_player.pause()
            MusicSkill._is_playing = False
            return "Music paused boss."
        return "Nothing is playing right now boss."

    def _resume(self) -> str:
        if MusicSkill._vlc_player and not MusicSkill._is_playing:
            MusicSkill._vlc_player.play()
            MusicSkill._is_playing = True
            return "Resuming music boss."
        return "Nothing is paused boss."

    def _stop(self) -> str:
        if MusicSkill._vlc_player:
            MusicSkill._vlc_player.stop()
            MusicSkill._is_playing = False
            MusicSkill._current_song = None
            return "Music stopped boss."
        return "Nothing is playing boss."

    # ── Helper ────────────────────────────────────────────────────────────────

    def _extract_query(self, text: str) -> str:
        """Extract song name from what the user said."""
        removals = [
            "can you play", "i want to listen to", "put on some",
            "play the song called", "play the song", "play song",
            "play some music", "play music", "play some", "put on",
            "play", "for me", "please", "music", "song",
            "on spotify", "on youtube", "right now"
        ]
        query = text
        for phrase in sorted(removals, key=len, reverse=True):
            query = query.replace(phrase, "").strip()

        return query.strip()