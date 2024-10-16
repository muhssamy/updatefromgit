"""
    How To update From Git
"""

import argparse
import logging
import os
import sys
import time

from azlog import AzLogger

from updatefromgit import (
    acquire_token_user_id_password_confidential,
    commit_all_items_to_git,
    get_git_status,
    update_workspace_from_git,
)

logger = AzLogger(__name__)
logger.setLevel(logging.INFO)


FABRIC_API_URL = "https://api.fabric.microsoft.com/v1"
CLIENT_ID = ""
TENANT_ID = ""
USERNAME = ""
PASSWORD = ""
WORKSPACE_ID = ""


def set_main_parameters():
    """
    Getting variables from argument
    """
    parser = argparse.ArgumentParser(description="Update workspace from GIT")
    parser.add_argument("--WORKSPACE_ID", type=str, required=True, help="Workspace ID")
    parser.add_argument("--CLIENT_ID", type=str, required=True, help="Client ID")
    parser.add_argument(
        "--CLIENT_SECRET", type=str, required=True, help="Client Secret"
    )
    parser.add_argument("--TENANT_ID", type=str, required=True, help="Tenant ID")
    parser.add_argument("--USER_NAME", type=str, required=True, help="Username")
    parser.add_argument("--PASSWORD", type=str, required=True, help="Password")
    args = parser.parse_args()

    global WORKSPACE_ID
    global CLIENT_ID
    global CLIENT_SECRET
    global TENANT_ID
    global USERNAME
    global PASSWORD

    WORKSPACE_ID = args.WORKSPACE_ID
    CLIENT_ID = args.CLIENT_ID
    TENANT_ID = args.TENANT_ID
    USERNAME = args.USER_NAME
    PASSWORD = args.PASSWORD
    CLIENT_SECRET = args.CLIENT_SECRET

    logger.command(f"Workspace ID {WORKSPACE_ID}")
    logger.command(f"UserName {USERNAME}")


def main_func():
    """
    main Function
    """
    set_main_parameters()
    access_token = acquire_token_user_id_password_confidential(
        TENANT_ID, CLIENT_ID, USERNAME, PASSWORD, CLIENT_SECRET
    )
    update_workspace_from_git(WORKSPACE_ID, access_token)
    # time.sleep(100)
    # workspace_head = get_git_status(WORKSPACE_ID, access_token)
    # commit_all_items_to_git(WORKSPACE_ID, workspace_head, access_token)

    logger.command("Program Completed")


if __name__ == "__main__":
    main_func()
