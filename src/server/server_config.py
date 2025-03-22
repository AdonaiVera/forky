""" Configuration for the server. """

from fastapi.templating import Jinja2Templates

MAX_DISPLAY_SIZE: int = 300_000
DELETE_REPO_AFTER: int = 60 * 60  # In seconds


EXAMPLE_REPOS: list[dict[str, str]] = [
    {"name": "Supervision", "url": "https://github.com/roboflow/supervision"},
    {"name": "FiftyOne", "url": "https://github.com/voxel51/fiftyone"},
    {"name": "Keras", "url": "https://github.com/keras-team/keras"},
    {"name": "Smol Models", "url": "https://github.com/huggingface/smollm"},
    {"name": "VisionAgent", "url": " https://github.com/landing-ai/vision-agent"},



]

templates = Jinja2Templates(directory="server/templates")
