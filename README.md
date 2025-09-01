# DevKit Forense – Ferramenta Educacional de Perícia Digital

![Python](https://img.shields.io/badge/Python-3.11-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100-green.svg) ![Typer](https://img.shields.io/badge/Typer-0.7-orange.svg) ![SQLite](https://img.shields.io/badge/SQLite-3.41.2-lightgrey.svg)

## Sumário
1. [Introdução](#introdução)  
2. [Estrutura do Projeto](#estrutura-do-projeto)  
3. [Módulos Forenses](#módulos-forenses)  
   - [Network](#network)  
   - [Browser](#browser)  
   - [Email](#email)  
4. [Aplicações de Apoio](#aplicações-de-apoio)  
   - [Dashboard](#dashboard)  
   - [Visualizadores de Resultados](#visualizadores-de-resultados)  
   - [Assistente Interativo (Wizard)](#assistente-interativo-wizard)  
5. [Fluxo de Integração](#fluxo-de-integração)  
6. [Tecnologias Utilizadas](#tecnologias-utilizadas)  
7. [Planejamento e Futuras Extensões](#planejamento-e-futuras-extensões)  
8. [Instalação](#instalação)  
9. [Exemplos de Execução](#exemplos-de-execução)  
10. [Considerações Finais](#considerações-finais)

---

## 1. Introdução

**Objetivo:**  
O DevKit Forense é uma suíte de ferramentas educacionais para análise de evidências digitais, projetada para auxiliar no ensino de perícia digital. Combina **CLI**, **API** e **aplicações de apoio**, tornando o uso mais interativo, visual e didático.  

**Escopo:**  
- Execução de análises forenses em browsers, arquivos, emails e redes.  
- Visualização interativa de resultados.  
- Geração de relatórios automáticos.  
- Assistente interativo (Wizard) para guiar o usuário em tarefas complexas.  

**Público-alvo:**  
- Estudantes e professores de Segurança da Informação e Perícia Digital.  

---

## 2. Estrutura do Projeto

O DevKit está organizado em três camadas principais:

1. **CLI** – Executa os módulos forenses pelo terminal.  
2. **API** – Interface programática para execução de módulos e integração com dashboards.  
3. **Core** – Contém a lógica central, classes, funções e utilitários compartilhados pelos módulos.  

---

## 3. Módulos Forenses

### Network
| Módulo | Descrição |
|--------|-----------|
| `arp_scan` | Varre a rede para identificar dispositivos conectados via ARP. |
| `dns_recon` | Realiza levantamento de informações de DNS de domínios e hosts. |
| `fingerprinting` | Identifica sistemas, serviços e versões na rede. |
| `ip_info` | Consulta informações detalhadas sobre um endereço IP. |
| `network_map` | Gera mapa visual de hosts e conexões detectadas. |
| `ping_sweep` | Verifica quais hosts estão ativos em uma faixa de IP. |
| `port_scanner` | Identifica portas abertas e serviços ativos em hosts. |
| `snmp_scan` | Realiza varredura SNMP em dispositivos de rede. |
| `traceroute` | Traça o caminho percorrido por pacotes até um host alvo. |

### Browser
| Módulo | Descrição |
|--------|-----------|
| `browser_history` | Coleta histórico de navegação de diferentes browsers. |
| `common_words` | Identifica palavras mais comuns em histórico de navegação e downloads. |
| `downloads_history` | Lista arquivos baixados pelos usuários. |
| `fav_screen` | Captura e organiza screenshots de sites favoritos ou acessados. |
| `full_browser_history` | Consolida todo histórico de navegação em um único relatório. |
| `logins_chrome` | Extração de credenciais armazenadas no Chrome. |
| `logins_edge` | Extração de credenciais armazenadas no Edge. |
| `unusual_patterns` | Identifica padrões suspeitos em histórico de navegação ou downloads. |

### Email
| Módulo | Descrição |
|--------|-----------|
| `email_parser` | Extrai e organiza informações de emails. |
| `header_analysis` | Analisa cabeçalhos para identificar origem, roteamento e possíveis fraudes. |

---

## 4. Aplicações de Apoio

### Dashboard
**Objetivo:** Centralizar informações e permitir execução rápida de módulos.  

**Funcionalidades:**  
- Menu lateral com módulos do DevKit.  
- Cards com resumo de análises recentes.  
- Acesso direto a visualizadores e Wizard.  

**Tecnologias sugeridas:** Streamlit (web), PyQt (desktop).  

### Visualizadores de Resultados
**Objetivo:** Transformar saídas da CLI em gráficos e tabelas interativas.  

**Exemplos:**  
- Mapas de rede interativos.  
- Timeline de eventos e logs.  
- Gráficos de arquivos analisados, tipos e padrões suspeitos.  

**Integração:** Recebe dados da CLI em formato JSON ou CSV.  

### Assistente Interativo (Wizard)
**Objetivo:** Guiar o usuário passo a passo em tarefas complexas.  

**Exemplo de fluxo:**  
1. Seleção do tipo de análise (pendrive, rede, logs, etc.)  
2. Configuração de opções (scan de malware, intervalo de IP, dispositivo alvo)  
3. Execução automática dos módulos necessários  
4. Geração de relatórios e acesso aos visualizadores  

**Tecnologias sugeridas:**  
- Terminal interativo (`questionary`, `PyInquirer`)  
- Web/Desktop (mesmo framework do Dashboard)  

---

## 5. Fluxo de Integração

1. CLI executa módulos → gera resultados.  
2. API possibilita integração programática com dashboards e outras aplicações.  
3. Dashboard centraliza execução e resumo dos resultados.  
4. Visualizadores transformam dados em gráficos e tabelas interativas.  
5. Wizard guia o usuário em tarefas complexas.  

---

## 6. Tecnologias Utilizadas

- **Python** – Linguagem principal do projeto.  
- **FastAPI** – API para integração e execução de módulos.  
- **Typer** – CLI estruturada e interativa.  
- **SQLite** – Banco de dados local leve.  

---

## 7. Planejamento e Futuras Extensões

| Aplicação / Módulo | Objetivo | Possíveis Extensões |
|-------------------|----------|------------------|
| Dashboard | Painel central para visualização e execução de módulos | Filtros avançados, alertas em tempo real, integração direta com relatórios |
| Visualizadores | Transformar dados da CLI em gráficos, mapas e tabelas | Timeline interativa, heatmaps de rede, gráficos de comportamento de usuários |
| Wizard | Guiar o usuário passo a passo | Templates de análise rápida, integração automática com módulos de email e data, relatórios PDF/HTML |
| Novos módulos CLI | Expansão da análise forense | Logs de sistemas, recuperação de dispositivos móveis, análise de mídia, detecção de malware, integração com threat intelligence |
| Ferramentas auxiliares | Suporte a módulos existentes e novos | Exportação avançada de relatórios, dashboards customizáveis, notificações em tempo real |

---

## 8. Instalação

```bash
# Clonar o repositório
git clone https://github.com/ErickG123/devkit_forense.git
cd devkit-forense

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows

# Instalar dependências
pip install -r requirements.txt
```

---

## 9. Exemplos de Execução

**CLI:**
```bash
# Executar módulo de network scan
python cli.py network_map --target 192.168.0.0/24

# Coletar histórico do Chrome
python cli.py browser_history --browser chrome
```

**API:**
```bash
# Executar API
uvicorn api.main:app --reload
```

---

## 10. Considerações Finais

O DevKit Forense combina **educação e prática**, permitindo que usuários explorem análise forense digital de forma segura, didática e interativa.  
As aplicações de apoio aumentam a acessibilidade e engajamento, tornando o estudo da perícia digital mais visual e intuitivo.  
O planejamento de novos módulos e ferramentas garante evolução contínua da plataforma, mantendo-a atualizada e relevante para atividades acadêmicas e laboratoriais.
