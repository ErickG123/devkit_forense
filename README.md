# DevKit Forense – Documento de Funcionalidades

## 1. Introdução

**Objetivo:**  
O DevKit Forense é uma suíte de ferramentas educacionais para análise de evidências digitais, projetada para auxiliar no ensino de perícia digital. Ele combina uma **CLI principal** com **aplicações de apoio** que tornam o uso mais interativo, visual e didático.  

**Escopo:**  
- Execução de análises forenses em navegadores, arquivos, emails e redes.  
- Visualização interativa de resultados.  
- Geração de relatórios automáticos.  
- Assistente interativo (Wizard) para guiar o usuário em tarefas complexas.  

**Público-alvo:**  
- Estudantes e professores de cursos de Segurança da Informação e Perícia Digital.  

---

## 2. Arquitetura do Sistema

O DevKit é composto por três camadas principais:  

1. **CLI Principal** – executa os módulos forenses.  
2. **Aplicações de apoio** – Dashboard, Visualizadores de Resultados, Wizard.  
3. **Módulos forenses** – organizados por categoria: Browsers, Data, Email, Network.

---

## 3. Módulos Forenses

### 3.1 Browsers
| Módulo | Descrição |
|--------|-----------|
| `browser_history.py` | Coleta histórico de navegação de diferentes browsers. |
| `common_words.py` | Identifica palavras mais comuns em histórico de navegação e downloads. |
| `downloads_history.py` | Lista arquivos baixados pelos usuários. |
| `fav_screen.py` | Captura e organiza screenshots de sites favoritos ou acessados. |
| `full_browser_history` | Consolida todo histórico de navegação em um único relatório. |
| `logins_chrome`, `logins_edge` | Extração de credenciais armazenadas nos browsers. |
| `unusual_patterns` | Identifica padrões suspeitos em histórico de navegação ou downloads. |

### 3.2 Data
| Módulo | Descrição |
|--------|-----------|
| `data_recovery` | Recuperação de arquivos apagados ou parcialmente corrompidos. |

### 3.3 Email
| Módulo | Descrição |
|--------|-----------|
| `email_parser` | Extrai e organiza informações de emails. |
| `header_analysis` | Análise de cabeçalhos para identificar origem, roteamento e possíveis fraudes. |

### 3.4 Network
| Módulo | Descrição |
|--------|-----------|
| `fingerprinting` | Identifica sistemas, serviços e versões em uma rede. |
| `network_map` | Gera mapa visual de hosts e conexões detectadas. |
| `ping_sweep` | Verifica quais hosts estão ativos em uma faixa de IP. |
| `port_scanner` | Identifica portas abertas e serviços ativos em hosts. |

---

## 4. Aplicações de Apoio

### 4.1 Dashboard
**Objetivo:** Centralizar informações e permitir execução rápida de módulos.  
**Funcionalidades:**  
- Menu lateral com módulos do DevKit.  
- Cards com resumo de análises recentes.  
- Acesso direto a visualizadores e Wizard.  
**Tecnologias sugeridas:** Streamlit (web), PyQt (desktop).  

### 4.2 Visualizadores de Resultados
**Objetivo:** Transformar saídas da CLI em gráficos e tabelas interativas.  
**Exemplos:**  
- Mapas de rede interativos.  
- Timeline de eventos e logs.  
- Gráficos de arquivos analisados, tipos e padrões suspeitos.  
**Integração:** Recebe dados da CLI em formato JSON ou CSV.  

### 4.3 Assistente Interativo (Wizard)
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

1. CLI executa módulos e gera resultados.  
2. Dashboard centraliza execução e resume resultados.  
3. Visualizadores transformam dados em gráficos/tabelas interativas.  
4. Wizard guia o usuário e facilita a execução dos módulos.  

---

## 6. Planejamento e Ferramentas em Desenvolvimento

| Aplicação / Módulo | Objetivo | Status / Possíveis Extensões |
|-------------------|----------|-----------------------------|
| **Dashboard** | Painel central para visualização e execução de módulos | Em desenvolvimento. Futuras extensões: filtros avançados, alertas em tempo real, integração direta com relatórios. |
| **Visualizadores de Resultados** | Transformar dados da CLI em gráficos, mapas e tabelas interativas | Em desenvolvimento. Futuras extensões: timeline interativa, heatmaps de rede, gráficos de comportamento de usuários. |
| **Assistente Interativo (Wizard)** | Guiar o usuário em análises passo a passo | Em desenvolvimento. Futuras extensões: templates de análise rápida, integração automática com módulos de email e data, relatórios PDF/HTML automáticos. |
| **Possíveis novos módulos** | Expansão da CLI | - Análise de logs de sistemas (Windows/Linux) <br> - Recuperação de dados de dispositivos móveis <br> - Análise de mídias (imagens, vídeos) <br> - Detecção de malware e scripts maliciosos em arquivos <br> - Integração com APIs de threat intelligence |
| **Ferramentas auxiliares** | Suporte a módulos existentes e novos | - Exportação avançada de relatórios (PDF, HTML, CSV) <br> - Integração com dashboards interativos <br> - Geradores de gráficos customizáveis <br> - Notificações em tempo real de eventos suspeitos |

**Observações:**  
- O conjunto de aplicações complementares mantém a CLI como núcleo, mas oferece interfaces gráficas e interativas que facilitam o aprendizado e a interpretação dos resultados.  
- A previsão de novos módulos e ferramentas auxiliares permite expansão futura do DevKit, tornando-o mais completo para cenários educacionais e de teste forense.

---

## 7. Considerações Finais

O DevKit Forense combina **educação e prática**, permitindo que usuários explorem análise forense digital de forma segura, didática e interativa.  
As aplicações de apoio aumentam a acessibilidade e o engajamento, tornando o estudo da perícia digital mais visual e intuitivo.  
O planejamento de novos módulos e ferramentas garante evolução contínua da plataforma, mantendo-a atualizada e relevante para atividades acadêmicas e laboratoriais.
