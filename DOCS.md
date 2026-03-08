# ACME.sh SSL Add-on 使用文档

## 快速开始

### 1. 准备工作

在申请 SSL 证书之前，请确保：

- 拥有一个有效的域名
- 域名 DNS 解析正常
- 拥有 DNS 提供商的 API 访问权限

### 2. 获取 DNS API 凭证

#### Cloudflare

1. 登录 Cloudflare Dashboard
2. 选择你的域名
3. 点击 **获取您的 API 令牌**
4. 创建具有以下权限的令牌：
   - `区域:读取`
   - `DNS:编辑`
5. 复制令牌并保存

#### 阿里云

1. 登录阿里云控制台
2. 进入 **访问控制** → **AccessKey 管理**
3. 创建 AccessKey
4. 记录 `AccessKey ID` 和 `AccessKey Secret`

#### DNSPod

1. 登录 DNSPod 控制台
2. 进入 **账号中心** → **密钥管理**
3. 创建密钥
4. 记录 `ID` 和 `Token`

### 3. 配置 Add-on

在 Home Assistant 的 Add-on 配置页面，填写以下信息：

```yaml
email: your-email@example.com
domains:
  - "*.example.com"  # 通配符域名
  - "example.com"    # 根域名
dns_provider: dns_cf
dns_env:
  CF_Token: "your-token-here"
keylength: "ec-256"
```

### 4. 启动 Add-on

1. 点击 **保存** 保存配置
2. 点击 **启动** 启动 Add-on
3. 查看日志确认证书申请成功

### 5. 配置 Home Assistant

编辑 `configuration.yaml`：

```yaml
http:
  ssl_certificate: /ssl/example.com.pem
  ssl_key: /ssl/example.com-key.pem
```

重启 Home Assistant 使配置生效。

## 高级配置

### 使用 ECC 证书

ECC 证书比 RSA 证书更小、更快：

```yaml
keylength: "ec-256"  # 或 "ec-384"
```

### 使用不同的 ACME 服务器

```yaml
# Let's Encrypt（默认）
acme_server: "letsencrypt"

# Let's Encrypt 测试环境
acme_server: "letsencrypt_test"

# ZeroSSL
acme_server: "zerossl"

# Google Trust Services
acme_server: "google"
```

### 自定义续期间隔

使用 Cron 表达式设置续期检查时间：

```yaml
# 每天凌晨 2 点
renew_interval: "0 2 * * *"

# 每周一凌晨 3 点
renew_interval: "0 3 * * 1"

# 每月 1 日凌晨 4 点
renew_interval: "0 4 1 * *"
```

### 部署钩子

证书更新后执行自定义命令：

```yaml
deploy_hook: "curl -X POST http://homeassistant:8123/api/services/homeassistant/restart"
```

## 故障排除

### 调试模式

在配置中添加：

```yaml
staging: true
```

这将使用 Let's Encrypt 的测试环境，避免达到速率限制。

### 手动测试 DNS API

在 Add-on 的 **终端** 标签页中运行：

```bash
# 测试 Cloudflare API
export CF_Token="your-token"
acme.sh --issue --dns dns_cf -d example.com --staging
```

### 查看证书信息

```bash
openssl x509 -in /ssl/example.com.pem -text -noout
```

### 强制续期

```bash
acme.sh --renew -d example.com --force
```

### 删除证书

```bash
acme.sh --remove -d example.com
```

## 安全建议

1. **保护 API 密钥**
   - 不要在公共仓库中提交配置文件
   - 定期轮换 API 密钥

2. **使用测试环境**
   - 首次配置时使用 `staging: true`
   - 确认配置无误后再切换到生产环境

3. **备份证书**
   - 定期备份 `/ssl` 目录
   - 备份 `/data/acme.sh` 目录（包含账户信息）

## 支持的 DNS 提供商完整列表

| 提供商 | 代码 | 环境变量 |
|-------|------|---------|
| Cloudflare | dns_cf | `CF_Token`, `CF_Account_ID`, `CF_Zone_ID` |
| 阿里云 | dns_ali | `Ali_Key`, `Ali_Secret` |
| DNSPod.cn | dns_dp | `DP_Id`, `DP_Key` |
| DNSPod.com | dns_dpi | `DPI_Id`, `DPI_Key` |
| GoDaddy | dns_gd | `GD_Key`, `GD_Secret` |
| AWS Route53 | dns_aws | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| Linode | dns_linode | `LINODE_API_KEY` |
| OVH | dns_ovh | `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY` |
| DigitalOcean | dns_do | `DO_API_KEY` |
| Hetzner | dns_hetzner | `HETZNER_API_KEY` |
| Gandi | dns_gandi | `GANDI_API_KEY` |
| Namecheap | dns_namecheap | `NAMECHEAP_API_KEY`, `NAMECHEAP_API_USER` |
| Namesilo | dns_namesilo | `Namesilo_Key` |
| Porkbun | dns_porkbun | `PORKBUN_API_KEY`, `PORKBUN_SECRET_API_KEY` |
| PowerDNS | dns_pdns | `PDNS_Url`, `PDNS_ServerId`, `PDNS_Token` |
| RFC2136 | dns_rfc2136 | `RFC2136_NAMESERVER`, `RFC2136_TSIG_KEY` |
| Vultr | dns_vultr | `VULTR_API_KEY` |

更多提供商请参考 [acme.sh DNS API Wiki](https://github.com/acmesh-official/acme.sh/wiki/dnsapi)

## 获取帮助

- [acme.sh GitHub](https://github.com/acmesh-official/acme.sh)
- [acme.sh Wiki](https://github.com/acmesh-official/acme.sh/wiki)
- [Home Assistant 社区](https://community.home-assistant.io/)
