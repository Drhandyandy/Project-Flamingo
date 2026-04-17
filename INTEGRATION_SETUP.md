# Project-Flamingo Integration Setup Guide

## 🚀 Complete Integration Overview

This project is connected to:
- **Render** - Deployment & Hosting
- **Google AI Studio** - AI Development Environment
- **Gemini API** - Google's Advanced AI Model
- **GitHub Copilot** - AI-Powered Code Assistance
- **Jules** - Team Collaboration

---

## 1️⃣ Render Deployment Setup

### Step 1: Get Render Deploy Hook
1. Go to your [Render Dashboard](https://dashboard.render.com)
2. Select your service: `srv-d7h5f7i8qa3s73cun760`
3. Navigate to **Settings** → **Deploy Hook**
4. Copy the deploy hook URL

### Step 2: Add GitHub Secret
1. Go to your GitHub repository: **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `RENDER_DEPLOY_HOOK`
4. Value: Paste the deploy hook URL from Step 1
5. Click **Add secret**

### Step 3: Auto-Deployment
- The GitHub Actions workflow (`.github/workflows/deploy-render.yml`) will now automatically deploy to Render every time you push to the `main` branch
- Check the **Actions** tab in GitHub to monitor deployments

---

## 2️⃣ Google AI Studio & Gemini API Setup

### Step 1: Get API Keys
1. Visit [Google AI Studio](https://aistudio.google.com)
2. Click **Get API Key** → **Create API Key in new project**
3. Copy your API key

### Step 2: Add GitHub Secrets
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add two new secrets:
   - Name: `GOOGLE_AI_API_KEY` | Value: [Your API key from Step 1]
   - Name: `GEMINI_API_KEY` | Value: [Your API key from Step 1]

### Step 3: Use in Your Python Code
```python
import os
import google.generativeai as genai

# Load API key from environment
api_key = os.getenv('GOOGLE_AI_API_KEY')
genai.configure(api_key=api_key)

# Use Gemini model
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Hello, world!")
print(response.text)
```

### Step 4: Update requirements.txt
Add to `requirements.txt`:
```
google-generativeai
```

Then run:
```bash
pip install -r requirements.txt
```

---

## 3️⃣ GitHub Copilot Integration

### Step 1: Install Copilot Extension
- **Visual Studio Code**: Install [GitHub Copilot extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)
- **JetBrains IDE**: Install [GitHub Copilot for JetBrains](https://plugins.jetbrains.com/plugin/17718-github-copilot)
- **Other editors**: Check [Copilot supported editors](https://github.com/features/copilot)

### Step 2: Authenticate
1. Open your IDE
2. The Copilot extension will prompt you to authenticate
3. Sign in with your GitHub account (that has Copilot access)

### Step 3: Enable for This Repository
1. In your IDE, open the Project-Flamingo repository
2. Copilot will automatically activate
3. Start typing code or comments to get AI suggestions

---

## 4️⃣ Add Jules as Collaborator

### Step 1: Navigate to Settings
1. Go to your repository on GitHub
2. Click **Settings** → **Collaborators**

### Step 2: Add Jules
1. Click **Add people**
2. Enter Jules's GitHub username
3. Select permission level (recommend: **Maintain** for full access)
4. Click **Add [Jules's username] to this repository**

### Step 3: Jules Accepts Invitation
- Jules will receive an invitation and can access the repository

---

## 📁 Environment Variables

Copy the `.env.example` file to create `.env`:
```bash
cp .env.example .env
```

Fill in your actual values:
```
GOOGLE_AI_API_KEY=your_actual_key_here
GEMINI_API_KEY=your_actual_key_here
RENDER_DEPLOY_HOOK=your_deploy_hook_url_here
```

⚠️ **IMPORTANT**: Never commit `.env` to version control. It's already in `.gitignore`.

---

## ✅ Verification Checklist

- [ ] Render deploy hook added to GitHub Secrets
- [ ] Google AI API key added to GitHub Secrets
- [ ] Gemini API key added to GitHub Secrets
- [ ] `.env.example` copied to `.env` locally
- [ ] `requirements.txt` updated with `google-generativeai`
- [ ] GitHub Actions workflow has run at least once
- [ ] Jules added as collaborator
- [ ] GitHub Copilot extension installed and authenticated

---

## 🔗 Quick Links

- [Render Dashboard](https://dashboard.render.com/web/srv-d7h5f7i8qa3s73cun760)
- [Google AI Studio](https://aistudio.google.com)
- [GitHub Repository Settings](https://github.com/Drhandyandy/Project-Flamingo/settings)
- [Repository Secrets](https://github.com/Drhandyandy/Project-Flamingo/settings/secrets/actions)
- [GitHub Actions](https://github.com/Drhandyandy/Project-Flamingo/actions)

---

## 🆘 Troubleshooting

**Render deployment not triggering?**
- Check that `RENDER_DEPLOY_HOOK` secret is set correctly
- Verify the GitHub Actions workflow status in the **Actions** tab

**Google AI API not working?**
- Ensure `GOOGLE_AI_API_KEY` is set correctly in GitHub Secrets
- Run `pip install google-generativeai` to ensure the library is installed

**Copilot not working?**
- Restart your IDE
- Check that you're signed in with a GitHub account that has Copilot access
- Ensure Copilot extension is enabled

---

**All systems connected! 🎉**
