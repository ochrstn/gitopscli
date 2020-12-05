import logging
import os
import uuid
import unittest
from uuid import UUID
from unittest.mock import call
import pytest
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.deploy import DeployCommand
from gitopscli.git import GitRepoApi, GitProvider, GitRepoApiFactory, GitRepo
from gitopscli.io.yaml_util import update_yaml_file
from .mock_mixin import MockMixin


class DeployCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(DeployCommand)

        self.os_mock = self.monkey_patch(os)
        self.os_mock.path.isfile.return_value = True

        self.update_yaml_file_mock = self.monkey_patch(update_yaml_file)
        self.update_yaml_file_mock.return_value = True

        self.logging_mock = self.monkey_patch(logging)
        self.logging_mock.info.return_value = None

        self.uuid_mock = self.monkey_patch(uuid)
        self.uuid_mock.uuid4.return_value = UUID("b973b5bb-64a6-4735-a840-3113d531b41c")

        self.git_repo_api_mock = self.create_mock(GitRepoApi)
        self.git_repo_api_mock.create_pull_request.return_value = GitRepoApi.PullRequestIdAndUrl(
            42, "<url of dummy pr>"
        )
        self.git_repo_api_mock.merge_pull_request.return_value = None
        self.git_repo_api_mock.delete_branch.return_value = None

        self.git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock

        self.git_repo_mock = self.monkey_patch(GitRepo)
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.__exit__.return_value = False
        self.git_repo_mock.checkout.return_value = None
        self.git_repo_mock.new_branch.return_value = None
        self.git_repo_mock.commit.return_value = None
        self.git_repo_mock.push.return_value = None
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"

        self.seal_mocks()

    def test_happy_flow(self):
        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.d' to 'bar' in test/file.yml"),
            call.GitRepo.push("master"),
        ]

    def test_create_pr_single_value_change_happy_flow(self):
        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=True,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.uuid.uuid4(),
            call.GitRepo.new_branch("gitopscli-deploy-b973b5bb"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.GitRepo.push("gitopscli-deploy-b973b5bb"),
            call.GitRepoApi.create_pull_request(
                "gitopscli-deploy-b973b5bb",
                "master",
                "Updated values in test/file.yml",
                "Updated 1 value in `test/file.yml`:\n```yaml\na.b.c: foo\n```\n",
            ),
        ]

    def test_create_pr_multiple_value_changes_happy_flow(self):
        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=True,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.uuid.uuid4(),
            call.GitRepo.new_branch("gitopscli-deploy-b973b5bb"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.d' to 'bar' in test/file.yml"),
            call.GitRepo.push("gitopscli-deploy-b973b5bb"),
            call.GitRepoApi.create_pull_request(
                "gitopscli-deploy-b973b5bb",
                "master",
                "Updated values in test/file.yml",
                "Updated 2 values in `test/file.yml`:\n```yaml\na.b.c: foo\na.b.d: bar\n```\n",
            ),
        ]

    def test_create_pr_and_merge_happy_flow(self):
        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=True,
            auto_merge=True,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.uuid.uuid4(),
            call.GitRepo.new_branch("gitopscli-deploy-b973b5bb"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.d' to 'bar' in test/file.yml"),
            call.GitRepo.push("gitopscli-deploy-b973b5bb"),
            call.GitRepoApi.create_pull_request(
                "gitopscli-deploy-b973b5bb",
                "master",
                "Updated values in test/file.yml",
                "Updated 2 values in `test/file.yml`:\n```yaml\na.b.c: foo\na.b.d: bar\n```\n",
            ),
            call.GitRepoApi.merge_pull_request(42),
            call.GitRepoApi.delete_branch("gitopscli-deploy-b973b5bb"),
        ]

    def test_single_commit_happy_flow(self):
        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=True,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "updated 2 values in test/file.yml\n\na.b.c: foo\na.b.d: bar"),
            call.GitRepo.push("master"),
        ]

    def test_single_commit_single_value_change_happy_flow(self):
        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=True,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.GitRepo.push("master"),
        ]

    def test_commit_message_multiple_value_changes_happy_flow(self):
        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message="testcommit",
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "testcommit"),
            call.GitRepo.push("master"),
        ]

    def test_checkout_error(self):
        checkout_exception = GitOpsException("dummy checkout error")
        self.git_repo_mock.checkout.side_effect = checkout_exception

        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        with pytest.raises(GitOpsException) as ex:
            DeployCommand(args).execute()
        self.assertEqual(ex.value, checkout_exception)

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
        ]

    def test_file_not_found(self):
        self.os_mock.path.isfile.return_value = False

        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        with pytest.raises(GitOpsException) as ex:
            DeployCommand(args).execute()
        self.assertEqual(str(ex.value), "No such file: test/file.yml")

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
        ]

    def test_key_not_found(self):
        self.update_yaml_file_mock.side_effect = KeyError("dummy key error")

        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        with pytest.raises(GitOpsException) as ex:
            DeployCommand(args).execute()
        self.assertEqual(str(ex.value), "Key 'a.b.c' not found in test/file.yml")

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
        ]

    def test_nothing_to_update(self):
        self.update_yaml_file_mock.return_value = False

        args = DeployCommand.Args(
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            commit_message=None,
        )
        DeployCommand(args).execute()

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Yaml property %s already up-to-date", "a.b.c"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Yaml property %s already up-to-date", "a.b.d"),
            call.logging.info("All values already up-to-date. I'm done here"),
        ]