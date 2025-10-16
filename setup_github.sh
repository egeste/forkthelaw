#!/bin/bash
# Script to set up GitHub repository for automated crawling

set -e

echo "======================================"
echo "GitHub Actions Setup Helper"
echo "======================================"
echo

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    echo "✓ Git repository initialized"
else
    echo "✓ Git repository already initialized"
fi

# Check if remote is set
if ! git remote get-url origin &> /dev/null; then
    echo
    echo "Please enter your GitHub repository URL:"
    echo "(e.g., https://github.com/username/forkthelaw.git)"
    read -r REPO_URL
    git remote add origin "$REPO_URL"
    echo "✓ Remote origin set to: $REPO_URL"
else
    echo "✓ Remote origin already set to: $(git remote get-url origin)"
fi

echo
echo "======================================"
echo "Checking GitHub CLI..."
echo "======================================"

if ! command -v gh &> /dev/null; then
    echo "✗ GitHub CLI (gh) not found"
    echo
    echo "Please install GitHub CLI:"
    echo "  macOS:   brew install gh"
    echo "  Linux:   See https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "  Windows: See https://github.com/cli/cli/releases"
    echo
    echo "After installation, authenticate with:"
    echo "  gh auth login"
    exit 1
else
    echo "✓ GitHub CLI found: $(gh --version | head -n1)"
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo
    echo "Authenticating with GitHub..."
    gh auth login
fi

echo
echo "======================================"
echo "Repository Status"
echo "======================================"
git status

echo
echo "======================================"
echo "Files to be committed:"
echo "======================================"
echo
echo "GitHub Actions workflows:"
echo "  .github/workflows/crawl.yml"
echo "  .github/workflows/status-report.yml"
echo
echo "Documentation:"
echo "  GITHUB_ACTIONS.md"
echo "  README.md (updated)"
echo
echo "Configuration:"
echo "  .gitignore (updated)"
echo "  requirements.txt"
echo
echo "Helper scripts:"
echo "  test_workflow.sh"
echo "  setup_github.sh"
echo

read -p "Do you want to commit and push these files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "Adding files..."
    git add .github/workflows/
    git add GITHUB_ACTIONS.md
    git add README.md
    git add .gitignore
    git add requirements.txt
    git add test_workflow.sh
    git add setup_github.sh

    # Add Python files if they exist and haven't been committed
    git add cli.py database.py jobs.py scraper.py worker.py rate_limiter.py 2>/dev/null || true

    echo
    echo "Creating commit..."
    git commit -m "Add GitHub Actions automated crawling

- Add daily crawl workflow (3 hours max)
- Add status report workflow
- Add comprehensive documentation
- Update README with GitHub Actions info
- Add helper scripts for testing and setup

The crawler will now run automatically at 2 AM UTC daily,
persisting the database via GitHub Releases."

    echo
    echo "Pushing to GitHub..."

    # Get default branch name
    BRANCH=$(git symbolic-ref --short HEAD)

    # Push to remote
    if git push -u origin "$BRANCH"; then
        echo
        echo "======================================"
        echo "✓ Successfully pushed to GitHub!"
        echo "======================================"
        echo
        echo "Next steps:"
        echo
        echo "1. Enable GitHub Actions:"
        echo "   → Go to: $(git remote get-url origin | sed 's/\.git$//')/settings/actions"
        echo "   → Enable 'Allow all actions and reusable workflows'"
        echo "   → Enable 'Read and write permissions'"
        echo
        echo "2. Trigger first workflow run:"
        echo "   → Go to: $(git remote get-url origin | sed 's/\.git$//')/actions"
        echo "   → Select 'Daily Law Crawler'"
        echo "   → Click 'Run workflow'"
        echo
        echo "3. Or trigger via CLI:"
        echo "   → gh workflow run crawl.yml"
        echo
        echo "4. Monitor progress:"
        echo "   → Actions tab: $(git remote get-url origin | sed 's/\.git$//')/actions"
        echo "   → Releases: $(git remote get-url origin | sed 's/\.git$//')/releases"
        echo
    else
        echo
        echo "✗ Failed to push to GitHub"
        echo "Please check your remote URL and permissions"
        exit 1
    fi
else
    echo
    echo "Commit cancelled. To commit manually:"
    echo "  git add .github/ GITHUB_ACTIONS.md README.md"
    echo "  git commit -m 'Add GitHub Actions automated crawling'"
    echo "  git push"
fi

echo
echo "======================================"
echo "Setup Complete!"
echo "======================================"
