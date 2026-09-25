#!/usr/bin/env bash
set -e

cat << 'EOF' > /etc/nginx/sites-available/cristianreynaga.com
server {
        listen 80;
        listen [::]:80;

        root /var/www/cristianreynaga.com/html;
        index index.html index.htm index.nginx-debian.html;

        server_name cristianreynaga.com www.cristianreynaga.com;

        location = /bici {
                return 301 /bici/;
        }

        location /bici/ {
                proxy_pass http://127.0.0.1:8095/;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
                try_files $uri $uri/ =404;
        }

        location /api/extract {
                proxy_pass http://127.0.0.1:8100/api/extract;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
        }
}
EOF

cat << 'EOF' > /etc/nginx/sites-available/dev.cristianreynaga.com
server {

    server_name dev.cristianreynaga.com;

    root /var/www/dev.cristianreynaga.com;
    index index.html;

    location = /bici {
        return 301 /bici/;
    }

    location /bici/ {
        proxy_pass http://127.0.0.1:8095/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ =404;
    }

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/dev.cristianreynaga.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/dev.cristianreynaga.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = dev.cristianreynaga.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    listen [::]:80;

    server_name dev.cristianreynaga.com;
    return 404; # managed by Certbot

}
EOF

nginx -t
systemctl reload nginx
echo "Nginx successfully configured and reloaded!"
