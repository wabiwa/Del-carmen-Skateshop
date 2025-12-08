from django.contrib import admin
from .models import (
    Usuario, Direccion, Categoria, Producto, 
    Pedido, DetallePedido, Post, Comentario, Reseña, Noticia
)

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0 
    readonly_fields = ('producto', 'precio_unitario', 'cantidad') 
    can_delete = False 

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'direccion_completa', 'mostrar_total', 'estado', 'fecha')
    
    list_filter = ('estado', 'fecha')
    search_fields = ('usuario__username', 'id', 'usuario__direccion__calle') 
    
    inlines = [DetallePedidoInline]
    ordering = ('-fecha',)
    
    readonly_fields = ('direccion_completa',)

    def mostrar_total(self, obj):
        return f"${obj.total:,.0f}".replace(",", ".")
    mostrar_total.short_description = 'Total CLP'

    def direccion_completa(self, obj):
        try:
            d = obj.usuario.direccion
            if d:
                return f"{d.calle}, {d.comuna} ({d.region})"
            else:
                return "⚠️ Sin dirección registrada"
        except:
            return "Error en datos"
    
    direccion_completa.short_description = 'Dirección de Envío'

# 3. Administración de DIRECCIONES
@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ('calle', 'comuna', 'region', 'usuario_asociado')
    list_filter = ('region', 'comuna')
    search_fields = ('calle', 'usuario_perfil__username')

    def usuario_asociado(self, obj):
        try:
            return obj.usuario_perfil.username
        except:
            return "Sin usuario"
    usuario_asociado.short_description = 'Cliente'

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'mostrar_categorias')
    list_filter = ('categorias',)
    search_fields = ('nombre',)
    list_editable = ('stock', 'precio') 

    def mostrar_categorias(self, obj):
        return ", ".join([c.nombre for c in obj.categorias.all()])
    mostrar_categorias.short_description = 'Categorías'

admin.site.register(Usuario)
admin.site.register(Categoria)
admin.site.register(Post)
admin.site.register(Comentario)
admin.site.register(Reseña)
