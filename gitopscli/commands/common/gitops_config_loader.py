from gitopscli.git_api import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.yaml_file import YamlFile


def load_gitops_config(git_api_config: GitApiConfig, organisation: str, repository_name: str) -> GitOpsConfig:
    git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name)
    with GitRepo(git_repo_api) as git_repo:
        git_repo.clone()
        gitops_config_file_path = git_repo.get_full_file_path(".gitops.config.yaml")
        try:
            gitops_config_yaml = YamlFile.read(gitops_config_file_path)
            return GitOpsConfig.from_yaml_file_v0(gitops_config_yaml)
        except FileNotFoundError as ex:
            raise GitOpsException("No such file: .gitops.config.yaml") from ex
