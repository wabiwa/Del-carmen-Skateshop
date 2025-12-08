from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Avg
from django.db import transaction
from django.http import HttpRequest
import random 

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys

from .models import Categoria, Producto, Post, Comentario, Pedido, DetallePedido, Reseña, Direccion 
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm, ProductoForm, PostForm, 
    ComentarioForm, DireccionEnvioForm, ResenaForm, CategoriaForm
)

# ======================================================================
# VISTAS PÚBLICAS Y CATÁLOGO
# ======================================================================

def home(request):
    categorias_con_productos = Producto.objects.filter(stock__gt=0).values_list('categorias',flat=True).distinct()
    categorias_destacadas = Categoria.objects.filter(id__in=categorias_con_productos).order_by('nombre')[:2]
    
    categorias_para_front=[]

    for categoria in categorias_destacadas:
        primer_producto = Producto.objects.filter(categorias=categoria, stock__gt=0).first()
        if primer_producto:
            categorias_para_front.append({
                'nombre': categoria.nombre,
                'slug': categoria.slug,
                'imagen_url':primer_producto.imagen.url if primer_producto.imagen else None
            })
    
    posts_destacados = Post.objects.filter(estado='publicado').order_by('-fecha')[:3]

    context = {
        'categorias_destacadas_front': categorias_para_front, 
        'posts_destacados': posts_destacados, 
        'page_title': 'Inicio'
    }
    return render(request, 'SkateApp/home.html', context)

def catalogo(request, categoria_slug=None):
    categorias = Categoria.objects.all()
    productos = Producto.objects.filter(stock__gt=0).order_by('nombre') 
    categoria_actual = None
    query = request.GET.get('q') 
    
    if categoria_slug:
        categoria_actual = get_object_or_404(Categoria, slug=categoria_slug)
        productos = productos.filter(categorias__in=[categoria_actual])
        
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        ).distinct()

    productos = productos.annotate(avg_calificacion=Avg('reseñas__calificacion'))

    context = {
        'categoria_actual': categoria_actual,
        'categorias': categorias,
        'productos': productos,
        'page_title': 'Catálogo',
        'query': query,
    }
    return render(request, 'SkateApp/catalogo.html', context)

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    reseñas = producto.reseñas.all().order_by('-fecha')
    promedio_calificacion = reseñas.aggregate(Avg('calificacion'))['calificacion__avg']
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para opinar.")
            return redirect('SkateApp:iniciar_sesion')
            
        form = ResenaForm(request.POST)
        if form.is_valid():
            ya_opino = reseñas.filter(usuario=request.user).exists()
            if ya_opino:
                messages.warning(request, "Ya has dejado una opinión para este producto.")
            else:
                nueva_resena = form.save(commit=False)
                nueva_resena.usuario = request.user
                nueva_resena.producto = producto
                nueva_resena.save()
                messages.success(request, "¡Gracias por tu valoración!")
            
            return redirect('SkateApp:detalle_producto', producto_id=producto.id)
    else:
        form = ResenaForm()

    context = {
        'producto': producto,
        'reseñas': reseñas,
        'promedio_calificacion': promedio_calificacion,
        'form': form
    }
    return render(request, 'SkateApp/detalle_producto.html', context)

# ======================================================================
# VISTAS DE AUTENTICACIÓN
# ======================================================================

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro exitoso. ¡Bienvenido!')
            return redirect('SkateApp:home') 
        else:
            messages.error(request, 'Error en el registro. Verifique los datos.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'SkateApp/registro.html', {'form': form})

def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('SkateApp:home') 
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('SkateApp:home')
        else:
            messages.error(request, 'Credenciales incorrectas.')
            
    return render(request, 'SkateApp/login.html')

@login_required 
def cerrar_sesion(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('SkateApp:home')

# ======================================================================
# VISTAS DE PANEL DE USUARIO
# ======================================================================

@login_required
def panel_usuario(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')
    context = {
        'pedidos': pedidos,
        'page_title': 'Mi Panel'
    }
    return render(request, 'SkateApp/panel_usuario.html', context)

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('SkateApp:panel_usuario')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'SkateApp/editar_perfil.html', {'form': form})

@login_required
def gestionar_direcciones(request):
    try:
        direccion = request.user.direccion
    except Direccion.DoesNotExist:
        direccion = None

    if request.method == 'POST':
        calle = request.POST.get('calle')
        comuna = request.POST.get('comuna')
        region = request.POST.get('region')
        
        if calle and comuna and region:
            if direccion:
                direccion.calle = calle
                direccion.comuna = comuna
                direccion.region = region
                direccion.save()
            else:
                nueva_direccion = Direccion.objects.create(calle=calle, comuna=comuna, region=region)
                request.user.direccion = nueva_direccion
                request.user.save()
            messages.success(request, 'Dirección guardada.')
            return redirect('SkateApp:panel_usuario')

    return render(request, 'SkateApp/gestionar_direcciones.html', {'direccion_actual': direccion})

# ======================================================================
# VISTAS DE CARRITO Y CHECKOUT
# ======================================================================

def gestionar_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito = request.session.get('carrito', {})
    
    carrito[str(producto_id)] = {
        'cantidad': 1, 
        'precio': str(producto.precio), 
        'nombre': producto.nombre
    }
    
    request.session['carrito'] = carrito
    request.session.modified = True 
    
    messages.success(request, f'¡{producto.nombre} agregado al carrito!')
    return redirect('SkateApp:ver_carrito')

def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    items_carrito = []
    subtotal = 0
    
    for item_id, item_data in carrito.items():
        try:
            producto = Producto.objects.get(id=int(item_id))
            precio = float(item_data['precio'])
            subtotal += precio
            items_carrito.append({
                'producto_id': item_id, 
                'nombre': producto.nombre, 
                'precio_unitario': precio, 
                'cantidad': 1, 
                'costo_item': precio
            })
        except Producto.DoesNotExist:
            continue 
            
    return render(request, 'SkateApp/carrito.html', {
        'items_carrito': items_carrito, 
        'total_general': subtotal 
    })

def eliminar_item_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    if str(producto_id) in carrito:
        del carrito[str(producto_id)]
        request.session.modified = True
        messages.warning(request, 'Producto eliminado del carrito.')
    return redirect('SkateApp:ver_carrito')

 
@transaction.atomic 
def checkout(request):

    if not request.user.is_authenticated:
        messages.warning(request, "Para finalizar tu compra, necesitas iniciar sesión o registrarte.")
        return redirect('SkateApp:iniciar_sesion')

    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect('SkateApp:catalogo')

    subtotal = 0
    items_checkout = []
    for item_id, item_data in carrito.items():
        precio = float(item_data['precio'])
        subtotal += precio * item_data['cantidad']
        items_checkout.append({
            'nombre': item_data['nombre'],
            'precio': precio,
            'cantidad': item_data['cantidad'],
            'total': precio * item_data['cantidad']
        })
    
    costo_envio = 5000 
    total_final = subtotal + costo_envio

    try:
        direccion_existente = request.user.direccion
    except:
        direccion_existente = None

    if request.method == 'POST':
        form = DireccionEnvioForm(request.POST, instance=direccion_existente)
        if form.is_valid():
            direccion = form.save()
            
            if not direccion_existente:
                request.user.direccion = direccion
                request.user.save()

            nuevo_pedido = Pedido.objects.create(
                usuario=request.user,
                estado='pendiente', 
                total=total_final
            )

            for item_id, item_data in carrito.items():
                producto = Producto.objects.get(id=int(item_id))
                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=producto,
                    cantidad=item_data['cantidad'],
                    precio_unitario=item_data['precio']
                )
                producto.stock -= item_data['cantidad']
                producto.save()

            return redirect('SkateApp:iniciar_pago_webpay', pedido_id=nuevo_pedido.id)
            
    else:
        form = DireccionEnvioForm(instance=direccion_existente)

    context = {
        'items': items_checkout,
        'subtotal': subtotal,
        'envio': costo_envio,
        'total': total_final,
        'form': form
    } 
    return render(request, 'SkateApp/checkout.html', context)
@login_required
def compra_exitosa(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'SkateApp/compra_exitosa.html', {'pedido': pedido})

# ======================================================================
# INTEGRACIÓN WEBPAY PLUS (TRANSBANK)
# ======================================================================

@login_required
def iniciar_pago_webpay(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    tx = Transaction(WebpayOptions(
        IntegrationCommerceCodes.WEBPAY_PLUS, 
        IntegrationApiKeys.WEBPAY, 
        IntegrationType.TEST
    ))
    
    amount = int(pedido.total)
    buy_order = str(pedido.id)
    session_id = str(random.randrange(1000000, 99999999))
    return_url = request.build_absolute_uri(reverse('SkateApp:confirmar_pago_webpay'))
    
    try:
        response = tx.create(buy_order, session_id, amount, return_url)
        
        return render(request, 'SkateApp/redireccion_webpay.html', {
            'url': response['url'],
            'token': response['token']
        })
        
    except Exception as e:
        messages.error(request, f"Error al conectar con Webpay: {str(e)}")
        return redirect('SkateApp:panel_usuario')

@csrf_exempt 
def confirmar_pago_webpay(request):
    token = request.GET.get('token_ws') or request.POST.get('token_ws')
    
    if not token:
        messages.warning(request, "La compra fue anulada o expiró.")
        return redirect('SkateApp:panel_usuario')

    tx = Transaction(WebpayOptions(
        IntegrationCommerceCodes.WEBPAY_PLUS, 
        IntegrationApiKeys.WEBPAY, 
        IntegrationType.TEST
    ))

    try:
        response = tx.commit(token)
        
        if response['status'] == 'AUTHORIZED':
            pedido_id = response['buy_order']
            pedido = Pedido.objects.get(id=pedido_id)
            
            pedido.estado = 'pagado'
            pedido.save()
            
            request.session['carrito'] = {} 
            
            messages.success(request, "¡Pago Aprobado! Gracias por tu compra.")
            return redirect('SkateApp:panel_usuario')
        else:
            messages.error(request, "El pago fue rechazado por el banco.")
            return redirect('SkateApp:panel_usuario')
            
    except Exception as e:
        messages.error(request, f"Hubo un error al confirmar: {str(e)}")
        return redirect('SkateApp:panel_usuario')

# ======================================================================
# ZONA DE COMUNIDAD
# ======================================================================

def comunidad(request):
    posts = Post.objects.all().order_by('-fecha')
    form = PostForm()
    comentario_form = ComentarioForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para publicar.")
            return redirect('SkateApp:iniciar_sesion')
            
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.usuario = request.user 
            post.save()
            messages.success(request, "¡Publicación creada con éxito!")
            return redirect('SkateApp:comunidad')

    context = {
        'posts': posts,
        'form': form,
        'comentario_form': comentario_form
    }
    return render(request, 'SkateApp/comunidad.html', context)

def agregar_comentario(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para comentar.")
            return redirect('SkateApp:iniciar_sesion')

        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.usuario = request.user
            comentario.post = post
            comentario.save()
            messages.success(request, "¡Comentario agregado!")
            
    return redirect('SkateApp:comunidad')

@user_passes_test(lambda u: u.is_superuser)
def eliminar_post(request: HttpRequest, post_id: int):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        
        try:
            post.delete()
            messages.success(request, f'La publicación "{post.titulo}" ha sido eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al intentar eliminar la publicación: {e}')

        return redirect('SkateApp:comunidad') 
    
    return redirect('SkateApp:comunidad')

# ======================================================================
# ZONA DE ADMINISTRADOR (Gestión de Productos)
# ======================================================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado exitosamente al catálogo.')
            return redirect('SkateApp:catalogo')
    else:
        form = ProductoForm()
    return render(request, 'SkateApp/agregar_producto.html', {'form': form, 'page_title': 'Agregar Producto'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def agregar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria agregada exitosamente al catálogo.')
            return redirect('SkateApp:catalogo')
    else:
        form = CategoriaForm()
    return render(request, 'SkateApp/agregar_categoria.html', {'form': form, 'titulo': 'Nueva Categoría'})

@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente.')
            return redirect('SkateApp:detalle_producto', producto_id=producto.id)
    else:
        form = ProductoForm(instance=producto)
        
    return render(request, 'SkateApp/editar_producto.html', {'form': form, 'producto': producto})

@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.warning(request, f'Producto "{nombre_producto}" ha sido eliminado.')
        return redirect('SkateApp:catalogo')
    
    return redirect('SkateApp:detalle_producto', producto_id=producto.id)



# ======================================================================
# VISTA API (Asistente)
# ======================================================================

@csrf_exempt
def asistente_ia(request):
    if request.method == 'POST':
        return JsonResponse({'answer': "Hola, soy tu asistente virtual."})
    return JsonResponse({'error': 'Método no permitido'}, status=405)