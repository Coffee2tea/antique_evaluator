import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
# Try to get API key from Streamlit secrets first, then fallback to environment variables
OPENAI_API_KEY = None
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    print(f"✅ Loaded API key from Streamlit secrets: {OPENAI_API_KEY[:10]}..." if OPENAI_API_KEY else "❌ API key from secrets is empty")
except (KeyError, FileNotFoundError, AttributeError) as e:
    print(f"⚠️ Could not load from Streamlit secrets ({type(e).__name__}), trying environment variables...")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    print(f"✅ Loaded API key from environment: {OPENAI_API_KEY[:10]}..." if OPENAI_API_KEY else "❌ No API key found in environment")
except Exception as e:
    print(f"❌ Unexpected error loading secrets: {e}")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"🔑 Final API key status: {'✅ Available' if OPENAI_API_KEY else '❌ Not found'}")

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