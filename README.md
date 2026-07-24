# renew_therose

TheRose.cloud 服务器自动续期脚本。通过浏览器自动化登录面板，点击 Extend 续期，并发送 Telegram 通知结果。

## 工作原理

```
GitHub Actions (定时/手动触发)
        ↓
  设置代理（sing-box，固定节点）
        ↓
  安装 Chrome + Python 依赖
        ↓
  seleniumbase 自动化登录 TheRose 面板
        ↓
  CF Turnstile 验证（3次重试 + 页面源码检测）
        ↓
  点击 Extend → 点击 Order now → 检查续期结果
        ↓
  Telegram 通知（成功/失败 + 截图）
```

## 前置条件

- 一个 [TheRose.cloud](https://client.therose.cloud) 账号（邮箱 + 密码）
- 一个 GitHub 账号（免费）
- （可选）Telegram Bot Token 和 Chat ID 用于接收通知

## 环境变量

请在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中添加以下 Repository secrets：

| 变量 | 必需 | 说明 |
|------|------|------|
| `EMAIL` | ✅ 是 | TheRose 登录邮箱 |
| `PASSWORD` | ✅ 是 | TheRose 登录密码 |
| `NODE_LINK` | ❌ 否 | sing-box 节点订阅链接，用于固定出口 IP（可选，不填则直连） |
| `TG_BOT_TOKEN` | ❌ 否 | Telegram Bot Token（不填则不发送通知） |
| `TG_CHAT_ID` | ❌ 否 | Telegram Chat ID |

## 快速开始

### 1. 创建仓库

点击 **Use this template** → **Create a new repository**（建议设为 **Private** 私密仓库，避免密码泄露）

### 2. 添加 Secrets

1. 进入仓库 **Settings → Secrets and variables → Actions**
2. 点击 **New repository secret**
3. 依次添加以下 secrets：

| Secret | 说明 |
|--------|------|
| `EMAIL` | TheRose 登录邮箱 |
| `PASSWORD` | TheRose 登录密码 |
| `NODE_LINK` | 可选：sing-box 节点订阅链接，用于固定出口 IP（避免被 CF 拦截） |
| `TG_BOT_TOKEN` | 可选：Telegram Bot Token |
| `TG_CHAT_ID` | 可选：Telegram Chat ID |

### 3. 启用 Actions

1. 进入仓库 **Actions** 选项卡
2. 点击 **`I understand my workflows, go ahead and enable them`**
3. 左侧找到 **Renew TheRose** 工作流
4. 点击 **Run workflow** → 选择分支 `main` → **Run**

### 4. 设置定时自动续期

工作流默认已配置定时触发（北京时间每天 08:00），位于 `renew.yml` 中：

```yaml
schedule:
  - cron: '0 0 * * *'   # UTC 00:00 = 北京时间 08:00
```

如需修改频率，编辑 [`.github/workflows/renew.yml`](./.github/workflows/renew.yml) 中的 cron 表达式。

## 固定节点（NODE_LINK）说明

`NODE_LINK` 是可选的 sing-box 节点订阅链接，用于在 GitHub Actions 中设置代理，解决：

- **CF Turnstile 验证频繁** — 直连 IP 可能被 Cloudflare 拦截或频繁弹出验证码
- **IP 风控** — 某些机房 IP 被标记为高风险
- **地区限制** — 通过代理节点选择合适地区的出口 IP

> 如果不设置 `NODE_LINK`，脚本将直连访问 TheRose 面板。

### 获取 NODE_LINK

1. 从你的机场/节点服务商获取 sing-box 订阅链接
2. 或者使用自建节点的订阅地址
3. 链接格式通常是 `https://xxx.com/xxx/singbox`

## 获取 Telegram 通知（可选）

### 创建 Bot

1. 在 Telegram 搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`，按提示创建 Bot
3. 复制 Bot Token（格式如 `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

### 获取 Chat ID

1. 搜索你的 Bot 用户名，发送 `/start`
2. 访问 `https://api.telegram.org/bot<你的Token>/getUpdates`
3. 在返回的 JSON 中找到 `chat.id` 的值

### 设置 Secrets

```text
TG_BOT_TOKEN = 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TG_CHAT_ID = 123456789
```

## 手动运行

### 方式一：GitHub Actions

进入仓库 **Actions → Renew TheRose → Run workflow**，点击 **Run workflow** 即可立即执行。

### 方式二：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/renew_therose.git
cd renew_therose

# 2. 安装依赖
pip install seleniumbase requests

# 3. 设置环境变量
export EMAIL="your@email.com"
export PASSWORD="your_password"
export HEADLESS="false"   # 本地运行建议关闭 headless，方便观察

# 4. 运行脚本
python renew_therose.py
```

## 常见问题

### 登录失败（卡在 Turnstile 验证）？
- 脚本使用了 **3 次重试** + **页面源码关键词检测** 的 CF 盾处理方案
- 如果仍然失败，尝试设置 `NODE_LINK` 使用代理出口
- 检查 GitHub Actions 运行日志中的截图，查看具体验证情况

### 续期按钮未找到？
- TheRose 面板 UI 可能已更新，需检查脚本中的选择器是否需要更新
- 如果服务器刚续期过，可能暂时没有 Extend 按钮

### 如何调试？
1. 手动触发 **Run workflow**，勾选 **调试模式**
2. 运行完成后，在运行结果页下载 **Artifacts**（截图压缩包）
3. 查看 `login_failed.png` / `renewal_failed.png` 分析问题

## CF Turnstile 处理方案

本脚本的 CF 盾处理方案移植自 [Auto-Renew-Bothosting](https://github.com/krisxu23/Auto-Renew-Bothosting)：

1. **`handle_turnstile()`** — 点击验证码 → 等待 6-8 秒 → 用 `wait_for_turnstile_pass()` 检测页面源码
2. **`wait_for_turnstile_pass()`** — 轮询检测页面中是否还有 CF 关键词（"verify you are human"、"确认您是真人" 等）
3. 最多重试 3 次
4. 登录前和登录后各处理一次（应对弹出式 Turnstile 挑战）

## 文件说明

| 文件 | 说明 |
|------|------|
| [`renew_therose.py`](./renew_therose.py) | 续期自动化脚本（含 CF 盾处理、代理支持） |
| [`.github/workflows/renew.yml`](./.github/workflows/renew.yml) | GitHub Actions 工作流配置（含代理设置、进程清理、旧记录清理） |