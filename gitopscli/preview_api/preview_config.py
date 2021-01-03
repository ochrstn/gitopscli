import hashlib
from dataclasses import dataclass

from gitopscli.git_api.git_repo_path_ref import GitRepoPathRef
from gitopscli.preview_api.replacement import Replacement


@dataclass(frozen=True)
class PreviewConfig:
    host: str
    application_name: str
    template: GitRepoPathRef
    target: GitRepoPathRef
    file_content_replacements: dict

    def __post_init__(self) -> None:
        assert isinstance(self.host, str), "host of wrong type!"
        assert isinstance(self.application_name, str), "application_name of wrong type!"
        assert isinstance(self.template, GitRepoPathRef), "template of wrong type!"
        assert isinstance(self.target, GitRepoPathRef), "target of wrong type!"
        assert isinstance(self.file_content_replacements, dict), "file_content_replacements of wrong type!"
        for key, replacements in self.file_content_replacements.items():
            for replacement in replacements:
                assert isinstance(replacement.variable, Replacement.Variable), f"replacement {key} value of wrong type!"

    def get_rendered_host(self, preview_id: str) -> str:
        hashed_preview_id = self.__create_hashed_preview_id(preview_id)
        return self.host.replace("{SHA256_8CHAR_BRANCH_HASH}", hashed_preview_id)

    def get_preview_name(self, preview_id: str) -> str:
        hashed_preview_id = self.__create_hashed_preview_id(preview_id)
        return f"{self.application_name}-{hashed_preview_id}-preview"

    @staticmethod
    def __create_hashed_preview_id(preview_id: str) -> str:
        return hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]
