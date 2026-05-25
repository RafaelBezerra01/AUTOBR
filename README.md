# AutoBR — CRUD de Veículos com Flask + SQLite

Site estilo WebMotors para anunciar e gerenciar veículos.

## 🚀 Como rodar

### 1. Instale as dependências
```bash
pip install flask
```

### 2. Execute o servidor
```bash
python app.py
```

### 3. Acesse no navegador
```
http://localhost:5000
```

---

## 📁 Estrutura

```
webmotors/
├── app.py                 # Flask app + rotas + SQLite
├── requirements.txt
└── templates/
    ├── base.html          # Layout base (nav, flash, footer)
    ├── index.html         # Listagem com busca e filtros
    ├── detail.html        # Detalhes do veículo
    └── form.html          # Formulário criar/editar
```

## ⚡ Funcionalidades CRUD

| Ação     | Rota                     | Método |
|----------|--------------------------|--------|
| Listar   | `/`                      | GET    |
| Detalhar | `/car/<id>`              | GET    |
| Criar    | `/car/new`               | GET/POST |
| Editar   | `/car/<id>/edit`         | GET/POST |
| Deletar  | `/car/<id>/delete`       | POST   |

## 🔍 Filtros disponíveis
- Busca por texto (marca, modelo, cidade)
- Filtro por marca
- Filtro por combustível
- Filtro por câmbio (automático/manual)
- Faixa de preço (mín/máx)

## 🗄️ Banco de dados
- SQLite local (`cars.db`) — criado automaticamente
- 8 veículos de exemplo inseridos no primeiro run
