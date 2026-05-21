#!/usr/bin/env python3
"""
自动化发布脚本
Automate Release Script

功能：
1. 版本号管理（语义化版本）
2. 自动生成变更日志
3. 构建分发包
4. 创建Git标签
5. 发布到PyPI
6. 创建GitHub Release

使用方式：
    python scripts/auto_release.py [options]

选项：
    --type      发布类型：major, minor, patch (默认: patch)
    --dry-run   预览模式，不执行实际操作
    --skip-tests 跳过测试
    --skip-build 跳过构建
    --pypi       发布到PyPI
    --github     创建GitHub Release
"""

import os
import sys
import re
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def log_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")

def log_warning(msg):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

class ReleaseManager:
    def __init__(self, dry_run=False, skip_tests=False, skip_build=False):
        self.dry_run = dry_run
        self.skip_tests = skip_tests
        self.skip_build = skip_build
        self.project_root = Path(__file__).parent.parent
        self.version_file = self.project_root / "pyproject.toml"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        self.current_version = self._get_current_version()
        self.new_version = None
        
    def _get_current_version(self):
        """获取当前版本号"""
        content = self.version_file.read_text()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
        raise ValueError("无法在pyproject.toml中找到版本号")
    
    def _parse_version(self, version_str):
        """解析版本字符串"""
        parts = version_str.split('.')
        return [int(p) for p in parts] + [0, 0, 0][:3-len(parts)]
    
    def _bump_version(self, release_type):
        """根据发布类型更新版本号"""
        major, minor, patch = self._parse_version(self.current_version)
        
        if release_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif release_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def _update_version_file(self, new_version):
        """更新pyproject.toml中的版本号"""
        content = self.version_file.read_text()
        new_content = re.sub(
            r'(version\s*=\s*")[^"]+(")',
            rf'\g<1>{new_version}\g<2>',
            content
        )
        self.version_file.write_text(new_content)
        log_info(f"版本号已更新: {self.current_version} -> {new_version}")
    
    def _generate_changelog(self):
        """生成变更日志"""
        log_info("生成变更日志...")
        
        # 获取自上次发布以来的提交
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '--since="2 weeks ago"', '-20'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            changes = {
                'added': [],
                'changed': [],
                'fixed': [],
                'removed': []
            }
            
            for commit in commits:
                if commit:
                    msg = commit.split(' ', 1)[1] if ' ' in commit else commit
                    # 简单分类
                    if any(kw in msg.lower() for kw in ['add', 'new', 'feat']):
                        changes['added'].append(f"- {msg}")
                    elif any(kw in msg.lower() for kw in ['fix', 'bug', 'patch']):
                        changes['fixed'].append(f"- {msg}")
                    elif any(kw in msg.lower() for kw in ['remove', 'delete']):
                        changes['removed'].append(f"- {msg}")
                    else:
                        changes['changed'].append(f"- {msg}")
            
            # 生成CHANGELOG
            changelog = f"""# 更新日志

## [{self.new_version}] - {datetime.now().strftime('%Y-%m-%d')}

"""
            if changes['added']:
                changelog += "### ✨ 新增功能\n\n" + '\n'.join(changes['added']) + "\n\n"
            if changes['changed']:
                changelog += "### 🔄 功能改进\n\n" + '\n'.join(changes['changed']) + "\n\n"
            if changes['fixed']:
                changelog += "### 🐛 问题修复\n\n" + '\n'.join(changes['fixed']) + "\n\n"
            if changes['removed']:
                changelog += "### 🗑️ 移除功能\n\n" + '\n'.join(changes['removed']) + "\n\n"
            
            # 追加现有CHANGELOG
            if self.changelog_file.exists():
                existing_changelog = self.changelog_file.read_text()
                changelog += existing_changelog
            
            self.changelog_file.write_text(changelog)
            log_success("变更日志已更新")
            
        except subprocess.CalledProcessError as e:
            log_warning(f"无法获取git提交历史: {e}")
    
    def run_tests(self):
        """运行测试"""
        if self.skip_tests:
            log_warning("跳过测试")
            return True
        
        log_info("运行测试...")
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
                cwd=self.project_root
            )
            if result.returncode == 0:
                log_success("所有测试通过！")
                return True
            else:
                log_error("测试失败！")
                return False
        except Exception as e:
            log_error(f"测试执行失败: {e}")
            return False
    
    def build_package(self):
        """构建分发包"""
        if self.skip_build:
            log_warning("跳过构建")
            return True
        
        log_info("构建分发包...")
        try:
            # 清理旧构建
            subprocess.run(['rm', '-rf', 'dist/', 'build/', '*.egg-info'], cwd=self.project_root)
            
            # 构建源码包和wheel
            subprocess.run(
                ['python', '-m', 'build'],
                cwd=self.project_root,
                check=True
            )
            
            log_success("构建完成！")
            return True
        except subprocess.CalledProcessError as e:
            log_error(f"构建失败: {e}")
            return False
    
    def publish_pypi(self):
        """发布到PyPI"""
        log_info("发布到PyPI...")
        try:
            # 先发布到TestPyPI
            log_info("发布到TestPyPI...")
            result = subprocess.run(
                ['python', '-m', 'twine', 'upload', '--repository', 'testpypi', 'dist/*'],
                cwd=self.project_root,
                input='y\n'  # 自动确认
            )
            
            if result.returncode == 0:
                log_success("已发布到TestPyPI")
                
                # 询问是否发布到正式PyPI
                print("\n是否发布到正式PyPI? (y/N): ", end='')
                if input().lower() == 'y':
                    log_info("发布到正式PyPI...")
                    result = subprocess.run(
                        ['python', '-m', 'twine', 'upload', 'dist/*'],
                        cwd=self.project_root,
                        input='y\n'
                    )
                    if result.returncode == 0:
                        log_success("已发布到PyPI！")
                        return True
                
                return True
            else:
                log_error("发布到TestPyPI失败")
                return False
                
        except Exception as e:
            log_error(f"PyPI发布失败: {e}")
            return False
    
    def create_github_release(self):
        """创建GitHub Release"""
        log_info("创建GitHub Release...")
        try:
            # 添加git标签
            tag_name = f"v{self.new_version}"
            
            # 检查标签是否存在
            result = subprocess.run(
                ['git', 'tag', '-l', tag_name],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout.strip():
                log_warning(f"标签 {tag_name} 已存在")
                return True
            
            # 创建标签
            subprocess.run(
                ['git', 'tag', '-a', tag_name, '-m', f'发布版本 {self.new_version}'],
                cwd=self.project_root
            )
            log_info(f"已创建标签: {tag_name}")
            
            # 推送到远程
            log_info("推送标签到远程...")
            subprocess.run(
                ['git', 'push', 'origin', tag_name],
                cwd=self.project_root
            )
            
            log_success("GitHub Release 创建完成！")
            return True
            
        except Exception as e:
            log_error(f"GitHub Release 创建失败: {e}")
            return False
    
    def commit_changes(self):
        """提交版本更新"""
        log_info("提交更改...")
        try:
            subprocess.run(['git', 'add', 'pyproject.toml', 'CHANGELOG.md'], cwd=self.project_root)
            subprocess.run(
                ['git', 'commit', '-m', f'chore: 准备发布 v{self.new_version}'],
                cwd=self.project_root
            )
            subprocess.run(['git', 'push'], cwd=self.project_root)
            log_success("更改已提交并推送")
            return True
        except Exception as e:
            log_error(f"提交失败: {e}")
            return False
    
    def release(self, release_type):
        """执行完整的发布流程"""
        print("\n" + "="*50)
        print("       NFO to VSMETA 自动化发布")
        print("="*50 + "\n")
        
        self.new_version = self._bump_version(release_type)
        
        log_info(f"当前版本: {self.current_version}")
        log_info(f"新版本: {self.new_version}")
        log_info(f"发布类型: {release_type}")
        
        if self.dry_run:
            log_warning("预览模式 - 不会执行实际操作")
            return
        
        # 确认发布
        print(f"\n确认发布版本 {self.new_version}? (y/N): ", end='')
        if input().lower() != 'y':
            log_info("发布已取消")
            return
        
        # 执行发布流程
        steps = [
            ("运行测试", self.run_tests),
            ("更新版本号", lambda: self._update_version_file(self.new_version)),
            ("生成变更日志", self._generate_changelog),
            ("提交更改", self.commit_changes),
            ("构建包", self.build_package),
            ("创建GitHub Release", self.create_github_release),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*40}")
            log_info(f"执行: {step_name}")
            print(f"{'='*40}")
            
            if not step_func():
                log_error(f"步骤 '{step_name}' 失败")
                if not step_func == self.run_tests:
                    proceed = input("继续执行? (y/N): ").lower() == 'y'
                    if not proceed:
                        sys.exit(1)
        
        log_success("\n" + "="*50)
        log_success("   发布完成！")
        log_success("="*50)
        print(f"\n新版本: v{self.new_version}")
        print(f"下一步:")
        print(f"  1. 检查 GitHub: https://github.com/1525745393/TRAE--AI-NFO-to-VSMETA/releases")
        print(f"  2. 如需发布到PyPI，运行: python scripts/auto_release.py --pypi")


def main():
    parser = argparse.ArgumentParser(description='自动化发布脚本')
    parser.add_argument('--type', '-t', 
                        choices=['major', 'minor', 'patch'],
                        default='patch',
                        help='发布类型 (默认: patch)')
    parser.add_argument('--dry-run', '-d',
                        action='store_true',
                        help='预览模式，不执行实际操作')
    parser.add_argument('--skip-tests',
                        action='store_true',
                        help='跳过测试')
    parser.add_argument('--skip-build',
                        action='store_true',
                        help='跳过构建')
    parser.add_argument('--pypi',
                        action='store_true',
                        help='发布到PyPI')
    parser.add_argument('--github',
                        action='store_true',
                        help='创建GitHub Release')
    
    args = parser.parse_args()
    
    manager = ReleaseManager(
        dry_run=args.dry_run,
        skip_tests=args.skip_tests,
        skip_build=args.skip_build
    )
    
    if args.pypi:
        manager.publish_pypi()
    else:
        manager.release(args.type)


if __name__ == '__main__':
    main()
