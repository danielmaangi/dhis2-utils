import requests
import json
import os
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AccessLevel(Enum):
    """Access levels for DHIS2 sharing"""
    NO_ACCESS = "--------"
    READ = "r-------"
    READ_WRITE = "rw------"
    READ_WRITE_DELETE = "rwd-----"

@dataclass
class UserAccess:
    """Represents user access settings"""
    id: str
    access: str
    displayName: Optional[str] = None

@dataclass
class UserGroupAccess:
    """Represents user group access settings"""
    id: str
    access: str
    displayName: Optional[str] = None

@dataclass
class SharingSettings:
    """Represents sharing settings for a metadata object"""
    public_access: str = "--------"
    external_access: bool = False
    users: List[UserAccess] = None
    user_groups: List[UserGroupAccess] = None
    
    def __post_init__(self):
        if self.users is None:
            self.users = []
        if self.user_groups is None:
            self.user_groups = []

class DHIS2SharingClient:
    """Client for managing DHIS2 metadata sharing"""
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize DHIS2 sharing client
        
        Args:
            base_url: DHIS2 instance URL (e.g., 'https://play.dhis2.org/demo')
            username: DHIS2 username
            password: DHIS2 password
        """
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_sharing_settings(self, metadata_type: str, metadata_id: str) -> Dict:
        """
        Get current sharing settings for a metadata object
        
        Args:
            metadata_type: Type of metadata (e.g., 'categoryOptions', 'dataElements')
            metadata_id: ID of the metadata object
            
        Returns:
            Current sharing settings
        """
        url = f"{self.base_url}/api/{metadata_type}/{metadata_id}/sharing"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get sharing settings: {e}")
    
    def update_sharing_settings(self, metadata_type: str, metadata_id: str, 
                              sharing_settings: Union[SharingSettings, Dict]) -> Dict:
        """
        Update sharing settings for a metadata object
        
        Args:
            metadata_type: Type of metadata (e.g., 'categoryOptions', 'dataElements')
            metadata_id: ID of the metadata object
            sharing_settings: New sharing settings
            
        Returns:
            Response from DHIS2 API
        """
        url = f"{self.base_url}/api/{metadata_type}/{metadata_id}/sharing"
        
        # Convert SharingSettings to dict if needed
        if isinstance(sharing_settings, SharingSettings):
            data = self._sharing_settings_to_dict(sharing_settings)
        else:
            data = sharing_settings
        
        try:
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            # Handle empty responses
            if response.text.strip() == '':
                return {"status": "success", "message": "Sharing settings updated successfully"}
            
            try:
                return response.json()
            except ValueError as json_error:
                # If JSON parsing fails, return the raw text
                return {
                    "status": "success", 
                    "message": "Sharing settings updated successfully",
                    "raw_response": response.text
                }
                
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_details = f"HTTP {response.status_code}: {response.text}" if 'response' in locals() else str(e)
            raise Exception(f"Failed to update sharing settings: {error_details}")
    
    def share_category_option(self, category_option_id: str, 
                            users: List[UserAccess] = None,
                            user_groups: List[UserGroupAccess] = None,
                            public_access: str = "--------") -> Dict:
        """
        Share a category option with specific users/groups
        
        Args:
            category_option_id: ID of the category option
            users: List of user access settings
            user_groups: List of user group access settings
            public_access: Public access level
            
        Returns:
            Response from DHIS2 API
        """
        sharing_settings = SharingSettings(
            public_access=public_access,
            users=users or [],
            user_groups=user_groups or []
        )
        
        return self.update_sharing_settings('categoryOptions', category_option_id, sharing_settings)
    
    def share_multiple_category_options(self, category_option_ids: List[str],
                                      users: List[UserAccess] = None,
                                      user_groups: List[UserGroupAccess] = None,
                                      public_access: str = "--------") -> List[Dict]:
        """
        Share multiple category options with the same settings
        
        Args:
            category_option_ids: List of category option IDs
            users: List of user access settings
            user_groups: List of user group access settings
            public_access: Public access level
            
        Returns:
            List of responses from DHIS2 API
        """
        results = []
        for option_id in category_option_ids:
            try:
                result = self.share_category_option(
                    option_id, users, user_groups, public_access
                )
                results.append({
                    'id': option_id,
                    'status': 'success',
                    'response': result
                })
            except Exception as e:
                results.append({
                    'id': option_id,
                    'status': 'error',
                    'error': str(e)
                })
        return results
    
    def get_users(self, fields: str = "id,displayName,username") -> List[Dict]:
        """Get list of users from DHIS2"""
        url = f"{self.base_url}/api/users"
        params = {'fields': fields, 'paging': 'false'}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json().get('users', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get users: {e}")
    
    def get_user_groups(self, fields: str = "id,displayName") -> List[Dict]:
        """Get list of user groups from DHIS2"""
        url = f"{self.base_url}/api/userGroups"
        params = {'fields': fields, 'paging': 'false'}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json().get('userGroups', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get user groups: {e}")
    
    def get_category_options(self, fields: str = "id,displayName,code") -> List[Dict]:
        """Get list of category options from DHIS2"""
        url = f"{self.base_url}/api/categoryOptions"
        params = {'fields': fields, 'paging': 'false'}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json().get('categoryOptions', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get category options: {e}")
    
    def _sharing_settings_to_dict(self, settings: SharingSettings) -> Dict:
        """Convert SharingSettings to dictionary format expected by DHIS2 API"""
        
        # Convert users list to dict with user IDs as keys
        users_dict = {}
        for user in settings.users:
            users_dict[user.id] = {
                'access': user.access,
                'displayName': user.displayName
            }
        
        # Convert user groups list to dict with group IDs as keys  
        user_groups_dict = {}
        for group in settings.user_groups:
            user_groups_dict[group.id] = {
                'access': group.access,
                'displayName': group.displayName
            }
        
        return {
            'sharing': {
                'external': settings.external_access,
                'users': users_dict,
                'userGroups': user_groups_dict,
                'public': settings.public_access
            }
        }
    
    def find_user_by_username(self, username: str) -> Optional[Dict]:
        """Find user by username"""
        users = self.get_users()
        for user in users:
            if user.get('username') == username:
                return user
        return None
    
    def find_user_group_by_name(self, name: str) -> Optional[Dict]:
        """Find user group by name"""
        groups = self.get_user_groups()
        for group in groups:
            if group.get('displayName') == name:
                return group
        return None

    def share_all_category_options_with_all_users(self, access_level: str = AccessLevel.READ.value) -> List[Dict]:
        """
        Share all category options with all users
        
        Args:
            access_level: Access level to grant to all users
            
        Returns:
            List of results for each category option
        """
        try:
            # Get all category options
            print("Fetching all category options...")
            category_options = self.get_category_options()
            print(f"Found {len(category_options)} category options")
            
            # Get all users
            print("Fetching all users...")
            users = self.get_users()
            print(f"Found {len(users)} users")
            
            if not category_options:
                return [{"status": "error", "message": "No category options found"}]
            
            if not users:
                return [{"status": "error", "message": "No users found"}]
            
            # Create user access list for all users
            user_access_list = []
            for user in users:
                user_access = UserAccess(
                    id=user['id'],
                    access=access_level,
                    displayName=user.get('displayName', user.get('username', 'Unknown'))
                )
                user_access_list.append(user_access)
            
            print(f"Sharing {len(category_options)} category options with {len(user_access_list)} users...")
            
            # Share each category option with all users
            results = []
            for i, option in enumerate(category_options, 1):
                option_id = option['id']
                option_name = option.get('displayName', 'Unknown')
                
                print(f"Processing {i}/{len(category_options)}: {option_name}")
                
                try:
                    result = self.share_category_option(
                        option_id,
                        users=user_access_list,
                        public_access=access_level
                    )
                    
                    results.append({
                        'id': option_id,
                        'name': option_name,
                        'status': 'success',
                        'users_shared_with': len(user_access_list),
                        'response': result
                    })
                    
                except Exception as e:
                    results.append({
                        'id': option_id,
                        'name': option_name,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Summary
            successful = len([r for r in results if r['status'] == 'success'])
            failed = len([r for r in results if r['status'] == 'error'])
            
            print(f"\nSharing completed:")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Total: {len(results)}")
            
            return results
            
        except Exception as e:
            return [{"status": "error", "message": f"Failed to share all category options: {str(e)}"}]

def example_usage():
    """Example usage of the DHIS2 sharing client"""
    
    # Get credentials from environment variables
    base_url = os.getenv('DHIS2_BASE_URL')
    username = os.getenv('DHIS2_USERNAME')
    password = os.getenv('DHIS2_PASSWORD')
    
    # Validate environment variables
    if not all([base_url, username, password]):
        print("Error: Missing required environment variables.")
        print("Please ensure DHIS2_BASE_URL, DHIS2_USERNAME, and DHIS2_PASSWORD are set in your .env file.")
        return
    
    # Initialize client
    client = DHIS2SharingClient(
        base_url=base_url,
        username=username,
        password=password
    )
    
    try:
        # Share all category options with all users
        print("Starting bulk sharing operation...")
        results = client.share_all_category_options_with_all_users(AccessLevel.READ.value)
        
        # Display detailed results
        print("\nDetailed Results:")
        for result in results:
            if result['status'] == 'success':
                print(f"✓ {result['name']} - Shared with {result['users_shared_with']} users")
            else:
                print(f"✗ {result.get('name', 'Unknown')} - Error: {result.get('error', result.get('message', 'Unknown error'))}")
        
        # Show summary statistics
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'error'])
        
        print(f"\nFinal Summary:")
        print(f"Successfully shared: {successful} category options")
        print(f"Failed to share: {failed} category options")
        print(f"Total processed: {len(results)} category options")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    example_usage()
