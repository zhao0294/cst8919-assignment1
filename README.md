# CST8919 Assignment 1: Securing and Monitoring an Authenticated Flask App

## Overview

This project combines the Auth0 authentication from Lab 1 with Azure monitoring from Lab 2 to create a production-ready secure Flask application with comprehensive logging and threat detection capabilities.

## Features

- **Auth0 SSO Integration**: Secure user authentication using Auth0
- **Structured Logging**: JSON-formatted logs for Azure Monitor analysis
- **Activity Monitoring**: Tracks user logins, protected route access, and unauthorized attempts
- **Threat Detection**: KQL queries to identify suspicious access patterns
- **Azure Alerts**: Automated notifications for security incidents

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

## Setup Instructions

### 1. Auth0 Configuration

1. Go to [Auth0 Dashboard](https://manage.auth0.com/) and create a new "Regular Web Application"
2. Configure the following settings:
   - **Allowed Callback URLs**: `http://localhost:3000/callback`, `https://your-app-name.azurewebsites.net/callback`
   - **Allowed Logout URLs**: `http://localhost:3000`, `https://your-app-name.azurewebsites.net`
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

Visit `http://localhost:3000` to test the application.

### 3. Azure Deployment

1. **Create Azure Resources** (via Azure Portal or CLI):
   - Resource Group
   - App Service Plan (Free tier F1)
   - Web App with Python 3.9 runtime

2. **Configure Environment Variables** in Azure App Service:
   - Add all variables from your `.env` file
   - Update AUTH0 callback URLs to include Azure domain

3. **Enable Diagnostic Settings**:
   - Go to Azure Portal > App Service > Monitoring > Diagnostic settings
   - Enable **AppServiceConsoleLogs**
   - Send to **Log Analytics workspace**

4. **Deploy Application**:
   - Use Azure CLI: `az webapp deployment source config-zip`
   - Or use Azure Portal > Deployment Center

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
     - Threshold value: 0
     - Evaluated based on:
       - Period: 15 minutes
       - Frequency: 5 minutes

4. **Action Group**:
   - Create new action group
   - Add email notification action
   - Notification type: Email/SMS/Push/Voice

5. **Alert Details**:
   - Severity: 3 (Low)
   - Alert rule name: "Excessive Protected Route Access"
   - Description: "User accessing protected route more than 10 times in 15 minutes"

### Testing Alert System

1. **Authenticate** through Auth0 login
2. **Access** `/protected` route multiple times rapidly (>10 times in 15 minutes)
3. **Monitor** Alert should trigger within 5-15 minutes
4. **Verify** Email notification received

## Testing & Simulation

### Using test-app.http

The included `test-app.http` file contains various test scenarios:

1. **Basic functionality tests**:
   - Home page access
   - Health check
   - Login flow initiation

2. **Security testing**:
   - Unauthorized access attempts
   - Multiple protected route accesses

3. **Update baseUrl** in the file for your deployment:
   - Local: `@baseUrl = http://localhost:3000`
   - Azure: `@baseUrl = https://your-app-name.azurewebsites.net`

### Manual Testing Steps

1. **Test normal user flow**:
   - Visit home page
   - Click login
   - Complete Auth0 authentication
   - Access protected page
   - Logout

2. **Test security scenarios**:
   - Try accessing `/protected` without authentication
   - Login and access `/protected` 15+ times quickly
   - Check Azure Monitor logs
   - Verify alert triggers

## Security Considerations

- **Environment Variables**: Never commit `.env` files with secrets
- **HTTPS**: Use HTTPS in production (Azure provides this automatically)
- **Session Security**: Flask sessions are signed with secret key
- **Rate Limiting**: Consider implementing rate limiting for production
- **IP Allowlisting**: Consider restricting access by IP for admin functions

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