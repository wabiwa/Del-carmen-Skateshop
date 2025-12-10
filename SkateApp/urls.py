from django.urls import path
from . import views

app_name = 'SkateApp'

urlpatterns = [
    # --- PÁGINAS PRINCIPALES ---
    path('', views.home, name='home'),
    
    # --- CATÁLOGO Y PRODUCTOS ---
    path('catalogo/', views.catalogo, name='catalogo'),
    path('catalogo/<slug:categoria_slug>/', views.catalogo, name='productos_por_categoria'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),

    # --- CARRITO Y CHECKOUT ---
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/add/<int:producto_id>/', views.gestionar_carrito, name='gestionar_carrito'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/remove/<int:producto_id>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('checkout/', views.checkout, name='checkout'),
    path('compra-exitosa/<int:pedido_id>/', views.compra_exitosa, name='compra_exitosa'),

    # --- INTEGRACIÓN WEBPAY (Rutas Correctas) ---
    path('webpay/iniciar/<int:pedido_id>/', views.iniciar_pago_webpay, name='iniciar_pago_webpay'),
    path('webpay/retorno/', views.confirmar_pago_webpay, name='confirmar_pago_webpay'),

    # --- AUTENTICACIÓN Y USUARIOS ---
    path('registro/', views.registro, name='registro'),
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),
    
    # --- PANEL DE USUARIO ---
    path('panel/', views.panel_usuario, name='panel_usuario'),
    path('panel/editar/', views.editar_perfil, name='editar_perfil'),
    path('panel/direccion/', views.gestionar_direcciones, name='gestionar_direcciones'),

    # --- ZONA DE COMUNIDAD ---
    path('comunidad/', views.comunidad, name='comunidad'),
    path('comunidad/comentar/<int:post_id>/', views.agregar_comentario, name='agregar_comentario'),

    # --- ZONA DE ADMINISTRACIÓN ---
    path('administracion/gestion', views.gestion_administrador, name="gestion_administrador"),
    path('administracion/agregar-categoria/', views.agregar_categoria, name='agregar_categoria'),
    path('administracion/gestionar-categorias/', views.gestionar_categorias, name='gestionar_categorias'),
    path('administracion/gestionar-categorias/editar/<int:categoria_id>/', views.editar_categoria, name="editar_categoria"),
    path('administracion/gestionar-categorias/eliminar/<int:categoria_id>/', views.eliminar_categoria, name="eliminar_categoria"),
    path('administracion/agregar-producto/', views.agregar_producto, name='agregar_producto'),
    path('administracion/gestionar-procuctos/', views.gestionar_productos, name='gestionar_productos'),
    path('producto/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('comunidad/eliminar/<int:post_id>/', views.eliminar_post, name='eliminar_post'),
    path('administrador/gestionar-posts/', views.gestionar_posts, name='gestionar_posts'),
    path("administrador/gestionar-usuarios/", views.gestionar_usuarios, name="gestionar_usuarios"),
    path("administrador/editar-usuario/<int:user_id>/", views.editar_usuario, name="editar_usuario"),
    path("administrador/eliminar-usuario/<int:user_id>/", views.eliminar_usuario, name="eliminar_usuario"),

    # --- API (Asistente) ---
    path('api/asistente/', views.asistente_ia, name='asistente_ia_api'),
]