# Contract: Footer File Discovery

## Endpoint: GET /api/footer/files
**Type**: Backend HTTP API endpoint
**Method**: GET
**Path**: `/api/footer/files`

## Request Contract
```javascript
// GET request, no body parameters
// Query parameters: none
```

## Response Contract
```javascript
// Successful discovery response
{
  "status": "success",
  "files": [
    {
      "filename": "roadmap.md",
      "path": "backend/data/footer/roadmap.md", 
      "lastModified": "2025-09-25T10:30:00Z",
      "size": 2048,
      "isValid": true
    },
    {
      "filename": "changelog.md",
      "path": "backend/data/footer/changelog.md",
      "lastModified": "2025-09-25T09:15:00Z", 
      "size": 1536,
      "isValid": true
    }
  ],
  "excluded": [
    "_hidden.md",
    "_template.md"
  ],
  "errors": []
}
```

## Error Response Contract
```javascript
// Directory access error
{
  "status": "error",
  "message": "Footer directory not accessible",
  "code": "DIRECTORY_NOT_FOUND",
  "files": [],
  "excluded": [],
  "errors": [
    {
      "file": "backend/data/footer/",
      "error": "Directory does not exist or insufficient permissions"
    }
  ]
}
```

## Validation Rules
1. **File filtering**:
   - MUST include only files with .md extension
   - MUST exclude files starting with underscore (_)
   - MUST exclude hidden files and directories

2. **File information**:
   - MUST provide filename without path
   - MUST provide full relative path from project root
   - MUST provide lastModified timestamp
   - MUST provide file size in bytes
   - MUST indicate validity status

3. **Error handling**:
   - MUST continue processing if individual files are inaccessible
   - MUST report specific errors per file
   - MUST provide empty arrays for failed operations
   - MUST include error details for debugging

## Contract Tests
These tests MUST fail until implementation is complete:

### Test: Successful Discovery
```javascript
// Should discover valid markdown files
expect(discoverFooterFiles()).toMatchContract({
  status: "success",
  files: expect.arrayContaining([
    expect.objectContaining({
      filename: expect.stringMatching(/\.md$/),
      path: expect.stringContaining("backend/data/footer/"),
      lastModified: expect.any(String),
      size: expect.any(Number),
      isValid: expect.any(Boolean)
    })
  ])
});
```

### Test: Exclusion Filtering  
```javascript
// Should exclude underscore-prefixed files
const result = discoverFooterFiles();
expect(result.files).not.toContainEqual(
  expect.objectContaining({
    filename: expect.stringMatching(/^_.*\.md$/)
  })
);
expect(result.excluded).toContain("_hidden.md");
```

### Test: Directory Missing
```javascript
// Should handle missing directory gracefully
jest.mock('fs', () => ({
  readdirSync: jest.fn(() => { throw new Error('ENOENT') })
}));

expect(discoverFooterFiles()).toMatchContract({
  status: "error",
  code: "DIRECTORY_NOT_FOUND",
  files: [],
  errors: expect.arrayContaining([
    expect.objectContaining({
      error: expect.stringContaining("Directory does not exist")
    })
  ])
});
```