# 新材联发布助手 / 小豆芽拖放增效

用于准备视频文案、核对日期与账号，并向小豆芽内的抖音/视频号页面上传填写；最终发布由人工完成。

## 当前状态

- 当前候选版本：`v0.5.44-r13`，验证版，运营现场完整验收尚未通过。
- 该项目从用户提供的 `v0.5.44` Windows 交付包恢复编译模块后进行窄范围修复，**不是完整原始源码**。
- 本目录包含可审计的修复函数、补丁与重打包脚本、测试、业务背景、决策及验证记录。
- 本次导入对应本地提交 `59d3f84`；本地历史未整体导入团队仓库，避免混入早期环境和运行资料。

## 阅读顺序

1. [PROJECT_STATE.md](PROJECT_STATE.md)：当前事实、版本、风险与下一步。
2. [investigation/ACCEPTANCE.md](investigation/ACCEPTANCE.md)：已验证范围与运营现场剩余条件。
3. [AGENTS.md](AGENTS.md)：项目工程约束。
4. [DECISIONS.md](DECISIONS.md)：修复依据和长期决策。

## 工程布局

- `investigation/*_replacement.py`：恢复后维护的替换函数源代码。
- `investigation/patch_*.py`：受控修改恢复模块。
- `investigation/inspect_package.py`、`read_code.py`：原包解析与静态检查。
- `investigation/build_candidate.py`：重建候选包，核验预期模块变化及其他原包文件一致性。
- `investigation/test_*.py`：模拟与纯函数回归。
- `investigation/verify_*.py`、`run_*.cjs`：真实组件、历史现场实验与浏览器验证脚本。

## 复现前提

需要获授权的原始ZIP、Python **3.11**（对应原包marshal格式），以及相应测试素材/依赖。原包SHA256：

`cc69200bb215ecb875f2d803e23f923ad88038a517105e48c2348b46d8869865`

当前调查脚本保留开发期间的Windows路径、浏览器运行时路径及历史样本引用，克隆后需按实际环境配置。它们不能直接视为跨机器安装程序或CI流水线；应先静态阅读，再运行相关脚本。`verify_live_*`、`verify_actual_draft.py`等可能实际操作外部平台，**不属于可直接批量执行的自动测试**，执行前必须核对目标、授权和已有内容。

恢复、补丁、打包依次使用 `inspect_package.py` / `read_code.py`、对应 `patch_*.py`、`build_candidate.py`；已有恢复文件不要覆盖运营数据。测试依赖恢复模块、候选包和部分本地素材，未准备齐全时不能声称克隆即可通过全部测试。

## 验证与交付边界

r13已覆盖38项自动回归、合成分组/虚拟账号列表、分批加载及失败恢复、部分真实OCR和本机小豆芽读取。**模拟160账号不等于运营160个真实账号；本机成功不等于运营电脑验收；本轮没有完成每日上百条真实发布验收。** 详见验收记录。

应用ZIP、EXE、原视频、恢复的二进制模块、运行日志、运营草稿、账号绑定、密钥均不纳入本次Git导入。r13验证包SHA256：

`f8a4e027d404e31be4b2894556bd7f8de40c0deaa5169958e66f5a34826652e3`

如需分发Windows验证包，应通过经授权的制品存储或Release单独管理，不把大体积二进制和运营数据直接提交到Git。
