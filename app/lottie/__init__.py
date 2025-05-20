# Lottie generator module initialization

__all__ = [
    "IImageProcessor",
    "ISVGParser",
    "ILottieGenerator",
    "OpenCVImageProcessor",
    "SVGElementsParser",
    "LottieGenerator",
    "ManualLottieGenerator",
    "LottieGeneratorFacade",
]

from app.lottie.interfaces import IImageProcessor, ISVGParser, ILottieGenerator
from app.lottie.image_processor import OpenCVImageProcessor
from app.lottie.svg_parser import SVGElementsParser
from app.lottie.lottie_generator import LottieGenerator, ManualLottieGenerator
from app.lottie.facade import LottieGeneratorFacade

# Export the facade for simplified API access
__all__ = ["LottieGeneratorFacade"]
