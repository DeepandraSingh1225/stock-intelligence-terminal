import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

user_data = "#!/bin/bash
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
ExecStart=/usr/bin/python3.11 -m uvicorn server:app --host 0.0.0.0 --port 5000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aeroquant
systemctl start aeroquant
"

print(Launching EC2 t2.micro instance...)
res = ec2.run_instances(
    ImageId=ami-0354c98ae10b02961,
    InstanceType=t2.micro,
    MinCount=1,
    MaxCount=1,
    SecurityGroupIds=[sg-04cb7513abef2ff7f],
    IamInstanceProfile={Name: AeroQuantEC2Profile},
    UserData=user_data,
    TagSpecifications=[
        {
            ResourceType: instance,
            Tags: [{Key: Name, Value: AeroQuant-Terminal}]
        }
    ]
)

inst_id = res[Instances][0][InstanceId]
print(fEC2 Instance launched successfully! Instance ID: {inst_id})
