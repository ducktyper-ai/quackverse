# QuackCore Error Code Reference

This document defines the blessed error code taxonomy for QuackCore capabilities.

All machine-readable error codes and skip codes must follow the format: `QC_<AREA>_<DETAIL>`

## Blessed Error Areas

### QC_CFG_* - Configuration Errors

Configuration-related failures.

Examples:
- `QC_CFG_MISSING` - Required configuration parameter missing
- `QC_CFG_INVALID` - Configuration value is invalid
- `QC_CFG_PARSE_ERROR` - Failed to parse configuration file

### QC_IO_* - I/O Operations

File and data I/O failures.

Examples:
- `QC_IO_NOT_FOUND` - File or resource not found
- `QC_IO_READ_ERROR` - Failed to read file
- `QC_IO_WRITE_ERROR` - Failed to write file
- `QC_IO_DECODE_ERROR` - Failed to decode media/data format

### QC_NET_* - Network Operations

Network and connectivity failures.

Examples:
- `QC_NET_TIMEOUT` - Network request timed out
- `QC_NET_UNAVAILABLE` - Service or endpoint unavailable
- `QC_NET_DNS_ERROR` - DNS resolution failed

### QC_VAL_* - Validation Failures

Input validation and policy decisions (often used for skips).

Examples:
- `QC_VAL_INVALID` - Generic validation failure
- `QC_VAL_TOO_SHORT` - Input below minimum threshold
- `QC_VAL_TOO_LONG` - Input exceeds maximum threshold
- `QC_VAL_UNSUPPORTED` - Unsupported format or provider
- `QC_VAL_UNSUPPORTED_PROVIDER` - Unsupported service provider

### QC_AUTH_* - Authentication/Authorization

Security and permissions failures.

Examples:
- `QC_AUTH_INVALID` - Invalid credentials
- `QC_AUTH_EXPIRED` - Credentials or token expired
- `QC_AUTH_FORBIDDEN` - Insufficient permissions

### QC_RATE_* - Rate Limiting

Rate limit and quota failures.

Examples:
- `QC_RATE_EXCEEDED` - Request rate limit exceeded
- `QC_RATE_QUOTA_EXCEEDED` - Usage quota exceeded

### QC_TOOL_* - Tool-Internal Errors

Errors internal to the tool implementation.

Examples:
- `QC_TOOL_CRASH` - Tool crashed unexpectedly
- `QC_TOOL_TIMEOUT` - Tool execution timed out
- `QC_TOOL_INVALID_STATE` - Tool in invalid state

### QC_INT_* - Integration-Specific Errors

Errors specific to external integrations.

Examples:
- `QC_INT_SALESFORCE_ERROR` - Salesforce API error
- `QC_INT_DRIVE_ERROR` - Google Drive API error
- `QC_INT_S3_ERROR` - AWS S3 error

## Usage Guidelines

1. **Always use QC_ prefix** - All machine codes must start with `QC_`
2. **Choose appropriate area** - Pick the most specific blessed area
3. **Be specific with detail** - Make the detail portion descriptive
4. **Document new codes** - Add new codes to this registry when defining them
5. **Reuse existing codes** - Prefer existing codes over creating new ones

## Examples in Code
```python
# Skip due to validation policy
result = CapabilityResult.skip(
    reason="Video duration under 10 seconds",
    code="QC_VAL_TOO_SHORT"
)

# Error due to missing file
result = CapabilityResult.fail(
    msg="Video file not found",
    code="QC_IO_NOT_FOUND",
    metadata={"path": "/data/video.mp4"}
)

# Error due to network timeout
result = CapabilityResult.fail(
    msg="API request timed out after 30 seconds",
    code="QC_NET_TIMEOUT",
    metadata={"timeout_sec": 30}
)
```

## Adding New Areas

If you need a new error area that doesn't fit the blessed taxonomy:

1. Propose it in a design review
2. Document the use case
3. Add it to this registry
4. Update `common/enums.py` documentation