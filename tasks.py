from invoke import task


@task
def test(c):
    """
    Run the test suite
    """
    print("🚀 Testing code: Running pytest")
    c.run("poetry run pytest --cov=flex_menu --cov-report=html --cov-report=term")


@task
def docs(c):
    """
    Build the documentation and open it in the browser
    """
    c.run("poetry run sphinx-build -E -b html docs docs/_build")


@task
def check(c):
    """
    Run every gate CI runs, in the same order, before opening a pull request.

    1. pre-commit: ruff lint, ruff format, mypy, deptry, Poetry validation
    2. Poetry lock file consistency
    3. The test suite with coverage
    """
    print("🚀 Starting checks...")
    print("=" * 60)

    print("\n🧹 Step 1: Linting, formatting, type checking and dependency analysis")
    c.run("poetry run pre-commit run -a")

    print("\n🔒 Step 1b: Refreshing the lock file (manual-stage hooks)")
    c.run("poetry run pre-commit run --hook-stage manual -a")

    print("\n🔍 Step 2: Checking Poetry lock file consistency with 'pyproject.toml'")
    c.run("poetry check --lock")

    print("\n🧪 Step 3: Running the test suite with coverage")
    c.run("poetry run pytest --cov=flex_menu --cov-report=term --tb=no -qq")

    print("\n" + "=" * 60)
    print("✅ All checks passed.")
    print("   Releases are cut by dispatching the Prepare Release workflow — see AGENTS.md.")


@task
def live_docs(c):
    """
    Build the documentation and serve it with live reload
    """
    c.run("poetry run sphinx-autobuild -b html --host 0.0.0.0 --port 9000 --watch . -c . . _build/html")
