# Bilingual Language Pack Design

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/bilingual-language-pack.md)

## [S1] Problem

Quick Language Switcher should let users create bilingual Blender UI language packs, starting with Simplified Chinese plus English. Blender does not expose a safe Python API for dynamically injecting a full replacement translation catalog for built-in UI strings. Runtime probes showed that `bpy.app.translations.register()` can translate add-on-owned strings, but it does not override existing Blender core translations such as `File` under `zh_HANS`.

Therefore, full Blender UI bilingual translation requires installing generated gettext resources into Blender's runtime locale folder and updating Blender's language menu resource file.

## [S2] Scope

First implementation supports only Blender 5.x Simplified Chinese bilingual packs:

- Source language: `zh_HANS`.
- Generated language codes: `zh_en` and `en_zh`.
- Generated files are first baked into the add-on folder under `generated/<blender_version>/...`.
- Installation copies generated `.mo` files into Blender's `datafiles/locale` folder.
- Installation patches Blender's `datafiles/locale/languages` file.
- Installation, update, uninstall, and restore operations require a Blender restart to fully take effect.

Out of scope for the first implementation:

- Arbitrary language pairs.
- In-place replacement of `zh_HANS/LC_MESSAGES/blender.mo`.
- Monkey patching Blender translation functions.
- Editing `_bl_i18n_utils/settings.py`.
- Automatic privilege escalation for non-writable Blender installations.

## [S3] User Warning

Before installation, the UI must clearly warn users:

```text
This feature modifies Blender language resource files:
- datafiles/locale/languages
- datafiles/locale/<custom_lang>/LC_MESSAGES/blender.mo

These files belong to Blender's text resources. Changes require restarting Blender.
If the Blender installation is not writable, another tool modifies these files, or the Blender version changes, the language list may become inconsistent.
The add-on creates backups before modifying files and provides uninstall/restore actions.
```

The action should be named `Install Bilingual Language Pack`, not a passive label such as `Enable`, so users understand that resources are being installed.

## [S4] File Layout

Source resource expected from Blender:

```text
<BlenderRoot>/5.0/datafiles/locale/zh_HANS/LC_MESSAGES/blender.mo
<BlenderRoot>/5.0/datafiles/locale/languages
```

Generated cache inside the add-on:

```text
Quickly_switch_languages/generated/<blender_version>/zh_en/LC_MESSAGES/blender.mo
Quickly_switch_languages/generated/<blender_version>/en_zh/LC_MESSAGES/blender.mo
```

Installed resources inside Blender:

```text
<BlenderRoot>/5.0/datafiles/locale/zh_en/LC_MESSAGES/blender.mo
<BlenderRoot>/5.0/datafiles/locale/en_zh/LC_MESSAGES/blender.mo
```

## [S5] Bake Rules

The add-on needs a pure Python `.mo` reader/writer so users do not need GNU gettext tools on Windows.

The baker reads source `.mo` entries where the original string is the English msgid and the translated string is the Chinese msgstr. It writes two catalogs:

- `zh_en`: `Chinese / English`.
- `en_zh`: `English / Chinese`.

Rules:

- Preserve the header entry where `msgid == ""`.
- Do not bilingualize entries with empty `msgstr`.
- Do not bilingualize entries where `msgstr == msgid`.
- Preserve gettext context keys using the `msgctxt + "\x04" + msgid` form.
- Preserve UTF-8 encoding.
- Validate placeholder compatibility before combining strings. If placeholders differ, keep the source translation unchanged for that entry.
- Use ` / ` as the first-stage separator for short UI strings.

## [S6] Install Flow

Installation is staged and conservative:

1. Detect Blender version and locale root.
2. Verify `languages` and source `zh_HANS` `.mo` exist.
3. Verify the locale root and `languages` are writable.
4. Bake or reuse generated `.mo` files for the current Blender version.
5. Create a first-install backup of `languages` as `languages.quick_language_switcher.bak` if absent.
6. Copy generated `.mo` files into `zh_en` and `en_zh` locale folders.
7. Patch `languages` by adding a marked block:

```text
# BEGIN Quick Language Switcher bilingual languages
998:English + Chinese - English (简体中文):en_zh:100%
999:Chinese + English - 简体中文 (English):zh_en:100%
# END Quick Language Switcher bilingual languages
```

8. Write an install manifest.
9. Report that Blender must be restarted.

If a target language code already exists outside the add-on's marked block, installation must stop and report a conflict.

## [S7] Manifest

The manifest records exactly what the add-on installed, so uninstall does not guess.

```json
{
  "blender_version": "5.0.1",
  "locale_root": ".../datafiles/locale",
  "source_language": "zh_HANS",
  "source_mo_hash": "...",
  "languages_hash_before": "...",
  "installed_language_codes": ["zh_en", "en_zh"],
  "installed_files": [
    "zh_en/LC_MESSAGES/blender.mo",
    "en_zh/LC_MESSAGES/blender.mo"
  ],
  "added_language_lines": [
    "998:English + Chinese - English (简体中文):en_zh:100%",
    "999:Chinese + English - 简体中文 (English):zh_en:100%"
  ]
}
```

The manifest may live in the add-on folder for the first implementation. Later it can move to a Blender user resource path if packaging requires it.

## [S8] Uninstall Flow

Uninstall removes only add-on-owned resources:

1. Read the manifest.
2. Remove the marked block from `languages`.
3. Delete installed `.mo` files listed in the manifest.
4. Remove `zh_en` and `en_zh` directories only if they are empty.
5. Keep generated cache unless the user chooses full cleanup.
6. Report that Blender must be restarted.

Uninstall must not restore the full backup by default, because users or other tools may have modified `languages` after installation.

## [S9] Restore Flow

Restore is separate from uninstall:

- `Uninstall Bilingual Pack`: safe targeted removal.
- `Restore languages backup`: overwrite `languages` with `languages.quick_language_switcher.bak` after a stronger confirmation.

Restore is a recovery action for corrupted or manually edited state, not the normal uninstall path.

## [S10] Failure Handling

The installer should avoid partial state where possible:

- If bake fails, do not write Blender resources.
- If copying `.mo` succeeds but patching `languages` fails, delete copied `.mo` files.
- If manifest writing fails after installation, report an incomplete install and offer repair/uninstall.
- If `languages` contains an existing conflicting `zh_en` or `en_zh` entry, stop without modifying files.
- If files are not writable, do not attempt privilege escalation; report that Blender must run with sufficient permissions or use a writable portable installation.

## [S11] Testing Strategy

Pure Python tests:

- `.mo` reader parses known fixtures.
- `.mo` writer round-trips parsed entries.
- baker preserves headers, contexts, empty translations, identical translations, and placeholder safety.
- `languages` patcher adds/removes marked blocks without touching unrelated lines.
- manifest-driven uninstall deletes only listed files.

Blender/manual tests:

- Bake and install on Blender 5.0.1 portable.
- Restart Blender.
- Confirm `zh_en` and `en_zh` appear in `PreferencesView.language` enum.
- Switch to both generated languages.
- Uninstall, restart, and confirm generated languages disappear.
