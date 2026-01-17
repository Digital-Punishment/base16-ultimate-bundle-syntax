from pathlib import Path, PurePath
from spectrum.main import generate_pixels, parse_hex
from PIL import Image
# from typing import NoReturn

# import pprint
import yaml
import json
import re

source_path = "../schemes/base16"
schemes_path = "../styles/schemes"
settings_path = "../lib/base16c_settings.json"
package_path = "../package.json"

def lower_filename(name: str) -> str:
    """Convert scheme name to file name."""
    return name\
        .replace("(", "").replace(")", "")\
        .replace(",", "")\
        .replace("é", "e")\
        .replace(" ", "-").lower()

def lower_keyword(name: str) -> str:
    name = re.sub(r"\(\w+\s*\w+\)", "", name)
    return name\
        .lower()\
        .replace(",", "")\
        .replace("é", "e")\
        .replace(" lighter", "")\
        .replace(" light", "")\
        .replace(" darker", "")\
        .replace(" dark", "")\
        .replace(" hard", "")\
        .replace(" medium", "")\
        .replace(" soft", "")\
        .replace(" terminal", "")\
        .replace(" high contrast", "")\
        .replace(" contrast", "")\
        .replace(" plus", "")\
        .replace(" dimmed", "")\
        .replace("  ", " ")\
        .lstrip(" ").rstrip(" ")

def convert_scheme(scheme_path: Path) -> str:
    """Convert yaml scheme to .less scheme."""
    with scheme_path.open(mode = "r") as source_file:
        yaml_content = yaml.safe_load(source_file)

    less_filename = lower_filename(yaml_content["name"])
    less_filepath = Path(schemes_path / PurePath(less_filename).with_suffix(".less"))
    spectrum_filepath = Path(schemes_path / PurePath(less_filename).with_suffix(".png"))

    spectrum_colors = []
    less_content = f"//Name: {yaml_content["name"]}\n//Author: {yaml_content["author"]}\n"
    for color in sorted(yaml_content["palette"]):
        color_code = yaml_content["palette"][color].upper()\
            if "#" in yaml_content["palette"][color]\
            else "#" + yaml_content["palette"][color].upper()
        less_content += f"@{yaml_content["system"]}-color-{color}: {color_code};\n"

        color_rgb = parse_hex(yaml_content["palette"][color].strip("#"))
        if color_rgb is not None:
            spectrum_colors.append(color_rgb)

    need_update = False
    if not less_filepath.exists() or not spectrum_filepath.exists():
        need_update = True
    else:
        with less_filepath.open(mode = "r") as less_file:
            less_file_content = less_file.read()
        if less_content != less_file_content:
            need_update = True

    if need_update:
        with less_filepath.open(mode = "w") as less_file:
            less_file.write(less_content)
        spectrum_pixels = generate_pixels(spectrum_colors, 720, 20)
        Image.fromarray(spectrum_pixels, mode="RGB").save(spectrum_filepath)
        print(f"Update file: {less_filename}.less")
    else:
        print(f"File is up to date: {less_filename}.less")

    return yaml_content["name"].replace("-", " ").title()

def generate_readme(name_list: list) -> str:
    readme_content = "#Base16 Syntax Theme"

    schemes_list = ""
    for name in name_list:
        author = ""
        scheme_path = Path(schemes_path / PurePath(lower_filename(name)).with_suffix(".less"))
        preview_path = Path(schemes_path / PurePath(lower_filename(name)).with_suffix(".png"))
        with scheme_path.open(mode = "r") as scheme_file:
            for line in scheme_file:
                if "Author:" in line:
                    author = line.lstrip("/").lstrip(" ").rstrip("\n").removeprefix("Author: ")
        schemes_list += f"\n- {name} (Author: {"Unknown" if author == "" else author})\n"
        if preview_path.exists():
            schemes_list += f"![name](https://github.com/Digital-Punishment/base16-compilation-syntax/blob/master/styles/schemes/{lower_filename(name)}.png?raw=true)\n"

    return readme_content

if __name__ == "__main__":
    schemes = sorted(Path(source_path).glob("*.y*ml"))

    name_list = [convert_scheme(scheme) for scheme in schemes]
    print(f"{len(name_list)} schemes in package")

    with Path(settings_path).open(mode = "r") as settings_file:
        settings_content = json.loads(settings_file.read())
    settings_content["config"]["scheme"]["enum"] = sorted(name_list)
    with Path(settings_path).open(mode = "w") as settings_file:
        json.dump(settings_content, settings_file, indent = 2)

    keywords = set([lower_keyword(name) for name in name_list])
    keywords.add("base16")
    with Path(package_path).open(mode = "r") as package_file:
        package_content = json.loads(package_file.read())
    package_content["keywords"] = sorted(keywords)
    with Path(package_path).open(mode = "w") as package_file:
        json.dump(package_content, package_file, indent = 2)
