"""
     Initalize the dependencies
"""

from .gitfunctions import (
    acquire_token_user_id_password_confidential,
    acquire_token_user_id_password_public,
    commit_all_items_to_git,
    generate_config_file,
    get_git_status,
    update_workspace_from_git,
)
from .update_linked_services import update_linked_services
