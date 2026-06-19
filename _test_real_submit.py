import urllib.request, urllib.parse, http.cookiejar, re, sys

BASE = 'http://127.0.0.1:8000/ventas/nuevo/'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Step 1: GET the form to get CSRF and initial values
resp = opener.open(BASE)
html = resp.read().decode('utf-8')

csrf = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html)
if not csrf:
    print('NO CSRF')
    sys.exit(1)
csrf = csrf.group(1)
print(f'CSRF: {csrf[:20]}...')

# Extract initial values
def get_val(html, name):
    m = re.search(f'name="{re.escape(name)}"[^>]*value="([^"]*)"', html)
    return m.group(1) if m else ''

nrofactura = get_val(html, 'nrofactura')
timbrado = get_val(html, 'timbrado')
timbrado_vence = get_val(html, 'timbrado_vence')
serie = get_val(html, 'serie')
totalexentas = get_val(html, 'totalexentas')
totalimponible = get_val(html, 'totalimponible')
totalfactura = get_val(html, 'totalfactura')

print(f'nrofactura={nrofactura}, serie={serie}, timbrado={timbrado}')

# Step 2: POST with real data
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
    'nrofactura': nrofactura or '44685',
    'serie': serie or '001-001',
    'timbrado': timbrado or '12345678',
    'timbrado_vence': timbrado_vence or '2027-06-18',
    'totalexentas': totalexentas or '0',
    'totalimponible': totalimponible or '5000000',
    'totalfactura': totalfactura or '5000000',
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

print(f'POSTing with nrofactura={data["nrofactura"]}...')

try:
    resp2 = opener.open(BASE, data=post_data)
    print('STATUS:', resp2.status)
    print('URL:', resp2.url)
    print('OK: Venta creada (redirect)')
    # Read response to confirm success message
    html2 = resp2.read().decode('utf-8')
    if 'success' in html2.lower() or 'exitosamente' in html2.lower():
        m = re.search(r'(?:success|exitosamente)[^<]*', html2, re.I)
        if m:
            print('MSG:', m.group(0))
except urllib.error.HTTPError as e:
    print('ERROR', e.code)
    body = e.read().decode('utf-8', errors='replace')
    # Look for traceback
    tb = re.search(r'Traceback.*?(?=</html>|\Z)', body, re.DOTALL)
    if tb:
        print(tb.group(0)[:2000])
    else:
        # Form errors
        errs = re.findall(r'<small class="text-danger[^"]*"[^>]*>(.*?)</small>', body, re.DOTALL)
        if errs:
            for e in errs:
                print('Field error:', re.sub(r'<[^>]+>', '', e).strip())
        errs2 = re.findall(r'<ul class="errorlist[^"]*"[^>]*>(.*?)</ul>', body, re.DOTALL)
        if errs2:
            for e in errs2:
                print('Form error:', re.sub(r'<[^>]+>', '', e).strip())
        if not errs and not errs2:
            print(body[:1500])
