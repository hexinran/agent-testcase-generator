#!/usr/bin/env python3
"""
Phase 4: 自测验证脚本

验证测试用例的 reference_solution 是否能正确通过 graders。

用法:
    python3 phase4_verify.py <case_file> [--work-dir <dir>] [--keep-env]

功能:
1. 在当前目录创建 phase4_workspace/ 子目录
2. 根据 case.json 的 environment 创建文件
3. 执行 init_commands
4. 按 reference_solution 逐步执行
5. 验证 graders
6. 输出验证结果

区别于 phase6_haiku.py：
- 本脚本直接按 reference_solution 执行，不调用 AI 模型
- 用于快速验证出题设计是否正确
"""
import sys
import os
import json
import argparse
import subprocess
import shutil
import time
import signal
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

def setup_workspace(case_data: dict, work_dir: Path) -> None:
    """
    设置工作环境

    Args:
        case_data: 测试用例数据
        work_dir: 工作目录
    """
    # 清理并创建目录
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. 根据 environment 创建文件
    environment = case_data.get('environment', [])
    for file_info in environment:
        file_path = file_info.get('path', '')
        content = file_info.get('content', '')
        executable = file_info.get('executable', False)

        if not file_path:
            continue

        full_path = work_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')

        if executable:
            full_path.chmod(0o755)

    print(f"  Created {len(environment)} environment files")

    # 2. 执行 init_commands
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
                    cwd=str(work_dir),
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
# Reference Solution 执行
# ============================================================

def execute_reference_solution(work_dir: Path, reference_solution: list) -> List[Dict]:
    """
    执行 reference_solution

    Args:
        work_dir: 工作目录
        reference_solution: 参考解决方案列表

    Returns:
        执行轨迹
    """
    trajectory = []

    for i, action in enumerate(reference_solution):
        tool = action.get('tool', '')
        input_data = action.get('input', {})
        reasoning = action.get('reasoning', '')

        step = {
            'step': i + 1,
            'tool': tool,
            'input': input_data,
            'reasoning': reasoning,
            'success': False,
            'output': ''
        }

        try:
            if tool == 'Read':
                file_path = input_data.get('file_path', '')
                file_path = file_path.replace('{{SANDBOX}}/', '').replace('{{SANDBOX}}', '')
                full_path = work_dir / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    step['success'] = True
                    step['output'] = f"Read {len(content)} chars from {file_path}"
                else:
                    step['output'] = f"File not found: {file_path}"

            elif tool == 'Edit':
                file_path = input_data.get('file_path', '')
                file_path = file_path.replace('{{SANDBOX}}/', '').replace('{{SANDBOX}}', '')
                old_string = input_data.get('old_string', '')
                new_string = input_data.get('new_string', '')

                full_path = work_dir / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    if old_string in content:
                        new_content = content.replace(old_string, new_string)
                        full_path.write_text(new_content, encoding='utf-8')
                        step['success'] = True
                        step['output'] = f"Edited {file_path}"
                    else:
                        step['output'] = f"old_string not found in {file_path}"
                else:
                    step['output'] = f"File not found: {file_path}"

            elif tool == 'Write':
                file_path = input_data.get('file_path', '')
                file_path = file_path.replace('{{SANDBOX}}/', '').replace('{{SANDBOX}}', '')
                content = input_data.get('content', '')

                full_path = work_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                step['success'] = True
                step['output'] = f"Wrote {len(content)} chars to {file_path}"

            elif tool == 'Grep':
                # Grep 主要是探索，不修改文件
                step['success'] = True
                step['output'] = f"Grep executed (exploration)"

            elif tool == 'Glob':
                # Glob 主要是探索，不修改文件
                step['success'] = True
                step['output'] = f"Glob executed (exploration)"

            elif tool == 'Bash':
                command = input_data.get('command', '')
                background = input_data.get('background', False) or input_data.get('run_in_background', False)

                if background:
                    # 后台执行
                    try:
                        process = subprocess.Popen(
                            command,
                            shell=True,
                            cwd=str(work_dir),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        step['success'] = True
                        step['output'] = f"Started background process (PID: {process.pid})"
                        step['pid'] = process.pid
                    except Exception as e:
                        step['success'] = False
                        step['output'] = f"Failed to start background process: {e}"
                else:
                    # 同步执行
                    try:
                        result = subprocess.run(
                            command,
                            shell=True,
                            cwd=str(work_dir),
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        step['success'] = result.returncode == 0
                        step['output'] = result.stdout[:500] if result.stdout else result.stderr[:500]
                    except subprocess.TimeoutExpired:
                        step['success'] = False
                        step['output'] = "Command timed out"

            elif tool == 'KillShell':
                shell_id = input_data.get('shell_id', '')
                pid_file = input_data.get('pid_file', '')

                try:
                    if pid_file:
                        # 通过 PID 文件
                        pid_path = work_dir / pid_file
                        if pid_path.exists():
                            pid = int(pid_path.read_text().strip())
                            try:
                                os.kill(pid, signal.SIGTERM)
                                step['success'] = True
                                step['output'] = f"Killed process {pid}"
                                # 清理 PID 文件
                                pid_path.unlink()
                            except ProcessLookupError:
                                step['success'] = True  # 进程已经不存在也算成功
                                step['output'] = f"Process {pid} already terminated"
                        else:
                            step['success'] = False
                            step['output'] = f"PID file not found: {pid_file}"
                    else:
                        step['success'] = False
                        step['output'] = "No pid_file provided"
                except Exception as e:
                    step['success'] = False
                    step['output'] = f"KillShell error: {e}"

            elif tool == 'WebFetch':
                url = input_data.get('url', '')
                # 简化处理，假设成功
                step['success'] = True
                step['output'] = f"WebFetch executed for {url}"

            elif tool == 'web_search':
                query = input_data.get('query', '')
                step['success'] = True
                step['output'] = f"web_search executed for {query}"

            else:
                step['output'] = f"Unknown tool: {tool}"

        except Exception as e:
            step['output'] = f"Error: {str(e)}"

        trajectory.append(step)

    return trajectory


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


def verify_graders(case_data: dict, work_dir: Path, trajectory: List[Dict]) -> GraderResult:
    """
    执行 grader 验证

    Args:
        case_data: 测试用例数据
        work_dir: 工作目录
        trajectory: 执行轨迹

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
                        passed, message = check_func(work_dir, params, trajectory)
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
    parser = argparse.ArgumentParser(description='Phase 4: 自测验证')
    parser.add_argument('case_file', help='测试用例 JSON 文件路径')
    parser.add_argument('--work-dir', default='phase4_workspace', help='工作目录名（默认: phase4_workspace）')
    parser.add_argument('--output', help='输出结果文件路径')
    parser.add_argument('--keep-env', action='store_true', help='保留工作环境（不删除）')
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
    tool_name = task.get('tool_name', 'Unknown')
    difficulty = task.get('difficulty', 0)
    environment = case_data.get('environment', [])
    reference_solution = case_data.get('reference_solution', [])

    # work_dir 相对于 case.json 所在目录
    working_dir = case_path.parent
    work_dir = working_dir / args.work_dir

    print(f"\n{'='*60}")
    print(f"Phase 4: 自测验证")
    print(f"{'='*60}")
    print(f"Case ID: {case_id}")
    print(f"Tool: {tool_name}, Difficulty: D{difficulty}")
    print(f"Environment files: {len(environment)}")
    print(f"Reference solution steps: {len(reference_solution)}")
    print(f"Work directory: {work_dir}")

    # Step 1: 设置工作环境
    print(f"\n--- Setting up workspace ---")
    setup_workspace(case_data, work_dir)

    # Step 2: 执行 reference_solution
    print(f"\n--- Executing Reference Solution ---")
    trajectory = execute_reference_solution(work_dir, reference_solution)

    for step in trajectory:
        status = "✓" if step['success'] else "✗"
        output_preview = step['output'][:60] if step['output'] else ''
        print(f"  {status} Step {step['step']}: {step['tool']} - {output_preview}")

    # Step 3: 验证 graders
    print(f"\n--- Verifying Graders ---")
    result = verify_graders(case_data, work_dir, trajectory)

    for check_result in result.results:
        status = "✓" if check_result.passed else "✗"
        print(f"  {status} [{check_result.check_type}] {check_result.message}")
        if args.verbose and check_result.description:
            print(f"      {check_result.description}")

    if result.tool_calls_details:
        print(f"\n--- Tool Calls ---")
        for tc in result.tool_calls_details:
            status = "✓" if tc.get('verified') else "✗"
            print(f"  {status} {tc.get('tool')}: {tc.get('description')}")

    # 输出结果
    print(f"\n{'='*60}")
    if result.passed:
        print(f"✓ Phase 4 PASSED")
    else:
        print(f"✗ Phase 4 FAILED")
    print(f"  Checks: {result.passed_checks}/{result.total_checks} passed")
    print(f"  Tool calls verified: {result.tool_calls_verified}")
    print(f"{'='*60}")

    # 保存结果
    output_data = {
        'phase': 4,
        'case_id': case_id,
        'timestamp': datetime.now().isoformat(),
        'passed': result.passed,
        'execution_trajectory': trajectory,
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
        }
    }

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = working_dir / 'phase4_result.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nResult saved to: {output_path}")

    # 清理工作环境
    if not args.keep_env and work_dir.exists():
        shutil.rmtree(work_dir)
        print(f"Cleaned up: {work_dir}")

    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
