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
├── server.py              # Main Flask application with Auth0 integration
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── home.html         # Home page template
│   └── protected.html    # Protected page template
├── test-app.http         # REST Client test file for generating test data
├── env.example           # Environment variables template
└── README.md            # This file
```

## Setup Instructions

### 1. Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd flask-auth0-clean
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your Auth0 credentials
   ```

5. **Run the application**:
   ```bash
   python server.py
   ```
   The app will be available at `http://localhost:3000`

### 2. Auth0 Configuration

1. **Create Auth0 Application**:
   - Go to [Auth0 Dashboard](https://manage.auth0.com/)
   - Create a new "Regular Web Application"
   - Configure callback URLs: `http://localhost:3000/callback`
   - Configure logout URLs: `http://localhost:3000/`

2. **Set environment variables**:
   ```
   AUTH0_DOMAIN=your-domain.auth0.com
   AUTH0_CLIENT_ID=your-client-id
   AUTH0_CLIENT_SECRET=your-client-secret
   APP_SECRET_KEY=your-secret-key
   ```

### 3. Azure Deployment

1. **Create Azure Resources**:
   ```bash
   # Create resource group
   az group create --name cst8919-rg --location canadacentral
   
   # Create app service plan
   az appservice plan create --name cst8919-plan --resource-group cst8919-rg --sku B1
   
   # Create web app
   az webapp create --name cst8919-plan --resource-group cst8919-rg --plan cst8919-plan --runtime "PYTHON:3.9"
   ```

2. **Configure environment variables in Azure Portal**:
   - Go to your Web App → Configuration → Application settings
   - Add the same environment variables as local setup
   - **Important**: Update Auth0 callback/logout URLs to include Azure URL

3. **Deploy to Azure**:
   ```bash
   # Package application
   zip -r app.zip . -x "venv/*" "*.pyc" "__pycache__/*" ".env" ".git/*"
   
   # Deploy
   az webapp deployment source config-zip --resource-group cst8919-rg --name cst8919-plan --src app.zip
   ```

4. **Update Auth0 URLs for Azure**:
   - **Allowed Callback URLs**: Add `https://your-app-name.azurewebsites.net/callback`
   - **Allowed Logout URLs**: Add `https://your-app-name.azurewebsites.net/`

## Security Monitoring & Alerting

### KQL Query for Threat Detection

The following KQL query detects users who access the `/protected` route more than 10 times in 15 minutes:

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

### Azure Alert Configuration

1. **Create Action Group**:
   - Name: `cst8919-security-alerts`
   - Add email action with your email address

2. **Create Alert Rule**:
   - **Signal type**: Log
   - **Query**: Use the KQL query above
   - **Threshold**: 0 (triggers when any results are found)
   - **Evaluation frequency**: 5 minutes
   - **Time window**: 15 minutes
   - **Severity**: 3 (Low)
   - **Action group**: Select the created action group

### Testing the Alert

1. **Generate test data**:
   - Use `test-app.http` with VSCode REST Client
   - Or manually access `/protected` 15+ times in quick succession
   - Or use browser console: `for(let i=0; i<15; i++) { fetch('/protected'); }`

2. **Verify alert trigger**:
   - Check email for alert notification
   - Verify in Azure Portal → Alerts

## Logging Structure

The application logs user activities in structured JSON format:

```json
{
  "timestamp": "2025-07-02T10:30:00.000Z",
  "activity_type": "protected_route_access",
  "user_id": "auth0|123456789",
  "email": "user@example.com",
  "name": "John Doe",
  "client_ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "route": "/protected"
  }
}
```

## Testing

### Using VSCode REST Client

1. Install "REST Client" extension
2. Open `test-app.http`
3. Update `@baseUrl` variable for your environment
4. Click "Send Request" buttons to test endpoints

### Manual Testing

1. **Local testing**: `http://localhost:3000`
2. **Azure testing**: `https://your-app-name.azurewebsites.net`
3. **Test flow**: Login → Access protected page → Logout

## Troubleshooting

### Common Issues

1. **Auth0 callback URL mismatch**:
   - Ensure callback URLs in Auth0 match exactly (including protocol)
   - For Azure: Use HTTPS URLs

2. **Module not found errors**:
   - Ensure `requirements.txt` is included in deployment package
   - Check Azure Web App runtime version

3. **Logout redirect issues**:
   - Verify logout URLs in Auth0 configuration
   - Check for trailing slashes

### Log Analysis

- **View logs**: Azure Portal → Web App → Log stream
- **Query logs**: Log Analytics workspace → Logs
- **Monitor alerts**: Azure Portal → Alerts

## Security Considerations

- Environment variables are not committed to Git
- Sensitive data is stored in Azure Key Vault (recommended for production)
- HTTPS is enforced on Azure deployment
- Session data is minimized to reduce cookie size
- All user activities are logged for security monitoring

## Links
- **YouTube Demo**:[Watch on YouTube](https://youtu.be/CqnQ2tUOOEw)