from django.db import models


class Moneda(models.Model):
	moneda = models.CharField(max_length=50)
	abreviatura = models.CharField(max_length=5)
	decimales = models.PositiveSmallIntegerField(default=0)
	activo = models.BooleanField(default=True)

	class Meta:
		db_table = 'MONEDAS'

	def __str__(self):
		return self.abreviatura


class Cliente(models.Model):
	nombre = models.CharField(max_length=200)
	apellido = models.CharField(max_length=200, blank=True)
	documento = models.CharField(max_length=20, blank=True, db_column='ruc')
	direccion = models.CharField(max_length=200, blank=True)
	email = models.CharField(max_length=200, blank=True)
	telefono = models.CharField(max_length=200, blank=True)
	activo = models.BooleanField(default=True)

	class Meta:
		# Usar la misma tabla que la app `clientes` para reutilizar los registros existentes.
		# Este modelo actúa como un alias hacia esa tabla y no será gestionado
		# por las migraciones de Django para evitar conflictos de esquema.
		db_table = 'clientes_cliente'
		managed = False

	def __str__(self):
		full_name = f"{self.nombre} {self.apellido}".strip()
		return full_name or self.documento


class Deposito(models.Model):
	deposito = models.CharField(max_length=200)
	direccion = models.CharField(max_length=150, blank=True)
	telefono = models.CharField(max_length=15, blank=True)

	class Meta:
		db_table = 'DEPOSITOS'

	def __str__(self):
		return self.deposito


class TipoDocumento(models.Model):
	tipo = models.CharField(max_length=200)
	abreviatura = models.CharField(max_length=5)
	tipoid = models.PositiveIntegerField(default=0)
	activo = models.BooleanField(default=True)

	class Meta:
		db_table = 'TIPOS_DOCUMENTO'

	def __str__(self):
		return self.abreviatura


class Timbrado(models.Model):
	ESTADO_VIGENTE = 'vigente'
	ESTADO_VENCIDO = 'vencido'
	ESTADO_ANULADO = 'anulado'
	ESTADO_CHOICES = [
		(ESTADO_VIGENTE, 'Vigente'),
		(ESTADO_VENCIDO, 'Vencido'),
		(ESTADO_ANULADO, 'Anulado'),
	]

	numero = models.CharField(max_length=20)
	serie = models.CharField(max_length=20)
	nro_inicio = models.PositiveIntegerField(default=1)
	nro_fin = models.PositiveIntegerField(default=1)
	fecha_vencimiento = models.DateField()
	estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_VIGENTE)

	class Meta:
		db_table = 'TIMBRADOS'

	def __str__(self):
		return f'{self.numero} - {self.serie} ({self.nro_inicio}-{self.nro_fin})'


class Plazo(models.Model):
	plazo = models.CharField(max_length=100)
	tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, db_column='tipoid')
	cuotas = models.PositiveIntegerField(default=1)
	irregular = models.BooleanField(default=False)

	class Meta:
		db_table = 'PLAZOS'

	def __str__(self):
		return self.plazo


class Venta(models.Model):
	fechaproce = models.DateTimeField()
	fechafactura = models.DateField()
	cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_column='clienteid')
	timbrado_registro = models.ForeignKey(Timbrado, on_delete=models.PROTECT, null=True, blank=True, db_column='timbradoid')
	serie = models.CharField(max_length=10)
	nrofactura = models.PositiveIntegerField()
	timbrado = models.CharField(max_length=20, blank=True)
	timbrado_vence = models.DateField(null=True, blank=True)
	totalexentas = models.PositiveBigIntegerField(default=0)
	totalimponible = models.PositiveBigIntegerField(default=0)
	totalbase = models.PositiveBigIntegerField(default=0)
	totalfactura = models.PositiveBigIntegerField(default=0)
	deposito = models.ForeignKey(Deposito, on_delete=models.PROTECT, db_column='depositoid')
	moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT, db_column='monedaid')
	tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, db_column='tipodocid')
	plazo = models.ForeignKey(Plazo, on_delete=models.PROTECT, db_column='plazoid')

	class Meta:
		db_table = 'VENTAS'

	def __str__(self):
		return f"{self.serie}-{self.nrofactura}"


class CuentaCobrar(models.Model):
	tabla = models.CharField(max_length=50, default='VENTAS')
	venta = models.ForeignKey(Venta, on_delete=models.CASCADE, db_column='tablaid')
	cuota = models.PositiveIntegerField()
	importe = models.PositiveBigIntegerField()
	cobrado = models.PositiveBigIntegerField(default=0)
	vence = models.DateField()

	class Meta:
		db_table = 'CUENTAS_COBRAR'

	def __str__(self):
		return f"{self.venta} cuota {self.cuota}"


class Empresa(models.Model):
	empresa = models.CharField(max_length=200)
	direccion = models.CharField(max_length=150, blank=True)
	telefono = models.CharField(max_length=15, blank=True)
	mail = models.CharField(max_length=50, blank=True)
	ruc = models.CharField(max_length=50)
	moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT, db_column='monedaid')

	class Meta:
		db_table = 'EMPRESAS'

	def __str__(self):
		return self.empresa


class Producto(models.Model):
	producto = models.CharField(max_length=200)
	iva = models.DecimalField(max_digits=5, decimal_places=2)
	precio_venta = models.DecimalField(max_digits=18, decimal_places=5, default=0)
	servicio = models.BooleanField(default=False)

	class Meta:
		db_table = 'PRODUCTOS'

	def __str__(self):
		return self.producto


class ProductoDetalle(models.Model):
	codbarra = models.CharField(max_length=50, primary_key=True)
	producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='productoid', related_name='detalles')
	colorid = models.PositiveIntegerField(null=True, blank=True)
	tamanoid = models.PositiveIntegerField(null=True, blank=True)
	disenoid = models.PositiveIntegerField(null=True, blank=True)
	uxb = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)

	class Meta:
		db_table = 'PRODUCTO_DETALLE'

	def __str__(self):
		return f"{self.producto.producto} - {self.codbarra}"


class PlazoDetalle(models.Model):
	plazo = models.ForeignKey(Plazo, on_delete=models.CASCADE, related_name='detalles', db_column='plazoid')
	cuota = models.PositiveIntegerField()
	dias = models.PositiveIntegerField()

	class Meta:
		db_table = 'PLAZO_DETALLES'

	def __str__(self):
		return f"{self.plazo.plazo} - Cuota {self.cuota} ({self.dias} días)"


class VentaDetalle(models.Model):
	venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles', db_column='ventaid')
	producto_detalle = models.ForeignKey(ProductoDetalle, on_delete=models.PROTECT, db_column='codbarra')
	precio = models.DecimalField(max_digits=18, decimal_places=5)
	cantidad = models.DecimalField(max_digits=18, decimal_places=5)
	iva = models.DecimalField(max_digits=5, decimal_places=2)
	impuesto5 = models.DecimalField(max_digits=18, decimal_places=5, default=0)
	impuesto10 = models.DecimalField(max_digits=18, decimal_places=5, default=0)
	total = models.DecimalField(max_digits=18, decimal_places=5)

	class Meta:
		db_table = 'VENTA_DETALLES'
		unique_together = ('venta', 'producto_detalle')

	def __str__(self):
		return f"Venta {self.venta.id} - {self.producto_detalle.codbarra}"


class Cobro(models.Model):
	cuenta = models.ForeignKey(CuentaCobrar, on_delete=models.CASCADE, related_name='cobros')
	fecha_pago = models.DateField()
	monto = models.PositiveBigIntegerField()
	referencia = models.CharField(max_length=100, blank=True)

	class Meta:
		db_table = 'COBROS'

	def __str__(self):
		return f"Cobro {self.monto} - cuota {self.cuenta.cuota}"
