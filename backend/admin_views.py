from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, DeleteView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Sum, Count
from excel_processor.models import ExcelProcess, PDFProcessHistory, RegistroExcel
from production_sheets.models import ProductionSheet, ProductionDetail

class AdminViewMixin(UserPassesTestMixin):
    def test_func(self):
        return True

class AdminHomeView(AdminViewMixin, TemplateView):
    template_name = 'admin/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Estadísticas generales
        context['stats'] = {
            'excel_processes': ExcelProcess.objects.count(),
            'pdf_processes': PDFProcessHistory.objects.count(),
            'production_sheets': ProductionSheet.objects.count(),
            'production_details': ProductionDetail.objects.count(),
            'registros_excel': RegistroExcel.objects.count(),
        }
        return context

# Vistas para ExcelProcess
class ExcelProcessListView(AdminViewMixin, ListView):
    model = ExcelProcess
    template_name = 'admin/excel_process_list.html'
    context_object_name = 'files'
    ordering = ['-fecha_carga']
    paginate_by = 100

class ExcelProcessDeleteView(AdminViewMixin, DeleteView):
    model = ExcelProcess
    template_name = 'admin/confirm_delete.html'
    success_url = reverse_lazy('custom_admin:excel_process_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.file.delete()  # Eliminar el archivo físico
        self.object.delete()
        messages.success(request, f'Archivo Excel eliminado correctamente.')
        return redirect(success_url)

# Vistas para ProductionDetail
class ProductionDetailListView(AdminViewMixin, ListView):
    model = ProductionDetail
    template_name = 'admin/production_detail_list.html'
    context_object_name = 'details'
    ordering = ['-production_sheet__upload_date', 'op', 'ref', 'size']
    paginate_by = 100

    def get_queryset(self):
        return super().get_queryset().select_related('production_sheet')

class ProductionDetailDeleteView(AdminViewMixin, DeleteView):
    model = ProductionDetail
    template_name = 'admin/confirm_delete.html'
    success_url = reverse_lazy('custom_admin:production_detail_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Detalle de producción eliminado correctamente.')
        return redirect(success_url)

# Vistas para RegistroExcel
class RegistroExcelListView(AdminViewMixin, ListView):
    model = RegistroExcel
    template_name = 'admin/registro_excel_list.html'
    context_object_name = 'registros'
    ordering = ['-fecha_registro']
    paginate_by = 100

    def get_queryset(self):
        return super().get_queryset().select_related('proceso')

class RegistroExcelEditView(AdminViewMixin, UpdateView):
    model = RegistroExcel
    template_name = 'admin/registro_excel_edit.html'
    fields = ['orden', 'produccion', 'cant_orig', 'saldo_entregar', 'cant_produc', 'iny', 'otros']
    success_url = reverse_lazy('custom_admin:registro_excel_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Registro Excel actualizado correctamente.')
        return response

class RegistroExcelDeleteView(AdminViewMixin, DeleteView):
    model = RegistroExcel
    template_name = 'admin/confirm_delete.html'
    success_url = reverse_lazy('custom_admin:registro_excel_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Registro Excel eliminado correctamente.')
        return redirect(success_url)

# Vistas para PDFProcessHistory
class PDFProcessListView(AdminViewMixin, ListView):
    model = PDFProcessHistory
    template_name = 'admin/pdf_process_list.html'
    context_object_name = 'pdfs'
    ordering = ['-process_date']
    paginate_by = 100

class PDFProcessDeleteView(AdminViewMixin, DeleteView):
    model = PDFProcessHistory
    template_name = 'admin/confirm_delete.html'
    success_url = reverse_lazy('custom_admin:pdf_process_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Historial de PDF eliminado correctamente.')
        return redirect(success_url)

class ProductionDetailEditView(AdminViewMixin, UpdateView):
    model = ProductionDetail
    template_name = 'admin/production_detail_edit.html'
    fields = ['op', 'ref', 'size', 'quantity']
    success_url = reverse_lazy('custom_admin:production_detail_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Detalle de producción actualizado correctamente.')
        return response

# Vistas para ProductionSheet
class ProductionSheetListView(AdminViewMixin, ListView):
    model = ProductionSheet
    template_name = 'admin/production_sheet_list.html'
    context_object_name = 'sheets'
    ordering = ['-upload_date']
    paginate_by = 100

class ProductionSheetEditView(AdminViewMixin, UpdateView):
    model = ProductionSheet
    template_name = 'admin/production_sheet_edit.html'
    fields = ['file', 'upload_date']
    success_url = reverse_lazy('custom_admin:production_sheet_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Planilla de producción actualizada correctamente.')
        return response

class ProductionSheetDeleteView(AdminViewMixin, DeleteView):
    model = ProductionSheet
    template_name = 'admin/confirm_delete.html'
    success_url = reverse_lazy('custom_admin:production_sheet_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.file.delete()  # Eliminar el archivo físico
        self.object.delete()
        messages.success(request, f'Planilla de producción eliminada correctamente.')
        return redirect(success_url)