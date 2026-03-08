ARG BUILD_FROM
FROM $BUILD_FROM

# 安装必要的依赖（参考官方 Dockerfile）
RUN apk add --no-cache \
    bash \
    curl \
    openssl \
    openssh-client \
    coreutils \
    bind-tools \
    ca-certificates \
    jq \
    cronie \
    socat \
    libidn \
    tzdata \
    sed \
    tar

# 设置 acme.sh 环境变量（参考官方配置）
ENV LE_WORKING_DIR=/opt/acme.sh
ENV LE_CONFIG_HOME=/data/acme.sh
ENV AUTO_UPGRADE=0

# 复制 acme.sh 源码并安装
COPY acme.sh-master/acme.sh /install/acme.sh
COPY acme.sh-master/deploy /install/deploy
COPY acme.sh-master/dnsapi /install/dnsapi
COPY acme.sh-master/notify /install/notify

# 安装 acme.sh
RUN cd /install && \
    ./acme.sh --install \
        --home "$LE_WORKING_DIR" \
        --config-home "$LE_CONFIG_HOME" \
        --no-cron && \
    ln -s "$LE_WORKING_DIR/acme.sh" /usr/local/bin/acme.sh && \
    rm -rf /install

# 创建必要的目录
RUN mkdir -p /data/acme.sh /ssl && \
    chmod -R o+rwx "$LE_WORKING_DIR" && \
    chmod -R o+rwx "$LE_CONFIG_HOME"

# 复制运行脚本
COPY run.sh /
RUN chmod a+x /run.sh

# 数据卷
VOLUME ["/data", "/ssl"]

ENTRYPOINT ["/run.sh"]
CMD []
