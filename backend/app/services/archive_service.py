from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json

try:  # openai 可选：缺失时走确定性 fallback
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

load_dotenv()


class ArchiveService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)

    def generate_archive_summary(self, transcripts: List[Dict[str, Any]],
                                  craftsmen: List[Dict[str, Any]],
                                  audio_metadata: Dict[str, Any]) -> Dict[str, Any]:
        full_transcript = "\n\n".join([
            f"[{t.get('speaker_label', '未知')} - {t.get('predicted_school', '未知流派')}]\n{t['content']}"
            for t in transcripts
        ])

        prompt = f"""
你是一位传统弓箭制作工艺的档案管理员。请根据以下会议记录，生成一份结构化的工艺档案摘要。

会议背景信息：
- 木工坊环境: {json.dumps(audio_metadata.get('ambience_profile', {}), ensure_ascii=False)}
- 参与匠人: {json.dumps([c['name'] + '(' + c.get('school', '未知流派') + ')' for c in craftsmen], ensure_ascii=False)}

口传知识转录内容：
{full_transcript}

请按照以下结构生成档案：
1. 会议主题（一句话概括）
2. 核心工艺要点（提取胎角比例、训弓技巧、材料选择等关键信息）
3. 流派对比分析（如有不同流派匠人发言，分析其工艺差异）
4. 传承价值评估（评估这些口传知识的非遗保护价值）
5. 关键词列表（提取10-15个核心关键词）

请以JSON格式返回，包含以下字段：
- title: 会议主题
- summary: 详细摘要（300-500字）
- key_points: 核心工艺要点数组
- school_analysis: 流派分析对象
- heritage_value: 传承价值评估
- keywords: 关键词数组
- content: 完整结构化内容
"""

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "你是一位专业的非物质文化遗产档案管理员，擅长整理传统工艺口传知识。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)
                return result
            except Exception as e:
                print(f"OpenAI API error: {e}")
                return self._generate_summary_fallback(transcripts, craftsmen, audio_metadata)
        else:
            return self._generate_summary_fallback(transcripts, craftsmen, audio_metadata)

    def _generate_summary_fallback(self, transcripts: List[Dict[str, Any]],
                                     craftsmen: List[Dict[str, Any]],
                                     audio_metadata: Dict[str, Any]) -> Dict[str, Any]:
        all_content = " ".join([t['content'] for t in transcripts])

        key_points = []
        keywords = ["传统弓箭", "工艺传承"]

        if "胎角" in all_content:
            key_points.append("涉及胎角比例相关工艺")
            keywords.append("胎角")
        if "训弓" in all_content:
            key_points.append("包含训弓技巧传授")
            keywords.append("训弓")
        if "木材" in all_content:
            key_points.append("讨论了木材选择和处理")
            keywords.append("木材")
        if "角弓" in all_content:
            key_points.append("涉及角弓制作工艺")
            keywords.append("角弓")
        if "比例" in all_content:
            key_points.append("提及材料比例和尺寸要求")
            keywords.append("比例")

        schools = set()
        for t in transcripts:
            school = t.get('predicted_school')
            if school and school != "未知流派":
                schools.add(school)

        return {
            "title": "传统弓箭制作工艺传承交流会议",
            "summary": f"本次会议共{len(craftsmen)}位匠人参与，来自{len(schools)}个不同流派。"
                      f"会议围绕传统弓箭制作工艺展开交流，涵盖了{len(key_points)}个核心工艺要点。"
                      f"这些口传知识对于非遗保护和工艺传承具有重要价值。",
            "key_points": key_points if key_points else ["传统工艺交流", "技艺传承讨论"],
            "school_analysis": {
                "schools_involved": list(schools),
                "differences": "需要进一步分析流派工艺差异"
            },
            "heritage_value": "高",
            "keywords": keywords,
            "content": {
                "transcripts": transcripts,
                "craftsmen": craftsmen,
                "metadata": audio_metadata
            }
        }

    def generate_html_archive(self, archive_data: Dict[str, Any]) -> str:
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{archive_data.get('title', '工艺档案')} - 弓道纪要</title>
    <style>
        body {{ font-family: 'Noto Serif SC', serif; line-height: 1.8; max-width: 900px; margin: 0 auto; padding: 40px 20px; color: #333; }}
        h1 {{ color: #8B4513; border-bottom: 3px solid #D2691E; padding-bottom: 15px; }}
        h2 {{ color: #A0522D; margin-top: 30px; }}
        .summary {{ background: #FFF8DC; padding: 20px; border-radius: 8px; border-left: 5px solid #D2691E; }}
        .key-points {{ list-style: none; padding: 0; }}
        .key-points li {{ background: #F5DEB3; margin: 10px 0; padding: 12px 18px; border-radius: 6px; }}
        .keywords span {{ display: inline-block; background: #DEB887; color: #4A3728; padding: 5px 12px; margin: 5px; border-radius: 20px; font-size: 0.9em; }}
        .school-analysis {{ background: #FAEBD7; padding: 20px; border-radius: 8px; }}
        .heritage-value {{ font-size: 1.2em; font-weight: bold; color: #8B4513; }}
        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <h1>🏹 {archive_data.get('title', '传统弓箭制作工艺档案')}</h1>
    
    <div class="summary">
        <h2>📜 档案摘要</h2>
        <p>{archive_data.get('summary', '')}</p>
    </div>

    <h2>🔑 核心工艺要点</h2>
    <ul class="key-points">
        {''.join([f'<li>📌 {point}</li>' for point in archive_data.get('key_points', [])])}
    </ul>

    <div class="school-analysis">
        <h2>🎭 流派分析</h2>
        <p><strong>涉及流派：</strong>{', '.join(archive_data.get('school_analysis', {}).get('schools_involved', ['未知']))}</p>
        <p><strong>工艺差异：</strong>{archive_data.get('school_analysis', {}).get('differences', '')}</p>
    </div>

    <h2>💎 传承价值评估</h2>
    <p class="heritage-value">{archive_data.get('heritage_value', '待评估')}</p>

    <h2>🏷️ 关键词</h2>
    <div class="keywords">
        {''.join([f'<span>{kw}</span>' for kw in archive_data.get('keywords', [])])}
    </div>

    <div class="footer">
        <p>弓道纪要 - 传统弓箭制作工艺传承平台</p>
        <p>本档案由AI辅助生成，仅供非遗保护参考</p>
    </div>
</body>
</html>
"""
        return html_content


archive_service = ArchiveService()
