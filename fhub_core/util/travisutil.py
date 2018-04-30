import logging
import os

import funcy
import git

from fhub_core.exc import UnexpectedTravisEnvironmentError
from fhub_core.util.gitutil import PullRequestBuildDiffer

logger = logging.getLogger(__name__)


def get_travis_env_or_fail(name):
    if name in os.environ:
        return os.environ[name]
    else:
        # dump_travis_env_vars()
        raise UnexpectedTravisEnvironmentError


def ensure_expected_travis_env_vars(names):
    if not set(names).issubset(set(os.environ.keys())):
        raise UnexpectedTravisEnvironmentError


def dump_travis_env_vars():
    travis_env_vars = funcy.select_keys(
        lambda key: key.startswith('TRAVIS'),
        os.environ)
    logger.debug(travis_env_vars)


def get_travis_pr_num():
    '''Return the PR number if the job is a pull request, None otherwise

    See also:
        - <https://docs.travis-ci.com/user/environment-variables
          /#Default-Environment-Variables>
    '''
    try:
        travis_pull_request = get_travis_env_or_fail('TRAVIS_PULL_REQUEST')
        if travis_pull_request == 'false':
            return None
        else:
            try:
                pr_num = int(travis_pull_request)
                return pr_num
            except ValueError:
                return None
    except UnexpectedTravisEnvironmentError:
        return None


def is_travis_pr():
    '''Check if the current job is a pull request build'''
    return get_travis_pr_num() is not None


class TravisPullRequestBuildDiffer(PullRequestBuildDiffer):
    def __init__(self, pr_num):
        super().__init__(pr_num, None)
        self.repo = self._detect_repo

    def check_environment(self):
        ensure_expected_travis_env_vars([
            'TRAVIS_BUILD_DIR',
            'TRAVIS_PULL_REQUEST',
            'TRAVIS_COMMIT_RANGE',
        ])

        travis_pr_num = get_travis_pr_num()
        if travis_pr_num != self.pr_num:
            raise UnexpectedTravisEnvironmentError

    def get_diff_str(self):
        return get_travis_env_or_fail('TRAVIS_COMMIT_RANGE')

    def _detect_repo(self):
        build_dir = get_travis_env_or_fail('TRAVIS_BUILD_DIR')
        return git.Repo(build_dir)