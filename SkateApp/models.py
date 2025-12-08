from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# ======================================================================
# GESTIÓN DE USUARIOS Y DIRECCIONES
# ======================================================================

# 1. Modelo Dirección 
class Direccion(models.Model):
    calle = models.CharField(max_length=255)
    comuna = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.calle}, {self.comuna}"

class Usuario(AbstractUser):
    direccion = models.OneToOneField(
        'Direccion', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='usuario_perfil'
    )

    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='cliente')

    def __str__(self):
        return self.username

# ======================================================================
# CATÁLOGO Y PRODUCTOS
# ======================================================================

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, db_index=True) 
    slug = models.SlugField(unique=True, blank=True, null=True, db_index=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def clean(self):
        nombre_normalizado = self.nombre.strip().lower()
        
        existe = Categoria.objects.filter(nombre__iexact=self.nombre)
        if self.pk:
            existe = existe.exclude(pk=self.pk) 

        if existe.exists():
            raise ValidationError("Ya existe una categoría con ese nombre.")
    
    def generar_slug_unico(self):
        base_slug = slugify(self.nombre)
        slug = base_slug
        contador = 1

        while Categoria.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{contador}"
            contador += 1

        return slug

    def save(self, *args, **kwargs):
        self.full_clean() 
        if not self.slug:
            self.slug = self.generar_slug_unico()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=200, db_index=True) # Búsqueda optimizada
    
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    stock = models.IntegerField()
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    
    categorias = models.ManyToManyField(Categoria, related_name='productos')

    def __str__(self):
        return self.nombre

# ======================================================================
# VENTAS Y PEDIDOS
# ======================================================================

class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pedidos')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    codigo_seguimiento = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Código de Starken/Chilexpress para rastreo"
    )

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1)
    
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

# ======================================================================
# COMUNIDAD Y CONTENIDO
# ======================================================================

class Post(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='publicado')

    def __str__(self):
        return self.titulo

class Reseña(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='reseñas')
    pedido = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True)
    texto = models.TextField()
    calificacion = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.usuario} a {self.producto}"

class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    imagen = models.ImageField(upload_to='noticias/', blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo
    

class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.usuario.username} en {self.post.titulo}"