from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .forms import LoginForm, UserProfileForm, RegisterForm

User = get_user_model()


# ============================================================
# 1. VISTA DE LOGIN
# ============================================================
class UserLoginView(View):
    """Vista para iniciar sesión."""
    template_name = 'core/login.html'

    def get(self, request, *args, **kwargs):
        """Muestra el formulario de login. Si ya está autenticado, redirige al home."""
        if request.user.is_authenticated:
            return redirect('core:home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        """Procesa el login. La autenticación vive SOLO aquí (no en el form)."""
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
            else:
                # El error va al form → un solo mensaje en pantalla
                form.add_error(None, "Usuario o contraseña incorrectos.")

        return render(request, self.template_name, {'form': form})


# ============================================================
# 2. VISTA DE REGISTRO (admin-only)
# ============================================================
class UserRegisterView(LoginRequiredMixin, View):
    """
    Vista para registrar nuevos usuarios (admin-only) NO SE USA AUN ESTA PENDIENTE.

    Sprint 2: agregar chequeo del grupo Administrator.
    Ver docs/PLAN_REGISTER_Y_USUARIOS.md (sección 6.2.2).
    """
    template_name = 'core/register.html'
    login_url = 'users:login'

    def handle_no_permission(self):
        """Muestra un mensaje cuando alguien sin sesión intenta registrar."""
        messages.info(
            self.request,
            "Debés iniciar sesión para registrar usuarios."
        )
        return super().handle_no_permission()

    def get(self, request, *args, **kwargs):
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Usuario '{user.username}' creado exitosamente. Podés crear otro."
            )
            return redirect('users:register')
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
                "¡Contraseña cambiada exitosamente! Por favor inicia sesión nuevamente."
            )
            return redirect('users:login')
        else:
            messages.success(self.request, "¡Perfil actualizado correctamente!")
        return response


# ============================================================
# 4. VISTA DE LOGOUT
# ============================================================
class UserLogoutView(View):
    """Vista para cerrar sesión. Redirige al home después del logout."""
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('core:home')