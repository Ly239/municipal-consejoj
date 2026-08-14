from django.shortcuts import render, redirect, get_object_or_404
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
            return redirect('home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        """Procesa el formulario de login y autentica al usuario."""
        if request.user.is_authenticated:
            return redirect('home')

        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')

        return render(request, self.template_name, {
            'form': form,
            'error_message': 'Nombre de usuario o contraseña incorrectos.'
        })


# ============================================================
# 2. VISTA DE REGISTRO (opcional, para uso futuro)
# ============================================================
class UserRegisterView(View):
    """Vista para registrar nuevos usuarios."""
    template_name = 'core/register.html'

    def get(self, request, *args, **kwargs):
        """Muestra el formulario de registro. Si ya está autenticado, redirige al home."""
        if request.user.is_authenticated:
            return redirect('home')
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        """Procesa el formulario de registro y crea un nuevo usuario."""
        if request.user.is_authenticated:
            return redirect('home')

        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Crear usuario con los datos del formulario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            messages.success(request, "¡Registro exitoso! Por favor inicia sesión.")
            return redirect('login')

        return render(request, self.template_name, {'form': form})


# ============================================================
# 3. VISTA DE PERFIL
# ============================================================
class UserProfileView(LoginRequiredMixin, UpdateView):
    """Vista para que el usuario edite su perfil y cambie su contraseña."""
    model = User
    form_class = UserProfileForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('home')

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
            return redirect('login')
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
        return redirect('home')