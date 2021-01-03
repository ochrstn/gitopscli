from dataclasses import dataclass


@dataclass
class GitRepoPathRef:
    git_url: str
    org: str
    repo: str
    branch: str
    path: str
