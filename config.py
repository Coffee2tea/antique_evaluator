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

# Language configurations
LANGUAGES = {
    "中文": {
        "code": "zh",
        "name": "中文",
        "flag": "🇨🇳"
    },
    "English": {
        "code": "en", 
        "name": "English",
        "flag": "🇺🇸"
    }
}

# Text translations
TEXTS = {
    "zh": {
        # Header
        "app_title": "🏺 AI古董鉴定专家",
        "app_subtitle": "基于最新AI技术的智能古董鉴定与真伪分析平台",
        
        # Usage instructions
        "usage_title": "📋 使用说明",
        "usage_steps": """**📝 使用步骤：**
1. 上传古董图片（支持JPG、PNG、WEBP格式）
2. 输入古董描述信息（可选）
3. 点击评估按钮
4. 等待最新AI模型分析结果

**💡 专业建议：**
- 上传多角度的清晰图片
- 包含底部、侧面、细节特写
- 图片大小不超过10MB""",
        
        "supported_formats": """**📁 支持格式：**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WEBP (.webp)

**🎯 AI功能：**
- 真伪鉴定分析
- 年代估测
- 材质识别
- 价值评估""",
        
        # Upload section
        "upload_title": "上传古董图片开始鉴定",
        "upload_subtitle": "请上传您的古董照片",
        "upload_description": "支持多张图片同时上传，建议包含不同角度的照片",
        "upload_tips": ["💡 正面照", "💡 背面照", "💡 细节特写", "💡 底部标记"],
        
        # Input fields
        "info_title": "📝 古董信息描述",
        "info_subtitle": "(更多详细背景信息能为鉴定带来更好的效果)",
        "name_label": "🏷️ 古董名称/标题 (可选):",
        "name_placeholder": "例如：清代康熙青花瓷碗、汉代玉璧、明代铜镜等",
        "description_label": "📄 古董描述信息 (可选):",
        "description_placeholder": "请输入古董的详细描述，如：\n- 年代/朝代\n- 材质（陶瓷、玉石、金属等）\n- 尺寸大小\n- 制作工艺",
        "period_label": "📅 估计年代:",
        "period_placeholder": "例如：清代、民国、宋代等",
        "material_label": "🔍 估计材质:",
        "material_placeholder": "例如：青花瓷、和田玉、青铜等",
        "acquisition_label": "📍 获得方式:",
        "acquisition_placeholder": "例如：家传、拍卖购买、古玩市场等",
        
        # Buttons
        "evaluate_btn": "🔍 开始古董鉴定",
        "reset_btn": "🔄 重新开始",
        "example1_btn": "🏺 试用例子1",
        "example2_btn": "🏛️ 试用例子2",
        
        # Results
        "result_title": "🎯 最终鉴定结果",
        "report_title": "📋 专业古董鉴定详细报告",
        "high_confidence": "🟢 **高可信度**: 这件古董很可能是真品",
        "medium_confidence": "🟡 **中等可信度**: 需要进一步专业鉴定", 
        "low_confidence": "🟠 **较低可信度**: 存在疑点，建议谨慎",
        "very_low_confidence": "🔴 **低可信度**: 可能是仿制品或现代制品",
        
        # Report
        "report_main_title": "🏺 古董文物鉴定报告",
        "report_subtitle": "AI 智能分析评估",
        "conclusion_title": "🏆 鉴定结论",
        "suggestion_title": "💡 专业建议",
        "disclaimer": "⚠️ 重要声明: 本报告基于AI深度学习分析生成，仅供专业参考。最终鉴定结果需结合实物检测，建议咨询权威古董鉴定机构进行确认。"
    },
    
    "en": {
        # Header
        "app_title": "🏺 AI Antique Expert",
        "app_subtitle": "Professional antique authentication and analysis platform powered by advanced AI technology",
        
        # Usage instructions
        "usage_title": "📋 Instructions",
        "usage_steps": """**📝 How to Use:**
1. Upload antique photos (supports JPG, PNG, WEBP formats)
2. Enter antique description (optional)
3. Click evaluate button
4. Wait for AI analysis results

**💡 Professional Tips:**
- Upload clear photos from multiple angles
- Include front, back, detail close-ups
- Image size should not exceed 10MB""",
        
        "supported_formats": """**📁 Supported Formats:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WEBP (.webp)

**🎯 AI Features:**
- Authenticity analysis
- Period estimation
- Material identification
- Value assessment""",
        
        # Upload section
        "upload_title": "Upload Antique Photos to Start Authentication",
        "upload_subtitle": "Please upload your antique photos",
        "upload_description": "Support multiple image uploads, recommend including photos from different angles",
        "upload_tips": ["💡 Front view", "💡 Back view", "💡 Detail shots", "💡 Base marks"],
        
        # Input fields
        "info_title": "📝 Antique Information",
        "info_subtitle": "(More detailed background information leads to better authentication results)",
        "name_label": "🏷️ Antique Name/Title (Optional):",
        "name_placeholder": "e.g.: Qing Dynasty Kangxi Blue and White Bowl, Han Dynasty Jade Disc, Ming Mirror, etc.",
        "description_label": "📄 Antique Description (Optional):",
        "description_placeholder": "Please enter detailed description such as:\n- Period/Dynasty\n- Material (ceramic, jade, metal, etc.)\n- Size dimensions\n- Craftsmanship",
        "period_label": "📅 Estimated Period:",
        "period_placeholder": "e.g.: Qing Dynasty, Republic Period, Song Dynasty, etc.",
        "material_label": "🔍 Estimated Material:",
        "material_placeholder": "e.g.: Blue and white porcelain, Hetian jade, bronze, etc.",
        "acquisition_label": "📍 How Acquired:",
        "acquisition_placeholder": "e.g.: Family heirloom, auction purchase, antique market, etc.",
        
        # Buttons
        "evaluate_btn": "🔍 Start Authentication",
        "reset_btn": "🔄 Start Over",
        "example1_btn": "🏺 Try Example 1",
        "example2_btn": "🏛️ Try Example 2",
        
        # Results
        "result_title": "🎯 Final Authentication Results",
        "report_title": "📋 Professional Antique Authentication Report",
        "high_confidence": "🟢 **High Confidence**: This antique is very likely authentic",
        "medium_confidence": "🟡 **Medium Confidence**: Further professional authentication needed",
        "low_confidence": "🟠 **Low Confidence**: There are concerns, proceed with caution",
        "very_low_confidence": "🔴 **Very Low Confidence**: Likely reproduction or modern piece",
        
        # Report
        "report_main_title": "🏺 Antique Authentication Report",
        "report_subtitle": "AI Intelligent Analysis & Assessment",
        "conclusion_title": "🏆 Authentication Conclusion",
        "suggestion_title": "💡 Professional Recommendations",
        "disclaimer": "⚠️ Important Notice: This report is generated by AI deep learning analysis for professional reference only. Final authentication results should be combined with physical examination. We recommend consulting authoritative antique authentication institutions for confirmation."
    }
} 