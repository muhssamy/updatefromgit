"""
     Git Funtions 

    Script to Update From and To Fabric workspaces
"""

import json
import logging
import os
import time

import msal
import requests
from azlog import AzLogger

logger = AzLogger(__name__)
logger.setLevel(logging.INFO)
# Constants

FABRIC_API_URL = "https://api.fabric.microsoft.com/v1"
CLIENT_ID = ""
TENANT_ID = ""
USERNAME = ""
PASSWORD = ""
WORKSPACE_ID = ""


def acquire_token_user_id_password_confidential(
    tenant_id: str,
    client_id: str,
    user_name: str,
    password: str,
    client_credential: str,
):
    """
    Get Entra ID Token on behalf of a user using service principle with Confidential Application

    Parameters
    ----------
    tenant_id : str
        Nahdi Tenant ID
    client_id : str
        Service Principle ID
    user_name : str
        user email used to run this process
    password : str
        user passowrd
    client_credential : str
        Service Principle secret

    Returns
    -------
    Entra Id Token
    """
    logger.command("Generating token for Fabric APIs")
    # Initialize the MSAL Confidential client
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_credential
    )
    scopes = ["https://api.fabric.microsoft.com/.default"]
    result = app.acquire_token_by_username_password(user_name, password, scopes)
    if "access_token" in result:
        access_token = result["access_token"]
    else:
        access_token = None
    return access_token


def acquire_token_user_id_password_public(
    tenant_id: str, client_id: str, user_name: str, password: str
):
    """
    Get Entra ID Token on behalf of a user using service principle with public Appliction

    Parameters
    ----------
    tenant_id : str
        Nahdi Tenant ID
    client_id : str
        Service Principle ID
    user_name : str
        user email used to run this process
    password : str
        user passowrd
    client_credential : str
        Service Principle secret

    Returns
    -------
    Entra Id Token
    """
    logger.command("Generating token for Fabric APIs")
    # Initialize the MSAL Confidential client
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id, authority=authority)
    scopes = ["https://api.fabric.microsoft.com/.default"]
    result = app.acquire_token_by_username_password(user_name, password, scopes)
    if "access_token" in result:
        access_token = result["access_token"]
    else:
        access_token = None
    return access_token


def poll_lro_get_status(location_url: str, headers: dict, delay_second: int):
    """
    Fabric Long Running Oprations

    https://learn.microsoft.com/en-us/rest/api/fabric/articles/long-running-operation

     Parameters
     ----------
     location_url : str
         the location header that will be returned to you while the operation is still running
     headers : dict
         headers
     delay_second : int
         Time to wait
    """
    while True:
        status_response = requests.get(location_url, headers=headers, timeout=120)
        status_code = status_response.status_code
        if status_code == 200:
            logger.command("Git Sync completed")
            break
        status = status_response.json().get("Status", "Unknown")
        if status not in ("NotStarted", "Running"):
            break
        logger.command("GIT sync operation is still in progress...")
        time.sleep(delay_second)  # Wait for 10 seconds before polling again


def get_git_status(workspace_id: str, token):
    """
    The status indicates changes to the item(s) since the last workspace and remote branch sync.
    If both locations were modified, the API flags a conflict.

    https://learn.microsoft.com/en-us/rest/api/fabric/core/git/get-status

    Parameters
    ----------
    workspace_id : str
        fabric workspace id
    token : _type_
        entra id token

    Returns
    -------
    str
        workspace Head
    """
    try:
        logger.command("Retriving latest Workspace commit ID")
        url = f"{FABRIC_API_URL}/workspaces/{workspace_id}/git/status"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(url, headers=headers, timeout=120)
        # response.raise_for_status()
        workspaceheadid = response.json().get("workspaceHead")
        logger.command(f"Latest workspacehead: {workspaceheadid}")
        return workspaceheadid
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get Git status: {e}")
        os._exit(1)
        return None


def update_workspace_from_git(workspace_id: str, token):
    """
    The update only affects items in the workspace that were changed in those commits


    https://learn.microsoft.com/en-us/rest/api/fabric/core/git/update-from-git

    Parameters
    ----------
    workspace_id : str
        Fabric Workspace ID
    token : _type_
        Entra Id Token
    """
    try:
        logger.command(
            f"Starting the UpateSync operation for the workspace {workspace_id}"
        )
        headers = {"Authorization": f"Bearer {token}"}
        # Get remoteCommitHash for the git
        gitstatusurl = f"{FABRIC_API_URL}/workspaces/{workspace_id}/git/status"
        response = requests.get(gitstatusurl, headers=headers, timeout=120)

        if response.status_code == 200:
            git_status = response.json()
            remote_commit_hash = git_status["remoteCommitHash"]
            workspace_head = git_status["workspaceHead"]
            logger.command(f"Remote Commit Hash: {remote_commit_hash}")
            logger.command(f"Workspace Head: {workspace_head}")

            # Define the update parameters with conflict resolution policy
            update_params = {
                "workspaceHead": workspace_head,
                "remoteCommitHash": remote_commit_hash,
                "conflictResolution": {
                    "conflictResolutionType": "Workspace",
                    "conflictResolutionPolicy": "PreferRemote",
                },
                "options": {"allowOverrideItems": True},
            }

            # Update the workspace
            updateworkspaceurl = (
                f"{FABRIC_API_URL}/workspaces/{workspace_id}/git/updateFromGit"
            )

            update_response = requests.post(
                updateworkspaceurl, headers=headers, json=update_params, timeout=120
            )

            if update_response.status_code == 200:
                git_status = update_response.json()
                logger.command(
                    f"Workspace {workspace_id} synced successfully with RemoteSync conflict resolution!"
                )
                # logger.command(git_status)
            elif update_response.status_code == 202:
                logger.command("Request accepted, update workspace is in progress.")
                # time.sleep(10)
                location_url = update_response.headers.get("Location")
                # operation = update_response.headers.get("x-ms-operation-id")
                logger.command(
                    f"Polling URL to track operation status is {location_url}"
                )
                # logger.command(f"Polling URL to track operation status is {operation}")
                time.sleep(20)
                poll_lro_get_status(location_url, headers, 10)

            else:
                logger.error(
                    f"Failed to update the workspace. Status Code: {update_response.status_code} - {update_response.text}"
                )
                os._exit(1)
        else:
            logger.error(
                f"Failed to retrieve Git status. Status Code: {response.status_code} This is the Error {response.json()}"
            )
            os._exit(1)

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        os._exit(1)


def commit_all_items_to_git(workspace_id: str, workspace_head: str, token):
    """
    Commits the changes made in the workspace to the connected remote branch.


    https://learn.microsoft.com/en-us/rest/api/fabric/core/git/commit-to-git

    Parameters
    ----------
    workspace_id : str
        Fabric Workspace ID
    workspace_head : str
        workspace Head
    token : _type_
        Entra ID Token
    """
    try:
        logger.command(
            f"Initialize committ of all changed items for workspace {workspace_id}"
        )
        commit_url = f"{FABRIC_API_URL}/workspaces/{workspace_id}/git/commitToGit"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "mode": "All",
            "workspaceHead": workspace_head,
            "commitMessage": "Committing all items from Fabric workspace to Git",
        }
        response = requests.post(commit_url, headers=headers, json=payload, timeout=120)

        if response.status_code == 200:
            logger.command("Successfully committed all items to Git.")
        elif response.status_code == 400:
            logger.warning("No Changed Items to commmit")
        else:
            logger.error(f"Failed to commit items. Status code: {response.status_code}")
            os._exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to commit items: {e}")
        os._exit(1)


def generate_lakehouse_config(workspace_id: str, token: str) -> dict:
    """
    Fetch only 'Lakehouse' items from the workspace and return a structured dictionary with relevant data.

    Parameters
    ----------
    workspace_id : str
        The ID of the workspace for which the items need to be fetched.
    token : str
        The authentication token to access the Microsoft Fabric API.

    Returns
    -------
    dict
        A dictionary containing Lakehouse items.
    """

    def fetch_workspace_items() -> list:
        url = f"{FABRIC_API_URL}/workspaces/{workspace_id}/items"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        items = response.json().get("value", [])
        return [item for item in items if item["type"] == "Lakehouse"]

    # Prepare data structure
    lakehouse_data = {}
    filtered_items = fetch_workspace_items()

    for item in filtered_items:
        lh_key = f"{item['displayName']}"
        lakehouse_data[lh_key] = {
            "typeProperties": {
                "artifactId": item["id"],
                "workspaceId": workspace_id,
                "rootFolder": "Tables",
            },
            "name": item["displayName"],
        }

    return lakehouse_data


def generate_warehouse_config(workspace_id: str, token: str) -> dict:
    """
    Fetch 'Warehouse' items from the workspace, retrieve their details, and return a structured dictionary.

    Parameters
    ----------
    workspace_id : str
        The ID of the workspace for which the items need to be fetched.
    token : str
        The authentication token to access the Microsoft Fabric API.

    Returns
    -------
    dict
        A dictionary containing Warehouse items.
    """

    def fetch_workspace_items() -> list:
        url = f"{FABRIC_API_URL}/workspaces/{workspace_id}/items"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        items = response.json().get("value", [])
        return [item for item in items if item["type"] == "Warehouse"]

    def fetch_warehouse_details(warehouse_id: str) -> dict:
        url = f"{FABRIC_API_URL}/workspaces/{workspace_id}/warehouses/{warehouse_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()

    # Prepare data structure
    warehouse_data = {}
    filtered_items = fetch_workspace_items()

    for item in filtered_items:
        warehouse = fetch_warehouse_details(item["id"])
        wh_key = f"{item['displayName']}"
        warehouse_data[wh_key] = {
            "typeProperties": {
                "artifactId": warehouse["id"],
                "endpoint": warehouse["properties"]["connectionString"],
                "workspaceId": workspace_id,
            },
            "objectId": warehouse["id"],
            "name": warehouse["displayName"],
        }

    return warehouse_data


def generate_config_file(
    lakehouse_workspace_id: str, warehouse_workspace_id: str, token: str
) -> None:
    """
    Run `generate_lakehouse_config` for the Lakehouse workspace and `generate_warehouse_config`
    for the Warehouse workspace, then merge the results into a single JSON object without
    any outer keys, such as 'warehouse' or 'lakehouse'.

    Parameters
    ----------
    lakehouse_workspace_id : str
        The workspace ID containing only 'Lakehouse' items.
    warehouse_workspace_id : str
        The workspace ID containing only 'Warehouse' items.
    token : str
        The authentication token.

    Returns
    -------
    None
        Saves the merged result to `linkedservice-config.json`.
    """

    # Run the function for Lakehouse items
    lakehouse_data = generate_lakehouse_config(lakehouse_workspace_id, token)

    # Run the function for Warehouse items
    warehouse_data = generate_warehouse_config(warehouse_workspace_id, token)

    # Merge the two dictionaries into one (no outer keys like 'warehouse' or 'lakehouse')
    merged_result = {**warehouse_data, **lakehouse_data}

    # Delete the file if it exists
    filename = "linkedservice-config.json"
    if os.path.exists(filename):
        os.remove(filename)

    # Save the merged result to the JSON file
    with open(filename, "w") as outfile:
        json.dump(merged_result, outfile, indent=4)

    logger.command(f"Linked service config file created: {filename}")
