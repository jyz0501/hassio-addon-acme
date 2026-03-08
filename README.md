# ACME.sh SSL Home Assistant Add-on

这是一个基于 [acme.sh](https://github.com/acmesh-official/acme.sh) 的 Home Assistant Add-on，用于自动申请和管理 SSL 证书。

## 功能特性

- 🚀 支持多种 ACME 服务器（Let's Encrypt、ZeroSSL、Google Trust Services、Buypass、SSL.com）
- 🔒 支持 100+ 种 DNS 提供商（Cloudflare、阿里云、DNSPod、AWS Route53 等）
- 🔄 自动证书续期
- 📁 自动将证书安装到 Home Assistant SSL 目录
- 🛠️ 支持 RSA 和 ECC 证书
- 🧪 支持 Staging 环境测试
- 🐛 调试模式支持

## 支持的 DNS 提供商

| DNS 提供商 | 代码 | 环境变量示例 |
|-----------|------|-------------|
| Cloudflare | dns_cf | `CF_Token=xxx;CF_Zone_ID=xxx` |
| 阿里云 | dns_ali | `Ali_Key=xxx;Ali_Secret=xxx` |
| DNSPod | dns_dp | `DP_Id=xxx;DP_Key=xxx` |
| GoDaddy | dns_gd | `GD_Key=xxx;GD_Secret=xxx` |
| AWS Route53 | dns_aws | `AWS_ACCESS_KEY_ID=xxx;AWS_SECRET_ACCESS_KEY=xxx` |
| Linode | dns_linode | `LINODE_API_KEY=xxx` |
| OVH | dns_ovh | `OVH_APPLICATION_KEY=xxx;OVH_APPLICATION_SECRET=xxx;OVH_CONSUMER_KEY=xxx` |
| DigitalOcean | dns_do | `DO_API_KEY=xxx` |
| Hetzner | dns_hetzner | `HETZNER_API_KEY=xxx` |
| Gandi | dns_gandi | `GANDI_API_KEY=xxx` |
| Namecheap | dns_namecheap | `NAMECHEAP_API_KEY=xxx;NAMECHEAP_API_USER=xxx` |
| Namesilo | dns_namesilo | `Namesilo_Key=xxx` |
| Porkbun | dns_porkbun | `PORKBUN_API_KEY=xxx;PORKBUN_SECRET_API_KEY=xxx` |
| Vultr | dns_vultr | `VULTR_API_KEY=xxx` |

更多 DNS 提供商请参考 [acme.sh DNS API 文档](https://github.com/acmesh-official/acme.sh/wiki/dnsapi)

## 安装方法

### 方法一：通过 HACS 安装（推荐）

1. 打开 HACS（Home Assistant Community Store）
2. 点击 **集成** → 右上角 **⋮** → **自定义仓库**
3. 添加仓库地址：`https://github.com/jyz0501/hassio-addon-acme`
4. 类别选择 **加载项**
5. 点击 **添加**
6. 在 HACS 中找到 "ACME.sh SSL Add-on" 并点击 **下载**
7. 下载完成后，在 Home Assistant **设置** → **加载项** 中找到并安装

### 方法二：手动添加仓库

1. 在 Home Assistant 中，进入 **设置** → **加载项** → **加载项商店**
2. 点击右上角菜单，选择 **仓库**
3. 添加此仓库地址：`https://github.com/jyz0501/hassio-addon-acme`
4. 刷新页面后，找到 "ACME.sh SSL" 并安装

## 配置示例

### Cloudflare 配置示例

```yaml
email: your-email@example.com
domains:
  - "*.example.com"
  - "example.com"
dns_provider: dns_cf
dns_env: "CF_Token=your-cloudflare-api-token;CF_Zone_ID=your-zone-id"
keylength: "ec-256"
staging: false
auto_renew: true
renew_interval: "0 2 * * *"
acme_server: "letsencrypt"
```

### 阿里云配置示例

```yaml
email: your-email@example.com
domains:
  - "*.example.com"
  - "example.com"
dns_provider: dns_ali
dns_env: "Ali_Key=your-aliyun-access-key;Ali_Secret=your-aliyun-access-secret"
keylength: "ec-256"
auto_renew: true
acme_server: "letsencrypt"
```

### DNSPod 配置示例

```yaml
email: your-email@example.com
domains:
  - "*.example.com"
  - "example.com"
dns_provider: dns_dp
dns_env: "DP_Id=your-dnspod-id;DP_Key=your-dnspod-token"
keylength: "ec-256"
auto_renew: true
acme_server: "letsencrypt"
```

### 高级配置示例

```yaml
email: your-email@example.com
domains:
  - "*.example.com"
  - "example.com"
dns_provider: dns_cf
dns_env: "CF_Token=your-token"
keylength: "ec-256"
days: 60                    # 到期前60天续期
staging: false
force_issue: false          # 强制重新申请
auto_renew: true
renew_interval: "0 2 * * *"
reload_cmd: ""              # 证书重载命令
deploy_hook: ""             # 部署钩子
acme_server: "letsencrypt"
debug: false                # 调试模式
```

## 配置选项说明

| 选项 | 必需 | 默认值 | 说明 |
|-----|------|-------|------|
| `email` | ✅ | - | 用于注册 ACME 账户的邮箱 |
| `domains` | ✅ | - | 要申请证书的域名列表 |
| `dns_provider` | ✅ | `dns_cf` | DNS API 提供商代码 |
| `dns_env` | ✅ | - | DNS 提供商的环境变量（格式: `KEY1=value1;KEY2=value2`） |
| `keylength` | ❌ | `ec-256` | 密钥长度：`2048`、`3072`、`4096`、`ec-256`、`ec-384` |
| `days` | ❌ | `60` | 到期前多少天开始续期 |
| `staging` | ❌ | `false` | 是否使用 Staging 环境（测试用） |
| `force_issue` | ❌ | `false` | 强制重新申请证书 |
| `auto_renew` | ❌ | `true` | 是否启用自动续期 |
| `renew_interval` | ❌ | `0 2 * * *` | 续期检查间隔（cron 表达式） |
| `reload_cmd` | ❌ | - | 证书更新后的重载命令 |
| `deploy_hook` | ❌ | - | 证书部署后的钩子脚本 |
| `acme_server` | ❌ | `letsencrypt` | ACME 服务器 |
| `debug` | ❌ | `false` | 调试模式 |

## 证书位置

申请成功后，证书将保存在以下位置：

- `/ssl/acme.sh/<domain>/` - 证书完整目录
  - `cert.pem` - 证书
  - `key.pem` - 私钥
  - `fullchain.pem` - 完整证书链
  - `ca.pem` - CA 证书
- `/ssl/<domain>.pem` - 完整证书链（供 Home Assistant 使用）
- `/ssl/<domain>-key.pem` - 私钥（供 Home Assistant 使用）

## Home Assistant 配置

在 `configuration.yaml` 中使用证书：

```yaml
http:
  ssl_certificate: /ssl/example.com.pem
  ssl_key: /ssl/example.com-key.pem
```

## 故障排除

### 查看日志

在 Add-on 页面点击 **日志** 查看运行日志。

### 调试模式

启用调试模式获取详细信息：

```yaml
debug: true
```

### 常见问题

1. **证书申请失败**
   - 检查 DNS 提供商的 API 密钥是否正确
   - 确认域名 DNS 解析正常
   - 检查邮箱格式是否正确
   - 启用 `debug: true` 查看详细日志

2. **证书未自动续期**
   - 检查 `auto_renew` 是否设置为 `true`
   - 查看日志中的续期任务是否正常运行

3. **Staging 模式**
   - 测试时建议开启 `staging: true`
   - 正式使用时请设置为 `false`

4. **强制重新申请**
   - 设置 `force_issue: true` 可以强制重新申请证书

## 更新日志

### 1.0.0
- 初始版本发布
- 支持多种 DNS 提供商
- 支持自动续期
- 支持多种 ACME 服务器
- 支持调试模式

## 许可证

MIT License
