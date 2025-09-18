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

# DevKit Forense: Uma Suíte de Ferramentas Educacionais para Análise Forense Digital

## 📖 Introdução

O estudo da perícia forense digital, embora fascinante, apresenta uma curva de aprendizado íngreme. Ferramentas profissionais são poderosas, mas muitas vezes complexas e pouco intuitivas para estudantes que estão dando os primeiros passos na área.

Para endereçar essa lacuna, o **DevKit Forense** foi desenvolvido como um projeto de TCC. Trata-se de uma suíte de ferramentas projetada desde o início com um **foco educacional**. Nosso objetivo é simplificar a análise de evidências digitais, tornando o processo de aprendizado mais interativo, visual e didático.

Este projeto é destinado a **estudantes e professores da área de Segurança da Informação e Perícia Digital**, servindo como uma ponte entre o conhecimento teórico e a aplicação prática.

---

## ✨ Recursos em Destaque

O DevKit Forense combina o poder da linha de comando com a clareza de interfaces gráficas para oferecer uma experiência de aprendizado completa.

* **🔍 Análise Multifacetada:** Execute módulos de análise forense focados nos artefatos mais comuns do dia a dia digital, incluindo:
    * Navegadores Web (histórico, cache, downloads)
    * Clientes de E-mail
    * Tráfego de Rede (análise de pacotes)

---

## 🏛️ Arquitetura do Projeto

Para garantir modularidade e flexibilidade, o DevKit foi estruturado em três camadas principais, cada uma com um propósito claro:

1.  **`CLI (Command-Line Interface)`**
    * **O que faz:** É a porta de entrada para a execução direta dos módulos forenses. Ideal para automação de tarefas, scripts e para usuários que preferem a agilidade do terminal.

2.  **`API (Application Programming Interface)`**
    * **O que faz:** Expõe as funcionalidades do Core de forma programática. Permite que as aplicações de apoio (como dashboards visuais) consumam os dados e executem análises, além de possibilitar a integração do DevKit com outras ferramentas.

3.  **`Core`**
    * **O que faz:** É o coração do projeto. Contém toda a lógica de negócio, as classes, funções e utilitários de análise. Centralizar a lógica no Core garante que as regras sejam consistentes, o código seja reutilizável e a manutenção seja simplificada, já que tanto a CLI quanto a API consomem desta mesma base.

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
A forma mais simples de instalar a CLI é utilizando o **PyPI**.  
Execute o seguinte comando no terminal:

```bash
pip install forensic-cli
```

## 7. Exemplos de Execução da CLI

### Comandos de Rede (`network`)

Utilitários para escanear, mapear e analisar redes e dispositivos.

### `map`
Mapeia dispositivos ativos na rede e salva os resultados em arquivos JSON e CSV.

**Sintaxe:**
```bash
forensic-cli network map --network <RANGE_IP> [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --network | -n | Range de IPs da rede. Ex: 192.168.1.1-254 | Obrigatório |
| --ports | -p | Portas para escanear em cada host. | 21,22,80,443,445,8080 |
| --output | -o | Diretório para salvar os resultados. | ./output |

### `scan`
Realiza um scan de portas em um host específico e exibe os resultados em uma tabela.

**Sintaxe:**
```bash
forensic-cli network scan --target <ALVO> [OPÇÕES]
```

Opções:
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --target | -t | Alvo do scan (IP ou hostname). | Obrigatório |
| --ports | -p | Portas para escanear. Ex: '22,80,100-200'. | 21,22,53,80,443,445,3306,8080 |

### `sweep`
Verifica hosts ativos em um range de IPs via ping.

**Sintaxe:**
```bash
forensic-cli network sweep --network <RANGE_IP>
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --network | N/A | Range de IPs da rede. Ex: 192.168.1.1-254 | Obrigatório |

### `fingerprinting`
Detecta o sistema operacional, serviços e portas abertas em um host.

**Sintaxe:**
```bash
forensic-cli network fingerprinting --ip <IP_HOST>
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --ip | N/A | Endereço IP do host. Ex: 192.168.0.10 | Obrigatório |

### `traceroute`
Exibe o caminho (hops) e a latência (RTT) até um domínio ou host.

**Sintaxe:**
```bash
forensic-cli network traceroute --domain <DOMINIO>
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --domain | N/A | Informe um domínio ou hostname. Ex: google.com | Obrigatório |

### `arpscan`
Realiza uma varredura ARP para identificar dispositivos na rede local.

**Sintaxe:**
```bash
forensic-cli network arpscan --network <RANGE_IP>
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --network | N/A | Range de IPs da rede. Ex: 192.168.1.1-254 | Obrigatório |

### `dnscan`
Realiza reconhecimento DNS em um domínio ou IP, com opção de buscar subdomínios.

**Sintaxe:**
```bash
forensic-cli network dnscan --target <ALVO> [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --target | N/A | Domínio ou IP alvo. Ex: exemplo.com | Obrigatório |
| --output-dir | N/A | Diretório para salvar os resultados (JSON e CSV). | Nenhum |
| --with-subdomains | N/A | Tenta descobrir subdomínios comuns. | False |

### `ipinfo`
Obtém informações detalhadas (geolocalização, ASN) sobre um IP ou hostname.

**Sintaxe:**
```bash
forensic-cli network ipinfo --ip <IP_HOST>
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --ip | N/A | IP ou hostname do destino. Ex: 8.8.8.8 | Obrigatório |

### `smbscan`
Verifica serviços SMB (Server Message Block) ativos em um host.

**Sintaxe:**
```bash
forensic-cli network smbscan --ip <IP_HOST>
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --ip | N/A | IP ou hostname do destino. Ex: 192.168.0.10 | Obrigatório |

### `snmpscan`
Executa uma varredura SNMP (Simple Network Management Protocol) para obter informações de um dispositivo.

**Sintaxe:**
```bash
forensic-cli network snmpscan --ip <IP_HOST>
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --ip | N/A | IP ou hostname do destino. Ex: 192.168.0.10 | Obrigatório |

### Comandos de Navegador (`browser`)
Ferramentas para extrair e analisar artefatos de navegadores web como Chrome, Edge e Firefox.

### `history`
Extrai o histórico de navegação dos navegadores instalados.

**Sintaxe:**
```bash
forensic-cli browser history [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --chrome | N/A | Extrair histórico do Google Chrome. | False |
| --edge | N/A | Extrair histórico do Microsoft Edge. | False |
| --firefox | N/A | Extrair histórico do Mozilla Firefox. | False |
| --all | N/A | Extrair de todos os navegadores suportados. | False |

### `downloads`
Extrai o histórico de downloads dos navegadores.

**Sintaxe:**
```bash
forensic-cli browser downloads [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --output-dir | -o | Diretório para salvar os artefatos. | artefatos/downloads |
| --chrome | N/A | Extrair downloads do Chrome. | False |
| --edge | N/A | Extrair downloads do Edge. | False |
| --firefox | N/A | Extrair downloads do Firefox. | False |
| --all | N/A | Extrair de todos os navegadores. | False |

### `favscreen`
Processa arquivos de histórico (.json), captura favicons e screenshots das URLs encontradas.

**Sintaxe:**
```bash
forensic-cli browser favscreen [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --input-dir | -i | Diretório contendo os JSONs de histórico. | artefatos/historico |
| --output-dir | -o | Diretório para salvar favicons e prints. | artefatos/favscreen |

### `logins`
Extrai senhas e logins salvos no Chrome e Edge.

**Sintaxe:**
```bash
forensic-cli browser logins [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --output-dir | -o | Diretório para salvar os logins em JSON. | artefatos/logins |
| --chrome | N/A | Extrair logins do Chrome. | False |
| --edge | N/A | Extrair logins do Edge. | False |
| --all | N/A | Extrair de todos os navegadores. | False |

### `patterns`
Analisa arquivos de histórico (.json) para encontrar padrões de navegação e gera gráficos.

**Sintaxe:**
```bash
forensic-cli browser patterns [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --input-dir | -i | Diretório com os JSONs de histórico. | artefatos/historico |
| --output-dir | -o | Diretório para salvar gráficos e relatórios. | artefatos/patterns_output |

### `words`
Extrai as palavras mais pesquisadas do histórico do navegador.

**Sintaxe:**
```bash
forensic-cli browser words [OPÇÕES]
```

**Opções:**
| Opção | Atalho | Descrição | Padrão |
| :--- | :---: | :--- | :--- |
| --output-dir | -o | Diretório para salvar o JSON com as palavras. | artefatos/words_output |
| --chrome | N/A | Extrair palavras do Chrome. | True |
