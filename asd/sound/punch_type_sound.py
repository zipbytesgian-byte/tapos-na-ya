import atexit
import os
import sys
import wave        # CHANGE 1: lets us read and write .wav files (built into Python)
import array       # CHANGE 1: lets us treat the raw audio as a list of numbers
import tempfile    # CHANGE 1: gives us the temp folder to save the quieter copy

try:
    import winsound
except ImportError:              # hindi Windows
    winsound = None

# Walang kailangang i-install. MCI ay built-in sa Windows at kaya
# ang maraming sound nang sabay, kaya hindi napuputol ang music.
_winmm = None
if sys.platform.startswith("win"):
    try:
        import ctypes
        _winmm = ctypes.windll.winmm
    except Exception:
        _winmm = None

HAS_MCI = _winmm is not None

SOUND_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- SETTINGS (puwede ninyong baguhin) ----------------
SFX_ENABLED = True       # False = walang sound effects
MUSIC_ENABLED = True     # False = walang background music
MUSIC_FILE = "Energizing Game.wav"

# CHANGE 2: This is the music volume setting. Change this number to make the
# music louder or quieter. 1.0 = original loudness, 0.5 = half, 0.1 = very quiet.
# (You already had this line, but nothing used it until now.)
MUSIC_VOLUME = 0.3

# pangalan -> (filename, volume 0.0-1.0)
SFX = {
    # laban
    "bell":          ("bell.wav", 1.0),
    "punch":         ("punch.wav", 1.0),
    "crit":          ("crit.wav", 1.0),
    "ult":           ("ult.wav", 1.0),              # Twin Punch
    "ult_berserk":   ("ult_berserk.wav", 1.0),
    "ult_bloodlust": ("ult_bloodlust.wav", 1.0),
    "ult_lava":      ("ult_lava.wav", 1.0),
    "hurt":          ("hurt.wav", 1.0),
    "roar":          ("roar.wav", 0.9),             # kapag galit na ang kalaban
    "tick":          ("tick.wav", 0.6),             # paubos na ang oras
    "ko_win":        ("ko_win.wav", 1.0),
    "ko_lose":       ("ko_lose.wav", 1.0),
    # menu at shop
    "move":          ("move.wav", 0.6),
    "select":        ("select.wav", 0.7),
    "back":          ("back.wav", 0.7),
    "buy":           ("buy.wav", 0.9),
    "denied":        ("denied.wav", 0.8),
    "cheat":         ("cheat.wav", 1.0),
}

# Ang mga ito ay tumutunog lang kapag gumagana ang MCI. Kapag winsound lang
# ang magagamit, puputulin nila ang background music, kaya nilalaktawan.
MCI_ONLY = {"move", "select", "back", "buy", "denied", "cheat", "tick", "roar"}

_aliases = {}            # name -> MCI alias (o None kapag hindi nabuksan)
_music_on = False


def _mci(command):
    if _winmm is None:
        return -1
    try:
        return _winmm.mciSendStringW(command, None, 0, None)
    except Exception:
        return -1


def _open(name):
    """Buksan ang sound sa MCI isang beses lang, tapos gamitin ulit."""
    if name in _aliases:
        return _aliases[name]
    alias = None
    entry = SFX.get(name)
    if entry and HAS_MCI:
        path = os.path.join(SOUND_DIR, entry[0])
        if os.path.exists(path):
            a = "sfx_" + name
            _mci("close " + a)
            if _mci('open "%s" type waveaudio alias %s' % (path, a)) == 0:
                _mci("setaudio %s volume to %d" % (a, int(entry[1] * 1000)))  # kung hindi suportado, okay lang
                alias = a
    _aliases[name] = alias
    return alias


def preload():
    """I-load na lahat ng sound sa simula para walang delay sa unang tunog."""
    if HAS_MCI and SFX_ENABLED:
        for name in SFX:
            _open(name)


def _close_all():
    if HAS_MCI:
        _mci("close all")


atexit.register(_close_all)


# CHANGE 3: NEW FUNCTION. winsound (which plays the music) has no volume
# control, so instead we make a quieter copy of the music file and play that.
# How it works: a .wav file is just a long list of numbers (the sound wave).
# Multiplying every number by MUSIC_VOLUME (for example 0.3) makes the whole
# thing quieter. The copy is saved in your temp folder, so your original
# "Energizing Game.wav" is never changed.
def _quiet_copy(path, volume):
    """Gumawa ng mas mahinang kopya ng wav at ibalik ang path nito."""
    # The volume is part of the file name (for example ..._30.wav for 0.3).
    # So when you change MUSIC_VOLUME, a new copy is made automatically and
    # you never need to delete anything by hand.
    out = os.path.join(tempfile.gettempdir(),
                       "punch_type_music_%d.wav" % int(volume * 100))
    if os.path.exists(out):
        return out                       # already made before, so reuse it
    try:
        with wave.open(path, "rb") as src:
            params = src.getparams()
            if src.getsampwidth() != 2:  # only 16-bit wavs are supported
                return path              # otherwise play the original
            frames = src.readframes(src.getnframes())
        samples = array.array("h")       # "h" = 16-bit numbers
        samples.frombytes(frames)
        # multiply every sample by the volume to make it quieter
        quiet = array.array("h", (int(s * volume) for s in samples))
        with wave.open(out, "wb") as dst:
            dst.setparams(params)
            dst.writeframes(quiet.tobytes())
        return out
    except Exception:
        return path                      # if anything goes wrong, play the original


def play_music():
    global _music_on
    if not MUSIC_ENABLED or _music_on:
        return              # tuloy lang ang music, huwag i-restart
    path = os.path.join(SOUND_DIR, MUSIC_FILE)
    if winsound and os.path.exists(path):
        # CHANGE 4: this is the line that actually lowers the volume. It swaps
        # the original music file for the quieter copy before playing it.
        # Before this change, the original (loud) file was played directly.
        path = _quiet_copy(path, MUSIC_VOLUME)
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        _music_on = True


def stop_music():
    global _music_on
    if winsound:
        winsound.PlaySound(None, winsound.SND_PURGE)
    _music_on = False


def play_sfx(name):
    if not SFX_ENABLED:
        return
    entry = SFX.get(name)
    if not entry:
        return
    if HAS_MCI:
        alias = _open(name)
        if alias:
            _mci("play %s from 0" % alias)
            return
    # Wala o hindi gumana ang MCI: winsound na lang (isang sound lang sabay)
    if winsound is None or name in MCI_ONLY:
        return
    path = os.path.join(SOUND_DIR, entry[0])
    if not os.path.exists(path):
        return              # kapag walang file, hindi magka-crash ang game
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except RuntimeError:
        pass

preload()

if __name__ == "__main__":
    print("HAS_MCI:", HAS_MCI)
    for n in SFX:
        print(f"{n:15}", "OK" if _aliases.get(n) else "FAILED")
