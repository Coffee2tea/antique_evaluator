#!/usr/bin/env python3
"""
启动脚本 - 古董鉴定专家应用
Launch script for the Antique Evaluator application
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_requirements():
    """检查基本要求"""
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    
    # 检查必要文件
    required_files = ['app.py', 'config.py', 'evaluator.py']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ 错误: 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    return True

def install_dependencies():
    """安装依赖包"""
    if not Path('requirements.txt').exists():
        print("❌ 错误: requirements.txt文件不存在")
        return False
    
    print("📦 正在安装依赖包...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依赖包安装完成")
            return True
        else:
            print(f"❌ 依赖包安装失败: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ 安装过程中发生错误: {e}")
        return False

def check_env_file():
    """检查环境变量文件"""
    if not Path('.env').exists():
        print("⚠️  警告: .env文件不存在")
        print("请创建.env文件并配置您的OpenAI API密钥:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        print("\n您也可以在应用启动后在侧边栏输入API密钥")
        return False
    
    # 检查API密钥
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_api_key_here':
            print("⚠️  警告: OpenAI API密钥未配置")
            print("请在.env文件中设置正确的API密钥，或在应用启动后在侧边栏输入")
            return False
        
        print("✅ 环境变量配置正确")
        return True
        
    except ImportError:
        print("⚠️  python-dotenv未安装，将尝试安装依赖包...")
        return False
    except Exception as e:
        print(f"⚠️  检查环境变量时发生错误: {e}")
        return False

def launch_streamlit():
    """启动Streamlit应用"""
    print("🚀 正在启动古董鉴定专家应用...")
    print("应用将在浏览器中自动打开")
    print("如果没有自动打开，请访问: http://localhost:8501")
    print("\n按 Ctrl+C 停止应用\n")
    
    try:
        # 启动Streamlit
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.headless', 'false',
            '--server.port', '8501',
            '--browser.gatherUsageStats', 'false'
        ])
        
        # 等待一段时间让Streamlit启动
        time.sleep(3)
        
        # 尝试打开浏览器
        try:
            webbrowser.open('http://localhost:8501')
        except:
            pass  # 如果无法打开浏览器也不影响应用运行
        
        # 等待进程结束
        process.wait()
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"❌ 启动应用时发生错误: {e}")

def main():
    """主函数"""
    print("🏺 古董鉴定专家 - 启动器")
    print("=" * 50)
    
    # 检查基本要求
    if not check_requirements():
        print("\n请修复上述问题后重新运行")
        return
    
    # 尝试导入Streamlit来检查是否已安装
    try:
        import streamlit
        print("✅ Streamlit已安装")
    except ImportError:
        print("📦 Streamlit未安装，正在安装依赖包...")
        if not install_dependencies():
            print("❌ 安装失败，请手动运行: pip install -r requirements.txt")
            return
    
    # 检查环境文件
    env_ok = check_env_file()
    
    # 询问是否继续
    if not env_ok:
        response = input("\n是否继续启动应用? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("👋 启动已取消")
            return
    
    print("\n" + "=" * 50)
    
    # 启动应用
    launch_streamlit()

if __name__ == "__main__":
    main() 