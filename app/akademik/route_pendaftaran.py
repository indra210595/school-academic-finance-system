from flask import render_template, request, url_for, make_response, send_file
from flask_login import login_required
from app import db
from app.models import CalonSiswa, OrangTua, Pendaftaran, Jurusan, TahunAjaran, Siswa, Kelas, User, Role
from app.models import Spp, Invoice, InvoiceItem
from app.akademik import akademik_bp
from sqlalchemy import func
import time
from datetime import datetime
from werkzeug.security import generate_password_hash
from io import BytesIO
import openpyxl

PER_PAGE = 5


@akademik_bp.route('/pendaftaran', methods=['GET', 'POST'])
@login_required
def pendaftaran():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    # dropdown form pendaftaran
    list_jurusan = db.session.execute(db.select(Jurusan).order_by(Jurusan.nama_jurusan)).scalars().all()
    list_ta = db.session.execute(db.select(TahunAjaran).where(TahunAjaran.is_active == True)).scalars().all()

    if request.method == 'POST':
        # data calon siswa
        nama_lengkap = request.form.get('nama_lengkap')
        jenis_kelamin = request.form.get('jenis_kelamin')
        tempat_lahir = request.form.get('tempat_lahir')
        tanggal_lahir = datetime.strptime(request.form.get('tanggal_lahir'), '%Y-%m-%d').date()
        agama = request.form.get('agama')
        asal_sekolah = request.form.get('asal_sekolah')
        telepon = request.form.get('telepon')
        email = request.form.get('email')

        # cek email
        if email:
            check_email = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
            if check_email:
                # Kalau email udah kedaftar, langsung gagalin proses pendaftaran
                msg, cat = f"Gagal simpan! Email <b>{email}</b> sudah terdaftar sebagai akun pengguna di sistem.", "danger"

                stmt = db.select(Pendaftaran).order_by(Pendaftaran.id.desc()).limit(PER_PAGE).offset(0)
                daftar_pendaftaran = db.session.execute(stmt).scalars().all()
                return render_template('akademik/_daftar_pendaftaran.html',
                                       daftar_pendaftaran=daftar_pendaftaran, current_page=1, total_pages=1,
                                       per_page=PER_PAGE, search="",
                                       alert_message=msg, alert_category=cat)

        # data ortu
        nama_ayah = request.form.get('nama_ayah')
        telp_ayah = request.form.get('telp_ayah')
        pekerjaan_ayah = request.form.get('pekerjaan_ayah')

        # data jurusan & tahun ajaran
        jurusan_id = int(request.form.get('jurusan_id'))
        tahun_ajaran_id = int(request.form.get('tahun_ajaran_id'))

        time.sleep(0.5)

        try:
            # save pendaftaran
            no_daftar = f"PPDB-{int(time.time())}"
            daftar = Pendaftaran(
                nomor=no_daftar,
                jurusan_id=jurusan_id,
                tahun_ajaran_id=tahun_ajaran_id,
                tanggal_daftar=datetime.utcnow().date(),
                status='pending'
            )
            db.session.add(daftar)
            db.session.flush()  # dapet daftar.id duluan sebelum commit

            # save calon siswa
            calon = CalonSiswa(
                pendaftaran_id=daftar.id,
                nama_lengkap=nama_lengkap,
                jenis_kelamin=jenis_kelamin,
                tempat_lahir=tempat_lahir,
                tanggal_lahir=tanggal_lahir,
                agama=agama,
                asal_sekolah=asal_sekolah,
                telepon=telepon,
                email=email
            )
            db.session.add(calon)
            db.session.flush() # ambil calon.id buat ortu

            # save ortu
            ayah = OrangTua(
                calon_siswa_id=calon.id,
                tipe='ayah',
                nama=nama_ayah,
                telepon=telp_ayah,
                pekerjaan=pekerjaan_ayah
            )
            db.session.add(ayah)
            db.session.commit()

            msg, cat = f"Pendaftaran <b>{nama_lengkap}</b> sukses dibuat dengan nomor <b>{no_daftar}</b>.", "success"
        except Exception as e:
            db.session.rollback()
            msg, cat = f"Gagal simpan data. Error: {str(e)}", "danger"

        # get data terbaru buat refresh tabel kanan
        stmt = db.select(Pendaftaran).order_by(Pendaftaran.id.desc()).limit(PER_PAGE).offset(0)
        daftar_pendaftaran = db.session.execute(stmt).scalars().all()
        return render_template('akademik/_daftar_pendaftaran.html',
                               daftar_pendaftaran=daftar_pendaftaran, current_page=1, total_pages=1, per_page=PER_PAGE,
                               search="",
                               alert_message=msg, alert_category=cat)

    # GET
    stmt = db.select(Pendaftaran).order_by(Pendaftaran.id.desc())
    count_stmt = db.select(func.count(Pendaftaran.id))

    if search_query:
        # search nama calon siswa atau nomor pendaftaran
        stmt = stmt.join(CalonSiswa).where((CalonSiswa.nama_lengkap.ilike(f"%{search_query}%")) | (
            Pendaftaran.no_pendaftaran.ilike(f"%{search_query}%")))
        count_stmt = count_stmt.join(CalonSiswa).where((CalonSiswa.nama_lengkap.ilike(f"%{search_query}%")) | (
            Pendaftaran.no_pendaftaran.ilike(f"%{search_query}%")))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar_pendaftaran = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/pendaftaran.html',
                           daftar_pendaftaran=daftar_pendaftaran, list_jurusan=list_jurusan, list_ta=list_ta,
                           current_page=page, total_pages=total_pages, per_page=PER_PAGE, search=search_query)


@akademik_bp.route('/pendaftaran/tabel', methods=['GET'])
@login_required
def pendaftaran_tabel():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    stmt = db.select(Pendaftaran).order_by(Pendaftaran.id.desc())
    count_stmt = db.select(func.count(Pendaftaran.id))

    if search_query:
        stmt = stmt.join(CalonSiswa).where((CalonSiswa.nama_lengkap.ilike(f"%{search_query}%")) | (
            Pendaftaran.no_pendaftaran.ilike(f"%{search_query}%")))
        count_stmt = count_stmt.join(CalonSiswa).where((CalonSiswa.nama_lengkap.ilike(f"%{search_query}%")) | (
            Pendaftaran.no_pendaftaran.ilike(f"%{search_query}%")))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar_pendaftaran = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/_daftar_pendaftaran.html',
                           daftar_pendaftaran=daftar_pendaftaran, current_page=page, total_pages=total_pages,
                           per_page=PER_PAGE, search=search_query)


@akademik_bp.route('/pendaftaran/status/<int:id>', methods=['POST'])
@login_required
def ubah_status_pendaftaran(id):
    target = db.session.get(Pendaftaran, id)
    status_baru = request.args.get('status')  # diterima / ditolak

    if target and status_baru in ['diterima', 'ditolak']:
        target.status = status_baru
        db.session.commit()

    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    stmt = db.select(Pendaftaran).order_by(Pendaftaran.id.desc())
    count_stmt = db.select(func.count(Pendaftaran.id))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar_pendaftaran = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/_daftar_pendaftaran.html',
                           daftar_pendaftaran=daftar_pendaftaran, current_page=page, total_pages=total_pages,
                           per_page=PER_PAGE, search=search_query,
                           alert_message=f"Status pendaftaran <b>{target.calon_siswa.nama_lengkap}</b> diubah jadi <b>{status_baru.upper()}</b>!",
                           alert_category="info")


@akademik_bp.route('/pendaftaran/detail/<int:id>', methods=['GET'])
@login_required
def detail_pendaftaran(id):
    # Ambil data transaksi pendaftaran lengkap beserta relasinya
    pendaftaran = db.session.get(Pendaftaran, id)

    if not pendaftaran:
        return "<div class='modal-body text-danger fw-bold'>Data tidak ditemukan!</div>"

    # Ambil data anak & list orang tua dari relationship
    calon = pendaftaran.calon_siswa
    list_ortu = calon.orang_tua_list if calon else []

    # Pisahin data ayah/ibu/wali biar gampang di-render di HTML
    ayah = next((o for o in list_ortu if o.tipe == 'ayah'), None)
    ibu = next((o for o in list_ortu if o.tipe == 'ibu'), None)

    return render_template('akademik/_detail_pendaftaran.html',
                           p=pendaftaran, c=calon, ayah=ayah, ibu=ibu)


@akademik_bp.route('/pendaftaran/terima-modal/<int:id>', methods=['GET'])
@login_required
def modal_terima_kelas(id):
    pendaftaran = db.session.get(Pendaftaran, id)

    # cari kelas yang JURUSAN dan TAHUN AJARAN COCOK sama pilihan si calon siswa
    stmt = db.select(Kelas).where(
        Kelas.jurusan_id == pendaftaran.jurusan_id,
        Kelas.tahun_ajaran_id == pendaftaran.tahun_ajaran_id
    ).order_by(Kelas.nama_kelas)
    kelas_pilihan = db.session.execute(stmt).scalars().all()

    options_kelas = "".join(
        f'<option value="{k.id}">{k.nama_kelas}</option>' for k in kelas_pilihan
    )

    if not kelas_pilihan:
        return f"""
        <div class="modal-header bg-danger text-white">
            <h5 class="modal-title fw-bold">Error!</h5>
        </div>
        <div class="modal-body text-center py-4">
            <p class="text-danger fw-bold mb-0">
                Gagal! Belum ada Kelas yang dibikin buat Jurusan <u>{pendaftaran.jurusan.nama_jurusan}</u> di periode ini.
            </p>
            <small class="text-muted">Silahkan bikin kelasnya dulu di menu Master Data Kelas</small>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Tutup
            </button>
        </div>
        """.strip()

    # Balikin isi body modal plus form HTMX buat konfirmasi
    return f"""
    <div class="modal-header bg-success text-white">
        <h5 class="modal-title fw-bold">
            <i class="fa-solid fa-graduation-cap me-2"></i> 
                Plotting Kelas & Aktivasi
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
    </div>
    <form hx-post="{url_for('akademik.konfirmasi_terima_siswa', id=pendaftaran.id)}" hx-target="#bagian-tabel-pendaftaran" hx-swap="innerHTML">
        <div class="modal-body py-4">
            <p class="mb-3">
                Silahkan tentukan penempatan kelas untuk calon siswa bernama: <br><strong class="text-primary fs-5">{pendaftaran.calon_siswa.nama_lengkap}</strong>
            </p>
            <div class="mb-3">
                <label class="form-label fw-bold small">Pilih Kelas Aktif ({pendaftaran.jurusan.nama_jurusan})</label>
                <select class="form-select border-success" name="kelas_id" required>
                    <option value="">-- Pilih Kelas --</option>
                    {options_kelas}
                </select>
            </div>
            <small class="text-muted d-block bg-light p-2 border rounded">
                <i class="fa-solid fa-circle-info text-info me-1"></i> 
                Sistem otomatis akan membuatkan nomor <b>NIS otomatis</b> dan <b>akun login siswa</b> setelah tombol konfirmasi diklik.
            </small>
        </div>
        <div class="modal-footer bg-light">
            <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">Batal</button>
            <button type="submit" class="btn btn-success fw-bold" data-bs-dismiss="modal">Konfirmasi & Terima Siswa 🎉</button>
        </div>
    </form>
    """.strip()


@akademik_bp.route('/pendaftaran/konfirmasi-terima/<int:id>', methods=['POST'])
@login_required
def konfirmasi_terima_siswa(id):
    pendaftaran = db.session.get(Pendaftaran, id)
    calon = pendaftaran.calon_siswa
    kelas_id = int(request.form.get('kelas_id'))

    try:
        # GENERATE NOMOR NIS OTOMATIS (Cth: NIS-20260001)
        tahun_sekarang = datetime.now().year
        total_siswa = db.session.execute(db.select(func.count(Siswa.id))).scalar()
        nis_baru = f"NIS-{tahun_sekarang}{str(total_siswa + 1).zfill(4)}"

        # CARI ROLE ID FOR SISWA
        role_siswa = db.session.execute(db.select(Role).where(Role.name.ilike('%siswa%'))).scalar_one_or_none()
        role_id = role_siswa.id if role_siswa else 3  # Default fallback ke angka 3 kalau ga ketemu

        # BIKIN AKUN LOGIN SISWA DI TABEL USERS (Wajib karena NOT NULL di DB)
        user_siswa = User(
            name=calon.nama_lengkap,
            username=nis_baru,  # Username pake nomor NIS
            email=calon.email or f"{nis_baru}@school.id",
            password=generate_password_hash("siswa123"),  # Default password
            role_id=role_id
        )
        db.session.add(user_siswa)
        db.session.flush()  # get user_siswa.id dulu

        # KKLONING DATA MASUK KE TABEL UTAMA SISWA
        siswa_baru = Siswa(
            nis=nis_baru,
            nama_siswa=calon.nama_lengkap,
            jenis_kelamin=calon.jenis_kelamin,
            tanggal_lahir=calon.tanggal_lahir,
            kelas_id=kelas_id,
            status='aktif',
            user_id=user_siswa.id
        )
        db.session.add(siswa_baru)
        db.session.flush() # get id siswa

        # generate spp 12 bulan kedepan
        get_spp = db.select(Spp).where(
            Spp.tahun_ajaran_id == pendaftaran.tahun_ajaran_id,
            db.or_(Spp.jurusan_id == pendaftaran.jurusan_id, Spp.jurusan_id == None)
        ).order_by(Spp.jurusan_id.desc())

        master_spp = db.session.execute(get_spp).scalars().first()
        nominal_spp = master_spp.jumlah if master_spp else 0

        # ambil tahun awal dari string Tahun Ajaran "2026/2027" -> ambil 2026-nya
        try:
            tahun_awal = int(pendaftaran.tahun_ajaran.tahun.split('/')[0])
        except:
            tahun_awal = datetime.now().year  # Fallback

        # looping 12 Bulan (Juli ke Juni tahun depan)
        for i in range(12):
            bulan_tagihan = 7 + i
            tahun_tagihan = tahun_awal

            # Kalau bulannya udah lewat Desember (12), balikin ke Januari (1) dan tahunnya +1
            if bulan_tagihan > 12:
                bulan_tagihan -= 12
                tahun_tagihan += 1

                # Bikin Invoice Induk
            invoice_baru = Invoice(
                siswa_id=siswa_baru.id,
                bulan=bulan_tagihan,
                tahun=tahun_tagihan,
                total=nominal_spp,
                status='unpaid'
            )
            db.session.add(invoice_baru)
            db.session.flush()  # Flush lagi biar dapet ID invoice_baru buat itemnya

            # Bikin Detail Item Invoicenya biar rapi
            nama_bulan = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
                          "September", "Oktober", "November", "Desember"]
            item_baru = InvoiceItem(
                invoice_id=invoice_baru.id,
                nama_item=f"Pembayaran SPP Bulan {nama_bulan[bulan_tagihan]} {tahun_tagihan}",
                jumlah=nominal_spp
            )
            db.session.add(item_baru)

        # UBAH STATUS PENDAFTARAN JADI DITERIMA
        pendaftaran.status = 'diterima'
        db.session.commit()

        msg, cat = f"<b>{calon.nama_lengkap}</b> resmi jadi siswa aktif dengan NIS: <b>{nis_baru}</b>.", "success"
    except Exception as e:
        db.session.rollback()
        msg, cat = f"Gagal aktivasi siswa. Error: {str(e)}", "danger"

    # Re-render partial tabel pendaftaran biar laporannya keupdate otomatis
    stmt = db.select(Pendaftaran).order_by(Pendaftaran.id.desc()).limit(PER_PAGE)
    daftar_pendaftaran = db.session.execute(stmt).scalars().all()
    return render_template('akademik/_daftar_pendaftaran.html',
                           daftar_pendaftaran=daftar_pendaftaran, current_page=1, total_pages=1, per_page=PER_PAGE,
                           search="",
                           alert_message=msg, alert_category=cat)

# laporan
@akademik_bp.route('/laporan/pendaftaran', methods=['GET'])
@login_required
def laporan_pendaftaran():
    tahun_aktif = db.session.scalars(
        db.select(TahunAjaran).where(TahunAjaran.is_active == True)
    ).first()

    # kalau belum ada yang diset aktif, ambil tahun pendaftaran terbaru
    if not tahun_aktif:
        tahun_aktif = db.session.scalars(
            db.select(TahunAjaran).order_by(TahunAjaran.id.desc())
        ).first()

    if not tahun_aktif:
        flash("Tahun ajaran belum dibuat!", "warning")
        return redirect(url_for('akademik.pembayaran_spp'))

    # hitung statistik berdasarkan Status Pendaftaran (pending, diterima, dll)
    query_status = db.session.query(
        Pendaftaran.status,
        func.count(Pendaftaran.id).label('jumlah')
    ).filter(Pendaftaran.tahun_ajaran_id == tahun_aktif.id) \
        .group_by(Pendaftaran.status).all()

    # convert hasil query tuple jadi dictionary biar gampang dipanggil di HTML template
    stats_status = {row.status: row.jumlah for row in query_status}
    stats_status['total'] = sum(stats_status.values())

    # hitung pendaftar per Jurusan
    query_jurusan = db.session.query(
        Jurusan.nama_jurusan,
        func.count(Pendaftaran.id).label('jumlah')
    ).join(Pendaftaran, Pendaftaran.jurusan_id == Jurusan.id) \
        .filter(Pendaftaran.tahun_ajaran_id == tahun_aktif.id) \
        .group_by(Jurusan.nama_jurusan).all()

    return render_template('akademik/laporan_pendaftaran.html',
                           tahun_aktif=tahun_aktif,
                           stats_status=stats_status,
                           laporan_jurusan=query_jurusan)

@akademik_bp.route('/laporan/pendaftaran/export', methods=['GET'])
@login_required
def export_laporan_pendaftaran():
    tahun_aktif = db.session.scalars(
        db.select(TahunAjaran).where(TahunAjaran.is_active == True)
    ).first()

    if not tahun_aktif:
        tahun_aktif = db.session.scalars(
            db.select(TahunAjaran).order_by(TahunAjaran.id.desc())
        ).first()

    query_jurusan = db.session.query(
        Jurusan.nama_jurusan,
        func.count(Pendaftaran.id).label('jumlah')
    ).join(Pendaftaran, Pendaftaran.jurusan_id == Jurusan.id)\
     .filter(Pendaftaran.tahun_ajaran_id == tahun_aktif.id)\
     .group_by(Jurusan.nama_jurusan).all()

    # file Excel pake openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rekap PPDB"

    # judul di baris atas
    ws.append([f"LAPORAN PENDAFTARAN SISWA BARU - TA {tahun_aktif.tahun}"])
    ws.append([]) # kosong buat jarak

    # Header Tabel
    headers = ["No", "Nama Jurusan", "Jumlah Pendaftar"]
    ws.append(headers)

    # Looping data pendaftar
    for index, row in enumerate(query_jurusan, start=1):
        ws.append([index, row.nama_jurusan, f"{row.jumlah} Siswa"])

    # simpan ke memory buffer biar instan ga nyampah di storage server
    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    # kirim file ke browser buat otomatis didownload
    nama_file = f"Laporan_PPDB_{tahun_aktif.tahun.replace('/', '_')}.xlsx"
    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nama_file
    )