from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("sair/", views.logout_view, name="logout"),
    path("painel/", views.dashboard, name="dashboard"),
    path("api/categorias/", views.ticket_categories_api, name="ticket_categories_api"),
    path("api/cargos/", views.user_roles_api, name="user_roles_api"),
    path("chamados/", views.ticket_list, name="ticket_list"),
    path("chamados/novo/", views.ticket_create, name="ticket_create"),
    path("chamados/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("usuarios/", views.user_management, name="user_management"),
    path("usuarios/novo/", views.user_create, name="user_create"),
    path("usuarios/importar/", views.user_bulk_upload, name="user_bulk_upload"),
    path("usuarios/<int:pk>/editar/", views.user_edit, name="user_edit"),
    path("usuarios/<int:pk>/senha/", views.user_change_password, name="user_change_password"),
    path("usuarios/<int:pk>/ativar/", views.user_toggle_active, name="user_toggle_active"),
    path("anuncios/", views.announcement_management, name="announcement_management"),
    path("anuncios/novo/", views.announcement_create, name="announcement_create"),
    path("anuncios/<int:pk>/editar/", views.announcement_edit, name="announcement_edit"),
    path("anuncios/<int:pk>/publicar/", views.announcement_toggle_publish, name="announcement_toggle_publish"),
    path("anuncios/<int:pk>/remover/", views.announcement_delete, name="announcement_delete"),
]
