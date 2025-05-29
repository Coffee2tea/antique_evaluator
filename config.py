import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
# Try to get API key from Streamlit secrets first, then fallback to environment variables
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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