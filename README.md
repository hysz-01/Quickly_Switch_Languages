# Quick Language Switcher

Quick Language Switcher is a Blender add-on for quickly switching UI languages from the top bar. It also provides an advanced bilingual language-pack installer that can generate custom Blender locale entries such as `zh_en`, `en_zh`, or `en_ja`.

## Features

- **Top-bar language switcher**: Adds a `Switch Language` menu to Blender's top bar.
- **Favorite languages**: Add, remove, and reorder language shortcuts.
- **Mouse popup shortcut**: Press `Shift+Ctrl+L` to open the switcher at the mouse cursor.
- **Plugin UI translations**: Built-in add-on UI strings support English, Simplified Chinese, Traditional Chinese, and Japanese.
- **Bilingual language packs**: Generate and install custom bilingual Blender UI locales.
- **Scoped bilingual bake**: Optionally limit bilingual output to common areas such as Node / Shader / Geometry Nodes.
- **Emergency cleanup**: Remove bilingual locale entries and files recorded by this add-on's manifest or marker block.

## Installation

1. Copy the `Quickly_switch_languages` folder to your Blender add-ons directory.
   - Windows: `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\`
   - macOS: `~/Library/Application Support/Blender/<version>/scripts/addons/`
   - Linux: `~/.config/blender/<version>/scripts/addons/`
2. Open Blender and go to `Edit > Preferences > Add-ons`.
3. Search for `Quick Language Switcher` and enable it.

## Basic Usage

1. Click `Switch Language` in the top bar.
2. Choose a favorite language.
3. Blender switches the interface language immediately by setting `bpy.context.preferences.view.language`.

Favorite language data is stored in Blender's user configuration directory:

```text
config/quick_language_switcher/languages.json
```

The packaged `data/languages.json` file is only the default template. Runtime favorites are not written back into the add-on package.

## Default Favorites

The default favorite list is intentionally small:

- English (`en_US`)
- Simplified Chinese (`zh_HANS`)
- Japanese (`ja_JP`)

Defaults are migrated once. After migration, user deletions are respected and default languages are not forced back into the list every time Blender starts.

## Bilingual Language Packs

The advanced bilingual feature modifies Blender locale resource files under `datafiles/locale`. Use it only if you accept that it writes files into the Blender installation directory.

The installer can:

- Read real Blender locale `.mo` files from `datafiles/locale/*/LC_MESSAGES/blender.mo`.
- Bake a generated bilingual `.mo` file using safe formatting rules.
- Add a generated language entry to Blender's `datafiles/locale/languages` file.
- Store install state in Blender user config as `config/quick_language_switcher/bilingual_manifest.json`.
- Keep multiple generated bilingual locales installed at the same time.

The installer does **not** automatically switch Blender to the generated language. After installing, restart Blender and manually choose the generated locale in `Preferences > Interface > Language`.

The add-on attempts to remove generated bilingual packs automatically when disabled or unregistered. This is intentional: the add-on tries to restore Blender's locale directory to a clean state when it is not active. Re-enable the add-on and install the bilingual pack again if you need it later.

## Safety Boundaries

- Original Blender locale files such as `zh_HANS/LC_MESSAGES/blender.mo` are not overwritten.
- Generated locale files are installed into separate locale directories such as `zh_en/LC_MESSAGES/blender.mo`.
- Installed generated locales can coexist. Installing `en_ja` should not remove a previously installed `zh_en`.
- The installer records the current UI language before installation and restores it afterward.
- Disabling or unregistering the add-on attempts a best-effort cleanup of generated bilingual locale files.
- Manifest paths are validated before deletion during uninstall or cleanup.
- Emergency cleanup without a manifest only removes locale directories declared in this add-on's marker block inside Blender's `languages` file. If both the manifest and marker block are missing, manually inspect `datafiles/locale` for orphan generated directories.

## Troubleshooting

### The top-bar menu does not appear

- Make sure the add-on is enabled in `Edit > Preferences > Add-ons`.
- Restart Blender after enabling the add-on.

### A generated bilingual language is not available

- Restart Blender after installing a bilingual language pack.
- Confirm the generated language is listed in `Preferences > Interface > Language`.
- If it is still missing, run `Emergency Cleanup`, restart Blender, and install the pack again.

### Blender reports that a source `.mo` file is missing

The requested source language may not be installed in this Blender build, or the locale folder may use a different real directory name. The add-on scans Blender's actual locale directories, but it still requires the source `blender.mo` file to exist.

### A generated language remains in favorites but cannot be selected

Install that bilingual pack again or remove the stale favorite entry. A favorite entry only stores a shortcut; it does not guarantee the generated locale is installed in Blender.

## Developer Checks

Run the unit tests from the add-on directory:

```powershell
pytest -q
```

Compile the key modules:

```powershell
python -m py_compile "__init__.py" "core\language_manager.py" "core\paths.py" "core\localization.py" "core\keymap.py" "ui\menu.py" "ui\preferences.py" "bilingual\installer.py" "bilingual\baker.py" "bilingual\mo.py" "bilingual\scope.py"
```

For Blender registration smoke tests, use `--factory-startup --background` to avoid conflicts with a user profile that already has the add-on enabled.

## License

GPL-3.0-or-later. See `LICENSE`.
