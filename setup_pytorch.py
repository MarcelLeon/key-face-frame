#!/usr/bin/env python3
"""
PyTorch 智能安装脚本

自动检测系统硬件并安装最优的 PyTorch 版本：
- NVIDIA GPU: CUDA 版本
- Apple Silicon: MPS 加速版本
- 其他: CPU 版本

解决 Issue #2: 自动检测 CUDA 并安装对应版本
"""

import os
import platform
import subprocess
import sys


def run_command(cmd: str, capture_output: bool = True) -> tuple[bool, str]:
    """
    运行系统命令

    Args:
        cmd: 命令字符串
        capture_output: 是否捕获输出

    Returns:
        (success, output)
    """
    try:
        if capture_output:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0, result.stdout + result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=30)
            return result.returncode == 0, ""
    except Exception as e:
        return False, str(e)


def check_nvidia_gpu() -> tuple[bool, str]:
    """
    检测 NVIDIA GPU 和 CUDA 支持

    Returns:
        (has_cuda, cuda_version)
    """
    # 检查 nvidia-smi 命令
    success, output = run_command("nvidia-smi")
    if not success:
        return False, ""

    # 尝试从 nvidia-smi 输出中提取 CUDA 版本
    for line in output.split("\n"):
        if "CUDA Version:" in line:
            try:
                version = line.split("CUDA Version:")[-1].strip().split()[0]
                return True, version
            except:
                pass

    return True, "unknown"


def check_apple_silicon() -> bool:
    """
    检测是否为 Apple Silicon (M系列芯片)

    Returns:
        是否为 Apple Silicon
    """
    if platform.system() != "Darwin":
        return False

    success, output = run_command("uname -m")
    return "arm64" in output.lower()


def get_pytorch_install_command() -> tuple[str, str]:
    """
    根据系统硬件返回最优的 PyTorch 安装命令

    Returns:
        (description, install_command)
    """
    system = platform.system()

    # 检查 NVIDIA GPU
    has_cuda, cuda_version = check_nvidia_gpu()
    if has_cuda:
        # 根据 CUDA 版本选择合适的 PyTorch
        major_version = cuda_version.split(".")[0] if cuda_version != "unknown" else "12"

        if major_version >= "12":
            desc = f"检测到 NVIDIA GPU (CUDA {cuda_version}) - 安装 CUDA 12.1 版本"
            cmd = "pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121"
        elif major_version >= "11":
            desc = f"检测到 NVIDIA GPU (CUDA {cuda_version}) - 安装 CUDA 11.8 版本"
            cmd = "pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118"
        else:
            desc = f"检测到旧版 CUDA ({cuda_version}) - 安装 CPU 版本"
            cmd = "pip install torch torchvision"

        return desc, cmd

    # 检查 Apple Silicon
    if check_apple_silicon():
        desc = "检测到 Apple Silicon (M系列芯片) - 安装 MPS 加速版本"
        cmd = "pip install torch torchvision"
        return desc, cmd

    # 默认 CPU 版本
    desc = f"未检测到 GPU - 安装 CPU 版本 ({system})"
    cmd = "pip install torch torchvision"
    return desc, cmd


def verify_pytorch_installation():
    """
    验证 PyTorch 安装并显示加速器信息
    """
    print("\n" + "=" * 60)
    print("验证 PyTorch 安装...")
    print("=" * 60)

    verify_script = """
import torch

print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA 版本: {torch.version.cuda}")
    print(f"GPU 数量: {torch.cuda.device_count()}")
    print(f"GPU 名称: {torch.cuda.get_device_name(0)}")

# 检查 MPS (Apple Silicon)
if hasattr(torch.backends, 'mps'):
    print(f"MPS 可用: {torch.backends.mps.is_available()}")

# 推荐的设备
if torch.cuda.is_available():
    device = "cuda"
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"\\n推荐使用设备: {device}")
"""

    try:
        result = subprocess.run(
            [sys.executable, "-c", verify_script], capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print("⚠️  验证时出现警告:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 验证失败: {e}")


def main():
    print("=" * 60)
    print("PyTorch 智能安装脚本")
    print("=" * 60)
    print()

    # 检测系统
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version.split()[0]}")
    print()

    # 检测硬件并获取安装命令
    desc, install_cmd = get_pytorch_install_command()

    print("🔍 硬件检测结果:")
    print(f"   {desc}")
    print()

    print("📦 将要执行的安装命令:")
    print(f"   {install_cmd}")
    print()

    # 确认安装
    response = input("是否继续安装? (y/n): ").strip().lower()
    if response not in ["y", "yes", "是"]:
        print("❌ 安装已取消")
        return

    # 先卸载已有的 torch
    print("\n" + "=" * 60)
    print("卸载现有 PyTorch...")
    print("=" * 60)
    subprocess.run(
        "pip uninstall -y torch torchvision torchaudio",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 安装新版本
    print("\n" + "=" * 60)
    print("安装 PyTorch...")
    print("=" * 60)
    success, _ = run_command(install_cmd, capture_output=False)

    if not success:
        print("\n❌ 安装失败！")
        print("请检查网络连接或手动安装:")
        print(f"   {install_cmd}")
        sys.exit(1)

    # 验证安装
    verify_pytorch_installation()

    print("\n" + "=" * 60)
    print("✅ PyTorch 安装完成！")
    print("=" * 60)
    print()
    print("提示:")
    print("  - 如需重新安装其他版本，请重新运行此脚本")
    print("  - GPU 版本需要安装对应的 CUDA 驱动")
    print("  - 详见: https://pytorch.org/get-started/locally/")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消安装")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
