from cxc import views as cxc_views


def lista_ventas(request):
    """Alias funcional de /ventas/ hacia la implementación actual en CxC."""
    return cxc_views.lista_ventas(request)


def crear_venta(request):
    """Alias funcional de /ventas/nuevo/ hacia la implementación actual en CxC."""
    return cxc_views.crear_venta(request)


def detalle_venta(request, venta_id):
    """Alias funcional de /ventas/<id>/ hacia la implementación actual en CxC."""
    return cxc_views.detalle_venta(request, venta_id=venta_id)


def editar_venta(request, venta_id):
    """Alias funcional de /ventas/<id>/editar/ hacia la implementación actual en CxC."""
    return cxc_views.editar_venta(request, venta_id=venta_id)


def eliminar_venta(request, venta_id):
    """Alias funcional de /ventas/<id>/eliminar/ hacia la implementación actual en CxC."""
    return cxc_views.eliminar_venta(request, venta_id=venta_id)