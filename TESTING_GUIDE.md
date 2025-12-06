# 🧪 Saathi Legal Assistant Testing Guide

## 1. 🏠 LOCAL TESTING (Development)

### Basic Server Test:
```bash
# Start local server
python app_production.py

# Expected output:
# 🚀 Starting Saathi Legal Assistant - Gemini Powered
# 🤖 Model: gemini-1.5-flash  
# 🔑 API Configured: False/True
# 🌐 Running on 0.0.0.0:5000
# * Running on http://127.0.0.1:5000
```

### Test URLs (Local):
- **Landing Page**: http://127.0.0.1:5000/
- **Health Check**: http://127.0.0.1:5000/health
- **API Status**: http://127.0.0.1:5000/api/status
- **Chat Interface**: http://127.0.0.1:5000/chat.html

---

## 2. 🌐 RAILWAY PRODUCTION TESTING

### Check Deployment Status:
1. Go to Railway dashboard
2. Check build logs for:
   ```
   [INFO] Starting gunicorn
   [INFO] Listening at: http://0.0.0.0:8080
   [INFO] Using worker: sync
   [INFO] Booting worker with pid: [number]
   ```

### Production Test URLs:
- **Landing Page**: https://your-app-name.railway.app/
- **Health Check**: https://your-app-name.railway.app/health
- **API Status**: https://your-app-name.railway.app/api/status

---

## 3. 🔧 API TESTING

### PowerShell Commands:
```powershell
# Health check
Invoke-RestMethod -Uri "http://127.0.0.1:5000/health" -Method GET

# API status  
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/status" -Method GET

# Test chat endpoint
$chatData = @{
    message = "Hello, I need legal help"
    conversation_history = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/chat" -Method POST -Body $chatData -ContentType "application/json"
```

### Expected Health Response:
```json
{
  "status": "healthy",
  "app": "Saathi Legal Assistant - Gemini Powered",
  "version": "2.0.0",
  "api_configured": true/false,
  "model": "gemini-1.5-flash",
  "provider": "Google Gemini",
  "timestamp": "2025-08-12T..."
}
```

---

## 4. 🎯 FEATURE TESTING

### UI/UX Features:
- ✅ Landing page loads without errors
- ✅ "Get Started" button works
- ✅ Chat interface is responsive
- ✅ Loading indicators appear
- ✅ Input validation works
- ✅ Back button navigates correctly

### Chat System:
- ✅ Send message functionality
- ✅ Conversation history display
- ✅ Reset conversation works
- ✅ Error handling for failed requests

### Document Templates:
- ✅ Template list loads: `/api/templates`
- ✅ Template questions load: `/api/template-questions/rent_agreement`
- ✅ Document generation: `/api/generate-document`

---

## 5. 🚨 ERROR TESTING

### Common Error Scenarios:
```powershell
# Test 404 error
Invoke-RestMethod -Uri "http://127.0.0.1:5000/nonexistent" -Method GET

# Test malformed chat request
$badData = @{ invalid = "data" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5000/chat" -Method POST -Body $badData -ContentType "application/json"
```

### Expected Error Response:
```json
{
  "error": "Endpoint not found",
  "status": "error"
}
```

---

## 6. 📱 MOBILE TESTING

### Test on Different Devices:
- **Chrome DevTools**: F12 → Device simulation
- **Real devices**: Use network IP (e.g., http://192.168.29.99:5000/)
- **Responsive design**: Check breakpoints at 768px, 1024px

---

## 7. 🔍 LOG MONITORING

### Local Logs:
- Watch terminal output for requests
- Check for error messages
- Monitor response times

### Railway Logs:
```bash
# If you have Railway CLI installed
railway logs

# Or check in Railway dashboard > Deployments > View Logs
```

### Key Log Patterns:
- ✅ Good: `[INFO] "GET / HTTP/1.1" 200`
- ❌ Error: `[ERROR] "GET / HTTP/1.1" 500`
- ⚠️ Warning: `DeprecationWarning` (should be fixed now)

---

## 8. 🎛️ PERFORMANCE TESTING

### Load Testing (Optional):
```powershell
# Simple stress test - multiple requests
1..10 | ForEach-Object { 
    Invoke-RestMethod -Uri "http://127.0.0.1:5000/health" -Method GET 
}
```

### Check Response Times:
```powershell
Measure-Command { 
    Invoke-RestMethod -Uri "http://127.0.0.1:5000/" -Method GET 
}
```

---

## 9. ✅ SUCCESS CRITERIA

### Local Testing Success:
- [ ] Server starts without import errors
- [ ] All static files load (CSS, JS)
- [ ] Health endpoint returns 200
- [ ] Chat interface is functional
- [ ] No 404 errors for required files

### Production Testing Success:
- [ ] Railway shows "Deployment successful"
- [ ] Gunicorn workers start properly
- [ ] No development server warnings
- [ ] External requests work correctly
- [ ] Container doesn't crash after startup

---

## 10. 🐛 TROUBLESHOOTING

### Common Issues:
1. **Import Errors**: Missing dependencies in requirements.txt
2. **404 Errors**: Static file routing issues
3. **500 Errors**: Application crashes or API configuration
4. **Container Crashes**: Development server in production

### Debug Commands:
```powershell
# Check if server is running
netstat -ano | findstr :5000

# Test specific endpoint
curl -v http://127.0.0.1:5000/health

# Check Railway deployment
# Go to Railway dashboard > View Logs
```

---

## 🎯 Quick Test Checklist:

**Local Testing:**
```powershell
# 1. Start server
python app_production.py

# 2. Test health
Invoke-RestMethod -Uri "http://127.0.0.1:5000/health"

# 3. Open browser
Start-Process "http://127.0.0.1:5000/"
```

**Production Testing:**
- Visit your Railway app URL
- Check Railway logs for Gunicorn startup
- Test health endpoint on production URL

---

## 11. 🔐 Anonymous Session & Consent Checks

1. **Verify anon_id creation (browser):** Load the landing page, open DevTools → Application → Local Storage, and confirm `saathi_anon_id` exists. Clearing storage should regenerate a new value on refresh.
2. **API echo test:**
  ```powershell
  $headers = @{ 'Content-Type' = 'application/json'; 'X-Anon-Id' = 'test-anon-123' }
  Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/start-session" -Method POST -Headers $headers -Body '{"user_name":"QA","session_id":"sess-1"}'
  ```
  Response should include the same `anon_id` value.
3. **Consent persistence:** Submit `/api/consent` with the same header and confirm a corresponding row appears in `consent_events` (`anon_id` column) and log fallback if DB unavailable.
4. **Rate limiting linkage:** Reuse a single `anon_id` to hit `/api/chat` more than `RATE_LIMIT_REQUESTS` times per minute and confirm the 429 response references that identifier; switch to a new `anon_id` to reset the window without changing IP.
5. **Calculator / reviewer propagation:** Send calculator or reviewer requests with and without the `X-Anon-Id` header and make sure audit logs capture the resolved anon_id (inspect SQLite `audit_logs` table).
