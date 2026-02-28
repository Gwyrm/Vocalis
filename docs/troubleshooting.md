# Troubleshooting Guide

Common issues and solutions for Vocalis.

## Backend Issues

### ❌ "Port 8080 already in use"

**Error:**
```
Address already in use
```

**Solution:**
```bash
# Find process using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or restart on different port
export PORT=8081
python main.py
```

### ❌ "Ollama connection failed"

**Error:**
```
Cannot connect to http://localhost:11434
```

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434

# Start Ollama
ollama serve

# Or with Docker
docker run -d -p 11434:11434 ollama/ollama
docker exec ollama ollama pull mistral
```

### ❌ "Database locked"

**Error:**
```
database is locked
```

**Solution:**
```bash
# Remove lock files
cd backend
rm *.db-shm *.db-wal

# Restart backend
python main.py
```

### ❌ "Module not found"

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### ❌ "Reading from readonly database"

**Error:**
```
attempt to write a readonly database
```

**Solution:**
```bash
# Check file permissions
ls -la backend/*.db

# Fix permissions
chmod 644 backend/*.db

# Restart from correct directory
cd backend
python main.py
```

## Frontend Issues

### ❌ "Flutter command not found"

**Error:**
```
Command 'flutter' not found
```

**Solution:**
```bash
# Add Flutter to PATH
export PATH="$PATH:$HOME/flutter/bin"

# Verify installation
flutter --version
```

### ❌ "Cannot connect to localhost:8080"

**Error:**
```
Connection refused / Network error
```

**Solution:**
1. Check backend is running:
   ```bash
   curl http://localhost:8080/api/health
   ```

2. If backend not running:
   ```bash
   cd backend && python main.py
   ```

3. Check API URL in app (should be `http://localhost:8080`)

### ❌ "Plugins not found"

**Error:**
```
No pubspec.lock file found
```

**Solution:**
```bash
cd frontend
flutter clean
flutter pub get
flutter run -d chrome
```

### ❌ "Chrome not found"

**Error:**
```
No device found (for -d chrome)
```

**Solution:**
```bash
# Run on connected device
flutter run

# Or specify another device
flutter devices  # List available devices
flutter run -d <device-name>
```

## Authentication Issues

### ❌ "Invalid email or password"

**Error:**
```json
{"detail": "Invalid email or password"}
```

**Solution:**
1. Check credentials:
   - Doctor: `doctor@hopital-demo.fr` / `demo123`
   - Nurse: `nurse@hopital-demo.fr` / `demo123`

2. Verify user exists in database:
   ```bash
   sqlite3 backend/demo.db "SELECT email FROM users;"
   ```

3. Reset password if needed:
   ```python
   from auth import hash_password
   import sqlite3

   conn = sqlite3.connect("backend/demo.db")
   cursor = conn.cursor()
   cursor.execute(
       "UPDATE users SET password_hash = ? WHERE email = ?",
       (hash_password("demo123"), "doctor@hopital-demo.fr")
   )
   conn.commit()
   ```

### ❌ "Invalid or expired token"

**Error:**
```json
{"detail": "Invalid or expired token"}
```

**Solution:**
1. Token expired → Login again
2. Invalid token → Clear local storage and login
3. Check Authorization header is correct:
   ```
   Authorization: Bearer <token>
   ```

### ❌ "Doctor role required"

**Error:**
```json
{"detail": "Doctor role required"}
```

**Solution:**
- Only doctors can confirm prescriptions
- Login as doctor account, not nurse
- Or create as nurse, have doctor confirm

## Prescription Issues

### ❌ "Prescription not saved"

**Error:**
- Form submits but nothing happens
- No success message

**Solution:**
1. Check browser console (F12) for errors
2. Verify backend is running
3. Check network tab for failed requests
4. Ensure patient_id is valid
5. Try again after clearing browser cache

### ❌ "LLM not extracting data correctly"

**Error:**
- Medication comes back as null
- Dosage not recognized

**Solution:**
1. Use clearer prescription language:
   ```
   ❌ "Give amoxicilline"
   ✅ "Amoxicilline 500mg, three times daily for 10 days"
   ```

2. Check Ollama is running:
   ```bash
   curl http://localhost:11434
   ```

3. Verify LLM model is loaded:
   ```bash
   ollama list
   ```

### ❌ "Voice transcription not working"

**Error:**
- No audio recorded
- Transcription fails

**Solution:**
1. Check browser permissions (allow microphone)
2. Verify backend has Whisper loaded
3. Check browser console for errors
4. Try shorter, clearer audio
5. Use text input as fallback

### ❌ "Prescription not in history"

**Error:**
- Create prescription but doesn't appear in history

**Solution:**
1. Refresh page (F5)
2. Check patient_id is linked:
   ```bash
   sqlite3 backend/demo.db \
     "SELECT id, patient_id FROM prescriptions ORDER BY created_at DESC LIMIT 1;"
   ```

3. If patient_id is null, issue was fixed in latest version
4. Update to latest code:
   ```bash
   git pull origin main
   ```

### ❌ "Cannot edit prescription - 403 Forbidden"

**Error:**
```json
{"detail": "Only draft prescriptions can be edited"}
```

**Meaning:**
- You're trying to edit a **signed** prescription
- Signed prescriptions are locked and read-only

**Solution:**
1. Check prescription status (see status badge in UI)
2. If status is **"✓ Signée"** (Signed):
   - Cannot edit this prescription
   - Create a new prescription instead
3. If status is **"⏳ À signer"** (Draft):
   - Should be editable
   - Try refreshing page
   - Check you're logged in as correct user

### ❌ "Edit button not showing for draft prescription"

**Error:**
- Draft prescription exists but no Edit button visible

**Solution:**
1. Refresh page (F5)
2. Check status badge:
   - Orange badge = Draft → Edit button should show
   - Green badge = Signed → Edit button hidden (correct)
3. Check user role:
   - Must be doctor or nurse to edit
   - Different user may see read-only view
4. Clear browser cache
5. Check network tab (F12) for errors

### ❌ "Edited prescription didn't save"

**Error:**
- Click "Enregistrer", button shows spinner, but changes don't persist
- No success message shown

**Solution:**
1. Check backend is running:
   ```bash
   curl http://localhost:8080/api/health
   ```

2. Check network (F12 → Network tab):
   - Look for failed PUT request
   - Check response status code

3. If 422 error:
   - Check required fields are not empty
   - Medication, dosage, duration are required

4. If 404 error:
   - Prescription may have been deleted
   - Refresh and check prescription still exists

5. Try editing again with simpler changes

## Network Issues

### ❌ "Cannot reach API"

**Error:**
```
Failed to load resource: the server responded with a status of 401
Network error
```

**Solution:**
1. Backend must be running:
   ```bash
   ps aux | grep python
   ```

2. Check port is correct (8080)
3. Test directly:
   ```bash
   curl http://localhost:8080/api/health
   ```

4. Check CORS settings if behind proxy
5. Try disabling browser extensions

## Performance Issues

### 🐢 "App is slow"

**Solution:**
1. Close unnecessary browser tabs
2. Restart backend and frontend
3. Clear browser cache
4. Check Ollama resource usage:
   ```bash
   # On macOS with Docker
   docker stats
   ```

5. Voice/LLM operations are slower (expected 2-5 seconds)

## Getting Help

### Collect Debug Information

```bash
# Backend version info
python --version
pip list | grep fastapi

# Frontend version info
flutter --version
dart --version

# System info
uname -a
```

### Check Logs

```bash
# Backend logs
tail -f /tmp/backend.log

# Browser logs
F12 → Console → Check for red errors
```

### Common Log Locations

- Backend: `/tmp/backend.log` or console output
- Database: `backend/*.db`
- Frontend: Browser Developer Tools (F12)

---

**Still stuck?** Check the full [Documentation](index.md) or open an issue on GitHub.
