"""PolyScribe 核心常量。"""

SCHEMA_VERSION = "0.1.0"

WORKFLOWS = ("separation", "muscriptor", "game", "basic_pitch")
TARGETS = ("piano", "vocal", "harmony", "chords")

DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 2

MUSCRIPTOR_CHORD_PREFIX = "muscriptor:chord="
MUSCRIPTOR_MODEL = "medium"
GAME_LANGUAGE = "zh"
GAME_RELEASE_TAG = "v1.0.0"
GAME_WEIGHTS_ARCHIVE = "GAME-1.0-medium.zip"
GAME_WEIGHTS_URL = (
    "https://github.com/openvpi/GAME/releases/download/"
    f"{GAME_RELEASE_TAG}/{GAME_WEIGHTS_ARCHIVE}"
)
GAME_REPO_URL = "https://github.com/openvpi/GAME.git"

VOCAL_SEP_MODEL = "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt"
KARAOKE_SEP_MODEL = "UVR_MDXNET_KARA_2.onnx"

PIANO_NAME_ALIASES = (
    "acoustic_piano",
    "acoustic piano",
    "grand_piano",
    "grand piano",
    "bright_acoustic_piano",
    "piano",
)
# GM 原声钢琴族：0 Acoustic Grand, 1 Bright Acoustic, 2 Electric Grand
PIANO_PROGRAMS = frozenset({0, 1, 2})
