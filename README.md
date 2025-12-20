# 🎥 CallMesh

A secure, registration-free video calling application with WebRTC support, built using Django and Vue.js.

README.md on english, [русском](README_ru.md)

## ✨ Features

- **🔐 Security**: Password-based authentication, CSRF protection
- **📱 Responsive**: Full support for mobile devices
- **🎯 Simplicity**: One-click room creation
- **⚡ WebRTC**: Direct P2P connection for minimal latency
- **🌙 Dark Mode**: Automatic switching based on system settings
- **📊 Monitoring**: Real-time connection quality statistics
- **🔄 PWA**: Progressive Web App support for installation on devices

## 🏗️ Architecture

```
📦 CallMesh
├── 🐍 Backend (Django)
│   ├── REST API
│   ├── WebSocket (Channels)
│   ├── Redis (caching and sessions)
│   └── PostgreSQL (database)
├── 🖥️ Frontend (Vue.js 3)
│   ├── Composition API
│   ├── Pinia (state management)
│   ├── TailwindCSS (styles)
│   └── WebRTC (video communication)
└── 🐳 Docker
    ├── Nginx (proxy)
    ├── PostgreSQL
    ├── Redis
    └── SSL/HTTPS
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/egorserdyuk/callmesh
cd callmesh
```

2. **Run with Docker Compose**
```bash
# Create .env file from example
cp env.example .env

# Start containers
docker-compose up --build
```

3. **Create a superuser**
```bash
docker-compose exec backend python manage.py createsuperuser
```

4. **Access the application**
- Frontend: http://localhost
- Backend API: http://localhost/api
- Admin panel: http://localhost/admin

## 📋 System Requirements

- **Server**: Ubuntu 20.04+ or similar Linux system
- **RAM**: Minimum 2GB, recommended 4GB+
- **CPU**: 2+ cores
- **Disk**: 20GB+ free space
- **Network**: Static IP or domain for SSL

## 🛠️ Production Deployment

### 1. Server Preparation

Update the system and install required packages:

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
```

### 2. Install Docker

**Add Docker keys and repository:**
```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
```

**Install Docker and components:**
```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Add user to Docker group:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. Install Nginx and Certbot

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### 5. Configure SSL Certificates

**Obtain Let's Encrypt certificates:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Stop system Nginx after obtaining certificates:**
```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### 6. Project Configuration

**Create environment file:**
```bash
cp env.example .env
```

**Configure variables in `.env`:**
```bash
# Core settings
DEBUG=False
SECRET_KEY=your-super-secret-django-key-here
DOMAIN_NAME=yourdomain.com

# Database
POSTGRES_PASSWORD=strong-database-password

# SSL certificate paths
SSL_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem

# Domains
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Update nginx.conf:**
Replace `yourdomain.com` with your actual domain in `nginx.conf`.

### 7. Start the Application

**Build and start containers:**
```bash
docker-compose up --build -d
```

**Create superuser:**
```bash
docker-compose exec backend python manage.py createsuperuser
```

**Check container status:**
```bash
docker-compose ps
```

### 8. Verify Deployment

- **Frontend**: https://yourdomain.com
- **Backend API**: https://yourdomain.com/api/health/
- **Admin panel**: https://yourdomain.com/admin/
- **WebSocket**: wss://yourdomain.com/ws/

## 🔧 Project Management

### Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop project
docker-compose down

# Full cleanup (including data)
docker-compose down -v --remove-orphans
```

### Updating the Project

```bash
# Fetch updates
git pull origin master

# Rebuild and restart
docker-compose up --build -d

# Apply migrations (if any)
docker-compose exec backend python manage.py migrate
```

### Backup

```bash
# Create database backup
docker-compose exec db pg_dump -U postgres videocall_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker-compose exec -T db psql -U postgres videocall_db < backup_file.sql
```

## 📊 Monitoring

### Health Check Endpoints

- **Overall status**: `/api/health/`
- **System metrics**: `/api/metrics/` (admins only)

### Logs

```bash
# All logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f db
```

## 🛡️ Security

### Security Recommendations

1. **Change the default password** in the admin panel
2. **Use strong passwords** for the database
3. **Renew SSL certificates regularly**
4. **Configure a firewall** to restrict access
5. **Monitor logs** for suspicious activity

### Firewall Setup (UFW)

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 🔧 Development

### Project Structure

```
📁 callmesh/
├── 📁 backend/                 # Django backend
│   ├── 📁 apps/               # Django apps
│   │   ├── 📁 authentication/ # Authentication system
│   │   ├── 📁 core/          # Core models and utilities
│   │   └── 📁 rooms/         # Room management
│   ├── 📁 videocall_app/     # Main Django settings
│   └── 🐳 Dockerfile
├── 📁 videocall-frontend/     # Vue.js frontend
│   ├── 📁 src/
│   │   ├── 📁 components/    # Vue components
│   │   ├── 📁 stores/        # Pinia stores
│   │   ├── 📁 services/      # API and utilities
│   │   └── 📁 router/        # Vue Router
│   └── 🐳 Dockerfile
├── 🐳 docker-compose.yml     # Docker Compose configuration
├── 📄 nginx.conf             # Nginx configuration
└── 📄 .env.example           # Environment variables example
```

### Local Development

```bash
# Backend (Python/Django)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt
python manage.py runserver

# Frontend (Vue.js)
cd videocall-frontend
npm install
npm run dev
```

