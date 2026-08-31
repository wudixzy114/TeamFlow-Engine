# file: test_password_setup.py
import requests
import time

# --- 配置 ---
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
UNIQUE_ID = int(time.time())

# --- 定义测试用户 ---
# 使用您指定的邮箱
USER_EMAIL = "a1631632222@163.com" 
USER_USERNAME = f"reset{UNIQUE_ID}"
INITIAL_PASSWORD = "InitialPassword123"

def run_password_reset_setup():
    """主函数，用于注册用户并请求密码重置。"""
    print("--- 启动密码重置测试准备流程 ---")

    # --- 1. 注册阶段 ---
    print(f"\n[STEP 1] 注册测试用户: {USER_EMAIL}")
    register_user(USER_EMAIL, USER_USERNAME, INITIAL_PASSWORD)

    # --- 2. 忘记密码请求 ---
    print(f"\n[STEP 2] 为邮箱 {USER_EMAIL} 请求发送密码重置验证码")
    request_password_reset(USER_EMAIL)
    
    print("\n--- 准备工作完成 ---")
    print("\n下一步操作:")
    print(f"1. 请检查您的邮箱 '{USER_EMAIL}'，找到包含6位验证码的邮件。")
    print("2. 使用下面的 curl 命令模板，在终端中手动测试重置密码功能。")

# --- API 辅助函数 ---

def register_user(email, username, password):
    """注册一个新用户用于测试。"""
    try:
        res = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register", 
            json={"email": email, "password": password, "username": username}
        )
        # 如果用户已存在 (400)，也视为成功，因为我们可以继续测试流程
        if res.status_code == 201:
            print(f"  [SUCCESS] 用户 '{username}' 注册成功。")
        elif res.status_code == 400 and "already registered" in res.text:
            print(f"  [INFO] 用户 '{username}' 已存在，继续测试。")
        else:
            # 抛出其他HTTP错误
            res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] 注册用户时发生网络错误: {e}")
        # 终止脚本，因为后续步骤无法进行
        raise

def request_password_reset(email):
    """向 /forgot-password 发送请求。"""
    try:
        res = requests.post(f"{BASE_URL}{API_PREFIX}/auth/forgot-password", json={"email": email})
        res.raise_for_status()
        print("  [SUCCESS] 成功发送密码重置请求。API 返回 200 OK。")
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] 请求密码重置时发生网络错误: {e.response.text if e.response else e}")
        print("  [HINT] 请确保您的 FastAPI 应用和 Redis 服务都在运行中。")
        # 终止脚本
        raise

if __name__ == "__main__":
    # 确保即使发生错误，程序也能正常退出
    try:
        run_password_reset_setup()
    except Exception as e:
        print(f"\n测试因错误而终止。")