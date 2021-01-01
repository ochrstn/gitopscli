from typing import Any, List

from ruamel.yaml import YAML, YAMLError

from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.yaml_util import YAMLException


class YamlFile:

    file_path: str
    yaml: YAML

    def __init__(self, file_path: str, yaml: Any) -> None:
        self.file_path = file_path
        self.yaml = yaml

    @staticmethod
    def read(file_path: str) -> "YamlFile":
        with open(file_path, "r") as stream:
            try:
                yaml = YAML().load(stream)
                return YamlFile(file_path, yaml)
            except YAMLError as ex:
                raise YAMLException(f"Error parsing YAML file: {file_path}") from ex

    def get_value(self, key: str) -> Any:
        keys = key.split(".")
        data = self.yaml
        for k in keys:
            if not isinstance(data, dict) or k not in data:
                raise GitOpsException(f"Key '{key}' not found in GitOps config!")
            data = data[k]
        return data

    def get_string_value(self, key: str) -> str:
        value = self.get_value(key)
        if not isinstance(value, str):
            raise GitOpsException(f"Item '{key}' should be a string in GitOps config!")
        return value

    def get_list_value(self, key: str) -> List[Any]:
        value = self.get_value(key)
        if not isinstance(value, list):
            raise GitOpsException(f"Item '{key}' should be a list in GitOps config!")
        return value
