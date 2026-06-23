from django.core.management.base import BaseCommand

from tickets.models import TicketCategory


DEFAULT_CATEGORIES = {
    "DIRECAO": [
        ("Relacoes Institucionais e Parcerias", "Tratativas, propostas e demandas vinculadas a instituicoes externas e parceiros estrategicos."),
        ("Orgaos Colegiados e Conselhos", "Demandas, pautas, convocacoes e deliberacoes vinculadas aos Conselhos da Unidade de Ensino."),
        ("Agendamento e Reunioes de Alinhamento", "Solicitacao de agendas com a Direcao para alinhamentos estrategicos."),
        ("Outros Assuntos da Direcao", "Demandas gerais de alta gestao nao listadas anteriormente."),
    ],
    "VICE_DIRECAO": [
        ("Agendamento de Reunioes", "Solicitacao de agendas para reuniao com a Vice-direcao."),
        ("Mediacao de Conflitos e Clima Organizacional", "Tratativas preliminares de conflitos e convivencia."),
        ("Manutencao Predial e Infraestrutura", "Reparos estruturais, pintura, eletrica, hidraulica e zeladoria."),
        ("Outros Assuntos da Vice-direcao", "Demandas gerais da Vice-direcao."),
    ],
    "COORDENACAO_PEDAGOGICA": [
        ("Acompanhamento Pedagogico", "Demandas relacionadas ao desempenho, frequencia e risco de evasao."),
        ("Inclusao e Acessibilidade", "Suporte pedagogico para estudantes com necessidades educacionais especificas."),
        ("Reunioes", "Solicitacao de reunioes para alinhamento pedagogico."),
        ("Outros Assuntos do Pedagogico", "Demandas gerais do setor pedagogico."),
    ],
    "COORDENACAO_TECNICA": [
        ("Acompanhamento Tecnico-pedagogico", "Demandas vinculadas ao Jornada para o Futuro."),
        ("Duvidas sobre Matriz Curricular", "Duvidas sobre matriz, ementas, cargas horarias e competencias tecnicas."),
        ("Visitas e Assessoria Tecnico-pedagogica", "Agendamentos para assessoria junto as unidades externas."),
        ("Outros Assuntos da Coordenacao Tecnica", "Demandas gerais da Coordenacao Tecnica."),
    ],
    "BIBLIOTECA": [
        ("Reposicao / Sugestao de Acervo", "Indicacao de titulos e bibliografias."),
        ("Reserva de Espaco / Projetos de Leitura", "Agendamento do espaco fisico da biblioteca."),
        ("Emprestimo", "Solicitacao de emprestimo ou reserva de livros ou materiais didaticos."),
        ("Outros Assuntos da Biblioteca", "Demandas gerais da biblioteca."),
    ],
    "LABORATORIO_ENSINO": [
        ("Preparacao de Aula Pratica", "Organizacao do espaco, ferramentas e equipamentos para aulas."),
        ("Solicitacao / Reposicao de Insumos", "Pedido de materiais de consumo para experimentos e praticas."),
        ("Manutencao de Equipamentos de Laboratorio", "Falhas mecanicas, calibracao e danos em bancadas."),
        ("Outros Assuntos dos Laboratorios de Ensino", "Demandas gerais dos laboratorios."),
    ],
    "STAI": [
        ("Demandas de Mercado e Empresas", "Prospecção de serviços tecnologicos e solucoes para o setor produtivo local."),
        ("Reserva dos Espacos de Inovacao", "Agendamento ou liberacao de acesso dos ambientes de inovacao."),
        ("Ordens de Servico STAI", "Abertura, monitoramento ou entrega de diagnosticos e fluxos operacionais."),
        ("Outros Assuntos do STAI", "Demandas gerais do setor."),
    ],
    "SECRETARIA_ESCOLAR": [
        ("Gestao de Turmas e Matriculas", "Cadastro de turmas, efetivacao de matriculas e organizacao dos diarios."),
        ("Emissao de Documentos e Certificados", "Historicos, declaracoes, diplomas e certificados."),
        ("Registros Academicos e Sistemas Oficiais", "Lancamento e correcao de dados em sistemas oficiais."),
        ("Outros Assuntos da Secretaria", "Demandas gerais da secretaria escolar."),
    ],
    "TI": [
        ("Problemas com Hardware e Equipamentos", "Computadores lentos, projetores, impressoras e periféricos com defeito."),
        ("Acesso a Rede e Internet", "Falhas de conexao Wi-Fi, cabos de rede ou lentidao no sinal."),
        ("Contas, Logins e Ambientes Virtuais", "Reset de senhas e problemas de acesso a sistemas."),
        ("Instalacao de Softwares", "Necessidade de instalacao de programas especificos."),
        ("Outros Assuntos de TI", "Demandas gerais de TI."),
    ],
    "PSICOLOGIA_ESCOLAR": [
        ("Mediacao de Conflitos / Relacoes Interpessoais", "Demandas de intervencao para conflitos e desentendimentos."),
        ("Apoio ao Processo de Ensino-Aprendizagem", "Suporte a estudantes com dificuldades de aprendizagem."),
        ("Suporte em Crises / Acolhimento Emergencial", "Acolhimento e intervencao psicológica imediata."),
        ("Outros Assuntos de Psicologia Escolar", "Demandas gerais da psicologia escolar."),
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

