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
        self.system_prompt = """
        你是一个世界级的古董分析专家，运用最先进的GPT-o3推理能力，拥有深厚的古董鉴定知识和数十年的实战经验。你熟悉各个历史时期的文物特征、制作工艺、材料特点和市场价值。请运用你的专业知识和强大的逻辑推理能力进行深度分析。

        **重要：你必须以JSON格式返回分析结果，确保数据准确性和一致性。**

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

        **必须返回的JSON格式：**
        ```json
        {
            "authenticity_score": 85,
            "category": "明代青花瓷",
            "period": "明朝永乐年间",
            "material": "高岭土胎体，钴蓝釉料",
            "brief_analysis": "基于图像分析的核心判断总结",
            "detailed_report": "完整的专业鉴定报告，重点阐述图像证据，适当引用用户信息进行对比验证"
        }
        ```

        **字段说明：**
        - authenticity_score: 真品可能性百分比 (0-100) - 主要基于图像分析
        - category: 古董类型分类 - 基于视觉特征识别
        - period: 历史时期/朝代 - 基于工艺风格判断
        - material: 主要材质和工艺 - 基于图像观察
        - brief_analysis: 2-3句话的核心判断总结
        - detailed_report: 详细的专业分析报告 (500-800字)

        **重要要求：**
        1. authenticity_score必须与detailed_report中的结论完全一致
        2. 所有分析都要有具体的视觉证据支撑
        3. detailed_report要包含完整的分析过程和专业术语
        4. **重点强调图像观察结果，用户提供的信息只作为对比参考**
        5. **如果用户描述与图像分析有矛盾，要明确指出并解释原因**
        6. 确保JSON格式正确，所有字符串都要用双引号
        7. 文本中的换行用\\n表示，引号用\\"转义
        """
    
    def evaluate_antique(self, image_urls: list = None, uploaded_files: list = None, descriptions: list = None, title: str = None) -> dict:
        """
        Evaluate antique using GPT-o3 with JSON response format
        
        Args:
            image_urls: List of image URLs to analyze
            uploaded_files: List of uploaded file objects
            descriptions: List of description strings about the antique
            title: Title or name of the antique
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating if evaluation was successful
            - score: Authenticity score (0-100)
            - evaluation: Formatted evaluation text for display
            - raw_response: Raw AI response
            - data: Parsed JSON data with all fields
        """
        try:
            if not image_urls and not uploaded_files:
                return {
                    "success": False,
                    "error": "No images provided for evaluation",
                    "score": 0,
                    "evaluation": "请上传图片进行鉴定",
                    "data": {}
                }

            # Process images
            image_content = []
            processed_count = 0
            
            # Handle uploaded files
            if uploaded_files:
                for file_obj in uploaded_files:
                    try:
                        # Check if it's already a data URL
                        if isinstance(file_obj, str) and file_obj.startswith('data:'):
                            image_content.append({
                                "type": "image_url",
                                "image_url": {"url": file_obj}
                            })
                            processed_count += 1
                            logger.info(f"Processing data URL: {file_obj[:50]}...")
                        else:
                            # Process uploaded file object
                            file_obj.seek(0)  # Reset file pointer
                            image_data = file_obj.read()
                            if len(image_data) > 0:
                                # Determine image format
                                image_format = "jpeg"  # Default
                                if hasattr(file_obj, 'type'):
                                    if 'png' in file_obj.type.lower():
                                        image_format = "png"
                                    elif 'gif' in file_obj.type.lower():
                                        image_format = "gif"
                                
                                # Encode to base64
                                import base64
                                base64_image = base64.b64encode(image_data).decode('utf-8')
                                data_url = f"data:image/{image_format};base64,{base64_image}"
                                
                                image_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": data_url}
                                })
                                processed_count += 1
                                logger.info(f"Successfully processed uploaded image {processed_count}")
                            
                    except Exception as e:
                        logger.error(f"Error processing uploaded file: {e}")
                        continue
            
            # Handle image URLs
            if image_urls:
                for url in image_urls:
                    try:
                        # For URLs, we need to download and convert to data URL
                        import requests
                        import base64
                        
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            # Determine image format from URL or content-type
                            image_format = "jpeg"  # Default
                            content_type = response.headers.get('content-type', '')
                            if 'png' in content_type:
                                image_format = "png"
                            elif 'gif' in content_type:
                                image_format = "gif"
                            elif url.lower().endswith('.png'):
                                image_format = "png"
                            elif url.lower().endswith('.gif'):
                                image_format = "gif"
                            
                            # Encode to base64
                            base64_image = base64.b64encode(response.content).decode('utf-8')
                            data_url = f"data:image/{image_format};base64,{base64_image}"
                            
                            image_content.append({
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            })
                            processed_count += 1
                            logger.info(f"Successfully processed image {processed_count}: {url}")
                    except Exception as e:
                        logger.error(f"Error processing image URL {url}: {e}")
                        continue

            if not image_content:
                return {
                    "success": False,
                    "error": "No valid images could be processed",
                    "score": 0,
                    "evaluation": "无法处理上传的图片，请检查图片格式",
                    "data": {}
                }

            logger.info(f"Successfully processed {processed_count} images out of {len(uploaded_files or []) + len(image_urls or [])}")
            logger.info(f"Total image_content items: {len(image_content)}")

            # Prepare user prompt with description information
            user_prompt = self._prepare_user_prompt(descriptions or [], title)

            # Create the message for GPT-o3
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": user_prompt}
                    ] + image_content
                }
            ]

            # Make API call to GPT-o3
            response = self.client.chat.completions.create(
                model="o3",
                messages=messages,
                max_completion_tokens=4000
            )

            raw_response = response.choices[0].message.content
            logger.info("Successfully received response from GPT-o3")

            # Parse JSON response
            parsed_data = self._parse_json_response(raw_response)
            
            # Extract score for backward compatibility
            score = parsed_data.get('authenticity_score', 50)
            
            # Format evaluation text for display
            formatted_evaluation = self.format_evaluation_report(parsed_data.get('detailed_report', raw_response))

            return {
                "success": True,
                "score": score,
                "evaluation": formatted_evaluation,
                "raw_response": raw_response,
                "data": parsed_data
            }

        except Exception as e:
            error_msg = f"Error in antique evaluation: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "score": 0,
                "evaluation": f"鉴定过程中发生错误：{str(e)}",
                "data": {}
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
    
    def _extract_authenticity_score(self, text: str) -> int:
        """Extract authenticity percentage from JSON response"""
        try:
            # Try to find and parse JSON from the response
            # First, try to extract JSON block
            json_pattern = r'\{[^{}]*"authenticity_score"[^{}]*\}'
            json_match = re.search(json_pattern, text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                try:
                    data = json.loads(json_str)
                    if 'authenticity_score' in data:
                        score = int(data['authenticity_score'])
                        return max(0, min(100, score))  # Ensure score is between 0-100
                except json.JSONDecodeError:
                    pass
            
            # If JSON parsing fails, try to find the score in the text
            # Look for "authenticity_score": number pattern
            score_pattern = r'"authenticity_score":\s*(\d+)'
            score_match = re.search(score_pattern, text)
            if score_match:
                score = int(score_match.group(1))
                return max(0, min(100, score))
                
            # Fallback: look for percentage patterns in text
            patterns = [
                r'(\d+)%为真品',
                r'(\d+)%为真',
                r'真品可能性[：:\\s]*(\d+)%',
                r'真品概率[：:\\s]*(\d+)%',
                r'authenticity_score[：:\\s]*(\d+)',
                r'(\d+)%的可能性',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        score = int(matches[-1])  # Take the last match
                        return max(0, min(100, score))
                    except ValueError:
                        continue
                        
            # Default fallback
            print("Warning: Could not extract authenticity score, using default 50")
            return 50
            
        except Exception as e:
            print(f"Error extracting authenticity score: {e}")
            return 50

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

    def format_evaluation_report(self, report_text: str) -> str:
        """Format the evaluation report with structured simple styling"""
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
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Main sections (一、二、三、四、)
            if any(keyword in line for keyword in ['一、', '二、', '三、', '四、', '第一', '第二', '第三', '第四']):
                content_parts.append(f'''
<div style="margin: 1.5rem 0; padding: 1.5rem; border: 2px solid #e5e7eb; border-radius: 8px; background-color: #f9fafb;">
<h2 style="margin: 0 0 1rem 0; padding: 0; font-weight: bold; font-size: 1.3rem; color: #1f2937; border-bottom: 1px solid #d1d5db; padding-bottom: 0.5rem;">{line}</h2>
''')
                
            elif line.startswith('**') and line.endswith('**'):
                # Subsection headers
                subsection = line[2:-2]
                content_parts.append(f'<h3 style="margin: 1rem 0 0.5rem 0; font-weight: bold; font-size: 1.1rem; color: #374151;">{subsection}</h3>')
                
            elif ':' in line and len(line.split(':')[0]) < 35:
                # Key-value pairs
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    content_parts.append(f'''
<div style="margin: 0.5rem 0; padding: 0.75rem; border-left: 3px solid #3b82f6; background-color: #f8fafc;">
<div style="font-weight: bold; color: #1e40af; margin-bottom: 0.25rem;">{key}</div>
<div style="color: #374151;">{value}</div>
</div>''')
                else:
                    content_parts.append(f'<p style="margin: 0.5rem 0; padding: 0.5rem; color: #374151;">{line}</p>')
                
            elif line.startswith('结论') or '真品可能性' in line or '综合判断' in line:
                # Conclusions
                content_parts.append(f'''
<div style="margin: 1rem 0; padding: 1rem; border: 2px solid #f59e0b; border-radius: 6px; background-color: #fefbf3;">
<div style="font-weight: bold; color: #92400e; margin-bottom: 0.5rem;">🏆 鉴定结论</div>
<p style="margin: 0; color: #92400e; font-weight: bold;">{line}</p>
</div>''')
                
            elif line.startswith('建议') or '注意事项' in line:
                # Recommendations
                content_parts.append(f'''
<div style="margin: 1rem 0; padding: 1rem; border: 2px solid #10b981; border-radius: 6px; background-color: #f0fdf4;">
<div style="font-weight: bold; color: #065f46; margin-bottom: 0.5rem;">💡 专业建议</div>
<p style="margin: 0; color: #065f46; font-weight: bold;">{line}</p>
</div>''')
                
            else:
                # Regular paragraphs
                content_parts.append(f'<p style="margin: 0.5rem 0; padding: 0.25rem; line-height: 1.6; color: #374151;">{line}</p>')
        
        # Close any open section divs
        if content_parts and '<div style="margin: 1.5rem 0; padding: 1.5rem; border: 2px solid #e5e7eb' in str(content_parts):
            content_parts.append('</div>')
        
        content = '\n'.join(content_parts)
        
        # Create the structured simple report
        return f'''
<div style="max-width: 100%; margin: 0 auto; font-family: system-ui, -apple-system, sans-serif;">

<!-- Header Section -->
<div style="text-align: center; margin-bottom: 2rem; padding: 2rem; border: 2px solid #3b82f6; border-radius: 10px; background-color: #eff6ff;">
<h1 style="margin: 0 0 0.5rem 0; font-size: 1.8rem; font-weight: bold; color: #1e40af;">🏺 古董文物鉴定报告</h1>
<p style="margin: 0; color: #3730a3; font-weight: 600;">AI智能分析评估</p>
<div style="margin-top: 1rem; padding: 0.5rem 1rem; background-color: #dbeafe; border-radius: 20px; display: inline-block;">
<span style="color: #1e40af; font-size: 0.9rem; font-weight: 600;">📅 {timestamp}</span>
</div>
</div>

<!-- Content Section -->
<div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 2rem;">
{content}
</div>

<!-- Footer Section -->
<div style="margin-top: 2rem; padding: 1.5rem; background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; text-align: center;">
<div style="padding: 1rem; border: 1px solid #d1d5db; border-radius: 6px; background-color: #ffffff;">
<p style="margin: 0; color: #374151; font-size: 0.9rem;">
<strong style="color: #dc2626;">⚠️ 重要声明：</strong> 
本报告基于AI深度学习分析生成，仅供专业参考。最终鉴定结果需结合实物检测，建议咨询权威古董鉴定机构进行确认。
</p>
</div>
<div style="margin-top: 1rem; color: #6b7280; font-size: 0.8rem;">
<span style="margin: 0 1rem;">🤖 GPT-o3</span>
<span style="margin: 0 1rem;">🔒 安全</span>
<span style="margin: 0 1rem;">🏺 专业</span>
</div>
</div>

</div>
'''