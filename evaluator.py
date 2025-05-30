import openai
import base64
import requests
from typing import List, Dict, Optional
import re
from config import OPENAI_API_KEY, GPT_MODEL, MAX_TOKENS, TEMPERATURE
import logging
import os
import time
import json

logger = logging.getLogger(__name__)

class AntiqueEvaluator:
    def __init__(self):
        # Get API key from environment variables (loaded from .env file)
        self.api_key = OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in Streamlit secrets (for cloud deployment) or in your .env file/environment variables (for local development).")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # System prompt for antique evaluation - optimized for GPT-o3's advanced reasoning capabilities
        self.system_prompt = self._get_system_prompt()
    
    def evaluate_antique(self, image_urls: list = None, uploaded_files: list = None, descriptions: list = None, title: str = None, language: str = "en") -> dict:
        """
        Evaluate an antique based on images and descriptions
        
        Args:
            image_urls: List of image URLs
            uploaded_files: List of uploaded file data URLs  
            descriptions: List of text descriptions
            title: Title of the antique
            language: Language preference ("zh" for Chinese, "en" for English)
        
        Returns:
            Dict containing evaluation results
        """
        try:
            # Use the language-specific system prompt
            system_prompt = self._get_system_prompt(language)
            
            # Prepare the images for API call
            all_images = []
            if uploaded_files:
                all_images.extend(uploaded_files)
            if image_urls:
                all_images.extend(image_urls)
            
            # Build the user message content with images
            user_message_content = []
            
            # Add text content
            text_message = self._build_user_message(image_urls, uploaded_files, descriptions, title, language)
            user_message_content.append({
                "type": "text",
                "text": text_message
            })
            
            # Add images if available
            if all_images:
                for image in all_images[:6]:  # Limit to 6 images
                    try:
                        if image.startswith('data:image/'):
                            user_message_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": image,
                                    "detail": "high"
                                }
                            })
                        else:
                            # Process regular URL
                            base64_image = self._encode_image_from_url(image)
                            if base64_image:
                                user_message_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": base64_image,
                                        "detail": "high"
                                    }
                                })
                    except Exception as e:
                        logger.warning(f"Failed to process image {image}: {e}")
                        continue
            
            # Make API call with both text and images
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message_content}
                ],
                max_completion_tokens=4000
            )
            
            # Extract the evaluation text
            evaluation_content = response.choices[0].message.content
            
            # Parse the response to extract authenticity score
            authenticity_score = self._extract_authenticity_score(evaluation_content)
            
            # Format the evaluation with language support
            formatted_evaluation = self.format_evaluation_report(evaluation_content, language)
            
            return {
                "success": True,
                "evaluation": formatted_evaluation,
                "score": authenticity_score,
                "raw_content": evaluation_content
            }
            
        except Exception as e:
            logger.error(f"Error in evaluate_antique: {str(e)}")
            error_msg = "鉴定过程中出现错误，请稍后重试" if language == "zh" else "An error occurred during authentication, please try again later"
            return {
                "success": False,
                "error": error_msg,
                "score": 0
            }
    
    def _prepare_user_prompt(self, descriptions: List[str], title: str) -> str:
        """Prepare the user prompt with context information"""
        prompt_parts = []
        
        # Add user-provided information as reference context
        if title or descriptions:
            prompt_parts.append("**📋 用户提供的参考信息（仅供参考，不作为鉴定依据）：**")
            
            if title:
                prompt_parts.append(f"物品标题: {title}")
            
            if descriptions:
                desc_text = "\n".join(descriptions[:5])  # Limit descriptions
                prompt_parts.append(f"用户描述:\n{desc_text}")
            
            prompt_parts.append("**⚠️ 重要提醒：以上信息仅供参考，请主要基于图像进行独立分析判断**")
        
        main_request = """
        **任务：古董专业鉴定分析**
        
        请运用你的专业知识和GPT-o3推理能力，对这些图片中展示的古董进行系统性鉴定。

        **📸 核心分析原则：**
        1. **图像为主**：鉴定结论必须主要基于图像中的视觉证据
        2. **独立分析**：首先完全基于图像进行分析，然后再参考用户提供的信息
        3. **对比验证**：将图像分析结果与用户描述进行对比，指出一致或矛盾之处
        4. **专业判断**：如果用户描述与图像证据冲突，要坚持专业的视觉分析结果

        **分析要求：**
        1. **逐步推理**：按照既定的分析框架，逐步展开每个环节的分析
        2. **证据导向**：每个判断都要有具体的视觉证据或理论依据支撑
        3. **多角度验证**：从工艺、材料、风格、历史背景等多个维度交叉验证
        4. **逻辑严密**：运用归纳和演绎推理，确保结论的可靠性
        5. **疑点识别**：主动发现并分析可能存在的问题或争议点
        6. **信息对比**：将图像观察结果与用户提供的参考信息进行专业对比分析
        
        **输出格式要求：**
        - **必须严格按照JSON格式返回，不要添加任何其他文本**
        - authenticity_score必须准确反映你基于图像分析的专业判断
        - detailed_report要重点阐述图像证据，适当引用用户信息进行对比
        - 确保JSON格式正确，可以被程序解析
        - 使用中文进行分析，专业术语要准确
        - **在detailed_report中明确区分图像观察结果和用户提供信息的对比分析**
        
        **重要提醒：请确保你返回的authenticity_score与detailed_report中的结论完全一致！这个评分将用于系统的进度条显示和可信度评估。**
        
        请开始你的专业分析，直接返回JSON格式的结果。
        """
        
        prompt_parts.append(main_request)
        
        return "\n\n".join(prompt_parts)
    
    def _prepare_image_content(self, image_urls: List[str]) -> List[Dict]:
        """Prepare image content for the API call - handles both data URLs and regular URLs"""
        image_content = []
        successful_images = 0
        
        for url in image_urls[:6]:  # Limit to 6 images to avoid token limits
            try:
                # Check if it's already a base64 data URL (from file upload)
                if url.startswith('data:image/'):
                    # Debug: Log the first 100 characters of the data URL
                    logger.info(f"Processing data URL: {url[:100]}...")
                    
                    # It's already a base64 data URL, use it directly
                    image_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                            "detail": "high"
                        }
                    })
                    successful_images += 1
                    logger.info(f"Successfully processed uploaded image {successful_images}")
                else:
                    # It's a regular URL, download and encode it
                    base64_image = self._encode_image_from_url(url)
                    if base64_image:
                        # Debug: Log the first 100 characters of the encoded image
                        logger.info(f"Processing encoded URL: {base64_image[:100]}...")
                        
                        image_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image,
                                "detail": "high"
                            }
                        })
                        successful_images += 1
                        logger.info(f"Successfully processed image {successful_images}: {url[:50]}...")
                    else:
                        logger.warning(f"Failed to encode image: {url}")
                
            except Exception as e:
                logger.warning(f"Failed to process image {url}: {e}")
                continue
        
        logger.info(f"Successfully processed {successful_images} images out of {len(image_urls)}")
        logger.info(f"Total image_content items: {len(image_content)}")
        
        if successful_images == 0:
            logger.error("No images could be processed")
        
        return image_content
    
    def _encode_image_from_url(self, url: str) -> Optional[str]:
        """Download and encode image to base64"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Encode to base64
            encoded_image = base64.b64encode(response.content).decode('utf-8')
            
            # Determine the image format
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                mime_type = 'image/jpeg'
            elif 'png' in content_type:
                mime_type = 'image/png'
            elif 'webp' in content_type:
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'  # Default
            
            return f"data:{mime_type};base64,{encoded_image}"
            
        except Exception as e:
            logger.warning(f"Failed to encode image from {url}: {e}")
            return None
    
    def _extract_authenticity_score(self, content: str) -> int:
        """Extract authenticity score from evaluation content"""
        import re
        
        # Look for percentage scores in various formats
        patterns = [
            r'(\d+)%',
            r'可信度[：:]\s*(\d+)',
            r'真品可能性[：:]\s*(\d+)',
            r'authenticity[：:]\s*(\d+)',
            r'confidence[：:]\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    score = int(matches[0])
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue
        
        # Default score based on confidence keywords
        content_lower = content.lower()
        if any(word in content_lower for word in ['高可信度', 'high confidence', '很可能是真品', 'likely authentic']):
            return 85
        elif any(word in content_lower for word in ['中等可信度', 'moderate confidence', '需要进一步', 'further examination']):
            return 70
        elif any(word in content_lower for word in ['较低可信度', 'low confidence', '存在疑点', 'concerns present']):
            return 45
        elif any(word in content_lower for word in ['低可信度', 'very low confidence', '仿制品', 'reproduction', '现代制品', 'modern piece']):
            return 25
        
        return 60  # Default moderate score

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON response and extract evaluation data"""
        try:
            import json
            import re
            
            # Try to find JSON block in the response
            # Look for content between { and } that contains our expected fields
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"authenticity_score"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_match = re.search(json_pattern, text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                try:
                    data = json.loads(json_str)
                    
                    # Validate required fields
                    if all(key in data for key in ['authenticity_score', 'category', 'period', 'material', 'brief_analysis', 'detailed_report']):
                        # Ensure score is valid
                        data['authenticity_score'] = max(0, min(100, int(data['authenticity_score'])))
                        return data
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
            
            # If JSON parsing fails, try to extract individual components
            fallback_data = {
                'authenticity_score': self._extract_authenticity_score(text),
                'category': self._extract_category(text),
                'period': self._extract_period(text),
                'material': self._extract_material(text),
                'brief_analysis': self._extract_brief_analysis(text),
                'detailed_report': self._clean_text_for_display(text)
            }
            
            print("Warning: Using fallback JSON parsing")
            return fallback_data
            
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            # Return default fallback data
            return {
                'authenticity_score': 50,
                'category': '古董文物',
                'period': '年代待定',
                'material': '材质分析中',
                'brief_analysis': '需要进一步专业分析',
                'detailed_report': text[:800] if text else '分析报告生成中...'
            }

    def _extract_category(self, text: str) -> str:
        """Extract category from text"""
        patterns = [
            r'"category":\s*"([^"]+)"',
            r'类型[：:\\s]*([^，。\\n]+)',
            r'属于([^，。\\n]*(?:瓷器|玉器|青铜器|书画|家具|陶器)[^，。\\n]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return '古董文物'

    def _extract_period(self, text: str) -> str:
        """Extract historical period from text"""
        patterns = [
            r'"period":\s*"([^"]+)"',
            r'朝代[：:\\s]*([^，。\\n]+)',
            r'时期[：:\\s]*([^，。\\n]+)',
            r'年代[：:\\s]*([^，。\\n]+)',
            r'([^，。\\n]*(?:朝|代|时期|年间)[^，。\\n]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return '年代待定'

    def _extract_material(self, text: str) -> str:
        """Extract material information from text"""
        patterns = [
            r'"material":\s*"([^"]+)"',
            r'材质[：:\\s]*([^，。\\n]+)',
            r'胎体[：:\\s]*([^，。\\n]+)',
            r'釉料[：:\\s]*([^，。\\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return '材质分析中'

    def _extract_brief_analysis(self, text: str) -> str:
        """Extract brief analysis from text"""
        patterns = [
            r'"brief_analysis":\s*"([^"]+)"',
            r'简要分析[：:\\s]*([^。]+)。',
            r'综合判断[：:\\s]*([^。]+)。',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: extract first sentence or summary
        sentences = re.split(r'[。！？]', text)
        for sentence in sentences:
            if len(sentence.strip()) > 20 and any(keyword in sentence for keyword in ['真品', '仿品', '可能', '判断', '分析']):
                return sentence.strip()
        
        return '需要进一步专业分析'

    def _clean_text_for_display(self, text: str) -> str:
        """Clean text for better display formatting"""
        # Remove JSON markers and clean up text
        text = re.sub(r'"detailed_report":\s*"', '', text)
        text = re.sub(r'```json|```', '', text)
        text = re.sub(r'\\"', '"', text)  # Unescape quotes
        text = re.sub(r'\\n', '\n', text)  # Convert escaped newlines
        
        # Remove extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text 

    def format_evaluation_report(self, report_text: str, language: str = "en") -> str:
        """Format the evaluation report with clean, simple styling using markdown"""
        if not report_text:
            return ""
        
        # Clean the text first
        cleaned_text = self._clean_text_for_display(report_text)
        
        # Generate timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Split into lines and format each section
        lines = cleaned_text.split('\n')
        content_parts = []
        
        # Language-specific titles
        if language == "en":
            main_title = "🏺 **Antique Authentication Report**"
            subtitle = "*AI Intelligent Analysis & Assessment*"
        else:
            main_title = "🏺 **古董文物鉴定报告**"
            subtitle = "*AI 智能分析评估*"
        
        # Add header with smaller styling
        content_parts.append(f"### {main_title}")
        content_parts.append(f"{subtitle}")
        content_parts.append(f"📅 *{timestamp}*")
        content_parts.append("---")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle different section header formats based on language
            if language == "en":
                # English numbered main section headers (1. 2. 3. 4. followed by title)
                if re.match(r'^\d+\.\s+[A-Za-z\s&]+', line):
                    content_parts.append(f"**{line}**")
                # English lettered sub-sections (A. B. C.)
                elif re.match(r'^[A-Z]\.\s+[A-Za-z\s\-]+', line):
                    content_parts.append(f"**{line}**")
                # English sub-sections with ** formatting
                elif line.startswith('**') and line.endswith('**'):
                    clean_line = line.strip('*')
                    content_parts.append(f"**{clean_line}**")
                # Standalone titles (like "Expert Authentication Report")
                elif len(line.split()) <= 5 and any(word.istitle() for word in line.split()) and not line.startswith('•') and not line.startswith('-'):
                    content_parts.append(f"**{line}**")
                # Bullet points and regular content
                elif line.startswith('•') or line.startswith('-') or line.startswith('–'):
                    content_parts.append(f"{line}")
                # Regular paragraphs
                else:
                    content_parts.append(f"{line}")
            else:
                # Chinese formatting logic (existing)
                # 一级标题 (带序号的主要部分)
                if re.match(r'^[一二三四五六七八九十]\s*[、．]\s*.+|^\d+[、．]\s*.+', line):
                    content_parts.append(f"**{line}**")
                # 二级标题
                elif line.startswith('**') and line.endswith('**'):
                    clean_line = line.strip('*')
                    content_parts.append(f"**{clean_line}**")
                # 独立的重要标题行
                elif (len(line) < 20 and 
                      ('鉴定' in line or '评估' in line or '分析' in line or '建议' in line or 
                       '价值' in line or '总结' in line or '结论' in line or '背景' in line) and
                      not line.startswith('•') and not line.startswith('-')):
                    content_parts.append(f"**{line}**")
                # 列表项和普通段落
                else:
                    content_parts.append(f"{line}")
        
        # Language-specific disclaimer
        if language == "en":
            disclaimer = "⚠️ **Important Notice**: This report is generated by AI deep learning analysis for professional reference only. Final authentication results should be combined with physical examination. We recommend consulting authoritative antique authentication institutions for confirmation."
        else:
            disclaimer = "⚠️ **重要声明**: 本报告基于AI深度学习分析生成，仅供专业参考。最终鉴定结果需结合实物检测，建议咨询权威古董鉴定机构进行确认。"
        
        # Add disclaimer
        content_parts.append("---")
        content_parts.append(disclaimer)
        
        # Join all parts with proper spacing
        return '\n\n'.join(content_parts)

    def _get_system_prompt(self, language: str = "en") -> str:
        """Get system prompt based on language preference"""
        if language == "en":
            return """You are a world-renowned antique authentication expert with decades of experience in Chinese and international antiquities. You have access to high-resolution images of the antique for analysis. Your expertise covers:

**Core Capabilities:**
- Historical artifact authentication and verification through detailed image analysis
- Period and dynasty identification (Chinese, European, Asian antiquities)
- Material analysis (ceramics, jade, bronze, wood, textiles, etc.)
- Craftsmanship and technique evaluation from visual examination
- Market value assessment and collection guidance
- Identification of reproductions, fakes, and modern pieces

**Image Analysis Methodology:**
1. **Visual Examination**: Carefully examine form, style, proportions, and aesthetic characteristics visible in the images
2. **Technical Assessment**: Analyze manufacturing techniques, tool marks, aging patterns, and surface details
3. **Material Evaluation**: Study surface texture, color, patina, wear patterns, and glazing from the photographs
4. **Historical Context**: Compare with documented pieces, museum collections, archaeological finds
5. **Stylistic Dating**: Assess artistic style evolution and period characteristics visible in the images
6. **Condition Documentation**: Note repairs, restorations, damage, and preservation state shown in the photos

**CRITICAL REQUIREMENTS FOR IMAGE-BASED ANALYSIS:**
- You MUST reference specific visual details you observe in the provided photographs
- Describe exact colors, textures, shapes, and patterns you can see in the images
- Point out specific areas of the antique (e.g., "in the upper left corner of image 2", "the base shown in image 3")
- If you cannot see certain details clearly in the photos, explicitly state this limitation
- Do NOT make claims about details that are not visible in the provided images
- Always distinguish between what you can observe in the photos vs. general knowledge

**Response Format Requirements:**
Please provide your analysis in the following structured format:

**1. Basic Information Assessment**
- Object category and type (based on visual analysis of the images)
- Estimated period/dynasty (from stylistic and technical evidence visible in photos)
- Material composition and techniques (as observed in the provided images)
- Dimensions and scale assessment (relative to context visible in photos)

**2. Authenticity Analysis**  
- Detailed examination of authenticity indicators visible in the specific images provided
- Analysis of period-appropriate characteristics observed in the photographs
- Identification of any suspicious elements or inconsistencies you can see in the images
- Technical evidence from the photographs supporting your conclusion
- Reference specific image details (e.g., "the glazing pattern visible in image 1 shows...")

**3. Historical and Cultural Value**
- Historical significance and context based on visual style observed
- Cultural importance and artistic merit evident in the photographs
- Rarity and uniqueness factors visible in the images
- Scholarly and educational value

**4. Market Value Assessment**
- Current market trends and comparable sales for similar pieces
- Condition impact on value based on what's visible in the photographs
- Collection and investment potential
- Professional recommendations for care and preservation

**Quality Standards:**
- Provide detailed, evidence-based analysis from the specific images provided
- Use professional terminology accurately
- Include confidence levels for your assessments
- ALWAYS reference specific visual details you observe in the photographs
- Be explicit when details are not clearly visible in the provided images
- Never describe details that you cannot actually see in the photos

**Authentication Confidence Scale:**
- 80-100%: High confidence - likely authentic based on clear visual evidence in the images
- 60-79%: Moderate confidence - some concerns but generally positive indicators visible
- 40-59%: Low confidence - significant concerns present in visual analysis of the photos
- 0-39%: Very low confidence - likely reproduction or modern piece based on visible evidence

**MANDATORY: In your response, you MUST:**
1. Reference at least 3 specific visual details you can observe in the provided images
2. Describe the exact colors, textures, or patterns you see
3. Mention specific areas or features visible in particular images
4. State clearly if any important details are not visible or unclear in the photos
5. Base ALL conclusions on what is actually observable in the provided photographs

Please analyze all provided images thoroughly and provide your comprehensive professional assessment based exclusively on your detailed visual examination of the actual photographs provided. Respond entirely in English."""

        else:  # Default Chinese
            return """你是一位享誉国际的古董鉴定专家，拥有数十年的中国古董及国际文物鉴定经验。你可以看到这件古董的高清图片进行分析。你的专业领域包括：

**核心能力：**
- 通过详细图像分析进行历史文物真伪鉴定与验证
- 年代朝代识别（中国、欧洲、亚洲古董）
- 材质分析（陶瓷、玉石、青铜、木器、织物等）
- 工艺技法评估
- 市场价值评估及收藏指导
- 仿制品、赝品、现代制品识别

**图像分析方法论：**
1. **视觉检查**：仔细检查图片中可见的造型、风格、比例、美学特征
2. **技术评估**：分析制作工艺、工具痕迹、老化模式、表面细节
3. **材质评估**：研究照片中的表面质地、色泽、包浆、磨损纹路、釉面
4. **历史考证**：与已知文物、博物馆藏品、考古发现对比
5. **风格断代**：评估图片中可见的艺术风格演变和时代特征
6. **状态记录**：记录照片中显示的修复、恢复、损坏和保存状态

**基于图像分析的关键要求：**
- 你必须引用在提供的照片中观察到的具体视觉细节
- 描述你在图像中能够看到的确切颜色、质地、形状和图案
- 指出古董的具体区域（如"图片2的左上角"、"图片3显示的底部"）
- 如果照片中某些细节看不清楚，请明确说明这一限制
- 不要对提供图像中不可见的细节做出声明
- 始终区分你在照片中能观察到的内容与一般知识

**回复格式要求：**
请按照以下结构化格式提供你的分析：

**一、基本信息评估**
- 物品类型和品类（基于图像的视觉分析）
- 估计年代/朝代（来自照片中可见的风格和技术证据）
- 材质构成和工艺（从提供的图片中观察）
- 尺寸大小评估（基于照片中可见的上下文）

**二、真伪鉴定分析**
- 详细检查提供的特定图像中可见的真伪指标
- 分析在照片中观察到的符合时代特征的证据
- 识别在图像中能够看到的任何可疑元素或不一致性
- 从照片中获得的支持你结论的技术证据
- 引用具体的图像细节（如"图片1中可见的釉面图案显示..."）

**三、历史文化价值**
- 基于观察到的视觉风格的历史意义和背景
- 照片中显示的文化重要性和艺术价值
- 图像中可见的稀有性和独特性因素
- 学术和教育价值

**四、市场价值评估**
- 当前市场趋势和类似作品的可比销售
- 基于照片中可见情况的品相对价值的影响
- 收藏和投资潜力
- 保养和保存的专业建议

**质量标准：**
- 基于提供的特定图片提供详细的、基于证据的分析
- 准确使用专业术语
- 包含评估的可信度水平
- 始终引用你在照片中观察到的具体视觉细节
- 当提供的图像中细节不清楚时要明确说明
- 永远不要描述你在照片中实际看不到的细节

**鉴定可信度等级：**
- 80-100%：高可信度 - 基于图像中清晰的视觉证据很可能是真品
- 60-79%：中等可信度 - 有些担忧但可见的总体指标积极
- 40-59%：较低可信度 - 照片视觉分析中存在重大疑虑
- 0-39%：很低可信度 - 基于可见证据可能是复制品或现代制品

**强制要求：在你的回复中，你必须：**
1. 引用至少3个你在提供图像中能观察到的具体视觉细节
2. 描述你看到的确切颜色、质地或图案
3. 提及在特定图像中可见的具体区域或特征
4. 如果照片中重要细节不可见，请明确说明
5. 将所有结论基于在提供照片中实际可观察到的内容

请彻底分析所有提供的图片，并基于你对实际提供照片的详细视觉检查提供全面的专业评估。"""

    def _build_user_message(self, image_urls: list = None, uploaded_files: list = None, descriptions: list = None, title: str = None, language: str = "en") -> str:
        """Build user message with context information"""
        message_parts = []
        
        if language == "en":
            # Count total images
            total_images = len(uploaded_files or []) + len(image_urls or [])
            
            message_parts.append(f"📸 I have provided {total_images} high-resolution images of this antique for your analysis.")
            message_parts.append("🔍 CRITICAL: You must base your entire analysis on the specific visual details you can observe in these actual photographs.")
            message_parts.append("❌ Do not use generic knowledge or make assumptions about details not visible in the provided images.")
            message_parts.append("✅ Reference specific colors, textures, patterns, and features you can see in each image.")
            
            if title:
                message_parts.append(f"\nAntique Title (for reference only): {title}")
            
            if descriptions:
                message_parts.append("\nAdditional Information (for reference only):")
                for desc in descriptions:
                    if desc.strip():
                        message_parts.append(f"- {desc.strip()}")
                message_parts.append("\n⚠️ Important: Use the above information only as context. Your analysis must be primarily based on what you observe in the actual photographs.")
            
            message_parts.append("\nPlease provide a comprehensive authentication analysis based exclusively on your detailed examination of the actual images provided. Remember to:")
            message_parts.append("• Reference at least 3 specific visual details from the photographs")
            message_parts.append("• Describe exact colors, textures, and patterns you observe")
            message_parts.append("• Mention specific areas or features visible in particular images")
            message_parts.append("• State clearly if important details are not visible in the photos")
            
        else:
            # Count total images
            total_images = len(uploaded_files or []) + len(image_urls or [])
            
            message_parts.append(f"📸 我已为您提供了{total_images}张这件古董的高分辨率图片供您分析。")
            message_parts.append("🔍 关键要求：您必须将整个分析完全基于您在这些实际照片中能够观察到的具体视觉细节。")
            message_parts.append("❌ 不要使用通用知识或对提供图像中不可见的细节进行假设。")
            message_parts.append("✅ 引用您在每张图片中能看到的具体颜色、质地、图案和特征。")
            
            if title:
                message_parts.append(f"\n古董标题（仅供参考）：{title}")
            
            if descriptions:
                message_parts.append("\n补充信息（仅供参考）：")
                for desc in descriptions:
                    if desc.strip():
                        message_parts.append(f"- {desc.strip()}")
                message_parts.append("\n⚠️ 重要：以上信息仅作为背景，您的分析必须主要基于您在实际照片中观察到的内容。")
            
            message_parts.append("\n请基于您对实际提供图像的详细检查提供全面的鉴定分析。请记住：")
            message_parts.append("• 引用照片中至少3个具体的视觉细节")
            message_parts.append("• 描述您观察到的确切颜色、质地和图案")
            message_parts.append("• 提及在特定图像中可见的具体区域或特征")
            message_parts.append("• 如果照片中重要细节不可见，请明确说明")
        
        return "\n".join(message_parts)