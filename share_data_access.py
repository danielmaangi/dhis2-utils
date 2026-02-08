import requests
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DataAccessLevel(Enum):
    """Data access levels for DHIS2 sharing
    
    DHIS2 access string format: [metadata][data]
    - First 4 chars: metadata access (r/w/d/-)
    - Last 4 chars: data access (r/w/-)
    
    Examples:
    - "--------": No access
    - "--r-----": Data read only
    - "--rw----": Data read-write
    - "r-r-----": Metadata read + Data read
    - "r-rw----": Metadata read + Data read-write
    - "rwrw----": Full metadata and data access
    """
    NO_ACCESS = "--------"
    DATA_READ_ONLY = "--r-----"
    DATA_READ_WRITE = "--rw----"
    METADATA_READ_DATA_READ = "r-r-----"
    METADATA_READ_DATA_READWRITE = "r-rw----"
    FULL_ACCESS = "rwrw----"

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

class DHIS2DataSharingClient:
    """Client for managing DHIS2 data access permissions on category options"""
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize DHIS2 data sharing client
        
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
                              sharing_data: Dict) -> Dict:
        """
        Update sharing settings for a metadata object
        
        Args:
            metadata_type: Type of metadata (e.g., 'categoryOptions', 'dataElements')
            metadata_id: ID of the metadata object
            sharing_data: New sharing settings
            
        Returns:
            Response from DHIS2 API
        """
        url = f"{self.base_url}/api/{metadata_type}/{metadata_id}/sharing"
        
        try:
            response = self.session.put(url, json=sharing_data)
            response.raise_for_status()
            
            # Handle empty responses
            if response.text.strip() == '':
                return {"status": "success", "message": "Sharing settings updated successfully"}
            
            try:
                return response.json()
            except ValueError:
                return {
                    "status": "success", 
                    "message": "Sharing settings updated successfully",
                    "raw_response": response.text
                }
                
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_details = f"HTTP {response.status_code}: {response.text}" if 'response' in locals() else str(e)
            raise Exception(f"Failed to update sharing settings: {error_details}")
    
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
    
    def share_category_option_data_access(self, 
                                         category_option_id: str,
                                         users: List[UserAccess] = None,
                                         user_groups: List[UserGroupAccess] = None,
                                         public_access: str = "--------") -> Dict:
        """
        Share data access for a category option with specific users/groups
        
        Args:
            category_option_id: ID of the category option
            users: List of user access settings (should use data access levels)
            user_groups: List of user group access settings
            public_access: Public access level
            
        Returns:
            Response from DHIS2 API
        """
        # Convert users list to dict with user IDs as keys
        users_dict = {}
        if users:
            for user in users:
                users_dict[user.id] = {
                    'access': user.access,
                    'displayName': user.displayName
                }
        
        # Convert user groups list to dict with group IDs as keys  
        user_groups_dict = {}
        if user_groups:
            for group in user_groups:
                user_groups_dict[group.id] = {
                    'access': group.access,
                    'displayName': group.displayName
                }
        
        sharing_data = {
            'sharing': {
                'external': False,
                'users': users_dict,
                'userGroups': user_groups_dict,
                'public': public_access
            }
        }
        
        return self.update_sharing_settings('categoryOptions', category_option_id, sharing_data)
    
    def bulk_share_data_access_with_all_users(self, 
                                             access_level: str = DataAccessLevel.DATA_READ_WRITE.value,
                                             public_access: str = DataAccessLevel.DATA_READ_WRITE.value) -> List[Dict]:
        """
        Grant data access to all category options for all users
        
        This is the main function to solve the "User does not have write access to category option" error.
        It grants data write permissions to all users for all category options.
        
        Args:
            access_level: Data access level to grant to all users (default: data read-write)
            public_access: Public access level (default: data read-write)
            
        Returns:
            List of results for each category option
        """
        try:
            # Get all category options
            print("=" * 80)
            print("DHIS2 Data Access Sharing - Bulk Operation")
            print("=" * 80)
            print("\nFetching all category options...")
            category_options = self.get_category_options()
            print(f"✓ Found {len(category_options)} category options")
            
            # Get all users
            print("\nFetching all users...")
            users = self.get_users()
            print(f"✓ Found {len(users)} users")
            
            if not category_options:
                return [{"status": "error", "message": "No category options found"}]
            
            if not users:
                return [{"status": "error", "message": "No users found"}]
            
            # Create user access list for all users with DATA access
            user_access_list = []
            for user in users:
                user_access = UserAccess(
                    id=user['id'],
                    access=access_level,
                    displayName=user.get('displayName', user.get('username', 'Unknown'))
                )
                user_access_list.append(user_access)
            
            print(f"\n{'=' * 80}")
            print(f"Granting DATA ACCESS to {len(category_options)} category options")
            print(f"Access Level: {access_level} (Data Read-Write)")
            print(f"Users: {len(user_access_list)}")
            print(f"{'=' * 80}\n")
            
            # Share each category option with all users
            results = []
            for i, option in enumerate(category_options, 1):
                option_id = option['id']
                option_name = option.get('displayName', 'Unknown')
                
                # Progress indicator
                progress = f"[{i}/{len(category_options)}]"
                print(f"{progress} Processing: {option_name[:60]}...", end='', flush=True)
                
                try:
                    result = self.share_category_option_data_access(
                        option_id,
                        users=user_access_list,
                        public_access=public_access
                    )
                    
                    results.append({
                        'id': option_id,
                        'name': option_name,
                        'status': 'success',
                        'users_shared_with': len(user_access_list),
                        'access_level': access_level,
                        'response': result
                    })
                    
                    print(" ✓ Success")
                    
                except Exception as e:
                    results.append({
                        'id': option_id,
                        'name': option_name,
                        'status': 'error',
                        'error': str(e)
                    })
                    print(f" ✗ Failed: {str(e)[:50]}")
            
            # Summary
            successful = len([r for r in results if r['status'] == 'success'])
            failed = len([r for r in results if r['status'] == 'error'])
            
            print(f"\n{'=' * 80}")
            print("OPERATION COMPLETE")
            print(f"{'=' * 80}")
            print(f"✓ Successful: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
            print(f"✗ Failed: {failed}/{len(results)}")
            
            if failed > 0:
                print(f"\n⚠ Failed category options:")
                for result in results:
                    if result['status'] == 'error':
                        print(f"  - {result['name']}: {result['error']}")
            
            print(f"{'=' * 80}\n")
            
            return results
            
        except Exception as e:
            return [{"status": "error", "message": f"Failed to share data access: {str(e)}"}]
    
    def diagnose_category_option(self, category_option_id: str) -> Dict:
        """
        Diagnose data access issues for a specific category option
        
        Args:
            category_option_id: ID of the category option to diagnose
            
        Returns:
            Diagnostic information about the category option's sharing settings
        """
        try:
            sharing = self.get_sharing_settings('categoryOptions', category_option_id)
            
            # Analyze sharing settings
            public_access = sharing.get('object', {}).get('publicAccess', '--------')
            users = sharing.get('object', {}).get('userAccesses', {})
            user_groups = sharing.get('object', {}).get('userGroupAccesses', {})
            
            # Check if public has data write access
            has_public_data_write = len(public_access) >= 4 and 'w' in public_access[2:4]
            
            # Count users with data write access
            users_with_data_write = 0
            for user_id, user_data in users.items():
                access = user_data.get('access', '--------')
                if len(access) >= 4 and 'w' in access[2:4]:
                    users_with_data_write += 1
            
            return {
                'category_option_id': category_option_id,
                'public_access': public_access,
                'has_public_data_write': has_public_data_write,
                'total_users_with_access': len(users),
                'users_with_data_write': users_with_data_write,
                'user_groups_with_access': len(user_groups),
                'full_sharing': sharing
            }
            
        except Exception as e:
            return {
                'category_option_id': category_option_id,
                'error': str(e)
            }

def example_usage():
    """Example usage of the DHIS2 data sharing client"""
    
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
    print("Initializing DHIS2 Data Sharing Client...")
    client = DHIS2DataSharingClient(
        base_url=base_url,
        username=username,
        password=password
    )
    print(f"Connected to: {base_url}\n")
    
    try:
        # Grant data write access to all category options for all users
        # This solves: "User does not have write access to category option combo"
        results = client.bulk_share_data_access_with_all_users(
            access_level=DataAccessLevel.DATA_READ_WRITE.value,
            public_access=DataAccessLevel.DATA_READ_WRITE.value
        )
        
        # Save detailed results to file
        output_file = 'data_sharing_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    example_usage()
