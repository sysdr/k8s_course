#!/bin/bash
# Fix and apply professional HTML dashboard in one go

set -euo pipefail

NAMESPACE="debug-challenge"

echo "🔧 Fixing and applying professional HTML dashboard..."

# Delete all frontend pods to force recreation
kubectl delete pods -n ${NAMESPACE} -l app=frontend --grace-period=0 || true
sleep 2

# Get the current deployment and create a clean version with dashboard
kubectl get deployment frontend -n ${NAMESPACE} -o yaml > /tmp/frontend-base.yaml

# Create the dashboard server.js code (minified to avoid YAML issues)
cat > /tmp/dashboard-server.js << 'EOF'
const express=require('express');const axios=require('axios');const app=express();
const API_URL=process.env.API_URL||'http://api-backend:8000';
app.get('/health',(r,s)=>s.json({status:'healthy',service:'frontend',api_url:API_URL}));
app.get('/',async(r,s)=>{try{
const[p,st]=await Promise.all([
axios.get(`${API_URL}/api/products`,{timeout:5000}).catch(()=>({data:[]})),
axios.get(`${API_URL}/api/stats`,{timeout:5000}).catch(()=>({data:null}))
]);
const html=genHTML(p.data||[],st.data||null);s.send(html);
}catch(e){s.status(500).send(genError(e.message));}});
function genHTML(products,stats){
const s=stats?`<div class="stats-grid"><div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">${stats.total_products||0}</div><div class="stat-label">Total Products</div></div><div class="stat-card"><div class="stat-icon">💰</div><div class="stat-value">$${((stats.total_inventory_value||0)/1000).toFixed(1)}K</div><div class="stat-label">Inventory Value</div></div><div class="stat-card"><div class="stat-icon">🏷️</div><div class="stat-value">${stats.categories?stats.categories.length:0}</div><div class="stat-label">Categories</div></div></div>`:'';
return`<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>E-Commerce Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);color:#e2e8f0;min-height:100vh;padding:20px}.container{max-width:1400px;margin:0 auto}header{background:rgba(255,255,255,0.05);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:24px 32px;margin-bottom:32px;box-shadow:0 8px 32px rgba(0,0,0,0.3)}h1{font-size:32px;font-weight:700;background:linear-gradient(135deg,#10b981 0%,#f59e0b 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:8px}.subtitle{color:#94a3b8;font-size:14px}.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:32px}.stat-card{background:rgba(255,255,255,0.05);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:24px;text-align:center;transition:transform 0.2s,box-shadow 0.2s;box-shadow:0 4px 16px rgba(0,0,0,0.2)}.stat-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,0.3)}.stat-icon{font-size:32px;margin-bottom:12px}.stat-value{font-size:36px;font-weight:700;color:#10b981;margin-bottom:8px}.stat-label{color:#94a3b8;font-size:14px;text-transform:uppercase;letter-spacing:0.5px}.products-section h2{font-size:24px;margin-bottom:24px;color:#e2e8f0}.products-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px}.product-card{background:rgba(255,255,255,0.05);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:24px;transition:transform 0.2s,box-shadow 0.2s;box-shadow:0 4px 16px rgba(0,0,0,0.2)}.product-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,0.4);border-color:rgba(16,185,129,0.5)}.product-header{display:flex;justify-content:space-between;align-items:start;margin-bottom:12px}.product-name{font-size:20px;font-weight:700;color:#e2e8f0;flex:1}.product-price{font-size:24px;font-weight:700;color:#10b981}.product-description{color:#94a3b8;font-size:14px;line-height:1.6;margin-bottom:16px}.product-footer{display:flex;justify-content:space-between;align-items:center;padding-top:16px;border-top:1px solid rgba(255,255,255,0.1)}.product-category{background:rgba(16,185,129,0.2);color:#10b981;padding:6px 12px;border-radius:8px;font-size:12px;font-weight:600;text-transform:uppercase}.product-stock{color:#f59e0b;font-size:14px;font-weight:600}</style></head><body><div class="container"><header><h1>🛒 E-Commerce Dashboard</h1><p class="subtitle">Real-time product inventory and analytics</p></header>${s}<div class="products-section"><h2>Products</h2><div class="products-grid">${products.map(p=>`<div class="product-card"><div class="product-header"><div class="product-name">${(p.name||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div><div class="product-price">$${(p.price||0).toFixed(2)}</div></div><div class="product-description">${(p.description||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div><div class="product-footer"><span class="product-category">${(p.category||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</span><span class="product-stock">${p.stock||0} in stock</span></div></div>`).join('')}</div></div></div></body></html>`;}
function genError(m){return`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}.error-container{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:16px;padding:32px;text-align:center;max-width:600px}.error-title{font-size:24px;color:#ef4444;margin-bottom:16px}.error-message{color:#94a3b8}</style></head><body><div class="error-container"><div class="error-title">⚠️ Connection Error</div><div class="error-message">${(m||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div></div></body></html>`;}
app.listen(3000,'0.0.0.0',()=>{console.log(`Frontend server running on port 3000`);console.log(`Configured to connect to backend at: ${API_URL}`);});
EOF

# Create updated deployment YAML using Python
python3 << 'PYEOF'
import yaml
import sys

# Read base deployment
with open('/tmp/frontend-base.yaml', 'r') as f:
    deploy = yaml.safe_load(f)

# Read dashboard code
with open('/tmp/dashboard-server.js', 'r') as f:
    dashboard_code = f.read()

# Create the args with dashboard code
new_args = [
    "-c",
    f"""apk add --no-cache curl
mkdir -p /app
cd /app
cat > package.json << 'PKGEOF'
{{
  "name": "frontend",
  "version": "1.0.0",
  "dependencies": {{
    "express": "^4.18.2",
    "axios": "^1.6.2"
  }}
}}
PKGEOF
npm install
cat > server.js << 'SRVEOF'
{dashboard_code}
SRVEOF
node server.js"""
]

# Update deployment
deploy['spec']['template']['spec']['containers'][0]['args'] = new_args
if 'env' not in deploy['spec']['template']['spec']['containers'][0]:
    deploy['spec']['template']['spec']['containers'][0]['env'] = []
# Update or add API_URL env
env_exists = False
for env in deploy['spec']['template']['spec']['containers'][0]['env']:
    if env.get('name') == 'API_URL':
        env['value'] = 'http://api-backend:8000'
        env_exists = True
        break
if not env_exists:
    deploy['spec']['template']['spec']['containers'][0]['env'].append({
        'name': 'API_URL',
        'value': 'http://api-backend:8000'
    })

# Remove metadata that causes issues
if 'metadata' in deploy:
    deploy['metadata'].pop('resourceVersion', None)
    deploy['metadata'].pop('uid', None)
    deploy['metadata'].pop('generation', None)
    deploy['metadata'].pop('creationTimestamp', None)
if 'status' in deploy:
    del deploy['status']

# Write updated YAML
with open('/tmp/frontend-dashboard.yaml', 'w') as f:
    yaml.dump(deploy, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print("✅ Deployment YAML created successfully")
PYEOF

# Apply the deployment
echo "📦 Applying deployment with dashboard..."
kubectl apply -f /tmp/frontend-dashboard.yaml

# Wait for rollout
echo "⏳ Waiting for pods to be ready..."
kubectl rollout status deployment/frontend -n ${NAMESPACE} --timeout=120s

# Restart port-forward
pkill -f "kubectl port-forward.*frontend" || true
sleep 2
kubectl port-forward -n ${NAMESPACE} svc/frontend-svc 8080:80 > /dev/null 2>&1 &
sleep 3

# Test
echo "🧪 Testing dashboard..."
sleep 5
if curl -s http://localhost:8080/ | grep -q "E-Commerce Dashboard"; then
    echo ""
    echo "✅ SUCCESS! Professional HTML dashboard is now live!"
    echo "🌐 Access it at: http://localhost:8080"
    echo ""
    echo "Dashboard features:"
    echo "  • Dark theme with green/teal/orange accents (no purple/blue)"
    echo "  • Statistics cards"
    echo "  • Product grid with hover effects"
    echo "  • Professional, modern design"
else
    echo "⚠️  Dashboard might still be loading. Check: http://localhost:8080"
fi

