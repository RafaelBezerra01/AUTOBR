from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'webmotors_secret'
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, 'cars.db')

# Função para obter conexão com o banco de dados
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Função para inicializar o banco de dados e criar a tabela de carros
def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price REAL NOT NULL,
            mileage INTEGER NOT NULL,
            fuel TEXT NOT NULL,
            transmission TEXT NOT NULL,
            color TEXT NOT NULL,
            description TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            seller_name TEXT NOT NULL,
            seller_phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Seed inicial de dados para testes
    count = conn.execute('SELECT COUNT(*) FROM cars').fetchone()[0]
    if count == 0:
        seeds = [
            ('Toyota', 'Corolla Cross', 2023, 149900, 12000, 'Híbrido', 'Automático', 'Branco Pérola', 'SUV compacto em excelente estado, único dono, revisões em dia.', 'São Paulo', 'SP', 'Carlos Lima', '(11) 99876-5432'),
            ('Honda', 'Civic', 2022, 129900, 28000, 'Flex', 'Automático', 'Cinza Grafite', 'Sedan esportivo com pacote de acessórios completo.', 'Rio de Janeiro', 'RJ', 'Ana Souza', '(21) 98765-4321'),
            ('Volkswagen', 'T-Cross', 2023, 139800, 5000, 'Flex', 'Automático', 'Vermelho Tornado', 'SUV compacto zero km de estoque.', 'Belo Horizonte', 'MG', 'Pedro Martins', '(31) 97654-3210'),
            ('Chevrolet', 'Tracker', 2022, 122500, 35000, 'Turbo Flex', 'Automático', 'Azul Nitro', 'Premier com teto solar e couro.', 'Curitiba', 'PR', 'Mariana Costa', '(41) 96543-2109'),
            ('Jeep', 'Compass', 2023, 189900, 8000, 'Diesel', 'Automático', 'Preto Brilliant', 'Limited com pacote Night Eagle.', 'Brasília', 'DF', 'Roberto Alves', '(61) 95432-1098'),
            ('Hyundai', 'HB20', 2022, 72900, 42000, 'Flex', 'Manual', 'Prata', 'Hatch econômico com direção elétrica.', 'Salvador', 'BA', 'Fernanda Reis', '(71) 94321-0987'),
            ('Fiat', 'Pulse', 2023, 98500, 15000, 'Turbo Flex', 'Automático', 'Verde Botânico', 'Impetus com todos os opcionais.', 'Fortaleza', 'CE', 'Lucas Ferreira', '(85) 93210-9876'),
            ('Renault', 'Duster', 2022, 109900, 22000, 'Flex', 'Manual', 'Laranja Atacama', '4x4 ideal para aventuras off-road.', 'Porto Alegre', 'RS', 'Juliana Nunes', '(51) 92109-8765'),
        ]
        conn.executemany('''INSERT INTO cars (brand, model, year, price, mileage, fuel, transmission, color, description, city, state, seller_name, seller_phone)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', seeds)
        conn.commit()
    conn.close()

# Página inicial com busca e filtros
@app.route('/')
def index():
    conn = get_db()
    search = request.args.get('search', '')
    brand = request.args.get('brand', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    fuel = request.args.get('fuel', '')
    transmission = request.args.get('transmission', '')

    query = 'SELECT * FROM cars WHERE 1=1'
    params = []
    if search:
        query += ' AND (brand LIKE ? OR model LIKE ? OR city LIKE ?)'
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if brand:
        query += ' AND brand = ?'
        params.append(brand)
    if min_price:
        query += ' AND price >= ?'
        params.append(float(min_price))
    if max_price:
        query += ' AND price <= ?'
        params.append(float(max_price))
    if fuel:
        query += ' AND fuel = ?'
        params.append(fuel)
    if transmission:
        query += ' AND transmission = ?'
        params.append(transmission)

    query += ' ORDER BY created_at DESC'
    cars = conn.execute(query, params).fetchall()
    brands = [r[0] for r in conn.execute('SELECT DISTINCT brand FROM cars ORDER BY brand').fetchall()]
    conn.close()
    return render_template('index.html', cars=cars, brands=brands,
                           search=search, brand=brand, min_price=min_price,
                           max_price=max_price, fuel=fuel, transmission=transmission)

# Página de detalhes do veículo
@app.route('/car/<int:car_id>')
def car_detail(car_id):
    conn = get_db()
    car = conn.execute('SELECT * FROM cars WHERE id = ?', (car_id,)).fetchone()
    conn.close()
    if not car:
        flash('Veículo não encontrado.', 'error')
        return redirect(url_for('index'))
    return render_template('detail.html', car=car)

#criação de anúncios com validação de dados numéricos e mensagens de erro para o usuário
@app.route('/car/new', methods=['GET', 'POST'])
def car_new():
    if request.method == 'POST':
        data = request.form
        
        # Validação de dados numéricos
        try:
            year = int(data['year'])
            price = float(data['price'])
            mileage = int(data['mileage'])
        except ValueError:
            flash('Erro: Os campos Ano, Preço e Quilometragem devem conter apenas números.', 'error')
            # Retorna o formulário com os dados preenchidos para o usuário corrigir
            return render_template('form.html', car=data, action='new')

        # Se passou na validação, insere no banco
        conn = get_db()
        conn.execute('''INSERT INTO cars (brand, model, year, price, mileage, fuel, transmission, color, description, city, state, seller_name, seller_phone)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                     (data['brand'], data['model'], year, price,
                      mileage, data['fuel'], data['transmission'], data['color'],
                      data['description'], data['city'], data['state'], data['seller_name'], data['seller_phone']))
        conn.commit()
        conn.close()
        flash('Veículo anunciado com sucesso!', 'success')
        return redirect(url_for('index'))
        
    return render_template('form.html', car=None, action='new')

# Edição de anúncios com validação de dados numéricos e mensagens de erro para o usuário
@app.route('/car/<int:car_id>/edit', methods=['GET', 'POST'])
def car_edit(car_id):
    conn = get_db()
    car = conn.execute('SELECT * FROM cars WHERE id = ?', (car_id,)).fetchone()
    if not car:
        conn.close()
        flash('Veículo não encontrado.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        data = request.form
        conn.execute('''UPDATE cars SET brand=?, model=?, year=?, price=?, mileage=?, fuel=?, transmission=?, color=?, description=?, city=?, state=?, seller_name=?, seller_phone=?
                        WHERE id=?''',
                     (data['brand'], data['model'], int(data['year']), float(data['price']),
                      int(data['mileage']), data['fuel'], data['transmission'], data['color'],
                      data['description'], data['city'], data['state'], data['seller_name'], data['seller_phone'], car_id))
        conn.commit()
        conn.close()
        flash('Veículo atualizado com sucesso!', 'success')
        return redirect(url_for('car_detail', car_id=car_id))
    conn.close()
    return render_template('form.html', car=car, action='edit')

# Exclusão de anúncios
@app.route('/car/<int:car_id>/delete', methods=['POST'])
def car_delete(car_id):
    conn = get_db()
    conn.execute('DELETE FROM cars WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()
    flash('Veículo removido com sucesso.', 'success')
    return redirect(url_for('index'))

# Endpoint para estatísticas básicas da plataforma
@app.route('/api/stats')
def stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM cars').fetchone()[0]
    avg_price = conn.execute('SELECT AVG(price) FROM cars').fetchone()[0] or 0
    conn.close()
    return jsonify({'total': total, 'avg_price': round(avg_price, 2)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
