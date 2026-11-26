# 🌸 Pétala Livraria — Sistema de Gestão & E-commerce Literário

<div align="center">

  <img src="trabalho01/ap/static/images/petala.svg" alt="Pétala Livraria Logo" width="130" />

  <br />

  [![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)
  [![Render](https://img.shields.io/badge/Render-Deploy_Live-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://petala-livraira.onrender.com/)
  [![Tests](https://img.shields.io/badge/Testes-24_Passando-success?style=for-the-badge&logo=pytest&logoColor=white)](#-testes-automatizados)
  [![License](https://img.shields.io/badge/Licen%C3%A7a-MIT-blue?style=for-the-badge)](#-licen%C3%A7a)

  <br />

  **Plataforma web completa para livraria e catálogo literário**, desenvolvida em **Python/Django**, unindo e-commerce moderno, controle de acesso em três níveis (Admin, Vendedor, Cliente), integração resiliente com a **Open Library API**, carrinho de compras dinâmico e armazenamento em nuvem no **Supabase**.

  <br />

  🔗 **Site em Produção:** [**https://petala-livraira.onrender.com/**](https://petala-livraira.onrender.com/)

  <br />

  [Visão Geral](#-sobre-o-projeto) •
  [Funcionalidades](#-funcionalidades-principais) •
  [Demonstração](#-telas-e-destaques-visuais) •
  [Tecnologias](#-tecnologias-utilizadas) •
  [Arquitetura](#-arquitetura-do-sistema) •
  [Modelo de Dados](#-modelo-de-dados) •
  [Como Executar](#-como-executar-localmente) •
  [Deploy](#-deploy--hospedagem)

</div>

---

## 📑 Sumário

- [🌸 Sobre o Projeto](#-sobre-o-projeto)
- [✨ Funcionalidades Principais](#-funcionalidades-principais)
  - [Matriz de Controle de Acesso (RBAC)](#matriz-de-controle-de-acesso-rbac)
  - [Catálogo e Busca Avançada](#catálogo-e-busca-avançada)
  - [Integração Open Library API](#integração-open-library-api-descobrir-livros)
  - [Carrinho de Compras & Checkout](#carrinho-de-compras--checkout)
  - [Design Responsivo & Menu Mobile](#design-responsivo--menu-mobile)
- [🖼️ Telas e Destaques Visuais](#-telas-e-destaques-visuais)
- [🛠️ Tecnologias Utilizadas](#️-tecnologias-utilizadas)
- [🏗️ Arquitetura do Sistema](#️-arquitetura-do-sistema)
- [🗄️ Modelo de Dados](#️-modelo-de-dados)
- [📂 Estrutura de Pastas](#-estrutura-de-pastas)
- [🚀 Como Executar Localmente](#-como-executar-localmente)
  - [Pré-requisitos](#pré-requisitos)
  - [Passo a Passo](#passo-a-passo)
- [🧪 Testes Automatizados](#-testes-automatizados)
- [☁️ Deploy & Hospedagem](#️-deploy--hospedagem)
- [🎨 Identidade Visual](#-identidade-visual)
- [👥 Equipe e Autoria](#-equipe-e-autoria)
- [📄 Licença](#-licença)

---

## 🌸 Sobre o Projeto

A **Pétala Livraria** é uma solução completa desenvolvida para suprir as demandas operacionais e comerciais de livrarias físicas e virtuais. Inspirada na elegância e aconchego das livrarias clássicas aliadas à praticidade da tecnologia web moderna, a aplicação entrega:

- Uma experiência de compra fluida e imersiva para o leitor.
- Um painel administrativo robusto e seguro para lojistas e vendedores.
- Descoberta de títulos mundiais através da API aberta da **Open Library**.
- Resiliência operacional com fallback em cache, tolerância a falhas e sincronização com serviços cloud (*Render, Supabase e AWS*).

O projeto foi construído respeitando os princípios de arquitetura limpa do Django (MVT — Model-View-Template), com separação estrita de responsabilidades, autenticação RBAC, interface adaptativa (*Mobile-First*) e cobertura de testes automatizados.

---

## ✨ Funcionalidades Principais

### Matriz de Controle de Acesso (RBAC)

O sistema possui controle de permissões baseado em papéis (*Role-Based Access Control*), garantindo que cada usuário acerte somente o que lhe compete:

| Funcionalidade / Módulo | 👤 Cliente Visitante | 🛒 Cliente Autenticado | 📦 Vendedor | 👑 Administrador |
| :--- | :---: | :---: | :---: | :---: |
| **Explorar Catálogo e Detalhes** | ✅ | ✅ | ✅ | ✅ |
| **Descobrir Livros (Open Library API)** | ✅ | ✅ | ✅ | ✅ |
| **Filtros e Paginação Avançada** | ✅ | ✅ | ✅ | ✅ |
| **Adicionar à Sacola / Carrinho** | ✅ | ✅ | ✅ | ✅ |
| **Finalizar Compra / Fazer Pedido** | ❌ (exige login) | ✅ | ✅ | ✅ |
| **Consultar Histórico de Pedidos** | ❌ | ✅ | ✅ | ✅ |
| **Cadastrar / Editar Livros e Estoque** | ❌ | ❌ | ✅ | ✅ |
| **Gerenciar Status dos Pedidos** | ❌ | ❌ | ✅ | ✅ |
| **Acesso ao Django Admin** | ❌ | ❌ | ❌ | ✅ |
| **Gestão Geral de Usuários e Perfis** | ❌ | ❌ | ❌ | ✅ |

---

### Catálogo e Busca Avançada
- **Filtro Multi-critério:** Pesquisa por título, autor, categoria e faixa de preço (mínimo e máximo).
- **Ordenação Inteligente:** Menor preço, maior preço, mais recentes e ordem alfabética.
- **Paginação Dinâmica:** Navegação por páginas com persistência de parâmetros de busca na URL (`&q=...&categoria=...&page=...`), sem perda do filtro ao avançar páginas.

### Integração Open Library API (Descobrir Livros)
- **Consulta Global:** Permite aos usuários pesquisar e explorar títulos internacionais em tempo real diretamente da API pública da [Open Library](https://openlibrary.org/).
- **Cache Otimizado:** Armazenamento em cache de 30 minutos em memória do Django, minimizando requisições externas e garantindo resposta sub-segundo.
- **Fallback Resiliente:** Em caso de lentidão, rate limit ou timeout na rede, o sistema exibe automaticamente uma seleção curada de clássicos literários pré-carregados, impedindo telas em branco.
- **Paginação Dupla:** Paginação independente para o catálogo da API e para as obras locais da livraria.

### Carrinho de Compras & Checkout
- **Sessão Persistente:** Sacola gerenciada via sessão HTTP do Django, permitindo adicionar livros sem login prévio.
- **Badge Dinâmico:** Contador no cabeçalho atualizado em tempo real com o número de itens na sacola.
- **Controle de Quantidade:** Incremento, decremento e remoção unitária com recálculo automático de subtotais e frete/total.
- **Conversão em Pedido:** Ao finalizar, o carrinho é convertido em registro `Pedido` e `ItemPedido` no banco de dados, com status inicial `Pendente`.

### Design Responsivo & Menu Mobile
- **Breakpoint de 1100px:** Transição suave da barra de navegação tradicional para um **Menu Hambúrguer Off-Canvas**.
- **Drawer Animado:** Menu lateral deslizante com fundo em *Backdrop Blur* e fechamento via botão, overlay ou tecla `ESC`.
- **Rodapé Corporativo:** Informações institucionais, links rápidos, redes sociais fictícias, métodos de pagamento aceitos e certificação SSL.

---

## 🖼️ Telas e Destaques Visuais

<div align="center">

| Página Inicial / Destaques | Catálogo com Filtros & Paginação |
|:---:|:---:|
| Visual clássico, destaques literários e categorias | Filtro por autor, categoria, preço e ordenação |

| Descobrir Livros (Open Library API) | Sacola de Compras Interativa |
|:---:|:---:|
| Pesquisa mundial de livros com cache resiliente | Atualização em tempo real de itens e valores |

</div>

---

## 🛠️ Tecnologias Utilizadas

A stack do projeto foi selecionada priorizando confiabilidade, escalabilidade e facilidade de manutenção:

### Backend & Aplicação
- **[Python 3.12+](https://www.python.org/)**: Linguagem base pela sua elegância e suporte a tipagem.
- **[Django 6.1](https://www.djangoproject.com/)**: Framework web corporativo de alto desempenho com ORM maduro, CSRF protection, sessions e autenticação nativa.
- **[Gunicorn 21+](https://gunicorn.org/)**: WSGI HTTP Server robusto para ambientes de produção Linux e containers.
- **[WhiteNoise 6+](https://whitenoise.readthedocs.io/)**: Serviço de arquivos estáticos de alta eficiência integrado diretamente na pipeline WSGI.
- **[Requests](https://requests.readthedocs.io/)**: Cliente HTTP para comunicação externa com a Open Library API.

### Banco de Dados & Armazenamento
- **[PostgreSQL (Supabase)](https://supabase.com/)**: Banco de dados relacional principal em nuvem, garantindo integridade ACID.
- **[Supabase Storage](https://supabase.com/storage)**: Bucket de mídia na nuvem para hospedagem das capas e imagens dos livros.
- **[SQLite 3](https://www.sqlite.org/)**: Banco de dados relacional local para desenvolvimento ágil sem necessidade de serviços externos.

### Frontend
- **HTML5 Semântico**: Estrutura acessível e bem indexável.
- **CSS3 Moderno**: Flexbox, CSS Grid, variáveis de tema (paleta floral) e animações suaves.
- **JavaScript Vanilla**: Lógica do menu hambúrguer, modais, validações de formulário e interações de carrinho.

### Infraestrutura & DevOps
- **[Render PaaS](https://render.com/)**: Plataforma de deploy contínuo integrada via Git com script `build.sh`.
- **[AWS Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/)**: Suporte a deploy em infraestrutura gerenciada AWS com bundle pré-configurado.

---

## 🏗️ Arquitetura do Sistema

O diagrama a seguir detalha o fluxo de requisição, autenticação, persistência e integração externa:

```mermaid
flowchart TD
    subgraph Cliente["Navegador do Usuário"]
        UserBrowser["Desktop / Tablet / Mobile"]
    end

    subgraph CDN_Proxy["Servidor Web & Proxy"]
        RenderRouter["Render Router / HTTPS"]
        GunicornWSGI["Gunicorn WSGI Server"]
        WhiteNoise["WhiteNoise (Static Files)"]
    end

    subgraph CoreDjango["Aplicação Django (Pétala Livraria)"]
        Urls["urls.py (Roteador de Rotas)"]
        Middlewares["Middlewares (Auth, Session, CSRF)"]
        Views["views.py (Regras de Negócio)"]
        CacheMem["Django Memory Cache (30 min)"]
        Templates["Templates DTL + Static CSS/JS"]
    end

    subgraph Externo["Serviços Externos & Nuvem"]
        OpenLibrary["Open Library REST API"]
        SupabaseDB[("PostgreSQL Database (Supabase)")]
        SupabaseStorage["Supabase Storage (Capas & Mídia)"]
        LocalSQLite[("SQLite3 (Desenvolvimento)")]
    end

    UserBrowser -->|HTTPS Request| RenderRouter
    RenderRouter --> GunicornWSGI
    GunicornWSGI --> Middlewares
    Middlewares --> WhiteNoise
    Middlewares --> Urls
    Urls --> Views
    
    Views -->|Renderiza| Templates
    Templates -->|Devolve HTML/CSS/JS| UserBrowser
    
    Views -->|Consulta Títulos| CacheMem
    CacheMem -.->|Miss / Expiração| OpenLibrary
    
    Views -->|ORM Django| SupabaseDB
    Views -.->|Ambiente Local| LocalSQLite
    Templates -->|Carrega Imagens| SupabaseStorage
```

---

## 🗄️ Modelo de Dados

Abaixo está o modelo entidade-relacionamento estruturado no ORM do Django:

```mermaid
erDiagram
    AUTH_USER ||--|| PERFIL : "possui (1:1)"
    AUTH_USER ||--o{ PEDIDO : "realiza (1:N)"
    CATEGORIA ||--o{ SERVICO : "contem (1:N)"
    PEDIDO ||--|{ ITEM_PEDIDO : "inclui (1:N)"
    SERVICO ||--o{ ITEM_PEDIDO : "compoe (1:N)"

    AUTH_USER {
        int id PK
        string username
        string email
        string first_name
        string last_name
        boolean is_staff
        boolean is_active
    }

    PERFIL {
        int id PK
        int user_id FK
        string tipo_usuario "CLIENTE | VENDEDOR | ADMIN"
        string telefone
        string endereco
        string foto
    }

    CATEGORIA {
        int id PK
        string nome
        string slug
        string descricao
        boolean ativo
    }

    SERVICO {
        int id PK
        string titulo
        string autor
        int categoria_id FK
        string isbn
        decimal preco
        int estoque
        text descricao
        string imagem
        boolean ativo
    }

    PEDIDO {
        int id PK
        int cliente_id FK
        string status "PENDENTE | PAGO | CANCELADO"
        decimal total
        datetime criado_em
        datetime atualizado_em
    }

    ITEM_PEDIDO {
        int id PK
        int pedido_id FK
        int servico_id FK
        int quantidade
        decimal preco_unitario
    }

    CONTATO {
        int id PK
        string nome
        string email
        string assunto
        text mensagem
        boolean respondido
        datetime data_envio
    }
```

---

## 📂 Estrutura de Pastas

```text
Petala-Livraira/
│
├── .gitignore
├── .gitattributes
├── README.md                          # Documentação do projeto
│
└── trabalho01/                        # Diretório raiz do projeto Django
    ├── manage.py                      # Utilitário CLI do Django
    ├── requirements.txt               # Dependências do projeto
    ├── runtime.txt                    # Versão do Python para o Render (3.12.7)
    ├── build.sh                       # Script de build para deploy no Render
    ├── Procfile                       # Declaração do processo web Gunicorn
    │
    ├── ap/                            # Aplicação principal (Pétala Livraria)
    │   ├── admin.py                   # Customização do Django Admin
    │   ├── apps.py                    # Configuração da app
    │   ├── forms.py                   # Formulários de autenticação, contato e catálogo
    │   ├── models.py                  # Modelos relacionais (Servico, Categoria, Pedido...)
    │   ├── views.py                   # Views, filtros, paginação, carrinho e Open Library
    │   ├── urls.py                    # Rotas da aplicação
    │   ├── tests.py                   # Testes automatizados (24 testes unitários)
    │   │
    │   ├── fixtures/                  # Carga de dados iniciais para produção
    │   │   └── dados_iniciais.json    # Categorias e livros com imagens sincronizadas
    │   │
    │   ├── static/                    # Arquivos estáticos
    │   │   ├── css/
    │   │   │   └── style.css          # Estilos globais, tema floral, drawer mobile e footer
    │   │   ├── js/
    │   │   │   └── main.js            # Interatividades, menu hambúrguer e carrinho
    │   │   └── images/                # Logotipos, ícones e assets visuais
    │   │
    │   └── templates/                 # Templates HTML (Django Template Language)
    │       ├── base.html              # Layout base (header, drawer mobile, footer)
    │       ├── index.html             # Página inicial com vitrine e destaques
    │       ├── servicos.html          # Catálogo completo com filtros e paginação
    │       ├── produtos.html          # Descobrir Livros (Open Library API + Catálogo)
    │       ├── carrinho.html          # Sacola de compras e resumo de pedido
    │       ├── sobre.html             # Página institucional "Sobre Nós"
    │       ├── contato.html           # Formulário de contato e suporte
    │       ├── login.html             # Formulário de login
    │       ├── cadastro.html          # Registro de novo usuário
    │       └── painel/                # Telas restritas a Vendedores e Administradores
    │
    └── trabalho01/                    # Configurações do projeto Django
        ├── asgi.py
        ├── wsgi.py                    # Ponto de entrada WSGI para Gunicorn
        ├── settings.py                # Configurações gerais (DB, WhiteNoise, Cache, Auth)
        └── urls.py                    # Roteador raiz
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- **[Python 3.12+](https://www.python.org/downloads/)** instalado.
- **[Git](https://git-scm.com/)** instalado.

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/niludev02/Petala-Livraira.git
   cd Petala-Livraira/trabalho01
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   # No Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # No Linux ou macOS:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as Variáveis de Ambiente (opcional para SQLite local):**
   Crie um arquivo `.env` dentro da pasta `trabalho01/` caso deseje conectar a um banco PostgreSQL:
   ```env
   SECRET_KEY=sua-chave-secreta-de-desenvolvimento
   DEBUG=True
   # DATABASE_URL=postgresql://usuario:senha@host:5432/nome_banco
   ```
   > *Nota: Por padrão, sem `DATABASE_URL`, o Django utiliza automaticamente o banco local SQLite3.*

5. **Execute as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

6. **Carregue os dados iniciais do catálogo:**
   ```bash
   python manage.py loaddata ap/fixtures/dados_iniciais.json
   ```

7. **Crie um superusuário (administrador):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

9. **Acesse no seu navegador:**
   - Loja Virtual: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - Painel Administrativo: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Testes Automatizados

A aplicação conta com uma suíte de **24 testes unitários automatizados** cobrindo todas as regras de negócio críticas:
- Criação e validação de modelos (`Categoria`, `Servico`, `Perfil`, `Pedido`).
- Regras de controle de acesso (permissões de Cliente vs. Vendedor vs. Admin).
- Operações da sacola de compras (adicionar, alterar quantidade, remover, limpar).
- Algoritmo de filtragem e paginação do catálogo de livros.
- Resiliência da view de integração com a Open Library API e mecânica de fallback.

Para rodar toda a suíte de testes:

```bash
cd trabalho01
python manage.py test ap
```

Resultado esperado:
```text
Found 24 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........................
----------------------------------------------------------------------
Ran 24 tests in 3.421s

OK
Destroying test database for alias 'default'...
```

---

## ☁️ Deploy & Hospedagem

### Render (Produção Atual)
O projeto está publicado em: **[https://petala-livraira.onrender.com/](https://petala-livraira.onrender.com/)**

A pipeline do Render executa automaticamente a cada push na branch `main`:
1. `build.sh`:
   - Instalação dos pacotes via `pip install -r requirements.txt`.
   - Coleta de arquivos estáticos via `python manage.py collectstatic --no-input`.
   - Execução de migrações via `python manage.py migrate`.
   - Carga idempotente de dados iniciais via `python manage.py loaddata ap/fixtures/dados_iniciais.json`.
2. `Procfile`:
   - Inicialização do servidor de produção: `web: gunicorn trabalho01.wsgi:application --bind 0.0.0.0:$PORT`.

### Armazenamento de Capas no Supabase Storage
Para assegurar persistência permanente em servidores de hospedagem efêmeros (como instâncias grátis de PaaS), as imagens de catálogo são servidas pelo bucket de armazenamento em nuvem do **Supabase Storage**, com URLs públicas acessíveis globalmente.

---

## 🎨 Identidade Visual

O design da **Pétala Livraria** adota uma paleta calorosa e sofisticada inspirada em flores e papel envelhecido:

| Elemento | Amostra | Código Hex | Aplicação |
| :--- | :---: | :---: | :--- |
| **Pétala Suave** | `■` | `#f7cad0` | Detalhes, badges e realces secundários |
| **Rosa Botão** | `■` | `#de6b48` | Chamadas de ação (CTA) e destaques |
| **Bordô Clássico** | `■` | `#7a1f3d` | Títulos principais, botões primários e cabeçalho |
| **Creme Papel** | `■` | `#faf8f5` | Fundo principal da aplicação |
| **Texto Tinta** | `■` | `#2d2426` | Tipografia de alta legibilidade |

---

## 👥 Equipe e Autoria

Projeto concebido e desenvolvido com dedicação como trabalho acadêmico e portfólio profissional:

- **Desenvolvedor:** Carolina / Equipe Pétala Livraria
- **GitHub:** [@niludev02](https://github.com/niludev02)
- **Live Demo:** [petala-livraira.onrender.com](https://petala-livraira.onrender.com/)

---

## 📄 Licença

Este projeto é distribuído sob os termos da licença **MIT**. Consulte o arquivo de licença para mais detalhes.

<div align="center">
  <sub>Feito com ☕, 📖 e amor pela literatura. © 2026 Pétala Livraria.</sub>
</div>
