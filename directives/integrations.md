# Directive: External Integrations

## Goal
Connect GitHub activity and session wraps to Slack for real-time project visibility. Not required, but recommended for the best experience.

## When to Use
- Setting up a new DOE project and want notifications
- Onboarding Slack or GitHub integrations
- Debugging why wrap summaries aren't posting

## Inputs
- A Slack workspace (free plan works)
- GitHub repos subscribed via the GitHub for Slack app
- Slack incoming webhook URLs stored in `.env`

## Setup

### 1. GitHub for Slack (PR + CI notifications)

Install the GitHub for Slack app in your workspace. Create one channel per project (e.g. `#myproject`). In each channel:

```
/github subscribe Owner/repo-name pulls reviews workflows
```

This gives you PR opened/merged/closed, code reviews, and CI pass/fail. Skip `comments` initially -- bot comments (claude-code-action, Dependabot, Vercel) can double the noise. You'll still see human comments via DMs if you're mentioned.

Invite the GitHub bot to the channel first (`/invite @GitHub`) or it won't respond.

### 2. Slack Incoming Webhook (wrap summaries)

Create a Slack app at api.slack.com/apps (From scratch). Enable Incoming Webhooks. Add one webhook per channel -- each webhook URL maps to a specific channel.

Add the URLs to `.env` (gitignored, never committed):

```
SLACK_WEBHOOK_URL_MYPROJECT=https://hooks.slack.com/services/T.../B.../xxx
```

The key format is `SLACK_WEBHOOK_URL_<CHANNEL>` where `<CHANNEL>` matches the `--channel` arg passed to `slack_notify.py`.

### 3. Wrap Integration

`/wrap` calls `execution/slack_notify.py` automatically after the Gist sync step. It reads the webhook URL from `.env` and posts a formatted summary with:
- Session number, date, and tag (BUILD/PLAN/DEBUG/HOUSEKEEPING/RESEARCH)
- Feature name and session title
- Summary as bullet points
- App version, kit version, commits, lines, steps, duration, streak

If `.env` is missing or the webhook URL isn't set, the wrap continues without posting. Slack notification is always best-effort.

## Channel Structure

One channel per project. All signals (PRs, CI, wraps) go to the same channel. Split by signal type (separate PR/CI/deploy channels) only when different people care about different signals -- not before.

Rename channels freely -- subscriptions and webhooks are tied to internal IDs, not display names.

## Edge Cases
- Free Slack plan: 90-day message history, 10 app integrations max. Webhooks count as 1 integration (the app), not per-webhook.
- GitHub for Slack needs to be invited to each channel before `/github subscribe` works.
- Bot comments from claude-code-action will appear if you subscribe to `comments`. Leave `comments` off unless you want them.
- Webhook URLs are secrets. Store in `.env`, never in committed files. Pre-commit hooks with secret detection will catch accidental commits.

## Verification
- [ ] `/github subscribe` responds in the channel (not silently ignored)
- [ ] A test PR triggers a notification in the correct channel
- [ ] `python3 execution/slack_notify.py --channel <name> --file docs/wraps/session-N.json` posts successfully
- [ ] `.env` is listed in `.gitignore`
- [ ] Webhook URLs do not appear in any committed file
