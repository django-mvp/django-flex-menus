# ADR 0001 — Supported Python and Django versions

**Status:** accepted

## Decision

The package supports Python 3.12 and above, and Django 5.2 or later.

The tested matrix is Python 3.12 and 3.13 against Django 5.2 and 6.0 — the same matrix every
package in this family runs, so that a toolchain change is tested once rather than per repo.

`requires-python`, the `django` constraint in `pyproject.toml`, the classifiers, and the README's
Requirements section all say this, and they move together. A version that is claimed as tested is
a version the matrix runs.

Widening or narrowing the range is a deliberate change to this record, not a side effect of a
dependency bump.

## Why

The package previously declared `python >=3.11` and `django >=4.2,<5.3` while testing Python 3.12
and 3.13 against Django 5.0, 5.1 and 5.2. Several of the claimed combinations had never been run.
Python 3.11 could not have worked in development at all: the documentation toolchain requires
3.12, so dependency resolution failed outright below it — which is what had been breaking the
weekly dependency-update job every week.

Two options were open. Test everything that was claimed, which means a matrix covering Django
versions their own maintainers no longer support. Or claim what is tested.

The second is the honest one. Django 4.2, 5.0 and 5.1 all sit in the project's unsupported list
and receive neither bug fixes nor security updates. Carrying them costs matrix time on every push
and buys a consumer nothing they should be relying on.

Raising the Python floor to 3.12 costs nothing here: nobody could have been installing this
package on 3.11 alongside its own tooling.

The runtime constraint is deliberately `>=5.2` with no ceiling, while the matrix stops at 6.0.
Django 6.1 is released and supported, so a consumer on it can install the package — it is simply
not one of the combinations tested here. Closing that gap means moving the family matrix, which
belongs in the shared workflow rather than in this repository.

## Revisit if

The family matrix moves — the tested versions follow it rather than being chosen here. Also
revisit if a consumer turns up who is genuinely pinned to Django 5.1 or Python 3.11 and cannot
move: the decision assumes nobody is relying on a claim that was never tested.
