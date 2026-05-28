from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, abort
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
import os

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = 'webmotors_secret'
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, 'cars.db')

UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Função para validar extensões de arquivos
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para obter conexão com o banco de dados
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Função para criar bancos de dados
def init_db():
    conn = get_db()
    # Tabela de usuarios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    # Tabela de Carros
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, 
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
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Seed inicial de dados para testes
    count = conn.execute('SELECT COUNT(*) FROM cars').fetchone()[0]
    if count == 0:
        seeds = [
            (1, 'Toyota', 'Corolla Cross', 2023, 149900, 12000, 'Híbrido', 'Automático', 'Branco Pérola', 'SUV compacto em excelente estado, único dono, revisões em dia.', 'São Paulo', 'SP', 'Carlos Lima', '(11) 99876-5432'),
            (1,'Honda', 'Civic', 2022, 129900, 28000, 'Flex', 'Automático', 'Cinza Grafite', 'Sedan esportivo com pacote de acessórios completo.', 'Rio de Janeiro', 'RJ', 'Ana Souza', '(21) 98765-4321'),
            (1,'Volkswagen', 'T-Cross', 2023, 139800, 5000, 'Flex', 'Automático', 'Vermelho Tornado', 'SUV compacto zero km de estoque.', 'Belo Horizonte', 'MG', 'Pedro Martins', '(31) 97654-3210'),
            (1,'Chevrolet', 'Tracker', 2022, 122500, 35000, 'Turbo Flex', 'Automático', 'Azul Nitro', 'Premier com teto solar e couro.', 'Curitiba', 'PR', 'Mariana Costa', '(41) 96543-2109'),
            (1,'Jeep', 'Compass', 2023, 189900, 8000, 'Diesel', 'Automático', 'Preto Brilliant', 'Limited com pacote Night Eagle.', 'Brasília', 'DF', 'Roberto Alves', '(61) 95432-1098'),
            (1,'Hyundai', 'HB20', 2022, 72900, 42000, 'Flex', 'Manual', 'Prata', 'Hatch econômico com direção elétrica.', 'Salvador', 'BA', 'Fernanda Reis', '(71) 94321-0987'),
            (1,'Fiat', 'Pulse', 2023, 98500, 15000, 'Turbo Flex', 'Automático', 'Verde Botânico', 'Impetus com todos os opcionais.', 'Fortaleza', 'CE', 'Lucas Ferreira', '(85) 93210-9876'),
            (1,'Renault', 'Duster', 2022, 109900, 22000, 'Flex', 'Manual', 'Laranja Atacama', '4x4 ideal para aventuras off-road.', 'Porto Alegre', 'RS', 'Juliana Nunes', '(51) 92109-8765'),
        ]
        conn.executemany('''INSERT INTO cars (user_id, brand, model, year, price, mileage, fuel, transmission, color, description, city, state, seller_name, seller_phone)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', seeds)
        # Criação de um usuário admin padrão
        admin_exists = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
        if not admin_exists:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        ('admin', '123', 'admin'))
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        ('user', '123', 'user'))
        conn.commit()
    conn.close()

from werkzeug.security import generate_password_hash, check_password_hash

# Rota para registro de novos usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Hash da senha para segurança
        
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, password, 'user'))
            conn.commit()
            flash('Conta criada com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Este nome de usuário já existe.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user['password'] == password:
            session.clear() 
            session['user_id'] = user['id']   
            session['username'] = user['username'] 
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
            
    return render_template('login.html')
# Rota para logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'success')
    return redirect(url_for('index'))

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
        
        # Lógica para imagens
        files = request.files.getlist('images')
        saved_filenames = []

        for file in files[:6]: # Limite de 6 fotos
            if file and allowed_file(file.filename):
                # Gera um nome único para a imagem
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"{os.urandom(8).hex()}.{ext}"
                
                # Salva fisicamente na pasta static/uploads
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                saved_filenames.append(unique_name)
        
        # Transforma a lista de nomes em uma string (ex: "foto1.jpg,foto2.jpg")
        images_str = ",".join(saved_filenames)

        # Pega o ID do usuário logado para associar o anúncio a ele
        user_id = session.get('user_id') # Pega o ID do usuário logado
        
        
        conn = get_db()
        
        conn.execute('''
            INSERT INTO cars (
                user_id, brand, model, year, price, mileage, fuel, transmission, 
                color, description, city, state, seller_name, seller_phone, images
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, data['brand'], data['model'], int(data['year']), float(data['price']),
             int(data['mileage']), data['fuel'], data['transmission'], data['color'],
             data['description'], data['city'], data['state'], data['seller_name'], 
             data['seller_phone'], images_str)) # <-- Agora salvando a string das fotos
        
        conn.commit()
        conn.close()
        flash('Anúncio publicado com sucesso!', 'success')
        return redirect(url_for('index'))
    
    return render_template('form.html', action='new')

# Edição de anúncios com validação de dados numéricos e mensagens de erro para o usuário
@app.route('/car/<int:car_id>/edit', methods=['GET', 'POST'])
@login_required
def car_edit(car_id):
    conn = get_db()
    car = conn.execute('SELECT * FROM cars WHERE id = ?', (car_id,)).fetchone()
    
    # VERIFICAÇÃO DE SEGURANÇA
    is_admin = session.get('role') == 'admin'
    is_owner = car['user_id'] == session.get('user_id')

    if not (is_admin or is_owner):
        conn.close()
        flash('Acesso negado. Você não é o dono deste anúncio nem administrador.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = request.form
        
        # logica das imagens
        files = request.files.getlist('images')
        new_filenames = []
        
        for file in files[:6]:
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"{os.urandom(8).hex()}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                new_filenames.append(unique_name)
        
        # Se o usuário subiu novas fotos, usamos as novas. 
        # Se não subiu nada, mantemos as fotos antigas que já estavam no banco.
        if new_filenames:
            images_to_save = ",".join(new_filenames)
        else:
            images_to_save = car['images']

        conn.execute('''UPDATE cars SET 
                        brand=?, model=?, year=?, price=?, mileage=?, fuel=?, 
                        transmission=?, color=?, description=?, city=?, state=?, 
                        seller_name=?, seller_phone=?, images=? 
                        WHERE id=?''',
                     (data['brand'], data['model'], int(data['year']), float(data['price']),
                      int(data['mileage']), data['fuel'], data['transmission'], data['color'],
                      data['description'], data['city'], data['state'], data['seller_name'], 
                      data['seller_phone'], images_to_save, car_id))
        conn.commit()
        conn.close()
        flash('Anúncio atualizado com sucesso!', 'success')
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
