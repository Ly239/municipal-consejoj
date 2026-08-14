## # Guía rápida para poner en marcha el proyecto
---

🚀 Cómo levantar el proyecto localmente

Requisitos previos

· Python 3.7.2 o superior
· PostgreSQL (o SQLite para pruebas rápidas)
· Git

Pasos

```bash
# 1. Clonar el repositorio (privado)
git clone https://github.com/tu-usuario/proyecto-consejo-comunal.git
cd proyecto-consejo-comunal

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (crear archivo .env)
# Ejemplo mínimo:
DEBUG=True
SECRET_KEY=tu-clave-secreta
DATABASE_URL=postgres://usuario:pass@localhost:5432/consejo_db

# 5. Migrar base de datos y cargar seeders
python manage.py makemigrations
python manage.py migrate
python manage.py seeders

# 6. Ejecutar servidor local
python manage.py runserver


# 7. Acceder

· Sitio web: http://127.0.0.1:8000/
· Administrador: http://127.0.0.1:8000/admin/ (usuario root, contraseña admin123)
· Inicio de sesión para líder: http://127.0.0.1:8000/auth/login/ (usuario lider, contraseña lider123)

#8. Comandos útiles

Comando Propósito
python manage.py seeders Recargar datos iniciales (idempotente)
python manage.py createsuperuser Crear superusuario manual (si no usas seeders)
python manage.py test Ejecutar pruebas (cuando se escriban)

```


---


## 🌱 Seeders (datos iniciales)

Todos los seeders se encuentran en `abcstracts/management/commands/`. Se ejecutan con:

```bash
python manage.py seeders
```

¿Qué cargan?

Comando Datos cargados
seed_basic_data.py Tipos de documento, categorías especiales, tipos de movimiento, estados de proyecto, tipos de proyecto.
seed_permissions.py Permisos soft_delete_* y restore_* para cada modelo que herede de BaseModel.
seed_groups.py Grupo Líder de Calle con permisos relevantes.
seed_root_user.py Usuario root (superadmin) y usuario lider (ejemplo práctico).

Los seeders están diseñados para ser idempotentes: si los datos ya existen, no los duplican.
