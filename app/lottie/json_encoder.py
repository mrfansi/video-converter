import json
from typing import Any

class LottieJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for Lottie animations that handles non-serializable objects
    """
    def default(self, obj: Any) -> Any:
        # Handle methods and other non-serializable types
        if callable(obj):
            return str(obj)
        # Handle other special types if needed
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)
