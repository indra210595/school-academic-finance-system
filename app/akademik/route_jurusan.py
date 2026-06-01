from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.akademik import akademik_bp
from app.models import Jurusan
from app import db
import time
from sqlalchemy import func

PER_PAGE = 5

@akademik_bp.route('/jurusan', methods=['GET', 'POST'])
@login_required
def jurusan():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    if request.method == 'POST':
        nama_jurusan = request.form.get('nama_jurusan')
        deskripsi = request.form.get('deskripsi')

        time.sleep(0.5)

        cek_jurusan = db.session.execute(db.select(Jurusan).where(Jurusan.nama_jurusan == nama_jurusan)).scalar_one_or_none()

        if cek_jurusan:
            total_data = db.session.execute(db.select(func.count(Jurusan.id))).scalar()
            total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
            daftar_jurusan = db.session.execute(db.select(Jurusan).order_by(Jurusan.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
            return render_template('akademik/_daftar_jurusan.html',
                                   daftar_jurusan=daftar_jurusan,
                                   current_page = 1,
                                   total_pages=total_pages,
                                   per_page=PER_PAGE,
                                   alert_message=f"Jurusan <b>{nama_jurusan}</b> sudah ada! Coba yang lain.",
                                   alert_category="danger")

        jurusan_baru = Jurusan(nama_jurusan=nama_jurusan, deskripsi=deskripsi)
        db.session.add(jurusan_baru)
        db.session.commit()

        # Ambil data terbaru setelah ditambah, terus render komponen tabelnya
        total_data = db.session.execute(db.select(func.count(Jurusan.id))).scalar()
        total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
        daftar_jurusan = db.session.execute(db.select(Jurusan).order_by(Jurusan.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
        return render_template('akademik/_daftar_jurusan.html',
                               daftar_jurusan=daftar_jurusan,
                               current_page=1,
                               total_pages=total_pages,
                               per_page=PER_PAGE,
                               alert_message=f"Data <b>{jurusan_baru.nama_jurusan}</b> berhasil disimpan.",
                               alert_category="success")

    # search
    stmt = db.select(Jurusan).order_by(Jurusan.id.desc())
    count_stmt = db.select(func.count(Jurusan.id))
    if search_query:
        # Cari berdasarkan nama jurusan ATAU deskripsi yang mirip
        stmt = stmt.where(
            (Jurusan.nama_jurusan.ilike(f"%{search_query}%")) | (Jurusan.deskripsi.ilike(f"%{search_query}%")))
        count_stmt = count_stmt.where(
            (Jurusan.nama_jurusan.ilike(f"%{search_query}%")) | (Jurusan.deskripsi.ilike(f"%{search_query}%")))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar_jurusan = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/jurusan.html',
                           daftar_jurusan=daftar_jurusan, current_page=page, total_pages=total_pages, per_page=PER_PAGE,
                           search=search_query)

# RUTE BANTUAN BUAT RE-REFRESH TABEL (PAS BATAL)
@akademik_bp.route('/jurusan/tabel', methods=['GET'])
@login_required
def jurusan_tabel():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    stmt = db.select(Jurusan).order_by(Jurusan.id.desc())
    count_stmt = db.select(func.count(Jurusan.id))

    if search_query:
        stmt = stmt.where(
            (Jurusan.nama_jurusan.ilike(f"%{search_query}%")) | (Jurusan.deskripsi.ilike(f"%{search_query}%")))
        count_stmt = count_stmt.where(
            (Jurusan.nama_jurusan.ilike(f"%{search_query}%")) | (Jurusan.deskripsi.ilike(f"%{search_query}%")))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar_jurusan = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/_daftar_jurusan.html',
                           daftar_jurusan=daftar_jurusan, current_page=page, total_pages=total_pages, per_page=PER_PAGE,
                           search=search_query)


# EDIT JURUSAN
@akademik_bp.route('/jurusan/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_jurusan(id):
    jurusan = db.session.get(Jurusan, id)

    if request.method == 'POST':
        nama_jurusan = request.form.get('nama_jurusan')
        deskripsi = request.form.get('deskripsi')

        # ngecek duplikat nama jurusan, tapi abaikan ID milik baris yang lagi diedit
        cek = db.session.execute(
            db.select(Jurusan).where(Jurusan.nama_jurusan == nama_jurusan, Jurusan.id != id)).scalar_one_or_none()

        if cek:
            daftar_jurusan = db.session.execute(db.select(Jurusan).order_by(Jurusan.id.desc())).scalars().all()
            return render_template('akademik/_daftar_jurusan.html',
                                   daftar_jurusan=daftar_jurusan,
                                   alert_message=f"Gagal! Jurusan dengan nama <b>{nama_jurusan}</b> sudah ada.",
                                   alert_category="danger")

        jurusan.nama_jurusan = nama_jurusan
        jurusan.deskripsi = deskripsi
        db.session.commit()

        # Ambil data terbaru dan kirim partial tabel utuh (biar alert sukses muncul di atas)
        daftar_jurusan = db.session.execute(db.select(Jurusan).order_by(Jurusan.id.desc())).scalars().all()
        return render_template('akademik/_daftar_jurusan.html',
                               daftar_jurusan=daftar_jurusan,
                               alert_message=f"Sip! Data jurusan berhasil diperbarui.",
                               alert_category="success")

    # UBAH TAMPILAN BARIS TR JADI SEBUAH FORM INPUT
    no = request.args.get('no', '')
    return f"""
    <tr id="baris-{jurusan.id}" class="table-warning-subtle">
        <td>{no}</td>
        <td>
            <input type="text" class="form-control form-control-sm fw-bold" name="nama_jurusan" value="{jurusan.nama_jurusan}" form="form-edit-{jurusan.id}" required>
        </td>
        <td>
            <input type="text" class="form-control form-control-sm" name="deskripsi" value="{jurusan.deskripsi}" form="form-edit-{jurusan.id}">
        </td>
        <td class="text-center">
            <form id="form-edit-{jurusan.id}" 
                  hx-post="{url_for('akademik.edit_jurusan', id=jurusan.id)}" 
                  hx-target="#bagian-tabel-jurusan" 
                  hx-swap="innerHTML">
            </form>

            <button type="submit" form="form-edit-{jurusan.id}" class="btn btn-sm btn-success fw-bold me-1">
                Simpan
            </button>
            <button type="button" 
                    hx-get="{url_for('akademik.jurusan_tabel')}" 
                    hx-target="#bagian-tabel-jurusan" 
                    hx-swap="innerHTML" 
                    class="btn btn-sm btn-secondary fw-bold">
                Batal
            </button>
        </td>
    </tr>
    """.strip()

# DELETE jurusan dari HTMX
@akademik_bp.route('/jurusan/<int:id>', methods=['DELETE'])
@login_required
def hapus_jurusan(id):
    jurusan_yg_mau_dihapus = db.session.get(Jurusan, id)

    if jurusan_yg_mau_dihapus:
        db.session.delete(jurusan_yg_mau_dihapus)
        db.session.commit()
        # balikin string kosong (biar HTMX ngeganti baris <tr> jadi hilang)
        return ""

    return "Data tidak ada", 404