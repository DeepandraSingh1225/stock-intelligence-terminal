import boto3
import time

ssm = boto3.client('ssm', region_name='us-east-1')

shell_script = """#!/bin/bash
set -e

# 1. Download and install cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "Installing Cloudflared..."
    curl -L --output /tmp/cloudflared.rpm https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
    dnf install -y /tmp/cloudflared.rpm
fi

# 2. Setup persistent systemd service
cat << 'EOF' > /etc/systemd/system/cloudflared-tunnel.service
[Unit]
Description=Cloudflare Tunnel for AeroQuant
After=network.target aeroquant.service

[Service]
ExecStart=/usr/local/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:5000
Restart=always
RestartSec=5
StandardOutput=append:/var/log/cloudflared.log
StandardError=append:/var/log/cloudflared.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cloudflared-tunnel
systemctl restart cloudflared-tunnel

sleep 6
echo "=== CLOUDFLARE_URL ==="
grep -o 'https://[a-zA-Z0-9-]*\\.trycloudflare\\.com' /var/log/cloudflared.log | tail -n 1
"""

print("Sending SSM command to install Cloudflare HTTPS Tunnel on EC2...")
res = ssm.send_command(
    InstanceIds=['i-049dd8f1c4ea8ab28'],
    DocumentName='AWS-RunShellScript',
    Parameters={'commands': [shell_script]}
)

cmd_id = res['Command']['CommandId']
print(f"SSM Command sent! Command ID: {cmd_id}")

print("Waiting for SSM execution...")
for i in range(12):
    time.sleep(3)
    try:
        inv = ssm.get_command_invocation(CommandId=cmd_id, InstanceId='i-049dd8f1c4ea8ab28')
        status = inv.get('Status')
        if status in ('Success', 'Failed', 'TimedOut', 'Cancelled'):
            print(f"Execution finished with status: {status}")
            stdout = inv.get('StandardOutputContent', '')
            stderr = inv.get('StandardErrorContent', '')
            print("STDOUT:")
            print(stdout)
            if stderr:
                print("STDERR:")
                print(stderr)
            break
    except Exception as e:
        print(f"Waiting... ({e})")
