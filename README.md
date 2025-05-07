# 🔍 DevKit Forense - Módulo de Navegadores

Este projeto é parte de uma Iniciação Científica focada no desenvolvimento de um **toolkit modular para análise de evidências digitais**, com o objetivo de automatizar a extração e análise de artefatos forenses em ambientes simulados.

## 📦 Módulo Atual: Navegadores Web

O módulo de navegadores realiza a coleta, análise e visualização de dados provenientes dos principais navegadores (Google Chrome, Microsoft Edge e Mozilla Firefox), utilizando bancos locais SQLite e arquivos de cache.

### Funcionalidades Implementadas

#### 🧭 Histórico Completo de Navegação
- Extração detalhada do histórico completo dos sites acessados.
- Exportação dos dados em formato `.json`.

#### 📌 Últimos Acessos e Sites Mais Visitados
- Lista dos últimos sites acessados.
- Geração do top 5 dos domínios mais visitados.
- Permite detectar padrões de comportamento digital do usuário.

#### 📥 Histórico de Downloads
- Recuperação de arquivos baixados com nome, URL, caminho local e timestamp.
- Suporte para análise de múltiplos perfis de navegador.

#### 🌐 Favicons e Capturas de Tela dos Sites
- Download automático dos **favicons** dos domínios acessados.
- Geração de **capturas de tela (screenshots)** dos sites visitados recentemente (via headless browser).

#### ⚠️ Detecção de Padrões Incomuns
- Geração de gráficos de **acessos por hora** e **por período do dia (madrugada, manhã, tarde, noite)**.
- Detecção de:
  - Acessos fora do horário habitual (ex.: madrugada).
  - Acessos repetidos em curtos intervalos (potencial automação).
- Gráficos salvos automaticamente em `.png`.

#### 🔐 Extração de Logins e Senhas (Chrome e Edge)
- Extração de credenciais armazenadas localmente.
- Visualização dos sites com dados de login salvos.
> ⚠️ As senhas ainda não são descriptografadas por questões de segurança e autenticação local do sistema operacional.

## 📁 Estrutura Esperada

Os dados extraídos são organizados e salvos na pasta `artefatos/`, separados por categoria (`historico`, `downloads`, `cookies`, etc.).

## 🧰 Tecnologias Utilizadas

- `Python 3.10+`
- `SQLite3`
- `Pandas`
- `Matplotlib`
- `Requests`, `BeautifulSoup`
- `Playwright` (para screenshots)
- `os`, `json`, `datetime`, `cryptography` (em desenvolvimento)

## 🚧 Em Desenvolvimento

- Decriptação segura de senhas (com suporte à autenticação do Windows).
- Extração e análise de **cookies de sessão**.
- Módulo de **linha do tempo forense**.
- Módulo de **formulários autocompletos (autofill)**.
- Módulo para análise forense de redes.

## 📌 Objetivo da Iniciação Científica

Desenvolver um ambiente modular que sirva de base para simulações de investigações forenses, com foco em automação e acessibilidade para pesquisadores e estudantes da área de Segurança e Computação Forense.

## 🤝 Contribuição

Contribuições, sugestões ou colaborações são bem-vindas! Entre em contato ou abra uma issue neste repositório.

## 📜 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

Este projeto está licenciado sob a [GPL-3.0 License](LICENSE-GPL).
