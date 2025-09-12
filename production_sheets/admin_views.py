from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from .models import ProductionSheet, ProductionDetail
from django.db.models import Sum, Count

class AdminViewMixin(UserPassesTestMixin):
    def test_func(self):
        # Esta vista solo será accesible mediante URL directa
        # No requiere autenticación pero no aparecerá en ningún menú
        return True

class AdminListView(AdminViewMixin, ListView):
    template_name = 'production_sheets/admin/list.html'
    context_object_name = 'sheets'
    
    def get_queryset(self):
        queryset = ProductionSheet.objects.annotate(
            total_refs=Count('productiondetail__ref', distinct=True),
            total_units=Sum('productiondetail__quantity')
        ).order_by('-upload_date')
        return queryset

class AdminDeleteView(AdminViewMixin, DeleteView):
    model = ProductionSheet
    template_name = 'production_sheets/admin/confirm_delete.html'
    success_url = reverse_lazy('production_sheets:admin_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Eliminar primero los detalles relacionados
        self.object.productiondetail_set.all().delete()
        # Luego eliminar la planilla
        self.object.delete()
        
        messages.success(request, f'Planilla {self.object.manifest_number} eliminada correctamente.')
        return redirect(success_url)

class AdminEditView(AdminViewMixin, UpdateView):
    model = ProductionSheet
    template_name = 'production_sheets/admin/edit.html'
    fields = ['manifest_number', 'origin', 'packing_date']
    success_url = reverse_lazy('production_sheets:admin_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar los detalles de producción al contexto
        context['details'] = self.object.productiondetail_set.all().order_by('op', 'ref', 'size')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Planilla {self.object.manifest_number} actualizada correctamente.')
        return response