# =============================================================================
# conftest.py — pytest 的公共配置文件
# =============================================================================
# 这个文件是 pytest 框架的特殊文件，pytest 运行测试时会自动发现并加载它。
# 它的作用是：定义所有测试文件共享的 Mock 对象和 Fixture（测试夹具）。
# 你不需要在任何测试文件中手动 import conftest，pytest 会自动处理。
# =============================================================================

# --- 导入真实依赖（用于后续替换） ---
from src.db.main import get_session
# ↑ get_session 是真实的数据库会话生成器，测试时会被替换成假的

from src.auth.dependencies import AccessTokenBearer, RoleChecker, RefreshTokenBearer
# ↑ 这三个是真实的权限校验类，测试时也会被替换成 Mock

from src.db.models import Book
# ↑ Book 是真实的数据库模型类，用于构造测试数据

from src import app
# ↑ app 是真实的 FastAPI 应用实例，TestClient 需要它来发送请求

# --- 导入测试工具 ---
from fastapi.testclient import TestClient
# ↑ TestClient：FastAPI 提供的测试客户端，可以在不启动真实服务器的情况下发送 HTTP 请求

from datetime import datetime
# ↑ datetime：用于给测试数据设置时间字段

from unittest.mock import Mock
# ↑ Mock：Python 标准库提供的"模拟对象"，可以假装成任何东西
#   它的神奇之处在于：你调用它的任何方法，它都会自动记录下来，
#   之后可以用 assert_xxx 来验证"这个方法是否被调用了"、"调用参数是什么"

import pytest
# ↑ pytest：Python 最流行的测试框架

import uuid
# ↑ uuid：用于生成全局唯一的随机 ID


# =============================================================================
# 创建全局 Mock 对象（"假货"）
# =============================================================================
# 这些 Mock 对象会替代真实的数据库会话、用户服务、书籍服务。
# 测试时，所有对数据库的操作实际上都发生在这些 Mock 对象上，
# 不会产生任何真实的副作用（不会真的写数据库、不会真的发邮件）。

mock_session = Mock()
# ↑ 假的数据库会话，替代真实的 AsyncSession

mock_user_service = Mock()
# ↑ 假的用户服务，替代真实的 UserService

mock_book_service = Mock()
# ↑ 假的书籍服务，替代真实的 BookService


# =============================================================================
# 假的数据库会话生成器
# =============================================================================
# FastAPI 的 Depends() 要求依赖函数是生成器（用 yield 而不是 return），
# 这样框架可以在请求结束后执行清理代码。
# 这里用 yield 返回 mock_session，模拟真实 get_session 的行为。

def get_mock_session():
    yield mock_session


# =============================================================================
# 创建真实的依赖实例（仅用于注册到 dependency_overrides 中作为 key）
# =============================================================================
# 注意：这里创建的是"真实的"实例，但它们只是用来作为字典的 key。
# 真正生效的是 dependency_overrides 字典中的 value（即 Mock 对象）。

access_token_bearer = AccessTokenBearer()
# ↑ 访问令牌校验器实例

refresh_token_bearer = RefreshTokenBearer()
# ↑ 刷新令牌校验器实例

role_checker = RoleChecker(['admin'])
# ↑ 角色校验器实例，要求用户具有 'admin' 角色


# =============================================================================
# FastAPI 依赖覆盖（dependency_overrides）—— 测试的核心魔法
# =============================================================================
# dependency_overrides 是一个字典，它的作用是：
#   "当路由需要某个依赖时，不要给它真的，给它这个假的。"
#
# 例如：路由中有 session: AsyncSession = Depends(get_session)
#   正常运行时 → 给一个真实的数据库连接
#   测试运行时 → 给 mock_session（因为 dependency_overrides 替换了 get_session）

app.dependency_overrides[get_session] = get_mock_session
# ↑ 把真实的 get_session 替换成 get_mock_session
#   现在所有路由拿到的 session 都是 mock_session

app.dependency_overrides[role_checker] = Mock()
# ↑ 把真实的 role_checker 替换成一个 Mock 对象
#   现在所有路由的角色校验都会"假装通过"

app.dependency_overrides[refresh_token_bearer] = Mock()
# ↑ 把真实的 refresh_token_bearer 替换成一个 Mock 对象
#   现在所有路由的刷新令牌校验都会"假装通过"


# =============================================================================
# Fixture 定义（测试夹具）
# =============================================================================
# @pytest.fixture 是 pytest 的核心装饰器。
# 被它标记的函数就是一个"fixture"（测试夹具）。
#
# 工作原理：
#   当测试函数参数中有 fixture 的名字时，pytest 会自动调用该 fixture 函数，
#   把返回值传给测试函数。这就是"依赖注入"。
#
# 例如：def test_xxx(fake_session, test_client):
#   pytest 会自动调用 fake_session() 和 test_client()，把结果传入。

@pytest.fixture
def fake_session():
    """返回假的数据库会话，供测试函数使用"""
    return mock_session


@pytest.fixture
def fake_user_service():
    """返回假的用户服务，供测试函数使用"""
    return mock_user_service


@pytest.fixture
def fake_book_service():
    """返回假的书籍服务，供测试函数使用"""
    return mock_book_service


@pytest.fixture
def test_client():
    """返回 FastAPI 测试客户端，用于发送 HTTP 请求"""
    return TestClient(app)


@pytest.fixture
def test_book():
    """返回一个预先构造好的 Book 对象，用于测试"获取单本书"等场景"""
    return Book(
        uid=uuid.uuid4(),
        # ↑ uuid.uuid4() 生成一个随机的 UUID（如 550e8400-e29b-41d4-a716-446655440000）
        user_uid=uuid.uuid4(),
        title="test-title",
        description="test-description",
        page_count=200,
        language="中文",
        published_date=datetime.now(),
        # ↑ datetime.now() 获取当前时间
        update_at=datetime.now()
    )