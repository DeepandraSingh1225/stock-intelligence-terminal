import boto3
import time

ec2 = boto3.client('ec2', region_name='us-east-1')

user_data_script = """#!/bin/bash
exec > >(tee -a /var/log/aeroquant_bootstrap.log) 2>&1
echo "=== Starting AeroQuant EC2 Bootstrap: $(date) ==="

# 1. Setup 2GB Swap space to ensure smooth pip builds on 1GB RAM
if [ ! -f /swapfile ]; then
    echo "Creating 2GB swap file..."
    dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 2. Update and install packages
echo "Installing Python 3.11, Git, and iptables..."
dnf update -y
dnf install -y python3.11 python3.11-pip git iptables

# 3. Clone repository
echo "Cloning AeroQuant repository..."
mkdir -p /home/ec2-user/app
rm -rf /home/ec2-user/app/*
git clone https://github.com/DeepandraSingh1225/stock-intelligence-terminal.git /home/ec2-user/app
chown -R ec2-user:ec2-user /home/ec2-user/app

# 4. Install optimized Python dependencies
echo "Installing Python requirements..."
sudo -u ec2-user python3.11 -m pip install --upgrade pip
sudo -u ec2-user python3.11 -m pip install --no-cache-dir -r /home/ec2-user/app/requirements.txt

# 5. Configure Port 80 -> 5000 redirect
echo "Setting up iptables redirect..."
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000 || true

# 6. Setup systemd service for AeroQuant
echo "Configuring systemd service..."
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

# 7. Enable and Start service
systemctl daemon-reload
systemctl enable aeroquant
systemctl start aeroquant

echo "=== AeroQuant Bootstrap Completed Successfully: $(date) ==="
"""

print("Launching EC2 t3.micro instance with 15GB disk in us-east-1...")
response = ec2.run_instances(
    ImageId='ami-0354c98ae10b02961',
    InstanceType='t3.micro',
    MinCount=1,
    MaxCount=1,
    SecurityGroupIds=['sg-04cb7513abef2ff7f'],
    UserData=user_data_script,
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/xvda',
            'Ebs': {
                'VolumeSize': 15,
                'VolumeType': 'gp3',
                'DeleteOnTermination': True
            }
        }
    ],
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': 'AeroQuant-Terminal-Live'}
            ]
        }
    ]
)

instance = response['Instances'][0]
instance_id = instance['InstanceId']
print(f"Launched instance ID: {instance_id}")

print("Waiting for instance to enter 'running' state and obtain public IP...")
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])

desc = ec2.describe_instances(InstanceIds=[instance_id])
inst_info = desc['Reservations'][0]['Instances'][0]
public_ip = inst_info.get('PublicIpAddress')
public_dns = inst_info.get('PublicDnsName')

print(f"Instance is RUNNING!")
print(f"Public IP:  {public_ip}")
print(f"Public DNS: {public_dns}")
print(f"Web URLs:   http://{public_ip}:5000 / http://{public_ip}")

with open('ec2_instance.txt', 'w') as f:
    f.write(f"{instance_id},{public_ip},{public_dns}\n")
