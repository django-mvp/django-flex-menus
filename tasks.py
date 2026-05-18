from invoke import task


@task
def test(c, tox=False):
    """
    Run the test suite
    """
    if tox:
        print("🚀 Testing code: Running pytest with all tests")
        c.run("tox")
    else:
        print("🚀 Testing code: Running pytest")
        c.run("poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html")


@task
def docs(c):
    """
    Build the documentation and open it in the browser
    """
    # c.run("sphinx-apidoc -M -T -o docs/ flex_menu **/migrations/* -e --force -d 2")
    c.run("sphinx-build -E -b html docs docs/_build")


@task
def prerelease(c):
    """
    Run comprehensive pre-release checks and update all required files.

    This task performs all necessary steps to prepare the repository for release:
    1. Run linting, formatting, type checking, and dependency checks via pre-commit hooks
    2. Run quality checks and tests

    Use this before running the release task to ensure everything is ready.

    Pre-commit hooks include:
    - Code formatting (Black, Ruff)
    - Type checking (mypy)
    - Dependency analysis (deptry)
    - Poetry validation
    """
    print("🚀 Starting comprehensive pre-release checks...")
    print("=" * 60)

    # Step 1: Run comprehensive linting, type checking, and dependency analysis
    print(
        "\n🧹 Step 1: Running comprehensive linting, type checking, and dependency analysis"
    )
    print("🚀 Running pre-commit hooks (includes mypy and deptry)")
    c.run("poetry run pre-commit run -a")

    print("🚀 Running manual pre-commit hooks (poetry-lock)")
    c.run("poetry run pre-commit run --hook-stage manual -a")

    # Step 2: Check Poetry lock file consistency
    print("\n🔍 Step 2: Checking Poetry lock file consistency")
    print("🚀 Checking Poetry lock file consistency with 'pyproject.toml'")
    c.run("poetry check --lock")

    # Step 3: Run comprehensive test suite
    print("\n🧪 Step 3: Running comprehensive test suite")
    print("🚀 Running pytest with coverage")
    c.run(
        "poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html --cov-report=term --tb=no -qq"
    )

    print("\n" + "=" * 60)
    print("✅ Pre-release checks completed successfully!")
    print(
        "🎉 Repository is ready for release. You can now run 'invoke release' with the appropriate rule."
    )
    print("   Example: invoke release --rule=patch")


@task
def release(c, rule="", commit_staged=False, retry=False):
    """
    Create a new git tag and push it to trigger a PyPI release.

    Pushing a version tag triggers the Release workflow, which builds and
    publishes the package to PyPI and creates a GitHub Release.

    Args:
        rule: Version bump rule (major, minor, patch, etc.)
        commit_staged: If True, commit staged changes alongside the version bump
        retry: If True, delete local/remote tag and re-push at HEAD (use after
               fixing a failed CI run — no version bump, no new commit)

    RULE        BEFORE  AFTER
    major       1.3.0   2.0.0
    minor       2.1.4   2.2.0
    patch       4.1.1   4.1.2
    premajor    1.0.2   2.0.0a0
    preminor    1.0.2   1.1.0a0
    prepatch    1.0.2   1.0.3a0
    prerelease  1.0.2   1.0.3a0
    prerelease  1.0.3a0 1.0.3a1
    prerelease  1.0.3b0 1.0.3b1

    Examples:
        invoke release --rule=patch    # bump patch version and release
        invoke release --retry         # re-push existing tag after fixing CI
    """
    if retry:
        version_short = c.run("poetry version -s", hide=True).stdout.strip()
        version = c.run("poetry version", hide=True).stdout.strip()
        tag = f"v{version_short}"
        print(f"♻️  Retrying release for {tag}...")
        response = (
            input(
                f"This will delete local and remote tag {tag} and re-push it at HEAD. Continue? (y/N): "
            )
            .strip()
            .lower()
        )
        if response not in ("y", "yes"):
            print("❌ Retry cancelled.")
            return
        c.run(f"git tag -d {tag}", warn=True)
        c.run(f"git push origin :refs/tags/{tag}", warn=True)
        c.run(f'git tag -a {tag} -m "{version}"')
        c.run("git push origin main --follow-tags")
        print(f"✅ Tag {tag} re-pushed — Release workflow retriggered!")
        return

    if not rule:
        print("❌ Error: You must specify a version bump rule (or use --retry).")
        print("   Example: invoke release --rule=patch")
        print(
            "\n   Available rules: major, minor, patch, premajor, preminor, prepatch, prerelease"
        )
        return

    # Bump the current version using the specified rule
    c.run(f"poetry version {rule}")

    # 1. Get the current version number as a variable
    version_short = c.run("poetry version -s", hide=True).stdout.strip()
    version = c.run("poetry version", hide=True).stdout.strip()

    # 2. Commit the changes to pyproject.toml (and optionally staged changes)
    if commit_staged:
        staged_result = c.run("git diff --cached --name-only", hide=True, warn=True)
        if staged_result.stdout.strip():
            print(f"🚀 Committing staged changes and version bump for v{version_short}")
            c.run(f'git add pyproject.toml && git commit -m "Release v{version_short}"')
        else:
            print(
                f"🚀 No staged changes found, committing only version bump for v{version_short}"
            )
            c.run(f'git commit pyproject.toml -m "Release v{version_short}"')
    else:
        c.run(f'git commit pyproject.toml -m "Release v{version_short}"')

    # 3. Create an annotated tag and push commit + tag together
    c.run(f'git tag -a v{version_short} -m "{version}"')
    c.run("git push origin main --follow-tags")
    print(
        f"✅ Release v{version_short} tagged and pushed — Release workflow triggered!"
    )


@task
def live_docs(c):
    """
    Build the documentation and open it in a live browser
    """
    c.run(
        "sphinx-autobuild -b html --host 0.0.0.0 --port 9000 --watch . -c . . _build/html"
    )
