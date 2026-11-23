create table if not exists public.perfis (
    django_id bigint primary key,
    username text not null,
    nome text,
    sobrenome text,
    email text,
    tipo_usuario text not null
);

create table if not exists public.categorias (
    django_id bigint primary key,
    nome text not null,
    descricao text,
    ativo boolean not null default true
);

create table if not exists public.livros (
    django_id bigint primary key,
    nome text not null,
    descricao text,
    preco numeric(10,2) not null,
    imagem text,
    autor text,
    isbn text,
    estoque integer not null default 0,
    ativo boolean not null default true,
    categoria_id bigint,
    vendedor_id bigint
);

create table if not exists public.contatos (
    django_id bigint primary key,
    nome text not null,
    email text not null,
    telefone text,
    mensagem text not null
);

create table if not exists public.pedidos (
    django_id bigint primary key,
    usuario_id bigint not null,
    status text not null,
    total numeric(10,2) not null default 0,
    criado_em timestamptz
);

create table if not exists public.itens_pedido (
    django_id bigint primary key,
    pedido_id bigint not null,
    livro_id bigint not null,
    quantidade integer not null,
    preco_unitario numeric(10,2) not null
);

create table if not exists public.carrinhos (
    usuario_id bigint primary key,
    itens jsonb not null default '{}'::jsonb
);

alter table public.livros
    add column if not exists categoria_id bigint,
    add column if not exists vendedor_id bigint;

alter table public.perfis
    add column if not exists foto_url text;
