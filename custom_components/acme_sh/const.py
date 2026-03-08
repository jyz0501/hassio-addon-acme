"""Constants for the ACME.sh integration."""
from typing import Final

DOMAIN: Final = "acme_sh"

CONF_DNS_PROVIDER: Final = "dns_provider"
CONF_DNS_ENV: Final = "dns_env"
CONF_KEYLENGTH: Final = "keylength"
CONF_DAYS: Final = "days"
CONF_STAGING: Final = "staging"
CONF_ACME_SERVER: Final = "acme_server"
CONF_AUTO_RENEW: Final = "auto_renew"
CONF_RENEW_INTERVAL: Final = "renew_interval"
CONF_FORCE_ISSUE: Final = "force_issue"

DEFAULT_KEYLENGTH: Final = "ec-256"
DEFAULT_DAYS: Final = 60
DEFAULT_ACME_SERVER: Final = "letsencrypt"
DEFAULT_DNS_PROVIDER: Final = "dns_cf"
DEFAULT_AUTO_RENEW: Final = True
DEFAULT_RENEW_INTERVAL: Final = "0 2 * * *"

ACME_SERVERS = {
    "letsencrypt": "Let's Encrypt",
    "letsencrypt_test": "Let's Encrypt (Staging)",
    "zerossl": "ZeroSSL",
    "google": "Google Trust Services",
    "googletest": "Google Trust Services (Test)",
    "buypass": "Buypass",
    "buypass_test": "Buypass (Test)",
    "sslcom": "SSL.com",
}

KEYLENGTH_OPTIONS = ["2048", "3072", "4096", "ec-256", "ec-384"]

DNS_PROVIDERS = {
    "dns_cf": "Cloudflare",
    "dns_ali": "阿里云",
    "dns_dp": "DNSPod",
    "dns_gd": "GoDaddy",
    "dns_aws": "AWS Route53",
    "dns_linode": "Linode",
    "dns_ovh": "OVH",
    "dns_do": "DigitalOcean",
    "dns_hetzner": "Hetzner",
    "dns_gandi": "Gandi",
    "dns_namecheap": "Namecheap",
    "dns_namesilo": "Namesilo",
    "dns_porkbun": "Porkbun",
    "dns_vultr": "Vultr",
}
