from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, ListView, UpdateView

from .forms import LoginForm, RegisterForm, UserProfileForm

User = get_user_model()


# ============================================================
# MIXIN DE PERMISOS PARA GESTIÓN DE USUARIOS
# ============================================================
class CanManageUsersMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Restringe la gestión de usuarios y muestra un mensaje si falta permiso."""
    permission_required = 'logic_users.can_manage_users'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "No tienes permisos para gestionar usuarios.")
        return redirect('core:home')


# ============================================================
# 1. VISTA DE LOGIN
# ============================================================
class UserLoginView(View):
    """Vista para iniciar sesión."""
    template_name = 'core/login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')

        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('core:home')

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'error_message': 'Nombre de usuario o contraseña incorrectos.',
            },
        )


# ============================================================
# 2. VISTA DE REGISTRO (Admin-only)
# ============================================================
class UserRegisterView(CanManageUsersMixin, View):
    """Vista para registrar nuevos usuarios."""
    template_name = 'core/register.html'

    def get(self, request, *args, **kwargs):
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario '{user.username}' creado exitosamente.")
            return redirect('users:user_list')
        return render(request, self.template_name, {'form': form})


# ============================================================
# 3. VISTA DE PERFIL
# ============================================================
class UserProfileView(LoginRequiredMixin, UpdateView):
    """Vista para que el usuario edite su perfil y cambie su contraseña."""
    model = User
    form_class = UserProfileForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('core:home')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mi perfil'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get('new_password'):
            logout(self.request)
            messages.success(
                self.request,
                '¡Contraseña cambiada exitosamente! Por favor inicia sesión nuevamente.',
            )
            return redirect('users:login') # Namespace users
        else:
            messages.success(self.request, '¡Perfil actualizado correctamente!')
        return response


# ============================================================
# 4. VISTA DE LOGOUT
# ============================================================
class UserLogoutView(View):
    """Vista para cerrar sesión. Redirige al home después del logout."""
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('core:home')


# ============================================================
# 5. GESTIÓN DE USUARIOS (CRUD - Admin Only)
# ============================================================
class UserListView(CanManageUsersMixin, ListView):
    """Listado de usuarios con buscador."""
    model = User
    template_name = 'core/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.all().prefetch_related('groups').order_by('username')
        query = self.request.GET.get('q', '').strip()

        if query:
            qs = qs.filter(Q(id_number__icontains=query) | Q(username__icontains=query))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class UserUpdateView(CanManageUsersMixin, UpdateView):
    """Editar usuario: cambiar rol y estado activo."""
    model = User
    template_name = 'core/user_edit.html'
    fields = ['is_active']
    success_url = reverse_lazy('users:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = Group.objects.all().order_by('name')
        context['is_self'] = self.object == self.request.user # 🆕 Para el template
        return context

    def form_valid(self, form):
        is_self = self.object == self.request.user
        new_role = self.request.POST.get('rol')
        
        # Auto-protección: Si se edita a sí mismo
        if is_self:
            if not form.cleaned_data.get('is_active'):
                form.add_error('is_active', 'No puedes desactivar tu propia cuenta.')
                return self.form_invalid(form)
            messages.success(self.request, "Tu perfil de administrador ha sido actualizado.")
            return super().form_valid(form)

        # Validar que el rol exista
        group = Group.objects.filter(name=new_role).first()
        if not group:
            form.add_error(None, 'Selecciona un rol válido.')
            return self.form_invalid(form)

        # Guardar y asignar el rol
        response = super().form_valid(form)
        self.object.groups.set([group]) 
        messages.success(self.request, f"Usuario '{self.object.username}' actualizado.")
        return response


class UserDeleteView(CanManageUsersMixin, DeleteView):
    """Eliminar usuario (soft delete → papelera)."""
    model = User
    template_name = 'core/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')

    def delete(self, request, *args, **kwargs):
        # Usamos delete() porque Django 3.2 no ejecuta form_valid()
        user = self.get_object()
        
        # Auto-protección: El admin no puede eliminarse a sí mismo
        if user == self.request.user:
            messages.error(request, 'No puedes eliminar tu propia cuenta.')
            return redirect(self.success_url)

        user.delete() # Soft delete
        messages.success(request, f"Usuario '{user.username}' movido a la papelera.")
        return redirect(self.success_url)