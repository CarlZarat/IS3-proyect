import urllib.request, urllib.parse, http.cookiejar, re, sys, io

BASE = 'http://127.0.0.1:8000'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

resp = opener.open(BASE + '/ventas/nuevo/')
html = resp.read().decode('utf-8')
m = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html)
if not m:
    print('NO CSRF')
    sys.exit(1)
csrf = m.group(1)

data = {
    'csrfmiddlewaretoken': csrf,
    'cliente': '4',
    'fechafactura': '2026-06-19',
    'timbrado_registro': '1',
    'moneda': '3',
    'tipo_documento': '3',
    'plazo': '7',
    'tipo_vencimiento': 'regular',
    'cantidad_cuotas': '1',
    'dias_entre_cuotas': '30',
    'detalles-TOTAL_FORMS': '1',
    'detalles-INITIAL_FORMS': '0',
    'detalles-MIN_NUM_FORMS': '0',
    'detalles-MAX_NUM_FORMS': '1000',
    'detalles-0-producto_detalle': 'P10-001',
    'detalles-0-precio': '5000000',
    'detalles-0-cantidad': '1',
    'detalles-0-impuesto10': '500000',
    'detalles-0-total': '5000000',
}
post_data = urllib.parse.urlencode(data).encode('utf-8')
resp2 = opener.open(BASE + '/ventas/nuevo/', data=post_data)
print('STATUS:', resp2.status)
print('URL:', resp2.url)
html2 = resp2.read().decode('utf-8')
if resp2.status == 302 or 'redirect' in resp2.url.lower():
    print('OK: Venta creada (redirect)')
elif 'alert-danger' in html2 or 'text-danger' in html2:
    errs = re.findall(r'<div class="alert alert-danger">(.*?)</div>', html2, re.DOTALL)
    for e in errs:
        print('ERROR:', e.strip())
    errs2 = re.findall(r'<small class="text-danger[^"]*"[^>]*>(.*?)</small>', html2, re.DOTALL)
    for e in errs2:
        print('FIELD ERROR:', e.strip())
else:
    print('UNKNOWN response')
    if 'error' in html2.lower():
        m2 = re.search(r'(?i)error[^<]*<[^>]*>([^<]+)', html2)
        if m2:
            print('Error msg:', m2.group(1))
print('DONE')
