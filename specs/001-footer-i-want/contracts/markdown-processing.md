# Contract: Footer Content Retrieval

## Endpoint: GET /api/footer/content/{filename}
**Type**: Backend HTTP API endpoint  
**Method**: GET
**Path**: `/api/footer/content/{filename}`
**Input**: filename parameter (without .md extension)

## Request Contract
```javascript
// GET /api/footer/content/roadmap
// Path parameter: filename (string, no .md extension)
// Query parameters: none  
```

## Response Contract
```javascript
// Successful content response  
{
  "status": "success",
  "filename": "roadmap.md",
  "content": "# [Roadmap](https://example.com)\n\nThis is the roadmap content...",
  "title": "Roadmap",
  "isExternal": true,
  "externalUrl": "https://example.com",
  "lastModified": "2025-09-25T10:30:00Z",
  "size": 1024
}
```

## Alternative Response: Internal Page
```javascript
// Internal page without external link
{
  "status": "success", 
  "result": {
    "title": "About Us",
    "isExternal": false,
    "externalUrl": null,
    "renderedContent": "<h1>About Us</h1><p>Learn more about our company...</p>",
    "rawContent": "# About Us\n\nLearn more about our company...",
    "lastModified": "2025-09-25T10:30:00Z",
    "isValid": true
  },
  "warnings": []
}
```

## Alternative Response: No Heading Fallback
```javascript
// File without top-level heading
{
  "status": "success",
  "result": {
    "title": "roadmap", // filename without extension
    "isExternal": false,
    "externalUrl": null,
    "renderedContent": "<p>Content without heading...</p>",
    "rawContent": "Content without heading...",
    "lastModified": "2025-09-25T10:30:00Z", 
    "isValid": true
  },
  "warnings": [
    "No top-level heading found, using filename as title"
  ]
}
```

## Error Response Contract
```javascript
// Processing error
{
  "status": "error",
  "message": "Failed to process markdown content",
  "code": "MARKDOWN_PARSE_ERROR",
  "result": null,
  "warnings": [],
  "errors": [
    {
      "line": 5,
      "column": 12,
      "message": "Invalid markdown syntax"
    }
  ]
}
```

## Validation Rules
1. **Heading extraction**:
   - MUST detect top-level heading (# syntax)
   - MUST parse markdown link syntax `# [Title](URL)` 
   - MUST extract title text and URL separately
   - MUST fallback to filename if no heading found

2. **External URL detection**:
   - MUST identify http:// and https:// URLs only
   - MUST validate URL format before marking as external
   - MUST handle malformed URLs gracefully

3. **Content rendering**:
   - MUST convert markdown to HTML
   - MUST preserve original raw content
   - MUST handle empty or whitespace-only files

4. **Error handling**:
   - MUST continue processing despite minor syntax errors
   - MUST provide line/column information for errors
   - MUST distinguish between warnings and blocking errors

## Contract Tests
These tests MUST fail until implementation is complete:

### Test: External Link Processing
```javascript
const input = {
  content: "# [External Link](https://example.com)\n\nContent here.",
  filename: "external.md"
};

expect(processMarkdownContent(input)).toMatchContract({
  status: "success",
  result: expect.objectContaining({
    title: "External Link",
    isExternal: true,
    externalUrl: "https://example.com",
    renderedContent: expect.stringContaining("<h1>"),
    isValid: true
  })
});
```

### Test: Internal Page Processing
```javascript
const input = {
  content: "# Internal Page\n\nThis stays on our site.",
  filename: "internal.md"
};

expect(processMarkdownContent(input)).toMatchContract({
  status: "success",
  result: expect.objectContaining({
    title: "Internal Page",
    isExternal: false,
    externalUrl: null,
    isValid: true
  })
});
```

### Test: Filename Fallback
```javascript
const input = {
  content: "No heading here, just content.",
  filename: "no-heading.md"
};

expect(processMarkdownContent(input)).toMatchContract({
  status: "success",
  result: expect.objectContaining({
    title: "no-heading",
    isExternal: false,
    isValid: true
  }),
  warnings: expect.arrayContaining([
    expect.stringContaining("No top-level heading found")
  ])
});
```

### Test: Parse Error Handling
```javascript
const input = {
  content: "# Valid Heading\n\n[Broken link syntax(incomplete",
  filename: "broken.md"
};

expect(processMarkdownContent(input)).toMatchContract({
  status: "error", 
  code: "MARKDOWN_PARSE_ERROR",
  result: null,
  errors: expect.arrayContaining([
    expect.objectContaining({
      message: expect.stringContaining("markdown syntax")
    })
  ])
});
```