#!/bin/bash
set -e

dnf update -y
dnf install -y python3.11 python3.11-pip git iptables

mkdir -p /home/ec2-user/app
git clone https://github.com/DeepandraSingh1225/stock-intelligence-terminal.git /home/ec2-user/app
chown -R ec2-user:ec2-user /home/ec2-user/app

sudo -u ec2-user python3.11 -m pip install --upgrade pip
sudo -u ec2-user python3.11 -m pip install -r /home/ec2-user/app/requirements.txt

iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000 || true

cat << 'EOF' > /etc/systemd/system/aeroquant.service
[Unit]
Description=AeroQuant Bloomberg Quantitative Terminal
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/app
Environment=PORT=5000
Environment=AWS_DEFAULT_REGION=us-east-1
Environment=AWS_API_GATEWAY_URL=https://kfc073dfuj.execute-api.us-east-1.amazonaws.com
ExecStart=/usr/bin/python3.11 -m gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aeroquant
systemctl start aeroquant
