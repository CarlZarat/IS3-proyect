import urllib.request, urllib.parse, http.cookiejar, re, sys

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
try:
    resp2 = opener.open(BASE + '/ventas/nuevo/', data=post_data)
    print('STATUS:', resp2.status)
    print('URL:', resp2.url)
    print('OK: Venta creada')
except urllib.error.HTTPError as e:
    print('ERROR', e.code)
    body = e.read().decode('utf-8', errors='replace')
    tb = re.search(r'Traceback.*?(?=</html>|\Z)', body, re.DOTALL)
    if tb:
        print(tb.group(0)[:3000])
    else:
        # check for form errors
        errs = re.findall(r'<ul class="errorlist[^"]*"[^>]*>(.*?)</ul>', body, re.DOTALL)
        for err in errs:
            print('Form error:', re.sub(r'<[^>]+>', '', err).strip())
        if not errs:
            print('Response snippet:', body[:1500])
