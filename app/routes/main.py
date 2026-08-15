from flask import Blueprint, jsonify, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home / Welcome page."""
    return render_template('base.html')


@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Medical Appointment & Prescription Manager',
        'version': '1.0.0'
    }), 200
