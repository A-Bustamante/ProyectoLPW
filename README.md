# Sistema de Control de Inventarios de Activos TI (CMDB)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Bootstrap](https://img.shields.io/badge/bootstrap-%238511FA.svg?style=for-the-badge&logo=bootstrap&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23F7DF1E.svg?style=for-the-badge&logo=javascript&logoColor=black)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)

Este proyecto es una aplicación web a la medida enfocada en el **Control de Inventarios de Activos TI (CMDB)** de la organización, integrando una arquitectura robusta Full-Stack basada en Django y la interfaz moderna Jazzmin, acoplando los principios **SOLID**, metodologías ágiles y estándares internacionales de calidad y seguridad.

---

## 👨‍💻 Autoría y Desarrollo
Este software ha sido diseñado, desarrollado y validado por:
*   **Autor/Desarrollador:** Cristian Alejandro Bustamante Escobar

---

## 🛠️ Stack Tecnológico y Arquitectura

El proyecto está diseñado bajo una arquitectura desacoplada y transaccional:

*   **Backend (Capa de Lógica):** 
    *   **Django 4.2 (Python 3.14.7)**: Framework robusto con inyección de parches para compatibilidad de RequestContext bajo Python 3.14.
    *   **Django ORM**: Mapeo relacional seguro de la base de datos de configuración de activos.
    *   **Jazzmin / AdminLTE**: Interfaz visual avanzada y responsiva para el panel administrativo de analistas de TI.
*   **Frontend (Capa de Presentación):**
    *   **HTML5 Semántico + CSS3 (Bootstrap 5)**: Interfaz oscura premium responsiva y moderna.
    *   **Custom Dark CSS (index.css)**: Estilos enriquecidos con gradientes dinámicos, glassmorphism y micro-animaciones.
    *   **Vanilla JavaScript**: Interactividad del lado del cliente y previsualizador de imágenes en vivo.
*   **Base de Datos y Caché:**
    *   **PostgreSQL / SQLite**: Base de datos relacional transaccional (con soporte adaptativo local).
    *   **Redis**: Sistema de caché en memoria para sesiones y optimización de dashboard.
*   **Infraestructura:**
    *   **Docker & Docker Compose**: Contenedorización de PostgreSQL, Redis y la app web.

---

## 📦 Módulos Funcionales

1.  **MÓDULO A: Registro y Codificación de Activos TI**
    *   Soporta clasificación jerárquica de activos (Laptops, Smartphones, Monitors, etc.).
    *   Autogenera códigos de barra/QR unívocos y códigos internos estructurados por año e incremental (ej. `LAP-2026-0042`).
    *   Carga estricta de imágenes físicas de evidencia (<5MB, formatos JPG/PNG).
2.  **MÓDULO B: Registro y Vinculación de Personal**
    *   Administración de colaboradores (ID, Nombres, Rol, Departamento, Email).
    *   Flag de control de vinculación (`Activo / Inactivo`). Si el colaborador está inactivo, el sistema restringe asignaciones y exige devoluciones pendientes.
3.  **MÓDULO C: Flujo de Check-In / Check-Out (Préstamos y Retornos)**
    *   **Check-Out:** Asigna activos en bodega a colaboradores activos, genera el acta PDF legal de entrega, y exige la carga del acta firmada.
    *   **Check-In:** Recibe equipos registrando el analista, la fecha/hora, accesorios y estado de daños, emitiendo alertas a RH en caso de mal uso.
4.  **MÓDULO D: Consolidación de Reportes y Auditorías**
    *   Dashboard analítico acelerado por caché con gráficos en tiempo real de la distribución del inventario.
    *   Buscador global por serial, código interno o ID de colaborador con visualización de línea de tiempo cronológica (Trazabilidad).

---

## 🔒 Estándares de Seguridad y Calidad

*   **ISO/IEC 27001 (Control de Acceso y Logs)**: 
    *   Registro automático e inmutable de auditoría (`AuditLog`) para cada acción (Checkout, Checkin, Borrado).
    *   Control de acceso basado en roles (RBAC) y desactivación completa de edición o borrado de logs en el panel de administración.
    *   **Borrado Remoto (Remote Wipe)**: Botón para reportes de extravío o robo, inhabilitando inmediatamente el equipo en la CMDB.
*   **IEEE 829 / ISO 29119 (Pruebas Unitarias)**:
    *   Suite de 9 pruebas unitarias verificando la doble asignación, límites de imágenes, desactivación de personal y coherencia del algoritmo de códigos.

---

## 🚀 Guía de Inicio Rápido (Entorno Local)

### 1. Requisitos Previos
*   Python 3.12, 3.13 o 3.14 instalado en el sistema.
*   Docker y Docker Compose (opcional para Postgres y Redis).

### 2. Configurar el Entorno Virtual
Ubíquese en el directorio del proyecto y ejecute:
```bash
# Crear entorno virtual
python -m venv venv

# Activar venv (Windows PowerShell)
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Migraciones y Base de Datos (SQLite Fallback)
El sistema detecta automáticamente la disponibilidad del servidor de Postgres. Para pruebas locales instantáneas con SQLite, solo prepare la base de datos:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Lanzar Servidor
Inicie la aplicación localmente:
```bash
python manage.py runserver
```
La aplicación web estará disponible en [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🔑 Credenciales por Defecto
*   **URL del Panel Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
*   **Usuario Administrador:** `admin`
*   **Contraseña:** `admin1234`

---

## 🐳 Despliegue con Docker Compose

Si prefiere ejecutar todo el stack (Django + PostgreSQL + Redis) en contenedores Docker:
```bash
docker-compose up --build
```
El contenedor ejecutará automáticamente las migraciones y levantará la aplicación en el puerto `8000`.
