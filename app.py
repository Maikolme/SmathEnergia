from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from models import db, User, Reading, Recommendation
from datetime import datetime, date
from sqlalchemy import func, extract
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///energiasmart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def calculate_consumption(readings):
    if len(readings) < 2:
        return []
    sorted_readings = sorted(readings, key=lambda r: r.reading_date)
    consumption = []
    for i in range(1, len(sorted_readings)):
        diff = sorted_readings[i].meter_reading - sorted_readings[i - 1].meter_reading
        days = (sorted_readings[i].reading_date - sorted_readings[i - 1].reading_date).days
        if days > 0 and diff >= 0:
            consumption.append({
                'date': sorted_readings[i].reading_date.isoformat(),
                'kwh': round(diff, 2),
                'days': days,
                'daily_avg': round(diff / days, 2)
            })
    return consumption


def generate_recommendations(user, consumption_data):
    recs = []
    if not consumption_data:
        return recs

    avg_monthly = sum(c['kwh'] for c in consumption_data) / len(consumption_data)
    avg_daily = sum(c['daily_avg'] for c in consumption_data) / len(consumption_data)

    if avg_monthly > user.monthly_goal_kwh:
        over = round(avg_monthly - user.monthly_goal_kwh, 2)
        recs.append({
            'title': 'Meta de ahorro superada',
            'description': f'Superas tu meta mensual en {over} kWh. Intenta reducir el consumo diario en {round(over / 30, 2)} kWh.',
            'category': 'meta',
            'priority': 'high'
        })

    if avg_daily > 8:
        recs.append({
            'title': 'Consumo diario alto',
            'description': 'Tu promedio diario supera los 8 kWh. Revisa electrodomésticos de alto consumo como aire acondicionado o calentadores.',
            'category': 'consumo',
            'priority': 'high'
        })
    elif avg_daily > 5:
        recs.append({
            'title': 'Consumo diario moderado',
            'description': 'Tu consumo diario es moderado. Pequeños ajustes pueden generar ahorros significativos.',
            'category': 'consumo',
            'priority': 'medium'
        })

    cost = round(avg_monthly * user.tariff_rate, 2)
    if cost > 50:
        recs.append({
            'title': 'Costo elevado estimado',
            'description': f'Tu factura estimada es ${cost}. Considera usar electrodomésticos eficientes y apagar luces innecesarias.',
            'category': 'costo',
            'priority': 'high'
        })

    co2 = round(avg_monthly * 0.42, 2)
    if co2 > 10:
        recs.append({
            'title': 'Alta emisión de CO₂',
            'description': f'Emites aproximadamente {co2} kg de CO₂ al mes. Reducir 10 kWh equivale a eliminar 4.2 kg de CO₂.',
            'category': 'ambiente',
            'priority': 'medium'
        })

    general_tips = [
        ('Apaga luces al salir', 'Reducir el uso de iluminación artificial puede ahorrar hasta un 15% en tu factura.', 'general', 'low'),
        ('Usa electrodomésticos eficientes', 'Los electrodomésticos con etiqueta energética A+ consumen hasta un 50% menos.', 'general', 'low'),
        ('Desconecta cargadores', 'Los cargadores conectados sin usar consumen energía fantasma. Desconéctalos cuando no los uses.', 'general', 'low'),
        ('Programa el termostato', 'Cada grado menos en calefacción puede reducir el consumo un 7%.', 'general', 'low'),
        ('Lava ropa en frío', 'El 90% de la energía de lavadora se usa para calentar agua. Lavar en frío ahorra significativamente.', 'general', 'low'),
    ]

    for title, desc, cat, pri in general_tips[:2]:
        recs.append({'title': title, 'description': desc, 'category': cat, 'priority': pri})

    return recs


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('¡Bienvenido de nuevo!', 'success')
            return redirect(url_for('dashboard'))
        flash('Email o contraseña incorrectos.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('Todos los campos son obligatorios.', 'error')
        elif password != confirm:
            flash('Las contraseñas no coinciden.', 'error')
        elif len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Este email ya está registrado.', 'error')
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('¡Cuenta creada exitosamente!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    readings = Reading.query.filter_by(user_id=current_user.id).order_by(Reading.reading_date.desc()).all()
    consumptions = calculate_consumption(readings)

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    month_readings = [r for r in readings if r.reading_date.month == current_month and r.reading_date.year == current_year]
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    prev_readings = [r for r in readings if r.reading_date.month == prev_month and r.reading_date.year == prev_year]

    current_consumption = 0
    if len(month_readings) >= 2:
        sorted_m = sorted(month_readings, key=lambda r: r.reading_date)
        current_consumption = round(sorted_m[-1].meter_reading - sorted_m[0].meter_reading, 2)

    prev_consumption = 0
    if len(prev_readings) >= 2:
        sorted_p = sorted(prev_readings, key=lambda r: r.reading_date)
        prev_consumption = round(sorted_p[-1].meter_reading - sorted_p[0].meter_reading, 2)

    variation = 0
    if prev_consumption > 0:
        variation = round(((current_consumption - prev_consumption) / prev_consumption) * 100, 1)

    estimated_cost = round(current_consumption * current_user.tariff_rate, 2)
    co2_emitted = round(current_consumption * 0.42, 2)
    goal_percent = round((current_consumption / current_user.monthly_goal_kwh) * 100, 1) if current_user.monthly_goal_kwh > 0 else 0
    goal_percent = min(goal_percent, 100)

    chart_labels = [c['date'] for c in consumptions[-12:]]
    chart_data = [c['kwh'] for c in consumptions[-12:]]

    categories = {
        'Iluminación': round(current_consumption * 0.15, 2),
        'Climatización': round(current_consumption * 0.35, 2),
        'Electrodomésticos': round(current_consumption * 0.30, 2),
        'Otros': round(current_consumption * 0.20, 2),
    }

    recommendations = generate_recommendations(current_user, consumptions)

    return render_template('dashboard.html',
        current_consumption=current_consumption,
        variation=variation,
        estimated_cost=estimated_cost,
        co2_emitted=co2_emitted,
        goal_percent=goal_percent,
        chart_labels=chart_labels,
        chart_data=chart_data,
        categories=categories,
        readings=readings[:10],
        recommendations=recommendations,
        consumptions=consumptions[-6:]
    )


@app.route('/readings')
@login_required
def readings_page():
    readings = Reading.query.filter_by(user_id=current_user.id).order_by(Reading.reading_date.desc()).all()
    return render_template('readings.html', readings=readings)


@app.route('/api/readings', methods=['POST'])
@login_required
def add_reading():
    data = request.get_json() if request.is_json else None
    if data:
        meter = data.get('meter_reading')
        reading_date = data.get('reading_date')
        notes = data.get('notes', '')
    else:
        meter = request.form.get('meter_reading')
        reading_date = request.form.get('reading_date')
        notes = request.form.get('notes', '')

    if not meter:
        return jsonify({'error': 'Lectura del medidor es requerida'}), 400

    try:
        meter = float(meter)
    except (ValueError, TypeError):
        return jsonify({'error': 'Lectura inválida'}), 400

    if reading_date:
        try:
            rd = datetime.strptime(reading_date, '%Y-%m-%d').date()
        except ValueError:
            rd = date.today()
    else:
        rd = date.today()

    reading = Reading(user_id=current_user.id, meter_reading=meter, reading_date=rd, notes=notes or '')
    db.session.add(reading)
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': 'Lectura registrada exitosamente'})
    flash('Lectura registrada exitosamente.', 'success')
    return redirect(url_for('readings_page'))


@app.route('/api/readings/<int:reading_id>', methods=['DELETE'])
@login_required
def delete_reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    if reading.user_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    db.session.delete(reading)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/statistics')
@login_required
def statistics_page():
    readings = Reading.query.filter_by(user_id=current_user.id).order_by(Reading.reading_date.asc()).all()
    consumptions = calculate_consumption(readings)

    monthly_data = {}
    for c in consumptions:
        month_key = c['date'][:7]
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += c['kwh']

    labels = list(monthly_data.keys())[-12:]
    values = [round(monthly_data[k], 2) for k in labels]

    total_kwh = sum(c['kwh'] for c in consumptions)
    total_cost = round(total_kwh * current_user.tariff_rate, 2)
    total_co2 = round(total_kwh * 0.42, 2)
    avg_monthly = round(total_kwh / max(len(labels), 1), 2)

    return render_template('statistics.html',
        labels=labels,
        values=values,
        total_kwh=round(total_kwh, 2),
        total_cost=total_cost,
        total_co2=total_co2,
        avg_monthly=avg_monthly,
        consumptions=consumptions
    )


@app.route('/recommendations')
@login_required
def recommendations_page():
    readings = Reading.query.filter_by(user_id=current_user.id).order_by(Reading.reading_date.asc()).all()
    consumptions = calculate_consumption(readings)
    recs = generate_recommendations(current_user, consumptions)

    return render_template('recommendations.html', recommendations=recs)


@app.route('/history')
@login_required
def history_page():
    readings = Reading.query.filter_by(user_id=current_user.id).order_by(Reading.reading_date.desc()).all()
    consumptions = calculate_consumption(readings)
    return render_template('history.html', readings=readings, consumptions=consumptions)


@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')


@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')


@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    if data.get('name'):
        current_user.name = data['name']
    if data.get('monthly_goal_kwh'):
        current_user.monthly_goal_kwh = float(data['monthly_goal_kwh'])
    if data.get('tariff_rate'):
        current_user.tariff_rate = float(data['tariff_rate'])
    if data.get('currency'):
        current_user.currency = data['currency']
    if 'notifications_enabled' in data:
        current_user.notifications_enabled = data['notifications_enabled']
    db.session.commit()
    return jsonify({'success': True, 'message': 'Perfil actualizado'})


@app.route('/api/stats')
@login_required
def api_stats():
    readings = Reading.query.filter_by(user_id=current_user.id).order_by(Reading.reading_date.asc()).all()
    consumptions = calculate_consumption(readings)
    return jsonify({
        'consumptions': consumptions,
        'monthly_goal': current_user.monthly_goal_kwh,
        'tariff_rate': current_user.tariff_rate
    })


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
