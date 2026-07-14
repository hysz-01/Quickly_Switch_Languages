# Quick Language Switcher - 开发经历与项目信息

## 项目概述

Quick Language Switcher 是一个 Blender 插件，旨在为频繁切换界面语言的用户提供快速访问常用语言的功能。插件在顶部菜单栏添加了一个 "Switch Languages to" 菜单，允许用户一键切换语言。

## 开发时间线

### 第一阶段：需求分析与设计

1. **需求澄清**：
   - 目标用户：所有需要频繁切换 Blender 界面语言的用户
   - 菜单位置：顶部菜单栏右侧
   - 功能：语言收藏夹，快速切换
   - 持久化：保存语言偏好
   - 双语支持（未来功能）

2. **技术调研**：
   - 研究了现有的类似插件：`toggle_language` 和 `secondary_language`
   - 确认 Blender API 支持动态切换语言：`bpy.context.preferences.view.language = language_code`
   - 确定存储方案：混合使用 Blender 偏好设置和外部 JSON 文件

### 第二阶段：实现

1. **项目结构搭建**：
   - 创建基本插件结构：`__init__.py`, `blender_manifest.toml`, `languages.json`
   - 实现热重载支持

2. **语言管理器**：
   - 实现 `LanguageManager` 类，处理 JSON 文件的读写操作
   - 支持添加、删除、更新收藏语言列表
   - 添加输入验证，防止添加空语言条目

3. **菜单系统**：
   - 创建 `LANGUAGE_SWITCHER_MT_menu` 菜单类
   - 实现语言切换操作符
   - 集成到顶部菜单栏

4. **设置面板**：
   - 实现 `QuickLanguageSwitcherPreferences` 类
   - 添加收藏语言管理界面
   - 实现动态语言选择弹出菜单

5. **集成与测试**：
   - 实现自动保存功能
   - 添加 JSON 文件加载逻辑
   - 创建集成测试

### 第三阶段：调试与修复

1. **图标问题**：
   - 发现 `LANGUAGE` 图标在 Blender 5.0 中不存在
   - 解决方案：替换为 `WORLD` 图标

2. **空白项目问题**：
   - 发现收藏夹列表中出现空白项目
   - 原因：JSON 文件中存在空语言条目
   - 解决方案：清理 JSON 文件，添加验证和清理方法

3. **语言选择弹出菜单问题**：
   - 点击语言选项时报错 "Language code and name cannot be empty"
   - 原因：操作符属性传递方式不正确
   - 解决方案：使用 `props` 方法设置操作符属性

## 技术决策

### 1. 存储方案
- **Blender 偏好设置**：存储基本配置（如自动保存选项）
- **外部 JSON 文件**：存储收藏语言列表
- **理由**：JSON 文件更灵活，易于编辑和备份；Blender 偏好设置与 Blender 集成度高

### 2. 语言切换机制
- **方法**：直接修改 `bpy.context.preferences.view.language`
- **参考**：官方 Blender API 和现有插件实现
- **自动保存**：可选功能，切换后自动保存偏好

### 3. 菜单集成
- **位置**：顶部菜单栏右侧
- **实现**：使用 `bpy.types.TOPBAR_HT_upper_bar.append()` 添加自定义绘制函数
- **理由**：符合 Blender 插件开发规范，用户体验良好

### 4. 语言列表获取
- **主要方法**：使用 `bpy.types.PreferencesView.bl_rna.properties["language"].enum_items`
- **备选方法**：使用 `bpy.app.translations.available_translations`
- **最终回退**：硬编码常用语言列表
- **理由**：确保获取所有 Blender 支持的语言，同时保持向后兼容

## 遇到的问题与解决方案

### 问题 1：Blender 5.0 中 `LANGUAGE` 图标不存在
- **现象**：设置面板显示错误，无法加载
- **原因**：Blender 5.0 移除了 `LANGUAGE` 图标
- **解决方案**：将所有 `LANGUAGE` 图标替换为 `WORLD` 图标

### 问题 2：收藏夹列表显示空白项目
- **现象**：列表中有可以触发的项，但没有显示文字
- **原因**：JSON 文件中存在空语言条目 `{"code": "", "name": ""}`
- **解决方案**：
  1. 清理 JSON 文件中的空条目
  2. 添加 `_cleanup_empty_favorites()` 方法，每次绘制时清理空项
  3. 在 `LanguageManager.add_favorite()` 中添加验证，防止添加空条目

### 问题 3：语言选择弹出菜单报错
- **现象**：点击语言选项时报错 "Language code and name cannot be empty"
- **原因**：通过 `layout.operator()` 的关键字参数传递操作符属性在某些 Blender 版本中不被支持
- **解决方案**：使用 `props` 方法设置操作符属性：
  ```python
  props = col.operator("language_switcher.add_language", text=f"{name} ({code})")
  props.language_code = code
  props.language_name = name
  ```

### 问题 4：测试环境限制
- **现象**：无法在 Blender 外部运行测试
- **原因**：测试依赖 `bpy` 模块，该模块只在 Blender 内部可用
- **解决方案**：接受测试需要在 Blender 内部运行的限制，依赖代码审查和手动测试

## 未来改进方向

1. **双语支持**：
   - 实现类似 Secondary Language 插件的双语显示功能
   - 支持自定义语言文件注册
   - 实现双语菜单显示

2. **性能优化**：
   - 缓存收藏语言列表，避免每次 UI 绘制都读取 JSON 文件
   - 优化语言切换操作，减少不必要的重绘

3. **用户体验改进**：
   - 添加语言搜索功能
   - 支持拖拽排序
   - 添加语言图标显示

4. **国际化**：
   - 支持插件界面的多语言显示
   - 添加更多语言到默认列表

## 项目文件结构

```
Quickly_switch_languages/
├── __init__.py              # 插件入口，注册和注销
├── blender_manifest.toml    # Blender 5.0+ 插件清单
├── languages.json          # 收藏语言列表存储
├── language_manager.py     # 语言管理器，处理 JSON 操作
├── menu.py                 # 菜单系统，顶部菜单栏集成
├── preferences.py          # 设置面板，插件配置
├── README.md               # 使用说明
├── DEVELOPMENT.md          # 开发经历与项目信息（本文件）
├── test_language_manager.py # 语言管理器测试
├── test_preferences.py     # 设置面板测试
└── test_integration.py     # 集成测试
```

## 开发工具与环境

- **开发环境**：Windows 10/11
- **Blender 版本**：5.0+
- **Python 版本**：3.10+
- **版本控制**：Git
- **代码编辑器**：VS Code + Python 扩展

## 致谢

- **Blender 社区**：提供丰富的 API 文档和插件示例
- **toggle_language 插件**：提供语言切换的参考实现
- **secondary_language 插件**：提供语言选择界面的参考实现
- **用户反馈**：帮助发现和修复问题