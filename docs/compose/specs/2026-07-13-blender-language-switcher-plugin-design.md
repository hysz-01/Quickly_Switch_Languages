# Blender Language Switcher Plugin Design

## [S1] Problem
Blender users who frequently switch between interface languages need a quick way to access their favorite languages without navigating through the preferences menu each time. The default Blender workflow requires opening Edit > Preferences > Interface > Language, which is cumbersome for multilingual users.

## [S2] Solution Overview
Create a Blender addon that adds a "Switch Languages to" menu in the top menu bar (right side). This menu displays a curated list of user-favorite languages, allowing one-click switching. The addon will:
1. Add a dropdown menu in the top bar showing favorite languages
2. Store favorite languages in a JSON file for flexibility
3. Store basic settings in Blender's addon preferences
4. Optionally save language preference after switching
5. Provide a settings page for managing favorites and configuration

## [S3] Architecture
### Components
1. **Addon Core**: Registers the addon, handles initialization and cleanup
2. **Menu System**: Adds "Switch Languages to" dropdown to top menu bar
3. **Language Manager**: Manages favorite languages (add/remove/sort) via JSON file
4. **Settings Panel**: Blender addon preferences page for configuration
5. **Language Switcher**: Handles actual language switching via Blender API

### Data Flow
1. User clicks "Switch Languages to" menu → shows favorite languages
2. User selects a language → calls `bpy.context.preferences.view.language = language_code`
3. If "Save preference after switching" is enabled → calls `bpy.ops.wm.save_userpref()`
4. Settings changes → saved to Blender addon preferences
5. Favorite languages changes → saved to external JSON file

## [S4] Menu Implementation
- Use `bpy.types.TOPBAR_HT_upper_bar.append()` to add custom draw function
- Create a dropdown menu class inheriting from `bpy.types.Menu`
- Menu displays favorite languages from JSON file
- Each language item triggers a language switch operator

## [S5] Storage Strategy
### Blender Addon Preferences
- `save_preference_after_switch`: Boolean for auto-saving preference
- Basic addon configuration

### External JSON File
- Location: `languages.json` in addon directory
- Structure:
```json
{
  "favorites": [
    {"code": "en_US", "name": "English"},
    {"code": "zh_CN", "name": "简体中文"},
    {"code": "ja_JP", "name": "日本語"}
  ]
}
```

## [S6] Settings Panel
Located in Edit > Preferences > Add-ons > Quick Language Switcher:
1. **General Settings**
   - [ ] Save preference after switching language
2. **Favorite Languages Management**
   - List of current favorites with remove buttons
   - Add language dropdown (shows all available Blender languages)
   - Sort/order functionality (drag or up/down buttons)

## [S7] Language Switching Mechanism
- Primary method: `bpy.context.preferences.view.language = language_code`
- Reference: Official Blender API and existing addons (toggle_language, secondary_language)
- After switching, optionally save with `bpy.ops.wm.save_userpref()`

## [S8] Future Considerations
- **Bilingual Display**: Register custom language files for dual-language display
- **Language File Management**: UI for importing/exporting custom language files
- **Advanced Sorting**: Custom ordering of favorite languages

## [S9] Technical Challenges
1. **Blender Version Compatibility**: Ensure compatibility with Blender 5.0+
2. **Language Code Validation**: Verify language codes exist in Blender's language list
3. **File Path Handling**: Cross-platform JSON file path management
4. **Menu Integration**: Proper placement in top menu bar without conflicting with other addons

## [S10] Success Criteria
1. Addon loads without errors in Blender 5.0
2. "Switch Languages to" menu appears in top menu bar
3. Clicking a language in the menu switches Blender interface language
4. Favorite languages persist across Blender sessions
5. Settings page accessible and functional
6. No performance impact on Blender startup or operation