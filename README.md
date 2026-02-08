# DHIS2 Sharing Management Tools

Python client libraries for managing DHIS2 metadata and data sharing permissions. These tools allow you to programmatically control who can access different metadata objects and data in a DHIS2 instance.

## Tools Available

### 1. `share.py` - Metadata Sharing
Manages **metadata access** permissions (who can view/edit metadata definitions).

### 2. `share_data_access.py` - Data Sharing ⭐ **NEW**
Manages **data access** permissions (who can view/write actual data values).

**Use this to solve the error:** `"User does not have write access to category option combo"`

## Features

- **Bulk Sharing Operations**: Share all category options with all users in one operation
- **Flexible Access Control**: Support for different permission levels (metadata vs data access)
- **Comprehensive API Integration**: Full integration with DHIS2's sharing API
- **Error Handling**: Robust error handling with detailed reporting
- **Progress Tracking**: Real-time progress updates during bulk operations
- **Environment Variable Support**: Secure credential management using .env files

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the `.env` file and update it with your DHIS2 credentials:

```bash
# DHIS2 Configuration
DHIS2_BASE_URL=https://your-dhis2-instance.com/
DHIS2_USERNAME=your_username
DHIS2_PASSWORD=your_password
```

2. Make sure the `.env` file is in the same directory as `share.py`

## Usage

### Solving "User does not have write access to category option" Error

This error occurs when users don't have **data write permissions** on category options. Use the `share_data_access.py` script:

```bash
python share_data_access.py
```

This will:
- Grant **data write access** (`--rw----`) to all users for all category options
- Show real-time progress for each category option
- Save detailed results to `data_sharing_results.json`

### Basic Metadata Sharing

To share metadata access (for viewing/editing category option definitions):

```bash
python share.py
```

### Programmatic Usage

#### Data Access Sharing (Recommended for Data Entry Issues)

```python
from share_data_access import DHIS2DataSharingClient, DataAccessLevel, UserAccess
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client
client = DHIS2DataSharingClient(
    base_url=os.getenv('DHIS2_BASE_URL'),
    username=os.getenv('DHIS2_USERNAME'),
    password=os.getenv('DHIS2_PASSWORD')
)

# Grant data write access to all category options for all users
results = client.bulk_share_data_access_with_all_users(
    access_level=DataAccessLevel.DATA_READ_WRITE.value
)

# Process results
for result in results:
    if result['status'] == 'success':
        print(f"✓ {result['name']} - Data access granted to {result['users_shared_with']} users")
    else:
        print(f"✗ {result['name']} - Error: {result['error']}")
```

#### Metadata Access Sharing

```python
from share import DHIS2SharingClient, AccessLevel, UserAccess
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client
client = DHIS2SharingClient(
    base_url=os.getenv('DHIS2_BASE_URL'),
    username=os.getenv('DHIS2_USERNAME'),
    password=os.getenv('DHIS2_PASSWORD')
)

# Share all category options with all users (READ access)
results = client.share_all_category_options_with_all_users(AccessLevel.READ.value)

# Process results
for result in results:
    if result['status'] == 'success':
        print(f"✓ {result['name']} - Shared with {result['users_shared_with']} users")
    else:
        print(f"✗ {result['name']} - Error: {result['error']}")
```

### Advanced Usage

#### Share specific category options with specific users:

```python
# Get users and category options
users = client.get_users()
category_options = client.get_category_options()

# Create user access list
user_access_list = [
    UserAccess(
        id=users[0]['id'],
        access=AccessLevel.READ_WRITE.value,
        displayName=users[0]['displayName']
    )
]

# Share specific category option
result = client.share_category_option(
    category_options[0]['id'],
    users=user_access_list,
    public_access=AccessLevel.READ.value
)
```

#### Get current sharing settings:

```python
sharing_settings = client.get_sharing_settings('categoryOptions', 'category_option_id')
print(json.dumps(sharing_settings, indent=2))
```

## Access Levels

### Understanding DHIS2 Access String Format

DHIS2 uses an 8-character access string: `[metadata][data]`
- **First 4 characters**: Metadata access (r/w/d/-)
- **Last 4 characters**: Data access (r/w/-)

### Metadata Access Levels (share.py)

- `AccessLevel.NO_ACCESS`: `"--------"` - No access
- `AccessLevel.READ`: `"r-------"` - Read only (view metadata)
- `AccessLevel.READ_WRITE`: `"rw------"` - Read and write metadata
- `AccessLevel.READ_WRITE_DELETE`: `"rwd-----"` - Read, write, and delete metadata

### Data Access Levels (share_data_access.py)

- `DataAccessLevel.NO_ACCESS`: `"--------"` - No access
- `DataAccessLevel.DATA_READ_ONLY`: `"--r-----"` - Data read only
- `DataAccessLevel.DATA_READ_WRITE`: `"--rw----"` - Data read-write ⭐ **Recommended**
- `DataAccessLevel.METADATA_READ_DATA_READ`: `"r-r-----"` - Metadata read + Data read
- `DataAccessLevel.METADATA_READ_DATA_READWRITE`: `"r-rw----"` - Metadata read + Data read-write
- `DataAccessLevel.FULL_ACCESS`: `"rwrw----"` - Full metadata and data access

## API Methods

### Data Sharing Client (DHIS2DataSharingClient)

#### Core Methods

- `bulk_share_data_access_with_all_users(access_level, public_access)` - Grant data access to all category options ⭐
- `share_category_option_data_access(category_option_id, users, user_groups, public_access)` - Share data access for specific category option
- `diagnose_category_option(category_option_id)` - Diagnose data access issues
- `get_sharing_settings(metadata_type, metadata_id)` - Get current sharing settings
- `update_sharing_settings(metadata_type, metadata_id, sharing_data)` - Update sharing settings

#### Helper Methods

- `get_users(fields)` - Get list of users
- `get_user_groups(fields)` - Get list of user groups  
- `get_category_options(fields)` - Get list of category options

### Metadata Sharing Client (DHIS2SharingClient)

#### Core Methods

- `get_sharing_settings(metadata_type, metadata_id)` - Get current sharing settings
- `update_sharing_settings(metadata_type, metadata_id, sharing_settings)` - Update sharing settings
- `share_category_option(category_option_id, users, user_groups, public_access)` - Share a category option
- `share_multiple_category_options(category_option_ids, users, user_groups, public_access)` - Share multiple category options
- `share_all_category_options_with_all_users(access_level)` - Share all category options with all users

#### Helper Methods

- `get_users(fields)` - Get list of users
- `get_user_groups(fields)` - Get list of user groups  
- `get_category_options(fields)` - Get list of category options
- `find_user_by_username(username)` - Find user by username
- `find_user_group_by_name(name)` - Find user group by name

## Security

- **Environment Variables**: Credentials are stored in `.env` file (not committed to version control)
- **HTTPS**: All API communications use HTTPS
- **Authentication**: Uses HTTP Basic Authentication with DHIS2

## Error Handling

The tool includes comprehensive error handling:

- Network connectivity issues
- Authentication failures
- API response errors
- Invalid metadata IDs
- Missing environment variables

## Requirements

- Python 3.7+
- `requests` library for HTTP operations
- `python-dotenv` for environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check with your organization's policies before using in production environments.

## Troubleshooting

### "User does not have write access to category option combo"

**Error Message:**
```
User does not have write access to category option combo: jSb0qiyf0Gi
[User has no data write access for CategoryOption: gt6o47euUrA]
```

**Solution:**
1. Run `python share_data_access.py`
2. This grants data write access to all category options for all users
3. Results are saved to `data_sharing_results.json`

### Difference Between Metadata and Data Sharing

- **Metadata Sharing** (`share.py`): Controls who can view/edit category option *definitions*
- **Data Sharing** (`share_data_access.py`): Controls who can enter/edit *data values* associated with category options

**Most data entry errors require data sharing, not metadata sharing!**

## Support

For issues related to DHIS2 API, consult the [DHIS2 Developer Documentation](https://docs.dhis2.org/en/develop/using-the-api/dhis-core-version-master/sharing.html).
