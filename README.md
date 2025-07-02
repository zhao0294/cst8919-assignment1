# CST8919 Assignment 1: Securing and Monitoring an Authenticated Flask App

## Overview

This project combines the Auth0 authentication from Lab 1 with Azure monitoring from Lab 2 to create a production-ready secure Flask application with comprehensive logging and threat detection capabilities.

## Features

- **Auth0 SSO Integration**: Secure user authentication using Auth0
- **Structured Logging**: JSON-formatted logs for Azure Monitor analysis
- **Activity Monitoring**: Tracks user logins, protected route access, and unauthorized attempts
- **Threat Detection**: KQL queries to identify suspicious access patterns
- **Azure Alerts**: Automated notifications for security incidents
- **Production Deployment**: Successfully deployed to Azure App Service

## Project Structure

```
flask-auth0-clean/
├── server.py              # Main Flask application with enhanced logging
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
├── test-app.http         # HTTP test requests
├── templates/
│   ├── home.html         # Home page template
│   └── protected.html    # Protected page template
└── README.md             # This file
```

## Deployment Status

✅ **Local Development**: Working on port 3000  
✅ **Azure Deployment**: Successfully deployed and operational  
✅ **Auth0 Integration**: Login and logout working correctly  
✅ **HTTPS Enforcement**: Properly configured for Azure deployment  

**Live Application**: https://cst8919-plan-amgwc3cpg9b5ascx.canadacentral-01.azurewebsites.net/

## Setup Instructions

### 1. Auth0 Configuration

1. Go to [Auth0 Dashboard](https://manage.auth0.com/) and create a new "Regular Web Application"
2. Configure the following settings:
   - **Allowed Callback URLs**: 
     ```
     http://localhost:3000/callback
     https://cst8919-plan-amgwc3cpg9b5ascx.canadacentral-01.azurewebsites.net/callback
     ```
   - **Allowed Logout URLs**: 
     ```
     http://localhost:3000
     http://localhost:3000/
     https://cst8919-plan-amgwc3cpg9b5ascx.canadacentral-01.azurewebsites.net
     https://cst8919-plan-amgwc3cpg9b5ascx.canadacentral-01.azurewebsites.net/
     ```
3. Note down:
   - Client ID
   - Client Secret  
   - Domain (e.g., your-tenant.auth0.com)

### 2. Local Development Setup

1. Clone this repository:
```bash
git clone <your-repo-url>
cd flask-auth0-clean
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
# Copy from .env.example and fill in your values
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret
AUTH0_DOMAIN=your-tenant.auth0.com
APP_SECRET_KEY=your_generated_secret_key
PORT=3000
```

Generate secret key:
```bash
openssl rand -hex 32
```

5. Run the application:
```bash
python server.py
```

6. Visit `http://localhost:3000` to test the application.

**✅ Local deployment verified and working!**

### 3. Azure Deployment

1. **Create Azure Resources** (via Azure Portal or CLI):
   - Resource Group: `cst8919-rg`
   - App Service Plan: `cst8919-plan` (Free tier F1)
   - Web App: `cst8919-plan` with Python 3.9 runtime

2. **Configure Environment Variables** in Azure App Service:
   - Add all variables from your `.env` file
   - Ensure AUTH0 callback and logout URLs include Azure domain

3. **Enable Diagnostic Settings**:
   - Go to Azure Portal > App Service > Monitoring > Diagnostic settings
   - Enable **AppServiceConsoleLogs**
   - Send to **Log Analytics workspace**

4. **Deploy Application**:
```bash
# Package application
zip -r app.zip . -x "venv/*" "*.pyc" "__pycache__/*" ".env" ".git/*"

# Deploy to Azure
az webapp deployment source config-zip --resource-group cst8919-rg --name cst8919-plan --src app.zip
```

**✅ Azure deployment verified and working!**

## Key Implementation Details

### HTTPS Enforcement for Azure
The application automatically detects Azure deployment and enforces HTTPS URLs for Auth0 callbacks and logout redirects:

```python
# Login route with HTTPS enforcement
if 'azurewebsites.net' in request.host:
    callback_url = url_for("callback", _external=True, _scheme='https')

# Logout route with exact URL matching
if 'azurewebsites.net' in request.host:
    return_to = "https://cst8919-plan-amgwc3cpg9b5ascx.canadacentral-01.azurewebsites.net"
```

### Auth0 URL Configuration
Critical for successful logout functionality:
- **Allowed Logout URLs** must include both with and without trailing slash
- **Allowed Callback URLs** must use HTTPS for Azure deployment
- Exact URL matching is required by Auth0

## Logging Architecture

### Structured Logging Format
The application logs user activities in JSON format for easy parsing by Azure Monitor:

```json
{
  "timestamp": "2025-01-04T12:34:56.789Z",
  "activity_type": "protected_route_access",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "user_id": "auth0|507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "John Doe",
  "details": {
    "route": "/protected"
  }
}
```

### Activity Types Tracked
- `login_initiated`: User starts login process
- `login_successful`: Successful Auth0 authentication
- `login_failed`: Failed authentication attempt
- `logout`: User logs out
- `home_page_access`: Home page visit
- `protected_route_access`: Access to protected resources
- `unauthorized_access_attempt`: Blocked access attempt

## Threat Detection & Monitoring

### KQL Query for Excessive Access Detection

This query identifies users who access the `/protected` route more than 10 times in 15 minutes:

```kql
AppServiceConsoleLogs
| where TimeGenerated > ago(15m)
| where ResultDescription contains "USER_ACTIVITY"
| where ResultDescription contains "protected_route_access"
| extend LogData = parse_json(substring(ResultDescription, indexof(ResultDescription, "{")))
| where isnotempty(LogData.user_id)
| summarize AccessCount = count() by 
    user_id = tostring(LogData.user_id),
    email = tostring(LogData.email),
    bin(TimeGenerated, 15m)
| where AccessCount > 10
| project TimeGenerated, user_id, email, AccessCount
| order by AccessCount desc
```

### Advanced Security Analysis Queries

1. **Failed Login Attempts**:
```kql
AppServiceConsoleLogs
| where TimeGenerated > ago(1h)
| where ResultDescription contains "login_failed"
| extend LogData = parse_json(substring(ResultDescription, indexof(ResultDescription, "{")))
| summarize FailedAttempts = count() by 
    client_ip = tostring(LogData.client_ip),
    bin(TimeGenerated, 5m)
| where FailedAttempts > 3
| order by FailedAttempts desc
```

2. **Unauthorized Access Patterns**:
```kql
AppServiceConsoleLogs
| where TimeGenerated > ago(30m)
| where ResultDescription contains "unauthorized_access_attempt"
| extend LogData = parse_json(substring(ResultDescription, indexof(ResultDescription, "{")))
| summarize UnauthorizedAttempts = count() by 
    client_ip = tostring(LogData.client_ip),
    user_agent = tostring(LogData.user_agent)
| order by UnauthorizedAttempts desc
```

## Azure Alert Configuration

### Alert Rule Setup

1. **Navigate to Azure Monitor** > Alerts > Create Alert Rule

2. **Scope**: Select your Log Analytics workspace

3. **Condition**:
   - Signal type: Custom log search
   - Search query: Use the excessive access KQL query above
   - Alert logic:
     - Based on: Number of results
     - Operator: Greater than
     - Threshold: 0
     - Evaluation frequency: Every 5 minutes

4. **Actions**: Configure email notifications or webhook actions

## Testing

### Local Testing
```bash
# Test login flow
curl -X GET http://localhost:3000/login

# Test protected route (should redirect to login)
curl -X GET http://localhost:3000/protected

# Test health endpoint
curl -X GET http://localhost:3000/health
```

### Azure Testing
```bash
# Test health endpoint
curl -X GET https://cst8919-plan-amgwc3cpg9b5ascx.canadacentral-01.azurewebsites.net/health

# Test login flow
curl -X GET https://cst8919-plan-amgwc3cpg9b5ascx.canadacentral-01.azurewebsites.net/login
```

## Troubleshooting

### Common Issues

1. **Auth0 Callback URL Mismatch**:
   - Ensure Allowed Callback URLs include both local and Azure URLs
   - Use HTTPS for Azure deployment URLs

2. **Logout Not Working**:
   - Verify Allowed Logout URLs include both with and without trailing slash
   - Check that the exact URL is being generated by the application

3. **Module Not Found Errors**:
   - Ensure `requirements.txt` is included in deployment package
   - Verify all dependencies are listed in requirements.txt

4. **Environment Variables**:
   - Check Azure App Service Configuration settings
   - Verify all required Auth0 variables are set

## Security Considerations

- Environment variables are stored securely in Azure App Service Configuration
- Sensitive files (.env) are excluded from Git repository
- HTTPS is enforced for all Azure deployments
- Structured logging provides audit trail for security monitoring
- Auth0 handles secure token management and user authentication

## Future Enhancements

- Implement rate limiting for login attempts
- Add multi-factor authentication support
- Enhanced threat detection with machine learning
- Real-time security dashboard
- Automated incident response workflows

## Demo Video

[YouTube Demo Link](your-youtube-link-here)

### Demo Content:
- Live Auth0 login/logout flow
- Azure deployment walkthrough
- Log generation and monitoring
- KQL query execution in Azure Monitor
- Alert configuration and testing
- Security scenarios demonstration

## What I Learned

- **Integration Complexity**: Combining Auth0, Flask, and Azure monitoring requires careful configuration
- **Structured Logging**: JSON format logs enable powerful querying and analysis
- **Real-time Monitoring**: Azure Monitor provides near real-time threat detection capabilities
- **DevSecOps Practices**: Security monitoring should be built into the application from the start

## Future Improvements

- **Machine Learning**: Use Azure ML for anomaly detection
- **Geographic Analysis**: Track login locations for suspicious patterns
- **Advanced Correlation**: Cross-reference multiple log sources
- **Automated Response**: Implement automatic user blocking for suspicious activity
- **Dashboard**: Create Azure Dashboard for security metrics visualization

## Troubleshooting

### Common Issues

1. **Auth0 Callback Error**:
   - Verify callback URLs in Auth0 dashboard
   - Check environment variables

2. **Azure Logs Not Appearing**:
   - Ensure AppServiceConsoleLogs is enabled
   - Check Log Analytics workspace connection
   - Wait 5-10 minutes for log ingestion

3. **Alert Not Triggering**:
   - Verify KQL query returns results
   - Check alert rule configuration
   - Ensure action group is properly configured

## Repository

- **GitHub**: [Your Repository URL]
- **Live Demo**: [Azure App Service URL]
- **Video Demo**: [YouTube URL]

---

**Submission Date**: [Your Submission Date]
**Course**: CST8919
**Assignment**: Assignment 1 