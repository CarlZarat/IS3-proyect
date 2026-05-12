from django.shortcuts import get_object_or_404, redirect, render
from .models import Cliente
from django import forms

# Create your views here.

def home(request):
    return render(request, 'home.html')

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'ruc', 'direccion', 'telefono', 'email']
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'ruc': 'RUC',
            'direccion': 'Direccion',
            'telefono': 'Telefono',
            'email': 'Correo electronico',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'nombre': 'Ej: Carlos',
            'apellido': 'Ej: Gonzalez',
            'ruc': 'Ej: 1234567-8',
            'direccion': 'Ej: Av. Principal 123',
            'telefono': 'Ej: 0981 123 456',
            'email': 'Ej: cliente@correo.com',
        }
        for field_name, field in self.fields.items():
            css_class = 'form-control'
            field.widget.attrs['class'] = css_class
            field.widget.attrs['placeholder'] = placeholders.get(field_name, '')
            if field.required:
                field.widget.attrs['required'] = 'required'

def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('nombre', 'apellido', 'id')
    return render(request, 'clientes/lista.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/form.html', {'form': form, 'titulo': 'Nuevo Cliente'})


def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/form.html', {'form': form, 'titulo': 'Editar Cliente'})


def dar_baja_cliente(request, cliente_id):
    if request.method == 'POST':
        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.activo = False
        cliente.save(update_fields=['activo'])
    return redirect('lista_clientes')


def reactivar_cliente(request, cliente_id):
    if request.method == 'POST':
        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.activo = True
        cliente.save(update_fields=['activo'])
    return redirect('lista_clientes')
