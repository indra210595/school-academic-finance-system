from flask import render_template, request, url_for
from flask_login import login_required
from app import db
from app.models import TahunAjaran
from app.akademik import akademik_bp
import time
from sqlalchemy import func

PER_PAGE = 5


@akademik_bp.route('/tahun-ajaran', methods=['GET', 'POST'])
@login_required
def tahun_ajaran():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    if request.method == 'POST':
        tahun = request.form.get('tahun_ajaran')
        is_aktif = request.form.get('is_aktif') == 'true'
        start_month = int(request.form.get('start_month'))
        end_month = int(request.form.get('end_month'))

        time.sleep(0.5)

        cek = db.session.execute(db.select(TahunAjaran).where(TahunAjaran.tahun == tahun)).scalar_one_or_none()

        # kalo ada
        if cek:
            total_data = db.session.execute(db.select(func.count(TahunAjaran.id))).scalar()
            total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
            daftar = db.session.execute(
                db.select(TahunAjaran).order_by(TahunAjaran.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
            return render_template('akademik/_daftar_tahun_ajaran.html',
                                   daftar_tahun_ajaran=daftar,
                                   current_page=1,
                                   total_pages=total_pages,
                                   per_page=PER_PAGE,
                                   search="",  # FIX: Tambahin biar template gak bingung
                                   alert_message=f"Tahun ajaran <b>{tahun}</b> sudah ada.",
                                   alert_category="danger")

        # Simpan
        baru = TahunAjaran(tahun=tahun, start_month=start_month, end_month=end_month, is_active=is_aktif)
        db.session.add(baru)
        db.session.commit()

        total_data = db.session.execute(db.select(func.count(TahunAjaran.id))).scalar()
        total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
        daftar = db.session.execute(
            db.select(TahunAjaran).order_by(TahunAjaran.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
        return render_template('akademik/_daftar_tahun_ajaran.html',
                               daftar_tahun_ajaran=daftar,
                               current_page=1,
                               total_pages=total_pages,
                               per_page=PER_PAGE,
                               search="", # kosongin search
                               alert_message=f"Tahun ajaran <b>{tahun}</b> berhasil disimpan.",
                               alert_category="success")

    # search
    stmt = db.select(TahunAjaran).order_by(TahunAjaran.id.desc())
    count_stmt = db.select(func.count(TahunAjaran.id))

    if search_query:
        stmt = stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))
        count_stmt = count_stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/tahun_ajaran.html',
                           daftar_tahun_ajaran=daftar, current_page=page, total_pages=total_pages, per_page=PER_PAGE,
                           search=search_query)


# kalo tombol search / pagination di klik
@akademik_bp.route('/tahun-ajaran/tabel', methods=['GET'])
@login_required
def tahun_ajaran_tabel():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    stmt = db.select(TahunAjaran).order_by(TahunAjaran.id.desc())
    count_stmt = db.select(func.count(TahunAjaran.id))

    if search_query:
        stmt = stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))
        count_stmt = count_stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/_daftar_tahun_ajaran.html',
                           daftar_tahun_ajaran=daftar,
                           current_page=page, total_pages=total_pages, per_page=PER_PAGE,
                           search=search_query)


# buat toggle (klik) aktif / tidak aktif
@akademik_bp.route('/tahun-ajaran/toggle/<int:id>', methods=['POST'])
@login_required
def toggle_tahun_ajaran(id):
    target = db.session.get(TahunAjaran, id)

    if target:
        target.is_active = not target.is_active
        db.session.commit()

    # Ambil parameter page & search saat ini biar pas di-toggle posisi tabel gak lompat/nge-reset
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    stmt = db.select(TahunAjaran).order_by(TahunAjaran.id.desc())
    count_stmt = db.select(func.count(TahunAjaran.id))

    if search_query:
        stmt = stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))
        count_stmt = count_stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/_daftar_tahun_ajaran.html',
                           daftar_tahun_ajaran=daftar,
                           current_page=page, total_pages=total_pages, per_page=PER_PAGE, search=search_query,
                           alert_message=f"Status Periode <b>{target.tahun}</b> berhasil diubah!",
                           alert_category="success")


#EDIT
@akademik_bp.route('/tahun-ajaran/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tahun_ajaran(id):
    target = db.session.get(TahunAjaran, id)
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    if request.method == 'POST':
        tahun = request.form.get('tahun_ajaran')

        # Cek duplikat nama tahun ajaran (abaikan id yang lagi diedit)
        cek = db.session.execute(
            db.select(TahunAjaran).where(TahunAjaran.tahun == tahun, TahunAjaran.id != id)).scalar_one_or_none()

        if cek:
            stmt = db.select(TahunAjaran).order_by(TahunAjaran.id.desc())
            if search_query:
                stmt = stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))
            daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

            return render_template('akademik/_daftar_tahun_ajaran.html',
                                   daftar_tahun_ajaran=daftar, current_page=page, total_pages=1, per_page=PER_PAGE,
                                   search=search_query,
                                   alert_message=f"Gagal! Tahun ajaran <b>{tahun}</b> sudah terdaftar.",
                                   alert_category="danger")

        # update
        target.tahun = tahun
        db.session.commit()

        # Ambil data terbaru buat ngerender ulang tabel utuh
        stmt = db.select(TahunAjaran).order_by(TahunAjaran.id.desc())
        count_stmt = db.select(func.count(TahunAjaran.id))
        if search_query:
            stmt = stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))
            count_stmt = count_stmt.where(TahunAjaran.tahun.ilike(f"%{search_query}%"))

        total_data = db.session.execute(count_stmt).scalar()
        total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
        daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

        return render_template('akademik/_daftar_tahun_ajaran.html',
                               daftar_tahun_ajaran=daftar, current_page=page, total_pages=total_pages,
                               per_page=PER_PAGE, search=search_query,
                               alert_message=f"Sip! Tahun ajaran berhasil diperbarui.", alert_category="success")

    # UBAH BARIS TR JADI FORM INPUT TEKS
    no = request.args.get('no', '')
    nama_bulan = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober',
                  'November', 'Desember']
    periode_bulan = f"{nama_bulan[target.start_month]} - {nama_bulan[target.end_month]}"

    # Render status statis pas lagi mode edit
    if target.is_active:
        status_badge = '<span class="badge bg-success-subtle text-success border border-success">Aktif</span>'
    else:
        status_badge = '<span class="badge bg-secondary-subtle text-secondary border border-secondary">Tidak Aktif</span>'

    return f"""
    <tr id="baris-tahun-{target.id}" class="table-warning-subtle">
        <td>{no}</td>
        <td>
            <input type="text" class="form-control form-control-sm fw-bold" name="tahun_ajaran" value="{target.tahun}" form="form-edit-tahun-{target.id}" required>
        </td>
        <td>{periode_bulan}</td>
        <td>{status_badge}</td>
        <td class="text-center">
            <form id="form-edit-tahun-{target.id}" 
                  hx-post="{url_for('akademik.edit_tahun_ajaran', id=target.id)}?page={page}&search={search_query}" 
                  hx-target="#bagian-tabel-tahun-ajaran" 
                  hx-swap="innerHTML">
            </form>
            <button type="submit" form="form-edit-tahun-{target.id}" class="btn btn-sm btn-success fw-bold me-1">Simpan</button>
            <button type="button" 
                    hx-get="{url_for('akademik.tahun_ajaran_tabel')}?page={page}&search={search_query}" 
                    hx-target="#bagian-tabel-tahun-ajaran" 
                    hx-swap="innerHTML" 
                    class="btn btn-sm btn-secondary fw-bold">
                Batal
            </button>
        </td>
    </tr>
    """.strip()

@akademik_bp.route('/tahun-ajaran/<int:id>', methods=['DELETE'])
@login_required
def hapus_tahun_ajaran(id):
    target = db.session.get(TahunAjaran, id)
    if target:
        db.session.delete(target)
        db.session.commit()
    return ""