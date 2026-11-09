from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, ListView, UpdateView

from .forms import LoginForm, RegisterForm, UserProfileForm

User = get_user_model()


# ============================================================
# 1. VISTA DE LOGIN
# ============================================================
class UserLoginView(View):
  """Vista para iniciar sesión."""

  template_name = 'core/login.html'

  def get(self, request, *args, **kwargs):
    """Muestra el formulario de login.

    Si ya está autenticado, redirige al home.
    """
    if request.user.is_authenticated:
      return redirect('core:home')
    form = LoginForm()
    return render(request, self.template_name, {'form': form})

  def post(self, request, *args, **kwargs):
    """Procesa el formulario de login y autentica al usuario."""
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
# 2. VISTA DE REGISTRO (Admin-only / Refactorizada)
# ============================================================
class UserRegisterView(PermissionRequiredMixin, View):
  """Vista para registrar nuevos usuarios.

  Requiere el permiso can_manage_users.
  """

  template_name = 'core/register.html'
  permission_required = 'logic_users.can_manage_users'
  raise_exception = (
      True  # Lanza 403 si no tiene permiso, en lugar de redirigir silenciosamente
  )

  def get(self, request, *args, **kwargs):
    form = RegisterForm()
    return render(request, self.template_name, {'form': form})

  def post(self, request, *args, **kwargs):
    form = RegisterForm(request.POST)
    if form.is_valid():
      user = form.save()
      messages.success(request, f"Usuario '{user.username}' creado exitosamente.")
      return redirect(
          'users:user_list'
      )  # Redirigimos al listado, no a crear otro[cite: 3]
    return render(request, self.template_name, {'form': form})
    raise_exception = True

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
    """Retorna el usuario actual (siempre edita su propio perfil)."""
    return self.request.user

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = 'Mi perfil'
    return context

  def form_valid(self, form):
    """Guarda los cambios y maneja el cambio de contraseña."""
    response = super().form_valid(form)
    # Si se cambió la contraseña, cerrar sesión y pedir que vuelva a iniciar
    if form.cleaned_data.get('new_password'):
      logout(self.request)
      messages.success(
          self.request,
          '¡Contraseña cambiada exitosamente! Por favor inicia sesión'
          ' nuevamente.',
      )
      return redirect('login')
    else:
      messages.success(self.request, '¡Perfil actualizado correctamente!')
    return response
    raise_exception = True

# ============================================================
# 4. VISTA DE LOGOUT
# ============================================================
class UserLogoutView(View):
  """Vista para cerrar sesión. Redirige al home después del logout."""

  def get(self, request, *args, **kwargs):
    logout(request)
    return redirect('core:home')
    raise_exception = True

# ============================================================
# 5. GESTIÓN DE USUARIOS (CRUD - Admin Only)[cite: 3]
# ============================================================
class UserListView(PermissionRequiredMixin, ListView):
  """Listado de usuarios con buscador."""

  model = User
  template_name = 'core/user_list.html'
  context_object_name = 'users'
  paginate_by = 20
  permission_required = 'logic_users.can_manage_users'
  raise_exception = True

  def get_queryset(self):
    qs = User.objects.all().prefetch_related('groups').order_by('username')
    query = self.request.GET.get('q', '').strip()

    if query:
      # Búsqueda por cédula o nombre de usuario[cite: 3]
      qs = qs.filter(Q(id_number__icontains=query) | Q(username__icontains=query))
    return qs

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['search_query'] = self.request.GET.get('q', '')
    return context
    raise_exception = True



class UserUpdateView(PermissionRequiredMixin, UpdateView):
  """Editar usuario: cambiar rol y estado activo."""

  model = User
  template_name = 'core/user_edit.html'
  fields = ['is_active']
  success_url = reverse_lazy('users:user_list')
  permission_required = 'logic_users.can_manage_users'
  raise_exception = True

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['role_choices'] = Group.objects.all().order_by('name')
    return context

  def form_valid(self, form):
    # Auto-protección: El admin no puede desactivar su propia cuenta[cite: 3]
    if self.object == self.request.user:
      if not form.cleaned_data.get('is_active'):
        form.add_error('is_active', 'No puedes desactivar tu propia cuenta.')
        return self.form_invalid(form)

    response = super().form_valid(form)

    # Actualizar el grupo (rol)[cite: 3]
    new_role = self.request.POST.get('rol')
    if new_role and Group.objects.filter(name=new_role).exists():
      self.object.groups.clear()
      self.object.groups.add(Group.objects.get(name=new_role))

    messages.success(self.request, f"Usuario '{self.object.username}' actualizado.")
    return response
    raise_exception = True
    

class UserDeleteView(PermissionRequiredMixin, DeleteView):
  """Eliminar usuario (soft delete → papelera)[cite: 3]."""

  model = User
  template_name = 'core/user_confirm_delete.html'
  success_url = reverse_lazy('users:user_list')
  permission_required = 'logic_users.can_manage_users'
  raise_exception = True

  def form_valid(self, form):
    user = self.get_object()
    # Evitar que el admin se elimine a sí mismo[cite: 3]
    if user == self.request.user:
      messages.error(self.request, 'No puedes eliminar tu propia cuenta.')
      return redirect('users:user_list')

    user.delete()  # El modelo User ya tiene overrideado el delete para hacer soft delete[cite: 3]
    messages.success(
        self.request, f"Usuario '{user.username}' movido a la papelera."
    )
    return redirect(self.success_url)
    raise_exception = True