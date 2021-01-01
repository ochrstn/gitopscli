from dataclasses import dataclass
from typing import List, Any

from gitopscli.gitops_exception import GitOpsException
from gitopscli.preview_api.preview_config import PreviewConfig
from gitopscli.preview_api.replacement import Replacement


@dataclass(frozen=True)
class GitOpsConfig:
    api_version: str
    preview_config: PreviewConfig

    def __post_init__(self) -> None:
        assert isinstance(self.api_version, str), "api_version of wrong type!"
        assert isinstance(self.preview_config, PreviewConfig), "preview_config of wrong type!"

    @staticmethod
    def from_yaml_file_v0(yaml_file: Any) -> "GitOpsConfig":
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
            application_name = yaml_file.get_string_value("deploymentConfig.applicationName")
            file_content_replacements = {"values.yaml": replacements}
            preview_config = PreviewConfig(
                host=yaml_file.get_string_value("previewConfig.route.host.template"),
                application_name=application_name,
                template_git_org=yaml_file.get_string_value("deploymentConfig.org"),
                template_git_repo=yaml_file.get_string_value("deploymentConfig.repository"),
                template_path=None,
                template_branch=None,
                target_git_org=yaml_file.get_string_value("deploymentConfig.org"),
                target_git_repo=yaml_file.get_string_value("deploymentConfig.repository"),
                target_path=None,
                target_branch=None,
                file_content_replacements=file_content_replacements,
            )

        return GitOpsConfig(api_version="v0", preview_config=preview_config)
