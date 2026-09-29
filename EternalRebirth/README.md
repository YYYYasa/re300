# 300 英雄 · 永恒重生

UE 5.8.3 本地地图重制工程。首版优先实现永恒竞技场的高画质漫游与双画风展示。

## 启动

- `Start_Realistic.cmd`：写实灯光风格。
- `Start_Anime.cmd`：现代二次元风格。
- `Open_Editor.cmd`：打开可编辑的 UE 工程。
- `Start_Heroes.cmd`：打开首批英雄展示关卡。
- `Start_Combat.cmd`：打开 H100 单英雄对战原型。
- `Start_Battle.cmd`：打开融合原地图的 H100 对战关卡（本轮更新入口）。

依赖本机 `D:\Epic Games\UE_5.8`。漫游通过 UnrealEditor 的独立游戏模式运行。

## 操作

| 按键 | 功能 |
| --- | --- |
| WASD / 鼠标 | 自由飞行 / 转动视角 |
| Q / E | 下降 / 上升 |
| Shift | 加速 |
| Tab | 在两种画风间切换 |
| 1–5 | 预设观景点 |
| T | 环绕航拍 |
| H | 隐藏界面 |
| F | 晴天 → 雨天 → 雪天循环切换 |
| G | 75% TSR / 原生分辨率 |
| F9 | 拍照，保存到 Saved/Screenshots |
| Esc | 退出 |

## 地图来源与重制内容

只读提取自本机 `D:\JumpGame\300Hero`。通过 JMP 索引、JumpX 网格和 xmap 场景数据重建 `lm4JJCmap`，对应客户端数据中的永恒竞技场。

- 324 个可见静态场景实例（含地形与水面），合并为 30 个分区网格；剔除 64 个遮挡地表的行走辅助面。
- 211 张原贴图转换为 PNG，再导入 UE。
- 新建材质：PBR 光照与表面细节、二次元分段明暗与深度/法线描边、Single Layer Water 动态河水。
- 地表使用独立材质，避免程序法线造成的斑纹；水面使用反射、透射、吸收、缓慢起伏和两层移动微波纹；草与叶片有轻微风动。写实日光提高了天空补光、缩短并软化投影。
- 新建光照：Lumen、虚拟阴影、天空大气与体积雾；26 个场景分区启用 Nanite，4 个水面分区使用普通网格。
- 新建原创远景山体、传送门动态光效与局部补光，用于增强低机位漫游画面。
- 新建原生 C++ 漫游控制、观景点、双画风切换与 HUD。
- 晴、雨、雪天气循环：雨滴和雪花跟随视角，地面水坑与积雪逐步形成，晴天逐步干燥和融化；三种天气有独立循环环境音。

原客户端没有被修改。漫游关卡不包含对战逻辑；独立战斗关卡提供下文的单英雄训练玩法。工程尚不包含联网、动态防御塔或商店系统。原模型与手绘贴图仍是美术基础，写实模式主要重做材质响应与光照，并非将全部原资源替换为摄影测量资产。

## 英雄导入进度

首批从本机客户端只读提取了编号 013、100、101 的英雄模型及引用贴图，转换为 UE 骨骼网格、骨架、材质和每名英雄的 Idle、Run、Attack 动画资源。资源位于 `/Game/Art/Heroes/H013`、`H100`、`H101`；展示关卡为 `/Game/Maps/HeroShowcase`。展示关卡已实机截图验证三名英雄的模型、材质与站立方向。动画资源已导入，但尚未在运行中的角色上验证播放效果，当前展示关卡使用静态姿态。其余英雄尚待分批导入。

新英雄的可复用流程位于 `../Tools/prepare_heroes.py`、`../Tools/convert_heroes_blender.py`、`../Tools/import_heroes.py` 和 `../Tools/materialize_heroes.py`。原客户端文件保持只读。关卡生成脚本 `../Tools/build_hero_gallery.py` 记录了源模型所需的网格组件 180° 方向修正。

## 单英雄对战原型

独立关卡 `/Game/Maps/HeroCombatPrototype` 使用 H100 作为可控英雄，H013 作为训练假人。鼠标右键点击地面移动（按住右键可持续更新目标点），滚轮平滑缩放视距，WASD 可辅助移动；移动和攻击时英雄会面向正确方向。鼠标左键普攻，命中 245 厘米内目标造成 75 点伤害；Q 释放前方范围技能，造成 165 点伤害且有 6 秒冷却；R 重置假人，Esc 退出。新版 HUD 显示英雄与假人血量、技能冷却、视距和操作提示。假人生命值降为零后会在 3 秒后重置。

Idle、Run、Attack 动画已经在运行中的 H100 上分别截图核对，普攻与技能伤害、假人倒下及重置通过自动演练。木偶的颠倒变换已在关卡资源中修正，英雄与木偶朝向也已通过新截图核对。截图位于 `Saved/Screenshots/Combat_*.png`，运行日志位于 `../Research/combat_facing_runtime.log`。玩法与关卡分别由 `Source/EternalRebirth/CombatPrototype.cpp` 和 `../Tools/build_combat_arena.py` 实现。此原型只实现单机训练场，不包含联网、完整技能组和敌方 AI。

复制的正式战斗展示关卡 `/Game/Maps/EternalCombat` 以 `EternalShowcase` 为底图，在中央路线放置 H100、训练假人和独立行走碰撞面，保留原地图。双击 `Start_Battle.cmd` 或运行 `Launch.ps1 -Mode Battle` 进入。战斗操作沿用上面的原型，另可在局内按 **Tab** 切换写实／现代二次元滤镜；HUD 会显示当前风格。关卡生成脚本为 `../Tools/build_eternal_combat.py`。

新地图已在 UE 5.8.3 中完成实机验证：H100 的 Idle／Run／Attack 资源均加载，移动、普攻、技能命中、假人倒下与复位、滚轮缩放均有运行日志；滤镜切换前后的截图为 `Saved/Screenshots/EternalCombat_Realistic.png` 和 `EternalCombat_Anime.png`，验证日志为 `../Research/eternal_combat_gameplay.log` 与 `../Research/eternal_combat_runtime_final.log`。

当前为自由飞行漫游，尚未加入步行碰撞。若之前已经打开早期版本，请保存并退出后用上述入口重新启动；默认关卡是 `EternalShowcase`，早期 `EternalGrounds` 保留用于开发比较。

### H100 战斗升级（2026-09-28）

- 战斗关卡的滚轮视距范围为 280–4500 厘米，镜头平滑趋近目标距离。
- 从客户端恢复 64 块辅助行走面，合并为 `/Game/Art/Collision/SM_Arena_Walkable`，使用真实三角面查询地面高度。移除了战斗地图原先 580×450 厘米的坐标限制。右键点击/按住移动，WASD 辅助移动；不包含自动绕障寻路。
- Idle/Run 使用 `/Game/Art/Heroes/H100/BS_H100_Locomotion`，依据实际移动速度混合；到点减速、松键减速、转身和镜头都有平滑过渡。
- HUD 使用原创深色半透明底、细金线、角色头像、目标血条、浮动伤害和环形技能冷却。保留 Tab 切换画风、R 重置目标。
- H100 默认造型源文件里的 19 段命名动作均已导入（另保留原 Idle/Run/Attack 别名）。普通攻击交替使用两段攻击动作，Q 使用 `single_skill_02` 动作。其余动作保存在资源浏览器中，尚未全部绑定按键或游戏状态。
- 基础造型特效目录中的 17 个源文件已提取，其中 13 个有网格并转换为 UE 静态网格；导入了 32 张特效贴图、对应材质、5 张 UI 图。25 个原配置/音频文件保存在 SourceArt 中。
- 普攻命中与 Q 范围技能使用原贴图重建可见效果，替换调试线框。原引擎的粒子规则、特效骨骼动画和 `.bank` 音频尚未完整转换为 UE 可播放资产；4 个纯粒子文件保留源数据。此批针对 H100 默认造型，不包括其它皮肤。

资源清单：`SourceArt/Effects/H100/manifest.json`、`ue_import_report.json`。重建脚本：`../Tools/import_h100_all_animations.py`、`build_h100_locomotion.py`、`convert_arena_walkable_blender.py`、`import_arena_walkable.py`、`prepare_h100_effects.py`、`convert_h100_effects_blender.py`、`import_h100_effects.py`。先提取，再转换 FBX，最后执行 UE 导入；不要只重新提取后跳过转换步骤。

## 可重建文件

- `../Tools/inspect_client.py`：读取 JMP 索引并定向提取。
- `../Tools/map_research.py`：解析客户端地图配置。
- `../Tools/convert_battlefield.py`：在 Blender 中恢复场景网格并导出 FBX。
- `../Tools/convert_textures.py`：使用 Pillow 转换旧 DDS 贴图。
- `../Tools/build_scene.py`：在 UE 编辑器中创建材质、地图与灯光。
- `../Tools/build_showcase.py`：创建修正后的展示关卡 `/Game/Maps/EternalShowcase`，保留早期关卡供比较。
- `../Tools/polish_showcase.py`：加入远景山体与传送门；`../Tools/finish_environment.py`：完成远景照明。
- `../Tools/finalize_materials.py`：保存 Nanite 材质实例设置。
- `../Tools/repair_surface.py`：修复地表材质、水面反射与写实光照。
- `../Tools/light_polish.py`：添加河道与双方基地的柔和局部补光。
- `../Tools/animate_environment.py`：生成反射河水材质、设置四块水面网格，并为四组植被贴图添加风动。
- `../Tools/build_weather_materials.py`：生成雨天水坑、湿表面和雪层材质；`../Tools/build_weather_effects.py`：导入环境音与雨雪粒子材质；`../Tools/build_weather_audio.py`：单独更新三种循环环境音。
- `../Tools/generate_weather_audio.py`：以确定性种子生成三条原创循环天气环境音 WAV。
- `Launch.ps1 -Mode Build`：编译本项目 C++ 模块。
- `Launch.ps1 -Mode RebuildScene`：按顺序重新生成网格、关卡、远景和传送门；运行前先关闭本工程的 UE 窗口。
- `Launch.ps1 -Mode Capture`：自动截取两种风格并记录切换验证结果。
- `Launch.ps1 -Mode Gallery`：以原生 1600×900 分辨率自动截取五个机位的两种风格。
- `Launch.ps1 -Mode Motion -View 5`：同一机位间隔四秒截两帧，用于检查河水与植被的动态变化。
- `Launch.ps1 -Mode WeatherCapture -View 5`：自动截取雨雪积累、晴天消退的过程并写出 `Saved/weather-test.json`。

兼容编译器 LLVM 20.1.8 保存在 `../Tools/LLVM`，仅在构建进程中设置路径。原始提取数据及索引位于 `../Research`。

## 工具来源

JMP 格式参考 [Anran-233/300ResourceBrowser](https://github.com/Anran-233/300ResourceBrowser)（Unlicense）；JumpX 结构参考 [Gamepiaynmo/JumpXToolchain](https://github.com/Gamepiaynmo/JumpXToolchain)（MIT）。两者源码与许可证保留在 `../Tools`。

## 验证状态

C++ 编辑器模块已编译通过，展示关卡已由 UE 5.8.3 保存。完成了 5 个观景点 × 2 种风格的 1600×900 实机截图，并验证了风格切换与全部观景点。水草更新后又在河道机位间隔四秒截图：水面与草区明显变化，静态地面基本不变。天气系统也完成了 1600×900 实机循环测试：雨雪粒子材质编译正常，三条环境音成功加载，雨天积水、雪天积雪与回晴后的消退均通过自动验证。当前地图构建报告位于 `Saved/build-report.json`，切换验证结果位于 `Saved/smoke-test.json`，天气结果位于 `Saved/weather-test.json`，截图在 `Saved/Screenshots`。
