# File Upload Debugging Guide

## Problem
Backend returns correct data including `file_path`, but frontend doesn't send it in the request URL.

## Backend Changes
✅ Added `file_path` field to `FileRead` model in `core/models.py`

## Frontend Debug Steps

### 1. Check File Upload Response
When you upload a file, check the browser Console for:
```
File upload response: {id: 5, filename: "...", file_path: "uploads/1/...", ...}
Current uploadedFiles before update: []
New uploadedFiles after update: [{id: 5, file_path: "uploads/1/...", ...}]
```

**Expected:** `file_path` should be present in the response

### 2. Check handleSubmit Call
When you click send, check Console for:
```
=== handleSubmit called ===
inputValue: "这是审美"
uploadedFiles.length: 1
uploadedFiles: [{id: 5, file_path: "uploads/1/xxx.txt", ...}]
Processing file: {id: 5, file_path: "uploads/1/xxx.txt", ...}
file.file_path: "uploads/1/xxx.txt"
Omnibox handleSubmit - filePaths: ["uploads/1/xxx.txt"]
```

**Expected:** `uploadedFiles` should contain the file with `file_path`

### 3. Check Parent Component Call
In page.tsx, check Console for:
```
handleSendMessage called with filePaths: ["uploads/1/xxx.txt"]
File paths parameter: uploads/1/xxx.txt
Request URL: http://localhost:8000/api/chat?input=...&file_paths=uploads%2F1%2Fxxx.txt&...
```

**Expected:** `filePaths` should be passed to parent and included in URL

## Possible Issues

### Issue 1: Backend not returning file_path
**Check:** Look at Network tab → upload request → Response
**Fix:** ✅ Already fixed by adding field to FileRead model

### Issue 2: State not persisting across mode change
**Check:** uploadedFiles should show in both home and chat mode
**Fix:** ✅ Already fixed by lifting state to page.tsx

### Issue 3: React state update timing
**Problem:** State might not update before submit is called
**Solution:** The logs will show if uploadedFiles is empty during handleSubmit

## Test Procedure
1. Open browser DevTools (F12) → Console tab
2. Upload a file (e.g., lemon.txt)
3. Look for "File upload response" log - verify file_path is present
4. Type a message and click send
5. Look for "=== handleSubmit called ===" log
6. Check if uploadedFiles contains the file
7. Check if filePaths array is passed to parent
8. Check Network tab for the /api/chat request URL

## Expected vs Actual

### Expected URL:
```
/api/chat?input=%E8%BF%99%E6%98%AF%E5%AE%A1%E7%BE%8E&file_paths=uploads%2F1%2Fxxx.txt&...
```

### Actual URL (if broken):
```
/api/chat?input=%E8%BF%99%E6%98%AF%E5%AE%A1%E7%BE%8E&file_paths=&...
```

## Next Steps
Run the test and share the Console logs. This will tell us exactly where the data is being lost.
