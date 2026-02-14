# tests/unit/router/dependencies.py
from typing import Annotated
from unittest.mock import Mock

import pytest
from sqlmodel import Session

from botty import (
    BaseRepository,
    BaseService,
    Context,
    Depends,
    Update,
)
from botty.context import ContextProtocol
from botty.di import DependencyResolver, RequestScope
from botty.exceptions import DatabaseNotConfiguredError, DependencyResolutionError
from botty.testing import TestContext, TestDependencyContainer


# -------------------------------------------------------------------
# Test doubles
# -------------------------------------------------------------------
class UserRepo(BaseRepository):
    model = None  # not used in tests


class SettingsService(BaseService):
    pass


# -------------------------------------------------------------------
# Dependency functions for testing
# -------------------------------------------------------------------
async def simple_dep() -> str:
    return "hello"


async def nested_dep(value: Annotated[str, Depends(simple_dep)]) -> str:
    return f"nested {value}"


def sync_dep() -> int:
    return 42


# -------------------------------------------------------------------
# Handlers with different parameter names
# -------------------------------------------------------------------
async def update_handler(upd: Update, context: Context): ...


async def context_handler(update: Update, ctx: ContextProtocol): ...


async def session_handler(update: Update, context: Context, sess: Session): ...


async def repo_handler(update: Update, context: Context, repo: UserRepo): ...


async def service_handler(update: Update, context: Context, svc: SettingsService): ...


async def typed_dep_handler(
    update: Update, context: Context, value: Annotated[str, Depends(simple_dep)]
): ...


async def nested_dep_handler(
    update: Update, context: Context, value: Annotated[str, Depends(nested_dep)]
): ...


async def no_annotation_handler(update: Update, context: Context, unknown): ...


async def str_annotation_handler(update: Update, context: Context, name: str): ...


async def session_handler_no_db(update: Update, context: Context, sess: Session): ...


async def two_deps_handler(
    update: Update,
    context: Context,
    a: Annotated[str, Depends(simple_dep)],
    b: Annotated[int, Depends(sync_dep)],
): ...


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------


class TestDependencyExtraction:
    """Tests for the internal _extract_depends helper (still used by container)."""

    def test_extract_depends_returns_none_for_non_annotated(self):
        from botty.di.utils import _extract_depends

        assert _extract_depends(str) is None

    def test_extract_depends_finds_depends(self):
        from botty.di.utils import _extract_depends

        ann = Annotated[str, Depends(simple_dep)]
        dep = _extract_depends(ann)
        assert isinstance(dep, Depends)
        assert dep.dependency is simple_dep


class TestBasicInjection:
    """Test injection of built‑in types, repositories, and services."""

    @pytest.mark.parametrize(
        "handler,expected_key,expected_attr",
        [
            (update_handler, "upd", "update"),
            (context_handler, "ctx", "context"),
            (session_handler, "sess", "session"),
        ],
        ids=["update", "context", "session"],
    )
    async def test_builtin_injection(
        self, handler, expected_key, expected_attr, resolver, request_scope
    ):
        kwargs = await resolver.resolve_handler(handler, request_scope)
        expected = getattr(request_scope, expected_attr)
        assert kwargs[expected_key] is expected

    async def test_repository_injection(self, resolver, request_scope):
        kwargs = await resolver.resolve_handler(repo_handler, request_scope)
        repo = kwargs["repo"]
        assert isinstance(repo, UserRepo)
        assert repo.session is request_scope.session

    async def test_service_injection(self, resolver, request_scope):
        kwargs1 = await resolver.resolve_handler(service_handler, request_scope)
        kwargs2 = await resolver.resolve_handler(service_handler, request_scope)
        svc1 = kwargs1["svc"]
        svc2 = kwargs2["svc"]
        assert isinstance(svc1, SettingsService)
        assert svc1 is svc2  # singleton


class TestDependsAnnotation:
    """Tests for handlers that use Annotated with Depends."""

    async def test_simple_depends(self, resolver, request_scope):
        kwargs = await resolver.resolve_handler(typed_dep_handler, request_scope)
        assert kwargs["value"] == "hello"

    async def test_nested_depends(self, resolver, request_scope):
        kwargs = await resolver.resolve_handler(nested_dep_handler, request_scope)
        assert kwargs["value"] == "nested hello"

    async def test_multiple_depends(self, resolver, request_scope):
        kwargs = await resolver.resolve_handler(two_deps_handler, request_scope)
        assert kwargs["a"] == "hello"
        assert kwargs["b"] == 42


class TestCaching:
    """Tests for the caching behaviour of dependencies."""

    async def test_dependency_cached_by_default(self, container, request_scope):
        call_count = 0

        async def dep_func():
            nonlocal call_count
            call_count += 1
            return 42

        dep = Depends(dep_func, use_cache=True)

        # Resolve twice
        await container.resolve_dependency(dep, request_scope)
        await container.resolve_dependency(dep, request_scope)

        assert call_count == 1

    async def test_dependency_not_cached_if_disabled(self, container, request_scope):
        call_count = 0

        async def dep_func():
            nonlocal call_count
            call_count += 1
            return 42

        dep = Depends(dep_func, use_cache=False)

        await container.resolve_dependency(dep, request_scope)
        await container.resolve_dependency(dep, request_scope)

        assert call_count == 2

    async def test_nested_dependency_caching_respects_inner_cache_setting(
        self, container, request_scope
    ):
        inner_call_count = 0
        outer_call_count = 0

        async def inner_dep():
            nonlocal inner_call_count
            inner_call_count += 1
            return "inner"

        # outer uses cache, inner does not
        async def outer_dep(
            inner: Annotated[str, Depends(inner_dep, use_cache=True)],
        ) -> str:
            nonlocal outer_call_count
            outer_call_count += 1
            return f"outer {inner}"

        dep = Depends(outer_dep, use_cache=False)

        # Resolve twice
        await container.resolve_dependency(dep, request_scope)
        await container.resolve_dependency(dep, request_scope)

        # Inner should be called once (cache), outer result is not cached
        assert inner_call_count == 1
        assert outer_call_count == 2


class TestErrorCases:
    """Tests for error conditions during dependency resolution."""

    async def test_no_annotation_raises(self, resolver, request_scope):
        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(no_annotation_handler, request_scope)
        assert "no dependency information" in str(exc.value).lower()
        assert "Parameter 'unknown' of handler 'no_annotation_handler'" in str(
            exc.value
        )

    async def test_str_annotation_without_depends_raises(self, resolver, request_scope):
        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(str_annotation_handler, request_scope)
        assert "annotation does not contain depends" in str(exc.value).lower()

    async def test_database_not_configured_for_session(self, container):
        """Session injection fails if no database provider in bot_data."""
        update = Update(update_id=1)
        ctx = TestContext()  # no database_provider
        scope = RequestScope(update, ctx)
        resolver = DependencyResolver(container)

        with pytest.raises(DatabaseNotConfiguredError) as exc:
            await resolver.resolve_handler(session_handler_no_db, scope)  # ty: ignore [invalid-argument-type]
        assert "no database provider configured" in str(exc.value)
        assert "handler 'session_handler_no_db'" in str(exc.value)

    async def test_dependency_raises_exception_replaced(self, container, request_scope):
        async def failing_dep():
            raise ValueError("fail")

        # We need a handler that uses this dep. Create a quick one.
        async def bad_handler(update, context, x: Annotated[str, Depends(failing_dep)]):
            pass

        resolver = DependencyResolver(container)
        with pytest.raises(DependencyResolutionError):
            await resolver.resolve_handler(bad_handler, request_scope)  # ty: ignore [invalid-argument-type]

    async def test_depends_with_none_dependency_raises(self, container, request_scope):
        dep = Depends(None)  # type: ignore
        with pytest.raises(DependencyResolutionError) as exc:
            await container.resolve_dependency(dep, request_scope)
        assert "dependency function not provided" in str(exc.value).lower()


class TestContainerFeatures:
    """Tests for DependencyContainer itself (singletons, reset)."""

    def test_singleton_caches_instance(self, container):
        first = container.singleton(SettingsService)
        second = container.singleton(SettingsService)
        assert first is second

    def test_singleton_instantiates_without_args(self, container):
        class NoArgsService(BaseService):
            def __init__(self):
                self.value = 42

        svc = container.singleton(NoArgsService)
        assert svc.value == 42

    def test_container_reset_clears_singletons(self, container):
        svc1 = container.singleton(SettingsService)
        container.reset()
        svc2 = container.singleton(SettingsService)
        assert svc1 is not svc2


class TestTestDoubles:
    """Tests for the testing‑specific overrides."""

    async def test_test_container_override(self, request_scope):
        container = TestDependencyContainer()
        fake_service = Mock()

        def get_service(update, context):
            return SettingsService()

        container.override(get_service, fake_service)

        dep = Depends(get_service)
        resolved = await container.resolve_dependency(dep, request_scope)
        assert resolved is fake_service

    async def test_test_request_scope_overrides(
        self, sample_update, test_context, session
    ):
        from botty.testing.scope import TestRequestScope

        # Define a dependency function that would normally return a UserRepo
        def get_user_repo(update: Update, context: Context) -> UserRepo:
            return UserRepo(session)  # real repo

        fake_repo = Mock()

        # Handler using the dependency via Depends
        async def handler(
            update: Update,
            context: Context,
            repo: Annotated[UserRepo, Depends(get_user_repo)],
        ):
            return repo

        overrides = {get_user_repo: fake_repo}
        scope = TestRequestScope(
            update=sample_update,
            context=test_context,
            session=session,
            overrides=overrides,
        )

        container = TestDependencyContainer()
        resolver = DependencyResolver(container)
        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert kwargs["repo"] is fake_repo
