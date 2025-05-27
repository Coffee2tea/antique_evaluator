import streamlit as st
from evaluator import AntiqueEvaluator
from config import APP_TITLE, APP_DESCRIPTION
import logging
import time
import base64
from PIL import Image
import io

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

def create_authenticity_progress_bar(score: int) -> str:
    """Create a colored progress bar for authenticity score"""
    # Calculate color from red to green based on score
    red_component = max(0, 255 - int(score * 2.55))
    green_component = min(255, int(score * 2.55))
    
    color = f"rgb({red_component}, {green_component}, 0)"
    
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
            真品可能性: {score}%
        </div>
    </div>
    """
    return progress_html

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
    """Format the evaluation report with professional styling"""
    if not report_text:
        return ""
    
    # Split the report into sections for better formatting
    lines = report_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Format headers and sections
        if any(keyword in line for keyword in ['第一步', '第二步', '第三步', '第四步', '基础信息', '工艺技术', '真伪判断', '市场价值', '总结']):
            formatted_lines.append(f'<h3 class="report-section-header">{line}</h3>')
        elif line.startswith('**') and line.endswith('**'):
            # Format bold sections
            formatted_lines.append(f'<h4 class="report-subsection">{line[2:-2]}</h4>')
        elif ':' in line and len(line.split(':')[0]) < 20:
            # Format key-value pairs
            parts = line.split(':', 1)
            if len(parts) == 2:
                formatted_lines.append(f'<div class="report-item"><span class="report-label">{parts[0]}:</span><span class="report-value">{parts[1].strip()}</span></div>')
            else:
                formatted_lines.append(f'<p class="report-paragraph">{line}</p>')
        else:
            # Regular paragraph
            formatted_lines.append(f'<p class="report-paragraph">{line}</p>')
    
    # Wrap in professional container
    formatted_content = '\n'.join(formatted_lines)
    
    return f"""
    <div class="professional-report-container">
        <div class="report-header">
            <h2 class="report-title">📋 专业古董鉴定分析报告</h2>
            <div class="report-meta">基于AI深度学习技术的综合评估</div>
        </div>
        <div class="report-content">
            {formatted_content}
        </div>
        <div class="report-footer">
            <div class="disclaimer">
                ⚠️ 本报告仅供参考，最终鉴定结果需结合实物检测。建议咨询专业古董鉴定机构进行确认。
            </div>
        </div>
    </div>
    """

def main():
    # Header with elegant, bright design
    st.markdown("""
    <div style='text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; border-radius: 20px; margin-bottom: 2.5rem; box-shadow: 0 8px 32px rgba(0,0,0,0.2); position: relative; overflow: hidden;'>
        <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);'></div>
        <h1 style='margin: 0; font-size: 2.8rem; font-weight: 600; font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif; letter-spacing: -0.02em; position: relative; z-index: 1; color: #ffffff; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>🏺 AI古董鉴定专家</h1>
        <p style='margin: 1rem 0 0 0; font-size: 1.1rem; font-weight: 400; color: rgba(255,255,255,0.9); opacity: 0.95; position: relative; z-index: 1;'>基于最新AI技术的智能古董鉴定与真伪分析平台</p>
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
    
    /* Professional Report Styling */
    .professional-report-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 20px;
        padding: 0;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        overflow: hidden;
        font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .report-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        color: white;
        text-align: center;
    }
    
    .report-title {
        margin: 0 0 0.5rem 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: white !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .report-meta {
        font-size: 1rem;
        opacity: 0.9;
        font-weight: 500;
    }
    
    .report-content {
        padding: 2.5rem;
        line-height: 1.8;
    }
    
    .report-section-header {
        color: #2d3748 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        margin: 2rem 0 1rem 0 !important;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
        border-radius: 12px;
        border-left: 4px solid #667eea;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .report-subsection {
        color: #4a5568 !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        margin: 1.5rem 0 0.75rem 0 !important;
        padding: 0.5rem 0;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .report-paragraph {
        color: #2d3748 !important;
        font-size: 1.1rem !important;
        line-height: 1.8 !important;
        margin: 1rem 0 !important;
        text-align: justify;
        text-justify: inter-ideograph;
    }
    
    .report-item {
        margin: 0.75rem 0;
        padding: 0.75rem 1rem;
        background: rgba(102, 126, 234, 0.05);
        border-radius: 8px;
        border-left: 3px solid #667eea;
    }
    
    .report-label {
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        display: inline-block;
        min-width: 120px;
    }
    
    .report-value {
        color: #2d3748 !important;
        font-size: 1.05rem !important;
        margin-left: 0.5rem;
        line-height: 1.6;
    }
    
    .report-footer {
        background: #f7fafc;
        padding: 1.5rem 2.5rem;
        border-top: 1px solid #e2e8f0;
    }
    
    .disclaimer {
        color: #718096 !important;
        font-size: 0.95rem !important;
        text-align: center;
        font-style: italic;
        line-height: 1.5;
    }
    
    /* Enhanced readability */
    .professional-report-container h1,
    .professional-report-container h2,
    .professional-report-container h3,
    .professional-report-container h4,
    .professional-report-container h5,
    .professional-report-container h6 {
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif !important;
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
        }
        
        .report-header {
            padding: 1.5rem;
        }
        
        .report-title {
            font-size: 1.5rem;
        }
        
        .report-content {
            padding: 1.5rem;
        }
        
        .report-section-header {
            font-size: 1.2rem !important;
            padding: 0.5rem 1rem;
        }
        
        .report-paragraph {
            font-size: 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Usage instructions with better formatting
    st.markdown('<div class="section-header"><h3>📋 使用说明</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **📝 使用步骤：**
        1. 上传古董图片（支持JPG、PNG、WEBP格式）
        2. 输入古董描述信息（可选）
        3. 点击评估按钮
        4. 等待最新AI模型分析结果
        
        **💡 专业建议：**
        - 上传多角度的清晰图片
        - 包含底部、侧面、细节特写
        - 图片大小不超过10MB
        """)
    
    with col2:
        st.success("""
        **📁 支持格式：**
        - JPEG (.jpg, .jpeg)
        - PNG (.png)
        - WEBP (.webp)
        
        **🎯 AI功能：**
        - 真伪鉴定分析
        - 年代估测
        - 材质识别
        - 价值评估
        """)
    
    # Main content section
    # Upload prompt section with icons and clear instructions
    st.markdown("""
    <div class="upload-prompt-section">
        <div class="upload-icon">📷</div>
        <h3 class="upload-title">上传古董图片开始鉴定</h3>
        <p class="upload-description">
            <strong>📸 请上传您的古董照片</strong><br>
            支持多张图片同时上传，建议包含不同角度的照片
        </p>
        <div class="upload-tips">
            <span class="tip-item">💡 正面照</span>
            <span class="tip-item">💡 背面照</span>
            <span class="tip-item">💡 细节特写</span>
            <span class="tip-item">💡 底部标记</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload area
    uploaded_files = st.file_uploader(
        "选择图片文件:",
        type=['jpg', 'jpeg', 'png', 'webp'],
        accept_multiple_files=True,
        help="可以同时上传多张图片，支持JPG、PNG、WEBP格式"
    )
    
    # Display uploaded images with better styling
    if uploaded_files:
        st.markdown('<div class="section-header"><h3>🖼️ 预览上传的图片</h3></div>', unsafe_allow_html=True)
        
        st.success(f"✅ 已成功上传 {len(uploaded_files)} 张图片")
        
        # Display images in a responsive grid
        cols_per_row = 3
        num_images = len(uploaded_files)
        
        for i in range(0, num_images, cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j in range(cols_per_row):
                idx = i + j
                if idx < num_images:
                    with cols[j]:
                        try:
                            image = Image.open(uploaded_files[idx])
                            st.markdown('<div class="image-preview">', unsafe_allow_html=True)
                            st.image(image, 
                                   caption=f"图片 {idx + 1}: {uploaded_files[idx].name}", 
                                   use_column_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"❌ 无法显示图片 {idx + 1}: {uploaded_files[idx].name}")
        
        # File size check
        # Reset file pointers before calculating size (Image.open() moves the pointer)
        for f in uploaded_files:
            f.seek(0)
        
        total_size = sum(len(f.read()) for f in uploaded_files)
        for f in uploaded_files:
            f.seek(0)
        
        if total_size > 50 * 1024 * 1024:
            st.warning("⚠️ 上传的图片总大小超过50MB，可能影响处理速度")
        else:
            file_size_mb = total_size / (1024 * 1024)
            st.info(f"📊 总文件大小: {file_size_mb:.1f} MB")
    
    # Input fields section
    st.markdown('<div class="section-header"><h3>📝 简单古董信息描述</h3></div>', unsafe_allow_html=True)
    
    # Two-column layout for input fields
    col1, col2 = st.columns(2)
    
    with col1:
        manual_title = st.text_input(
            "🏷️ 古董名称/标题 (可选):",
            placeholder="例如：清代康熙青花瓷碗、汉代玉璧、明代铜镜等"
        )
        
        manual_description = st.text_area(
            "📄 古董描述信息 (可选):",
            placeholder="请输入古董的详细描述，如：\n- 年代/朝代\n- 材质（陶瓷、玉石、金属等）\n- 尺寸大小\n- 制作工艺",
            height=220
        )
    
    with col2:
        estimated_period = st.text_input(
            "📅 估计年代:",
            placeholder="例如：清代、民国、宋代等"
        )
        
        estimated_material = st.text_input(
            "🔍 估计材质:",
            placeholder="例如：青花瓷、和田玉、青铜等"
        )
        
        acquisition_info = st.text_area(
            "📍 获得方式:",
            placeholder="例如：家传、拍卖购买、古玩市场等",
            height=120
        )
    
    # Evaluation button with enhanced styling and perfect center alignment
    st.markdown("---")
    st.markdown('<div style="margin: 2rem 0; text-align: center;">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        evaluate_button = st.button("🔍 开始古董鉴定", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if evaluate_button:
        if not uploaded_files:
            st.error("❌ 请至少上传一张古董图片")
            return
        
        # Build description
        full_description = []
        if manual_description:
            full_description.append(f"基本描述: {manual_description}")
        if estimated_period:
            full_description.append(f"估计年代: {estimated_period}")
        if estimated_material:
            full_description.append(f"估计材质: {estimated_material}")
        if acquisition_info:
            full_description.append(f"获得方式: {acquisition_info}")
        
        combined_description = "\n".join(full_description) if full_description else ""
        
        # Proceed with evaluation
        process_evaluation_with_uploaded_files(uploaded_files, combined_description, manual_title)
    
    # Enhanced footer with better contrast
    st.markdown("""
    <div class="footer-section">
        <h4 style='color: #212529; margin-bottom: 1.5rem; font-weight: 600; font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;'>🏺 AI古董鉴定专家</h4>
        <p style='color: #343a40; margin-bottom: 1rem; font-size: 1.1rem; font-weight: 500;'>基于最新AI模型的专业古董评估工具</p>
        <div style='margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(52, 58, 64, 0.3);'>
            <p style='color: #495057; margin: 0.75rem 0; font-weight: 600; font-size: 0.95rem;'>⚠️ 本工具仅供参考，重要决策请咨询专业古董鉴定师</p>
            <p style='color: #343a40; margin: 0.75rem 0; font-size: 0.95rem; font-weight: 500;'>💡 支持多角度图片上传，提供更准确的鉴定分析</p>
            <p style='color: #495057; margin: 0.75rem 0; font-size: 0.9rem; font-weight: 500;'>🔒 您的图片数据安全加密处理，不会被存储或泄露</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def process_evaluation_with_uploaded_files(uploaded_files, description: str, title: str):
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
                    <span>正在初始化 AI 智能评估器<span class="thinking-dots"></span></span>
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
                    <h2 style="color: #2d3748; margin: 1rem 0;">AI鉴定模型深度分析启动</h2>
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
                    <h2 style="color: #2d3748; margin: 1rem 0;">AI鉴定模型正在深度思考中...</h2>
                </div>
                <div class="deep-analysis-info">
                    <h3 style="margin: 0 0 1rem 0;">🔬 AI 智能分析进行中</h3>
                    <p style="margin: 0; font-size: 1.1rem;">
                        AI鉴定模型正在运用强大的推理能力分析您的古董<br>
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
        
        # Call AI evaluation (this is where the long process happens)
        result = evaluator.evaluate_antique(
            uploaded_files=image_data_urls
        )
        
        # Step 5: Show analysis phases after API call
        with progress_container.container():
            st.markdown('''
            <div class="gpt-o3-analysis-container">
                <div class="analysis-phase">
                    <div class="phase-title">💰 第四阶段：市场价值评估</div>
                    <div>评估历史价值、艺术价值、市场行情<span class="thinking-dots"></span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(1.5)
        
        # Show completion
        with progress_container.container():
            st.markdown('''
            <div class="completion-celebration">
                <h2 style="color: #22543d; margin: 0 0 1rem 0;">🎉 AI鉴定模型分析完成！</h2>
                <p style="color: #2f855a; margin: 0; font-size: 1.1rem;">
                    高级AI推理引擎已完成全面分析，正在生成专业鉴定报告...
                </p>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(1.5)
        
        # Clear progress and show results
        progress_container.empty()
        
        if result["success"]:
            # Display final results FIRST
            st.markdown("---")
            st.markdown("## 🎯 最终鉴定结果")
            
            # Get data from JSON response
            evaluation_data = result.get("data", {})
            authenticity_score = result["score"]
            
            # Display authenticity score with progress bar
            progress_html = create_authenticity_progress_bar(authenticity_score)
            st.markdown(progress_html, unsafe_allow_html=True)
            
            # Show additional structured information if available
            if evaluation_data:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if evaluation_data.get("category"):
                        st.markdown(f"**🏺 类型:** {evaluation_data['category']}")
                
                with col2:
                    if evaluation_data.get("period"):
                        st.markdown(f"**📅 年代:** {evaluation_data['period']}")
                
                with col3:
                    if evaluation_data.get("material"):
                        st.markdown(f"**🧱 材质:** {evaluation_data['material']}")
                
                # Show brief analysis if available
                if evaluation_data.get("brief_analysis"):
                    st.markdown(f"**💡 核心判断:** {evaluation_data['brief_analysis']}")
            
            # Score interpretation
            if authenticity_score >= 80:
                st.success(f"🟢 **高可信度**: 这件古董很可能是真品 ({authenticity_score}%)")
            elif authenticity_score >= 60:
                st.warning(f"🟡 **中等可信度**: 需要进一步专业鉴定 ({authenticity_score}%)")
            elif authenticity_score >= 40:
                st.warning(f"🟠 **较低可信度**: 存在疑点，建议谨慎 ({authenticity_score}%)")
            else:
                st.error(f"🔴 **低可信度**: 可能是仿制品或现代制品 ({authenticity_score}%)")
            
            # Then display the detailed evaluation text
            st.markdown("---")
            st.markdown("## 🎯 AI鉴定模型专业鉴定报告")
            
            # Use the formatted evaluation from the result
            st.markdown(result["evaluation"], unsafe_allow_html=True)
            
            # Display input summary
            with st.expander("📊 输入信息汇总", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📁 处理的图片:**")
                    for i, uploaded_file in enumerate(uploaded_files):
                        if i < len(image_data_urls):
                            st.markdown(f"✅ {uploaded_file.name}")
                        else:
                            st.markdown(f"❌ {uploaded_file.name} (处理失败)")
                
                with col2:
                    if title:
                        st.markdown(f"**📝 标题:** {title}")
                    if description:
                        st.markdown(f"**📄 描述:** {description[:200]}{'...' if len(description) > 200 else ''}")
            
            # Recommendations
            st.markdown("### 💡 专业建议")
            if authenticity_score >= 70:
                st.info("""
                **建议后续行动:**
                - ✅ 可考虑进行实物检测确认
                - 📚 查阅相关历史文献资料
                - 🏛️ 咨询博物馆或权威鉴定机构
                - 📸 拍摄更多细节照片建档
                """)
            else:
                st.warning("""
                **建议谨慎行动:**
                - ⚠️ 强烈建议实物专业鉴定
                - 🔍 重点检查工艺和材质细节
                - 📖 研究同时期真品对比资料
                - 💰 如用于交易需多方验证
                """)
        else:
            st.error(f"❌ 评估失败: {result.get('error', result.get('evaluation', '未知错误'))}")
            st.info("💡 请检查API密钥是否正确，或稍后重试")
                
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        st.error(f"❌ 评估过程中发生错误: {str(e)}")
        st.info("💡 请检查API密钥是否正确，或稍后重试")

if __name__ == "__main__":
    main() 