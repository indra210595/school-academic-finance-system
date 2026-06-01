from flask import render_template, request, url_for, make_response, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Spp, TahunAjaran, Jurusan, Siswa, Invoice, Payment
from app.akademik import akademik_bp
from sqlalchemy import or_, and_
from sqlalchemy import func
import time
from datetime import datetime, date
from weasyprint import HTML
from io import BytesIO
import openpyxl

PER_PAGE = 5

@akademik_bp.route('/master/spp', methods=['GET', 'POST'])
@login_required
def master_spp():
    page = request.args.get('page', 1, type=int)

    # POST
    if request.method == 'POST':
        tahun_ajaran_id = int(request.form.get('tahun_ajaran_id'))
        jurusan_id = int(request.form.get('jurusan_id')) # bisa kosong (semua)
        jurusan_id = int(jurusan_id) if jurusan_id and jurusan_id != "" else None
        jumlah = request.form.get('jumlah')

        try:
            cek_data = db.select(Spp).where(
                Spp.tahun_ajaran_id == int(tahun_ajaran_id),
                Spp.jurusan_id == jurusan_id
            )
            cek_duplikat = db.session.execute(cek_data).scalar_one_or_none()

            if cek_duplikat:
                msg, cat = "Tarif SPP ini sudah pernah dibuat", "danger"
            else:
                spp = Spp(
                    tahun_ajaran_id=tahun_ajaran_id,
                    jurusan_id=jurusan_id,
                    jumlah=int(jumlah)
                )
                db.session.add(spp)
                db.session.commit()
                msg, cat = "Data berhasil disimpan", "success"
        except Exception as e:
            db.session.rollback()
            msg, cat = f"Gagal simpan data. Error: {str(e)}", "danger"

        get_spp = db.select(Spp).order_by(Spp.id.desc())
        pagination = db.paginate(get_spp, page=1, per_page=PER_PAGE, error_out=False)
        return render_template('akademik/_daftar_spp.html',
                               list_spp=pagination.items,
                               current_page=pagination.page,
                               total_pages=pagination.pages,
                               per_page=PER_PAGE,
                               alert_message=msg,
                               alert_category=cat)

    # GET
    get_ta = db.select(TahunAjaran).where(TahunAjaran.is_active == True).order_by(TahunAjaran.tahun.desc())
    list_ta = db.session.execute(get_ta).scalars().all()

    get_jur = db.select(Jurusan).order_by(Jurusan.nama_jurusan)
    list_jur = db.session.execute(get_jur).scalars().all()

    get_spp = db.select(Spp).order_by(Spp.id.desc())
    pagination = db.paginate(get_spp, page=page, per_page=PER_PAGE, error_out=False)

    # ngecek kalau yang request adalah HTMX (pas ngeklik nomor halaman), balikin tabelnya doang
    if 'HX-Request' in request.headers:
        return render_template('akademik/_daftar_spp.html',
                               list_spp=pagination.items,
                               current_page=pagination.page,
                               total_pages=pagination.pages,
                               per_page=PER_PAGE)

    # kalau request biasa (awal buka halaman), balikin full template
    return render_template('akademik/master_spp.html',
                           list_ta=list_ta,
                           list_jur=list_jur,
                           list_spp=pagination.items,
                           current_page=pagination.page,
                           total_pages=pagination.pages,
                           per_page=PER_PAGE)

@akademik_bp.route('/master/spp/edit/<int:id>', methods=['GET'])
@login_required
def edit_spp_row(id):
    spp = db.session.get(Spp, id)
    list_ta = db.session.execute(db.select(TahunAjaran).order_by(TahunAjaran.tahun.desc())).scalars().all()
    list_jur = db.session.execute(db.select(Jurusan).order_by(Jurusan.nama_jurusan)).scalars().all()
    return render_template('akademik/_row_spp_edit.html', s=spp, list_ta=list_ta, list_jur=list_jur)

@akademik_bp.route('/master/spp/cancel/<int:id>', methods=['GET'])
@login_required
def cancel_spp_row(id):
    spp = db.session.get(Spp, id)
    # nyari posisi index baris asli biar angkanya gak berubah pas dicancel
    all_ids = db.session.execute(db.select(Spp.id).order_by(Spp.id.desc())).scalars().all()
    idx = all_ids.index(id) + 1 if id in all_ids else "#"
    return render_template('akademik/_row_spp.html', s=spp, index=idx)

@akademik_bp.route('/master/spp/update/<int:id>', methods=['POST'])
@login_required
def update_spp_row(id):
    spp = db.session.get(Spp, id)
    tahun_ajaran_id = request.form.get('tahun_ajaran_id')
    jurusan_id = request.form.get('jurusan_id')
    jurusan_id = int(jurusan_id) if jurusan_id and jurusan_id != "" else None
    jumlah = request.form.get('jumlah')

    try:
        stmt_cek = db.select(Spp).where(
            Spp.tahun_ajaran_id == int(tahun_ajaran_id),
            Spp.jurusan_id == jurusan_id,
            Spp.id != id
        )
        cek_duplikat = db.session.execute(stmt_cek).scalar_one_or_none()

        if cek_duplikat:
            alert_html = """
            <div id="bagian-alert-spp" hx-swap-oob="true">
                <div class="alert alert-danger alert-dismissible fade show fw-medium" role="alert">
                    <i class="fa-solid fa-circle-exclamation me-2"></i> Gagal Update! Kombinasi Tahun Ajaran & Jurusan tersebut sudah ada di baris lain.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            </div>
            """
            list_ta = db.session.execute(db.select(TahunAjaran).order_by(TahunAjaran.tahun.desc())).scalars().all()
            list_jur = db.session.execute(db.select(Jurusan).order_by(Jurusan.nama_jurusan)).scalars().all()
            return render_template('akademik/_row_spp_edit.html',
                                   s=spp, list_ta=list_ta, list_jur=list_jur, alert_html=alert_html)

        # update data
        spp.tahun_ajaran_id = int(tahun_ajaran_id)
        spp.jurusan_id = jurusan_id
        spp.jumlah = int(jumlah)
        db.session.commit()

        alert_html = """
        <div id="bagian-alert-spp" hx-swap-oob="true">
            <div class="alert alert-success alert-dismissible fade show fw-medium" role="alert">
                <i class="fa-solid fa-circle-check me-2"></i> Tarif SPP sukses diperbarui!
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        </div>
        """
        all_ids = db.session.execute(db.select(Spp.id).order_by(Spp.id.desc())).scalars().all()
        idx = all_ids.index(id) + 1 if id in all_ids else "#"
        return render_template('akademik/_row_spp.html', s=spp, index=idx, alert_html=alert_html)

    except Exception as e:
        db.session.rollback()
        return f"<tr id='row-spp-{id}' class='table-danger'><td colspan='5'>Error: {str(e)}</td></tr>"


@akademik_bp.route('/master/spp/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_spp_row(id):
    spp = db.session.get(Spp, id)
    try:
        db.session.delete(spp)
        db.session.commit()
        msg, cat = "Tarif master SPP berhasil dihapus", "success"
    except Exception as e:
        db.session.rollback()
        msg, cat = f"Gagal hapus tarif. Error: {str(e)}", "danger"

    get_spp = db.select(Spp).order_by(Spp.id.desc())
    pagination = db.paginate(get_spp, page=1, per_page=PER_PAGE, error_out=False)
    return render_template('akademik/_daftar_spp.html',
                           list_spp=pagination.items,
                           current_page=pagination.page,
                           total_pages=pagination.pages,
                           per_page=PER_PAGE,
                           alert_message=msg, alert_category=cat)

# transaksi

@akademik_bp.route('/pembayaran-spp', methods=['GET'])
@login_required
def pembayaran_spp():
    keyword_pencarian = request.args.get('search', '').strip()

    daftar_siswa = []

    if keyword_pencarian:
        query_pencarian_siswa = db.select(Siswa).where(
            (Siswa.nis.ilike(f"%{keyword_pencarian}%")) |
            (Siswa.nama_siswa.ilike(f"%{keyword_pencarian}%"))
        ).order_by(Siswa.nama_siswa)

        daftar_siswa = db.session.execute(query_pencarian_siswa).scalars().all()

    if 'HX-Request' in request.headers:
        return render_template('akademik/_table_pembayaran_spp.html',
                               siswa_list=daftar_siswa,
                               search=keyword_pencarian)

    return render_template('akademik/pembayaran_spp.html',
                           siswa_list=daftar_siswa,
                           search=keyword_pencarian)


@akademik_bp.route('/pembayaran-spp/siswa/<int:id>', methods=['GET'])
@login_required
def detail_pembayaran_spp(id):
    siswa = db.session.get(Siswa, id)

    if not siswa:
        flash("Data siswa tidak ditemukan!", "danger")
        return redirect(url_for('akademik.pembayaran_spp'))

    query_tagihan = db.select(Invoice).where(
        Invoice.siswa_id == id
    ).order_by(Invoice.tahun.asc(), Invoice.bulan.asc())

    daftar_tagihan = db.session.execute(query_tagihan).scalars().all()

    nama_bulan = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

    return render_template('akademik/detail_pembayaran_spp.html',
                           siswa=siswa,
                           list_tagihan=daftar_tagihan,
                           nama_bulan=nama_bulan)


@akademik_bp.route('/pembayaran-spp/bayar/<int:invoice_id>', methods=['POST'])
@login_required
def proses_bayar_spp(invoice_id):
    tagihan = db.session.get(Invoice, invoice_id)

    if not tagihan or tagihan.status == 'paid':
        return "Data tidak valid atau sudah dibayar", 400

    pembayaran_baru = Payment(
        invoice_id=tagihan.id,
        tanggal=date.today(),
        jumlah=tagihan.total,
        user_id=current_user.id
    )
    db.session.add(pembayaran_baru)

    tagihan.status = 'paid'
    db.session.commit()

    html_response = f"""
    <button class="btn btn-secondary btn-sm" disabled>Sudah Dibayar</button>

    <span id="status-{tagihan.id}" hx-swap-oob="true">
        <span class="badge bg-success">Lunas</span>
    </span>
    
    <span id="tanggal-{tagihan.id}" hx-swap-oob="true">
        {pembayaran_baru.tanggal.strftime('%d-%m-%Y')}
    </span>
    """

    return html_response


@akademik_bp.route('/pembayaran-spp/invoice/<int:invoice_id>/cetak')
@login_required
def cetak_invoice(invoice_id):
    tagihan = db.session.get(Invoice, invoice_id)

    html = render_template('akademik/invoice_template.html', tagihan=tagihan)

    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Invoice_{tagihan.id}.pdf'
    return response

# laporan
@akademik_bp.route('/laporan/bulanan', methods=['GET'])
@login_required
def laporan_bulanan():
    query_laporan = db.select(
        Invoice.tahun,
        Invoice.bulan,
        func.sum(Invoice.total).label('total_masuk'),
        func.count(Invoice.id).label('total_tagihan_lunas')
    ).where(Invoice.status == 'paid')\
     .group_by(Invoice.tahun, Invoice.bulan)\
     .order_by(Invoice.tahun.asc(), Invoice.bulan.asc())

    hasil_laporan = db.session.execute(query_laporan).all()

    nama_bulan = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                       "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

    return render_template('akademik/laporan_bulanan.html',
                           laporan=hasil_laporan,
                           nama_bulan=nama_bulan)


@akademik_bp.route('/laporan/bulanan/export', methods=['GET'])
@login_required
def export_laporan_bulanan():
    query_laporan = db.select(
        Invoice.tahun,
        Invoice.bulan,
        func.sum(Invoice.total).label('total_masuk'),
        func.count(Invoice.id).label('total_tagihan_lunas')
    ).where(Invoice.status == 'paid') \
        .group_by(Invoice.tahun, Invoice.bulan) \
        .order_by(Invoice.tahun.asc(), Invoice.bulan.asc())

    hasil_laporan = db.session.execute(query_laporan).all()

    nama_bulan = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                       "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

    # File Excel pake openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Laporan Pendapatan SPP"

    headers = ["No", "Periode Bulan", "Jumlah Tagihan Lunas", "Total Uang Masuk"]
    ws.append(headers)

    # looping buat masukin datanya
    for index, row in enumerate(hasil_laporan, start=1):
        # enumerate generate nomor otomatis di excel (index)
        periode = f"{nama_bulan[row.bulan]} {row.tahun}"
        jumlah_transaksi = f"{row.total_tagihan_lunas} Transaksi"

        ws.append([index, periode, jumlah_transaksi, row.total_masuk])

    # simpan ke memory (BytesIO) biar ga bikin file sampah di server
    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)  # reset pointer ke awal file

    # filenya langsung ke browser buat auto-download
    nama_file = f"Laporan_Keuangan_SPP_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nama_file
    )