# DHIS2 Sharing Management Tool

A Python client library for managing DHIS2 metadata sharing permissions. This tool allows you to programmatically control who can access different metadata objects (like category options, data elements, etc.) in a DHIS2 instance.

## Features

- **Bulk Sharing Operations**: Share all category options with all users in one operation
- **Flexible Access Control**: Support for different permission levels (read, read-write, read-write-delete)
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

### Basic Usage

Run the example script to share all category options with all users:

```bash
python share.py
```

### Programmatic Usage

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

The tool supports DHIS2's standard access levels:

- `AccessLevel.NO_ACCESS`: `"--------"` - No access
- `AccessLevel.READ`: `"r-------"` - Read only
- `AccessLevel.READ_WRITE`: `"rw------"` - Read and write
- `AccessLevel.READ_WRITE_DELETE`: `"rwd-----"` - Read, write, and delete

## API Methods

### Core Methods

- `get_sharing_settings(metadata_type, metadata_id)` - Get current sharing settings
- `update_sharing_settings(metadata_type, metadata_id, sharing_settings)` - Update sharing settings
- `share_category_option(category_option_id, users, user_groups, public_access)` - Share a category option
- `share_multiple_category_options(category_option_ids, users, user_groups, public_access)` - Share multiple category options
- `share_all_category_options_with_all_users(access_level)` - Share all category options with all users

### Helper Methods

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

## Support

For issues related to DHIS2 API, consult the [DHIS2 Developer Documentation](https://docs.dhis2.org/en/develop/using-the-api/dhis-core-version-master/sharing.html).
