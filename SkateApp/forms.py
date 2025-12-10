from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import Usuario, Producto, Post, Reseña, Direccion, Categoria
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
import sys

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Usuario 
        fields = ('username', 'email', 'first_name', 'last_name') 
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not '@' in email or not '.' in email:
             raise ValidationError("El correo electrónico debe ser válido (contener '@' y '.').")
        return email.lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = 'cliente'
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    password = None
    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email')

GROSERIAS = ['puta', 'mierda', 'cabrón', 'hijo de puta', 'weon', 'aweonao', 'maricon']
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['titulo', 'contenido']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de tu publicación'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comparte algo con la comunidad...'}),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 10:
            raise ValidationError("El título es demasiado corto (mínimo 10 caracteres).")
        if len(titulo) > 100:
            raise ValidationError("El título es demasiado largo (máximo 100 caracteres).")
        for palabra in GROSERIAS:
            if palabra.lower() in titulo.lower():
                raise ValidationError("El título contiene palabras inapropiadas.")
        return titulo
    
    def clean_contenido(self):
        contenido = self.cleaned_data.get('contenido')
        if len(contenido) < 20:
            raise ValidationError("El contenido es demasiado corto (mínimo 20 caracteres).")
        for palabra in GROSERIAS:
            if palabra.lower() in contenido.lower():
                raise ValidationError("El contenido contiene palabras inapropiadas.")
        return contenido

class ResenaForm(forms.ModelForm):
    class Meta:
        model = Reseña
        fields = ['calificacion', 'texto']
        widgets = {
            'calificacion': forms.Select(attrs={'class': 'form-select'}),
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '¿Qué te pareció el producto?'}),
        }
        labels = {
            'calificacion': 'Puntuación (1-5)',
            'texto': 'Tu opinión'
        }
    def clean_calificacion(self):
        calificacion = self.cleaned_data.get('calificacion')
        if calificacion < 1 or calificacion > 5:
            raise ValidationError("La calificación debe estar entre 1 y 5.")
        return calificacion

    def clean_texto(self):
        texto = self.cleaned_data.get('texto')
        if not texto.strip():
            raise ValidationError("La reseña no puede estar vacía.")
        if len(texto) < 10:
            raise ValidationError("La reseña debe tener al menos 10 caracteres.")
        return texto

from .models import Usuario, Producto, Post, Reseña, Comentario 


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.TextInput(attrs={
                'class': 'form-control form-control-sm', 
                'placeholder': 'Escribe una respuesta...'
            }),
        }
        labels = {
            'texto': ''
        }
    def clean_texto(self):
        texto = self.cleaned_data.get('texto')
        if not texto.strip():
            raise ValidationError("El comentario no puede estar vacío.")
        if len(texto) < 3:
            raise ValidationError("El comentario es demasiado corto.")
        if len(texto) > 250:
            raise ValidationError("El comentario es demasiado largo (máximo 250 caracteres).")
        for palabra in GROSERIAS:
            if palabra.lower() in texto.lower():
                raise ValidationError("El contenido contiene palabras inapropiadas.")
        return texto


class DireccionEnvioForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = ['calle', 'comuna', 'region']
        widgets = {
            'calle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Av. Principal 123'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Providencia'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Metropolitana'}),
        }
        labels = {
            'calle': 'Direccion (Calle y Numero)',
            'comuna': 'Comuna / Ciudad',
            'region': 'Region'
        }

    def clean_comuna(self):
        comuna = self.cleaned_data.get('comuna')
        if not comuna.strip():
            raise ValidationError("La comuna/ciudad no puede estar vacía.")
        return comuna.strip()
    
    def clean_region(self):
        region = self.cleaned_data.get('region')
        if not region.strip():
            raise ValidationError("La región no puede estar vacía.")
        return region.strip()

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción detallada...'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1', 'placeholder': 'Precio (Ej: 19.990)'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Cantidad en stock'}),
            'categorias': forms.SelectMultiple(attrs={'class': 'form-select'}), 
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'categorias' in self.fields:
            self.fields['categorias'].choices = [('', 'Selecciona una Categoría')] + list(self.fields['categorias'].choices)[1:]
    
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio <= 0:
            raise ValidationError("El precio debe ser un valor positivo.")
        return precio
    
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 1:
            raise ValidationError("El stock debe ser al menos 1.")
        return stock
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if len(nombre) < 5:
            raise ValidationError("El nombre del producto debe tener al menos 5 caracteres.")
        return nombre
    
    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if not imagen:
            return imagen

        try:
            img = Image.open(imagen)
            img.verify()
        except Exception:
            raise ValidationError(
                "La imagen no es válida. Guarda la captura como PNG/JPG antes de subirla."
            )

        img = Image.open(imagen)
        img = img.convert("RGB") 

        extension_origen = img.format

        if extension_origen not in ("JPEG", "PNG"):
            output = io.BytesIO()
            img.save(output, format="PNG")
            output.seek(0)

            imagen = InMemoryUploadedFile(
                output,
                "imagen",
                f"{imagen.name.split('.')[0]}.png",
                "image/png",
                sys.getsizeof(output),
                None,
            )

        return imagen

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'}),
        }
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        nombre = nombre.strip()
        if not nombre:
            raise ValidationError("El nombre de la categoría no puede estar vacío.")

        qs = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Esta categoría ya existe.")

        return nombre
