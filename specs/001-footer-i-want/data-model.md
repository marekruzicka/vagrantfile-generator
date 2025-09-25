# Data Model: Configurable Footer

## Entity Overview
This feature primarily deals with file-based entities and configuration structures rather than persistent data models.

## Core Entities

### FooterConfiguration
**Purpose**: Represents the configuration for footer text content
**Source**: `footer.md` file in backend/data/footer/ directory, served via HTTP API
**Fields**:
- `content`: String - Raw markdown content for footer text
- `renderedContent`: String - Processed HTML content for display
- `lastModified`: Date - File modification timestamp for cache invalidation
- `isValid`: Boolean - Whether content parsed successfully

**Validation Rules**:
- Content can be empty (fallback to default copyright)
- Must be valid markdown format
- File size limited to 10KB for performance

**State Transitions**:
- `Loading` → `Valid` (successful parse)
- `Loading` → `Invalid` (parse failure, use default)
- `Valid` → `Stale` (file modification detected)

### StaticPage
**Purpose**: Represents a static informational page linked from footer
**Source**: `.md` files in backend/data/footer/ directory served via HTTP API (excluding underscore-prefixed)
**Fields**:
- `filename`: String - Original filename without extension
- `title`: String - Extracted from top-level heading or filename fallback
- `content`: String - Full markdown content
- `renderedContent`: String - Processed HTML for display
- `isExternal`: Boolean - Whether heading contains external URL
- `externalUrl`: String - Extracted URL if isExternal=true
- `lastModified`: Date - File modification timestamp
- `isValid`: Boolean - Whether content parsed successfully

**Validation Rules**:
- Filename must not start with underscore
- Must have .md extension
- File size limited to 100KB per page
- External URL must be valid HTTP/HTTPS if present

**State Transitions**:
- `Discovered` → `Loading` (file read initiated)
- `Loading` → `Valid` (successful parse)
- `Loading` → `Invalid` (parse failure, show error page)
- `Valid` → `Stale` (file modification detected)

### FooterNavigationLink
**Purpose**: Represents a navigation link in the footer
**Source**: Derived from StaticPage entities
**Fields**:
- `text`: String - Display text for the link
- `href`: String - Target URL (internal page or external)
- `isExternal`: Boolean - Whether link opens externally
- `order`: Number - Display order in footer (alphabetical by default)
- `pageId`: String - Reference to source StaticPage filename

**Validation Rules**:
- Text must not be empty (use filename if heading missing)
- href must be valid URL format
- Internal links must reference valid pages

**Relationships**:
- FooterNavigationLink → StaticPage (many-to-one)
- StaticPage → FooterNavigationLink (one-to-one)

## File System Structure

```
backend/data/footer/
├── footer.md              # Footer configuration (text content)
├── roadmap.md             # Static page example
├── changelog.md           # Static page example
├── about.md              # Static page example
├── _hidden.md            # Ignored (underscore prefix)
└── _templates/           # Ignored directory
```

## Data Flow

1. **Initialization**:
   - Frontend requests footer file list from backend HTTP API
   - Backend scans backend/data/footer/ directory for .md files
   - Filter out underscore-prefixed files
   - Return file list to frontend for StaticPage entity creation

2. **Content Processing**:
   - Frontend fetches markdown content from backend HTTP API endpoints
   - Parse markdown files to extract headings and content
   - Detect external URLs in heading syntax
   - Generate FooterNavigationLink entities

3. **Rendering**:
   - Sort navigation links alphabetically
   - Render footer HTML with links and text content
   - Apply appropriate positioning CSS based on page context

4. **Update Handling**:
   - Monitor file modification timestamps
   - Invalidate and refresh stale content
   - Maintain user experience during updates

## Error Handling

### Missing Footer Configuration
- **Trigger**: footer.md file missing or empty
- **Response**: Use default copyright text
- **Fallback**: "© 2025 Vagrantfile Generator."

### Invalid Static Page
- **Trigger**: Corrupted or unparseable markdown file
- **Response**: Create footer link, show error page when clicked
- **Error Page Content**: "This page is temporarily unavailable"

### External URL Validation
- **Trigger**: Invalid URL in heading markdown link
- **Response**: Treat as internal link, show error if page missing
- **Logging**: Warning logged for invalid external URL format

## Performance Considerations

- **Caching**: Cache parsed content with file modification timestamps
- **Lazy Loading**: Load page content only when navigated to
- **Size Limits**: 10KB for footer.md, 100KB per static page
- **Update Frequency**: Check for file changes on page load (not real-time)