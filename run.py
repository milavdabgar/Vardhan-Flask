from app import create_app, db
from app.models import User, ServiceRequest, TicketUpdate

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'ServiceRequest': ServiceRequest,
        'TicketUpdate': TicketUpdate
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
