from flask import Blueprint

akademik_bp = Blueprint('akademik', __name__)

from app.akademik import route_jurusan, route_tahun_ajaran, route_kelas, route_pendaftaran, route_spp