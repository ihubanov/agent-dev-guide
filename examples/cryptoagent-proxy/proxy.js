const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');
dotenv.config();

const app = express();

const PROXY_TARGET = process.env.PROXY_TARGET || 'http://localhost:8000';
const PROXY_HOST = process.env.PROXY_HOST || 'localhost';
const PROXY_PORT = process.env.PROXY_PORT || 3080;

//console.log('[DEBUG] Loaded config:', { PROXY_TARGET, PROXY_HOST, PROXY_PORT });

app.use(cors());

// Serve chat.html at /chat
app.get('/chat', (req, res) => {
    console.info('[INFO] Serving chat.html at /chat (', `http://${PROXY_HOST}:${PROXY_PORT}/chat`, ')');
    res.sendFile(path.join(__dirname, 'chat.html'));
});

// Proxy everything else
app.use('/', createProxyMiddleware({
    target: PROXY_TARGET,
    changeOrigin: true,
    ws: true,
    pathRewrite: { '^/': '/' },
    // Exclude /chat from proxy
    onProxyReq: (proxyReq, req, res) => {
        if (req.path === '/chat') {
            res.end();
        }
    }
}));

app.listen(PROXY_PORT, PROXY_HOST, () => {
    console.info(`CORS proxy running on http://${PROXY_HOST}:${PROXY_PORT}`);
    console.info(`[INFO] Chat UI available at http://${PROXY_HOST}:${PROXY_PORT}/chat`);
});