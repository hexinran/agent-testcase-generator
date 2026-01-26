#!/usr/bin/env python3
"""
统一的自定义 Check 验证模块

所有 golden_check 的验证逻辑集中在这里，方便：
1. 数据送标时检查
2. SFT 轨迹收集时验证
3. 评测时使用

使用方式:
    from custom_checks import verify_check
    passed, detail = verify_check(check_type, params, sandbox_dir, trajectory=None)
"""

import os
import re
import json
import glob as glob_module
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any


# =============================================================================
# 核心验证函数
# =============================================================================

def verify_check(
    check_type: str,
    params: dict,
    sandbox_dir: Path,
    trajectory: Optional[List[dict]] = None
) -> Tuple[bool, str]:
    """
    统一的 check 验证入口

    Args:
        check_type: check 类型名
        params: check 参数
        sandbox_dir: sandbox 目录路径
        trajectory: 可选的轨迹数据（用于检查 tool_used 等）

    Returns:
        (passed, detail): 是否通过，详细说明
    """
    # 路径处理：替换 {{SANDBOX}} 占位符
    params = _normalize_params(params, sandbox_dir)

    # 查找对应的验证函数
    check_func = CHECK_REGISTRY.get(check_type)

    if check_func:
        try:
            return check_func(sandbox_dir, params, trajectory)
        except Exception as e:
            return False, f"check execution error: {e}"
    else:
        # 未知类型，标记为需要人工验证
        return True, f"unknown check type '{check_type}' - manual review needed"


def _normalize_params(params: dict, sandbox_dir: Path) -> dict:
    """规范化参数，处理路径占位符"""
    normalized = {}
    for k, v in params.items():
        if isinstance(v, str):
            # 替换占位符
            v = v.replace("{{SANDBOX}}", str(sandbox_dir))
            v = v.replace("${SANDBOX}", str(sandbox_dir))
            # 相对路径转绝对路径
            if k in ('path', 'file', 'file_path') and v and not Path(v).is_absolute():
                v = str(sandbox_dir / v)
        normalized[k] = v
    return normalized


def _resolve_path(path: str, sandbox_dir: Path) -> Path:
    """解析路径，支持相对路径和绝对路径"""
    if not path:
        return sandbox_dir
    p = Path(path)
    if p.is_absolute():
        return p
    return sandbox_dir / path


# =============================================================================
# 标准类型验证函数
# =============================================================================

def check_file_exists(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件是否存在"""
    path = params.get('path', '')
    full_path = _resolve_path(path, sandbox_dir)

    if full_path.exists():
        return True, f"file exists: {path}"
    return False, f"file not found: {path}"


def check_file_content_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件内容是否包含关键词"""
    path = params.get('path', params.get('path_pattern', ''))
    keyword = params.get('keyword', '')
    case_insensitive = params.get('case_insensitive', False)

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    try:
        content = full_path.read_text(encoding='utf-8', errors='replace')
        if case_insensitive:
            found = keyword.lower() in content.lower()
        else:
            found = keyword in content

        if found:
            return True, f"keyword '{keyword}' found in {path}"
        return False, f"keyword '{keyword}' not found in {path}"
    except Exception as e:
        return False, f"error reading file: {e}"


def check_file_content_not_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件内容不包含关键词"""
    path = params.get('path', '')
    keyword = params.get('keyword', params.get('pattern', ''))
    case_insensitive = params.get('case_insensitive', False)

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return True, f"file not found (OK for not_contains): {path}"

    try:
        content = full_path.read_text(encoding='utf-8', errors='replace')
        if case_insensitive:
            found = keyword.lower() in content.lower()
        else:
            found = keyword in content

        if not found:
            return True, f"keyword '{keyword}' correctly not in {path}"
        return False, f"keyword '{keyword}' unexpectedly found in {path}"
    except Exception as e:
        return False, f"error reading file: {e}"


def check_file_content_matches(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件内容是否匹配正则表达式"""
    path = params.get('path', '')
    pattern = params.get('pattern', '')

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    try:
        content = full_path.read_text(encoding='utf-8', errors='replace')
        if re.search(pattern, content, re.MULTILINE | re.DOTALL):
            return True, f"pattern matched in {path}"
        return False, f"pattern not matched in {path}"
    except re.error as e:
        return False, f"invalid regex: {e}"
    except Exception as e:
        return False, f"error: {e}"


# =============================================================================
# file_content 扩展类型
# =============================================================================

def check_file_content_match(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """file_content_match - 类似 file_content_matches，支持 regex 或 pattern 参数"""
    path = params.get('path', '')
    pattern = params.get('pattern', params.get('regex', ''))

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    try:
        content = full_path.read_text(encoding='utf-8', errors='replace')
        if re.search(pattern, content, re.MULTILINE | re.DOTALL):
            return True, f"pattern '{pattern[:50]}...' matched"
        return False, f"pattern not matched"
    except Exception as e:
        return False, f"error: {e}"


def check_file_content_regex(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """file_content_regex - 同 file_content_match"""
    return check_file_content_match(sandbox_dir, params, trajectory)


# =============================================================================
# glob 相关类型
# =============================================================================

def check_glob_result_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 glob 结果是否包含预期文件"""
    pattern = params.get('pattern', '')
    path = params.get('path', '')
    expected_files = params.get('expected_files', [])
    expected_file = params.get('expected_file', '')
    keyword = params.get('keyword', '')

    # 构建 glob 路径
    base_path = _resolve_path(path, sandbox_dir) if path else sandbox_dir
    glob_pattern = str(base_path / pattern) if pattern else str(base_path / '**/*')

    try:
        matched_files = glob_module.glob(glob_pattern, recursive=True)
        matched_names = [Path(f).name for f in matched_files]
        matched_rel = [str(Path(f).relative_to(sandbox_dir)) for f in matched_files if Path(f).is_relative_to(sandbox_dir)]

        # 检查预期文件
        if expected_file:
            expected_files = [expected_file]

        if expected_files:
            found = []
            not_found = []
            for ef in expected_files:
                ef_name = Path(ef).name
                if ef in matched_rel or ef_name in matched_names or any(ef in m for m in matched_rel):
                    found.append(ef)
                else:
                    not_found.append(ef)

            if not_found:
                return False, f"files not found: {not_found}"
            return True, f"all expected files found: {found}"

        # 检查关键词
        if keyword:
            if any(keyword in f for f in matched_rel + matched_names):
                return True, f"keyword '{keyword}' found in glob results"
            return False, f"keyword '{keyword}' not in glob results"

        return True, f"glob returned {len(matched_files)} files"
    except Exception as e:
        return False, f"glob error: {e}"


def check_glob_result_not_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 glob 结果不包含某文件"""
    pattern = params.get('pattern', '')
    path = params.get('path', '')
    unexpected_file = params.get('unexpected_file', params.get('expected_file', ''))

    base_path = _resolve_path(path, sandbox_dir) if path else sandbox_dir
    glob_pattern = str(base_path / pattern) if pattern else str(base_path / '**/*')

    try:
        matched_files = glob_module.glob(glob_pattern, recursive=True)
        matched_names = [Path(f).name for f in matched_files]

        if unexpected_file:
            uf_name = Path(unexpected_file).name
            if uf_name in matched_names:
                return False, f"unexpected file found: {unexpected_file}"

        return True, f"unexpected file correctly absent"
    except Exception as e:
        return False, f"glob error: {e}"


def check_glob_returns_files(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 glob 返回文件数量或特定文件"""
    pattern = params.get('pattern', '')
    path = params.get('path', '')
    expected_count = params.get('expected_count')
    expected_files = params.get('expected_files', [])

    base_path = _resolve_path(path, sandbox_dir) if path else sandbox_dir
    glob_pattern = str(base_path / pattern) if pattern else str(base_path / '**/*')

    try:
        matched_files = glob_module.glob(glob_pattern, recursive=True)

        if expected_count is not None:
            if len(matched_files) >= expected_count:
                return True, f"found {len(matched_files)} files (expected >= {expected_count})"
            return False, f"found {len(matched_files)} files (expected >= {expected_count})"

        if expected_files:
            return check_glob_result_contains(sandbox_dir, params, trajectory)

        return True, f"glob returned {len(matched_files)} files"
    except Exception as e:
        return False, f"glob error: {e}"


def check_glob_result_count(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 glob 结果数量"""
    pattern = params.get('pattern', '')
    min_count = params.get('min_count', 1)

    glob_pattern = str(sandbox_dir / pattern) if pattern else str(sandbox_dir / '**/*')

    try:
        matched_files = glob_module.glob(glob_pattern, recursive=True)
        if len(matched_files) >= min_count:
            return True, f"found {len(matched_files)} files (>= {min_count})"
        return False, f"found {len(matched_files)} files (< {min_count})"
    except Exception as e:
        return False, f"glob error: {e}"


def check_glob_pattern_matches(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 glob 模式匹配预期文件列表"""
    expected_files = params.get('expected_files', [])
    return check_glob_result_contains(sandbox_dir, {'expected_files': expected_files, 'pattern': '**/*'}, trajectory)


def check_glob_executed(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查是否执行了 glob"""
    pattern_contains = params.get('pattern_contains', '')
    # 需要检查轨迹
    if trajectory:
        for step in trajectory:
            if step.get('tool') == 'Glob':
                tool_input = step.get('input', {})
                if isinstance(tool_input, dict):
                    pattern = tool_input.get('pattern', '')
                    if pattern_contains in pattern:
                        return True, f"Glob executed with pattern containing '{pattern_contains}'"
        return False, f"Glob with pattern '{pattern_contains}' not found in trajectory"
    return True, "glob execution check skipped (no trajectory)"


def check_glob_used(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查是否使用了 glob 工具"""
    if trajectory:
        for step in trajectory:
            if step.get('tool') == 'Glob':
                return True, "Glob tool was used"
        return False, "Glob tool was not used"
    return True, "glob_used check skipped (no trajectory)"


# =============================================================================
# grep 相关类型
# =============================================================================

def check_grep_output_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 grep 输出包含预期内容"""
    pattern = params.get('pattern', '')
    path = params.get('path', '')
    expected = params.get('expected', params.get('expected_content', params.get('expected_substring', '')))
    expected_file = params.get('expected_file', '')
    expected_files = params.get('expected_files', [])

    search_path = _resolve_path(path, sandbox_dir) if path else sandbox_dir

    try:
        # 使用 grep 搜索
        cmd = ['grep', '-r', '-l', pattern, str(search_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        matched_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # 检查预期文件
        if expected_file:
            if any(expected_file in f for f in matched_files):
                return True, f"pattern found in {expected_file}"
            return False, f"pattern not found in {expected_file}"

        if expected_files:
            found = [ef for ef in expected_files if any(ef in f for f in matched_files)]
            if len(found) == len(expected_files):
                return True, f"pattern found in all expected files"
            return False, f"pattern not found in some files"

        # 检查内容
        if expected:
            cmd2 = ['grep', '-r', pattern, str(search_path)]
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            if expected in result2.stdout:
                return True, f"expected content '{expected[:50]}...' found"
            return False, f"expected content not found"

        if matched_files:
            return True, f"grep found matches in {len(matched_files)} files"
        return False, "grep found no matches"
    except Exception as e:
        return False, f"grep error: {e}"


def check_grep_result_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """同 grep_output_contains"""
    return check_grep_output_contains(sandbox_dir, params, trajectory)


def check_grep_pattern_found(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 grep 模式是否被找到"""
    pattern = params.get('pattern', '')
    path = params.get('path', '')

    search_path = _resolve_path(path, sandbox_dir) if path else sandbox_dir

    try:
        cmd = ['grep', '-r', '-l', pattern, str(search_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return True, f"pattern '{pattern}' found"
        return False, f"pattern '{pattern}' not found"
    except Exception as e:
        return False, f"grep error: {e}"


def check_grep_finds_content(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """同 grep_output_contains"""
    return check_grep_output_contains(sandbox_dir, params, trajectory)


def check_grep_finds_pattern(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 grep 在预期位置找到模式"""
    pattern = params.get('pattern', '')
    expected_in = params.get('expected_in', '')

    if not expected_in:
        return check_grep_pattern_found(sandbox_dir, params, trajectory)

    full_path = _resolve_path(expected_in, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {expected_in}"

    try:
        content = full_path.read_text(encoding='utf-8', errors='replace')
        if re.search(pattern, content):
            return True, f"pattern found in {expected_in}"
        return False, f"pattern not found in {expected_in}"
    except Exception as e:
        return False, f"error: {e}"


def check_grep_finds_file(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 grep 找到特定文件"""
    return check_grep_output_contains(sandbox_dir, params, trajectory)


def check_grep_output_not_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 grep 输出不包含某些文件"""
    pattern = params.get('pattern', '')
    path = params.get('path', '')
    excluded_files = params.get('excluded_files', [])

    search_path = _resolve_path(path, sandbox_dir) if path else sandbox_dir

    try:
        cmd = ['grep', '-r', '-l', pattern, str(search_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        matched_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        found_excluded = [ef for ef in excluded_files if any(ef in f for f in matched_files)]
        if found_excluded:
            return False, f"excluded files found in results: {found_excluded}"
        return True, "no excluded files in grep results"
    except Exception as e:
        return False, f"grep error: {e}"


# =============================================================================
# 脚本执行类型
# =============================================================================

def check_custom_script(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """执行自定义 Python 脚本"""
    script_content = params.get('script_content', '')
    timeout = params.get('timeout', 30)

    if not script_content:
        return False, "no script_content provided"

    try:
        # 创建临时脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            # 在 sandbox 目录下执行
            result = subprocess.run(
                ['python3', script_path],
                cwd=str(sandbox_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return True, f"script passed: {result.stdout.strip()[:100]}"
            else:
                return False, f"script failed: {result.stdout.strip()[:100]} {result.stderr.strip()[:100]}"
        finally:
            os.unlink(script_path)
    except subprocess.TimeoutExpired:
        return False, f"script timeout after {timeout}s"
    except Exception as e:
        return False, f"script error: {e}"


def check_bash_check(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """执行 bash 命令并检查输出"""
    command = params.get('command', '')
    expected = params.get('expected', '')

    if not command:
        return False, "no command provided"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout.strip()
        if expected in output:
            return True, f"command output contains '{expected}'"
        return False, f"expected '{expected}' not in output: {output[:100]}"
    except Exception as e:
        return False, f"bash error: {e}"


def check_bash_exit_code(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 bash 命令退出码"""
    command = params.get('command', '')
    expected_code = params.get('expected_code', 0)

    if not command:
        return False, "no command provided"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == expected_code:
            return True, f"exit code {result.returncode} == {expected_code}"
        return False, f"exit code {result.returncode} != {expected_code}"
    except Exception as e:
        return False, f"bash error: {e}"


# =============================================================================
# 工具调用检查类型
# =============================================================================

def check_tool_used(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查是否使用了特定工具"""
    tool_name = params.get('tool', params.get('tool_name', ''))

    if not trajectory:
        return True, "tool_used check skipped (no trajectory)"

    for step in trajectory:
        if step.get('tool') == tool_name:
            return True, f"tool '{tool_name}' was used"

    return False, f"tool '{tool_name}' was not used"


def check_tool_called(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """同 tool_used"""
    return check_tool_used(sandbox_dir, params, trajectory)


# =============================================================================
# 其他类型
# =============================================================================

def check_file_exists_any(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查任一文件存在"""
    paths = params.get('paths', [])

    for path in paths:
        full_path = _resolve_path(path, sandbox_dir)
        if full_path.exists():
            return True, f"file exists: {path}"

    return False, f"none of the files exist: {paths}"


def check_file_executable(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件是否可执行"""
    path = params.get('path', '')
    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    if os.access(str(full_path), os.X_OK):
        return True, f"file is executable: {path}"
    return False, f"file is not executable: {path}"


def check_file_found(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件被找到"""
    pattern = params.get('pattern', '')
    expected_files = params.get('expected_files', [])
    return check_glob_result_contains(sandbox_dir, {'pattern': pattern, 'expected_files': expected_files}, trajectory)


# =============================================================================
# 进程管理检查函数
# =============================================================================

def check_bash_process_running(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查进程是否在运行（通过 PID 文件或进程名）"""
    process_name = params.get('process_name', '')
    pid_file = params.get('pid_file', '')

    if pid_file:
        # 通过 PID 文件检查
        pid_path = _resolve_path(pid_file, sandbox_dir)
        if not pid_path.exists():
            return False, f"PID file not found: {pid_file}"

        try:
            pid = pid_path.read_text().strip()
            cmd = f"ps -p {pid}"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                return True, f"process with PID {pid} is running"
            return False, f"process with PID {pid} is not running"
        except Exception as e:
            return False, f"error checking PID: {e}"

    if process_name:
        # 通过进程名检查
        cmd = f"pgrep -f '{process_name}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip()
            return True, f"process '{process_name}' is running (PID: {pids})"
        return False, f"process '{process_name}' is not running"

    return False, "neither process_name nor pid_file provided"


def check_bash_process_not_running(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查进程已停止（用于验证 KillShell 效果）"""
    # 逆向验证，复用 bash_process_running 逻辑
    is_running, message = check_bash_process_running(sandbox_dir, params, trajectory)
    if not is_running:
        return True, f"process correctly not running: {message}"
    return False, f"process still running: {message}"


# =============================================================================
# Web 工具检查函数
# =============================================================================

def check_tool_used_webfetch(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """验证使用了 WebFetch 工具（可选：验证 URL 模式）"""
    url_pattern = params.get('url_pattern', '')

    if not trajectory:
        return False, "no trajectory provided"

    for step in trajectory:
        tool = step.get('tool', '')
        if tool == 'WebFetch':
            if not url_pattern:
                return True, "WebFetch was used"

            input_data = step.get('input', {})
            url = input_data.get('url', '')
            if url_pattern in url:
                return True, f"WebFetch used with URL containing '{url_pattern}'"

    if url_pattern:
        return False, f"WebFetch not used with URL pattern '{url_pattern}'"
    return False, "WebFetch tool not used"


def check_tool_used_web_search(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """验证使用了 mcp web_search 工具（可选：验证搜索关键词）"""
    keyword_pattern = params.get('keyword_pattern', '')

    if not trajectory:
        return False, "no trajectory provided"

    for step in trajectory:
        tool = step.get('tool', '')
        # MCP 工具格式：mcp__baidu-server__web_search
        if 'web_search' in tool or tool == 'WebSearch':
            if not keyword_pattern:
                return True, f"{tool} was used"

            input_data = step.get('input', {})
            query_list = input_data.get('query_list', [])
            query = input_data.get('query', '')

            # 检查关键词
            search_text = ' '.join(query_list) + ' ' + query
            if keyword_pattern.lower() in search_text.lower():
                return True, f"web_search used with keyword '{keyword_pattern}'"

    if keyword_pattern:
        return False, f"web_search not used with keyword '{keyword_pattern}'"
    return False, "web_search tool not used"


# =============================================================================
# Git 相关检查函数
# =============================================================================

def check_git_commit_message(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查最新提交消息是否包含特定模式"""
    pattern = params.get('pattern', '')

    if not pattern:
        return False, "no pattern provided"

    try:
        cmd = "git log -1 --pretty=%B"
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True,
            timeout=30
        )

        commit_message = result.stdout.strip()
        if not commit_message:
            return False, "no commit found"

        if re.search(pattern, commit_message):
            return True, f"commit message matches pattern '{pattern}'"
        return False, f"commit message does not match pattern '{pattern}': {commit_message[:100]}"
    except Exception as e:
        return False, f"git error: {e}"


def check_git_branch_exists(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查分支是否存在"""
    branch_name = params.get('branch_name', '')

    if not branch_name:
        return False, "no branch_name provided"

    try:
        cmd = f"git branch --list '{branch_name}'"
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True,
            timeout=30
        )

        if branch_name in result.stdout:
            return True, f"branch '{branch_name}' exists"
        return False, f"branch '{branch_name}' not found"
    except Exception as e:
        return False, f"git error: {e}"


def check_git_file_staged(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件是否已暂存"""
    file_path = params.get('file_path', '')

    if not file_path:
        return False, "no file_path provided"

    try:
        cmd = "git diff --cached --name-only"
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True,
            timeout=30
        )

        staged_files = result.stdout.strip().split('\n')
        if file_path in staged_files or any(file_path in f for f in staged_files):
            return True, f"file '{file_path}' is staged"
        return False, f"file '{file_path}' is not staged"
    except Exception as e:
        return False, f"git error: {e}"


def check_git_file_committed(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件是否在最新提交中"""
    file_path = params.get('file_path', '')

    if not file_path:
        return False, "no file_path provided"

    try:
        cmd = "git diff-tree --no-commit-id --name-only -r HEAD"
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True,
            timeout=30
        )

        committed_files = result.stdout.strip().split('\n')
        if file_path in committed_files or any(file_path in f for f in committed_files):
            return True, f"file '{file_path}' is in latest commit"
        return False, f"file '{file_path}' is not in latest commit"
    except Exception as e:
        return False, f"git error: {e}"


# =============================================================================
# 结构化数据检查函数
# =============================================================================

def check_json_path_equals(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 JSON 文件中特定路径的值"""
    path = params.get('path', '')
    json_path = params.get('json_path', '')
    expected = params.get('expected', '')

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    try:
        content = json.loads(full_path.read_text(encoding='utf-8'))

        # 解析 JSON 路径 (支持 a.b.c 格式)
        keys = json_path.split('.')
        value = content
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                return False, f"invalid path: {json_path}"

        if str(value) == str(expected):
            return True, f"json_path '{json_path}' equals '{expected}'"
        return False, f"json_path '{json_path}' is '{value}', expected '{expected}'"
    except json.JSONDecodeError as e:
        return False, f"invalid JSON: {e}"
    except Exception as e:
        return False, f"error: {e}"


def check_yaml_key_equals(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查 YAML 文件中特定键的值"""
    path = params.get('path', '')
    key_path = params.get('key_path', '')
    expected = params.get('expected', '')

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    try:
        import yaml
        content = yaml.safe_load(full_path.read_text(encoding='utf-8'))

        # 解析键路径 (支持 a.b.c 格式)
        keys = key_path.split('.')
        value = content
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                return False, f"invalid key path: {key_path}"

        if str(value) == str(expected):
            return True, f"yaml_key '{key_path}' equals '{expected}'"
        return False, f"yaml_key '{key_path}' is '{value}', expected '{expected}'"
    except ImportError:
        # 如果没有 yaml 模块，使用简单的字符串匹配
        content = full_path.read_text(encoding='utf-8')
        if f"{key_path.split('.')[-1]}: {expected}" in content:
            return True, f"yaml contains '{key_path}: {expected}' (simple match)"
        return False, f"yaml does not contain expected value (yaml module not available)"
    except Exception as e:
        return False, f"error: {e}"


# =============================================================================
# Plan 模式专用检查函数
# =============================================================================

def check_file_moved(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件是否从源位置移动到目标位置"""
    source = params.get('source', '')
    destination = params.get('destination', '')

    source_path = _resolve_path(source, sandbox_dir)
    dest_path = _resolve_path(destination, sandbox_dir)

    source_exists = source_path.exists()
    dest_exists = dest_path.exists()

    if not source_exists and dest_exists:
        return True, f"file moved from '{source}' to '{destination}'"
    elif source_exists and dest_exists:
        return False, f"file copied (source still exists): {source}"
    elif source_exists and not dest_exists:
        return False, f"file not moved (still at source): {source}"
    else:
        return False, f"neither source nor destination exists"


def check_import_updated(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件中的导入语句是否已更新"""
    path = params.get('path', '')
    old_import = params.get('old_import', '')
    new_import = params.get('new_import', '')

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    try:
        content = full_path.read_text(encoding='utf-8')

        has_old = old_import in content
        has_new = new_import in content

        if not has_old and has_new:
            return True, f"import updated from '{old_import}' to '{new_import}'"
        elif has_old and has_new:
            return False, f"both old and new imports exist"
        elif has_old and not has_new:
            return False, f"import not updated (old import still exists)"
        else:
            return False, f"neither old nor new import found"
    except Exception as e:
        return False, f"error: {e}"


def check_file_not_exists(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件不存在"""
    path = params.get('path', '')
    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return True, f"file correctly does not exist: {path}"
    return False, f"file unexpectedly exists: {path}"


def check_directory_exists(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查目录存在"""
    path = params.get('path', '')
    full_path = _resolve_path(path, sandbox_dir)

    if full_path.exists() and full_path.is_dir():
        return True, f"directory exists: {path}"
    elif full_path.exists():
        return False, f"path exists but is not a directory: {path}"
    return False, f"directory not found: {path}"


# =============================================================================
# Check 注册表
# =============================================================================

CHECK_REGISTRY = {
    # 标准类型
    'file_exists': check_file_exists,
    'file_content_contains': check_file_content_contains,
    'file_content_not_contains': check_file_content_not_contains,
    'file_content_matches': check_file_content_matches,

    # file_content 扩展
    'file_content_match': check_file_content_match,
    'file_content_regex': check_file_content_regex,

    # glob 相关
    'glob_result_contains': check_glob_result_contains,
    'glob_result_not_contains': check_glob_result_not_contains,
    'glob_returns_files': check_glob_returns_files,
    'glob_result_count': check_glob_result_count,
    'glob_pattern_matches': check_glob_pattern_matches,
    'glob_executed': check_glob_executed,
    'glob_used': check_glob_used,

    # grep 相关
    'grep_output_contains': check_grep_output_contains,
    'grep_result_contains': check_grep_result_contains,
    'grep_pattern_found': check_grep_pattern_found,
    'grep_finds_content': check_grep_finds_content,
    'grep_finds_pattern': check_grep_finds_pattern,
    'grep_finds_file': check_grep_finds_file,
    'grep_output_not_contains': check_grep_output_not_contains,

    # 脚本执行
    'custom_script': check_custom_script,
    'bash_check': check_bash_check,
    'bash_exit_code': check_bash_exit_code,

    # 工具调用检查
    'tool_used': check_tool_used,
    'tool_called': check_tool_called,

    # 进程管理检查
    'bash_process_running': check_bash_process_running,
    'bash_process_not_running': check_bash_process_not_running,

    # Web 工具检查
    'tool_used_webfetch': check_tool_used_webfetch,
    'tool_used_web_search': check_tool_used_web_search,

    # Git 相关检查
    'git_commit_message': check_git_commit_message,
    'git_branch_exists': check_git_branch_exists,
    'git_file_staged': check_git_file_staged,
    'git_file_committed': check_git_file_committed,

    # 结构化数据检查
    'json_path_equals': check_json_path_equals,
    'yaml_key_equals': check_yaml_key_equals,

    # Plan 模式检查
    'file_moved': check_file_moved,
    'import_updated': check_import_updated,
    'file_not_exists': check_file_not_exists,
    'directory_exists': check_directory_exists,

    # 其他
    'file_exists_any': check_file_exists_any,
    'file_executable': check_file_executable,
    'file_found': check_file_found,
}


# =============================================================================
# 便捷函数
# =============================================================================

def verify_checklist(
    checks: List[dict],
    sandbox_dir: Path,
    trajectory: Optional[List[dict]] = None
) -> Tuple[bool, List[dict]]:
    """
    验证整个 checklist

    Args:
        checks: golden_check 列表
        sandbox_dir: sandbox 目录
        trajectory: 可选的轨迹数据

    Returns:
        (all_passed, results): 是否全部通过，每个 check 的结果
    """
    results = []
    all_passed = True

    for check in checks:
        check_type = check.get('type', 'unknown')
        params = check.get('params', {})

        passed, detail = verify_check(check_type, params, sandbox_dir, trajectory)

        results.append({
            'type': check_type,
            'passed': passed,
            'detail': detail,
            'params': params
        })

        if not passed:
            all_passed = False

    return all_passed, results


def get_supported_check_types() -> List[str]:
    """获取所有支持的 check 类型"""
    return list(CHECK_REGISTRY.keys())


# =============================================================================
# 测试入口
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Custom checks module')
    parser.add_argument('--list', action='store_true', help='List all supported check types')
    parser.add_argument('--test', type=str, help='Test a specific check type')

    args = parser.parse_args()

    if args.list:
        print("Supported check types:")
        for i, t in enumerate(sorted(get_supported_check_types()), 1):
            print(f"  {i:2}. {t}")
        print(f"\nTotal: {len(CHECK_REGISTRY)} types")

    elif args.test:
        print(f"Testing check type: {args.test}")
        if args.test in CHECK_REGISTRY:
            print(f"  Function: {CHECK_REGISTRY[args.test].__name__}")
        else:
            print(f"  Not found in registry")
