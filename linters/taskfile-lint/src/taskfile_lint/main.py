from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

REQUIRED_ATTR_ORDER = [
    "aliases",
    "desc",
    "internal",
    "summary",
    "label",
    "prefix",
    "silent",
    "dotenv",
    "env",
    "vars",
    "requires",
    "sources",
    "dir",
    "platforms",
    "set",
    "shopt",
    "generates",
    "method",
    "prompt",
    "run",
    "deps",
    "preconditions",
    "status",
    "cmd",
    "cmds",
    "ignore_error",
    "interactive",
]


def main(argv=None):
    if argv is None:
        argv = sys.argv

    args_parser = argparse.ArgumentParser(description="Lints the given taskfile.")
    args_parser.add_argument("--file", help="Taskfile to lint.", required=True)
    parsed_args = args_parser.parse_args(argv[1:])
    taskfile_path: Path = Path(parsed_args.file)

    linting_failed = False
    if taskfile_path.suffix != ".yaml":
        print(f"{taskfile_path}: Taskfile must use the '.yaml' extension.", file=sys.stderr)
        linting_failed = True

    with open(taskfile_path, "r") as f:
        doc = yaml.safe_load(f)

    if not _validate_task_attribute_order_for_all_tasks(taskfile_path, doc):
        linting_failed = True

    if linting_failed:
        return 1

    return 0


def _validate_task_attribute_order_for_all_tasks(
    taskfile_path: Path, taskfile: Dict[str, Any]
) -> bool:
    """
    Validates that the order of attributes in each task of `taskfile` matches the order documented
    at https://docs.yscope.com/dev-guide/contrib-guides-taskfiles.html#ordering-of-task-attributes

    :param taskfile_path:
    :param taskfile:
    :return: Whether the order matches.
    """

    if "tasks" not in taskfile:
        # No tasks to validate
        return True

    linting_failed = False
    for task_name, task_value in taskfile["tasks"].items():
        if type(task_value) is list:
            # Task is using shorthand syntax for a list of commands
            continue

        if type(task_value) is dict:
            linting_failed |= not _validate_task_attribute_order(
                taskfile_path, task_name, task_value
            )
        else:
            # We don't treat this as a failure since if `task` itself doesn't treat it as invalid,
            # then it's likely a limitation of the linter.
            logger.error(f"{taskfile_path}: Task '{task_name}' is neither a dictionary nor a list.")
            continue

    if linting_failed:
        return False


def _validate_task_attribute_order(
    taskfile_path: Path, task_name: str, task_attributes: Dict[str, Any]
) -> bool:
    """
    Validates that the order of attributes in `task_attributes` matches the order documented at
    https://docs.yscope.com/dev-guide/contrib-guides-taskfiles.html#ordering-of-task-attributes

    :param taskfile_path:
    :param task_name:
    :param task_attributes:
    :return: Whether the order matches.
    """

    attr_names = list(task_attributes.keys())
    sorted_attr_names = sorted(attr_names, key=lambda x: REQUIRED_ATTR_ORDER.index(x))
    is_unsorted = False
    for a, b in zip(attr_names, sorted_attr_names):
        if a != b:
            is_unsorted = True
            break
    if is_unsorted:
        print(
            f"{taskfile_path}: Task '{task_name}' has unsorted attributes.",
            file=sys.stderr,
        )
        print(f"    Expected order: {sorted_attr_names}", file=sys.stderr)
        print(f"    Actual order  : {attr_names}", file=sys.stderr)
        return False

    return True


if "__main__" == __name__:
    main(sys.argv)
