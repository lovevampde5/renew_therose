# renew_therose

TheRose.cloud 服务器自动续期脚本。通过浏览器自动化登录面板，点击 Extend 续期，并发送 Telegram 通知结果。

## 工作原理

```
GitHub Actions (定时/手动触发)
        ↓
  安装 Chrome + Python 依赖
        ↓
  seleniumbase 自动化登录 TheRose 面板
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
| `TG_BOT_TOKEN` | ❌ 否 | Telegram Bot Token（不填则不发送通知） |
| `TG_CHAT_ID` | ❌ 否 | Telegram Chat ID |

## 快速开始

### 1. 创建仓库

点击 **Use this template** → **Create a new repository**（建议设为 **Private** 私密仓库，避免密码泄露）

### 2. 添加 Secrets

1. 进入仓库 **Settings → Secrets and variables → Actions**
2. 点击 **New repository secret**
3. 依次添加以下 secrets：
   - `EMAIL` — TheRose 登录邮箱
   - `PASSWORD` — TheRose 登录密码
   - `TG_BOT_TOKEN` — Telegram Bot Token（可选）
   - `TG_CHAT_ID` — Telegram Chat ID（可选）

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

将 Bot Token 和 Chat ID 添加到 GitHub Secrets：

| Secret | 值 |
|--------|-----|
| `TG_BOT_TOKEN` | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `TG_CHAT_ID` | `123456789` |

## 手动运行

### 方式一：GitHub Actions

进入仓库 **Actions → Renew TheRose → Run workflow**，点击 **Run workflow** 即可立即执行。

### 方式二：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/renew_therose.git
cd renew_therose

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量
export EMAIL="your@email.com"
export PASSWORD="your_password"
export TG_BOT_TOKEN=""
export TG_CHAT_ID=""

# 4. 运行脚本
python renew_therose.py
```

## 常见问题

### 登录失败？
- 检查 `EMAIL` 和 `PASSWORD` 是否正确
- 检查 TheRose 面板是否正常访问
- GitHub Actions 运行日志中会保存截图，查看是否有验证码/人机验证

### 续期按钮未找到？
- TheRose 面板 UI 可能已更新，需检查脚本中的选择器是否需要更新
- 如果服务器刚续期过，可能暂时没有 Extend 按钮

### 如何调试？
在 GitHub Actions 运行日志中查看：
1. 每一步的打印日志
2. 失败时会自动截图保存（`login_failed.png` / `renewal_failed.png`）
3. 截图可作为 Actions Artifact 下载

## 文件说明

| 文件 | 说明 |
|------|------|
| [`renew_therose.py`](./renew_therose.py) | 续期自动化脚本 |
| [`.github/workflows/renew.yml`](./.github/workflows/renew.yml) | GitHub Actions 工作流配置 |