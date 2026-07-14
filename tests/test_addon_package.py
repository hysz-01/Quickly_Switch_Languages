from Quickly_switch_languages.core.addon import addon_package_name


def test_addon_package_name_for_classic_addon_subpackage():
    assert addon_package_name("Quickly_switch_languages.ui") == "Quickly_switch_languages"


def test_addon_package_name_for_blender_extension_subpackage():
    assert addon_package_name("bl_ext.user_default.quickly_switch_languages.ui") == "bl_ext.user_default.quickly_switch_languages"
