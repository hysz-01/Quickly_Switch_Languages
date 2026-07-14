def addon_package_name(package: str) -> str:
    parts = package.split(".")
    if len(parts) >= 3 and parts[0] == "bl_ext":
        return ".".join(parts[:3])
    return parts[0]
