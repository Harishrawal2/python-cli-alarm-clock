import sys
import time


class AlarmSoundPlayer:
    SOUND_PATTERNS = {
        "normal": ("SystemExclamation", [(1000, 350)]),
        "fast": ("SystemAsterisk", [(1200, 160), (900, 160)]),
        "long": ("SystemHand", [(750, 800)]),
        "silent": ("", []),
    }

    def play(self, sound_style: str):
        sound_alias, beep_pattern = self.SOUND_PATTERNS[sound_style]

        if not beep_pattern:
            time.sleep(0.5)
            return

        try:
            import winsound

            winsound.PlaySound(sound_alias, winsound.SND_ALIAS)
            for frequency, duration in beep_pattern:
                winsound.Beep(frequency, duration)
        except (ImportError, RuntimeError):
            for _, duration in beep_pattern:
                print("\a", end="")
                sys.stdout.flush()
                time.sleep(duration / 1000)
