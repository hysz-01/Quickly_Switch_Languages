# Quick Language Switcher

[中文说明](#中文说明) | [English](#english)

## 中文说明

Quick Language Switcher 是适用于 **Blender 5.0+** 的扩展。它在顶栏提供常用界面语言的快速切换，并提供可选的双语界面语言包生成与安装功能。

### 功能

- 在 Blender 顶栏添加 `Switch Language` 菜单，从收藏语言中快速切换界面语言。
- 使用 `Shift + Ctrl + L` 在鼠标位置打开快速切换弹窗。
- 在扩展首选项中添加、删除和排序收藏语言；默认收藏项为 English、简体中文和日本語。
- 插件自身界面支持 English、简体中文、繁體中文和日本語。
- 可选的双语语言包：将固定的 English 与一项非英语语言组合为独立 locale，例如 `zh_en` 或 `en_zh`。
- 可选的实验性范围过滤，可只处理节点、材质、动画、视图、建模、雕刻、合成或渲染等相关术语，也可指定自定义关键词。

### 安装

优先使用 Release ZIP 安装扩展：

1. 从项目的 Release 下载 ZIP 文件，不要先解压。
2. 在 Blender 中打开 `Edit > Preferences > Get Extensions`。
3. 点击右上角下拉菜单，选择 `Install from Disk`。
4. 选择下载的 Release ZIP 并完成安装，然后启用 Quick Language Switcher。

如果无法使用扩展安装器，可采用手动文件夹安装：

1. 解压 Release ZIP，或将 `Quickly_switch_languages` 插件文件夹复制到 Blender 的 add-ons 目录。
2. 常见位置如下：
   - Windows：`%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\`
   - macOS：`~/Library/Application Support/Blender/<version>/scripts/addons/`
   - Linux：`~/.config/blender/<version>/scripts/addons/`
3. 在 Blender 中打开 `Edit > Preferences > Add-ons`，搜索 `Quick Language Switcher` 并启用。

### 基本使用

1. 在顶栏点击 `Switch Language`。
2. 选择一个收藏语言，Blender 会将界面语言切换为对应 locale。
3. 也可以按 `Shift + Ctrl + L`，在鼠标位置的弹窗中选择收藏语言。
4. 使用菜单中的 `Manage Languages...` 打开扩展首选项，管理收藏语言及其顺序。

收藏项会保存在 Blender 用户配置目录的 `config/quick_language_switcher/languages.json`。打包在扩展内的 `data/languages.json` 仅作为默认模板，运行时不会回写到扩展目录。生成的双语 locale 也可以加入收藏，但收藏项只是快捷入口；它不保证该 locale 仍安装在 Blender 中。

### 可选：双语语言包

双语功能会读取 Blender 真实存在的 `.mo` 翻译文件，并在 Blender 安装目录的 `datafiles/locale` 下创建独立 locale 目录和 `LC_MESSAGES/blender.mo` 文件；同时会在该目录的 `languages` 文件中添加本扩展标记的语言条目。请不要把其他工具的文件放入本扩展生成的 locale 目录：如果目标 `blender.mo` 已存在，当前版本可能覆盖它。

使用前请确认 Blender 安装目录中的 `datafiles/locale` 可写。没有写入权限时，安装会失败；在受保护的位置安装的 Blender 可能需要使用有相应权限的账户或调整安装位置。双语包固定使用 English，另一项所选的非英语语言必须在当前 Blender 安装中拥有对应的 `blender.mo` 文件。

安装步骤：

1. 打开 Blender 首选项中的 Quick Language Switcher 配置项。
2. 展开 Advanced Bilingual Packs，选择 English 和一项非英语语言；如有需要，启用实验性范围过滤并选择范围或关键词。
3. 选择安装双语包。
4. **重启 Blender**，然后在 `Preferences > Interface > Language` 中手动选择新生成的 locale。

安装过程会暂存并恢复安装前的当前界面语言，但不会自动切换到新生成的 locale。可以同时安装多个由本扩展生成的双语 locale。

### 清理与安全边界

- 卸载双语包，以及禁用或注销扩展时，会尽力清理本扩展生成的双语文件和写入的语言条目。文件权限或外部修改可能使清理无法完全完成。
- `Emergency Cleanup` 优先移除本扩展清单中记录的文件；清单缺失、无法读取，或其 `installed_files` 列表为空时，才会使用 Blender `languages` 文件内的 marker block 确定待清理 locale。若清单包含不安全的路径记录，清理会拒绝执行，而不会回退到 marker。它不会猜测其他未记录的目录；但 marker block 被篡改、复制或复用时，清理可能删除其中声明的 locale 的 `blender.mo` 文件。
- 若清单和 marker block 都缺失，工具不会猜测或删除可能属于其他来源的目录；请手动检查 `datafiles/locale` 中遗留的生成目录。
- 清理或卸载后请重启 Blender，以刷新语言列表。

### 排障

#### 顶栏没有 `Switch Language`

- 确认扩展已在 Blender 首选项中启用。
- 启用后重启 Blender。

#### 找不到或无法选择生成的双语语言

- 安装双语包后必须重启 Blender。
- 在 `Preferences > Interface > Language` 中手动选择生成的 locale。
- 确认 `datafiles/locale` 具有写入权限，并确认源语言的 `blender.mo` 文件存在。
- 如需恢复本扩展已记录的双语安装，可运行 `Emergency Cleanup`，重启 Blender 后重新安装。它不会猜测未记录的第三方目录；但 marker block 被篡改、复制或复用时，仍可能删除其中声明 locale 的 `blender.mo` 文件。

#### 菜单中的语言无法切换

- 该语言可能不在当前 Blender 安装的可用 locale 列表中。
- 对于双语 locale，请重新安装对应双语包，或从收藏项中移除失效入口。

### 开发验证

在扩展根目录运行：

```powershell
pytest -q
```

编译关键模块：

```powershell
python -m py_compile "__init__.py" "core\language_manager.py" "core\paths.py" "core\localization.py" "core\keymap.py" "ui\menu.py" "ui\preferences.py" "bilingual\installer.py" "bilingual\baker.py" "bilingual\mo.py" "bilingual\scope.py"
```

进行 Blender 注册烟雾测试时，使用 `--factory-startup --background`，避免用户配置中已启用的同一扩展造成冲突。

### 许可证

本项目采用 [GPL-3.0-or-later](LICENSE) 许可证。

## English

Quick Language Switcher is a **Blender 5.0+** extension. It provides fast access to favorite UI languages from Blender's top bar and an optional workflow for generating and installing bilingual UI language packs.

### Features

- Adds a `Switch Language` menu to Blender's top bar for switching among favorite UI languages.
- Press `Shift + Ctrl + L` to open the language switcher popup at the mouse cursor.
- Add, remove, and reorder favorite languages in the extension preferences. The defaults are English, Simplified Chinese, and Japanese.
- The add-on UI includes English, Simplified Chinese, Traditional Chinese, and Japanese translations.
- Optional bilingual language packs combine English with one non-English language to generate separate Blender locales such as `zh_en` or `en_zh`.
- Optional experimental scope filtering can limit bilingual output to terms related to nodes, materials, animation, viewport navigation, modeling, sculpting, compositing, or rendering; custom keywords are also supported.

### Installation

Install from the Release ZIP whenever possible:

1. Download the Release ZIP. Do not extract it first.
2. In Blender, open `Edit > Preferences > Get Extensions`.
3. Open the upper-right menu and select `Install from Disk`.
4. Select the Release ZIP, complete the installation, and enable Quick Language Switcher.

If the extension installer is unavailable, use manual folder installation instead:

1. Extract the Release ZIP, or copy the `Quickly_switch_languages` add-on folder into Blender's add-ons directory.
2. Common locations are:
   - Windows: `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\`
   - macOS: `~/Library/Application Support/Blender/<version>/scripts/addons/`
   - Linux: `~/.config/blender/<version>/scripts/addons/`
3. In Blender, open `Edit > Preferences > Add-ons`, search for `Quick Language Switcher`, and enable it.

### Basic Use

1. Click `Switch Language` in the top bar.
2. Choose a favorite language to switch Blender's UI locale.
3. Alternatively, press `Shift + Ctrl + L` and select a favorite from the popup at the mouse cursor.
4. Use `Manage Languages...` from the menu to open extension preferences and manage favorite languages and their order.

Favorites are stored in Blender's user configuration directory at `config/quick_language_switcher/languages.json`. The packaged `data/languages.json` is only a default template; runtime changes are not written back into the extension package. A generated bilingual locale may be a favorite, but a favorite is only a shortcut and does not guarantee that the locale remains installed in Blender.

### Optional Bilingual Language Packs

The bilingual feature reads real Blender `.mo` translation files and creates separate locale directories and `LC_MESSAGES/blender.mo` files under the Blender installation's `datafiles/locale` directory. It also adds an extension-marked language entry to that directory's `languages` file. Do not place files from other tools in a locale directory generated by this extension: the current version can overwrite an existing target `blender.mo` file.

Before installing, make sure `datafiles/locale` in the Blender installation is writable. Installation fails without write permission; Blender installations in protected locations may require an appropriately privileged account or a different installation location. Bilingual packs always use English; the selected non-English language must have its corresponding `blender.mo` file in the current Blender installation.

To install a bilingual pack:

1. Open the Quick Language Switcher entry in Blender preferences.
2. Expand Advanced Bilingual Packs, select English and one non-English language, and optionally enable the experimental scope filters and choose scopes or keywords.
3. Install the bilingual pack.
4. **Restart Blender**, then manually select the generated locale in `Preferences > Interface > Language`.

The installer saves and restores the currently selected UI language during installation, but it does not automatically switch Blender to the generated locale. Multiple bilingual locales generated by this extension can coexist.

### Cleanup And Safety Boundaries

- Uninstalling bilingual packs, disabling the extension, or unregistering it attempts best-effort cleanup of bilingual files and language entries created by this extension. Cleanup can remain incomplete when permissions or external changes prevent removal.
- `Emergency Cleanup` first removes files recorded by this extension's manifest. Only when the manifest is missing, unreadable, or has an empty `installed_files` list does it use locale codes declared in this extension's marker block in Blender's `languages` file to determine cleanup targets. If the manifest contains unsafe path records, cleanup refuses to proceed instead of falling back to the marker. It does not guess other unrecorded directories; however, if the marker block is tampered with, copied, or reused, cleanup can remove the `blender.mo` file for a locale declared in that block.
- If both the manifest and marker block are missing, the tool does not guess which directories are safe to remove. Inspect leftover generated directories in `datafiles/locale` manually.
- Restart Blender after cleanup or uninstalling to refresh the language list.

### Troubleshooting

#### The `Switch Language` top-bar menu is missing

- Confirm that the extension is enabled in Blender preferences.
- Restart Blender after enabling it.

#### A generated bilingual language is missing or cannot be selected

- Restart Blender after installing the bilingual pack.
- Manually select the generated locale in `Preferences > Interface > Language`.
- Confirm write access to `datafiles/locale` and that the source language's `blender.mo` file exists.
- To restore an installation tracked by this extension, run `Emergency Cleanup`, restart Blender, and install again. It does not guess unrecorded third-party directories; however, a tampered, copied, or reused marker block can still cause cleanup to remove the declared locale's `blender.mo` file.

#### A language in the menu cannot be switched

- The language may not be available in the current Blender installation.
- For a bilingual locale, reinstall its bilingual pack or remove its stale favorite entry.

### Development Checks

Run from the extension root:

```powershell
pytest -q
```

Compile the key modules:

```powershell
python -m py_compile "__init__.py" "core\language_manager.py" "core\paths.py" "core\localization.py" "core\keymap.py" "ui\menu.py" "ui\preferences.py" "bilingual\installer.py" "bilingual\baker.py" "bilingual\mo.py" "bilingual\scope.py"
```

For Blender registration smoke tests, use `--factory-startup --background` to avoid a conflict with a user profile that already has the extension enabled.

### License

Licensed under [GPL-3.0-or-later](LICENSE).
