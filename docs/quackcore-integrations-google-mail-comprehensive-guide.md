# QuackCore Google Mail Integration Documentation

The **quackcore.integrations.google.mail** module enables your QuackTools to interact with Gmail. It abstracts the complexity of Google OAuth2 authentication, email listing, downloading messages (including handling attachments), and error management. This guide explains the module’s architecture, configuration options, common usage patterns with detailed code examples, and troubleshooting advice.

---

## Table of Contents

- [Overview](#overview)
- [Architecture Overview](#architecture-overview)
- [Authentication and Credentials](#authentication-and-credentials)
- [Configuration Options](#configuration-options)
- [Usage Examples](#usage-examples)
  - [Initializing the Service](#initializing-the-service)
  - [Listing Emails](#listing-emails)
  - [Downloading an Email](#downloading-an-email)
- [Error Handling and Troubleshooting](#error-handling-and-troubleshooting)
- [Advanced Topics](#advanced-topics)
- [Conclusion](#conclusion)

---

## Overview

The Google Mail integration module is a key component of QuackCore that allows QuackTools (plugins in the QuackVerse ecosystem) to perform operations such as:

- **Authentication:** Establishing a secure connection with Gmail through OAuth 2.0.
- **Email Operations:** Listing emails based on a query, downloading email messages (and their attachments), and processing email content.
- **Error Management:** Consistent error handling with clear logging and retry mechanisms.

The module is organized into multiple sub-components such as service management, configuration, API protocols, utility functions, and operations for specific tasks (e.g., handling attachments).

---

## Architecture Overview

The module is split into several key files and packages:

- **`service.py`:**  
  Contains the `GoogleMailService` class responsible for overall integration logic. It loads configurations, manages authentication, and offers methods like `list_emails()` and `download_email()`.

- **`config.py`:**  
  Uses Pydantic models (specifically the `GmailServiceConfig`) to define and validate configuration settings. This ensures you have the required parameters, such as `storage_path` and `oauth_scope`, correctly set.

- **`protocols.py`:**  
  Defines protocols (interfaces) such as `GmailService`, `GoogleCredentials`, `GmailRequest`, and others. These help enforce type safety and ensure consistent implementation across the module.

- **`operations/`:**  
  Contains submodules that implement Gmail operations:
  - **`auth.py`:** Handles authentication and initializes the Gmail API service using the Google API client.
  - **`email.py`:** Implements functions for listing and downloading emails. It also includes helper functions to extract email headers, decode content, and process attachments.
  - **`attachments.py`:** Provides functionality for handling attachments, including filename cleaning, file path resolution, and binary file writing.

- **`utils/api.py`:**  
  Provides utility functions such as `execute_api_request` and a decorator `with_exponential_backoff` to perform API calls with retry logic and error handling.

Each of these components collaborates to provide a consistent interface for interacting with Gmail through your QuackTool.

---

## Authentication and Credentials

Authentication is central to the module. Here’s how it works:

1. **OAuth2 Client Secrets and Credentials Files:**  
   - You must have a **client secrets file** (JSON) obtained from the [Google Developer Console](https://console.developers.google.com/).
   - The **credentials file** stores the OAuth tokens (access token, refresh token, token URI, client ID, and client secret).

2. **GoogleAuthProvider:**  
   - In `service.py`, the `GoogleMailService.initialize()` method instantiates a `GoogleAuthProvider` using the paths to your client secrets and credentials files.
   - This provider calls `get_credentials()` to retrieve the current tokens. If the access token has expired, it will use the refresh token to obtain a new one.

3. **Initializing the Gmail API Service:**  
   - Using the credentials, the module calls `auth.initialize_gmail_service()`, which internally uses the `googleapiclient.discovery.build` function. This creates the `GmailService` object that you use to perform subsequent API operations.
   - **Tip for Junior Developers:** If you’re new to OAuth2, make sure you follow the [Google OAuth2 guide](https://developers.google.com/identity/protocols/oauth2) to correctly set up your project and understand the scopes you need (by default, this module uses `https://www.googleapis.com/auth/gmail.readonly`).

---

## Configuration Options

The library supports flexible configuration. Whether you supply parameters directly or load them from a file, here is what you need to know:

- **`client_secrets_file` (str):**  
  Path to your client secrets JSON file.

- **`credentials_file` (str):**  
  Path to the file storing your OAuth2 tokens.

- **`storage_path` (str):**  
  Directory where downloaded emails and attachments are stored.  
  > **Note:** If not provided explicitly, the configuration loaded by `GoogleMailService` must include this parameter.

- **`oauth_scope` (list[str]):**  
  Specifies the Gmail API scopes. The default is `["https://www.googleapis.com/auth/gmail.readonly"]`.

- **`max_retries` (int), `initial_delay` (float), `max_delay` (float):**  
  Used for configuring exponential backoff when the Gmail API returns errors. These settings help in handling rate-limiting or transient API issues.

- **`include_subject` and `include_sender` (bool):**  
  Flags to indicate whether the email subject and sender information should be included in the downloaded HTML file.

The configuration is validated using a Pydantic model in `config.py` (specifically, `GmailServiceConfig`), ensuring that each field is present and properly typed.

---

## Usage Examples

Below are detailed code snippets to help you quickly start using the Google Mail integration.

### Initializing the Service

Create an integration instance either via the factory method or by directly instantiating the service:

```python
from quackcore.integrations.google.mail import create_integration

# Option 1: Using the factory function (default configuration)
google_mail_service = create_integration()

# Option 2: Custom configuration by specifying necessary parameters
google_mail_service = google_mail_service.__class__(
    client_secrets_file="/path/to/client_secrets.json",
    credentials_file="/path/to/credentials.json",
    storage_path="/path/to/storage/directory",
    oauth_scope=["https://www.googleapis.com/auth/gmail.readonly"],
    include_subject=True,
    include_sender=True,
    max_retries=5,
    initial_delay=1.0,
    max_delay=30.0,
    log_level=20,  # logging.INFO level
)

# Initialize the service
init_result = google_mail_service.initialize()
if not init_result.success:
    print("Initialization failed:", init_result.message)
    exit(1)
print(init_result.message)
```

### Listing Emails

To list emails based on a search query (or the default query built from configuration):

```python
# Example: Listing emails that might be from a specific sender
search_query = "from:example@example.com"
list_result = google_mail_service.list_emails(query=search_query)

if list_result.success:
    emails = list_result.content
    print("Found {} emails:".format(len(emails)))
    for email_summary in emails:
        print(email_summary)
else:
    print("Error listing emails:", list_result.message)
```

### Downloading an Email

Download a specific email by its Gmail message ID. This example also shows how the email's subject and sender can be included in the final HTML file.

```python
# Replace with a valid Gmail message ID from your listed emails
msg_id = "YOUR_MESSAGE_ID_HERE"
download_result = google_mail_service.download_email(msg_id)

if download_result.success:
    print("Email downloaded successfully to:", download_result.content)
else:
    print("Error downloading email:", download_result.message)
```

---

## Error Handling and Troubleshooting

### Error Handling Mechanism

- **IntegrationResult:**  
  Most operations return an `IntegrationResult` object that contains:
  - `success`: Boolean flag indicating if the operation succeeded.
  - `content`: The successful output (e.g., a list of emails or file path).
  - `message`: Additional information, especially on failure.

- **Logging:**  
  The module makes use of the Python `logging` module. Adjusting `log_level` helps to see more granular information during development or debugging.

- **API Retry Logic:**  
  - API calls (e.g., listing messages, fetching message details, or downloading attachments) use functions from `utils/api.py` to implement exponential backoff.
  - In case of HTTP errors (like rate limits or transient server issues), the library automatically retries the call up to `max_retries`.

### Common Issues

1. **Authentication Issues:**  
   - **Symptom:** The service fails during initialization with an error about credentials.
   - **Solution:**  
     - Double-check that `client_secrets_file` and `credentials_file` paths are correct.
     - Confirm that your Google project is properly set up and that the OAuth2 client configuration includes the proper redirect URIs.
     - Review the [Google OAuth2 documentation](https://developers.google.com/identity/protocols/oauth2) for setup guidance.

2. **File System Errors:**  
   - **Symptom:** Errors during email download or attachment saving (e.g., "Failed to create directory").
   - **Solution:**  
     - Verify that the `storage_path` exists or that your application has permission to create directories and write files.
     - Check the filesystem logs for more detailed errors and adjust folder permissions if necessary.

3. **API Rate Limits and Quota:**  
   - **Symptom:** API calls fail with errors like 429 (Too Many Requests).
   - **Solution:**  
     - Adjust the `max_retries`, `initial_delay`, and `max_delay` parameters to better handle transient errors.
     - Monitor your API quota in the Google Cloud Console.

4. **Attachment Processing Errors:**  
   - **Symptom:** Errors during decoding or saving of attachments.
   - **Solution:**  
     - Ensure that the attachments are properly base64-encoded.
     - Review error logs for decoding errors and verify that your storage path has sufficient space and correct permissions.

---

## Advanced Topics

### Exponential Backoff
The utility function `with_exponential_backoff` wraps API calls to automatically retry failed requests under specific HTTP error conditions (e.g., 429, 500, 503). If you need to adjust or extend this functionality, review the implementation in `utils/api.py`.

### Customizing Logging
The module uses the standard Python logging module. You can set the logging level via the `log_level` parameter when initializing the `GoogleMailService` to see more detailed debug information during development.

### Extending the Integration
While the current module supports essential operations, you can extend it by:
- Adding new methods for different Gmail API endpoints.
- Implementing custom handlers for non-standard email formats.
- Creating subclasses of `GoogleMailService` to encapsulate additional business logic needed in your QuackTools.

---

## Conclusion

Happy coding with your QuackTools in the QuackVerse!

---