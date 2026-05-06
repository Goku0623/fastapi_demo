# =============================================================================
# test_auth.py — 用户认证相关接口的单元测试
# =============================================================================
# 本文件测试 /api/v1/auth 下的接口。
# 目前只有一个测试：用户注册（POST /api/v1/auth/sign_up）。
# =============================================================================

from src.auth.schemas import UserCreateModel
# ↑ UserCreateModel 是 Pydantic 模型，定义了注册时需要哪些字段（username, email, password）

# --- 定义接口路径前缀 ---
auth_prefix = f"/api/v1/auth"
# ↑ f"/api/v1/auth" 是 f-string（格式化字符串），这里没有变量所以和普通字符串一样。
#   写成 f-string 是为了方便以后加变量，比如 f"/api/{version}/auth"


def test_user_creation(fake_session, fake_user_service, test_client):
    # =========================================================================
    # 测试：用户注册接口 POST /api/v1/auth/sign_up
    # =========================================================================
    # 参数说明（全部由 pytest 自动注入，来自 conftest.py 中的 fixture）：
    #   fake_session       — 假的数据库会话（Mock 对象）
    #   fake_user_service  — 假的用户服务（Mock 对象）
    #   test_client        — FastAPI 测试客户端（TestClient 实例）
    #
    # 测试思路：
    #   1. 构造一份注册数据
    #   2. 用 TestClient 发送 POST 请求到 /api/v1/auth/sign_up
    #   3. 验证服务层的 user_exists() 被调用了（检查邮箱是否已存在）
    #   4. 验证服务层的 create_user() 被调用了（创建新用户）
    #   5. 验证调用时的参数是正确的
    # =========================================================================

    # --- 第1步：构造注册数据 ---
    sign_up_data = {
        "email": "1157107351@qq.com",
        "username": "goku",
        "password": "asd123456"
    }
    # ↑ 这是一个普通的 Python 字典，模拟前端发送的 JSON 数据

    # --- 第2步：发送 POST 请求 ---
    response = test_client.post(
        url=f"{auth_prefix}/sign_up",
        # ↑ 拼接出完整路径：/api/v1/auth/sign_up
        json=sign_up_data
        # ↑ json= 参数告诉 TestClient：把 sign_up_data 序列化为 JSON 放在请求体中
        #   等价于 HTTP 请求头 Content-Type: application/json
    )
    # ↑ response 是请求的响应对象，包含 status_code、json() 等信息
    #   虽然这个测试没有检查 response 的内容，但发送请求本身就会触发路由逻辑

    # --- 第3步：将字典转换为 Pydantic 模型（用于后续断言） ---
    user_data = UserCreateModel(**sign_up_data)
    # ↑ ** 是 Python 的"字典解包"操作符
    #   UserCreateModel(**sign_up_data) 等价于：
    #   UserCreateModel(
    #       email="1157107351@qq.com",
    #       username="goku",
    #       password="asd123456"
    #   )
    #   为什么要转换？因为路由内部会把 JSON 自动解析为 UserCreateModel，
    #   所以传给 create_user() 的也是 UserCreateModel 实例，
    #   断言时需要用相同类型的对象来匹配。

    # --- 第4步：断言（assert）—— 验证服务层方法是否被正确调用 ---

    # 断言1：验证 user_exists 方法被调用了一次
    assert fake_user_service.user_exists_called_once()
    # ↑ 这是 Mock 对象自动生成的方法！
    #   Mock 会记录所有对它的调用。当你调用 m.foo() 后，
    #   m.foo_called_once() 会检查 foo 是否恰好被调用了一次。
    #   如果没调用或调用了多次，断言失败。
    #
    #   对应路由中的代码：
    #     user_exists = await user_service.user_exists(email, session)

    # 断言2：验证 user_exists 被调用时的参数是 (email, session)
    assert fake_user_service.user_exists_called_once_with(
        sign_up_data["email"],  # 第一个参数：邮箱地址
        fake_session             # 第二个参数：数据库会话
    )
    # ↑ called_once_with 也是 Mock 自动生成的方法。
    #   它检查方法是否恰好被调用一次，且参数完全匹配。
    #   如果参数不对（比如传了不同的 email），断言失败。

    # 断言3：验证 create_user 方法被调用了一次
    assert fake_user_service.create_user_called_once()
    # ↑ 对应路由中的代码：
    #     new_user = await user_service.create_user(user_data, session)

    # 断言4：验证 create_user 被调用时的参数是 (user_data, session)
    assert fake_user_service.create_user_called_once_with(
        user_data,      # 第一个参数：UserCreateModel 实例
        fake_session    # 第二个参数：数据库会话
    )
    # ↑ 这里 user_data 是 UserCreateModel 对象，
    #   和路由内部 Pydantic 自动解析出的对象字段值相同，所以能匹配。

    # =========================================================================
    # 测试通过条件：以上 4 个 assert 全部为 True
    # 任何一个 assert 失败，pytest 都会报告 AssertionError，测试标记为 FAILED
    # =========================================================================