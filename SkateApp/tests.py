from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Categoria, Producto

User = get_user_model() 

class SkateShopTests(TestCase):
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.admin = User.objects.create_superuser(username='admin', password='admin123', email='admin@test.com')
        
        self.categoria = Categoria.objects.create(nombre='Tablas', slug='tablas')
        
        self.producto = Producto.objects.create(
            nombre='Skate Pro', 
            precio=50000, 
            stock=10, 
            descripcion='Tabla profesional'
        )
        
        self.producto.categorias.add(self.categoria)
        
        self.client = Client()

    def test_modelo_producto(self):
        """Prueba que el modelo Producto guarda correctamente (3.1.5.9)"""
        producto = Producto.objects.get(nombre='Skate Pro')
        self.assertEqual(producto.precio, 50000)
        self.assertEqual(str(producto), 'Skate Pro')

    def test_vista_catalogo(self):
        """Prueba que el catálogo carga y muestra productos (3.1.5.10)"""
        response = self.client.get(reverse('SkateApp:catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Skate Pro')

    def test_seguridad_panel_usuario(self):
        """Prueba de seguridad: Un anónimo no debe entrar al panel (3.1.3.5)"""
        self.client.logout()
        response = self.client.get(reverse('SkateApp:panel_usuario'))
        self.assertEqual(response.status_code, 302) 

    def test_agregar_carrito(self):
        """Prueba funcional del carrito de compras"""
        url = reverse('SkateApp:gestionar_carrito', args=[self.producto.id])
        response = self.client.get(url, follow=True) 
        self.assertEqual(response.status_code, 200)
        
        session = self.client.session
        self.assertIn(str(self.producto.id), session['carrito'])