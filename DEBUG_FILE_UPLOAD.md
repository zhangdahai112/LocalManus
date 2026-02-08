### File Upload Debug Checklist

## Expected Flow:
1. User selects file → Omnibox uploads immediately
2. File stored in `uploads/{user_id}/`
3. Response includes `file_path` field
4. User clicks send → filePaths array passed to page.tsx
5. page.tsx builds URL with file_paths query param
6. Backend receives file_paths and passes to orchestrator

## Debug Points:

### Frontend (Omnibox.tsx)
- [ ] Check console.log: "Omnibox handleSubmit - uploadedFiles"
- [ ] Verify uploadedFiles has items with file_path property
- [ ] Verify filePaths array is not empty

### Frontend (page.tsx)
- [ ] Check console.log: "Sending message with file paths"
- [ ] Check console.log: "File paths parameter"
- [ ] Check console.log: "Request URL"
- [ ] Verify URL contains `file_paths=...` parameter

### Backend
- [ ] Check orchestrator receives file_paths_list
- [ ] Check system prompt includes file context

## Test Case:
1. Upload a test.txt file
2. Type "这个文件是干啥的" and send
3. Expected URL should be:
   `/api/chat?input=...&session_id=...&file_paths=uploads%2F1%2Fxxx.txt&access_token=...`

## Common Issues:
- Empty file_paths parameter → uploadedFiles cleared too early
- Wrong file_path format → Check backend response
- Agent not seeing files → System prompt not updated
