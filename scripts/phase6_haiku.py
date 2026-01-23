#!/usr/bin/env python3
"""
Phase 6: Haiku 验证脚本

使用 Haiku 模型执行测试用例，验证弱模型是否能完成任务。

用法:
    python3 phase6_haiku.py <case_file> [--sandbox <sandbox_id>]

功能:
1. 准备 haiku 子目录
2. 调用 Haiku SDK 执行
3. 验证 graders
4. 输出完整结果
"""
import sys
import os
import json
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from sandbox.sandbox_manager import SandboxManager
from evaluation.grader_executor import GraderExecutor


def _parse_stream_json(stdout: str):
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

    # 解析每一行的 JSON
    for line in stdout.strip().split('\n'):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
            event_type = event.get('type', '')

            # 处理助手消息（可能包含工具调用或文本输出）
            if event_type == 'assistant':
                message = event.get('message', {})
                content_blocks = message.get('content', [])

                for block in content_blocks:
                    block_type = block.get('type', '')

                    # 工具调用
                    if block_type == 'tool_use':
                        step_counter += 1
                        tool_use_id = block.get('id', '')
                        tool_name = block.get('name', 'unknown')
                        tool_input = block.get('input', {})

                        # 添加到轨迹
                        trajectory.append({
                            'step': step_counter,
                            'tool': tool_name,
                            'input': tool_input,
                            'output': ''
                        })

                        # 记录映射关系
                        tool_use_map[tool_use_id] = len(trajectory) - 1

                    # 文本输出
                    elif block_type == 'text':
                        text = block.get('text', '')
                        if text:
                            final_output_parts.append(text)

            # 处理用户消息（包含工具结果）
            elif event_type == 'user':
                message = event.get('message', {})
                content_blocks = message.get('content', [])

                for block in content_blocks:
                    if block.get('type') == 'tool_result':
                        tool_use_id = block.get('tool_use_id', '')
                        content = block.get('content', '')

                        # 找到对应的工具调用，填充 output
                        if tool_use_id in tool_use_map:
                            step_index = tool_use_map[tool_use_id]
                            # 截断长输出
                            trajectory[step_index]['output'] = content[:500] if len(content) > 500 else content

            # 处理最终结果
            elif event_type == 'result':
                result_text = event.get('result', '')
                if result_text and not final_output_parts:
                    final_output_parts.append(result_text)

        except json.JSONDecodeError:
            # 跳过无法解析的行
            continue

    final_output = '\n'.join(final_output_parts)
    return trajectory, final_output


async def run_haiku_validation(query: str, sandbox_path: Path, max_turns: int = 100):
    """
    使用 Claude SDK 运行 Haiku 验证

    Args:
        query: 用户问题
        sandbox_path: sandbox 路径
        max_turns: 最大轮数

    Returns:
        验证结果字典
    """
    # SDK 初始化有兼容性问题，直接使用 CLI 方式
    return await run_haiku_cli(query, sandbox_path, max_turns)


async def run_haiku_cli(query: str, sandbox_path: Path, max_turns: int = 100):
    """
    使用 Claude CLI 运行 Haiku 验证，捕获详细的工具调用轨迹

    Args:
        query: 用户问题
        sandbox_path: sandbox 路径
        max_turns: 最大轮数

    Returns:
        验证结果字典
    """
    import subprocess

    start_time = datetime.now()

    try:
        # 使用 claude 命令行，启用 stream-json 格式捕获工具调用
        cmd = [
            'claude',
            '--model', 'haiku',
            '--dangerously-skip-permissions',
            '--output-format', 'stream-json',
            '--verbose',
            '-p', query
        ]

        result = subprocess.run(
            cmd,
            cwd=str(sandbox_path),
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )

        duration = (datetime.now() - start_time).total_seconds()

        # 解析 stream-json 输出提取工具调用轨迹
        trajectory = []
        final_output = ""

        if result.returncode == 0:
            trajectory, final_output = _parse_stream_json(result.stdout)

        return {
            "success": result.returncode == 0,
            "trajectory": trajectory,
            "total_steps": len(trajectory),
            "duration_sec": duration,
            "stdout": final_output,  # 只保存最终文本输出，不保存完整的 stream-json
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            "success": False,
            "error": "Timeout after 600 seconds",
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


def main():
    parser = argparse.ArgumentParser(description='Phase 6: Haiku 验证')
    parser.add_argument('case_file', help='测试用例 JSON 文件')
    parser.add_argument('--sandbox', help='使用现有 sandbox ID')
    parser.add_argument('--output', help='输出结果文件')
    parser.add_argument('--max-turns', type=int, default=100, help='最大轮数')
    parser.add_argument('--skip-execution', action='store_true', help='跳过执行，只验证现有结果')

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
    query = task.get('desc', '')
    environment = case_data.get('environment', [])

    print(f"\n{'='*60}")
    print(f"Phase 6: Haiku 验证")
    print(f"{'='*60}")
    print(f"Case ID: {case_id}")
    print(f"Query: {query[:80]}...")

    # 创建或获取 sandbox
    manager = SandboxManager()

    if args.sandbox:
        info = manager.get(args.sandbox)
        if info is None:
            print(f"Error: Sandbox not found: {args.sandbox}")
            sys.exit(1)
    else:
        # 提取 init_commands（如果有）
        init_commands = case_data.get('init_commands', [])

        info = manager.create_from_environment(
            environment,
            init_commands=init_commands,
            case_id=f"{case_id}_haiku"
        )

    # 重置 haiku 目录
    manager.reset_haiku(info)
    print(f"\nSandbox: {info.sandbox_id}")
    print(f"Haiku directory: {info.haiku_path}")

    # 执行 Haiku 验证
    if not args.skip_execution:
        print(f"\n--- Running Haiku Validation ---")
        print(f"This may take a few minutes...")

        haiku_result = asyncio.run(run_haiku_validation(
            query,
            info.haiku_path,
            args.max_turns
        ))

        print(f"Execution completed in {haiku_result.get('duration_sec', 0):.1f}s")
        print(f"Total steps: {haiku_result.get('total_steps', 0)}")

        if not haiku_result.get('success'):
            print(f"Warning: Haiku execution failed: {haiku_result.get('error', 'Unknown')}")
    else:
        # 加载现有结果
        haiku_result_file = info.haiku_path / 'haiku_result.json'
        if haiku_result_file.exists():
            with open(haiku_result_file, 'r') as f:
                haiku_result = json.load(f)
        else:
            haiku_result = {"success": False, "error": "No previous result found"}

    # 验证 graders
    print(f"\n--- Verifying Graders ---")
    executor = GraderExecutor(info.haiku_path)
    trajectory = haiku_result.get('trajectory', [])
    result = executor.execute(case_data, trajectory)

    for check_result in result.results:
        status = "✓" if check_result.passed else "✗"
        print(f"  {status} [{check_result.check_type}] {check_result.message}")

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
        'sandbox_id': info.sandbox_id,
        'timestamp': datetime.now().isoformat(),
        'haiku_execution': haiku_result,
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
                    'message': r.message
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
        output_path = info.root_path / 'phase6_result.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nResult saved to: {output_path}")

    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
