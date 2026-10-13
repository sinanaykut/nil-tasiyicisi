#!/bin/bash
# Build everything into dist/: the artifact page, a full preview page and the Netlify/PWA site zip.
set -e
cd "$(dirname "$0")"
python3 src/assemble.py
python3 - <<'PY'
p = open('dist/preview.html').read()
head = '<meta name="theme-color" content="#2B1D14"><link rel="manifest" href="manifest.webmanifest"><link rel="icon" type="image/png" sizes="192x192" href="icon-192.png"><link rel="apple-touch-icon" href="icon-180.png"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="Nil Kervancısı">'
import os, shutil
os.makedirs('dist/site', exist_ok=True)
open('dist/site/index.html', 'w').write(p.replace('<title>', head + '<title>', 1))
for f in os.listdir('site'): shutil.copy('site/' + f, 'dist/site/' + f)
shutil.copy('dist/site/index.html', 'dist/nil-kervancisi.html')
PY
(cd dist/site && rm -f ../nil-kervancisi-site.zip && zip -qr ../nil-kervancisi-site.zip .)
ls -la dist
