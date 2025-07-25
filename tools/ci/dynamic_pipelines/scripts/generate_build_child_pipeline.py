# SPDX-FileCopyrightText: 2024-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
"""This file is used for generating the child pipeline for build jobs."""

import argparse
import os
import typing as t

import __init__  # noqa: F401 # inject the system path
import yaml
from idf_build_apps.manifest import FolderRule
from idf_build_apps.utils import semicolon_separated_str_to_list
from idf_ci.idf_gitlab import build_child_pipeline
from idf_ci_utils import IDF_PATH

BUILD_CHILD_PIPELINE_FILEPATH = os.path.join(IDF_PATH, 'build_child_pipeline.yml')
TEST_PATHS = ['examples', os.path.join('tools', 'test_apps'), 'components']


def _separate_str_to_list(s: str) -> t.List[str]:
    """
    Gitlab env file will escape the doublequotes in the env file, so we need to remove them

    For example,

    in pipeline.env file we have

    MR_MODIFIED_COMPONENTS="app1;app2"
    MR_MODIFIED_FILES="main/app1.c;main/app2.c"

    gitlab will load the doublequotes as well, so we need to remove the doublequotes
    """
    return semicolon_separated_str_to_list(s.strip('"'))  # type: ignore


def main(arguments: argparse.Namespace) -> None:
    # load from default build test rules config file
    extra_default_build_targets: t.List[str] = []
    if arguments.default_build_test_rules:
        with open(arguments.default_build_test_rules) as fr:
            configs = yaml.safe_load(fr)

        if configs:
            extra_default_build_targets = configs.get('extra_default_build_targets') or []

    if extra_default_build_targets:
        FolderRule.DEFAULT_BUILD_TARGETS.extend(extra_default_build_targets)

    build_child_pipeline(
        paths=args.paths,
        modified_files=args.modified_files,
        compare_manifest_sha_filepath=args.compare_manifest_sha_filepath,
        yaml_output=args.yaml_output,
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate build child pipeline',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-o',
        '--yaml-output',
        default=BUILD_CHILD_PIPELINE_FILEPATH,
        help='Output YAML path',
    )
    # use relative path to avoid absolute path in pipeline
    parser.add_argument(
        '-p',
        '--paths',
        nargs='+',
        default=TEST_PATHS,
        help='Paths to the apps to build.',
    )
    parser.add_argument(
        '--default-build-test-rules',
        default=os.path.join(IDF_PATH, '.gitlab', 'ci', 'default-build-test-rules.yml'),
        help='default build test rules config file',
    )
    parser.add_argument(
        '--compare-manifest-sha-filepath',
        default=os.path.join(IDF_PATH, '.manifest_sha'),
        help='Path to the recorded manifest sha file generated by `idf-build-apps dump-manifest-sha`',
    )
    parser.add_argument(
        '--modified-files',
        type=_separate_str_to_list,
        default=os.getenv('MR_MODIFIED_FILES'),
        help='semicolon-separated string which specifies the modified files. '
        'app with `depends_filepatterns` set in the corresponding manifest files would only be built '
        'if any of the specified file pattern matches any of the specified modified files. '
        'If set to "", the value would be considered as None. '
        'If set to ";", the value would be considered as an empty list',
    )

    args = parser.parse_args()

    main(args)
