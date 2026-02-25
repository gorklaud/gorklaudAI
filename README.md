
<img width="1080" height="360" alt="im231312age" src="https://github.com/user-attachments/assets/6fd6a00a-b446-4121-9aa5-f3a157e47956" />


Gorklaud: Grok-powered X bot that spots mentions, reads context (including parent tweets), and replies with short, clear, humorous explanations. Made with Clawdbot. No emojis, no fluff — just helpful summaries.
Gorklaud is a friendly, automated bot that watches for mentions on X (Twitter), reads the tweet (and the parent tweet if it's a reply), and replies with a short, clear, humorous explanation that makes the content easy to understand — like explaining it to a 10-year-old.

Powered by xAI's Grok + Clawdbot.  
No emojis. No hashtags. No fluff. Just straightforward help.

## Features

- Polls recent mentions every ~30 seconds  
- Automatically fetches parent tweet context for threaded replies  
- Generates concise summaries/explanations (<280 characters)  
- Replies directly with only the helpful text (no framing like "Gorklaud says")  
- Privacy-first: no data storage, no analytics, no selling info

## Setup

1. **Create an X Developer App**  
   - Go to https://developer.x.com  
   - Create an app with **Read + Write** permissions  
   - Set Type: **Web App, Automated App or Bot**  
   - Generate **Consumer Key**, **Consumer Secret**, **Access Token**, **Access Token Secret** (with Read + Write)

2. **Get xAI API Key**  
   - Sign up at https://console.x.ai  
   - Create a new API key

3. **Install dependencies**

```bash
pip install requests requests-oauthlib python-dotenv
