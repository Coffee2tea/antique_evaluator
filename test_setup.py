#!/usr/bin/env python3
"""
测试脚本 - 验证古董鉴定专家应用的环境配置
Test script to validate the Antique Evaluator application setup
"""

import sys
import importlib
from typing import List, Tuple

def test_python_version() -> Tuple[bool, str]:
    """测试Python版本"""
    version = sys.version_info
    if version >= (3, 8):
        return True, f"✅ Python版本: {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要 3.8+)"

def test_dependencies() -> List[Tuple[bool, str]]:
    """测试依赖包安装"""
    dependencies = [
        ('streamlit', 'streamlit'),
        ('requests', 'requests'), 
        ('bs4', 'beautifulsoup4'),
        ('openai', 'openai'),
        ('dotenv', 'python-dotenv'),
        ('lxml', 'lxml'),
        ('PIL', 'Pillow')  # Pillow
    ]
    
    results = []
    
    for module_name, package_name in dependencies:
        try:
            importlib.import_module(module_name)
            results.append((True, f"✅ {package_name} 已安装"))
        except ImportError:
            results.append((False, f"❌ {package_name} 未安装"))
    
    return results

def test_config_files() -> List[Tuple[bool, str]]:
    """测试配置文件"""
    import os
    
    results = []
    
    # 检查必要文件
    required_files = ['app.py', 'evaluator.py', 'config.py']
    
    for file in required_files:
        if os.path.exists(file):
            results.append((True, f"✅ {file} 存在"))
        else:
            results.append((False, f"❌ {file} 不存在"))
    
    # 检查.env文件
    if os.path.exists('.env'):
        results.append((True, "✅ .env 文件存在"))
        
        # 检查API密钥
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            results.append((True, "✅ OpenAI API密钥已配置"))
        else:
            results.append((False, "❌ OpenAI API密钥未配置或使用默认值"))
    else:
        results.append((False, "❌ .env 文件不存在"))
    
    return results

def test_streamlit_config():
    """测试Streamlit配置"""
    try:
        import streamlit as st
        return True, "✅ Streamlit可以导入"
    except Exception as e:
        return False, f"❌ Streamlit导入失败: {str(e)}"

def main():
    """运行所有测试"""
    print("🏺 古董鉴定专家 - 环境测试")
    print("=" * 50)
    
    # 测试Python版本
    success, message = test_python_version()
    print(message)
    
    if not success:
        print("\n❌ Python版本不满足要求，请升级到3.8或更高版本")
        return
    
    print("\n📦 依赖包测试:")
    print("-" * 30)
    
    # 测试依赖
    dep_results = test_dependencies()
    all_deps_ok = True
    
    for success, message in dep_results:
        print(message)
        if not success:
            all_deps_ok = False
    
    if not all_deps_ok:
        print("\n❌ 请安装缺失的依赖包:")
        print("pip install -r requirements.txt")
        return
    
    print("\n📁 配置文件测试:")
    print("-" * 30)
    
    # 测试配置文件
    config_results = test_config_files()
    all_config_ok = True
    
    for success, message in config_results:
        print(message)
        if not success:
            all_config_ok = False
    
    print("\n🖥️ Streamlit测试:")
    print("-" * 30)
    
    # 测试Streamlit
    success, message = test_streamlit_config()
    print(message)
    
    print("\n" + "=" * 50)
    
    if all_deps_ok and all_config_ok and success:
        print("🎉 所有测试通过！您可以运行以下命令启动应用:")
        print("streamlit run app.py")
    else:
        print("⚠️ 存在配置问题，请根据上述提示进行修复")
        
        if not all_config_ok:
            print("\n📋 配置建议:")
            print("1. 确保所有Python文件都存在")
            print("2. 创建.env文件并配置OpenAI API密钥")
            print("3. 参考README.md获取详细配置说明")

if __name__ == "__main__":
    main() 