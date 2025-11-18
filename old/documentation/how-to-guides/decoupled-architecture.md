# Decoupled Architecture Setup

This guide explains how to set up MDJourney with a decoupled architecture where the backend runs on a headless server and the frontend runs locally, connected via SSH tunnel.

## Architecture Overview

```
┌─────────────────┐    SSH Tunnel    ┌─────────────────┐
│   Local Machine │ ◄──────────────► │  Remote Server  │
│                 │                  │                 │
│  ┌───────────┐  │                  │  ┌───────────┐  │
│  │ Frontend  │  │                  │  │  Backend  │  │
│  │ (React)   │  │                  │  │   API     │  │
│  └───────────┘  │                  │  └───────────┘  │
│                 │                  │                 │
│  ┌───────────┐  │                  │  ┌───────────┐  │
│  │ SSH Tunnel│  │                  │  │  Monitor  │  │
│  │ Port 8000 │  │                  │  │  Service  │  │
│  └───────────┘  │                  │  └───────────┘  │
└─────────────────┘                  └─────────────────┘
```

## Server Setup (Backend)

### 1. Deploy Backend Services

On your remote server, deploy only the backend services:

```bash
# Clone the repository
git clone <repository-url>
cd mdjourney-dev

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Deploy backend services (one-time setup may be needed, see below)
make start-backend
```

### 2. Configure Server Environment

Create a `.env` file on the server:

```bash
# Server Configuration
API_PORT=8000
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-redis-password

# Security
MDJOURNEY_API_KEY=your-secure-api-key-here

# Data paths
MONITOR_PATH=/app/monitor
SCHEMAS_PATH=/app/schemas
```

### 3. Verify Backend Deployment

Check that services are running:

```bash
# Check service status
docker-compose -f docker-compose.backend.yml ps

# Test API health
curl http://localhost:8000/api/v1/health
```

## Local Setup (Frontend)

### 1. Install Frontend Dependencies

On your local machine:

```bash
# Install frontend dependencies
make frontend-install
```

### 2. Configure Frontend Environment

Create a `.env.local` file in the frontend directory:

```bash
# In frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=10000
```

**Note:** The `.env.local` file is automatically ignored by git, so your local configuration won't be committed to the repository. The default `http://localhost:8000` in the source code acts as a fallback for development.

### 3. Start SSH Tunnel

Simply run the SSH tunnel command:

```bash
ssh -L 8000:localhost:8000 <username>@<server-host> -N
```

This creates a tunnel from your local port 8000 to the server's port 8000. The `-N` flag tells SSH not to execute any commands, just forward the port.

If your backend runs on KU Leuven HPC (compute node behind a login node), forward to the compute node via your login alias:

```bash
# Replace values accordingly
ssh -L 8000:<compute_node>:8000 vsc -N
# Example
ssh -L 8080:r23n10:8000 vsc -N
```

Then open in your browser:

```
http://localhost:8080/docs
```

### 4. Start Frontend Development Server

```bash
# Start frontend development server
make up-frontend
```

## SSH Tunnel Management

### Simple SSH Tunnel Commands

```bash
# Start tunnel
ssh -L 8000:localhost:8000 <username>@<server-host> -N

# Stop tunnel (Ctrl+C in the terminal where it's running)

# Check if tunnel is running
ps aux | grep "ssh.*-L.*8000"
```

### Background Tunnel (Optional)

If you want to run the tunnel in the background:

```bash
# Start tunnel in background
ssh -L 8000:localhost:8000 <username>@<server-host> -N -f

# Stop background tunnel
pkill -f "ssh.*-L.*8000"
```

### KU Leuven HPC: Compute-node tunneling

When services (e.g., FastAPI, Jupyter) run on HPC compute nodes, tunnel through the login node to the compute node.

1. Identify the compute node where your service runs:
   ```bash
   hostname            # when on the compute node
   squeue -u $USER     # via scheduler
   ```
   Note: Services usually do not run on the login node.

2. Create the tunnel from your local machine:
   ```bash
   ssh -L <local_port>:<compute_node>:<remote_port> <login_node_alias> -N
   # Example
   ssh -L 8080:r23n10:8000 vsc -N
   ```

3. (Optional) Use an SSH config alias in `~/.ssh/config` to simplify commands:
   ```
   Host vsc
       HostName login.hpc.kuleuven.be
       User <your_username>
       IdentityFile ~/.ssh/id_rsa
   ```

4. Verify the tunnel:
   ```bash
   curl http://localhost:8080
   ```

5. Troubleshooting quick checks:
   - Connection refused: Ensure the service is listening on the compute node and port.
   - Address already in use: Pick a free local port, e.g. `-L 8081:...`.
   - Web login prompt: Complete the web-based login then retry SSH.
   - Silent terminal with `-N`: Test via `curl http://localhost:<local_port>`.

## Development Workflows

### Option 1: Fully Decoupled (Recommended)

```bash
# On server: Start backend
make start-backend

# On local: Start tunnel and frontend
ssh -L 8000:localhost:8000 <username>@<server-host> -N &
make up-frontend
```

### Option 2: Local Backend + Frontend

```bash
# Start both locally
make dev-all
```

### Option 3: Mixed Development

```bash
# Start local backend
make start-api

# Start frontend (connects to local backend)
make up-frontend
```

## Troubleshooting

### SSH Tunnel Issues

**Connection refused:**
```bash
# Check if tunnel is running
make tunnel-status

# Verify server connectivity
ssh $MDJ_SERVER_USER@$MDJ_SERVER_HOST "curl http://localhost:8000/api/v1/health"
```

**Permission denied:**
```bash
# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa

# Test SSH connection
ssh -i ~/.ssh/id_rsa $MDJ_SERVER_USER@$MDJ_SERVER_HOST
```

**Port already in use:**
```bash
# Change local port
export MDJ_LOCAL_PORT=8001
make tunnel-restart
```

### Frontend Connection Issues

**API not reachable:**
```bash
# Check tunnel status
make tunnel-status

# Test API directly
curl http://localhost:8000/api/v1/health

# Check frontend configuration
echo $VITE_API_BASE_URL
```

**CORS errors:**
- Ensure `VITE_API_BASE_URL` points to tunnel port
- Check server CORS configuration

### Backend Issues

**Services not starting:**
```bash
# Check logs
docker-compose -f docker-compose.backend.yml logs

# Restart services
make down
make start-backend
```

**File permissions:**
```bash
# Fix volume permissions
sudo chown -R $USER:$USER monitor/ schemas/
```

## Security Considerations

### SSH Security

1. **Use SSH keys instead of passwords:**
   ```bash
   ssh-keygen -t rsa -b 4096
   ssh-copy-id $MDJ_SERVER_USER@$MDJ_SERVER_HOST
   ```

2. **Disable password authentication on server:**
   ```bash
   # In /etc/ssh/sshd_config
   PasswordAuthentication no
   PubkeyAuthentication yes
   ```

3. **Use non-standard SSH port:**
   ```bash
   # In /etc/ssh/sshd_config
   Port 2222
   ```

### API Security

1. **Use strong API keys:**
   ```bash
   export MDJOURNEY_API_KEY=$(openssl rand -hex 32)
   ```

2. **Restrict API access:**
   - Use firewall rules
   - Consider VPN instead of SSH tunnel for production

3. **Monitor access logs:**
   ```bash
   docker-compose -f docker-compose.backend.yml logs api
   ```

## Production Deployment

### Server Hardening

1. **Update system packages:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Configure firewall:**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 8000
   sudo ufw enable
   ```

3. **Set up monitoring:**
   ```bash
   # Add health check monitoring
   curl -f http://localhost:8000/api/v1/health || alert
   ```

### Backup Strategy

1. **Backup data volumes:**
   ```bash
   docker run --rm -v mdjourney_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .
   ```

2. **Backup configuration:**
   ```bash
   cp .env .env.backup
   cp docker-compose.backend.yml docker-compose.backend.yml.backup
   ```

## Performance Optimization

### SSH Tunnel Optimization

1. **Use compression:**
   ```bash
   ssh -C -L 8000:localhost:8000 $MDJ_SERVER_USER@$MDJ_SERVER_HOST
   ```

2. **Keep connection alive:**
   ```bash
   # In ~/.ssh/config
   Host your-server
       ServerAliveInterval 60
       ServerAliveCountMax 3
   ```

### Frontend Optimization

1. **Enable caching:**
   ```bash
   # In frontend/.env
   VITE_API_TIMEOUT=30000
   ```

2. **Use production build:**
   ```bash
   make frontend-build
   make frontend-preview
   ```

## Monitoring and Maintenance

### Health Checks

```bash
# Check all services
make tunnel-status
curl http://localhost:8000/api/v1/health

# Check server resources
ssh $MDJ_SERVER_USER@$MDJ_SERVER_HOST "docker stats"
```

### Log Management

```bash
# View logs
docker-compose -f docker-compose.backend.yml logs -f

# Rotate logs
docker system prune -f
```

This decoupled architecture provides flexibility for development while maintaining security and performance for production deployments.
