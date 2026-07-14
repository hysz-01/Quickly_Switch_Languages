DEFAULT_SCOPE_PRESET = "node_shader_geometry"


SCOPE_PRESETS = {
    "node_shader_geometry": {
        "label": "Node / Shader / Geometry Nodes",
        "keywords": [
            "Node", "Nodes", "Shader", "Socket", "Input", "Output",
            "Geometry", "Geometry Nodes", "Group", "Attribute", "Field",
            "Vector", "Color", "Value", "Normal", "UV", "Image",
            "Material", "Texture", "Principled", "BSDF",
        ],
    },
    "material_texture": {
        "label": "Material / Texture",
        "keywords": ["Material", "Texture", "Image", "Color", "Alpha", "Normal", "Roughness", "Metallic"],
    },
    "animation_rigging": {
        "label": "Animation / Rigging",
        "keywords": ["Animation", "Action", "Keyframe", "Rig", "Bone", "Armature", "Pose", "Constraint"],
    },
    "viewport_navigation": {
        "label": "Viewport / Navigation",
        "keywords": ["Viewport", "View", "Navigation", "Camera", "Orbit", "Pan", "Zoom", "Gizmo"],
    },
    "modeling_mesh": {
        "label": "Modeling / Mesh",
        "keywords": [
            "Mesh", "Vertex", "Vertices", "Edge", "Edges", "Face", "Faces",
            "Normal", "Normals", "Extrude", "Inset", "Bevel", "Loop Cut",
            "Subdivide", "Merge", "Separate", "Dissolve", "Knife", "Fill",
            "Triangulate", "Smooth", "Shade Smooth", "Edit Mode", "Object Mode",
        ],
    },
    "sculpt_paint": {
        "label": "Sculpt / Paint",
        "keywords": [
            "Sculpt", "Brush", "Stroke", "Radius", "Strength", "Smooth",
            "Mask", "Paint", "Texture Paint", "Vertex Paint", "Weight Paint",
            "Clone", "Smear", "Draw", "Inflate", "Grab", "Crease",
        ],
    },
    "compositor_vfx": {
        "label": "Compositor / VFX",
        "keywords": [
            "Compositor", "Composite", "Viewer", "Render Layers", "Image",
            "Alpha Over", "Color Balance", "Color Correction", "Hue/Saturation",
            "Glare", "Blur", "Defocus", "Mask", "Keying", "Cryptomatte",
        ],
    },
    "render_lighting": {
        "label": "Render / Lighting",
        "keywords": [
            "Render", "Rendering", "Light", "Lighting", "World", "Camera",
            "Cycles", "Eevee", "Sample", "Samples", "Shadow", "Ambient Occlusion",
            "Raytracing", "Denoise", "Exposure", "Color Management",
        ],
    },
}


def get_scope_keywords(enabled_presets=None, custom_keywords="", bpy_module=None, blender_version=None):
    presets = enabled_presets or [DEFAULT_SCOPE_PRESET]
    keywords = set()
    for preset in presets:
        keywords.update(SCOPE_PRESETS.get(preset, {}).get("keywords", []))
        if preset == DEFAULT_SCOPE_PRESET and bpy_module is not None:
            keywords.update(collect_blender_node_keywords(bpy_module))
    for item in custom_keywords.split(","):
        keyword = item.strip()
        if keyword:
            keywords.add(keyword)
    return keywords


def collect_blender_node_keywords(bpy_module):
    keywords = set()
    prefixes = ("ShaderNode", "GeometryNode", "CompositorNode", "FunctionNode")
    for type_name in dir(bpy_module.types):
        if not type_name.startswith(prefixes):
            continue
        node_type = getattr(bpy_module.types, type_name)
        name = getattr(getattr(node_type, "bl_rna", None), "name", "")
        if name:
            keywords.add(name)
    return keywords
