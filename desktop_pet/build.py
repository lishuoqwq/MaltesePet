"""
打包脚本 - 将Python应用程序打包成exe文件
"""
import os
import sys
import glob
import shutil
from pathlib import Path

def build_exe():
    """打包应用程序为可执行文件"""
    # 确定资源文件路径
    base_dir = Path(__file__).parent.absolute()
    src_dir = base_dir / 'src'
    resources_dir = base_dir / 'resources'
    gifs_dir = resources_dir / 'gifs'
    icons_dir = resources_dir / 'icons'
    build_dir = base_dir / 'build'
    dist_dir = base_dir / 'dist'
    
    # 确保资源目录存在
    gifs_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查资源文件
    icon_files = list(icons_dir.glob("*.jpg")) + list(icons_dir.glob("*.png")) + list(icons_dir.glob("*.ico"))
    icon_path = None
    icon_str = ""
    
    if icon_files:
        icon_path = str(icon_files[0])
        print(f"使用图标: {icon_path}")
        icon_str = f"icon='{icon_path}',"
    else:
        print("警告: 未找到图标文件")
    
    # 检查是否安装了PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        os.system(f"{sys.executable} -m pip install pyinstaller")
    
    # 清理旧的构建文件
    for path in [build_dir, dist_dir]:
        if path.exists():
            shutil.rmtree(path)
            print(f"已清理: {path}")
    
    # 构建命令
    build_cmd = [
        f"{sys.executable}",
        "-m",
        "PyInstaller",
        "--noconfirm",  # 不询问确认
        "--clean",      # 清理之前的构建文件
        "--onefile",    # 生成单个可执行文件
        "--windowed",   # 不显示控制台窗口
        f"--name=线条小狗桌面宠物",  # 输出文件名
        f"--add-data={gifs_dir};resources/gifs",  # 添加GIF资源
        f"--add-data={icons_dir};resources/icons",  # 添加图标资源
    ]
    
    # 添加图标
    if icon_path:
        build_cmd.append(f"--icon={icon_path}")
    
    # 添加主程序文件
    build_cmd.append(f"{src_dir}/puppy_pet.py")
    
    # 执行构建命令
    print("正在构建可执行文件...")
    print(" ".join(build_cmd))
    build_cmd_str = " ".join(build_cmd)
    os.system(build_cmd_str)
    
    # 检查构建结果
    exe_file = dist_dir / "线条小狗桌面宠物.exe"
    if exe_file.exists():
        print(f"构建成功: {exe_file}")
        print(f"文件大小: {exe_file.stat().st_size / (1024*1024):.2f} MB")
    else:
        print("构建失败，请查看错误信息。")
    
    print("构建过程完成。")

if __name__ == "__main__":
    build_exe() 