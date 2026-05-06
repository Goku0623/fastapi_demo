# =============================================================================
# test_book.py — 书籍相关接口的单元测试
# =============================================================================
# 本文件测试 /api/v1/books 下的接口。
# 包含 4 个测试：获取全部书籍、创建书籍、获取单本书、更新书籍。
# =============================================================================

from src.books.schemas import BookCreateModel
# ↑ BookCreateModel 是 Pydantic 模型，定义了创建书籍需要的字段
#   （title, author, publisher, published_date, page_count, language）

# --- 定义接口路径前缀 ---
books_prefix = "/api/v1/books"


# =============================================================================
# 测试1：获取全部书籍 — GET /api/v1/books
# =============================================================================
def test_get_all_books(test_client, fake_book_service, fake_session):
    # 参数说明（全部由 pytest 自动注入）：
    #   test_client       — FastAPI 测试客户端
    #   fake_book_service — 假的书籍服务（Mock 对象）
    #   fake_session      — 假的数据库会话（Mock 对象）

    # --- 发送 GET 请求 ---
    response = test_client.get(
        url=f"{books_prefix}"
        # ↑ 请求 /api/v1/books，对应路由中的 get_all_books()
    )
    # ↑ GET 请求没有请求体，所以不需要 json= 参数

    # --- 断言：验证服务层方法被正确调用 ---
    assert fake_book_service.get_all_books_called_once()
    # ↑ 验证 get_all_books 方法被调用了一次
    #   对应路由代码：books = await book_service.get_all_books(session)

    assert fake_book_service.get_all_books_called_once_with(fake_session)
    # ↑ 验证 get_all_books 被调用时传入了 fake_session 作为参数


# =============================================================================
# 测试2：创建书籍 — POST /api/v1/books
# =============================================================================
def test_create_book(test_client, fake_book_service, fake_session):
    # --- 构造创建书籍的数据 ---
    book_data = {
        "title": "Test Title",
        "author": "Test Author",
        "publisher": "Test Publications",
        "published_date": "2024-12-10",
        "language": "English",
        "page_count": 215
    }
    # ↑ 模拟前端发送的 JSON 数据

    # --- 发送 POST 请求 ---
    response = test_client.post(
        url=f"{books_prefix}",
        # ↑ 请求 /api/v1/books，对应路由中的 create_a_book()
        json=book_data
        # ↑ 把 book_data 作为 JSON 请求体发送
    )

    # --- 将字典转换为 Pydantic 模型（用于断言参数匹配） ---
    book_create_data = BookCreateModel(**book_data)
    # ↑ ** 字典解包，等价于：
    #   BookCreateModel(
    #       title="Test Title",
    #       author="Test Author",
    #       publisher="Test Publications",
    #       published_date="2024-12-10",
    #       language="English",
    #       page_count=215
    #   )

    # --- 断言：验证服务层方法被正确调用 ---
    assert fake_book_service.create_book_called_once()
    # ↑ 验证 create_book 方法被调用了一次
    #   对应路由代码：new_book = await book_service.create_book(book_data, user_id, session)

    assert fake_book_service.create_book_called_once_with(
        book_create_data,  # 第一个参数：BookCreateModel 实例
        fake_session       # 第二个参数：数据库会话
    )
    # ↑ 验证 create_book 的参数正确


# =============================================================================
# 测试3：根据 UID 获取单本书 — GET /api/v1/books/{book_uid}
# =============================================================================
def test_get_book_by_uid(test_client, fake_book_service, test_book, fake_session):
    # 参数说明：
    #   test_book — conftest.py 中定义的 fixture，一个预先构造好的 Book 对象
    #               这里用它的 uid 来构造请求路径

    # --- 发送 GET 请求，路径中包含书籍的 UID ---
    response = test_client.get(f"{books_prefix}/{test_book.uid}")
    # ↑ f"{books_prefix}/{test_book.uid}" 会生成类似 /api/v1/books/550e8400-...
    #   对应路由中的 get_book(book_uid: str)

    # --- 断言：验证服务层方法被正确调用 ---
    assert fake_book_service.get_book_called_once()
    # ↑ 验证 get_book 方法被调用了一次
    #   对应路由代码：book = await book_service.get_book(book_uid, session)

    assert fake_book_service.get_book_called_once_with(
        test_book.uid,  # 第一个参数：书籍的 UID
        fake_session    # 第二个参数：数据库会话
    )
    # ↑ 验证 get_book 的参数正确，特别是 UID 匹配


# =============================================================================
# 测试4：更新书籍 — PUT /api/v1/books/{book_uid}
# =============================================================================
def test_update_book_by_uid(test_client, fake_book_service, test_book, fake_session):
    # --- 发送 PUT 请求 ---
    response = test_client.put(f"{books_prefix}/{test_book.uid}")
    # ↑ PUT 方法用于更新资源，对应路由中的 update_book()
    #   注意：这个测试没有传请求体（实际路由需要 book_update_data），
    #   但因为所有依赖都被 Mock 了，请求仍然能"通过"

    # --- 断言：验证服务层方法被正确调用 ---
    assert fake_book_service.get_book_called_once()
    # ↑ 验证 get_book 被调用（更新前需要先查出原记录）
    #   对应路由代码：book_to_update = await self.get_book(book_uid, session)

    assert fake_book_service.get_book_called_once_with(
        test_book.uid,  # 第一个参数：书籍的 UID
        fake_session    # 第二个参数：数据库会话
    )
    # ↑ 验证 get_book 的参数正确

