# Quickstart: Configurable Footer Testing

## Setup Instructions

1. **Create footer directory structure**:
   ```bash
   mkdir -p frontend/src/footer
   cd frontend/src/footer
   ```

2. **Create test footer configuration**:
   ```bash
   echo "© 2025 Vagrantfile Generator. Built with ❤️ for developers." > footer.md
   ```

3. **Create sample static pages**:
   ```bash
   # Internal page example
   cat > roadmap.md << EOF
   # Roadmap
   
   ## Upcoming Features
   - Advanced networking configuration
   - Plugin system integration
   - Multi-provider support
   EOF
   
   # External link example  
   cat > github.md << EOF
   # [GitHub Repository](https://github.com/marekruzicka/vagrantfile-generator)
   
   Visit our GitHub repository for source code, issues, and contributions.
   EOF
   
   # Page without heading (filename fallback test)
   cat > support.md << EOF
   For technical support, please contact our team or visit the documentation.
   
   We're here to help with any questions about Vagrant configuration.
   EOF
   
   # Hidden file (should be ignored)
   echo "# Hidden Content" > _hidden.md
   ```

## Test Scenarios

### Scenario 1: Basic Footer Display
**Objective**: Verify footer appears on main page and secondary pages with correct positioning

**Steps**:
1. Navigate to main application page (http://localhost:5173)
2. Observe footer at bottom of viewport (no scrolling required)
3. Verify footer contains:
   - Navigation links: "Roadmap", "GitHub Repository", "support"
   - Footer text: "© 2025 Vagrantfile Generator. Built with ❤️ for developers."
4. Navigate to Project Detail page
5. Scroll to bottom of page
6. Verify footer appears at document bottom (scrolling required)

**Expected Results**:
- ✅ Footer visible on main page without scrolling
- ✅ Footer at document bottom on secondary pages  
- ✅ Footer contains exactly 3 navigation links
- ✅ Footer text displays below navigation links
- ✅ "_hidden.md" content not visible in footer

### Scenario 2: Internal Page Navigation
**Objective**: Verify navigation to internal static pages works correctly

**Steps**:
1. From main page, click "Roadmap" link in footer
2. Verify page displays roadmap content with consistent styling
3. Verify URL shows internal page route
4. Verify page has proper heading "Roadmap"
5. Verify footer remains visible at bottom after scrolling
6. Navigate back to main page
7. Repeat test with "support" link

**Expected Results**:
- ✅ Roadmap page displays with correct heading
- ✅ Content matches roadmap.md file content
- ✅ Page styling consistent with main application
- ✅ Footer remains functional on static pages
- ✅ Support page uses filename as title (no heading in file)

### Scenario 3: External Link Handling  
**Objective**: Verify external links open correctly without breaking navigation

**Steps**:
1. From main page, click "GitHub Repository" link in footer
2. Verify link opens in new tab/window (external link behavior)
3. Verify destination is correct GitHub URL
4. Return to main page
5. Verify main page remains functional

**Expected Results**:
- ✅ External link opens in new tab/window
- ✅ Correct GitHub URL is accessed
- ✅ Main application remains unaffected
- ✅ Footer continues to function normally

### Scenario 4: Error Handling
**Objective**: Verify graceful handling of corrupted or missing content

**Steps**:
1. Create corrupted markdown file:
   ```bash
   echo "# Broken [Link(incomplete markdown" > frontend/src/footer/broken.md
   ```
2. Refresh application
3. Verify "broken" link appears in footer
4. Click "broken" link
5. Verify error page displays instead of corrupted content
6. Navigate back to main page
7. Remove footer.md file:
   ```bash
   rm frontend/src/footer/footer.md
   ```
8. Refresh application
9. Verify footer still displays with default copyright text

**Expected Results**:
- ✅ Corrupted file creates footer link
- ✅ Error page displays when corrupted link clicked
- ✅ Error page has consistent styling  
- ✅ Default copyright text appears when footer.md missing
- ✅ Other footer links remain functional

### Scenario 5: Dynamic Content Updates
**Objective**: Verify footer updates when files are modified

**Steps**:
1. Add new static page:
   ```bash
   echo "# Changelog\n\n## Version 1.0\n- Initial release" > frontend/src/footer/changelog.md
   ```
2. Refresh application
3. Verify "Changelog" link appears in footer
4. Click link to verify content displays correctly
5. Modify existing page:
   ```bash
   echo "# Updated Roadmap\n\n## New Timeline\n- Q1 2025: Major updates" > frontend/src/footer/roadmap.md
   ```
6. Navigate to roadmap page
7. Verify updated content displays

**Expected Results**:
- ✅ New changelog link appears after file creation
- ✅ Changelog content displays correctly when clicked
- ✅ Modified roadmap content updates on page navigation
- ✅ Footer automatically includes new files

## Performance Validation

### Load Time Testing
**Objective**: Verify footer loads within performance constraints

**Steps**:
1. Open browser developer tools (Network tab)
2. Navigate to main page
3. Measure footer rendering time
4. Navigate to static pages
5. Measure page load times

**Success Criteria**:
- ✅ Footer renders in <100ms
- ✅ Page navigation completes in <50ms  
- ✅ No network timeouts or errors
- ✅ Responsive behavior on mobile devices

## Cleanup
```bash
# Remove test files after validation
rm -rf frontend/src/footer/
```

## Troubleshooting

### Footer Not Appearing
- Check footer directory exists: `frontend/src/footer/`
- Verify at least one .md file exists (not starting with underscore)
- Check browser console for JavaScript errors
- Verify container bind-mounting includes footer directory

### Links Not Working
- Verify markdown files have valid syntax
- Check file permissions are readable
- Confirm external URLs use valid http/https format
- Verify internal routing handles static page URLs

### Styling Issues
- Check Tailwind CSS classes are loading correctly
- Verify responsive breakpoints work across devices
- Confirm footer positioning CSS is applied
- Test with different viewport sizes

## Success Definition
All test scenarios pass with:
- Zero JavaScript errors in console
- Consistent visual styling across pages
- Proper responsive behavior
- Graceful error handling for edge cases
- Performance within specified constraints