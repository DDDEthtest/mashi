from PIL import Image


#Layers
LAYER_ORDER = [
    "background",
    "hair_back",
    "cape",
    "bottom",
    "upper",
    "head",
    "eyes",
    "hair_front",
    "hat",
    "left_accessory",
    "right_accessory",
]

#Images
DEFAULT_PNG_WIDTH = 552 * 2
DEFAULT_PNG_HEIGHT = 736 * 2
DEFAULT_TRAIT_WIDTH = 380 * 2
DEFAULT_TRAIT_HEIGHT = 600 * 2

#Other Config
ANIM_STEP = 0.06
MAX_GENERATIONS = 20
RESAMPLE_MODE = Image.Resampling.LANCZOS