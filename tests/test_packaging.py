"""
Tests for the package's declared metadata.

The supported Python and Django versions are a decision recorded in
`docs/adr/0001-supported-python-and-django-versions.md`. Four places restate it: the runtime
constraint in `pyproject.toml`, the `Framework :: Django` classifiers, `requires-python`, and the
README's Requirements section. They are meant to agree at all times.

They drifted once and nobody noticed until a consumer could not install the package: an automated
dependency update rewrote the runtime constraint from `django>=5.2` to `django>=6.1.1` while the
classifiers, the README and the test matrix went on claiming 5.2 and 6.0. The declared floor is a
statement about the range this library supports, so raising it to whatever version happened to be
newest excluded every consumer on a version the suite still tests.

These tests read the metadata as published and fail when the four stop agreeing.
"""

import re
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def pyproject():
    """The parsed contents of the package's pyproject.toml."""
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def readme():
    """The raw text of the README."""
    return (REPO_ROOT / "README.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def django_requirement(pyproject):
    """The declared runtime requirement on Django."""
    requirements = [
        Requirement(entry) for entry in pyproject["project"]["dependencies"]
    ]
    by_name = {requirement.name: requirement for requirement in requirements}
    assert "django" in by_name, "Django is no longer declared as a runtime dependency"
    return by_name["django"]


@pytest.fixture(scope="module")
def classified_django_versions(pyproject):
    """The Django versions claimed by the `Framework :: Django :: X.Y` classifiers."""
    versions = [
        Version(classifier.removeprefix("Framework :: Django :: ").strip())
        for classifier in pyproject["project"]["classifiers"]
        if re.fullmatch(r"Framework :: Django :: \d+\.\d+", classifier)
    ]
    assert versions, "no `Framework :: Django :: X.Y` classifiers are declared"
    return sorted(versions)


class TestDjangoSupportRange:
    """The declared Django range agrees with every version the package claims to support."""

    def test_every_classified_version_can_be_installed(
        self, django_requirement, classified_django_versions
    ):
        """A version listed in the classifiers must satisfy the runtime constraint."""
        excluded = [
            str(version)
            for version in classified_django_versions
            if not django_requirement.specifier.contains(version)
        ]
        assert not excluded, (
            f"the classifiers claim Django {', '.join(excluded)}, which "
            f"'{django_requirement}' will not install"
        )

    def test_the_floor_is_the_lowest_classified_version(
        self, django_requirement, classified_django_versions
    ):
        """The lower bound names the oldest supported release rather than a newer one."""
        lower_bounds = [
            Version(specifier.version)
            for specifier in django_requirement.specifier
            if specifier.operator == ">="
        ]
        assert len(lower_bounds) == 1, (
            f"expected exactly one lower bound, got '{django_requirement.specifier}'"
        )
        assert lower_bounds[0] == classified_django_versions[0], (
            f"the floor is Django {lower_bounds[0]} but the oldest classified version is "
            f"{classified_django_versions[0]}; raising the floor drops support and belongs in "
            f"docs/adr/0001-supported-python-and-django-versions.md, not in a dependency update"
        )

    def test_the_readme_states_the_classified_versions(
        self, readme, classified_django_versions
    ):
        """The README's Requirements section names the same Django versions as the classifiers."""
        sections = readme.split("## Requirements", 1)
        assert len(sections) == 2, (
            "the README has no `## Requirements` section; it is one of the places the "
            "supported versions are stated, so renaming it needs this test renamed too"
        )
        requirements_section = sections[1].split("\n## ", 1)[0]
        stated = {
            Version(match) for match in re.findall(r"\d+\.\d+", requirements_section)
        }
        missing = [
            str(version)
            for version in classified_django_versions
            if version not in stated
        ]
        assert not missing, (
            f"the README's Requirements section does not mention Django {', '.join(missing)}"
        )


class TestPythonSupportRange:
    """`requires-python` agrees with the Python versions the classifiers claim."""

    def test_every_classified_version_can_be_installed(self, pyproject):
        """A Python version listed in the classifiers must satisfy `requires-python`."""
        specifier = SpecifierSet(pyproject["project"]["requires-python"])
        versions = [
            Version(
                classifier.removeprefix("Programming Language :: Python :: ").strip()
            )
            for classifier in pyproject["project"]["classifiers"]
            if re.fullmatch(r"Programming Language :: Python :: \d+\.\d+", classifier)
        ]
        assert versions, (
            "no `Programming Language :: Python :: X.Y` classifiers are declared"
        )
        excluded = [
            str(version) for version in versions if not specifier.contains(version)
        ]
        assert not excluded, (
            f"the classifiers claim Python {', '.join(excluded)}, which "
            f"requires-python '{specifier}' will not install"
        )
