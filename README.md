# Citizen Assist AI

O **Citizen Assist AI** é um aplicativo web que desenvolvemos para facilitar o acesso a orientações sobre segurança digital, direitos do consumidor e serviços públicos digitais.

Começamos o projeto em Python, com um assistente executado pelo terminal. Depois, na disciplina de Data Structures and Algorithms (DSA), implementamos nossa própria lista encadeada e as operações de gerenciamento das orientações. Nesta versão, reunimos tudo em uma interface web com login, pesquisa, histórico e uma área administrativa.

## Integrantes

- **Leonardo Duarte** — RM 569029
- **Enzo de Nadai** — RM 569985
- **Eduardo Oliveira**

## O que o aplicativo faz

### Para o usuário

- **Login e cadastro:** cada pessoa pode criar sua conta e acessar o aplicativo.
- **Busca inteligente:** a pessoa escreve sua dúvida e o sistema procura as orientações mais relacionadas, utilizando palavras-chave e pontuação.
- **Categorias:** as orientações podem ser exploradas por assunto.
- **Detalhes das orientações:** apresentamos a resposta, documentos necessários, canal de atendimento, fonte e data de verificação.
- **Verificador de links:** consulta o Google Safe Browsing para identificar ameaças conhecidas em URLs.
- **Histórico individual:** registra pesquisas e orientações visualizadas, vinculadas à conta do usuário.
- **Avaliação das respostas:** a pessoa pode informar se uma orientação ajudou.
- **Indicadores:** apresenta dados das pesquisas e avaliações do próprio usuário.

### Para o administrador

Criamos uma área separada, acessível apenas para contas com perfil **admin**. Nela, podemos:

- Cadastrar orientações;
- Consultar e listar os registros;
- Atualizar seus dados;
- Excluir orientações;
- Organizar as orientações por título, utilizando **Bubble Sort**.

Os usuários comuns não têm acesso às operações administrativas.

## Tecnologias utilizadas

| Tecnologia | Utilização |
| --- | --- |
| Python | Lógica do sistema, busca e estruturas de dados |
| Flask | Rotas e integração entre o Python e as páginas web |
| HTML e CSS | Páginas e interface responsiva |
| JavaScript e Lucide Icons | Elementos da interface e ícones vetoriais |
| SQLite | Contas de usuários, perfis, histórico e avaliações |
| JSON | Base de conhecimento com as orientações |
| Google Safe Browsing | Consulta de ameaças conhecidas em URLs |

As senhas são armazenadas como **hash**, utilizando as funções de segurança do Werkzeug, e as sessões são usadas para identificar o usuário autenticado.

## Estrutura do projeto

```text
APP-FINAL/
├── app.py                       # Aplicação web Flask
├── main.py                      # Versão anterior do menu em terminal
├── assistente.py                # Funcionalidades do assistente original
├── orientacao.py                # Classe dos registros
├── base_conhecimento.py         # Leitura do JSON e busca por pontuação
├── no.py                        # Nó da lista encadeada
├── lista_encadeada.py           # CRUD, busca e Bubble Sort
├── validador_url.py             # Funções do verificador original
├── validador_web.py             # Consulta adaptada para a interface web
├── requirements.txt             # Dependências Python
├── templates/                   # Páginas HTML/Jinja2
├── static/
│   └── css/
│       └── estilo.css           # Estilos da interface
├── data/
│   └── base_conhecimento.json   # Orientações utilizadas pelo sistema
└── instance/                    # Banco SQLite e chave local (não publicar)
```

A pasta `instance/` é criada automaticamente na primeira execução do aplicativo.

## Como executar

**1.** Clone o repositório:

```bash
git clone https://github.com/LeonardoDuarte08/GLOBAL-SOLUTION-02---Citizen-Assist-AI---APP-FINAL.git
```

**2.** Entre na pasta do projeto:

```bash
cd GLOBAL-SOLUTION-02---Citizen-Assist-AI---APP-FINAL
```

**3.** Instale as dependências:

```bash
py -m pip install -r requirements.txt
```

**4.** Inicie o aplicativo:

```bash
py app.py
```

**5.** Abra no navegador:

**http://127.0.0.1:3001**

Em ambientes que utilizam `python` em vez de `py`, substitua o comando conforme a instalação local.

Ao entrar pela primeira vez, utilize a opção **Criar conta**. Depois, faça login para acessar a tela inicial.

### Configuração do verificador de URLs

Para utilizar o Google Safe Browsing, configure uma chave de API na variável de ambiente `GOOGLE_SAFE_BROWSING_KEY` ou em um arquivo `.env` local com este conteúdo:

```env
GOOGLE_SAFE_BROWSING_KEY=SUA_CHAVE_AQUI
```

O `validador_url.py` realiza a leitura dessa chave. O arquivo `.env` não deve ser enviado ao GitHub. Se a API não estiver configurada ou não responder, o aplicativo informa que a consulta não pôde ser concluída.

### Acesso administrativo

Novas contas são criadas com o perfil `usuario`. Para habilitar uma conta de administrador no ambiente local, podemos atualizar seu perfil no banco SQLite, com o Flask parado:

```powershell
py -c "import sqlite3; c=sqlite3.connect('instance/usuarios.db'); c.execute('UPDATE usuarios SET perfil=? WHERE email=?', ('admin', 'email@exemplo.com')); c.commit(); c.close()"
```

Substitua `email@exemplo.com` pelo e-mail cadastrado e entre novamente no aplicativo. A área **Admin** ficará disponível para essa conta.

## Como funciona a busca

Mantivemos a busca por regras desenvolvida na primeira versão do Citizen Assist AI:

1. Normalizamos os textos, retirando diferenças de maiúsculas, acentos e pontuação;
2. Comparamos a pergunta com as palavras-chave de cada orientação;
3. Somamos **3 pontos** para cada palavra-chave correspondente e **1 ponto** para palavras relevantes presentes no título;
4. Exibimos as orientações com pelo menos **3 pontos**, priorizando as mais relacionadas.

A ordenação das respostas por pontuação também foi implementada no código, sem depender de `sort()` ou `sorted()`.

## Estruturas de dados e algoritmos — DSA

Na disciplina de DSA, substituímos a lista principal de orientações por uma **lista simplesmente encadeada**, implementada por nós.

- A classe `No` guarda uma orientação e a referência para o próximo nó.
- A classe `ListaEncadeada` realiza inserção, busca, percurso, atualização, exclusão e pesquisa por título.
- No **Bubble Sort**, comparamos registros vizinhos e trocamos as orientações armazenadas nos nós para colocá-las em ordem alfabética.

### Complexidade dos algoritmos

Considerando `n` como a quantidade de orientações na lista:

| Operação | Complexidade no pior caso | Motivo |
| --- | --- | --- |
| Inserção | **O(n)** | Verificamos se o ID já existe e percorremos a lista para inserir ao final. |
| Busca por ID | **O(n)** | Podemos precisar visitar todos os nós. |
| Listagem | **O(n)** | Percorremos toda a lista. |
| Atualização | **O(n)** | Primeiro localizamos o registro. |
| Exclusão | **O(n)** | Percorremos os nós até encontrar o registro. |
| Pesquisa por título | **O(n)** | Comparamos o título de cada orientação. |
| Ordenação Bubble Sort | **O(n²)** | Realizamos comparações em passagens sucessivas pela lista. |

Essa análise considera o tamanho dos textos limitado, observando as operações da lista encadeada que implementamos.

## Histórico e indicadores

No aplicativo web, utilizamos o SQLite para vincular as consultas ao usuário autenticado. Registramos as buscas realizadas, as orientações acessadas e as avaliações enviadas.

Com essas informações, mostramos indicadores como:

- Total de pesquisas realizadas;
- Percentual de pesquisas que encontraram orientações;
- Quantidade de orientações visualizadas;
- Total de avaliações e percentual de respostas consideradas úteis.

Cada usuário acessa apenas seu próprio histórico e seus próprios indicadores.

## Testes realizados

Durante o desenvolvimento, testamos o funcionamento das funcionalidades principais:

| Teste | O que verificamos |
| --- | --- |
| Cadastro e login | Criação de conta e acesso com credenciais válidas |
| Permissões | Separação entre acesso de usuário e de administrador |
| Busca e categorias | Localização e exibição de orientações |
| CRUD | Cadastro, consulta, alteração e exclusão de registros |
| Lista encadeada | Inserção, busca, remoção e tratamento de IDs duplicados |
| Bubble Sort | Ordenação alfabética das orientações |
| Verificador de links | Integração da consulta com a interface web |
| Interface | Exibição das páginas, navegação e ícones Lucide |
| Histórico e indicadores | Registro e consulta dos dados associados ao usuário |

## Organização e continuidade

Mantivemos os repositórios anteriores para registrar a evolução do projeto:

- [Citizen Assist AI — Python](https://github.com/LeonardoDuarte08/GLOBAL-SOLUTION-02---Citizen-Assist-AI)
- [Citizen Assist AI — DSA](https://github.com/LeonardoDuarte08/GLOBAL-SOLUTION-02---Citizen-Assist-AI---DSA)
- [Citizen Assist AI — APP FINAL](https://github.com/LeonardoDuarte08/GLOBAL-SOLUTION-02---Citizen-Assist-AI---APP-FINAL)

Nesta versão, reunimos os recursos que desenvolvemos nas etapas anteriores e criamos uma experiência mais simples para quem utiliza o aplicativo, mantendo as funcionalidades técnicas de gerenciamento em uma área separada.
