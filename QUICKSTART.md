# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Automated GitHub Actions (Recommended)

1. **Run the setup script:**
   ```bash
   ./setup_github.sh
   ```

2. **Enable GitHub Actions** (visit the link provided by the script)

3. **Done!** The crawler runs automatically at 2 AM UTC daily.

### Option 2: Manual Local Crawling

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Seed the database:**
   ```bash
   python cli.py seed --all
   ```

3. **Start crawling:**
   ```bash
   python cli.py run --workers 2
   ```

## 📊 Check Progress

### GitHub Actions
```bash
# View workflow status
gh run list --workflow=crawl.yml

# Download latest database
gh release download latest -p 'law_library.db.gz'
gunzip law_library.db.gz
```

### Local
```bash
# View statistics
python cli.py stats

# Query database
sqlite3 law_library.db "SELECT COUNT(*) FROM us_code"
```

## ⚙️ Configuration

### Change crawl duration (GitHub Actions)
Edit `.github/workflows/crawl.yml`:
```yaml
duration_minutes:
  default: '180'  # Change from 180 minutes (3 hours)
```

### Change workers
Edit `.github/workflows/crawl.yml`:
```yaml
python cli.py run --workers 2  # Change from 2
```

### Change schedule
Edit `.github/workflows/crawl.yml`:
```yaml
schedule:
  - cron: '0 2 * * *'  # 2 AM daily (change as needed)
```

## 🎯 Content Types

Seed specific content:
```bash
python cli.py seed --uscode          # US Code
python cli.py seed --cfr             # Code of Federal Regulations
python cli.py seed --scotus          # Supreme Court Cases
python cli.py seed --constitution    # US Constitution
python cli.py seed --federal_rules   # Federal Rules
python cli.py seed --all             # Everything
```

## 🔧 Troubleshooting

### Stuck jobs
```bash
python cli.py reset
```

### Rate limit issues
Increase delay between requests:
```bash
python cli.py run --workers 1 --delay 15.0
```

### Download latest database
```bash
gh release download latest -p 'law_library.db.gz'
gunzip law_library.db.gz
```

## 📚 Documentation

- **Full README:** [README.md](README.md)
- **GitHub Actions Guide:** [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)
- **Test Workflow:** Run `./test_workflow.sh` before pushing

## 🆘 Need Help?

1. Check workflow logs: Actions tab → Daily Law Crawler → latest run
2. View status report: Check the pinned issue
3. Read the docs: [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)
4. Create an issue with logs and error messages

## ⏱️ Expected Timeline

With default settings (2 workers, 3 hours/day):

- **Constitution:** <1 day
- **Federal Rules:** <1 day
- **CFR:** <1 day
- **US Code:** ~4 days
- **Complete archive:** ~5-7 days

## 💡 Pro Tips

1. **Run test first:** `./test_workflow.sh` (3-minute test)
2. **Monitor regularly:** Check status report issue
3. **Backup locally:** Download database weekly
4. **Be respectful:** Don't decrease rate limits
5. **Multiple runs:** Split into 3×1 hour runs for faster progress

## 🎉 Success!

Once set up, the crawler runs completely automatically:
- ✅ Downloads continue from where they left off
- ✅ Database persists between runs
- ✅ Status reports keep you informed
- ✅ No local resources needed

Sit back and let GitHub Actions do the work!
