from django.core.management.base import BaseCommand

from tickets.models import TicketCategory


DEFAULT_CATEGORIES = {
    "DIRETORIA": [
        ("Demandas da diretoria", "Solicitacoes e tratativas ligadas a diretoria."),
        ("Reunioes estrategicas", "Agendamento de reunioes e pautas institucionais."),
        ("Parcerias e comunicacao institucional", "Assuntos com parceiros externos e comunicacao oficial."),
    ],
    "VICE_DIRETORIA": [
        ("Tecnologia da Informacao", "Suporte a computadores, rede e sistemas."),
        ("Psicologia", "Apoio psicologico e mediaacao de conflitos."),
        ("Seguranca", "Controle de acesso, seguranca patrimonial e rondas."),
        ("Zeladoria", "Limpeza, organizacao e apoio geral."),
        ("Cozinha", "Rotinas, apoio operacional e manutencao da cozinha."),
        ("Manutencao", "Pequenos reparos e servicos gerais."),
        ("Estagio", "Demandas relacionadas a jovem aprendiz."),
        ("Monitoria", "Apoio a monitoria de patio e disciplina."),
    ],
    "SECRETARIA": [
        ("Atendimento ao aluno", "Duvidas, documentos e atendimento ao publico."),
        ("Lancamentos e registros", "Lancamentos em sistema e organizacao de registros."),
        ("Outros assuntos da secretaria", "Demandas gerais da secretaria."),
    ],
    "STAI": [
        ("Apoio tecnico e inovacao", "Demandas de TI, negocios e inovacao."),
        ("Labs e projetos", "Uso de laboratorios e projetos de inovacao."),
        ("Outros assuntos do STAI", "Demandas gerais do setor."),
    ],
    "COORDENACAO_PEDAGOGICA": [
        ("Acompanhamento pedagogico", "Demandas relacionadas ao desempenho e frequencia."),
        ("Inclusao e acessibilidade", "Suporte pedagogico e acessibilidade."),
        ("Reunioes e alinhamentos", "Solicitacao de reunioes pedagogicas."),
        ("Outros assuntos pedagogicos", "Demandas gerais da coordenacao pedagógica."),
    ],
    "COORDENACAO_TECNICA": [
        ("Acompanhamento tecnico", "Demandas tecnicas e curriculares."),
        ("Duvidas sobre matriz", "Duvidas sobre matriz, ementas e cargas horarias."),
        ("Outros assuntos tecnicos", "Demandas gerais da coordenacao tecnica."),
    ],
    "BIBLIOTECA": [
        ("Acervo e reposicao", "Sugerir titulos e reposicao de acervo."),
        ("Reserva de espaco", "Agendamento de espaco e atividades."),
        ("Emprestimos", "Solicitacao de emprestimos e reservas."),
    ],
    "LABORATORIOS": [
        ("Aulas praticas", "Organizacao de aulas praticas e equipamentos."),
        ("Insumos", "Pedido de materiais de consumo."),
        ("Manutencao de equipamentos", "Falhas mecanicas e calibracao."),
    ],
    "DOCENCIA": [
        ("Sala de aula", "Demandas relacionadas as aulas e turmas."),
        ("Recursos didaticos", "Solicitacao de materiais e suporte."),
        ("Outros assuntos da docencia", "Demandas gerais dos professores."),
    ],
}


class Command(BaseCommand):
    help = "Cria categorias iniciais para o sistema de chamados."

    def handle(self, *args, **options):
        created = 0
        for department, categories in DEFAULT_CATEGORIES.items():
            for name, description in categories:
                _, was_created = TicketCategory.objects.update_or_create(
                    department=department,
                    name=name,
                    defaults={"description": description, "is_active": True},
                )
                created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Categorias inicializadas. Novas criadas: {created}"))
