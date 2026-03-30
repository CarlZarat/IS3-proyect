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
	documento = models.CharField(max_length=20, blank=True)
	direccion = models.CharField(max_length=200, blank=True)
	email = models.CharField(max_length=200, blank=True)
	telefono = models.CharField(max_length=200, blank=True)
	activo = models.BooleanField(default=True)

	class Meta:
		db_table = 'CLIENTES'

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


class Cobro(models.Model):
	cuenta = models.ForeignKey(CuentaCobrar, on_delete=models.CASCADE, related_name='cobros')
	fecha_pago = models.DateField()
	monto = models.PositiveBigIntegerField()
	referencia = models.CharField(max_length=100, blank=True)

	class Meta:
		db_table = 'COBROS'

	def __str__(self):
		return f"Cobro {self.monto} - cuota {self.cuenta.cuota}"
