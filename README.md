# One Arrow Game · 一箭又一箭

一个使用 Python 与 Pygame 编写的原创点击式箭头解谜游戏。玩家需要观察同一行或同一列上的阻挡关系，按正确顺序点击箭头，让所有箭头飞出棋盘。

![游戏主界面](assets/screenshots/03_game.png)

## 功能亮点

- 完整的开始、关卡选择、游戏、通关和失败界面
- 上、下、左、右四种箭头与严格的边界/路径检测
- 飞出淡出动画，以及红色闪烁、晃动和 `BLOCKED` 碰撞反馈
- 3 次失误机会、实时计时、得分与 1–3 星评价
- 5 个原创关卡，均通过自动求解器验证可通关
- 提示、撤销、重新开始、关卡解锁与本地最佳成绩
- AI 自动求解当前局面，并以提示方式给出下一支安全箭头
- 原创循环轻音乐，以及飞出、点错、失败、通关等独立音效
- 11 个自动化测试覆盖作业 T01–T06、扩展功能和音频资源完整性
- 无外部图片或音频素材，箭头和界面均由 Pygame 矢量绘制

## 环境与运行

推荐使用 Python 3.10–3.12。

```bash
python -m venv .venv
```

Windows：

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

macOS / Linux：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

如果系统的命令名是 `py` 或 `python3`，将上述 `python` 替换为对应命令即可。

## 操作说明

- 鼠标左键：点击箭头或按钮
- `H`：提示一支当前可安全移除的箭头
- `Z`：撤销上一步（成功或失败操作均可撤销）
- `R`：重新开始当前关卡
- `M`：开启或关闭全部音乐和音效
- `Esc`：返回开始界面

规则很简单：点击箭头后，程序沿箭头方向逐格扫描。前方没有箭头时，它会飞出棋盘；前方存在箭头时，本次点击失败并扣除一次失误机会。清空全部箭头即可过关。

## 界面展示

| 开始界面 | 关卡选择 |
| --- | --- |
| ![开始界面](assets/screenshots/01_start.png) | ![关卡选择](assets/screenshots/02_levels.png) |

| 通关界面 | 失败界面 |
| --- | --- |
| ![通关界面](assets/screenshots/04_clear.png) | ![失败界面](assets/screenshots/05_failed.png) |

## 核心设计

项目将规则与界面分开：`GameState` 不依赖 Pygame，所以路径判断和游戏流程可以自动测试；`GameApp` 只负责输入、绘制和动画。

路径检测从箭头相邻格开始，使用方向增量不断前进，直到发现阻挡或越过边界：

```python
dr, dc = arrow.direction.delta
row, col = arrow.row + dr, arrow.col + dc
while 0 <= row < size and 0 <= col < size:
    if (row, col) in arrows:
        return arrows[(row, col)]
    row += dr
    col += dc
return None
```

AI 提示使用广度优先搜索：状态是“尚未移除的坐标集合”，边是“移除一支当前无遮挡箭头”。搜索到空集合时，所得路径就是完整通关序列。相同的求解器也用于测试所有关卡是否可解。

## 自动测试

```bash
python -m unittest discover -s tests -v
```

当前结果：11 项测试全部通过。详细记录见 [测试报告](docs/TEST_REPORT.md)。

如需重建 README 截图：

```bash
python main.py --capture assets/screenshots
```

## 项目结构

```text
OneArrowGame/
├── main.py                 # Pygame 入口、界面、动画与流程
├── game_state.py           # 可独立测试的核心规则与求解器
├── arrow.py                # 箭头数据对象
├── level.py                # 5 个原创关卡
├── constants.py            # 方向、状态和常量
├── ui.py                   # 按钮、配色与矢量箭头
├── audio.py                # 音乐、音效播放与静音控制
├── tools/generate_audio.py # 原创音频生成脚本
├── tests/test_game_state.py
├── assets/screenshots/
├── docs/
│   ├── AIGC_RECORD.md
│   ├── BLOG_DRAFT.md
│   ├── PSP.md
│   └── TEST_REPORT.md
└── requirements.txt
```

## 开发与资料说明

- 作业要求来源：课程提供的《2026 秋软件工程个人作业（第二次）》PDF。
- 游戏核心玩法仅参考题目描述；代码、关卡、配色、图形和截图均为本项目原创生成。
- 背景音乐和音效由项目脚本程序化合成，未使用第三方音乐素材。
- 开发使用 Codex 辅助需求拆解、编码、调试、关卡验证和文档整理。真实过程见 [AIGC 使用记录](docs/AIGC_RECORD.md)。
- 游戏进度保存在项目目录的 `.one_arrow_save.json`，该文件已加入 `.gitignore`，不会上传个人游戏数据。

## 提交前 3 项个人化

1. 将 [博客草稿](docs/BLOG_DRAFT.md) 顶部的学号和作业链接替换为本人信息。
2. 按本人实际投入时间复核 [PSP 表](docs/PSP.md)。
3. 发布博客前再次运行自动测试并完整试玩前三关。

