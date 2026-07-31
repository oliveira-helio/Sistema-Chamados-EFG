from django.db import migrations, models


DEPARTMENT_CHOICES = [
    ("DIRETORIA", "Diretoria"),
    ("VICE_DIRETORIA", "Vice-diretoria"),
    ("TI", "Tecnologia da Informação"),
    ("PSICOLOGIA", "Psicologia"),
    ("SEGURANCA", "Segurança"),
    ("ZELADORIA", "Zeladoria"),
    ("COZINHA", "Cozinha"),
    ("MANUTENCAO", "Manutenção"),
    ("ESTAGIO", "Estágio"),
    ("MONITORIA", "Monitoria"),
    ("RECURSOS_HUMANOS", "Recursos humanos"),
    ("NUCLEO_EAD", "Núcleo de EAD"),
    ("SECRETARIA", "Secretaria"),
    ("STAI", "Stai"),
    ("COORDENACAO_PEDAGOGICA", "Coordenação pedagógica"),
    ("COORDENACAO_TECNICA", "Coordenação técnica"),
    ("BIBLIOTECA", "Biblioteca"),
    ("LABORATORIOS", "Laboratórios"),
    ("DOCENCIA", "Docência"),
]


CARGO_CHOICES = [
    ("DIRETOR", "Diretor(a)"),
    ("VICE_DIRETOR", "Vice-diretor(a)"),
    ("TEC_INFORMATICA", "Técnico(a) de Informática"),
    ("PSICOLOGO", "Psicologo(a)"),
    ("GUARDA_PATRIMONIAL", "Guarda Patrimonial"),
    ("ZELADOR", "Zelador(a)"),
    ("AUX_COZINHA", "Aux. de Cozinha"),
    ("SERVICOS_GERAIS", "Serviços Gerais"),
    ("JOVEM_APRENDIZ", "Jovem-Aprendiz"),
    ("MONITOR_PATIO", "Monitor(a) de Pátio"),
    ("ANALISTA_RH", "Analista de RH"),
    ("SUPERVISOR_EAD", "Supervisor EAD"),
    ("SUPERVISOR_INFRA_TI_SUPORTE_EAD", "Supervisor de Infraestrutura de TI e Suporte EAD"),
    ("SECRETARIO", "Secretario(a)"),
    ("AUX_ADM_EDUCACIONAL", "Aux. Adm. Educacional"),
    ("COORD_STAI", "Coordenador de Stai"),
    ("CONSULTOR_TI", "Consultor(a) de T.I"),
    ("CONSULTOR_NEGOCIOS", "Consultor(a) de Negocios"),
    ("TEC_LAB_INOVACAO", "Tec. de Lab. de Inovação"),
    ("COORD_PEDAGOGICO", "Coordenador(a) Pedagógico(a)"),
    ("COORD_TECNICO", "Coordenador(a) Técnico(a)"),
    ("ASSISTENTE_COORDENACAO", "Assistente de coordenação"),
    ("TECNICO_EDUCACIONAL", "Técnico(a) Adm. Educacional"),
    ("ASSISTENTE_EDUCACIONAL", "Assistente educacional"),
    ("BIBLIOTECARIO", "Bibliotecário(a)"),
    ("AUX_BIBLIOTECA", "Aux. de Biblioteca"),
    ("TECNICO_LABORATORIO", "Técnico(a) de Laboratório"),
    ("MONITOR_LABORATORIO", "Monitor(a) de Laboratório"),
    ("HORISTA", "Professor Horista"),
    ("MENSALISTA", "Professor Mensalista"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0007_normalize_hierarchy_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="first_access",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_access",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="department",
            field=models.CharField(choices=DEPARTMENT_CHOICES, max_length=40),
        ),
        migrations.AlterField(
            model_name="ticketcategory",
            name="department",
            field=models.CharField(choices=DEPARTMENT_CHOICES, max_length=40),
        ),
        migrations.AlterField(
            model_name="user",
            name="department",
            field=models.CharField(blank=True, choices=DEPARTMENT_CHOICES, default="", max_length=40),
        ),
        migrations.AlterField(
            model_name="user",
            name="cargo",
            field=models.CharField(choices=CARGO_CHOICES, default="TEC_INFORMATICA", max_length=40),
        ),
    ]
