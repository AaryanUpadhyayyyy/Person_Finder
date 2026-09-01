#!/bin/bash
exec > >(tee -i /var/log/user-data.log)
exec 2>&1

# Add 4GB Swap file to prevent OOM
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

sudo apt-get update
sudo apt-get install -y docker.io git curl debian-keyring debian-archive-keyring apt-transport-https

# Install Caddy for Auto HTTPS
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update
sudo apt-get install caddy -y

# Clone Repo and Build
cd /home/ubuntu
git clone https://github.com/AaryanUpadhyayyyyy/Person_Finder.git
cd Person_Finder/face_id_blockchain
sudo docker build -t backend .
sudo docker run -d -p 10000:7860 backend

# Get EC2 Public IP and set up Auto-HTTPS domain
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
cat <<EOF > /etc/caddy/Caddyfile
${PUBLIC_IP}.nip.io {
    reverse_proxy localhost:10000
}
EOF
sudo systemctl restart caddy
