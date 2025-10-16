# GitHub Actions Automated Crawling

This repository is configured to automatically crawl Cornell's Legal Information Institute daily using GitHub Actions workflows. The system runs for a maximum of 3 hours per day and persists the database between runs.

## 🔄 How It Works

### Daily Crawl Workflow (`crawl.yml`)

**Schedule:** Runs daily at 2 AM UTC (automatic)

**Process:**
1. Downloads the latest database from GitHub Releases
2. Resets any stuck jobs from previous runs
3. Runs the crawler with 2 workers for 3 hours (180 minutes)
4. Automatically stops after 3 hours using a timeout
5. Compresses and uploads the database to GitHub Releases
6. Creates artifacts for the latest run

**Key Features:**
- ⏰ **3-hour daily limit** - Respects rate limits and resource constraints
- 💾 **State persistence** - Database is preserved between runs via GitHub Releases
- 🔁 **Resumable** - Each run continues from where the previous one stopped
- 🛡️ **Fault tolerant** - Handles errors gracefully and retries failed jobs
- 📊 **Progress tracking** - Uploads statistics and artifacts after each run

### Status Report Workflow (`status-report.yml`)

**Schedule:** Runs at 6 AM UTC (4 hours after crawl starts)

**Process:**
1. Downloads the latest database
2. Generates a comprehensive status report
3. Creates or updates a GitHub Issue with the report

**Report Includes:**
- Job queue statistics
- Documents archived by category
- Database size
- Progress percentages
- Download links

## 🚀 Setup Instructions

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/yourusername/forkthelaw.git
cd forkthelaw
```

### 2. Enable GitHub Actions

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Actions** → **General**
3. Under "Actions permissions", select **Allow all actions and reusable workflows**
4. Under "Workflow permissions", select **Read and write permissions**
5. Check **Allow GitHub Actions to create and approve pull requests**
6. Click **Save**

### 3. Initial Database Seed (Optional)

You can either:

**Option A: Seed via GitHub Actions (Recommended)**

The workflow will automatically initialize and seed the database on the first run. No action needed!

**Option B: Seed Locally and Upload**

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database
python cli.py seed --all

# Create initial release
gh release create latest law_library.db.gz \
  --title "Initial Law Library Database" \
  --notes "Initial database with seeded jobs"
```

### 4. Trigger the Workflow

**Automatic:** The workflow will run daily at 2 AM UTC automatically.

**Manual:** You can trigger it immediately:

1. Go to **Actions** tab on GitHub
2. Select **Daily Law Crawler** workflow
3. Click **Run workflow** button
4. Optionally adjust the duration (default: 180 minutes)
5. Click **Run workflow**

### 5. Monitor Progress

Check the progress in several ways:

1. **Actions Tab:** View real-time logs of the running workflow
2. **Releases:** Download the latest database from the "latest" release
3. **Issues:** View the automated status report issue
4. **Artifacts:** Download run-specific database snapshots (retained for 7 days)

## 📊 Monitoring and Analytics

### View Live Logs

1. Go to **Actions** tab
2. Click on the most recent workflow run
3. Click on the **crawl** job
4. Expand the **Run crawler with timeout** step

### Download the Database

```bash
# Using GitHub CLI
gh release download latest -p 'law_library.db.gz'
gunzip law_library.db.gz

# Or download from releases page
# https://github.com/yourusername/forkthelaw/releases/latest
```

### Check Statistics Locally

```bash
python cli.py stats
```

### Query the Database

```bash
sqlite3 law_library.db

# Example queries
SELECT COUNT(*) FROM us_code;
SELECT COUNT(*) FROM cfr;
SELECT COUNT(*) FROM supreme_court_cases;
SELECT COUNT(*) FROM constitution;
SELECT COUNT(*) FROM federal_rules;
```

## ⚙️ Configuration

### Adjust Crawl Duration

Edit `.github/workflows/crawl.yml`:

```yaml
# Change the default duration (in minutes)
workflow_dispatch:
  inputs:
    duration_minutes:
      default: '180'  # Change this value
```

### Adjust Number of Workers

Edit `.github/workflows/crawl.yml`:

```yaml
# Change --workers parameter
timeout ${TIMEOUT}s python cli.py run --workers 2 --delay 10.0
#                                              ^ Change this
```

⚠️ **Warning:** Using more than 2-3 workers may violate rate limits!

### Change Schedule

Edit `.github/workflows/crawl.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Change this cron expression
  # Format: minute hour day month day-of-week
  # Examples:
  # '0 */6 * * *'   - Every 6 hours
  # '0 2,14 * * *'  - 2 AM and 2 PM daily
  # '0 2 * * 1'     - 2 AM every Monday
```

## 📈 Expected Timeline

With the current configuration (2 workers, 3 hours/day, 10-second delay):

- **US Code:** ~2,700 sections pending ÷ ~720 sections/day = **~4 days**
- **CFR:** ~300 sections pending ÷ ~720 sections/day = **<1 day**
- **Constitution:** 34 sections ÷ ~720 sections/day = **<1 day**
- **Federal Rules:** ~400 sections ÷ ~720 sections/day = **<1 day**
- **Supreme Court:** Depends on discovery results

**Total estimated time:** ~5-7 days to complete initial crawl

## 🛠️ Troubleshooting

### Workflow Fails to Download Database

**Issue:** `Error: Unable to download latest`

**Solution:** This is normal for the first run. The workflow will initialize a new database automatically.

### Database Not Updating

**Issue:** Database file size not increasing

**Solutions:**
1. Check workflow logs for errors
2. Run `python cli.py reset` in a manual workflow run
3. Check if all jobs are completed: `SELECT COUNT(*) FROM job_queue WHERE status='pending'`

### Rate Limit Errors

**Issue:** Getting HTTP 429 errors

**Solutions:**
1. Reduce workers: `--workers 1`
2. Increase delay: `--delay 15.0`
3. Reduce daily duration

### Out of Space

**Issue:** GitHub Actions runner out of disk space

**Solutions:**
1. Compress database more aggressively
2. Clean up old artifacts
3. Split into multiple databases by content type

## 🔒 Security Considerations

- **API Tokens:** The workflow uses `GITHUB_TOKEN` which is automatically provided
- **Private Repos:** Works in private repositories with the same setup
- **Rate Limits:** Be respectful of Cornell LII's servers
- **Costs:** GitHub Actions is free for public repos (2,000 minutes/month for private repos)

## 📝 Best Practices

1. **Monitor regularly:** Check the status issue weekly
2. **Backup locally:** Periodically download and backup the database
3. **Adjust as needed:** If consistently hitting timeouts, reduce workers or duration
4. **Respect the site:** Don't decrease delays below 10 seconds
5. **Clean up:** Delete old workflow runs and artifacts to save space

## 🎯 Advanced: Multiple Runs Per Day

To run multiple times per day (e.g., split 3 hours into three 1-hour sessions):

```yaml
schedule:
  - cron: '0 2 * * *'   # 2 AM UTC
  - cron: '0 10 * * *'  # 10 AM UTC
  - cron: '0 18 * * *'  # 6 PM UTC

# And adjust duration
duration_minutes:
  default: '60'  # 1 hour each
```

This can help with:
- More frequent updates
- Better distribution of load
- Faster recovery from errors

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cron Expression Generator](https://crontab.guru/)
- [GitHub Actions Pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Cornell LII robots.txt](https://www.law.cornell.edu/robots.txt)

## 🤝 Contributing

If you improve the workflows or add new features, please:

1. Test thoroughly in your fork
2. Document any configuration changes
3. Submit a pull request with a clear description
4. Update this documentation as needed

## ❓ Getting Help

If you encounter issues:

1. Check the workflow logs in the Actions tab
2. Review the status report issue
3. Search existing GitHub issues
4. Create a new issue with:
   - Workflow logs
   - Database statistics
   - Error messages
   - What you've already tried
