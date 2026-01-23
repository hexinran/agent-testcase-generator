#!/usr/bin/env python3
"""
Phase 4: 初检验证脚本

验证测试用例的 reference_solution 是否能正确通过 graders。

用法:
    python3 phase4_verify.py <case_file> [--sandbox <sandbox_id>]

功能:
1. 创建或使用现有 sandbox
2. 从 case 文件加载环境
3. 执行 reference_solution
4. 验证 graders
5. 输出验证结果
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from sandbox.sandbox_manager import SandboxManager
from evaluation.grader_executor import GraderExecutor


def execute_reference_solution(sandbox_path: Path, reference_solution: list) -> list:
    """
    执行 reference_solution

    Args:
        sandbox_path: sandbox 工作目录
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
                full_path = sandbox_path / file_path
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

                full_path = sandbox_path / file_path
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

                full_path = sandbox_path / file_path
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
                import subprocess
                import signal
                command = input_data.get('command', '')
                background = input_data.get('background', False)

                if background:
                    # 后台执行
                    try:
                        process = subprocess.Popen(
                            command,
                            shell=True,
                            cwd=str(sandbox_path),
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
                    result = subprocess.run(
                        command,
                        shell=True,
                        cwd=str(sandbox_path),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    step['success'] = result.returncode == 0
                    step['output'] = result.stdout[:500] if result.stdout else result.stderr[:500]

            elif tool == 'KillShell':
                import signal
                import os
                shell_id = input_data.get('shell_id', '')
                pid_file = input_data.get('pid_file', '')

                try:
                    if pid_file:
                        # 通过 PID 文件
                        pid_path = sandbox_path / pid_file
                        if pid_path.exists():
                            pid = int(pid_path.read_text().strip())
                            try:
                                os.kill(pid, signal.SIGTERM)
                                step['success'] = True
                                step['output'] = f"Killed process {pid}"
                            except ProcessLookupError:
                                step['success'] = False
                                step['output'] = f"Process {pid} not found"
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
                try:
                    import requests
                    response = requests.get(url, timeout=10)
                    step['success'] = response.status_code == 200
                    step['output'] = response.text[:500]
                except Exception as e:
                    step['success'] = False
                    step['output'] = f"WebFetch error: {e}"

            else:
                step['output'] = f"Unknown tool: {tool}"

        except Exception as e:
            step['output'] = f"Error: {str(e)}"

        trajectory.append(step)

    return trajectory


def main():
    parser = argparse.ArgumentParser(description='Phase 4: 初检验证')
    parser.add_argument('case_file', help='测试用例 JSON 文件')
    parser.add_argument('--sandbox', help='使用现有 sandbox ID')
    parser.add_argument('--output', help='输出结果文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 加载 case 文件
    case_path = Path(args.case_file)
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

    print(f"\n{'='*60}")
    print(f"Phase 4: 初检验证")
    print(f"{'='*60}")
    print(f"Case ID: {case_id}")
    print(f"Tool: {tool_name}, Difficulty: D{difficulty}")
    print(f"Environment files: {len(environment)}")
    print(f"Reference solution steps: {len(reference_solution)}")

    # 创建或获取 sandbox
    manager = SandboxManager()

    if args.sandbox:
        info = manager.get(args.sandbox)
        if info is None:
            print(f"Error: Sandbox not found: {args.sandbox}")
            sys.exit(1)
        # 重置工作区
        manager.reset_working(info)
    else:
        # 提取 init_commands（如果有）
        init_commands = case_data.get('init_commands', [])

        info = manager.create_from_environment(
            environment,
            init_commands=init_commands,
            case_id=case_id,
            tool_name=tool_name,
            difficulty=difficulty
        )

    print(f"\nSandbox: {info.sandbox_id}")
    print(f"Working directory: {info.working_path}")

    # 执行 reference_solution
    print(f"\n--- Executing Reference Solution ---")
    trajectory = execute_reference_solution(info.working_path, reference_solution)

    for step in trajectory:
        status = "✓" if step['success'] else "✗"
        print(f"  {status} Step {step['step']}: {step['tool']} - {step['output'][:60]}")

    # 验证 graders
    print(f"\n--- Verifying Graders ---")
    executor = GraderExecutor(info.working_path)
    result = executor.execute(case_data, trajectory)

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
        'sandbox_id': info.sandbox_id,
        'timestamp': datetime.now().isoformat(),
        'passed': result.passed,
        'execution_trajectory': trajectory,
        'grader_result': {
            'passed': result.passed,
            'total_checks': result.total_checks,
            'passed_checks': result.passed_checks,
            'failed_checks': result.failed_checks,
            'tool_calls_verified': result.tool_calls_verified,
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
        output_path = info.root_path / 'phase4_result.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nResult saved to: {output_path}")

    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
