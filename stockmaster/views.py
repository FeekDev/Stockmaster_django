from django.shortcuts import render
from rest_framework import viewsets
from .models import (TipoPersona,
                     Persona, Venta, DetalleFactura,
                     Articulo, Categoria
)
from .serializers import (
    ArticuloSerializer,
    TipoPersonaSerializer,
    PersonaSerializer,
    VentaSerializer,
    DetalleFacturaSerializer,
    CategoriaSerializer,
)

# Create your views here.
class TipoPersonaViewSet(viewsets.ModelViewSet):
    queryset = TipoPersona.objects.all()
    serializer_class = TipoPersonaSerializer

class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer


class DetalleFacturaViewSet(viewsets.ModelViewSet):
    queryset = DetalleFactura.objects.select_related('venta', 'articulo')
    serializer_class = DetalleFacturaSerializer

class ArticuloViewSet(viewsets.ModelViewSet):
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer