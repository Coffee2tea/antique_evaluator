import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Load from environment or .env file

# App Configuration
APP_TITLE = "🏺 AI古董鉴定专家"
APP_DESCRIPTION = "基于最新AI技术的智能古董鉴定与真伪分析平台 - 运用先进推理技术提供专业评估"

# GPT Model Configuration
GPT_MODEL = "o3"  # GPT-o3 model for advanced reasoning capabilities
MAX_TOKENS = 4096  # Will be used as max_completion_tokens for o3
TEMPERATURE = 0.3

# Image processing
MAX_IMAGE_SIZE = (1024, 1024)
SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'webp'] 