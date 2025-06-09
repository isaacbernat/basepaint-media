LATEST = 601
BATCH_SIZE = 100
CREATE_COVER = False
INCLUDE_VIDEO = False
INCLUDE_DESCRIPTION = False
EXCLUDE_IMAGES = False
INCLUDE_DESCRIPTION_IMAGE = False
INCLUDE_DESCRIPTION_IMAGE_GRID = False
ARCHIVE_VERSION = "0.3.0"
GOOGLE_API_KEY = "Replace with a valid Gemini API key in your GitHub repo secrets or locally"
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"  #  [m for m in genai.list_models()] to check other available models
GEMINI_SLEEP = [10, 55]  # avoid exceeding 10 RPM quota https://ai.google.dev/gemini-api/docs/rate-limits
# Gemini usage metrics available at https://aistudio.google.com/app/usage
