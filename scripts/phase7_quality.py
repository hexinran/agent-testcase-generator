#!/usr/bin/env python3
"""
Phase 7: 质量评估脚本

评估测试用例的质量，检查 hacking 风险和难度合理性。

用法:
    python3 phase7_quality.py <case_file> [--phase4-result <file>] [--phase6-result <file>]

评估维度:
1. Hacking 风险评估
2. 难度合理性
3. 信息分散度
4. Query 清晰度
5. 最终质量评级
"""
import sys
import os
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 添加 src 到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))


class QualityAnalyzer:
    """测试用例质量分析器"""

    def __init__(self, case_data: Dict):
        self.case_data = case_data
        self.task = case_data.get('task', {})
        self.environment = case_data.get('environment', [])
        self.reference_solution = case_data.get('reference_solution', [])
        self.graders = case_data.get('graders', [])

        # 难度定义
        self.difficulty_specs = {
            2: {'min_files': 3, 'max_files': 5, 'min_steps': 1, 'max_steps': 2},
            3: {'min_files': 8, 'max_files': 12, 'min_steps': 3, 'max_steps': 4},
            4: {'min_files': 12, 'max_files': 15, 'min_steps': 5, 'max_steps': 6},
            5: {'min_files': 15, 'max_files': 20, 'min_steps': 7, 'max_steps': 8},
            6: {'min_files': 20, 'max_files': 25, 'min_steps': 9, 'max_steps': 10},
            7: {'min_files': 25, 'max_files': 35, 'min_steps': 11, 'max_steps': 15},
        }

    def analyze(self) -> Dict[str, Any]:
        """执行完整的质量分析"""
        results = {
            'hacking_risk': self._analyze_hacking_risk(),
            'difficulty_check': self._check_difficulty(),
            'info_distribution': self._analyze_info_distribution(),
            'query_quality': self._analyze_query_quality(),
            'grader_quality': self._analyze_grader_quality(),
        }

        # 计算总体评级
        results['overall'] = self._calculate_overall_rating(results)

        return results

    def _analyze_hacking_risk(self) -> Dict[str, Any]:
        """分析 hacking 风险"""
        risks = []
        risk_score = 0

        # 检查 grader 中的关键值
        for grader in self.graders:
            for check in grader.get('checks', []):
                params = check.get('params', {})

                # 检查是否是容易猜测的值
                keyword = params.get('keyword', '')
                if keyword:
                    # 简单数字变化（如 5432 -> 5433）
                    if re.match(r'^\d+$', keyword) and len(keyword) <= 4:
                        risks.append(f"简单数字值容易被猜测: {keyword}")
                        risk_score += 2

                    # 常见版本号（v1, v2, v3）
                    if re.match(r'^v\d$', keyword, re.IGNORECASE):
                        risks.append(f"常见版本号容易被猜测: {keyword}")
                        risk_score += 2

                    # 布尔值（True/False）
                    if keyword.lower() in ['true', 'false']:
                        risks.append(f"布尔值容易被猜测: {keyword}")
                        risk_score += 1

        # 检查答案是否在 Query 中直接给出
        query = self.task.get('desc', '')
        for grader in self.graders:
            for check in grader.get('checks', []):
                keyword = check.get('params', {}).get('keyword', '')
                if keyword and keyword in query:
                    risks.append(f"答案值直接出现在 Query 中: {keyword[:30]}")
                    risk_score += 5

        # 检查环境文件中是否有过于明显的提示
        for env_file in self.environment:
            content = env_file.get('content', '')
            # 检查是否有 "should be", "correct value is" 等提示
            if re.search(r'(should be|correct.*is|fix.*to|change.*to)\s*[:=]?\s*\w+', content, re.IGNORECASE):
                risks.append(f"环境文件包含明显提示: {env_file.get('path', '')}")
                risk_score += 3

        level = 'low' if risk_score <= 2 else ('medium' if risk_score <= 5 else 'high')

        return {
            'level': level,
            'score': risk_score,
            'risks': risks
        }

    def _check_difficulty(self) -> Dict[str, Any]:
        """检查难度是否符合规范"""
        difficulty = self.task.get('difficulty', 0)
        spec = self.difficulty_specs.get(difficulty, {})

        file_count = len(self.environment)
        step_count = len(self.reference_solution)

        issues = []

        if spec:
            if file_count < spec['min_files']:
                issues.append(f"文件数 ({file_count}) 低于 D{difficulty} 最小要求 ({spec['min_files']})")
            elif file_count > spec['max_files']:
                issues.append(f"文件数 ({file_count}) 超过 D{difficulty} 最大值 ({spec['max_files']})")

            if step_count < spec['min_steps']:
                issues.append(f"步骤数 ({step_count}) 低于 D{difficulty} 最小要求 ({spec['min_steps']})")
            elif step_count > spec['max_steps']:
                issues.append(f"步骤数 ({step_count}) 超过 D{difficulty} 最大值 ({spec['max_steps']})")

        return {
            'difficulty': difficulty,
            'file_count': file_count,
            'step_count': step_count,
            'spec': spec,
            'passed': len(issues) == 0,
            'issues': issues
        }

    def _analyze_info_distribution(self) -> Dict[str, Any]:
        """分析信息分散度"""
        difficulty = self.task.get('difficulty', 0)

        # D4+ 需要信息分散
        if difficulty < 4:
            return {
                'required': False,
                'passed': True,
                'distribution': 'N/A (D2-D3 不要求)'
            }

        # 分析 reference_solution 中读取的文件
        files_read = set()
        for action in self.reference_solution:
            if action.get('tool') in ['Read', 'Grep', 'Glob']:
                input_data = action.get('input', {})
                file_path = input_data.get('file_path', input_data.get('path', ''))
                if file_path:
                    files_read.add(file_path.replace('{{SANDBOX}}/', ''))

        # 检查是否有干扰文件
        distractor_patterns = ['.bak', '.old', 'staging', 'dev', 'test', 'backup']
        distractor_count = 0
        for env_file in self.environment:
            path = env_file.get('path', '')
            if any(p in path.lower() for p in distractor_patterns):
                distractor_count += 1

        passed = len(files_read) >= 3 and distractor_count >= 1

        return {
            'required': True,
            'files_read': list(files_read),
            'files_read_count': len(files_read),
            'distractor_count': distractor_count,
            'passed': passed,
            'distribution': f"{len(files_read)} 个关键文件, {distractor_count} 个干扰文件"
        }

    def _analyze_query_quality(self) -> Dict[str, Any]:
        """分析 Query 质量"""
        query = self.task.get('desc', '')
        issues = []

        # 检查长度
        if len(query) < 20:
            issues.append("Query 过短")
        if len(query) > 500:
            issues.append("Query 过长")

        # 检查是否包含具体命令
        command_patterns = [
            r'(run|execute|use)\s+(the\s+)?(command|cmd)',
            r'`[^`]+`',  # 代码块
            r'--\w+',    # 命令行参数
        ]
        for pattern in command_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                issues.append("Query 包含具体命令或参数")
                break

        # 检查是否包含具体文件路径
        if re.search(r'[\\/][\w.-]+[\\/][\w.-]+', query):
            issues.append("Query 包含具体文件路径")

        return {
            'length': len(query),
            'passed': len(issues) == 0,
            'issues': issues
        }

    def _analyze_grader_quality(self) -> Dict[str, Any]:
        """分析 Grader 质量"""
        issues = []

        total_checks = 0
        content_checks = 0

        for grader in self.graders:
            for check in grader.get('checks', []):
                total_checks += 1
                check_type = check.get('check', '')

                # 检查是否只验证文件存在
                if check_type == 'file_exists':
                    issues.append(f"只检查文件存在，应验证内容: {check.get('params', {}).get('path', '')}")
                elif 'content' in check_type or 'match' in check_type:
                    content_checks += 1

        # 检查数量
        if total_checks < 2:
            issues.append(f"Check 数量过少 ({total_checks})，建议至少 2 个")

        return {
            'total_checks': total_checks,
            'content_checks': content_checks,
            'passed': len(issues) == 0,
            'issues': issues
        }

    def _calculate_overall_rating(self, results: Dict) -> Dict[str, Any]:
        """计算总体评级"""
        score = 100

        # 扣分项
        if results['hacking_risk']['level'] == 'high':
            score -= 30
        elif results['hacking_risk']['level'] == 'medium':
            score -= 15

        if not results['difficulty_check']['passed']:
            score -= 20

        if results['info_distribution']['required'] and not results['info_distribution']['passed']:
            score -= 20

        if not results['query_quality']['passed']:
            score -= 10

        if not results['grader_quality']['passed']:
            score -= 10

        # 评级
        if score >= 90:
            level = 'excellent'
        elif score >= 70:
            level = 'good'
        elif score >= 50:
            level = 'acceptable'
        else:
            level = 'needs_improvement'

        return {
            'score': max(0, score),
            'level': level,
            'recommendation': self._get_recommendation(results)
        }

    def _get_recommendation(self, results: Dict) -> str:
        """生成改进建议"""
        recommendations = []

        if results['hacking_risk']['level'] in ['medium', 'high']:
            recommendations.append("降低 hacking 风险：使用更复杂的答案值，确保必须从环境中读取")

        if not results['difficulty_check']['passed']:
            recommendations.append("调整文件数或步骤数以符合难度要求")

        if results['info_distribution']['required'] and not results['info_distribution']['passed']:
            recommendations.append("增加信息分散度：将关键信息分散到更多文件，添加干扰文件")

        if not results['query_quality']['passed']:
            recommendations.append("优化 Query：移除具体命令和路径，保持适当模糊度")

        if not results['grader_quality']['passed']:
            recommendations.append("改进 Grader：增加内容验证，不只检查文件存在")

        return "; ".join(recommendations) if recommendations else "质量良好，无需改进"


def main():
    parser = argparse.ArgumentParser(description='Phase 7: 质量评估')
    parser.add_argument('case_file', help='测试用例 JSON 文件')
    parser.add_argument('--phase4-result', help='Phase 4 结果文件')
    parser.add_argument('--phase6-result', help='Phase 6 结果文件')
    parser.add_argument('--output', help='输出结果文件')
    parser.add_argument('--json', action='store_true', help='只输出 JSON')

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

    if not args.json:
        print(f"\n{'='*60}")
        print(f"Phase 7: 质量评估")
        print(f"{'='*60}")
        print(f"Case ID: {case_id}")

    # 执行质量分析
    analyzer = QualityAnalyzer(case_data)
    results = analyzer.analyze()

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        # Hacking 风险
        print(f"\n--- Hacking 风险分析 ---")
        print(f"  风险等级: {results['hacking_risk']['level'].upper()}")
        print(f"  风险分数: {results['hacking_risk']['score']}")
        for risk in results['hacking_risk']['risks']:
            print(f"  ⚠ {risk}")

        # 难度检查
        print(f"\n--- 难度检查 ---")
        dc = results['difficulty_check']
        status = "✓" if dc['passed'] else "✗"
        print(f"  {status} D{dc['difficulty']}: {dc['file_count']} 文件, {dc['step_count']} 步骤")
        for issue in dc['issues']:
            print(f"  ⚠ {issue}")

        # 信息分散度
        print(f"\n--- 信息分散度 ---")
        id_ = results['info_distribution']
        if id_['required']:
            status = "✓" if id_['passed'] else "✗"
            print(f"  {status} {id_['distribution']}")
        else:
            print(f"  {id_['distribution']}")

        # Query 质量
        print(f"\n--- Query 质量 ---")
        qq = results['query_quality']
        status = "✓" if qq['passed'] else "✗"
        print(f"  {status} 长度: {qq['length']} 字符")
        for issue in qq['issues']:
            print(f"  ⚠ {issue}")

        # Grader 质量
        print(f"\n--- Grader 质量 ---")
        gq = results['grader_quality']
        status = "✓" if gq['passed'] else "✗"
        print(f"  {status} {gq['total_checks']} 个 check ({gq['content_checks']} 个内容验证)")
        for issue in gq['issues']:
            print(f"  ⚠ {issue}")

        # 总体评级
        print(f"\n{'='*60}")
        overall = results['overall']
        print(f"总体评分: {overall['score']}/100 ({overall['level'].upper()})")
        print(f"改进建议: {overall['recommendation']}")
        print(f"{'='*60}")

    # 保存结果
    output_data = {
        'phase': 7,
        'case_id': case_id,
        'timestamp': datetime.now().isoformat(),
        'quality_analysis': results
    }

    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        if not args.json:
            print(f"\nResult saved to: {output_path}")

    # 根据质量评级返回退出码
    if results['overall']['level'] in ['excellent', 'good']:
        sys.exit(0)
    elif results['overall']['level'] == 'acceptable':
        sys.exit(0)  # 可接受，返回 0
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
