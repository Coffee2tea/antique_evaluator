import streamlit as st
from evaluator import AntiqueEvaluator
from config import APP_TITLE, APP_DESCRIPTION, LANGUAGES, TEXTS
import logging
import time
import base64
from PIL import Image
import io
import os
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_text(key: str, lang: str = "en") -> str:
    """Get translated text based on language"""
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))

def create_language_selector():
    """Create language selection sidebar"""
    with st.sidebar:
        st.markdown("### 🌐 Language / 语言")
        
        # Initialize language in session state - now defaults to English
        if "language" not in st.session_state:
            st.session_state.language = "en"
        
        # Language selector
        selected_lang_name = st.selectbox(
            "Select Language:",
            options=list(LANGUAGES.keys()),
            index=1 if st.session_state.language == "en" else 0,
            format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}"
        )
        
        # Update session state when language changes
        new_lang = LANGUAGES[selected_lang_name]["code"]
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()
        
        return st.session_state.language

def create_authenticity_progress_bar(score: int, language: str = "en") -> str:
    """Create a colored progress bar for authenticity score"""
    # Calculate color from red to green based on score
    red_component = max(0, 255 - int(score * 2.55))
    green_component = min(255, int(score * 2.55))
    
    color = f"rgb({red_component}, {green_component}, 0)"
    
    # Language-specific text
    authenticity_text = "真品可能性" if language == "zh" else "Authenticity Likelihood"
    
    progress_html = f"""
    <div style="
        width: 100%;
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 3px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="
            width: {score}%;
            background-color: {color};
            height: 30px;
            border-radius: 7px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 16px;
            transition: width 0.5s ease-in-out;
        ">
            {authenticity_text}: {score}%
        </div>
    </div>
    """
    return progress_html

def encode_image_file_path(file_path: str) -> str:
    """Convert image file path to base64 data URL for OpenAI API"""
    try:
        # Read the file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        logger.info(f"Read {len(file_content)} bytes from {file_path}")
        
        # Encode to base64
        encoded_image = base64.b64encode(file_content).decode('utf-8')
        logger.info(f"Encoded image to base64, length: {len(encoded_image)}")
        
        # Determine the image format based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == '.png':
            mime_type = 'image/png'
        elif file_ext == '.webp':
            mime_type = 'image/webp'
        else:
            mime_type = 'image/jpeg'  # Default
        
        data_url = f"data:{mime_type};base64,{encoded_image}"
        logger.info(f"Created data URL with mime type: {mime_type}, total length: {len(data_url)}")
        
        return data_url
        
    except Exception as e:
        logger.error(f"Failed to encode image file {file_path}: {e}")
        return None

def encode_uploaded_image(uploaded_file) -> str:
    """Convert uploaded file to base64 data URL for OpenAI API"""
    try:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Read the file content
        file_content = uploaded_file.read()
        logger.info(f"Read {len(file_content)} bytes from {uploaded_file.name}")
        
        # Reset file pointer again for other uses
        uploaded_file.seek(0)
        
        # Encode to base64
        encoded_image = base64.b64encode(file_content).decode('utf-8')
        logger.info(f"Encoded image to base64, length: {len(encoded_image)}")
        
        # Determine the image format based on file type
        file_type = uploaded_file.type
        if 'jpeg' in file_type or 'jpg' in file_type:
            mime_type = 'image/jpeg'
        elif 'png' in file_type:
            mime_type = 'image/png'
        elif 'webp' in file_type:
            mime_type = 'image/webp'
        else:
            mime_type = 'image/jpeg'  # Default
        
        data_url = f"data:{mime_type};base64,{encoded_image}"
        logger.info(f"Created data URL with mime type: {mime_type}, total length: {len(data_url)}")
        
        return data_url
        
    except Exception as e:
        logger.error(f"Failed to encode uploaded image: {e}")
        return None

def format_evaluation_report(report_text: str) -> str:
    """Format the evaluation report with simple, clean, professional styling"""
    if not report_text:
        return ""
    
    # Split the report into sections for better formatting
    lines = report_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('<div class="report-spacer"></div>')
            continue
            
        # Detect major section headers (第一步, 第二步, etc.)
        if any(keyword in line for keyword in ['第一步', '第二步', '第三步', '第四步', '第五步']):
            formatted_lines.append(f'<h2 class="report-section-header">{line}</h2>')
        
        # Detect main category headers
        elif any(keyword in line for keyword in ['基础信息识别', '工艺技术分析', '真伪综合判断', '市场价值评估', '综合结论', '最终建议', '总结评估']):
            formatted_lines.append(f'<h3 class="report-category-header">{line}</h3>')
        
        # Detect elegant subtitles with brackets 【】or special keywords
        elif ('【' in line and '】' in line) or any(keyword in line for keyword in ['图像观察', '工艺分析', '材质检测', '时代特征', '真伪判断', '市场评估', '投资建议', '保存建议', '收藏价值']):
            formatted_lines.append(f'<h4 class="report-subtitle">{line}</h4>')
        
        # Detect key-value pairs or labeled information
        elif ':' in line and len(line.split(':')[0]) < 20:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().replace('**', '')
                value = parts[1].strip()
                formatted_lines.append(f'<div class="report-info-item"><span class="report-label">{key}:</span> <span class="report-value">{value}</span></div>')
            else:
                formatted_lines.append(f'<p class="report-paragraph">{line}</p>')
        
        # Detect numbered points or bullet points
        elif line.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-', '⚠️', '✅', '❌', '💡', '🔍')):
            formatted_lines.append(f'<div class="report-list-item">{line}</div>')
        
        # Detect score/rating lines
        elif any(keyword in line.lower() for keyword in ['可信度', '评分', '分数', '%', '星级']):
            formatted_lines.append(f'<div class="report-score-item">{line}</div>')
        
        # Regular paragraph
        else:
            formatted_lines.append(f'<p class="report-paragraph">{line}</p>')
    
    # Create clean, simple report layout
    formatted_content = '\n'.join(formatted_lines)
    
    return f"""
    <div class="clean-report">
        <div class="report-header-section">
            <h1 class="report-main-title">📋 专业古董鉴定分析报告</h1>
            <p class="report-subtitle-line">基于最先进多模态多专家思维链AI模型</p>
        </div>
        <div class="report-content-section">
            {formatted_content}
        </div>
        <div class="report-footer-section">
            <p class="report-disclaimer">⚠️ 本报告仅供参考，最终鉴定结果需结合实物检测。建议咨询专业古董鉴定机构进行确认。</p>
        </div>
    </div>
    """

def load_example_data(example_folder: str):
    """Load example antique data from the specified folder"""
    try:
        # Load text information
        info_file = os.path.join(example_folder, "info.txt")
        title = ""
        description = ""
        estimated_period = ""
        estimated_material = ""
        acquisition_info = ""
        
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('title:'):
                        title = line.replace('title:', '').strip()
                    elif line.startswith('description:'):
                        description = line.replace('description:', '').strip()
                    elif line.startswith('estimated_period:'):
                        estimated_period = line.replace('estimated_period:', '').strip()
                    elif line.startswith('estimated_material:'):
                        estimated_material = line.replace('estimated_material:', '').strip()
                    elif line.startswith('acquisition_info:'):
                        acquisition_info = line.replace('acquisition_info:', '').strip()
        
        # Load image files
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
        image_files = []
        
        # Use a set to avoid duplicates
        unique_image_files = set()
        
        for ext in image_extensions:
            # Search for lowercase extensions
            found_files = glob.glob(os.path.join(example_folder, ext))
            unique_image_files.update(found_files)
            
            # Search for uppercase extensions
            found_files = glob.glob(os.path.join(example_folder, ext.upper()))
            unique_image_files.update(found_files)
        
        # Convert set back to list and sort for consistent ordering
        image_files = sorted(list(unique_image_files))
        
        return title, description, estimated_period, estimated_material, acquisition_info, image_files
        
    except Exception as e:
        logger.error(f"Failed to load example data from {example_folder}: {e}")
        return "", "", "", "", "", []

def load_example_into_session(example_num: int):
    """Load example data into session state"""
    example_folder = f"example{example_num}"
    title, description, estimated_period, estimated_material, acquisition_info, image_files = load_example_data(example_folder)
    
    # Store in session state
    st.session_state.example_title = title
    st.session_state.example_description = description
    st.session_state.example_estimated_period = estimated_period
    st.session_state.example_estimated_material = estimated_material
    st.session_state.example_acquisition_info = acquisition_info
    st.session_state.example_images = image_files
    st.session_state.example_loaded = example_num
    
    # Trigger app reset to update UI
    st.session_state.reset_trigger = not st.session_state.reset_trigger

def main():
    # Initialize session state for reset functionality
    if "reset_trigger" not in st.session_state:
        st.session_state.reset_trigger = False
    
    # Add language selector and get current language
    current_lang = create_language_selector()
    
    # Reset function
    def reset_app():
        """Reset all form inputs and uploaded files"""
        st.session_state.reset_trigger = not st.session_state.reset_trigger
        # Clear file uploader
        if "uploaded_files" in st.session_state:
            del st.session_state.uploaded_files
        # Clear all text inputs
        for key in list(st.session_state.keys()):
            if key.startswith(("manual_title", "manual_description", "estimated_period", "estimated_material", "acquisition_info")):
                del st.session_state[key]
        # Clear example data
        if hasattr(st.session_state, 'example_title'):
            del st.session_state.example_title
        if hasattr(st.session_state, 'example_description'):
            del st.session_state.example_description
        if hasattr(st.session_state, 'example_estimated_period'):
            del st.session_state.example_estimated_period
        if hasattr(st.session_state, 'example_estimated_material'):
            del st.session_state.example_estimated_material
        if hasattr(st.session_state, 'example_acquisition_info'):
            del st.session_state.example_acquisition_info
        if hasattr(st.session_state, 'example_images'):
            del st.session_state.example_images
        if hasattr(st.session_state, 'example_loaded'):
            del st.session_state.example_loaded
        st.rerun()
    
    # Header with elegant, bright design - now using dynamic text
    st.markdown(f"""
    <div style='text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; border-radius: 20px; margin-bottom: 2.5rem; box-shadow: 0 8px 32px rgba(0,0,0,0.2); position: relative; overflow: hidden;'>
        <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);'></div>
        <h1 style='margin: 0; font-size: 2.8rem; font-weight: 600; font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif; letter-spacing: -0.02em; position: relative; z-index: 1; color: #ffffff; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{get_text("app_title", current_lang)}</h1>
        <p style='margin: 1rem 0 0 0; font-size: 1.1rem; font-weight: 400; color: rgba(255,255,255,0.9); opacity: 0.95; position: relative; z-index: 1;'>{get_text("app_subtitle", current_lang)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced CSS styling with improved contrast
    st.markdown("""
    <style>
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .section-header {
        background: linear-gradient(90deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        border-left: 4px solid #495057;
        margin: 2.5rem 0 1.5rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(73, 80, 87, 0.1);
    }
    
    .section-header h3 {
        margin: 0;
        color: #212529;
        font-weight: 600;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: -0.01em;
    }
    
    .upload-area {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border: 2px dashed #6c757d;
        border-radius: 20px;
        padding: 3rem;
        margin: 1.5rem 0;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    .upload-area:hover {
        border-color: #495057;
        background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
        color: #ffffff !important;
        border-radius: 18px;
        border: none;
        padding: 1.5rem 3.5rem;
        font-size: 1.8rem;
        font-weight: 700;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        cursor: pointer;
        width: 100%;
        box-shadow: 0 8px 25px rgba(74, 85, 104, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.02em;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        border: 2px solid transparent;
        min-height: 3.5rem;
    }
    
    .stButton > button * {
        color: #ffffff !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 35px rgba(74, 85, 104, 0.6);
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        color: #ffffff !important;
        text-shadow: 0 3px 8px rgba(0,0,0,0.6);
    }
    
    .stButton > button:hover * {
        color: #ffffff !important;
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
        color: #ffffff !important;
    }
    
    .stButton > button:active * {
        color: #ffffff !important;
    }
    
    .stButton > button:focus {
        color: #ffffff !important;
        outline: none;
        box-shadow: 0 0 0 3px rgba(74, 85, 104, 0.3);
    }
    
    .stButton > button:focus * {
        color: #ffffff !important;
    }
    
    .info-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 6px 25px rgba(0,0,0,0.1);
        border: 1px solid rgba(73, 80, 87, 0.15);
        backdrop-filter: blur(10px);
    }
    
    .image-preview {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(73, 80, 87, 0.1);
    }
    
    .image-preview:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.2);
    }
    
    .footer-section {
        background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 20px;
        padding: 3rem 2rem;
        margin-top: 4rem;
        text-align: center;
        border: 1px solid rgba(73, 80, 87, 0.15);
        box-shadow: 0 6px 25px rgba(0,0,0,0.1);
    }
    
    /* Custom styling for info and success boxes with better contrast */
    .stAlert > div {
        border-radius: 16px;
        border: 1px solid rgba(73, 80, 87, 0.1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .stAlert[data-baseweb="notification"] {
        border-radius: 16px;
    }
    
    /* Enhanced info box styling */
    .stAlert[data-baseweb="notification"][kind="info"] {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        color: #003d80;
    }
    
    .stAlert[data-baseweb="notification"][kind="success"] {
        background-color: #e8f5e8;
        border-left: 4px solid #28a745;
        color: #155724;
    }
    
    /* Input field styling with better contrast */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #ced4da;
        padding: 0.75rem 1rem;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        transition: all 0.3s ease;
        background-color: #ffffff;
        color: #212529;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #495057;
        box-shadow: 0 0 0 3px rgba(73, 80, 87, 0.15);
        outline: none;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #ced4da;
        padding: 0.75rem 1rem;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        transition: all 0.3s ease;
        background-color: #ffffff;
        color: #212529;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #495057;
        box-shadow: 0 0 0 3px rgba(73, 80, 87, 0.15);
        outline: none;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #495057 0%, #343a40 100%);
        border-radius: 10px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        border-radius: 12px;
        background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid rgba(73, 80, 87, 0.1);
    }
    
    /* Global typography improvements with better contrast */
    h1, h2, h3, h4, h5, h6 {
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        color: #212529;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    
    p, div, span, li {
        font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif;
        color: #212529;
        line-height: 1.6;
    }
    
    /* Streamlit specific text styling */
    .stMarkdown p {
        color: #212529;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #212529;
    }
    
    /* Labels and captions */
    .stTextInput label, .stTextArea label, .stFileUploader label {
        color: #495057;
        font-weight: 500;
    }
    
    /* File uploader text */
    .stFileUploader > div > div > div > div {
        color: #495057;
    }
    
    /* Subtle animation for cards */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .info-card, .section-header {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Upload prompt section styling */
    .upload-prompt-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin: 2.5rem 0 1.5rem 0;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .upload-prompt-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
        pointer-events: none;
    }
    
    .upload-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        display: block;
        position: relative;
        z-index: 1;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
    }
    
    .upload-title {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin: 1rem 0 !important;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .upload-description {
        color: rgba(255, 255, 255, 0.95) !important;
        font-size: 1.1rem !important;
        margin: 1.5rem 0 !important;
        position: relative;
        z-index: 1;
        line-height: 1.6 !important;
    }
    
    .upload-description strong {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    .upload-tips {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 1.5rem;
        position: relative;
        z-index: 1;
    }
    
    .tip-item {
        background: rgba(255, 255, 255, 0.15);
        color: #ffffff !important;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .tip-item:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Upload prompt responsive design */
    @media (max-width: 768px) {
        .upload-prompt-section {
            padding: 2rem 1.5rem;
            margin: 2rem 0 1rem 0;
        }
        
        .upload-icon {
            font-size: 2.8rem;
        }
        
        .upload-title {
            font-size: 1.5rem !important;
        }
        
        .upload-description {
            font-size: 1rem !important;
        }
        
        .upload-tips {
            gap: 0.75rem;
        }
        
        .tip-item {
            font-size: 0.85rem;
            padding: 0.4rem 0.8rem;
        }
    }
    
    /* GPT-o3 Analysis Animation Styles */
    @keyframes pulse {
        0%, 100% { opacity: 0.6; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.05); }
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes dots {
        0%, 20% { content: ''; }
        40% { content: '.'; }
        60% { content: '..'; }
        80%, 100% { content: '...'; }
    }
    
    .gpt-o3-analysis-container {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    .analysis-status {
        display: flex;
        align-items: center;
        gap: 1rem;
        font-size: 1.1rem;
        color: #2d3748;
        font-weight: 500;
    }
    
    .analysis-icon {
        font-size: 1.5rem;
        animation: pulse 2s infinite;
    }
    
    .thinking-dots::after {
        content: '';
        animation: dots 1.5s infinite;
    }
    
    .rotating-brain {
        font-size: 3rem;
        animation: rotate 3s linear infinite;
        display: inline-block;
    }
    
    .deep-analysis-info {
        background: rgba(255,255,255,0.7);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .progress-wave {
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        background-size: 200% 100%;
        animation: wave 2s ease-in-out infinite;
        border-radius: 2px;
        margin-top: 1rem;
    }
    
    @keyframes wave {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .analysis-phase {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7e2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #f56565;
    }
    
    .phase-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #c53030;
        margin-bottom: 0.5rem;
    }
    
    .completion-celebration {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        border: 2px solid #68d391;
        animation: celebration 0.5s ease-out;
    }
    
    @keyframes celebration {
        0% { transform: scale(0.95); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Professional Report Styling - Enhanced */
    .professional-report-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 24px;
        padding: 0;
        margin: 2rem 0;
        box-shadow: 0 12px 40px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        overflow: hidden;
        font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .report-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        color: white;
        text-align: center;
        position: relative;
    }
    
    .report-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
        pointer-events: none;
    }
    
    .report-title {
        margin: 0 0 0.5rem 0;
        font-size: 2rem;
        font-weight: 700;
        color: white !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .report-meta {
        font-size: 1.1rem;
        opacity: 0.95;
        font-weight: 500;
        position: relative;
        z-index: 1;
    }
    
    .report-content {
        padding: 3rem 2.5rem;
        line-height: 1.8;
        max-width: none;
    }
    
    /* Major Section Headers - Largest and most prominent */
    .report-major-section {
        color: #1a202c !important;
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        margin: 2.5rem 0 1.5rem 0 !important;
        padding: 1.25rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 16px;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
        transform: translateX(0);
        transition: all 0.3s ease;
    }
    
    /* Section Headers - Bold and prominent */
    .report-section-header {
        color: #2d3748 !important;
        font-size: 1.5rem !important;
        font-weight: 750 !important;
        margin: 2rem 0 1.25rem 0 !important;
        padding: 1rem 1.75rem;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 14px;
        border-left: 6px solid #667eea;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    /* Subsection Headers - Medium prominence */
    .report-subsection {
        color: #4a5568 !important;
        font-size: 1.25rem !important;
        font-weight: 650 !important;
        margin: 1.75rem 0 1rem 0 !important;
        padding: 0.75rem 1.25rem;
        background: linear-gradient(90deg, rgba(102, 126, 234, 0.08) 0%, rgba(102, 126, 234, 0.03) 100%);
        border-radius: 10px;
        border-left: 4px solid #a78bfa;
        position: relative;
    }
    
    .report-subsection::before {
        content: '▸';
        color: #667eea;
        font-size: 1.1rem;
        margin-right: 0.5rem;
        font-weight: bold;
    }
    
    /* Regular paragraphs */
    .report-paragraph {
        color: #2d3748 !important;
        font-size: 1.1rem !important;
        line-height: 1.8 !important;
        margin: 1.2rem 0 !important;
        text-align: justify;
        text-justify: inter-ideograph;
        padding: 0 0.5rem;
    }
    
    /* Key-value items */
    .report-item {
        margin: 1rem 0;
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.06) 0%, rgba(102, 126, 234, 0.03) 100%);
        border-radius: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 1px 8px rgba(0,0,0,0.04);
    }
    
    .report-label {
        color: #4a5568 !important;
        font-weight: 650 !important;
        font-size: 1.05rem !important;
        display: inline-block;
        min-width: 140px;
    }
    
    .report-value {
        color: #2d3748 !important;
        font-size: 1.05rem !important;
        margin-left: 0.5rem;
        line-height: 1.6;
        font-weight: 500;
    }
    
    /* Bullet points and numbered lists */
    .report-point {
        color: #2d3748 !important;
        font-size: 1.05rem !important;
        margin: 0.75rem 0;
        padding: 0.75rem 1.25rem;
        background: linear-gradient(90deg, rgba(102, 126, 234, 0.04) 0%, transparent 100%);
        border-radius: 8px;
        border-left: 3px solid #a78bfa;
        line-height: 1.6;
    }
    
    /* Score and rating highlights */
    .report-score {
        color: #2d3748 !important;
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        margin: 1rem 0;
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
        border-radius: 12px;
        border: 2px solid #68d391;
        text-align: center;
        box-shadow: 0 2px 12px rgba(104, 211, 145, 0.2);
    }
    
    .report-footer {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        padding: 2rem 2.5rem;
        border-top: 1px solid #e2e8f0;
    }
    
    .disclaimer {
        color: #718096 !important;
        font-size: 1rem !important;
        text-align: center;
        font-style: italic;
        line-height: 1.6;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 10px;
        border: 1px solid rgba(113, 128, 150, 0.2);
    }
    
    /* Enhanced typography hierarchy */
    .professional-report-container h1,
    .professional-report-container h2,
    .professional-report-container h3,
    .professional-report-container h4,
    .professional-report-container h5,
    .professional-report-container h6 {
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }
    
    .professional-report-container p,
    .professional-report-container div,
    .professional-report-container span {
        font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Responsive design for reports */
    @media (max-width: 768px) {
        .professional-report-container {
            margin: 1rem 0;
            border-radius: 16px;
        }
        
        .report-header {
            padding: 2rem 1.5rem;
        }
        
        .report-title {
            font-size: 1.6rem;
        }
        
        .report-content {
            padding: 2rem 1.5rem;
        }
        
        .report-major-section {
            font-size: 1.4rem !important;
            padding: 1rem 1.5rem;
            margin: 2rem 0 1rem 0 !important;
        }
        
        .report-section-header {
            font-size: 1.3rem !important;
            padding: 0.75rem 1.25rem;
            margin: 1.5rem 0 1rem 0 !important;
        }
        
        .report-subsection {
            font-size: 1.15rem !important;
            padding: 0.6rem 1rem;
        }
        
        .report-paragraph {
            font-size: 1.05rem !important;
        }
        
        .report-item {
            padding: 0.75rem 1rem;
        }
        
        .report-point {
            padding: 0.6rem 1rem;
        }
    }
    
    /* Clean, Elegant Report Styling */
    .elegant-report {
        max-width: 900px;
        margin: 2rem auto;
        padding: 0;
        font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        line-height: 1.7;
        color: #2d3748;
        background: #ffffff;
    }
    
    .report-header {
        text-align: center;
        padding: 3rem 2rem 2rem 2rem;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 3rem;
    }
    
    .report-main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a202c;
        margin: 0 0 1rem 0;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: -0.02em;
    }
    
    .report-subtitle-meta {
        font-size: 1.1rem;
        color: #718096;
        margin: 0;
        font-weight: 500;
    }
    
    .report-body {
        padding: 0 2rem;
    }
    
    .report-major-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2b6cb0;
        margin: 3rem 0 1.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2b6cb0;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .report-section-title {
        font-size: 1.4rem;
        font-weight: 650;
        color: #2d3748;
        margin: 2.5rem 0 1.2rem 0;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .report-elegant-subtitle {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2b6cb0;
        margin: 3rem 0 1.8rem 0;
        text-align: center;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 1.2rem 2rem;
        background: linear-gradient(135deg, rgba(43, 108, 176, 0.08) 0%, rgba(43, 108, 176, 0.04) 100%);
        border-radius: 16px;
        border: 2px solid rgba(43, 108, 176, 0.2);
        position: relative;
        box-shadow: 0 4px 20px rgba(43, 108, 176, 0.15);
        letter-spacing: 0.02em;
        text-shadow: 0 1px 2px rgba(43, 108, 176, 0.2);
    }
    
    .report-elegant-subtitle::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(43, 108, 176, 0.03) 50%, transparent 70%);
        border-radius: 14px;
        pointer-events: none;
    }
    
    .report-elegant-subtitle::after {
        content: '✦';
        position: absolute;
        top: 50%;
        left: 1rem;
        transform: translateY(-50%);
        color: rgba(43, 108, 176, 0.6);
        font-size: 1.2rem;
    }
    
    .report-subtitle {
        font-size: 1.2rem;
        font-weight: 600;
        color: #4a5568;
        margin: 2rem 0 1rem 0;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .report-text {
        font-size: 1.05rem;
        line-height: 1.8;
        color: #2d3748;
        margin: 1.2rem 0;
        text-align: justify;
    }
    
    .report-detail {
        font-size: 1.05rem;
        line-height: 1.7;
        color: #2d3748;
        margin: 1rem 0;
        padding-left: 1rem;
        border-left: 3px solid #e2e8f0;
    }
    
    .report-detail strong {
        color: #2b6cb0;
        font-weight: 600;
    }
    
    .report-point {
        font-size: 1.05rem;
        line-height: 1.7;
        color: #2d3748;
        margin: 0.8rem 0;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .report-highlight {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2b6cb0;
        margin: 1.5rem 0;
        padding: 1rem 1.5rem;
        background: linear-gradient(90deg, rgba(43, 108, 176, 0.08) 0%, rgba(43, 108, 176, 0.03) 100%);
        border-left: 4px solid #2b6cb0;
        border-radius: 0 8px 8px 0;
    }
    
    .report-footer {
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid #e2e8f0;
        text-align: center;
    }
    
    .report-disclaimer {
        font-size: 0.95rem;
        color: #718096;
        margin: 0;
        font-style: italic;
        line-height: 1.6;
    }
    
    /* Responsive design for elegant report */
    @media (max-width: 768px) {
        .elegant-report {
            margin: 1rem;
            max-width: none;
        }
        
        .report-header {
            padding: 2rem 1.5rem 1.5rem 1.5rem;
        }
        
        .report-main-title {
            font-size: 1.8rem;
        }
        
        .report-body {
            padding: 0 1.5rem;
        }
        
        .report-major-title {
            font-size: 1.4rem;
        }
        
        .report-section-title {
            font-size: 1.25rem;
        }
        
        .report-elegant-subtitle {
            font-size: 1.3rem;
            margin: 2rem 0 1.3rem 0;
            padding: 1rem 1.5rem;
        }
        
        .report-elegant-subtitle::after {
            left: 0.8rem;
            font-size: 1rem;
        }
        
        .report-subtitle {
            font-size: 1.1rem;
        }
    }
    
    /* Simple, Clean Report Styling - No Cards */
    .simple-report {
        max-width: 900px;
        margin: 2rem auto;
        padding: 2rem 0;
        font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        line-height: 1.7;
        color: #2d3748;
        background: none;
    }
    
    .report-main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a202c;
        margin: 0 0 1rem 0;
        text-align: center;
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: -0.02em;
    }
    
    .report-subtitle-meta {
        font-size: 1.1rem;
        color: #718096;
        margin: 0 0 2rem 0;
        text-align: center;
        font-weight: 500;
    }
    
    .report-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #e2e8f0 20%, #e2e8f0 80%, transparent 100%);
        margin: 2rem 0;
    }
    
    .report-disclaimer {
        font-size: 0.95rem;
        color: #718096;
        margin: 2rem 0 0 0;
        font-style: italic;
        line-height: 1.6;
        text-align: center;
        padding: 1rem;
        background: rgba(113, 128, 150, 0.05);
        border-radius: 8px;
        border: 1px solid rgba(113, 128, 150, 0.1);
    }
    
    /* Clean, Simple Report Styling */
    .clean-report {
        max-width: 1000px;
        margin: 2rem auto;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        line-height: 1.6;
        color: #1a1a1a;
        background: #ffffff;
    }
    
    /* Header Section */
    .report-header-section {
        text-align: center;
        padding: 2rem 0 3rem 0;
        border-bottom: 3px solid #e5e7eb;
        margin-bottom: 3rem;
    }
    
    .report-main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #111827;
        margin: 0 0 1rem 0;
        letter-spacing: -0.025em;
        text-align: center;
    }
    
    .report-subtitle-line {
        font-size: 1.1rem;
        color: #6b7280;
        margin: 0;
        font-weight: 500;
        text-align: center;
    }
    
    /* Content Section */
    .report-content-section {
        padding: 0 1rem;
    }
    
    /* Section Headers - Most Prominent */
    .report-section-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1f2937;
        margin: 3rem 0 1.5rem 0;
        padding: 1rem 0 0.5rem 0;
        border-bottom: 2px solid #3b82f6;
        text-align: left;
        letter-spacing: -0.01em;
    }
    
    /* Category Headers - Secondary Level */
    .report-category-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #374151;
        margin: 2.5rem 0 1.2rem 0;
        padding: 0.8rem 0 0.4rem 0;
        border-bottom: 1px solid #d1d5db;
        text-align: left;
    }
    
    /* Subtitles - Third Level */
    .report-subtitle {
        font-size: 1.2rem;
        font-weight: 600;
        color: #4b5563;
        margin: 2rem 0 1rem 0;
        padding: 0.5rem 0;
        text-align: left;
        position: relative;
    }
    
    .report-subtitle::before {
        content: "▶";
        color: #3b82f6;
        margin-right: 0.5rem;
        font-size: 0.9rem;
    }
    
    /* Paragraph Text */
    .report-paragraph {
        font-size: 1rem;
        line-height: 1.7;
        color: #374151;
        margin: 1rem 0;
        text-align: justify;
        text-justify: inter-word;
    }
    
    /* Info Items (Key-Value Pairs) */
    .report-info-item {
        margin: 0.8rem 0;
        padding: 0.5rem 0;
        border-left: 3px solid #e5e7eb;
        padding-left: 1rem;
    }
    
    .report-label {
        font-weight: 600;
        color: #1f2937;
        font-size: 1rem;
    }
    
    .report-value {
        color: #374151;
        font-size: 1rem;
        margin-left: 0.5rem;
    }
    
    /* List Items */
    .report-list-item {
        margin: 0.6rem 0;
        padding: 0.4rem 0;
        color: #374151;
        font-size: 1rem;
        line-height: 1.6;
        padding-left: 1.5rem;
        position: relative;
    }
    
    /* Score Items */
    .report-score-item {
        margin: 1rem 0;
        padding: 0.8rem 1.2rem;
        background: #f8fafc;
        border-left: 4px solid #10b981;
        border-radius: 0 8px 8px 0;
        font-weight: 600;
        color: #065f46;
        font-size: 1.05rem;
    }
    
    /* Spacer */
    .report-spacer {
        height: 1rem;
    }
    
    /* Footer Section */
    .report-footer-section {
        margin-top: 3rem;
        padding: 2rem 0;
        border-top: 2px solid #e5e7eb;
        text-align: center;
    }
    
    .report-disclaimer {
        font-size: 0.95rem;
        color: #6b7280;
        margin: 0;
        font-style: italic;
        line-height: 1.6;
        padding: 1rem;
        background: #f9fafb;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .clean-report {
            margin: 1rem;
            max-width: none;
        }
        
        .report-header-section {
            padding: 1.5rem 0 2rem 0;
        }
        
        .report-main-title {
            font-size: 2rem;
        }
        
        .report-content-section {
            padding: 0 0.5rem;
        }
        
        .report-section-header {
            font-size: 1.5rem;
            margin: 2.5rem 0 1.2rem 0;
        }
        
        .report-category-header {
            font-size: 1.25rem;
            margin: 2rem 0 1rem 0;
        }
        
        .report-subtitle {
            font-size: 1.1rem;
            margin: 1.5rem 0 0.8rem 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Usage instructions with better formatting
    st.markdown(f'<div class="section-header"><h3>{get_text("usage_title", current_lang)}</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(get_text("usage_steps", current_lang))
    
    with col2:
        st.success(get_text("supported_formats", current_lang))
    
    # Main content section
    # Example buttons section - place above upload section
    st.markdown(f"""
    <div class="example-buttons-section" style="margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 16px; border: 1px solid rgba(0,0,0,0.1);">
        <h4 style="margin: 0 0 1rem 0; color: #495057; font-weight: 600; text-align: center;">📚 {"试用演示例子" if current_lang == "zh" else "Try Demo Examples"}</h4>
        <p style="margin: 0 0 1.5rem 0; color: #6c757d; text-align: center; font-size: 0.9rem;">{"点击下方按钮快速加载古董示例进行体验" if current_lang == "zh" else "Click the buttons below to quickly load antique examples for testing"}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for example buttons
    col1, col2 = st.columns(2)
    
    with col1:
        example1_button = st.button(get_text("example1_btn", current_lang), use_container_width=True, help="加载第一个古董示例" if current_lang == "zh" else "Load first antique example")
    
    with col2:
        example2_button = st.button(get_text("example2_btn", current_lang), use_container_width=True, help="加载第二个古董示例" if current_lang == "zh" else "Load second antique example")
    
    # Handle example button clicks
    if example1_button:
        load_example_into_session(1)
        st.success("✅ 已加载试用例子1！" if current_lang == "zh" else "✅ Example 1 loaded successfully!")
        st.rerun()
    
    if example2_button:
        load_example_into_session(2)
        st.success("✅ 已加载试用例子2！" if current_lang == "zh" else "✅ Example 2 loaded successfully!")
        st.rerun()
    
    # Upload prompt section with icons and clear instructions
    upload_tips_html = " ".join([f'<span class="tip-item">{tip}</span>' for tip in get_text("upload_tips", current_lang)])
    st.markdown(f"""
    <div class="upload-prompt-section">
        <div class="upload-icon">📷</div>
        <h3 class="upload-title">{get_text("upload_title", current_lang)}</h3>
        <p class="upload-description">
            <strong>📸 {get_text("upload_subtitle", current_lang)}</strong><br>
            {get_text("upload_description", current_lang)}
        </p>
        <div class="upload-tips">
            {upload_tips_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload area with dynamic key for reset functionality
    uploaded_files = st.file_uploader(
        get_text("name_label", current_lang).replace("🏷️ 古董名称/标题 (可选):", "选择图片文件:").replace("🏷️ Antique Name/Title (Optional):", "Choose image files:"),
        type=['jpg', 'jpeg', 'png', 'webp'],
        accept_multiple_files=True,
        help="可以同时上传多张图片，支持JPG、PNG、WEBP格式" if current_lang == "zh" else "Upload multiple images simultaneously, supports JPG, PNG, WEBP formats",
        key=f"uploaded_files_{st.session_state.reset_trigger}"
    )
    
    # Check if example images should be displayed
    example_images_to_display = []
    if hasattr(st.session_state, 'example_loaded') and hasattr(st.session_state, 'example_images'):
        if st.session_state.example_loaded and st.session_state.example_images:
            example_images_to_display = st.session_state.example_images
    
    # Display uploaded images or example images with better styling
    if uploaded_files or example_images_to_display:
        if uploaded_files:
            st.markdown(f'<div class="section-header"><h3>🖼️ {"预览上传的图片" if current_lang == "zh" else "Preview Uploaded Images"}</h3></div>', unsafe_allow_html=True)
            st.success(f"✅ {'已成功上传' if current_lang == 'zh' else 'Successfully uploaded'} {len(uploaded_files)} {'张图片' if current_lang == 'zh' else 'images'}")
            images_to_display = uploaded_files
            is_uploaded = True
        else:
            st.markdown(f'<div class="section-header"><h3>🖼️ {"试用例子" if current_lang == "zh" else "Demo Example"}{st.session_state.example_loaded} - {"预览图片" if current_lang == "zh" else "Preview Images"}</h3></div>', unsafe_allow_html=True)
            st.info(f"📚 {'正在显示试用例子' if current_lang == 'zh' else 'Displaying demo example'}{st.session_state.example_loaded}{'的图片' if current_lang == 'zh' else ' images'}")
            images_to_display = example_images_to_display
            is_uploaded = False
        
        # Display images in a responsive grid
        cols_per_row = 3
        num_images = len(images_to_display)
        
        for i in range(0, num_images, cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j in range(cols_per_row):
                idx = i + j
                if idx < num_images:
                    with cols[j]:
                        try:
                            if is_uploaded:
                                image = Image.open(images_to_display[idx])
                                caption = f"{'图片' if current_lang == 'zh' else 'Image'} {idx + 1}: {images_to_display[idx].name}"
                            else:
                                image = Image.open(images_to_display[idx])
                                filename = os.path.basename(images_to_display[idx])
                                caption = f"{'示例图片' if current_lang == 'zh' else 'Example Image'} {idx + 1}: {filename}"
                            
                            st.markdown('<div class="image-preview">', unsafe_allow_html=True)
                            st.image(image, caption=caption, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        except Exception as e:
                            if is_uploaded:
                                st.error(f"❌ {'无法显示图片' if current_lang == 'zh' else 'Cannot display image'} {idx + 1}: {images_to_display[idx].name}")
                            else:
                                st.error(f"❌ {'无法显示示例图片' if current_lang == 'zh' else 'Cannot display example image'} {idx + 1}")
        
        # File size check for uploaded files only
        if is_uploaded:
            # Reset file pointers before calculating size (Image.open() moves the pointer)
            for f in uploaded_files:
                f.seek(0)
            
            total_size = sum(len(f.read()) for f in uploaded_files)
            for f in uploaded_files:
                f.seek(0)
            
            if total_size > 50 * 1024 * 1024:
                st.warning("⚠️ 上传的图片总大小超过50MB，可能影响处理速度" if current_lang == "zh" else "⚠️ Total uploaded image size exceeds 50MB, may affect processing speed")
            else:
                file_size_mb = total_size / (1024 * 1024)
                st.info(f"📊 {'总文件大小' if current_lang == 'zh' else 'Total file size'}: {file_size_mb:.1f} MB")
    
    # Input fields section
    st.markdown(f'<div class="section-header"><h3>{get_text("info_title", current_lang)} <span style="font-size: 0.6em; font-weight: 400; color: #6c757d;">{get_text("info_subtitle", current_lang)}</span></h3></div>', unsafe_allow_html=True)
    
    # Get example data if available
    example_title = ""
    example_description = ""
    example_estimated_period = ""
    example_estimated_material = ""
    example_acquisition_info = ""
    if hasattr(st.session_state, 'example_title') and hasattr(st.session_state, 'example_description') and hasattr(st.session_state, 'example_estimated_period') and hasattr(st.session_state, 'example_estimated_material') and hasattr(st.session_state, 'example_acquisition_info'):
        example_title = st.session_state.example_title if st.session_state.example_title != "[请在此输入古董标题]" else ""
        example_description = st.session_state.example_description if st.session_state.example_description != "[请在此输入古董描述信息]" else ""
        example_estimated_period = st.session_state.example_estimated_period if st.session_state.example_estimated_period != "[请在此输入估计年代]" else ""
        example_estimated_material = st.session_state.example_estimated_material if st.session_state.example_estimated_material != "[请在此输入估计材质]" else ""
        example_acquisition_info = st.session_state.example_acquisition_info if st.session_state.example_acquisition_info != "[请在此输入获得方式]" else ""
    
    # Two-column layout for input fields
    col1, col2 = st.columns(2)
    
    with col1:
        manual_title = st.text_input(
            get_text("name_label", current_lang),
            value=example_title,
            placeholder=get_text("name_placeholder", current_lang),
            key=f"manual_title_{st.session_state.reset_trigger}"
        )
        
        manual_description = st.text_area(
            get_text("description_label", current_lang),
            value=example_description,
            placeholder=get_text("description_placeholder", current_lang),
            height=220,
            key=f"manual_description_{st.session_state.reset_trigger}"
        )
    
    with col2:
        estimated_period = st.text_input(
            get_text("period_label", current_lang),
            value=example_estimated_period,
            placeholder=get_text("period_placeholder", current_lang),
            key=f"estimated_period_{st.session_state.reset_trigger}"
        )
        
        estimated_material = st.text_input(
            get_text("material_label", current_lang),
            value=example_estimated_material,
            placeholder=get_text("material_placeholder", current_lang),
            key=f"estimated_material_{st.session_state.reset_trigger}"
        )
        
        acquisition_info = st.text_area(
            get_text("acquisition_label", current_lang),
            value=example_acquisition_info,
            placeholder=get_text("acquisition_placeholder", current_lang),
            height=120,
            key=f"acquisition_info_{st.session_state.reset_trigger}"
        )
    
    # Add clarification about the role of text inputs
    if current_lang == "zh":
        st.info("""
        💡 **说明**: 以上文字信息将作为参考背景提供给专业鉴定系统。
        
        📸 **主要鉴定依据**: 图片中的视觉证据（工艺、材质、细节等）
        
        📝 **辅助参考信息**: 您提供的文字描述
        
        🔍 **分析方式**: 系统将首先基于图片进行独立分析，然后对比您的描述信息，指出一致性或差异。
        """)
    else:
        st.info("""
        💡 **Note**: The above text information will be provided as reference background to the professional authentication system.
        
        📸 **Primary Authentication Basis**: Visual evidence from images (craftsmanship, materials, details, etc.)
        
        📝 **Auxiliary Reference Information**: Text descriptions you provide
        
        🔍 **Analysis Method**: The system will first conduct independent analysis based on images, then compare with your description information, pointing out consistency or differences.
        """)
    
    # Button section with evaluation and reset buttons
    st.markdown("---")
    st.markdown('<div style="margin: 2rem 0; text-align: center;">', unsafe_allow_html=True)
    
    # Create columns for buttons
    col1, col2, col3, col4, col5 = st.columns([1, 2, 0.5, 2, 1])
    
    with col2:
        evaluate_button = st.button(get_text("evaluate_btn", current_lang), type="primary", use_container_width=True)
    
    with col4:
        reset_button = st.button(get_text("reset_btn", current_lang), use_container_width=True, help="清除所有上传的图片和填写的信息，开始新的鉴定" if current_lang == "zh" else "Clear all uploaded images and filled information, start new authentication")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle reset button click
    if reset_button:
        reset_app()
        st.success("✅ 已重置所有内容，可以开始新的鉴定！" if current_lang == "zh" else "✅ All content has been reset, you can start new authentication!")
        st.rerun()
    
    if evaluate_button:
        # Check if we have either uploaded files or example images
        has_uploaded = uploaded_files and len(uploaded_files) > 0
        has_examples = hasattr(st.session_state, 'example_images') and st.session_state.example_images
        
        if not has_uploaded and not has_examples:
            st.error("❌ 请至少上传一张古董图片或选择一个试用例子" if current_lang == "zh" else "❌ Please upload at least one antique image or select a demo example")
            return
        
        # Build description
        full_description = []
        if manual_description:
            desc_prefix = "古董描述信息" if current_lang == "zh" else "Antique Description"
            full_description.append(f"{desc_prefix}: {manual_description}")
        if estimated_period:
            period_prefix = "估计年代" if current_lang == "zh" else "Estimated Period"
            full_description.append(f"{period_prefix}: {estimated_period}")
        if estimated_material:
            material_prefix = "估计材质" if current_lang == "zh" else "Estimated Material"
            full_description.append(f"{material_prefix}: {estimated_material}")
        if acquisition_info:
            acquisition_prefix = "获得方式" if current_lang == "zh" else "How Acquired"
            full_description.append(f"{acquisition_prefix}: {acquisition_info}")
        
        combined_description = "\n".join(full_description) if full_description else ""
        
        # Proceed with evaluation based on input type
        if has_uploaded:
            process_evaluation_with_uploaded_files(uploaded_files, combined_description, manual_title, current_lang)
        else:
            process_evaluation_with_example_images(st.session_state.example_images, combined_description, manual_title, current_lang)
    
    # Enhanced footer with better contrast
    footer_title = get_text("app_title", current_lang)
    footer_subtitle = "基于最新AI模型的专业古董评估工具" if current_lang == "zh" else "Professional antique assessment tool based on latest AI models"
    footer_warning = "⚠️ 本工具仅供参考，重要决策请咨询专业古董鉴定师" if current_lang == "zh" else "⚠️ This tool is for reference only, please consult professional antique appraisers for important decisions"
    footer_tip = "💡 支持多角度图片上传，提供更准确的鉴定分析" if current_lang == "zh" else "💡 Supports multi-angle image uploads for more accurate authentication analysis"
    footer_security = "🔒 您的图片数据安全加密处理，不会被存储或泄露" if current_lang == "zh" else "🔒 Your image data is securely encrypted and processed, not stored or leaked"
    
    st.markdown(f"""
    <div class="footer-section">
        <h4 style='color: #212529; margin-bottom: 1.5rem; font-weight: 600; font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;'>{footer_title}</h4>
        <p style='color: #343a40; margin-bottom: 1rem; font-size: 1.1rem; font-weight: 500;'>{footer_subtitle}</p>
        <div style='margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(52, 58, 64, 0.3);'>
            <p style='color: #495057; margin: 0.75rem 0; font-weight: 600; font-size: 0.95rem;'>{footer_warning}</p>
            <p style='color: #343a40; margin: 0.75rem 0; font-size: 0.95rem; font-weight: 500;'>{footer_tip}</p>
            <p style='color: #495057; margin: 0.75rem 0; font-size: 0.9rem; font-weight: 500;'>{footer_security}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def process_evaluation_with_uploaded_files(uploaded_files, description: str, title: str, lang: str):
    """Process evaluation using uploaded image files with enhanced GPT-o3 analysis progress display"""
    try:
        # Create progress container
        progress_container = st.empty()
        
        # Step 1: Initialize evaluator with animation
        with progress_container.container():
            st.markdown('''
            <div class="gpt-o3-analysis-container">
                <div class="analysis-status">
                    <span class="analysis-icon">🔧</span>
                    <span>正在初始化专业评估系统<span class="thinking-dots"></span></span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        evaluator = AntiqueEvaluator()
        time.sleep(1.5)
        
        # Step 2: Process uploaded images
        with progress_container.container():
            st.markdown('''
            <div class="gpt-o3-analysis-container">
                <div class="analysis-status">
                    <span class="analysis-icon">📸</span>
                    <span>正在处理和分析上传的图片<span class="thinking-dots"></span></span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Convert uploaded files to base64 data URLs
        image_data_urls = []
        for i, uploaded_file in enumerate(uploaded_files):
            data_url = encode_uploaded_image(uploaded_file)
            if data_url:
                image_data_urls.append(data_url)
                logger.info(f"Successfully processed uploaded image {i+1}: {uploaded_file.name}")
            else:
                st.warning(f"⚠️ 无法处理图片: {uploaded_file.name}")
        
        if not image_data_urls:
            st.error("❌ 无法处理任何上传的图片，请检查图片格式")
            return
        
        time.sleep(1.5)
        
        # Step 3: AI Analysis with enhanced animation
        with progress_container.container():
            st.markdown('''
            <div class="gpt-o3-analysis-container">
                <div style="text-align: center;">
                    <span class="rotating-brain">🧠</span>
                    <h2 style="color: #2d3748; margin: 1rem 0;">专业鉴定系统深度分析启动</h2>
                </div>
                <div class="deep-analysis-info">
                    <h3 style="margin: 0 0 1rem 0;">🔬 多维度智能鉴定</h3>
                    <p style="margin: 0; font-size: 1.1rem;">
                        正在进行历史文献核对、工艺特征分析、材质科学检测、年代考证验证<br>
                        <strong>预计耗时1-3分钟，请耐心等待高质量分析结果</strong>
                    </p>
                </div>
                <div class="progress-wave"></div>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(2)
        
        # Step 4: Show AI thinking animation during API call
        with progress_container.container():
            st.markdown('''
            <div class="gpt-o3-analysis-container">
                <div style="text-align: center;">
                    <span class="rotating-brain">🧠</span>
                    <h2 style="color: #2d3748; margin: 1rem 0;">专业鉴定系统正在深度思考中...</h2>
                </div>
                <div class="deep-analysis-info">
                    <h3 style="margin: 0 0 1rem 0;">🔬 智能分析进行中</h3>
                    <p style="margin: 0; font-size: 1.1rem;">
                        专业鉴定系统正在运用先进算法分析您的古董<br>
                        <strong>请耐心等待，分析过程可能需要1-3分钟</strong>
                    </p>
                </div>
                <div class="progress-wave"></div>
                <div style="text-align: center; margin-top: 1.5rem;">
                    <div style="display: inline-flex; align-items: center; gap: 0.5rem; color: #667eea; font-weight: 600;">
                        <span style="animation: pulse 1.5s ease-in-out infinite;">💭</span>
                        <span>深度推理中</span>
                        <span class="thinking-dots"></span>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Start evaluation
        descriptions = [description] if description else []
        
        # Call AI evaluation (this is where the long process happens) - now with language support
        result = evaluator.evaluate_antique(
            uploaded_files=image_data_urls,
            descriptions=descriptions,
            title=title,
            language=lang
        )
        
        # Language-specific message for phase 4
        phase4_title = "💰 第四阶段：市场价值评估" if lang == "zh" else "💰 Phase 4: Market Value Assessment"
        phase4_desc = "评估历史价值、艺术价值、市场行情" if lang == "zh" else "Evaluating historical value, artistic value, market trends"
        
        # Step 5: Show analysis phases after API call
        with progress_container.container():
            st.markdown(f'''
            <div class="gpt-o3-analysis-container">
                <div class="analysis-phase">
                    <div class="phase-title">{phase4_title}</div>
                    <div>{phase4_desc}<span class="thinking-dots"></span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(1.5)
        
        # Language-specific completion messages
        completion_title = "🎉 专业鉴定分析完成！" if lang == "zh" else "🎉 Professional authentication analysis completed!"
        completion_desc = "专业鉴定系统已完成全面分析，正在生成详细报告..." if lang == "zh" else "Professional authentication system has completed comprehensive analysis, generating detailed report..."
        
        # Show completion
        with progress_container.container():
            st.markdown(f'''
            <div class="completion-celebration">
                <h2 style="color: #22543d; margin: 0 0 1rem 0;">{completion_title}</h2>
                <p style="color: #2f855a; margin: 0; font-size: 1.1rem;">
                    {completion_desc}
                </p>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(1.5)
        
        # Clear progress and show results
        progress_container.empty()
        
        if result["success"]:
            # Display final results with language support
            st.markdown("---")
            st.markdown(f"## {get_text('result_title', lang)}")
            
            # Display authenticity score with progress bar
            authenticity_score = result["score"]
            progress_html = create_authenticity_progress_bar(authenticity_score, lang)
            st.markdown(progress_html, unsafe_allow_html=True)
            
            # Score interpretation with language support
            if authenticity_score >= 80:
                st.success(get_text("high_confidence", lang) + f" ({authenticity_score}%)")
            elif authenticity_score >= 60:
                st.warning(get_text("medium_confidence", lang) + f" ({authenticity_score}%)")
            elif authenticity_score >= 40:
                st.warning(get_text("low_confidence", lang) + f" ({authenticity_score}%)")
            else:
                st.error(get_text("very_low_confidence", lang) + f" ({authenticity_score}%)")
            
            # Then display the detailed evaluation text
            st.markdown("---")
            st.markdown(f"## {get_text('report_title', lang)}")
            
            # Use the formatted evaluation from the result
            st.markdown(result["evaluation"], unsafe_allow_html=True)
            
            # Display input summary with language support
            input_summary_title = "📊 输入信息汇总" if lang == "zh" else "📊 Input Information Summary"
            with st.expander(input_summary_title, expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    image_count_label = "**📁 处理的图片:**" if lang == "zh" else "**📁 Processed Images:**"
                    st.markdown(image_count_label)
                    for i, uploaded_file in enumerate(uploaded_files):
                        st.markdown(f"  {i+1}. {uploaded_file.name}")
                
                with col2:
                    if title:
                        title_label = "**🏷️ 古董标题:**" if lang == "zh" else "**🏷️ Antique Title:**"
                        st.markdown(f"{title_label} {title}")
                    if description:
                        desc_label = "**📝 描述信息:**" if lang == "zh" else "**📝 Description:**"
                        display_desc = description[:100] + "..." if len(description) > 100 else description
                        st.markdown(f"{desc_label} {display_desc}")
                        
        else:
            error_title = "❌ 评估失败" if lang == "zh" else "❌ Evaluation Failed"
            st.error(f"{error_title}: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        error_msg = f"处理过程中发生错误: {str(e)}" if lang == "zh" else f"Error occurred during processing: {str(e)}"
        st.error(error_msg)
        logger.error(f"Error in process_evaluation_with_uploaded_files: {str(e)}")
        api_check_msg = "💡 请检查API密钥是否正确，或稍后重试" if lang == "zh" else "💡 Please check if API key is correct, or try again later"
        st.info(api_check_msg)

def process_evaluation_with_example_images(example_images, description: str, title: str, lang: str):
    """Process evaluation using example images with enhanced analysis progress display"""
    try:
        # Create progress container
        progress_container = st.empty()
        
        # Language-specific messages
        init_msg = "正在初始化专业评估系统" if lang == "zh" else "Initializing professional authentication system"
        process_msg = "正在处理示例图片数据" if lang == "zh" else "Processing example image data"
        analysis_msg = "专业鉴定系统深度分析启动" if lang == "zh" else "Professional authentication system deep analysis initiated"
        multi_analysis = "🔬 多维度智能鉴定" if lang == "zh" else "🔬 Multi-dimensional Intelligent Authentication"
        thinking_msg = "专业鉴定系统正在深度思考中..." if lang == "zh" else "Professional authentication system thinking deeply..."
        
        # Step 1: Initialize evaluator with animation
        with progress_container.container():
            st.markdown(f'''
            <div class="gpt-o3-analysis-container">
                <div class="analysis-status">
                    <span class="analysis-icon">🔧</span>
                    <span>{init_msg}<span class="thinking-dots"></span></span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        evaluator = AntiqueEvaluator()
        time.sleep(1.5)
        
        # Step 2: Process example images
        with progress_container.container():
            st.markdown(f'''
            <div class="gpt-o3-analysis-container">
                <div class="analysis-status">
                    <span class="analysis-icon">📸</span>
                    <span>{"正在处理和分析示例图片" if lang == "zh" else "Processing and analyzing example images"}<span class="thinking-dots"></span></span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Convert example images to base64 data URLs
        image_data_urls = []
        for i, image_file in enumerate(example_images):
            data_url = encode_image_file_path(image_file)
            if data_url:
                image_data_urls.append(data_url)
                logger.info(f"Successfully processed example image {i+1}: {image_file}")
            else:
                warning_msg = f"⚠️ 无法处理示例图片: {image_file}" if lang == "zh" else f"⚠️ Cannot process example image: {image_file}"
                st.warning(warning_msg)
        
        if not image_data_urls:
            error_msg = "❌ 无法处理任何示例图片，请检查图片格式" if lang == "zh" else "❌ Cannot process any example images, please check image formats"
            st.error(error_msg)
            return
        
        time.sleep(1.5)
        
        # Step 3: AI Analysis with enhanced animation
        analysis_title = "专业鉴定系统深度分析启动" if lang == "zh" else "Professional authentication system deep analysis initiated"
        analysis_info = "🔬 多维度智能鉴定" if lang == "zh" else "🔬 Multi-dimensional Intelligent Authentication"
        analysis_desc = "正在进行历史文献核对、工艺特征分析、材质科学检测、年代考证验证" if lang == "zh" else "Conducting historical document verification, craftsmanship analysis, material detection, period authentication"
        analysis_time = "预计耗时1-3分钟，请耐心等待高质量分析结果" if lang == "zh" else "Estimated time 1-3 minutes, please wait patiently for high-quality analysis results"
        
        with progress_container.container():
            st.markdown(f'''
            <div class="gpt-o3-analysis-container">
                <div style="text-align: center;">
                    <span class="rotating-brain">🧠</span>
                    <h2 style="color: #2d3748; margin: 1rem 0;">{analysis_title}</h2>
                </div>
                <div class="deep-analysis-info">
                    <h3 style="margin: 0 0 1rem 0;">{analysis_info}</h3>
                    <p style="margin: 0; font-size: 1.1rem;">
                        {analysis_desc}<br>
                        <strong>{analysis_time}</strong>
                    </p>
                </div>
                <div class="progress-wave"></div>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(2)
        
        # Step 4: Show AI thinking animation during API call
        thinking_title = "专业鉴定系统正在深度思考中..." if lang == "zh" else "Professional authentication system thinking deeply..."
        thinking_info = "🔬 智能分析进行中" if lang == "zh" else "🔬 Intelligent Analysis in Progress"
        thinking_desc = "专业鉴定系统正在运用先进算法分析您的古董" if lang == "zh" else "Professional authentication system is analyzing your antique using advanced algorithms"
        thinking_wait = "请耐心等待，分析过程可能需要1-3分钟" if lang == "zh" else "Please be patient, analysis process may take 1-3 minutes"
        thinking_process = "深度推理中" if lang == "zh" else "Deep reasoning in progress"
        
        with progress_container.container():
            st.markdown(f'''
            <div class="gpt-o3-analysis-container">
                <div style="text-align: center;">
                    <span class="rotating-brain">🧠</span>
                    <h2 style="color: #2d3748; margin: 1rem 0;">{thinking_title}</h2>
                </div>
                <div class="deep-analysis-info">
                    <h3 style="margin: 0 0 1rem 0;">{thinking_info}</h3>
                    <p style="margin: 0; font-size: 1.1rem;">
                        {thinking_desc}<br>
                        <strong>{thinking_wait}</strong>
                    </p>
                </div>
                <div class="progress-wave"></div>
                <div style="text-align: center; margin-top: 1.5rem;">
                    <div style="display: inline-flex; align-items: center; gap: 0.5rem; color: #667eea; font-weight: 600;">
                        <span style="animation: pulse 1.5s ease-in-out infinite;">💭</span>
                        <span>{thinking_process}</span>
                        <span class="thinking-dots"></span>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Start evaluation
        descriptions = [description] if description else []
        
        # Call AI evaluation (this is where the long process happens)
        result = evaluator.evaluate_antique(
            uploaded_files=image_data_urls,
            descriptions=descriptions,
            title=title,
            language=lang
        )
        
        # Language-specific message for phase 4
        phase4_title = "💰 第四阶段：市场价值评估" if lang == "zh" else "💰 Phase 4: Market Value Assessment"
        phase4_desc = "评估历史价值、艺术价值、市场行情" if lang == "zh" else "Evaluating historical value, artistic value, market trends"
        
        # Step 5: Show analysis phases after API call
        with progress_container.container():
            st.markdown(f'''
            <div class="gpt-o3-analysis-container">
                <div class="analysis-phase">
                    <div class="phase-title">{phase4_title}</div>
                    <div>{phase4_desc}<span class="thinking-dots"></span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(1.5)
        
        # Language-specific completion messages
        completion_title = "🎉 专业鉴定分析完成！" if lang == "zh" else "🎉 Professional authentication analysis completed!"
        completion_desc = "专业鉴定系统已完成全面分析，正在生成详细报告..." if lang == "zh" else "Professional authentication system has completed comprehensive analysis, generating detailed report..."
        
        # Show completion
        with progress_container.container():
            st.markdown(f'''
            <div class="completion-celebration">
                <h2 style="color: #22543d; margin: 0 0 1rem 0;">{completion_title}</h2>
                <p style="color: #2f855a; margin: 0; font-size: 1.1rem;">
                    {completion_desc}
                </p>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(1.5)
        
        # Clear progress and show results
        progress_container.empty()
        
        if result["success"]:
            # Display final results with language support
            st.markdown("---")
            st.markdown(f"## {get_text('result_title', lang)}")
            
            # Display authenticity score with progress bar
            authenticity_score = result["score"]
            progress_html = create_authenticity_progress_bar(authenticity_score, lang)
            st.markdown(progress_html, unsafe_allow_html=True)
            
            # Score interpretation with language support
            if authenticity_score >= 80:
                st.success(get_text("high_confidence", lang) + f" ({authenticity_score}%)")
            elif authenticity_score >= 60:
                st.warning(get_text("medium_confidence", lang) + f" ({authenticity_score}%)")
            elif authenticity_score >= 40:
                st.warning(get_text("low_confidence", lang) + f" ({authenticity_score}%)")
            else:
                st.error(get_text("very_low_confidence", lang) + f" ({authenticity_score}%)")
            
            # Then display the detailed evaluation text
            st.markdown("---")
            st.markdown(f"## {get_text('report_title', lang)}")
            
            # Use the formatted evaluation from the result
            st.markdown(result["evaluation"], unsafe_allow_html=True)
            
            # Display input summary with language support
            input_summary_title = "📊 输入信息汇总" if lang == "zh" else "📊 Input Information Summary"
            with st.expander(input_summary_title, expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    image_count_label = "**📁 处理的图片:**" if lang == "zh" else "**📁 Processed Images:**"
                    st.markdown(image_count_label)
                    for i, image_file in enumerate(example_images):
                        filename = os.path.basename(image_file)
                        st.markdown(f"  {i+1}. {filename}")
                
                with col2:
                    if title:
                        title_label = "**🏷️ 古董标题:**" if lang == "zh" else "**🏷️ Antique Title:**"
                        st.markdown(f"{title_label} {title}")
                    if description:
                        desc_label = "**📝 描述信息:**" if lang == "zh" else "**📝 Description:**"
                        display_desc = description[:100] + "..." if len(description) > 100 else description
                        st.markdown(f"{desc_label} {display_desc}")
                        
        else:
            error_title = "❌ 评估失败" if lang == "zh" else "❌ Evaluation Failed"
            st.error(f"{error_title}: {result.get('error', 'Unknown error')}")
            api_check_msg = "💡 请检查API密钥是否正确，或稍后重试" if lang == "zh" else "💡 Please check if API key is correct, or try again later"
            st.info(api_check_msg)
                
    except Exception as e:
        error_msg = f"处理过程中发生错误: {str(e)}" if lang == "zh" else f"Error occurred during processing: {str(e)}"
        st.error(error_msg)
        logger.error(f"Error in process_evaluation_with_example_images: {str(e)}")
        api_check_msg = "💡 请检查API密钥是否正确，或稍后重试" if lang == "zh" else "💡 Please check if API key is correct, or try again later"
        st.info(api_check_msg)

if __name__ == "__main__":
    main() 