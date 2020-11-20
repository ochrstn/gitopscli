import logging
import os

from ruamel.yaml import YAML

from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.io.yaml_util import merge_yaml_element
from gitopscli.gitops_exception import GitOpsException


def sync_apps_command(
    command,
    username,
    password,
    git_user,
    git_email,
    root_organisation,
    root_repository_name,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "sync-apps"
    git_api_config = GitApiConfig(username, password, git_provider, git_provider_url,)
    team_config_git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name)
    root_config_git_repo_api = GitRepoApiFactory.create(git_api_config, root_organisation, root_repository_name)
    with GitRepo(team_config_git_repo_api) as team_config_git_repo:
        with GitRepo(root_config_git_repo_api) as root_config_git_repo:
            __sync_apps(team_config_git_repo, root_config_git_repo, git_user, git_email)


def __sync_apps(team_config_git_repo: GitRepo, root_config_git_repo: GitRepo, git_user: str, git_email: str) -> None:
    logging.info("Team config repository: %s", team_config_git_repo.get_clone_url())
    logging.info("Root config repository: %s", root_config_git_repo.get_clone_url())

    repo_apps = __get_repo_apps(root_config_git_repo)
    logging.info("Found %s app(s) in apps repository: %s", len(repo_apps), ", ".join(repo_apps))

    logging.info("Searching apps repository in root repository's 'apps/' directory...")
    apps_config_file, apps_config_file_name, current_repo_apps, apps_from_other_repos = __find_apps_config_from_repo(
        team_config_git_repo, root_config_git_repo
    )
    if apps_config_file is None:
        raise GitOpsException(f"Could't find config file for apps repository in root repository's 'apps/' directory")

    if current_repo_apps == repo_apps:
        logging.info("Root repository already up-to-date. I'm done here.")
        return

    __check_if_app_already_exists(repo_apps, apps_from_other_repos)

    logging.info("Sync applications in root repository's %s.", apps_config_file_name)
    merge_yaml_element(apps_config_file, "applications", {repo_app: {} for repo_app in repo_apps}, True)
    __commit_and_push(team_config_git_repo, root_config_git_repo, git_user, git_email, apps_config_file_name)


def __find_apps_config_from_repo(team_config_git_repo: GitRepo, root_config_git_repo: GitRepo):
    yaml = YAML()
    apps_from_other_repos = []  # List for all entries in .applications from each config repository
    found_app_config_file = None
    found_app_config_file_name = None
    found_app_config_apps = set()
    bootstrap_entries = __get_bootstrap_entries(root_config_git_repo)
    for bootstrap_entry in bootstrap_entries:
        if "name" not in bootstrap_entry:
            raise GitOpsException("Every bootstrap entry must have a 'name' property.")
        app_file_name = "apps/" + bootstrap_entry["name"] + ".yaml"
        logging.info("Analyzing %s in root repository", app_file_name)
        app_config_file = root_config_git_repo.get_full_file_path(app_file_name)
        try:
            with open(app_config_file, "r") as stream:
                app_config_content = yaml.load(stream)
        except FileNotFoundError as ex:
            raise GitOpsException(f"File '{app_file_name}' not found in root repository.") from ex
        if "repository" not in app_config_content:
            raise GitOpsException(f"Cannot find key 'repository' in '{app_file_name}'")
        if app_config_content["repository"] == team_config_git_repo.get_clone_url():
            logging.info("Found apps repository in %s", app_file_name)
            found_app_config_file = app_config_file
            found_app_config_file_name = app_file_name
            found_app_config_apps = __get_applications_from_app_config(app_config_content)
        else:
            apps_from_other_repos += __get_applications_from_app_config(app_config_content)
    return found_app_config_file, found_app_config_file_name, found_app_config_apps, apps_from_other_repos


def __get_applications_from_app_config(app_config):
    apps = []
    if "applications" in app_config and app_config["applications"] is not None:
        apps += app_config["applications"].keys()
    return set(apps)


def __commit_and_push(
    team_config_git_repo: GitRepo, root_config_git_repo: GitRepo, git_user: str, git_email: str, app_file_name: str
):
    author = team_config_git_repo.get_author_from_last_commit()
    root_config_git_repo.commit(git_user, git_email, f"{author} updated " + app_file_name)
    root_config_git_repo.push("master")


def __get_bootstrap_entries(root_config_git_repo: GitRepo):
    root_config_git_repo.checkout("master")
    bootstrap_values_file = root_config_git_repo.get_full_file_path("bootstrap/values.yaml")
    try:
        with open(bootstrap_values_file, "r") as stream:
            bootstrap_yaml = YAML().load(stream)
    except FileNotFoundError as ex:
        raise GitOpsException("File 'bootstrap/values.yaml' not found in root repository.") from ex
    if "bootstrap" not in bootstrap_yaml:
        raise GitOpsException("Cannot find key 'bootstrap' in 'bootstrap/values.yaml'")
    return bootstrap_yaml["bootstrap"]


def __get_repo_apps(team_config_git_repo: GitRepo):
    team_config_git_repo.checkout("master")
    repo_dir = team_config_git_repo.get_full_file_path(".")
    return {
        name
        for name in os.listdir(repo_dir)
        if os.path.isdir(os.path.join(repo_dir, name)) and not name.startswith(".")
    }


def __check_if_app_already_exists(apps_dirs, apps_from_other_repos):
    for app_key in apps_dirs:
        if app_key in apps_from_other_repos:
            raise GitOpsException(f"application '{app_key}' already exists in a different repository")