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
            
            # Parse the JSON response and extract all data
            parsed_data = self._parse_json_response(evaluation_content)
            
            # Extract score from parsed data (more reliable than direct extraction)
            authenticity_score = parsed_data.get('authenticity_score', 50)
            
            # Use the cleaned detailed_report from parsed data for formatting
            formatted_evaluation = self.format_evaluation_report(parsed_data.get('detailed_report', evaluation_content), language)

            return {
                "success": True,
                "evaluation": formatted_evaluation,
                "score": authenticity_score,
                "raw_content": evaluation_content,
                "parsed_data": parsed_data  # Include parsed data for debugging
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
        - **关键要求：响应必须是完整有效的JSON格式 - 从 { 到 }**
        - **所有分析内容必须包含在"detailed_report"字段内**
        - **绝不在JSON外放置内容 - 一切都放在detailed_report内**
        - **detailed_report必须包含所有章节、分析和结论**
        - authenticity_score必须准确反映你基于图像分析的专业判断
        - detailed_report要重点阐述图像证据，适当引用用户信息进行对比
        - 确保JSON格式正确，可以被程序解析
        - 使用中文进行分析，专业术语要准确
        - **使用正确的JSON转义：detailed_report内\\n表示换行，\\"表示引号**
        - **测试你的响应：必须是以{开始以}结束的有效JSON**
        
        **重要提醒：请确保你返回的authenticity_score与detailed_report中的结论完全一致！这个评分将用于系统的进度条显示和可信度评估。**
        
        **绝对要求：仅返回JSON格式 - {之前和}之后都不能有内容 - 一切都在detailed_report字段内！**
        
        请开始你的专业分析，只返回有效的JSON。
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
        
        # First, try to find the score in structured sections (more reliable)
        structured_patterns = [
            # Look for scores in the Authentication Assessment section
            r'(?:Authentication Assessment|鉴定评估).*?(?:Confidence score|可信度评分)[：:\s]*(\d+)%?',
            r'(?:Confidence score|可信度评分)[：:\s]*(\d+)%?',
            # Look for final confidence scores
            r'(?:Final confidence|最终可信度)[：:\s]*(\d+)%?',
            r'(?:Overall confidence|总体可信度)[：:\s]*(\d+)%?',
            # Look for authenticity percentages
            r'(?:Authenticity|真品可能性)[：:\s]*(\d+)%?',
        ]
        
        # Try structured patterns first (they are more reliable)
        for pattern in structured_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                try:
                    score = int(matches[-1])  # Take the last match (most likely the final assessment)
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue
        
        # Fallback: Look for any percentage scores, but prioritize those near confidence-related terms
        confidence_context_patterns = [
            # Look for percentages within 50 characters of confidence-related words
            r'(?:confidence|可信度|authenticity|真品).{0,50}?(\d+)%',
            r'(\d+)%?.{0,50}?(?:confidence|可信度|authenticity|真品)',
        ]
        
        for pattern in confidence_context_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    score = int(matches[-1])  # Take the last match
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue
        
        # Last resort: any percentage in the text
        general_patterns = [
            r'(\d+)%',
        ]
        
        for pattern in general_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Filter out unrealistic scores and take the most reasonable one
                valid_scores = []
                for match in matches:
                    try:
                        score = int(match)
                        if 0 <= score <= 100:
                            valid_scores.append(score)
                    except ValueError:
                        continue
                
                if valid_scores:
                    # Prefer scores that are commonly used in authentication (multiples of 5)
                    preferred_scores = [s for s in valid_scores if s % 5 == 0]
                    if preferred_scores:
                        return preferred_scores[-1]  # Take the last one
                    else:
                        return valid_scores[-1]  # Take the last valid score
        
        # Default score based on confidence keywords (unchanged)
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
            
            # Clean the text first - remove any leading/trailing whitespace
            text = text.strip()
            
            # Find the JSON structure
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
                print(f"⚠️  JSON Structure Error: Cannot find valid JSON braces")
                raise ValueError("Invalid JSON structure")
            
            # Extract JSON and external content
            json_str = text[start_idx:end_idx + 1]
            before_json = text[:start_idx].strip()
            after_json = text[end_idx + 1:].strip()
            
            # Check for content outside JSON structure
            external_content = []
            if before_json:
                print(f"⚠️  Content found BEFORE JSON: {before_json[:200]}...")
                external_content.append(before_json)
            if after_json:
                print(f"⚠️  Content found AFTER JSON: {after_json[:200]}...")
                external_content.append(after_json)
            
            try:
                data = json.loads(json_str)
                
                # If there's external content, merge it into detailed_report
                if external_content:
                    print("🔄 Auto-fixing: Moving external content into detailed_report")
                    
                    # Combine external content
                    combined_external = "\n\n".join(external_content)
                    
                    # Clean and format the external content
                    combined_external = combined_external.replace('\\"', '"')  # Unescape quotes
                    combined_external = re.sub(r'\n\s*\n', '\n\n', combined_external)  # Clean whitespace
                    
                    # Merge with existing detailed_report or replace if empty
                    existing_report = data.get('detailed_report', '').strip()
                    
                    if existing_report and not existing_report.lower().startswith('complete professional analysis'):
                        # Append external content to existing report
                        data['detailed_report'] = existing_report + "\n\n" + combined_external
                    else:
                        # Replace with external content (it's likely the main analysis)
                        data['detailed_report'] = combined_external
                    
                    print("✅ Successfully merged external content into detailed_report")
                
                # Validate required fields
                required_fields = ['authenticity_score', 'category', 'period', 'material', 'brief_analysis', 'detailed_report']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"⚠️  Missing required JSON fields: {missing_fields}")
                    # Try to fill missing fields with fallback values
                    for field in missing_fields:
                        if field == 'authenticity_score':
                            data[field] = self._extract_authenticity_score(text)
                        elif field == 'category':
                            data[field] = self._extract_category(text)
                        elif field == 'period':
                            data[field] = self._extract_period(text)
                        elif field == 'material':
                            data[field] = self._extract_material(text)
                        elif field == 'brief_analysis':
                            data[field] = self._extract_brief_analysis(text)
                        elif field == 'detailed_report':
                            data[field] = self._clean_text_for_display(text)
                
                # Ensure score is valid
                if 'authenticity_score' in data:
                    try:
                        data['authenticity_score'] = max(0, min(100, int(data['authenticity_score'])))
                    except (ValueError, TypeError):
                        data['authenticity_score'] = self._extract_authenticity_score(text)
                
                # Ensure detailed_report has content
                if not data.get('detailed_report', '').strip():
                    data['detailed_report'] = self._clean_text_for_display(text)
                
                print("✅ Successfully parsed and validated JSON response")
                return data
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON Parsing Error: {e}")
                print(f"Attempted to parse: {json_str[:500]}...")
                
            # If JSON parsing fails, try to extract individual components with improved regex
            print("🔄 Attempting fallback parsing...")
            
            # Use the entire text for fallback parsing
            full_text = text
            
            fallback_data = {
                'authenticity_score': self._extract_authenticity_score(full_text),
                'category': self._extract_category(full_text),
                'period': self._extract_period(full_text),
                'material': self._extract_material(full_text),
                'brief_analysis': self._extract_brief_analysis(full_text),
                'detailed_report': self._clean_text_for_display(full_text)
            }
            
            print("⚠️  Using fallback JSON parsing - content may not be properly formatted")
            return fallback_data
            
        except Exception as e:
            print(f"❌ Error parsing JSON response: {e}")
            print(f"Raw response preview: {text[:300]}...")
            
            # Return default fallback data with the raw content
            return {
                'authenticity_score': self._extract_authenticity_score(text) if text else 50,
                'category': self._extract_category(text) if text else '古董文物',
                'period': self._extract_period(text) if text else '年代待定',
                'material': self._extract_material(text) if text else '材质分析中',
                'brief_analysis': self._extract_brief_analysis(text) if text else '需要进一步专业分析',
                'detailed_report': self._clean_text_for_display(text) if text else '分析报告生成中...'
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
            return """You are a world-class antique analysis expert, utilizing the most advanced GPT-o3 reasoning capabilities, with deep knowledge of antique authentication and decades of practical experience. You are familiar with the characteristics of artifacts from various historical periods, manufacturing techniques, material properties, and market values. Please apply your professional knowledge and powerful logical reasoning abilities for in-depth analysis.

**🚨 CRITICAL STOP - READ THIS FIRST:**
**YOUR RESPONSE MUST BE 100% VALID JSON - NOTHING ELSE**
**IF YOU ADD ANY TEXT OUTSIDE THE JSON BRACES { }, THE SYSTEM WILL BREAK**
**ALL YOUR ANALYSIS MUST GO INSIDE THE "detailed_report" FIELD AS A STRING**

**CRITICAL JSON FORMAT REQUIREMENTS:**
- **MANDATORY: Your entire response must be valid JSON from the first { to the final }**
- **NO CONTENT OUTSIDE JSON: Do not include any text, analysis, or explanations outside the JSON structure**
- **ALL ANALYSIS INSIDE detailed_report: The complete analysis, including all sections, subsections, and conclusions, must be contained within the "detailed_report" field as a properly escaped JSON string**
- **JSON ESCAPE RULES: Use \\n for line breaks, \\" for quotes within the detailed_report content**
- **COMPLETE RESPONSE IN JSON: The response must start with { and end with } with no additional text before or after**
- **🚨 STOP BEFORE CONTINUING: If you feel tempted to add content after the closing }, DON'T DO IT**

**📸 Key Principle - Image-Priority Analysis Method:**
1. **Images are the primary basis for authentication**: Your analysis must be based primarily on visual evidence in the images
2. **Text information is for reference only**: User-provided titles, descriptions, dates, materials, etc. can only serve as background reference and should not be directly accepted
3. **Cross-validation is key**: Compare user descriptions with image observations, pointing out consistencies or contradictions
4. **Independent judgment ability**: Even if user descriptions do not match your visual analysis, you must stick to professional judgments based on image evidence
5. **Questioning and verification**: Maintain professional skepticism towards user-provided information, verify or refute through image analysis

Please evaluate according to the following structured analysis framework and return in the specified JSON format:

**Analysis Framework:**
1. **Basic Information Identification**: Dynasty/period, type classification, material analysis (mainly based on images, referencing user information)
2. **Craft Technology Analysis**: Manufacturing techniques, technical characteristics, detail observation (completely based on images)
3. **Comprehensive Authenticity Judgment**: Period consistency, material credibility, style comparison, modern traces (image evidence primary, user description as auxiliary reference)
4. **Market Value Assessment**: Historical value, artistic value, market trends

**MANDATORY JSON FORMAT - NO EXCEPTIONS:**
```json
{
    "authenticity_score": 85,
    "category": "Ming Dynasty Blue and White Porcelain",
    "period": "Ming Dynasty Yongle Period", 
    "material": "Kaolin clay body, cobalt blue glaze",
    "brief_analysis": "Core judgment summary based on image analysis",
    "detailed_report": "COMPLETE PROFESSIONAL ANALYSIS GOES HERE\\n\\n1. BASIC INFORMATION IDENTIFICATION\\n• Analysis content...\\n\\n2. CRAFT TECHNOLOGY ANALYSIS\\n• More analysis...\\n\\n3. COMPREHENSIVE AUTHENTICITY JUDGMENT\\n• Final conclusions...\\n\\n4. MARKET VALUE ASSESSMENT\\n• Value assessment..."
}
```

**�� FINAL WARNING - CRITICAL FORMATTING RULES:**
1. authenticity_score must be completely consistent with conclusions in detailed_report
2. All analysis must have specific visual evidence support
3. detailed_report must contain the ENTIRE analysis (500-800 words) with proper \\n line breaks
4. **🚨 NEVER EVER put analysis content outside the JSON structure**
5. **🚨 The detailed_report field must contain ALL sections, subsections, bullet points, and conclusions**
6. **🚨 Use proper JSON string escaping for all special characters**
7. **🚨 Response must be parseable JSON - test with JSON.parse() in your mind**
8. **🚨 DO NOT ADD ANYTHING AFTER THE CLOSING } - STOP THERE**

**🚨 ABSOLUTE REQUIREMENT: Return ONLY valid JSON. No text before the opening {, no text after the closing }. All analysis content must be inside the detailed_report field as an escaped JSON string.**

**🚨 REMINDER: Your response will be parsed by JSON.parse(). If you add content outside the JSON structure, the parsing will fail and break the application.**

Begin your professional analysis and return ONLY the JSON format result.

**Output Format Requirements:**
- **Must strictly return in JSON format, do not add any other text**
- **CRITICAL: Response must be valid JSON from start to finish - { to }**
- **ALL analysis content must be contained within the "detailed_report" field**
- **NEVER put content outside the JSON - everything goes in detailed_report**
- **detailed_report must contain ALL sections, analysis, and conclusions**
- authenticity_score must accurately reflect your professional judgment based on image analysis
- detailed_report should focus on image evidence, appropriately citing user information for comparison
- Ensure correct JSON format that can be parsed by programs
- Use English for analysis, professional terminology must be accurate
- **Use proper JSON escaping: \\n for line breaks, \\" for quotes within detailed_report**
- **Test your response: it must be valid JSON that starts with { and ends with }**

**Important Reminder: Please ensure your returned authenticity_score is completely consistent with conclusions in detailed_report! This score will be used for system progress bar display and reliability assessment.**

**ABSOLUTE REQUIREMENT: JSON FORMAT ONLY - No content before { or after } - Everything inside detailed_report field!**

Please begin your professional analysis and return ONLY valid JSON.
"""

        else:  # Default Chinese
            return """你是一个世界级的古董分析专家，运用最先进的GPT-o3推理能力，拥有深厚的古董鉴定知识和数十年的实战经验。你熟悉各个历史时期的文物特征、制作工艺、材料特点和市场价值。请运用你的专业知识和强大的逻辑推理能力进行深度分析。

**🚨 关键停止 - 请先阅读此内容:**
**你的回复必须是100%有效的JSON - 没有其他内容**
**如果你在JSON大括号{ }外添加任何文本，系统将会崩溃**
**你的所有分析都必须放在"detailed_report"字段内作为字符串**

**关键JSON格式要求：**
- **强制要求：你的整个回复必须是从第一个{到最后一个}的有效JSON格式**
- **JSON结构外不得有任何内容：不要在JSON结构外包含任何文本、分析或解释**
- **所有分析都在detailed_report内：完整的分析，包括所有章节、小节和结论，都必须包含在"detailed_report"字段内作为正确转义的JSON字符串**
- **JSON转义规则：在detailed_report内容中使用\\n表示换行，\\"表示引号**
- **完整响应在JSON内：响应必须以{开始，以}结束，前后不得有任何额外文本**
- **🚨 在继续之前停止：如果你想在结束}后添加内容，不要这样做**

**📸 关键原则 - 图像优先分析法：**
1. **图像是鉴定的主要依据**：你的分析必须主要基于图像中的视觉证据
2. **文字信息仅作参考**：用户提供的标题、描述、年代、材质等信息只能作为背景参考，不能直接采信
3. **交叉验证是关键**：将用户描述与图像观察进行对比，指出一致性或矛盾之处
4. **独立判断能力**：即使用户描述与你的视觉分析不符，也要坚持基于图像证据的专业判断
5. **质疑和验证**：对用户提供的信息保持专业怀疑态度，通过图像分析来验证或反驳

请按照以下结构化分析框架进行评估，并以指定的JSON格式返回：

**分析框架：**
1. **基础信息识别**：朝代/时期、类型分类、材质分析（主要基于图像，参考用户信息）
2. **工艺技术分析**：制作工艺、技术特点、细节观察（完全基于图像）
3. **真伪综合判断**：时代一致性、材料可信度、风格对比、现代痕迹（图像证据为主，用户描述为辅助参考）
4. **市场价值评估**：历史价值、艺术价值、市场行情

**强制JSON格式 - 不得例外：**
```json
{
    "authenticity_score": 85,
    "category": "明代青花瓷",
    "period": "明朝永乐年间", 
    "material": "高岭土胎体，钴蓝釉料",
    "brief_analysis": "基于图像分析的核心判断总结",
    "detailed_report": "完整的专业分析内容在此\\n\\n一、基础信息识别\\n• 分析内容...\\n\\n二、工艺技术分析\\n• 更多分析...\\n\\n三、真伪综合判断\\n• 最终结论...\\n\\n四、市场价值评估\\n• 价值评估..."
}
```

**🚨 最终警告 - 关键格式规则：**
1. authenticity_score必须与detailed_report中的结论完全一致
2. 所有分析都要有具体的视觉证据支撑
3. detailed_report必须包含完整的分析内容（500-800字）并使用正确的\\n换行
4. **🚨 绝对不要在JSON结构外放置分析内容**
5. **🚨 detailed_report字段必须包含所有章节、小节、要点和结论**
6. **🚨 对所有特殊字符使用正确的JSON字符串转义**
7. **🚨 响应必须是可解析的JSON - 在脑中用JSON.parse()测试**
8. **🚨 不要在结束}后添加任何内容 - 就此停止**

**🚨 绝对要求：只返回有效的JSON。开头{之前没有文本，结尾}之后没有文本。所有分析内容都必须在detailed_report字段内作为转义的JSON字符串。**

**🚨 提醒：你的响应将被JSON.parse()解析。如果你在JSON结构外添加内容，解析将失败并破坏应用程序。**

请开始你的专业分析，只返回JSON格式的结果。

**Output Format Requirements:**
- **Must strictly return in JSON format, do not add any other text**
- **CRITICAL: Response must be valid JSON from start to finish - { to }**
- **ALL analysis content must be contained within the "detailed_report" field**
- **NEVER put content outside the JSON - everything goes in detailed_report**
- **detailed_report must contain ALL sections, analysis, and conclusions**
- authenticity_score must accurately reflect your professional judgment based on image analysis
- detailed_report should focus on image evidence, appropriately citing user information for comparison
- Ensure correct JSON format that can be parsed by programs
- Use English for analysis, professional terminology must be accurate
- **Use proper JSON escaping: \\n for line breaks, \\" for quotes within detailed_report**
- **Test your response: it must be valid JSON that starts with { and ends with }**

**Important Reminder: Please ensure your returned authenticity_score is completely consistent with conclusions in detailed_report! This score will be used for system progress bar display and reliability assessment.**

**ABSOLUTE REQUIREMENT: JSON FORMAT ONLY - No content before { or after } - Everything inside detailed_report field!**

Please begin your professional analysis and return ONLY valid JSON.
"""

    def _build_user_message(self, image_urls: list = None, uploaded_files: list = None, descriptions: list = None, title: str = None, language: str = "en") -> str:
        """Build user message with context information"""
        message_parts = []
        
        if language == "en":
            # Add user-provided information as reference context
            if title or descriptions:
                message_parts.append("**📋 User-Provided Reference Information (for reference only, not as authentication basis):**")
                
                if title:
                    message_parts.append(f"Item Title: {title}")
                
                if descriptions:
                    desc_text = "\n".join(descriptions[:5])  # Limit descriptions
                    message_parts.append(f"User Description:\n{desc_text}")
                
                message_parts.append("**⚠️ Important Reminder: The above information is for reference only, please conduct independent analysis and judgment mainly based on images**")
            
            main_request = """
            **Task: Professional Antique Authentication Analysis**
            
            Please use your professional knowledge and GPT-o3 reasoning capabilities to conduct systematic authentication of the antiques shown in these images.

            **📸 Core Analysis Principles:**
            1. **Image-primary**: Authentication conclusions must be based primarily on visual evidence in the images
            2. **Independent analysis**: First conduct analysis completely based on images, then refer to user-provided information
            3. **Comparative verification**: Compare image analysis results with user descriptions, pointing out consistencies or contradictions
            4. **Professional judgment**: If user descriptions conflict with image evidence, stick to professional visual analysis results

            **Analysis Requirements:**
            1. **Step-by-step reasoning**: Develop each step of analysis according to the established analysis framework
            2. **Evidence-oriented**: Every judgment must have specific visual evidence or theoretical basis support
            3. **Multi-angle verification**: Cross-validate from multiple dimensions including craftsmanship, materials, style, historical background
            4. **Logical rigor**: Use inductive and deductive reasoning to ensure reliability of conclusions
            5. **Identify concerns**: Actively discover and analyze possible problems or controversial points
            6. **Information comparison**: Conduct professional comparative analysis between image observation results and user-provided reference information
            
            **Output Format Requirements:**
            - **Must strictly return in JSON format, do not add any other text**
            - **CRITICAL: Response must be valid JSON from start to finish - { to }**
            - **ALL analysis content must be contained within the "detailed_report" field**
            - **NEVER put content outside the JSON - everything goes in detailed_report**
            - **detailed_report must contain ALL sections, analysis, and conclusions**
            - authenticity_score must accurately reflect your professional judgment based on image analysis
            - detailed_report should focus on image evidence, appropriately citing user information for comparison
            - Ensure correct JSON format that can be parsed by programs
            - Use English for analysis, professional terminology must be accurate
            - **Use proper JSON escaping: \\n for line breaks, \\" for quotes within detailed_report**
            - **Test your response: it must be valid JSON that starts with { and ends with }**
            
            **Important Reminder: Please ensure your returned authenticity_score is completely consistent with conclusions in detailed_report! This score will be used for system progress bar display and reliability assessment.**
            
            **ABSOLUTE REQUIREMENT: JSON FORMAT ONLY - No content before { or after } - Everything inside detailed_report field!**
            
            Please begin your professional analysis and return ONLY valid JSON.
            """
            
            message_parts.append(main_request)
            
        else:
            # Add user-provided information as reference context
            if title or descriptions:
                message_parts.append("**📋 用户提供的参考信息（仅供参考，不作为鉴定依据）：**")
                
                if title:
                    message_parts.append(f"物品标题: {title}")
                
                if descriptions:
                    desc_text = "\n".join(descriptions[:5])  # Limit descriptions
                    message_parts.append(f"用户描述:\n{desc_text}")
                
                message_parts.append("**⚠️ 重要提醒：以上信息仅供参考，请主要基于图像进行独立分析判断**")
            
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
            - **关键要求：响应必须是完整有效的JSON格式 - 从 { 到 }**
            - **所有分析内容必须包含在"detailed_report"字段内**
            - **绝不在JSON外放置内容 - 一切都放在detailed_report内**
            - **detailed_report必须包含所有章节、分析和结论**
            - authenticity_score必须准确反映你基于图像分析的专业判断
            - detailed_report要重点阐述图像证据，适当引用用户信息进行对比
            - 确保JSON格式正确，可以被程序解析
            - 使用中文进行分析，专业术语要准确
            - **使用正确的JSON转义：detailed_report内\\n表示换行，\\"表示引号**
            - **测试你的响应：必须是以{开始以}结束的有效JSON**
            
            **重要提醒：请确保你返回的authenticity_score与detailed_report中的结论完全一致！这个评分将用于系统的进度条显示和可信度评估。**
            
            **绝对要求：仅返回JSON格式 - {之前和}之后都不能有内容 - 一切都在detailed_report字段内！**
            
            请开始你的专业分析，只返回有效的JSON。
            """
            
            message_parts.append(main_request)
        
        return "\n\n".join(message_parts)