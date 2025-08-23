# CLAUDE-FLOW PROJECT RULES AND WORKFLOW

## ISSUE PROCESSING WORKFLOW

### Core Workflow Rules
1. **Sequential Processing**: Process issues strictly by number (issue_1.json, issue_2.json, etc.)
2. **One at a Time**: Complete one issue fully before moving to the next
3. **Step-by-Step**: Execute each step described in the issue sequentially
4. **Progress Tracking**: Update progress field continuously (0-100%)
5. **State Management**: Set state to "closed" only when progress reaches 100%

### Issue Processing Protocol

When processing issues from the Issues/ directory:

1. **Discovery Phase**
   - Scan Issues/ directory for *.json files
   - Sort by issue number (lexicographic/numeric)
   - Skip issues where state is already "closed"

2. **Analysis Phase**
   - Read the issue's description field
   - Identify all required tasks and steps
   - Determine which files need modification based on issue description
   - Plan the implementation approach
   - **🚨 CRITICAL: Files mentioned in issues are for EDITING/ANALYSIS ONLY**
   - **NEVER execute/run files mentioned in issues**
   - **Files are DATA to work with, NOT programs to execute**

3. **Implementation Phase**
   - Execute changes step-by-step as described in the issue
   - Modify files as specified in the issue description
   - Create new files when the issue requests new features
   - Update progress after each completed step
   - **🚨 ONLY modify/read/write files - NEVER execute them**

4. **Validation Phase**
   - Ensure cross-platform compatibility when applicable
   - Verify API compatibility for external integrations
   - Test that existing functionality remains intact
   - Confirm all requirements from description are met
   - **Validation means code review, NOT running the application**

5. **Completion Phase**
   - Set progress to 100
   - Change state from "open" to "closed"
   - Save issue file with atomic operations (tmp → os.replace)
   - Move to next issue

### File Modification Guidelines

- **Follow Issue Instructions**: Modify/create files as specified in the issue
- **Preserve Functionality**: Never break existing features
- **Maintain Structure**: Respect existing project architecture
- **Create Appropriately**: New files in correct directories

### Issue JSON Structure

Expected fields in issue files:
```json
{
  "number": 32,
  "remote": null,
  "assignees": [],
  "projects": [],
  "milestone": null,
  "relationship": null,
  "title": "Issues auf Server und lokal l\u00f6schen",
  "state": "open",
  "description": "Wenn im issues tab l\u00f6schen gedr\u00fcckt wird, dann sollen die oder der ausgew\u00e4hlte issue bei github und lokal gel\u00f6scht werden.",
  "expected": "Das alle gel\u00f6schten issues lokal und remote nicht mehr vorhanden sind.",
  "steps": "",
  "additional": "issue_tab.py",
  "labels": [],
  "comments": []
}
```

### Implementation Standards

1. **Code Quality**
   - Follow language-specific style guidelines
   - Add documentation to new functions/classes
   - Include type hints where appropriate
   - Handle exceptions gracefully

2. **Framework Guidelines**
   - Use project's specified framework
   - Follow framework conventions
   - Implement proper patterns
   - Ensure thread safety for async operations

3. **External Integration**
   - Maintain API compatibility
   - Handle authentication properly
   - Implement error handling for external calls
   - Use appropriate rate limiting

4. **Testing Requirements**
   - Test on target platform(s)
   - Verify components work correctly
   - Check operations work as expected
   - Validate integrations function properly

### Priority Rules

1. **ALWAYS** read and understand the full issue description before starting
2. **NEVER** skip steps described in the issue
3. **ALWAYS** maintain backward compatibility
4. **NEVER** break existing functionality
5. **ALWAYS** update progress incrementally
6. **NEVER** mark as closed until ALL requirements are met
7. **🚨 ALWAYS** test that the project still runs on its original platform
8. **🚨 NEVER** introduce platform-incompatible changes

### Error Handling

If an issue cannot be completed:
- Add error details to comments field
- Set progress to actual completion percentage
- Keep state as "open"
- Log detailed error information
- Continue with next issue if possible

### Atomic File Operations

When updating issue files:
```python
# Always use atomic operations
import tempfile
import os

# Write to temp file first
with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(issue_path)) as tmp:
    json.dump(issue_data, tmp, indent=2)
    temp_path = tmp.name

# Atomic replace
os.replace(temp_path, issue_path)
```

## FILE HANDLING RULES

### 🚨 CRITICAL: Files Are For Editing, Not Executing!

**FUNDAMENTAL RULE**: When issues mention files (e.g., "git.py", "main.js", "app.dart"):
- These files are **SOURCE CODE TO MODIFY**
- They are **NOT PROGRAMS TO RUN**
- They are **DATA/CONTENT TO WORK WITH**

### Correct File Operations

✅ **ALLOWED Operations on Files Mentioned in Issues:**
- READ the file to understand code structure
- ANALYZE the file to find problems
- MODIFY the file to fix issues
- CREATE new code in the file
- WRITE updated content to the file
- DELETE outdated code from the file

❌ **FORBIDDEN Operations on Files Mentioned in Issues:**
- EXECUTE the file (`python file.py`)
- RUN the file (`node file.js`)
- START the file as a program
- LAUNCH the file as application
- TEST by running the file

### Example Interpretations

| Issue Says | ❌ WRONG (NEVER DO THIS) | ✅ CORRECT (ALWAYS DO THIS) |
|------------|--------------------------|------------------------------|
| "Fix bug in [file]" | Execute/Run the file | Open file, read code, fix bug |
| "Tab missing in [file]" | Start application | Edit file, add tab code |
| "Error in [file]" | Launch program | Analyze file code, fix error |
| "Update [config]" | Execute config | Edit config content |

**NEVER use shell commands like `python`, `node`, `java`, etc. to RUN files!**
**ALWAYS use file operations to READ and EDIT files!**

## PLATFORM COMPATIBILITY RULES

### 🚨 CRITICAL: MAINTAIN PLATFORM COMPATIBILITY
**EVERY CHANGE MUST PRESERVE THE PROJECT'S ORIGINAL PLATFORM COMPATIBILITY**

### Platform Detection and Preservation
1. **FIRST**: Detect the project's target platform(s)
   - Check existing code for platform-specific imports/features
   - Look for requirements.txt, package.json, pubspec.yaml etc.
   - Identify platform indicators (e.g., Windows paths, Unix commands)
   - Check shebang lines, file endings, path separators

2. **ALWAYS**: Preserve original platform requirements
   - If project is Windows-only → Keep it Windows-only
   - If project is cross-platform → Maintain cross-platform compatibility
   - If project is Linux-only → Keep it Linux-only
   - NEVER introduce incompatible platform dependencies

3. **NEVER**: Break platform-specific functionality
   - Windows: Preserve Windows paths, registry access, COM objects
   - Linux/Mac: Preserve Unix permissions, signals, fork()
   - Mobile: Preserve platform-specific APIs

### Common Platform Pitfalls to Avoid

#### Python Projects
```python
# DETECT FIRST - Is this Windows-specific?
if 'winreg' in sys.modules or 'win32' in sys.modules:
    # This is a Windows project - preserve Windows features
    
# WRONG - Don't add Linux-specific to Windows project:
os.chmod(file, 0o755)  # Breaks on Windows

# WRONG - Don't add Windows-specific to Linux project:
import winreg  # Breaks on Linux
```

#### Path Handling
```python
# SAFE - Works everywhere:
from pathlib import Path
path = Path("subdirectory") / "file.txt"

# PLATFORM-SPECIFIC - Only if project already uses it:
path = "C:\\Users\\..."  # Keep if Windows-only project
path = "/home/user/..."  # Keep if Linux-only project
```

### Testing Requirements

**BEFORE MARKING ISSUE AS COMPLETE:**
1. Verify code runs on original platform
2. Check all imports work
3. Test file operations
4. Validate GUI components (if applicable)
5. Ensure external integrations work

### Platform-Specific Checklist

#### For Windows Projects:
- ✅ Paths use backslashes or Path()
- ✅ No Unix-only commands (chmod, chown)
- ✅ No fork(), use subprocess
- ✅ Windows line endings preserved (CRLF)
- ✅ No Linux-only packages

#### For Linux/Mac Projects:
- ✅ Paths use forward slashes or Path()
- ✅ No Windows-only modules (winreg, win32)
- ✅ Unix line endings preserved (LF)
- ✅ Permissions handled correctly
- ✅ No Windows-only packages

#### For Cross-Platform Projects:
- ✅ Use pathlib.Path everywhere
- ✅ Platform checks where needed
- ✅ Conditional imports for platform features
- ✅ Test on ALL target platforms
- ✅ Document platform requirements

## WORKFLOW AUTOMATION

### Batch Processing
Operations should be batched in single messages when possible:
- Read all necessary files
- Analyze requirements
- Implement all changes
- Update issue status

### Issue-Driven Development
- Let issues drive the implementation
- Don't assume project structure
- Follow issue specifications exactly
- Ask for clarification if unclear

## Important Reminders

- **Do what the issue asks**: nothing more, nothing less
- **NEVER assume project details**: get them from issues
- **ALWAYS batch operations** when possible
- **PREFER modifying existing files** over creating new ones
- **USE appropriate subdirectories** as specified in issues
- **RESPECT platform requirements** mentioned in issues
- **FOLLOW issue instructions** exactly as written
- **🚨 TEST EVERYTHING**: Ensure project still runs after changes
- **🚨 PRESERVE COMPATIBILITY**: Never break platform-specific features
- **🚨 VALIDATE BEFORE CLOSING**: Project must be fully functional
- **🚨 FILES ARE DATA**: Never execute files mentioned in issues - only edit them
- **🚨 CODE IS CONTENT**: Treat source files as text to modify, not programs to run