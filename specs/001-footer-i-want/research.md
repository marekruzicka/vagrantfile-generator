# Research: Configurable Footer

## Decision: Footer File Storage and Access Strategy
**Choice**: Backend HTTP API serving markdown files from `backend/data/footer/` directory
**Rationale**: 
- Leverages existing backend data structure (backend/data/)
- Uses standard HTTP API patterns consistent with existing VagrantAPI class
- Maintains frontend-backend separation with clear contracts
- Files served via FastAPI static routes, fetched via browser fetch API
- Consistent with existing project architecture and deployment patterns

**Alternatives Considered**:
- Filesystem bind-mounting: Rejected due to container complexity and frontend-backend boundary violation  
- Client-side file access: Rejected due to browser security constraints
- Mixed approach: Rejected to maintain architectural consistency

## Decision: Markdown Processing Approach  
**Choice**: Backend HTTP API endpoints for file discovery and content serving, frontend fetch for retrieval
**Rationale**:
- Extends existing VagrantAPI class patterns for HTTP communication
- Backend FastAPI serves markdown files as static routes
- Frontend uses standard fetch API for content retrieval
- Maintains clear frontend-backend separation with HTTP contracts
- Leverages existing backend/data/ directory structure

**Alternatives Considered**:
- Client-side markdown processing: Rejected due to file access limitations
- Pre-build markdown compilation: Rejected to maintain dynamic discovery feature
- Mixed approach: Rejected due to architectural inconsistency

## Decision: Footer Positioning Strategy
**Choice**: CSS-based responsive positioning with different behaviors per page type
**Rationale**:
- Main page: Positioned at bottom of viewport, always visible but responsive to avoid covering project cards
- Secondary pages: Normal document flow positioning at page bottom (scroll-to-view behavior)
- Responsive design ensures proper layout on all screen sizes
- Uses page context detection for conditional styling
- Maintains accessibility and mobile-first approach

**Alternatives Considered**:
- Fixed positioning on all pages: Rejected due to content interference on secondary pages
- JavaScript-based positioning: Rejected to maintain progressive enhancement
- Separate footer components: Rejected due to code duplication concerns

## Decision: External Link Detection
**Choice**: Parse markdown link syntax `# [Title](URL)` in heading extraction
**Rationale**:
- Clear, standard markdown syntax
- Easy to parse with regex or markdown parser
- Maintains consistency with markdown standards
- Explicit indication of external vs internal links

**Alternatives Considered**:
- URL pattern detection in plain text: Rejected due to ambiguity
- Special file naming conventions: Rejected due to user experience complexity
- Metadata headers: Rejected to keep files simple

## Decision: Error Handling for Corrupted Files
**Choice**: Graceful degradation with error page display
**Rationale**:
- Footer link still appears (user expectation management)
- Error page shows when clicked (clear user feedback)
- No blocking of other footer functionality
- Maintains system reliability and user experience

**Alternatives Considered**:
- Skip corrupted files entirely: Rejected due to poor user feedback
- System-wide error blocking: Rejected due to excessive failure scope
- Raw content display: Rejected due to potential security and UX issues

## Decision: Backend Integration Strategy
**Choice**: Extend existing FastAPI backend with static routes for footer files
**Rationale**:
- Consistent with existing backend/data/ directory structure (projects/, boxes/)
- Uses FastAPI static file serving capabilities
- Maintains existing VagrantAPI class patterns for frontend communication  
- Backend/data/footer/ directory aligns with established data organization
- No changes to existing container configuration needed

**Alternatives Considered**:
- Container bind-mounting: Rejected due to architectural complexity
- Separate file service: Rejected due to overengineering for simple file serving
- Frontend-only approach: Rejected due to browser file access limitations