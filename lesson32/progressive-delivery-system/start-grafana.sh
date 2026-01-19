#!/bin/bash
cd /home/systemdr03/git/k8s_course/lesson32/progressive-delivery-system
export PATH=\C:\Users\syste/bin:/usr/local/bin:/usr/bin:/bin:export KUBECONFIG=/tmp/kubeconfig-progressive

pkill -f 'kubectl.*port-forward' 2>/dev/null
kubectl port-forward -n progressive-delivery svc/grafana 30300:3000 > /tmp/grafana-pf.log 2>&1 &

sleep 3
echo 'Port forwarding started!'
echo 'Access Grafana at: http://localhost:30300'
ps aux | grep '[k]ubectl.*port-forward.*grafana'
