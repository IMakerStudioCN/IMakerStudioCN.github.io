# 参考三视图角色 · Blender 模型

本工程以用户提供的正面、侧面、背面三视图为外观依据，在 Blender 中用可编辑几何体制作。设计保留酒红短发、灰黑战术夹克、非对称裙摆、腿部装备、短靴、光环与虹彩晶翼，使用偏写实的二次元角色材质。

## 文件

- `Endfield_Operator.blend`：主工程，包含模型、材质、灯光、五个预设相机及内嵌参考图。
- `hero.png`：角色展示渲染。
- `front.png`、`side.png`、`back.png`：同尺度正交三视图。
- `three_views.png`：三视图同屏检查图，工程的第二个场景使用同一角色的关联实例生成。
- `face.png`：面部细节。
- `build_character.py`、`head_hair.py`、`gear_wings.py`：可重建场景的 Blender Python 脚本。
- `finish_character.py`：添加三视图检查场景并保存最终工程。
- `model_stats.json`：建模数据统计。
- `token_usage.md`、`token_usage.json`：本次生成过程已记录的 Token 统计。
- `token_audit.py`：从本地当前会话日志更新统计的脚本。

## 使用

使用 Blender 4.5 或兼容版本打开主工程。单位为米，Z 轴向上，角色正面朝 -Y。对象按头部、服装、装备、晶翼等集合组织；`OPERATOR | master control` 可整体移动角色。渲染使用 Cycles。

参考图在 `90 | Reference images` 集合中，默认隐藏。五个相机分别为三分之四展示、正面、侧面、背面和面部特写，可选择相机后设为活动相机。

这是按参考制作的静态、分部件角色模型。没有动画骨骼、表情形态键或经过人工整理的游戏级变形拓扑；细节与原图仍可能存在差异，不属于官方游戏资产。材质以程序节点与实体几何为主。

## 重建

```powershell
& 'D:\搅拌机\搅拌机\blender.exe' --background --python '.\build_character.py'
```

重建脚本会新建场景，并覆盖本目录同名模型和渲染文件。先另存手工修改过的版本。

## Token 口径

统计依据是本次请求对应的逐响应使用量记录，按响应 ID 去重，包含主线程及本次派生子线程。总 Token 为输入加输出；缓存输入已经包含在输入中，推理输出已经包含在输出中，不能重复相加。

交付前统计是一个时间截点，不包含尚未写入日志的响应，也不包含统计动作之后才生成的最终回复。会话结束后重新运行 `token_audit.py` 可更新数字。Blender 本地建模与渲染本身不消耗语言模型 Token。
