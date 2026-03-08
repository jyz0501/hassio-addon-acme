#!/usr/bin/with-contenv bashio
set -e

# ==============================================================================
# ACME.sh SSL Home Assistant Add-on
# 基于 https://github.com/acmesh-official/acme.sh
# ==============================================================================

# 获取配置
EMAIL=$(bashio::config 'email')
DOMAINS=$(bashio::config 'domains')
DNS_PROVIDER=$(bashio::config 'dns_provider')
KEYLENGTH=$(bashio::config 'keylength')
STAGING=$(bashio::config 'staging')
AUTO_RENEW=$(bashio::config 'auto_renew')
RENEW_INTERVAL=$(bashio::config 'renew_interval')
DEPLOY_HOOK=$(bashio::config 'deploy_hook')
ACME_SERVER=$(bashio::config 'acme_server')
DAYS=$(bashio::config 'days')
RELOAD_CMD=$(bashio::config 'reload_cmd')
FORCE_ISSUE=$(bashio::config 'force_issue')
DEBUG=$(bashio::config 'debug')

# 设置 acme.sh 环境变量
export LE_CONFIG_HOME=/data/acme.sh
export LE_WORKING_DIR=/opt/acme.sh

# 创建必要的目录
mkdir -p /data/acme.sh
mkdir -p /ssl/acme.sh

# 调试模式
if [ "${DEBUG}" = "true" ]; then
    set -x
    bashio::log.info "调试模式已启用"
fi

# ==============================================================================
# 设置 DNS 环境变量
# ==============================================================================
setup_dns_env() {
    bashio::log.info "配置 DNS 提供商环境变量..."
    
    # 解析 dns_env 字符串（格式: KEY1=value1;KEY2=value2）
    local dns_env_str=$(bashio::config 'dns_env')
    
    if [ -z "${dns_env_str}" ] || [ "${dns_env_str}" = "null" ]; then
        bashio::log.warning "未配置 DNS 环境变量"
        return 0
    fi
    
    # 按分号分割并设置环境变量
    IFS=';' read -ra ENVS <<< "${dns_env_str}"
    for env_pair in "${ENVS[@]}"; do
        # 去除首尾空格
        env_pair=$(echo "${env_pair}" | xargs)
        if [ -n "${env_pair}" ]; then
            export "${env_pair}"
            bashio::log.info "设置环境变量: ${env_pair%%=*}"
        fi
    done
}

# ==============================================================================
# 配置 ACME 服务器
# ==============================================================================
setup_acme_server() {
    bashio::log.info "配置 ACME 服务器: ${ACME_SERVER}"
    
    local server_url=""
    case "${ACME_SERVER}" in
        letsencrypt)
            server_url="letsencrypt"
            ;;
        letsencrypt_test)
            server_url="letsencrypt_test"
            ;;
        zerossl)
            server_url="zerossl"
            ;;
        sslcom)
            server_url="sslcom"
            ;;
        google)
            server_url="google"
            ;;
        googletest)
            server_url="googletest"
            ;;
        buypass)
            server_url="buypass"
            ;;
        buypass_test)
            server_url="buypass_test"
            ;;
        *)
            server_url="letsencrypt"
            ;;
    esac
    
    acme.sh --set-default-ca --server "${server_url}" --config-home /data/acme.sh
}

# ==============================================================================
# 注册/更新账户
# ==============================================================================
register_account() {
    if [ -n "${EMAIL}" ]; then
        bashio::log.info "注册/更新账户: ${EMAIL}"
        acme.sh --update-account --accountemail "${EMAIL}" --config-home /data/acme.sh || \
        acme.sh --register-account --accountemail "${EMAIL}" --config-home /data/acme.sh
    fi
}

# ==============================================================================
# 构建域名参数
# ==============================================================================
build_domain_args() {
    local domain_args=""
    for domain in $(echo "${DOMAINS}" | jq -r '.[]'); do
        domain_args="${domain_args} -d ${domain}"
    done
    echo "${domain_args}"
}

# ==============================================================================
# 申请证书
# ==============================================================================
issue_certificates() {
    bashio::log.info "开始申请证书..."
    
    local domain_args=$(build_domain_args)
    
    if [ -z "${domain_args}" ]; then
        bashio::log.error "未配置域名"
        return 1
    fi
    
    # 构建 acme.sh 命令
    local cmd="acme.sh --issue --dns ${DNS_PROVIDER} ${domain_args} --config-home /data/acme.sh"
    
    # 添加密钥长度
    cmd="${cmd} --keylength ${KEYLENGTH}"
    
    # 添加续期天数
    if [ -n "${DAYS}" ] && [ "${DAYS}" != "null" ]; then
        cmd="${cmd} --days ${DAYS}"
    fi
    
    # 添加 staging 模式
    if [ "${STAGING}" = "true" ]; then
        cmd="${cmd} --staging"
        bashio::log.warning "使用 Staging 模式（测试环境）"
    fi
    
    # 添加强制申请
    if [ "${FORCE_ISSUE}" = "true" ]; then
        cmd="${cmd} --force"
        bashio::log.warning "强制申请模式"
    fi
    
    # 添加调试模式
    if [ "${DEBUG}" = "true" ]; then
        cmd="${cmd} --debug"
    fi
    
    # 执行申请
    bashio::log.info "执行命令: ${cmd}"
    if eval "${cmd}"; then
        bashio::log.info "证书申请成功"
        
        # 安装证书
        install_certificate
        
        # 执行部署钩子
        if [ -n "${DEPLOY_HOOK}" ]; then
            bashio::log.info "执行部署钩子..."
            eval "${DEPLOY_HOOK}"
        fi
    else
        bashio::log.error "证书申请失败"
        return 1
    fi
}

# ==============================================================================
# 安装证书到指定目录
# ==============================================================================
install_certificate() {
    local main_domain=$(echo "${DOMAINS}" | jq -r '.[0]')
    local cert_dir="/ssl/acme.sh/${main_domain}"
    
    mkdir -p "${cert_dir}"
    
    bashio::log.info "安装证书到: ${cert_dir}"
    
    local cmd="acme.sh --install-cert -d ${main_domain} --config-home /data/acme.sh"
    
    # 添加证书文件路径
    cmd="${cmd} --cert-file ${cert_dir}/cert.pem"
    cmd="${cmd} --key-file ${cert_dir}/key.pem"
    cmd="${cmd} --fullchain-file ${cert_dir}/fullchain.pem"
    cmd="${cmd} --ca-file ${cert_dir}/ca.pem"
    
    # 添加重载命令
    if [ -n "${RELOAD_CMD}" ] && [ "${RELOAD_CMD}" != "null" ]; then
        cmd="${cmd} --reloadcmd '${RELOAD_CMD}'"
    else
        cmd="${cmd} --reloadcmd 'echo Certificate installed for ${main_domain}'"
    fi
    
    eval "${cmd}"
    
    # 复制到标准 SSL 目录供 Home Assistant 使用
    cp "${cert_dir}/fullchain.pem" "/ssl/${main_domain}.pem"
    cp "${cert_dir}/key.pem" "/ssl/${main_domain}-key.pem"
    
    bashio::log.info "证书已安装并复制到 /ssl 目录"
    bashio::log.info "  - 证书: /ssl/${main_domain}.pem"
    bashio::log.info "  - 私钥: /ssl/${main_domain}-key.pem"
}

# ==============================================================================
# 设置自动续期
# ==============================================================================
setup_renewal() {
    if [ "${AUTO_RENEW}" = "true" ]; then
        bashio::log.info "设置自动续期: ${RENEW_INTERVAL}"
        
        # 创建 crontab 文件
        echo "${RENEW_INTERVAL} /run.sh renew >> /proc/1/fd/1 2>&1" > /etc/crontabs/root
        
        # 启动 crond
        crond -b -l 8
        
        bashio::log.info "自动续期已启用"
    fi
}

# ==============================================================================
# 续期证书
# ==============================================================================
renew_certificates() {
    bashio::log.info "开始续期证书..."
    
    local cmd="acme.sh --cron --config-home /data/acme.sh"
    
    if [ "${DEBUG}" = "true" ]; then
        cmd="${cmd} --debug"
    fi
    
    if eval "${cmd}"; then
        bashio::log.info "证书续期检查完成"
        
        # 重新安装证书
        install_certificate
        
        # 执行部署钩子
        if [ -n "${DEPLOY_HOOK}" ]; then
            bashio::log.info "执行部署钩子..."
            eval "${DEPLOY_HOOK}"
        fi
    else
        bashio::log.error "证书续期失败"
        return 1
    fi
}

# ==============================================================================
# 列出所有证书
# ==============================================================================
list_certificates() {
    bashio::log.info "已安装的证书列表:"
    acme.sh --list --config-home /data/acme.sh
}

# ==============================================================================
# 显示证书信息
# ==============================================================================
show_cert_info() {
    local main_domain=$(echo "${DOMAINS}" | jq -r '.[0]')
    bashio::log.info "证书信息: ${main_domain}"
    acme.sh --info -d "${main_domain}" --config-home /data/acme.sh
}

# ==============================================================================
# 主逻辑
# ==============================================================================
main() {
    bashio::log.info "========================================"
    bashio::log.info "ACME.sh SSL Add-on 启动"
    bashio::log.info "版本: 1.0.0"
    bashio::log.info "========================================"
    
    # 设置环境
    setup_dns_env
    setup_acme_server
    register_account
    
    case "${1:-}" in
        renew)
            renew_certificates
            ;;
        list)
            list_certificates
            ;;
        info)
            show_cert_info
            ;;
        *)
            # 首次运行
            if [ -n "${DOMAINS}" ] && [ "${DOMAINS}" != "[]" ] && [ "${DOMAINS}" != "null" ]; then
                issue_certificates
                setup_renewal
            else
                bashio::log.warning "未配置域名，跳过证书申请"
                bashio::log.info "请在配置中添加域名后重启 Add-on"
            fi
            
            # 保持容器运行
            bashio::log.info "========================================"
            bashio::log.info "ACME.sh addon 运行中..."
            bashio::log.info "========================================"
            tail -f /dev/null
            ;;
    esac
}

# 运行主函数
main "$@"
