#!/usr/bin/env python3
"""Build the single-file game from its parts.

usage:  python3 src/assemble.py [SRC_DIR] [OUT_NAME]
  SRC_DIR   folder with the parts (default p33)
  OUT_NAME  writes OUT_NAME.html (artifact body) and OUT_NAME-preview.html (full page);
            default v33 -> v33.html and preview33.html (in the scratchpad root)

Layout of SRC_DIR (everything is concatenated in this order into one IIFE):
  core.txt, v8-merchants.txt, merch27.txt, v8-portrait.txt, snd.txt,
  sea/*.txt, ui/*.txt (sorted by their NN- prefix), then MODULES, then boot.txt
  CSS: css.txt + CSS_MODULES;  sprites: v8-sprites.svg + sprites27.txt
  chars33.dat (town people kit) is an inert data block placed before the script.
  Close-up characters are code-drawn SVG (chars40.txt + chars40.css).
A folder (ui/, sea/, v3/) is the same as one big file: its parts are joined in name order.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'src'
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if not os.path.isabs(SRC): SRC = os.path.join(ROOT, SRC)
MODULES = ['art27.txt', 'art28.txt', 'chars40.txt', 'chars30.txt', 'logo31.txt', 'v3', 'world33.txt', 'town29.txt',
           'temple.txt', 'temple42.txt', 'senet.txt', 'tavern42.txt', 'mini.txt', 'haggle28.txt', 'chars33.txt']
CSS_MODULES = ['css27.txt', 'art27.css', 'v3.css', 'town29.css', 'temple.css', 'temple42.css', 'senet.css', 'tavern42.css', 'mini.css', 'css28.txt',
               'art28.css', 'haggle28.css', 'motion35.css', 'chars40.css']
CSS_MODULES += ['voy42.css']   # v42: route token, road tombs, arrival ledger
def r(f, opt=False):
    p = os.path.join(SRC, f)
    if os.path.isdir(p): return ''.join(open(os.path.join(p, x)).read() for x in sorted(os.listdir(p)) if x.endswith('.txt'))
    if not os.path.exists(p):
        if opt: return ''
        raise SystemExit('missing part: ' + p)
    return open(p).read()
sprites = r('v8-sprites.svg').replace('<linearGradient id="gFogB"', '<linearGradient id="gFogBx"')
i = sprites.rfind('</svg>')
sprites = sprites[:i] + '  <symbol id="i-menu" viewBox="0 0 32 32"><path d="M6 9h20M6 16h20M6 23h20" stroke="currentColor" stroke-width="2.8" stroke-linecap="round"/></symbol>\n  <symbol id="i-bolt" viewBox="0 0 32 32"><path d="M18 3 7 18h8l-3 11 13-17h-8l3-9Z" fill="currentColor"/></symbol>\n  <symbol id="i-storm" viewBox="0 0 32 32"><g fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M6 14a6 6 0 0 1 11-4 5 5 0 0 1 8 5H6Z" fill="currentColor"/><path d="M9 20l-2 5M15 20l-2 6M21 20l-2 5"/></g></symbol>\n  <symbol id="i-moon" viewBox="0 0 32 32"><path d="M20 4a12 12 0 1 0 8 19A10 10 0 0 1 20 4Z" fill="currentColor"/></symbol>\n' + r('sprites27.txt', True) + r('sprites28.txt', True) + sprites[i:]
head = '''<title>Nil Kervancısı</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&family=Cinzel:wght@600;700&family=Nunito:wght@400;600;700;800&display=swap">
'''
pre = '''(function () {
  'use strict';
  const $ = s => document.querySelector(s);
  const KEY = 'nil-kervanci-v10', RECK = 'nil-kervanci-v9-rec', SLOTK = 'nil-kervanci-v10-slot', METAK = 'nil-kervanci-meta10', MUS = 'nil-kervanci-music', SFX = 'nil-kervanci-sfx';
  const lsGet = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const jget = (k, d) => { try { const v = JSON.parse(lsGet(k)); return v == null ? d : v; } catch (e) { return d; } };
'''
core = r('core.txt').replace('/*CORE*/', '').replace('/*ENDCORE*/', '')
mods = ''.join('\n' + r(f, True) for f in MODULES)
css = r('css.txt')
extra_css = ''.join(r(f, True) for f in CSS_MODULES)
j = css.rfind('</style>'); css = css[:j] + extra_css + '\n' + css[j:]
out = (head + css + '\n' + sprites + '\n' + r('body.txt') + '\n' + r('chars33.dat', True) + '\n<script>\n' + pre + core + '\n' + r('v8-merchants.txt') + '\n' +
       r('merch27.txt', True) + '\n  let uid = 0;\n' + r('v8-portrait.txt') + '\n' + r('snd.txt') + '\n' + r('sea') + '\n' + r('ui') + mods + '\n' + r('boot.txt') + '\n})();\n</script>\n')
a, b = (os.path.join(ROOT, OUT + '.html'), os.path.join(ROOT, OUT + '-preview.html')) if OUT else (os.path.join(ROOT, 'dist', 'nil-kervanci.html'), os.path.join(ROOT, 'dist', 'preview.html'))
os.makedirs(os.path.dirname(a), exist_ok=True)
open(a, 'w').write(out)
open(b, 'w').write('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + out + '</html>')
print(len(out), a, b)
