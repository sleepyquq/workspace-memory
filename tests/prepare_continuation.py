"""在系统临时目录准备独立会话的合成输入，不运行 Agent、不修改已安装 skill。"""

from pathlib import Path
import shutil
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def prepare() -> Path:
    run = Path(tempfile.mkdtemp(prefix="workspace-memory-continuation-"))
    project = run / "project"
    shutil.copytree(ROOT / "examples" / "editor-workspace", project)
    candidate = run / "skills" / "workspace-memory"
    candidate.mkdir(parents=True)
    shutil.copy2(ROOT / "SKILL.md", candidate / "SKILL.md")
    for folder in ("references", "assets", "scripts", "examples"):
        shutil.copytree(ROOT / folder, candidate / folder,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    memory = project / ".workspace-memory"
    (memory / "decisions" / "overwrite-and-undo.md").unlink()
    (memory / "decisions" / "authoring-safety.md").write_text("""---
id: authoring-safety
type: decision
status: active
summary: 服务端权限、参数验证、原子提交和同题冲突保留教师版本。
updated: 2026-10-20
---
# 编辑安全边界
## Decision
- 只有具有编辑权限的调用者可以修改草稿。
- 提交前验证所有目标题和非空文本，整批原子提交。
- 同题内容与生成开始时基线冲突时保留教师版本，拒绝 AI 写入。
## Rationale
- 权限和事务限制防止越权与半批提交；冲突拒绝用于保护人工编辑。
## Related
- [[topics/editor]]
""", encoding="utf-8")
    (memory / "topics" / "editor.md").write_text("""---
id: editor
type: topic
status: active
summary: 编辑模型、整包撤销及待接入的任务卡片。
updated: 2026-10-22
---
# 编辑与撤销
## Current Model
- 当前 `editor.py` 只实现内存原型；提交遵守 [[decisions/authoring-safety]]。
- 顶部编辑器撤销保存整包快照，撤销会恢复全部题目。
- 任务卡片撤销尚未实现。
## Durable Details
- `task_id` 是任务唯一键；恢复数据未来使用 `undo_snapshot` 字段。
- 已讨论的 HTTP 入口为 `POST /api/drafts/:draftId/revert`，目前没有 HTTP 服务。
## Open Issues
- 真实浏览器下尚未检查未保存人工修改对任务卡撤销的影响。
## Related
- [[decisions/authoring-safety]]
- [[topics/release]]
""", encoding="utf-8")
    (memory / "topics" / "device-trial.md").write_text("""---
id: device-trial
type: topic
status: dormant
summary: 实体离线设备联调等待硬件到货。
updated: 2026-10-18
---
# 离线设备联调
## Open Issues
- 设备负责人等待硬件到货，恢复日期未知。没有连接设备或执行实体测试。
## Durable Details
- 使用协议 `device-v1`；恢复时先核对真实版本再联调。
""", encoding="utf-8")
    (memory / "index.md").write_text("""# Memory Index
## Task Routing
| Area | Canonical notes |
| --- | --- |
| 编辑、覆盖、撤销 | [[topics/editor]] |
| 导出、发布、生产 | [[topics/release]] |
| 设备、离线、联调 | [[topics/device-trial]] |
## Topics
- [[topics/editor]] — 编辑模型、整包撤销及待接入的任务卡片。
- [[topics/release]] — 导出开关的环境状态及下一步授权。
- [[topics/device-trial]] — 实体离线设备联调等待硬件到货。
## Decisions
- [[decisions/authoring-safety]] — 当前编辑安全边界。
""", encoding="utf-8")
    # 历史记录有重复完成事项，也有仍未解决的事项，不能靠保留最后一行处理。
    history = "\n".join(
        f"- 2026-10-{day:02d} 第 {round_number} 轮：导出开关本地测试通过；生产尚未部署。见 [[topics/release]]。\n"
        f"- 2026-10-{day:02d} 第 {round_number} 轮：按钮标签本地检查完成，没有新增阻塞。"
        for round_number, day in enumerate(range(1, 23), 1)
    )
    history += "\n" + "\n".join(
        "- 编辑器旧模型的验证仅覆盖内存层，不代表浏览器、HTTP 服务或生产部署已验收。"
        for _ in range(45)
    )
    (memory / "state.md").write_text(f"""# Current State
Last updated: 2026-10-18
## 近期记录
{history}
## Current Focus
- 继续编辑器内存原型：[[topics/editor]]。
## Active Topics
- [[topics/editor]]
- [[topics/release]]
## Live Issues
- 导出开关本地修复已验证；生产仍为 `editor-r1`，待发布负责人获得窗口批准：[[topics/release]]。
- 浏览器未保存修改的真实验收未完成：[[topics/editor]]。
- 设备负责人等待硬件，恢复日期未知：[[topics/device-trial]]。
## Next Actions
- 确认下一轮编辑与撤销的行为，继续实现。
- 不把本地测试通过当作生产问题已关闭。
""", encoding="utf-8")

    (project / "editor.py").write_text('''"""合成编辑器的内存原型；不包含数据库、HTTP 或 UI。"""


class Editor:
    def __init__(self, items):
        self.items = dict(items)
        self.editor_history = []
        self.tasks = {}

    def manual_edit(self, item_id, text):
        self.editor_history.append(dict(self.items))
        self.items[item_id] = text

    def apply_ai(self, task_id, updates, generation_base, can_edit=True):
        if not can_edit:
            raise PermissionError("edit denied")
        for item_id, text in updates.items():
            if item_id not in self.items or not isinstance(text, str) or not text:
                raise ValueError("invalid update")
            if self.items[item_id] != generation_base[item_id]:
                raise ValueError("teacher version conflict")
        self.items.update(updates)

    def undo_editor(self, item_id):
        if self.editor_history:
            self.items = self.editor_history.pop()

    def undo_task(self, task_id):
        raise NotImplementedError("task undo not implemented")
''', encoding="utf-8")
    (project / "test_editor.py").write_text('''import unittest
from editor import Editor


class EditorTest(unittest.TestCase):
    def test_permission_denial_preserves_items(self):
        editor = Editor({"q1": "original"})
        with self.assertRaises(PermissionError):
            editor.apply_ai("t1", {"q1": "AI"}, dict(editor.items), can_edit=False)
        self.assertEqual(editor.items, {"q1": "original"})

    def test_invalid_batch_is_atomic(self):
        editor = Editor({"q1": "first", "q2": "second"})
        with self.assertRaises(ValueError):
            editor.apply_ai("t1", {"q1": "AI", "q2": ""}, dict(editor.items))
        self.assertEqual(editor.items, {"q1": "first", "q2": "second"})


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
    return run


if __name__ == "__main__":
    print(prepare())
