"""Shared test fixtures. pytest loads this file automatically."""

import pytest

import generate_data as gen


def make_dbs(folder, inject):
    """Build both databases in a folder, with the given bug injected into the target."""
    df = gen.build_orders()
    source, target = folder / "source.db", folder / "target.db"
    gen.write_source(df, source)
    gen.write_target(df, target, inject=inject)
    return source, target


@pytest.fixture(scope="session")
def clean_dbs(tmp_path_factory):
    return make_dbs(tmp_path_factory.mktemp("clean"), "none")


@pytest.fixture(scope="session")
def timezone_dbs(tmp_path_factory):
    return make_dbs(tmp_path_factory.mktemp("timezone"), "timezone")