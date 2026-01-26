#!/usr/bin/env python3
"""
Phase 6: Haiku 验证脚本

使用 Haiku 模型执行测试用例，验证弱模型是否能完成任务。

用法:
    python3 phase6_haiku.py <case_file> [--haiku-dir <dir>] [--timeout <seconds>]

功能:
1. 在当前目录创建 haiku_space/ 子目录
2. 根据 case.json 的 environment 创建文件
3. 执行 init_commands（KillShell 等场景必需）
4. cd 到 haiku_space/ 后调用 Haiku CLI（隔离答案）
5. 验证 graders
6. 输出完整结果
"""
import sys
import os
import json
import argparse
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict, Any

# 添加 scripts 目录到路径，以便导入 custom_checks
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from custom_checks import CHECK_REGISTRY, _resolve_path


# ============================================================
# 环境设置
# ============================================================

def setup_haiku_space(case_data: dict, haiku_dir: Path) -> None:
    """
    在 haiku_space 中创建环境

    Args:
        case_data: 测试用例数据
        haiku_dir: haiku 工作目录
    """
    # 清理并创建目录
    if haiku_dir.exists():
        shutil.rmtree(haiku_dir)
    haiku_dir.mkdir(parents=True, exist_ok=True)

    # 1. 根据 environment 创建文件
    environment = case_data.get('environment', [])
    for file_info in environment:
        file_path = file_info.get('path', '')
        content = file_info.get('content', '')
        executable = file_info.get('executable', False)

        if not file_path:
            continue

        full_path = haiku_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')

        if executable:
            full_path.chmod(0o755)

    print(f"  Created {len(environment)} environment files")

    # 2. 执行 init_commands（KillShell 场景关键！）
    init_commands = case_data.get('init_commands', [])
    if init_commands:
        print(f"  Executing {len(init_commands)} init commands...")
        for cmd_info in init_commands:
            command = cmd_info.get('command', '')
            description = cmd_info.get('description', '')
            wait_sec = cmd_info.get('wait_sec', 0)

            if not command:
                continue

            print(f"    - {description}")
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(haiku_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    print(f"      Warning: command returned {result.returncode}")
                    if result.stderr:
                        print(f"      stderr: {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                print(f"      Warning: command timed out")
            except Exception as e:
                print(f"      Error: {e}")

            if wait_sec > 0:
                time.sleep(wait_sec)


# ============================================================
# Haiku CLI 调用
# ============================================================

def _parse_stream_json(stdout: str) -> Tuple[List[Dict], str]:
    """
    解析 stream-json 格式的输出，提取工具调用轨迹

    Args:
        stdout: stream-json 格式的输出

    Returns:
        (trajectory, final_output): 工具调用轨迹列表和最终文本输出
    """
    trajectory = []
    final_output_parts = []
    step_counter = 0
    tool_use_map = {}  # tool_use_id -> step_index 的映射

    for line in stdout.strip().split('\n'):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
            event_type = event.get('type', '')

            if event_type == 'assistant':
                message = event.get('message', {})
                content_blocks = message.get('content', [])

                for block in content_blocks:
                    block_type = block.get('type', '')

                    if block_type == 'tool_use':
                        step_counter += 1
                        tool_use_id = block.get('id', '')
                        tool_name = block.get('name', 'unknown')
                        tool_input = block.get('input', {})

                        trajectory.append({
                            'step': step_counter,
                            'tool': tool_name,
                            'input': tool_input,
                            'output': ''
                        })
                        tool_use_map[tool_use_id] = len(trajectory) - 1

                    elif block_type == 'text':
                        text = block.get('text', '')
                        if text:
                            final_output_parts.append(text)

            elif event_type == 'user':
                message = event.get('message', {})
                content_blocks = message.get('content', [])

                for block in content_blocks:
                    if block.get('type') == 'tool_result':
                        tool_use_id = block.get('tool_use_id', '')
                        content = block.get('content', '')

                        if tool_use_id in tool_use_map:
                            step_index = tool_use_map[tool_use_id]
                            trajectory[step_index]['output'] = content[:500] if len(content) > 500 else content

            elif event_type == 'result':
                result_text = event.get('result', '')
                if result_text and not final_output_parts:
                    final_output_parts.append(result_text)

        except json.JSONDecodeError:
            continue

    final_output = '\n'.join(final_output_parts)
    return trajectory, final_output


def run_haiku_cli(query: str, haiku_dir: Path, timeout: int = 600) -> Dict[str, Any]:
    """
    使用 Claude CLI 运行 Haiku 验证

    关键：cwd 设置为 haiku_dir，Haiku 看不到外部的 case.json

    Args:
        query: 用户问题
        haiku_dir: haiku 工作目录（Haiku 的 cwd）
        timeout: 超时秒数

    Returns:
        验证结果字典
    """
    start_time = datetime.now()

    try:
        cmd = [
            'claude',
            '--model', 'haiku',
            '--dangerously-skip-permissions',
            '--output-format', 'stream-json',
            '--verbose',
            '-p', query
        ]

        # 关键：cwd 设置为 haiku_dir，Haiku 看不到外部的 case.json
        result = subprocess.run(
            cmd,
            cwd=str(haiku_dir),
            capture_output=True,
            text=True,
            timeout=timeout
        )

        duration = (datetime.now() - start_time).total_seconds()

        trajectory = []
        final_output = ""

        if result.returncode == 0:
            trajectory, final_output = _parse_stream_json(result.stdout)

        return {
            "success": result.returncode == 0,
            "trajectory": trajectory,
            "total_steps": len(trajectory),
            "duration_sec": duration,
            "stdout": final_output,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            "success": False,
            "error": f"Timeout after {timeout} seconds",
            "trajectory": [],
            "total_steps": 0,
            "duration_sec": duration
        }
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            "success": False,
            "error": str(e),
            "trajectory": [],
            "total_steps": 0,
            "duration_sec": duration
        }


# ============================================================
# Grader 验证
# ============================================================

class CheckResult:
    """单个检查的结果"""
    def __init__(self, check_type: str, passed: bool, message: str, description: str = ""):
        self.check_type = check_type
        self.passed = passed
        self.message = message
        self.description = description


class GraderResult:
    """Grader 验证结果"""
    def __init__(self):
        self.passed = False
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.tool_calls_verified = False
        self.tool_calls_details = []
        self.results: List[CheckResult] = []


def verify_graders(case_data: dict, haiku_dir: Path, trajectory: List[Dict]) -> GraderResult:
    """
    执行 grader 验证

    Args:
        case_data: 测试用例数据
        haiku_dir: haiku 工作目录
        trajectory: Haiku 执行轨迹

    Returns:
        GraderResult 验证结果
    """
    result = GraderResult()
    graders = case_data.get('graders', [])

    for grader in graders:
        grader_type = grader.get('type', '')

        if grader_type == 'state_check':
            checks = grader.get('checks', [])
            for check in checks:
                check_type = check.get('check', '')
                params = check.get('params', {})
                description = check.get('description', '')

                result.total_checks += 1

                # 调用 custom_checks.py 中的检查函数
                if check_type in CHECK_REGISTRY:
                    check_func = CHECK_REGISTRY[check_type]
                    try:
                        passed, message = check_func(haiku_dir, params, trajectory)
                    except Exception as e:
                        passed, message = False, f"Check error: {e}"
                else:
                    passed, message = False, f"Unknown check type: {check_type}"

                if passed:
                    result.passed_checks += 1
                else:
                    result.failed_checks += 1

                result.results.append(CheckResult(check_type, passed, message, description))

        elif grader_type == 'tool_calls':
            required = grader.get('required', [])
            tools_used = set(step.get('tool', '') for step in trajectory)

            all_verified = True
            for req in required:
                tool = req.get('tool', '')
                desc = req.get('description', '')
                verified = tool in tools_used

                if not verified:
                    all_verified = False

                result.tool_calls_details.append({
                    'tool': tool,
                    'description': desc,
                    'verified': verified
                })

            result.tool_calls_verified = all_verified

    # 计算总体是否通过
    result.passed = (result.failed_checks == 0) and result.tool_calls_verified

    return result


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Phase 6: Haiku 验证')
    parser.add_argument('case_file', help='测试用例 JSON 文件路径')
    parser.add_argument('--haiku-dir', default='haiku_space', help='Haiku 工作目录名（默认: haiku_space）')
    parser.add_argument('--output', help='输出结果文件路径')
    parser.add_argument('--timeout', type=int, default=600, help='Haiku 执行超时秒数（默认: 600）')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 加载 case 文件
    case_path = Path(args.case_file).resolve()
    if not case_path.exists():
        print(f"Error: Case file not found: {args.case_file}")
        sys.exit(1)

    with open(case_path, 'r', encoding='utf-8') as f:
        case_data = json.load(f)

    # 提取信息
    task = case_data.get('task', {})
    case_id = task.get('id', case_path.stem)
    query = task.get('desc', '')

    # haiku_dir 相对于 case.json 所在目录
    working_dir = case_path.parent
    haiku_dir = working_dir / args.haiku_dir

    print(f"\n{'='*60}")
    print(f"Phase 6: Haiku 验证")
    print(f"{'='*60}")
    print(f"Case ID: {case_id}")
    print(f"Query: {query[:80]}..." if len(query) > 80 else f"Query: {query}")
    print(f"Working directory: {working_dir}")
    print(f"Haiku directory: {haiku_dir}")

    # Step 1: 设置 haiku_space 环境
    print(f"\n--- Setting up Haiku environment ---")
    setup_haiku_space(case_data, haiku_dir)

    # Step 2: 执行 Haiku 验证
    print(f"\n--- Running Haiku validation ---")
    print(f"This may take a few minutes...")

    haiku_result = run_haiku_cli(query, haiku_dir, args.timeout)

    print(f"Execution completed in {haiku_result.get('duration_sec', 0):.1f}s")
    print(f"Total steps: {haiku_result.get('total_steps', 0)}")

    if not haiku_result.get('success'):
        error = haiku_result.get('error', 'Unknown')
        print(f"Warning: Haiku execution issue: {error}")

    if args.verbose and haiku_result.get('trajectory'):
        print(f"\n--- Haiku trajectory ---")
        for step in haiku_result['trajectory']:
            print(f"  Step {step['step']}: {step['tool']}")

    # Step 3: 验证 graders
    print(f"\n--- Verifying Graders ---")
    trajectory = haiku_result.get('trajectory', [])
    result = verify_graders(case_data, haiku_dir, trajectory)

    for check_result in result.results:
        status = "✓" if check_result.passed else "✗"
        print(f"  {status} [{check_result.check_type}] {check_result.message}")

    if result.tool_calls_details:
        print(f"\n--- Tool Calls ---")
        for tc in result.tool_calls_details:
            status = "✓" if tc.get('verified') else "✗"
            print(f"  {status} {tc.get('tool')}: {tc.get('description')}")

    # 输出结果
    print(f"\n{'='*60}")
    if result.passed:
        print(f"✓ Phase 6 PASSED - Haiku completed the task")
    else:
        print(f"✗ Phase 6 FAILED - Haiku did not complete the task")
    print(f"  Checks: {result.passed_checks}/{result.total_checks} passed")
    print(f"  Haiku steps: {haiku_result.get('total_steps', 0)}")
    print(f"  Duration: {haiku_result.get('duration_sec', 0):.1f}s")
    print(f"{'='*60}")

    # 保存结果
    output_data = {
        'phase': 6,
        'case_id': case_id,
        'timestamp': datetime.now().isoformat(),
        'haiku_execution': {
            'success': haiku_result.get('success', False),
            'total_steps': haiku_result.get('total_steps', 0),
            'duration_sec': haiku_result.get('duration_sec', 0),
            'trajectory': haiku_result.get('trajectory', []),
            'error': haiku_result.get('error')
        },
        'grader_result': {
            'passed': result.passed,
            'total_checks': result.total_checks,
            'passed_checks': result.passed_checks,
            'failed_checks': result.failed_checks,
            'tool_calls_verified': result.tool_calls_verified,
            'tool_calls_details': result.tool_calls_details,
            'details': [
                {
                    'check_type': r.check_type,
                    'passed': r.passed,
                    'message': r.message,
                    'description': r.description
                }
                for r in result.results
            ]
        },
        'haiku_evaluation': {
            'passed': result.passed,
            'haiku_steps': haiku_result.get('total_steps', 0),
            'duration_sec': haiku_result.get('duration_sec', 0),
            'passed_checks': result.passed_checks,
            'total_checks': result.total_checks
        }
    }

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = working_dir / 'phase6_result.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nResult saved to: {output_path}")

    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
