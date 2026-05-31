# 🚌 Gerenciador Pé Na Estrada Tour

Um sistema desktop robusto desenvolvido para otimizar a operação, o financeiro e o controle de embarque de passageiros em agências de excursões rodoviárias.

## 🚀 Sobre o Projeto
Este software foi construído como um laboratório prático de Engenharia de Software, aplicando conceitos de arquitetura, banco de dados relacionais e design de interface (UI/UX) para resolver um problema real de gestão do setor de turismo. A aplicação elimina planilhas manuais, centralizando a venda de passagens e a emissão de relatórios governamentais em um único executável local.

## ✨ Principais Funcionalidades
* **Dashboard Gerencial:** Tela interativa de boas-vindas com métricas vivas, atalhos de navegação profunda e lista de próximos passeios com barras de progresso (`CTkProgressBar`) de lotação.
* **Módulo de Fluxo de Caixa Global:** Visualização macro do faturamento, custos operacionais totais e lucro líquido consolidado de todas as excursões.
* **Gestão Kanban de Excursões:** Quadro visual dinâmico com colunas de status (A Realizar, Finalizados, Cancelados).
* **Alocação Visual de Poltronas:** Interface gráfica que gera o grid do ônibus matematicamente e gerencia assentos livres/ocupados em tempo real.
* **Módulo Financeiro Local:** Gestão de pagamentos (parciais e totais) integrados ao mapa do ônibus, com cálculo de status dinâmico (Pendente, Parcial, Quitado).
* **Inteligência de Custos:** Motor de cálculo em tempo real de Custos Adicionais, Ponto de Equilíbrio e Margem de Lucro por excursão.
* **Motor de Exportação em PDF:** Emissão automática de Recibos de Pagamento no momento do lançamento, geração corporativa do Balanço Financeiro da viagem e Manifestos de Embarque (versões Completas e Resumidas) com proteção de dados.
* **Regra de Negócio de Dependentes:** Lógica estruturada para gerenciar crianças de colo compartilhando o mesmo assento físico do responsável no sistema.
* **Banco de Dados Relacional:** Controle integrado via SQLite, utilizando `JOINs` para cruzar passageiros, viagens e assentos.
* **Configurações e Segurança Avançada:** Painel de exportação manual de Backup do banco de dados com carimbo de data/hora, acoplado a uma rotina de *Self-Healing* que previne quebras sistêmicas ao restaurar backups antigos.

## 🛠️ Tecnologias Utilizadas
* **Python 3**
* **CustomTkinter:** Para a construção de uma interface gráfica moderna, responsiva e com modo escuro.
* **ReportLab:** Motor de renderização para a geração de relatórios de alta qualidade em PDF.
* **SQLite3:** Banco de dados nativo e autossuficiente para persistência de informações.
* **PyInstaller:** Empacotamento do projeto em um executável (`.exe`) independente.

## 🤖 O Processo de Desenvolvimento com IA
Este projeto é um *case* de **AI-Assisted Development** (Desenvolvimento Assistido por Inteligência Artificial). Em vez de delegar a criação do sistema de forma passiva, o fluxo de desenvolvimento dividiu responsabilidades entre o programador humano e duas inteligências artificiais:

1. **Google Gemini (Arquitetura e Regras de Negócio):**
   Atuou como um "Engenheiro de Software Sênior" e conselheiro. Foi utilizado para debater a modelagem do banco de dados (normalização, constraints), desenhar a lógica de programação (ex: cálculo das coordenadas das poltronas do ônibus), prever impactos em cascata em módulos já finalizados e redigir os *prompts* técnicos arquiteturais.
   
2. **Agente Integrado na IDE / Antigravity (Execução):**
   Atuou como o "Desenvolvedor Mão na Massa". Recebeu os planos de implementação validados e cuidou da digitação do código-fonte, injeção de bibliotecas, manipulação dos arquivos do projeto local e tratamento de exceções (como erros de permissão do sistema operacional).

Essa abordagem híbrida permitiu que o foco humano ficasse nas **decisões de alto nível e na qualidade do produto final**, enquanto a IA acelerava a codificação mecânica.

## 👨💻 Autor
**Cosmo Matias Gomes** *Estudante de Ciência da Computação na Universidade Federal da Paraíba (UFPB).*
