#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re, sys, time, json, requests
from seleniumbase import SB

# ===== 环境变量 =====
EMAIL       = os.environ.get("EMAIL") or ""
PASSWORD    = os.environ.get("PASSWORD") or ""
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""
TG_CHAT_ID  = os.environ.get("TG_CHAT_ID") or ""
HEADLESS    = os.environ.get("HEADLESS", "true").lower() == "true"

# 代理（由 workflow 中 setup_proxy.sh 设置）
IS_PROXY       = os.environ.get("IS_PROXY", "false").lower() == "true"
PROXY_SERVER   = os.environ.get("PROXY_SERVER", "").strip() or "http://127.0.0.1:1080"

BASE_URL = "https://client.therose.cloud/login"

if not EMAIL or not PASSWORD:
    print("❌ 请设置环境变量 EMAIL 和 PASSWORD")
    sys.exit(1)


# ===== 工具函数 =====

def send_tg(token, chat_id, message):
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        print("📨 Telegram 通知已发送")
    except Exception as e:
        print(f"❌ Telegram 发送失败: {e}")


def get_current_ip(proxy_server=""):
    """获取当前出口 IP"""
    proxies = None
    if proxy_server:
        proxies = {"http": proxy_server, "https": proxy_server}
    try:
        resp = requests.get("https://api.ip.sb/ip", proxies=proxies, timeout=15)
        return resp.text.strip()
    except Exception as e:
        return f"获取失败: {e}"


# ===== CF Turnstile 处理（移植自 Auto-Renew-Bothosting）=====

def wait_for_turnstile_pass(sb, timeout=30):
    """
    等待 Turnstile 验证通过。
    通过检测页面源码中是否还存在 CF 相关关键词来判断。
    """
    start = time.time()
    cf_indicators = [
        "verify you are human",
        "确认您是真人",
        "troubleshoot",
        "just a moment",
        "cf-browser-verification",
        "challenge-platform",
    ]
    while time.time() - start < timeout:
        try:
            page_lower = sb.get_page_source().lower()
            if not any(x.lower() in page_lower for x in cf_indicators):
                print("✅ Turnstile 验证已通过")
                return True
        except Exception:
            pass
        sb.sleep(1)
    print("❌ Turnstile 验证超时未通过")
    return False


def handle_turnstile(sb, max_attempts=3, click_delay=8):
    """
    完整处理 Turnstile 验证：点击 → 等待 → 验证 → 重试。
    移植自 Auto-Renew-Bothosting 的方案。
    """
    print("🔒 检测 Turnstile 验证...")
    for attempt in range(1, max_attempts + 1):
        print(f"🔄 第 {attempt} 次尝试点击 Turnstile...")
        try:
            # 优先 WebDriver 方式（headless 兼容）
            sb.uc_click_captcha(timeout=5)
            print("✅ 已点击 Turnstile（WebDriver）")
        except Exception:
            try:
                # 回退 GUI 方式
                sb.uc_gui_click_captcha(timeout=5)
                print("✅ 已点击 Turnstile（GUI）")
            except Exception as e:
                print(f"⚠️ 点击 Turnstile 异常: {e}")

        time.sleep(click_delay)  # 等待 CF 验证完成

        if wait_for_turnstile_pass(sb, timeout=20):
            return True
        else:
            print(f"⏳ 第 {attempt} 次未通过验证" + ("" if attempt < max_attempts else "，已达最大重试次数"))

    return False


# ===== TheRose 登录流程 =====

def login(sb, email, password):
    print("🌐 打开登录页面...")
    sb.open(BASE_URL)
    sb.wait_for_ready_state_complete()
    sb.sleep(2)

    print("📧 填写邮箱...")
    sb.type('#login_form_email', email, timeout=10)
    print("🔑 填写密码...")
    sb.type('#login_form_password', password, timeout=10)
    sb.sleep(1)

    # 先处理一次 Turnstile（有的站点在登录前就加载了）
    print("🛡 处理 Turnstile...")
    handle_turnstile(sb, max_attempts=2, click_delay=6)

    print("🔑 点击登录按钮...")
    try:
        sb.uc_click('button:contains("Sign in")', timeout=10)
    except Exception as e:
        print(f"⚠️ 点击登录按钮异常: {e}")

    sb.sleep(3)

    # 等待跳转，最多 30 秒
    for _ in range(30):
        current_url = sb.get_current_url()
        page_title = sb.get_title() or ""
        print(f"📄 当前 URL: {current_url} | Title: {page_title}")
        if "panel" in current_url:
            print("✅ 登录成功，已跳转到 Dashboard")
            return True, current_url
        time.sleep(1)

    # 点击登录后如果弹出 Turnstile 挑战，再处理一次
    print("⚠️ 登录后可能弹出 Turnstile 挑战，尝试处理...")
    if handle_turnstile(sb, max_attempts=2, click_delay=6):
        print("🔑 再次点击登录按钮...")
        try:
            sb.uc_click('button:contains("Sign in")', timeout=10)
        except Exception:
            pass
        sb.sleep(3)
        for _ in range(30):
            current_url = sb.get_current_url()
            if "panel" in current_url:
                print("✅ 登录成功，已跳转到 Dashboard")
                return True, current_url
            time.sleep(1)

    print(f"❌ 登录失败，当前 URL: {sb.get_current_url()}")
    sb.save_screenshot("login_failed.png")
    return False, sb.get_current_url()


# ===== 续期操作 =====

def click_extend_button(sb):
    """点击 Extend 续期按钮"""
    selectors = [
        'span:contains("Extend")',
        'button:contains(title="Extend")',
    ]
    for sel in selectors:
        try:
            if sb.find_element(sel, timeout=2):
                print(f"✅ 找到按钮，选择器: {sel}")
                sb.uc_click(sel, timeout=5)
                print("✅ 点击成功")
                return True, {}
        except Exception:
            continue
    try:
        btn = sb.find_element('button:contains("Extend")', timeout=2)
        sb.driver.execute_script("arguments[0].click();", btn)
        print("✅ 通过 JavaScript 点击成功")
        return True, {}
    except Exception as e:
        return False, {"error": str(e)}


def check_renewal_success(sb):
    """检查续期是否成功"""
    success_selectors = [
        '.alert-success',
        '.alert.alert-success',
        'div[role="alert"].alert-success',
        'div.alert-success',
        'span:contains("successfully purchased")',
        'div:contains("successfully purchased")',
    ]

    print("⏳ 等待 5 秒检查续期结果...")
    time.sleep(5)

    for selector in success_selectors:
        try:
            element = sb.find_element(selector, timeout=2)
            if element:
                text = element.text
                print(f"✅ 发现成功提示！选择器: {selector}")
                print(f"📝 提示内容: {text}")
                return True, text
        except Exception:
            continue

    try:
        page_source = sb.get_page_source()
        if "successfully purchased" in page_source.lower():
            print("✅ 页面源码中发现 'successfully purchased' 关键词")
            return True, "服务器已成功续期"
    except Exception:
        pass

    return False, "未检测到续期成功提示"


# ===== 主流程 =====

def main():
    print("#" * 30)
    print("   TheRose.cloud 自动续期")
    print("#" * 30)

    # 检测代理
    if IS_PROXY:
        print(f"🔗 使用代理: {PROXY_SERVER}")
    else:
        print("🍭 直连访问（未使用代理）")

    sb_kwargs = {"uc": True, "headless": HEADLESS}
    if IS_PROXY:
        sb_kwargs["proxy"] = PROXY_SERVER

    with SB(**sb_kwargs) as sb:
        # 获取出口 IP
        try:
            ip = get_current_ip(PROXY_SERVER if IS_PROXY else "")
            print(f"📍 当前出口 IP: {ip}")
        except Exception as e:
            print(f"⚠️ 获取出口 IP 失败: {e}")

        # 登录
        success, url = login(sb, EMAIL, PASSWORD)
        if not success:
            msg = "❌ 登录失败"
            print(msg)
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            return

        print("📄 开始续期流程...")

        # 点击 Extend
        ok, info = click_extend_button(sb)
        if not ok:
            msg = f"❌ 点击 Extend 按钮失败: {info.get('error')}"
            print(msg)
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            return

        time.sleep(2)

        # 点击 Order now
        try:
            btn = sb.find_element('button:contains("Order now")', timeout=5)
            if btn:
                print("🛒 点击 Order now 按钮...")
                sb.uc_click('button:contains("Order now")')
                print("✅ 已点击 Order now 按钮")
            else:
                msg = "❌ 未找到 Order now 按钮"
                print(msg)
                send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
                return
        except Exception as e:
            msg = f"❌ 点击 Order now 失败: {e}"
            print(msg)
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            return

        # 检查续期结果
        print("🔍 检查续期结果...")
        renewal_success, renewal_msg = check_renewal_success(sb)

        if renewal_success:
            msg = f"✅ 续期成功！{renewal_msg}"
            print(msg)
            sb.save_screenshot("renewal_success.png")
        else:
            msg = f"❌ 续期可能失败: {renewal_msg}"
            print(msg)
            sb.save_screenshot("renewal_failed.png")

        send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)

    print("🏁 脚本执行完毕")


if __name__ == "__main__":
    main()