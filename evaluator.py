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
        
        if title:
            prompt_parts.append(f"**古董标题**: {title}")
        
        if descriptions:
            prompt_parts.append("**背景信息**:")
            for i, desc in enumerate(descriptions, 1):
                if desc.strip():
                    prompt_parts.append(f"{i}. {desc}")
        
        main_request = """
        **专业鉴定任务**
        
        请对图片中的古董进行专业鉴定分析。

        **分析要求：**
        1. **全面观察**：仔细观察图片中古董的各个角度和细节
        2. **专业判断**：运用古董鉴定的专业知识进行分析
        3. **证据支撑**：基于可见的视觉证据得出结论
        4. **综合评估**：从工艺、材质、风格、历史背景等维度分析
        5. **参考对比**：适当参考用户提供的背景信息，但以图像分析为主
        
        **输出格式**：
        请严格按照JSON格式返回分析结果，包含以下字段：
        - authenticity_score: 真伪可信度评分（0-100）
        - category: 古董类型
        - period: 历史时期
        - material: 材质描述
        - brief_analysis: 简要分析总结
        - detailed_report: 详细分析报告（必须包含完整的7个部分：基础信息识别、工艺技术分析、真伪综合判断、价值评估、评分理由分析(Pros vs. Cons)、最终鉴定结论(Final Authentication Results)、专业建议与保养指导）
        
        请开始专业分析，只返回JSON格式的结果。
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
        if language == "zh":
            return """
你是一位世界顶级的古董鉴定专家，拥有丰富的历史文物知识和专业的鉴定经验。

**核心任务：专业古董鉴定分析**

**分析原则：**
1. **图像分析为主导**：主要依据图片中的视觉信息进行专业判断
2. **包容性分析**：即使图片质量不完美，也要尽力从可见细节中提取有价值的信息
3. **专业判断优先**：基于你的专业知识进行独立分析，用户信息仅作参考
4. **建设性评估**：专注于古董本身的特征，而非图片技术问题

**重要提醒：**
- 不要因为图片质量问题而拒绝分析
- 即使某些细节不够清晰，也要基于可见部分进行专业分析
- 专注于古董的工艺、材质、风格等实质内容
- 如果某个角度不够清楚，可以基于其他角度的图片进行补充分析

**完整分析框架（必须包含所有7个部分）：**
1. **基础信息识别**：类型、时期、材质初步判断
2. **工艺技术分析**：制作技法、装饰工艺、技术特点
3. **真伪综合判断**：时代特征、材料特性、工艺水平评估
4. **价值评估**：历史价值、艺术价值、收藏价值、增值潜力分析
   - 历史价值：文物的历史意义和文化价值
   - 艺术价值：工艺水平、美学价值、艺术成就
   - 市场价值：当前市场估价和交易参考
   - 增值潜力分析：未来升值空间、市场趋势、稀缺性评估、收藏前景
5. **评分理由分析（Pros vs. Cons）**：
   - 支持真品的证据和理由（Pros）
   - 存疑或反对的因素（Cons）  
   - 基于证据权衡得出评分理由
6. **最终鉴定结论（Final Authentication Results）**：
   - 综合所有分析的最终判断
   - 明确的真伪结论和可信度
   - 专业建议和后续推荐
7. **专业建议与保养指导（Professional Recommendations & Care Instructions）**：
   - 针对该古董的专业保养方法
   - 存放环境要求（温湿度、光照等）
   - 清洁和维护建议
   - 收藏和展示建议
   - 进一步鉴定或研究的建议
   - 投资和交易相关建议（如适用）

**输出要求：**
- 必须返回完整有效的JSON格式
- 所有分析内容放在detailed_report字段中
- 使用\\n进行换行，使用\\"转义引号
- authenticity_score要与分析结论一致（0-100分）

**JSON格式模板：**
```json
{
    "authenticity_score": 85,
    "category": "古董类型",
    "period": "历史时期", 
    "material": "材质描述",
    "brief_analysis": "简要判断总结",
    "detailed_report": "完整分析内容\\n\\n一、基础信息识别\\n详细分析...\\n\\n二、工艺技术分析\\n详细分析...\\n\\n三、真伪综合判断\\n详细分析...\\n\\n四、价值评估\\n**历史价值：**\\n文物历史意义...\\n**艺术价值：**\\n工艺水平评估...\\n**市场价值：**\\n当前市场估价...\\n**增值潜力分析：**\\n• 市场趋势分析\\n• 稀缺性评估\\n• 收藏前景\\n• 未来升值空间\\n\\n五、评分理由分析（Pros vs. Cons）\\n**支持真品的证据（Pros）：**\\n• 证据1...\\n• 证据2...\\n**存疑因素（Cons）：**\\n• 疑点1...\\n• 疑点2...\\n**评分理由：**\\n基于以上分析...\\n\\n六、最终鉴定结论（Final Authentication Results）\\n**鉴定结论：**\\n最终判断...\\n**可信度评估：**\\n具体评估...\\n**专业建议：**\\n后续建议...\\n\\n七、专业建议与保养指导\\n**保养方法：**\\n• 具体保养步骤...\\n**存放要求：**\\n• 环境条件...\\n**收藏建议：**\\n• 专业建议...\\n**注意事项：**\\n• 重要提醒..."
}
```

请开始专业分析，只返回JSON格式结果。
"""
        else:
            return """
You are a world-renowned antique authentication expert with extensive knowledge of historical artifacts and professional appraisal experience.

**Core Task: Professional Antique Authentication Analysis**

**Analysis Principles:**
1. **Image-based analysis as primary**: Make professional judgments primarily based on visual information in the images
2. **Inclusive analysis**: Even if image quality is not perfect, extract valuable information from visible details
3. **Professional judgment priority**: Conduct independent analysis based on your expertise, user information is for reference only
4. **Constructive assessment**: Focus on the antique's characteristics rather than image technical issues

**Important Reminders:**
- Do not refuse analysis due to image quality issues
- Even if some details are unclear, conduct professional analysis based on visible parts
- Focus on substantial content like craftsmanship, materials, and style of the antique
- If one angle is unclear, supplement analysis based on other angles in the images

**Complete Analysis Framework (Must include all 7 sections):**
1. **Basic Information Identification**: Type, period, preliminary material assessment
2. **Craftsmanship Analysis**: Manufacturing techniques, decorative processes, technical features
3. **Authenticity Assessment**: Period characteristics, material properties, craftsmanship level evaluation
4. **Value Assessment**: Historical value, artistic value, collectible value, appreciation potential analysis
   - Historical value: Historical significance and cultural value of the artifact
   - Artistic value: Craftsmanship level, aesthetic value, artistic achievement
   - Market value: Current market valuation and transaction references
   - Appreciation potential analysis: Future appreciation space, market trends, rarity assessment, collection prospects
5. **Scoring Rationale Analysis (Pros vs. Cons)**:
   - Evidence supporting authenticity (Pros)
   - Concerning or opposing factors (Cons)
   - Scoring rationale based on evidence weighing
6. **Final Authentication Results**:
   - Comprehensive final judgment from all analysis
   - Clear authenticity conclusion and confidence level
   - Professional recommendations and next steps
7. **Professional Recommendations & Care Instructions**:
   - Specific care methods for this antique
   - Storage environment requirements (temperature, humidity, lighting)
   - Cleaning and maintenance suggestions
   - Collection and display recommendations
   - Further authentication or research suggestions
   - Investment and trading advice (if applicable)

**Output Requirements:**
- Must return complete valid JSON format
- All analysis content in detailed_report field
- Use \\n for line breaks, use \\" to escape quotes
- authenticity_score must match analysis conclusion (0-100 points)

**JSON Format Template:**
```json
{
    "authenticity_score": 85,
    "category": "Antique Type",
    "period": "Historical Period", 
    "material": "Material Description",
    "brief_analysis": "Brief judgment summary",
    "detailed_report": "Complete analysis content\\n\\nI. Basic Information Identification\\nDetailed analysis...\\n\\nII. Craftsmanship Analysis\\nDetailed analysis...\\n\\nIII. Authenticity Assessment\\nDetailed analysis...\\n\\nIV. Value Assessment\\n**Historical Value:**\\nHistorical Significance and Cultural Value...\\n**Artistic Value:**\\nCraftsmanship Level Assessment...\\n**Market Value:**\\nCurrent Market Valuation...\\n**Appreciation Potential Analysis:**\\n• Market Trend Analysis\\n• Rarity Assessment\\n• Collection Prospects\\n• Future Appreciation Space\\n\\nV. Scoring Rationale Analysis (Pros vs. Cons)\\n**Evidence Supporting Authenticity (Pros):**\\n• Evidence 1...\\n• Evidence 2...\\n**Concerning Factors (Cons):**\\n• Concern 1...\\n• Concern 2...\\n**Scoring Rationale:**\\nBased on the above analysis...\\n\\nVI. Final Authentication Results\\n**Authentication Conclusion:**\\nFinal judgment...\\n**Confidence Assessment:**\\nSpecific assessment...\\n**Professional Recommendations:**\\nNext steps...\\n\\nVII. Professional Recommendations & Care Instructions\\n**Care Methods:**\\n• Specific care steps...\\n**Storage Requirements:**\\n• Environmental conditions...\\n**Collection Advice:**\\n• Professional suggestions...\\n**Important Notes:**\\n• Key reminders..."
}
```

Please start professional analysis and return only JSON format results.
"""

    def _build_user_message(self, image_urls: list = None, uploaded_files: list = None, descriptions: list = None, title: str = None, language: str = "en") -> str:
        """Build user message with context information"""
        message_parts = []
        
        if language == "en":
            if title or descriptions:
                message_parts.append("**Reference Information:**")
                
                if title:
                    message_parts.append(f"Antique Title: {title}")
                
                if descriptions:
                    message_parts.append("Background Information:")
                    for i, desc in enumerate(descriptions[:5], 1):
                        if desc.strip():
                            message_parts.append(f"{i}. {desc}")
            
            main_request = """
            **Professional Authentication Task**
            
            Please conduct professional authentication analysis of the antique shown in the images.

            **Analysis Requirements:**
            1. **Comprehensive observation**: Carefully observe all angles and details of the antique in the images
            2. **Professional judgment**: Apply antique authentication expertise for analysis
            3. **Evidence-based**: Draw conclusions based on visible visual evidence
            4. **Comprehensive evaluation**: Analyze from dimensions of craftsmanship, materials, style, historical background
            5. **Reference comparison**: Appropriately reference user-provided background information, but prioritize image analysis
            
            **Output Format:**
            Please strictly return analysis results in JSON format, containing the following fields:
            - authenticity_score: Authenticity confidence score (0-100)
            - category: Antique type
            - period: Historical period
            - material: Material description
            - brief_analysis: Brief analysis summary
            - detailed_report: Detailed analysis report (must include complete 7 sections: Basic Information Identification, Craftsmanship Analysis, Authenticity Assessment, Value Assessment, Scoring Rationale Analysis (Pros vs. Cons), Final Authentication Results, Professional Recommendations & Care Instructions)
            
            Please start professional analysis and return only JSON format results.
            """
            
            message_parts.append(main_request)
            
        else:
            if title or descriptions:
                message_parts.append("**参考信息：**")
                
                if title:
                    message_parts.append(f"古董标题: {title}")
                
                if descriptions:
                    message_parts.append("背景信息:")
                    for i, desc in enumerate(descriptions[:5], 1):
                        if desc.strip():
                            message_parts.append(f"{i}. {desc}")
            
            main_request = """
            **专业鉴定任务**
            
            请对图片中的古董进行专业鉴定分析。

            **分析要求：**
            1. **全面观察**：仔细观察图片中古董的各个角度和细节
            2. **专业判断**：运用古董鉴定的专业知识进行分析
            3. **证据支撑**：基于可见的视觉证据得出结论
            4. **综合评估**：从工艺、材质、风格、历史背景等维度分析
            5. **参考对比**：适当参考用户提供的背景信息，但以图像分析为主
            
            **输出格式**：
            请严格按照JSON格式返回分析结果，包含以下字段：
            - authenticity_score: 真伪可信度评分（0-100）
            - category: 古董类型
            - period: 历史时期
            - material: 材质描述
            - brief_analysis: 简要分析总结
            - detailed_report: 详细分析报告（必须包含完整的7个部分：基础信息识别、工艺技术分析、真伪综合判断、价值评估、评分理由分析(Pros vs. Cons)、最终鉴定结论(Final Authentication Results)、专业建议与保养指导）
            
            请开始专业分析，只返回JSON格式的结果。
            """
            
            message_parts.append(main_request)
        
        return "\n\n".join(message_parts)