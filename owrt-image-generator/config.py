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
    merged_config.update({"files": device.get("files")})
    merged_config.update({"settings": device.get("settings")})
    return name, merged_config