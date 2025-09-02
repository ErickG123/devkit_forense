# DevKit Forense – Ferramenta Educacional de Perícia Digital

![Python](https://img.shields.io/badge/Python-3.11-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100-green.svg) ![Typer](https://img.shields.io/badge/Typer-0.7-orange.svg) ![SQLite](https://img.shields.io/badge/SQLite-3.41.2-lightgrey.svg)

## Sumário
1. [Introdução](#introdução)  
2. [Estrutura do Projeto](#estrutura-do-projeto)  
3. [Módulos Forenses](#módulos-forenses)  
   - [Network](#network)  
   - [Browser](#browser)  
   - [Email](#email)  
4. [Tecnologias Utilizadas](#tecnologias-utilizadas)  
5. [Planejamento e Futuras Extensões](#planejamento-e-futuras-extensões)  
6. [Instalação](#instalação)  
7. [Exemplos de Execução](#exemplos-de-execução)  

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
| Função | Descrição |
|--------|-----------|
| `ipinfo` | Consulta informações detalhadas sobre um endereço IP. |
| `arpscan` | Varre a rede para identificar dispositivos conectados via ARP. |
| `dnscan` | Realiza levantamento de informações de DNS de domínios e hosts. |
| `snmpscan` | Realiza varredura SNMP em dispositivos de rede. |
| `smbscan` | Verifica serviços SMB ativos em um host . |
| `sweep` | Verifica quais hosts estão ativos em uma faixa de IP. |
| `traceroute` | Traça o caminho percorrido por pacotes até um host alvo. |
| `map` | Gera mapa visual de hosts e conexões detectadas. |
| `scan` | Identifica portas abertas e serviços ativos em hosts. |
| `fingerprinting` | Identifica sistemas, serviços e versões na rede. |

### Browser
| Função | Descrição |
|--------|-----------|
| `logins` | Extração de credenciais armazenadas no Chrome e Edge. |
| `favscreen` | Captura e organiza screenshots de sites favoritos ou acessados. |
| `words` | Identifica palavras mais comuns em histórico de navegação e downloads. |
| `history` | Coleta histórico de navegação de diferentes browsers. |
| `patterns` | Identifica padrões suspeitos em histórico de navegação ou downloads. |
| `downloads` | Lista arquivos baixados pelos usuários. |

### Email
| Função | Descrição |
|--------|-----------|
| `email_parser` | Extrai e organiza informações de emails. |
| `header_analysis` | Analisa cabeçalhos para identificar origem, roteamento e possíveis fraudes. |

---

## 4. Tecnologias Utilizadas

- **Python** – Linguagem principal do projeto.  
- **FastAPI** – API para integração e execução de módulos.  
- **Typer** – CLI estruturada e interativa.  
- **SQLite** – Banco de dados local leve.  

---

## 5. Planejamento e Futuras Extensões

| Aplicação / Módulo | Objetivo | Possíveis Extensões |
|-------------------|----------|------------------|
| Dashboard | Painel central para visualização e execução de módulos | Filtros avançados, alertas em tempo real, integração direta com relatórios |
| Visualizadores | Transformar dados da CLI em gráficos, mapas e tabelas | Timeline interativa, heatmaps de rede, gráficos de comportamento de usuários |
| Wizard | Guiar o usuário passo a passo | Templates de análise rápida, integração automática com módulos de email e data, relatórios PDF/HTML |
| Novos módulos CLI | Expansão da análise forense | Logs de sistemas, recuperação de dispositivos móveis, análise de mídia, detecção de malware, integração com threat intelligence |
| Ferramentas auxiliares | Suporte a módulos existentes e novos | Exportação avançada de relatórios, dashboards customizáveis, notificações em tempo real |

---

## 6. Instalação

```bash
pip install forensic-cli
```

---

## 7. Exemplos de Execução

**CLI:**
```bash
# Executar módulo de network scan
forensic-cli network map --network 192.168.0.0/24

# Coletar histórico do Chrome
forensic-cli browser history --chrome
```

**API:**
```bash
# Executar API
uvicorn api.main:app --reload
```
