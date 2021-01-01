import hashlib
from dataclasses import dataclass
from typing import List, Any

from gitopscli.gitops_exception import GitOpsException
from gitopscli.preview_api.replacement import Replacement


@dataclass(frozen=True)
class GitOpsConfig:
    application_name: str
    team_config_org: str
    team_config_repo: str
    route_host_template: str
    replacements: List[Replacement]

    def __post_init__(self) -> None:
        assert isinstance(self.application_name, str), "application_name of wrong type!"
        assert isinstance(self.team_config_org, str), "team_config_org of wrong type!"
        assert isinstance(self.team_config_repo, str), "team_config_repo of wrong type!"
        assert isinstance(self.route_host_template, str), "route_host_template of wrong type!"
        assert isinstance(self.replacements, list), "replacements of wrong type!"
        for index, replacement in enumerate(Replacement.Variable):
            assert isinstance(replacement, Replacement.Variable), f"replacement[{index}] of wrong type!"

    def get_route_host(self, preview_id: str) -> str:
        hashed_preview_id = self.__create_hashed_preview_id(preview_id)
        return self.route_host_template.replace("{SHA256_8CHAR_BRANCH_HASH}", hashed_preview_id)

    def get_preview_namespace(self, preview_id: str) -> str:
        hashed_preview_id = self.__create_hashed_preview_id(preview_id)
        return f"{self.application_name}-{hashed_preview_id}-preview"

    @staticmethod
    def __create_hashed_preview_id(preview_id: str) -> str:
        return hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]

    @staticmethod
    def from_yaml_file(yaml_file: Any) -> "GitOpsConfig":
        replacements: List[Replacement] = []
        replacement_dicts = yaml_file.get_list_value("previewConfig.replace")
        for index, replacement_dict in enumerate(replacement_dicts):
            if not isinstance(replacement_dict, dict):
                raise GitOpsException(f"Item 'previewConfig.replace.[{index}]' should be a object in GitOps config!")
            if "path" not in replacement_dict:
                raise GitOpsException(f"Key 'previewConfig.replace.[{index}].path' not found in GitOps config!")
            if "variable" not in replacement_dict:
                raise GitOpsException(f"Key 'previewConfig.replace.[{index}].variable' not found in GitOps config!")
            path = replacement_dict["path"]
            variable_str = replacement_dict["variable"]
            if not isinstance(path, str):
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].path' should be a string in GitOps config!"
                )
            if not isinstance(variable_str, str):
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].variable' should be a string in GitOps config!"
                )
            try:
                variable = Replacement.Variable[variable_str]
            except KeyError as ex:
                possible_values = ", ".join(sorted([v.name for v in Replacement.Variable]))
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].variable' should be one of the following values in "
                    f"GitOps config: {possible_values}"
                ) from ex
            replacements.append(Replacement(path=path, variable=variable))

        return GitOpsConfig(
            application_name=yaml_file.get_string_value("deploymentConfig.applicationName"),
            team_config_org=yaml_file.get_string_value("deploymentConfig.org"),
            team_config_repo=yaml_file.get_string_value("deploymentConfig.repository"),
            route_host_template=yaml_file.get_string_value("previewConfig.route.host.template"),
            replacements=replacements,
        )
