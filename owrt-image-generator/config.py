from ruamel.yaml import YAML
from typing import Dict, Tuple

def load_config(config_file: str) -> Dict:
    with open(config_file) as f:
        yaml=YAML(typ='safe')
        return yaml.load(f)

def merge_config(template: Dict, device: Dict) -> Tuple[str, Dict]:
    name = "{}_{}".format(template.get("name"), device.get("name"))
    merged_config = {"name": name}
    merged_config.update({"files": template.get("files")})
    merged_config.update({"settings": template.get("settings")})
    if device.get("files"):
        for f in device.get("files"):
            merged_config["files"].append(f)
    if device.get("settings"):
        for s in device.get("settings"):
            merged_config["settings"].append(s)
    return name, merged_config