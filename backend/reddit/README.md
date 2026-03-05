# Reddit outreach (collector + human review)

## What you need from Reddit

1. **Create a Reddit “script” app**  
   Go to https://www.reddit.com/prefs/apps → “create another app…”  
   - Type: **script**  
   - Name: e.g. `AstroRoshniCollector`  
   - Redirect URI: `http://localhost:8080` (not used for read-only)  
   - Save. You’ll see **client id** (under the app name) and **secret**.

2. **Set in backend `.env`**  
   - `REDDIT_CLIENT_ID` = the short string under the app name  
   - `REDDIT_CLIENT_SECRET` = the “secret”  
   - `REDDIT_USER_AGENT` = e.g. `AstroRoshniCollector/1.0 by YourRedditUsername` (use your Reddit username)

3. **Optional**  
   - `REDDIT_SUBREDDITS` = comma-separated list, default: `astrology,AskAstrologers,vedicastrology`

## Flow

1. **Collect** – Admin → Reddit → “Run collector”. Fetches last 7 days of posts, detects birth-detail patterns, stores in `reddit_questions`.
2. **Analyze** – (Separate agent, not in this repo yet.) Picks questions with birth data, runs your chart + Gemini, saves drafts to `reddit_answers`.
3. **Review** – Admin → Reddit → “Draft answers”. Edit if needed, then “Approve & save” or “Reject”. Approved drafts are ready for a separate posting step (e.g. cron that posts via Reddit API).

## Install

```bash
pip install praw
```

(Already added to `requirements.txt`.)
