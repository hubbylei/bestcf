import os
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 从环境变量中读取Cloudflare的API相关信息
API_KEY = os.environ.get("CLOUDFLARE_API_TOKEN")
ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID")
ZONE_NAME = os.environ.get("CLOUDFLARE_ZONE_NAME")

def get_a_record(domain):
    url = f"https://doh.360.cn/resolve?name={domain}&type=A"
    response = requests.get(url)
    data = response.json()
    return [record['data'] for record in data.get('Answer', []) if record.get('type') == 1]

def delete_and_push_dns_records(ips):
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?name=best.{ZONE_NAME}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'result' in data:
            for record in data['result']:
                record_id = record['id']
                delete_dns_record(record_id)
    except requests.RequestException:
        pass  # 忽略错误

    for ip in ips:
        try:
            data = {
                "type": "A",
                "name": "best",
                "content": ip,
                "ttl": 60,
                "proxied": False
            }
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
        except requests.RequestException:
            pass  # 忽略错误

    print(f"best: Updated {len(ips)} IPs")

def delete_dns_record(record_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            print(f"Deleted record_id: {record_id}")
        else:
            raise Exception(f"Failed to delete DNS record with ID {record_id}: {response.text}")
    except requests.RequestException:
        pass  # 忽略错误

def main():
    domain = "jiasu.057150.xyz"
    print("Scanning proxy IP from various countries...")
    ips = get_a_record(domain)
    delete_and_push_dns_records(ips)
    print("DNS records update complete.")

if __name__ == "__main__":
    main()
