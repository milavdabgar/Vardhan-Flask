from app import create_app, db
from app.models import User, ServiceRequest, TicketUpdate
from flask import jsonify

app = create_app()

@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'ServiceRequest': ServiceRequest,
        'TicketUpdate': TicketUpdate
    }

if __name__ == '__main__':
    # Only used for development
    app.run(host='0.0.0.0', port=5000, debug=True)
