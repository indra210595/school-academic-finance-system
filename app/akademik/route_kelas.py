from flask import render_template, request, url_for
from flask_login import login_required
from app import db
from app.models import Kelas, Jurusan, TahunAjaran, Siswa
from app.akademik import akademik_bp
from sqlalchemy import func
import time

PER_PAGE = 5

@akademik_bp.route('/kelas', methods=['GET', 'POST'])
@login_required
def kelas():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    # Ambil data buat ngisi dropdown select di form kiri
    jurusans = db.session.execute(db.select(Jurusan).order_by(Jurusan.nama_jurusan)).scalars().all()
    tahun_ajarans = db.session.execute(db.select(TahunAjaran).order_by(TahunAjaran.tahun.desc())).scalars().all()

    if request.method == 'POST':
        nama_kelas = request.form.get('nama_kelas')
        jurusan_id = int(request.form.get('jurusan_id'))
        tahun_ajaran_id = int(request.form.get('tahun_ajaran_id'))

        time.sleep(0.5)

        # Cek duplikat: Kelas dengan nama yang sama di tahun ajaran yang sama
        cek = db.session.execute(
            db.select(Kelas).where(Kelas.nama_kelas == nama_kelas, Kelas.tahun_ajaran_id == tahun_ajaran_id)
        ).scalar_one_or_none()

        if cek:
            daftar = db.session.execute(db.select(Kelas).order_by(Kelas.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
            return render_template('akademik/_daftar_kelas.html',
                                   daftar_kelas=daftar, current_page=1, total_pages=1, per_page=PER_PAGE, search="",
                                   alert_message=f"Gagal! Kelas <b>{nama_kelas}</b> sudah ada di tahun ajaran tersebut.", alert_category="danger")

        # Simpan data baru
        baru = Kelas(nama_kelas=nama_kelas, jurusan_id=jurusan_id, tahun_ajaran_id=tahun_ajaran_id)
        db.session.add(baru)
        db.session.commit()

        total_data = db.session.execute(db.select(func.count(Kelas.id))).scalar()
        total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
        daftar = db.session.execute(db.select(Kelas).order_by(Kelas.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
        return render_template('akademik/_daftar_kelas.html',
                               daftar_kelas=daftar, current_page=1, total_pages=total_pages, per_page=PER_PAGE, search="",
                               alert_message=f"Sip! Kelas <b>{baru.nama_kelas}</b> berhasil ditambahkan.", alert_category="success")

    # GET
    stmt = db.select(Kelas).order_by(Kelas.id.desc())
    count_stmt = db.select(func.count(Kelas.id))

    if search_query:
        stmt = stmt.where(Kelas.nama_kelas.ilike(f"%{search_query}%"))
        count_stmt = count_stmt.where(Kelas.nama_kelas.ilike(f"%{search_query}%"))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/kelas.html',
                           daftar_kelas=daftar, list_jurusan=jurusans, list_ta=tahun_ajarans,
                           current_page=page, total_pages=total_pages, per_page=PER_PAGE, search=search_query)


# search
@akademik_bp.route('/kelas/tabel', methods=['GET'])
@login_required
def kelas_tabel():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    stmt = db.select(Kelas).order_by(Kelas.id.desc())
    count_stmt = db.select(func.count(Kelas.id))

    if search_query:
        stmt = stmt.where(Kelas.nama_kelas.ilike(f"%{search_query}%"))
        count_stmt = count_stmt.where(Kelas.nama_kelas.ilike(f"%{search_query}%"))

    total_data = db.session.execute(count_stmt).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

    return render_template('akademik/_daftar_kelas.html',
                           daftar_kelas=daftar, current_page=page, total_pages=total_pages, per_page=PER_PAGE, search=search_query)


# edit
@akademik_bp.route('/kelas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_kelas(id):
    target = db.session.get(Kelas, id)
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    offset = (page - 1) * PER_PAGE

    if request.method == 'POST':
        nama_kelas = request.form.get('nama_kelas')
        jurusan_id = int(request.form.get('jurusan_id'))
        tahun_ajaran_id = int(request.form.get('tahun_ajaran_id'))

        # Cek duplikat & (abaikan ID yang lagi diedit)
        cek = db.session.execute(
            db.select(Kelas).where(Kelas.nama_kelas == nama_kelas, Kelas.tahun_ajaran_id == tahun_ajaran_id,
                                   Kelas.id != id)
        ).scalar_one_or_none()

        if cek:
            stmt = db.select(Kelas).order_by(Kelas.id.desc())
            if search_query:
                stmt = stmt.where(Kelas.nama_kelas.ilike(f"%{search_query}%"))
            daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

            return render_template('akademik/_daftar_kelas.html',
                                   daftar_kelas=daftar, current_page=page, total_pages=1, per_page=PER_PAGE,
                                   search=search_query,
                                   alert_message=f"Gagal! Kelas <b>{nama_kelas}</b> sudah ada di tahun ajaran tersebut.",
                                   alert_category="danger")

        # update data
        target.nama_kelas = nama_kelas
        target.jurusan_id = jurusan_id
        target.tahun_ajaran_id = tahun_ajaran_id
        db.session.commit()

        # Ambil data terbaru buat re-render tabel utuh
        stmt = db.select(Kelas).order_by(Kelas.id.desc())
        count_stmt = db.select(func.count(Kelas.id))
        if search_query:
            stmt = stmt.where(Kelas.nama_kelas.ilike(f"%{search_query}%"))
            count_stmt = count_stmt.where(Kelas.nama_kelas.ilike(f"%{search_query}%"))

        total_data = db.session.execute(count_stmt).scalar()
        total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
        daftar = db.session.execute(stmt.limit(PER_PAGE).offset(offset)).scalars().all()

        return render_template('akademik/_daftar_kelas.html',
                               daftar_kelas=daftar, current_page=page, total_pages=total_pages, per_page=PER_PAGE,
                               search=search_query,
                               alert_message=f"Sip! Data kelas <b>{target.nama_kelas}</b> berhasil diperbarui.",
                               alert_category="success")

    # GET
    no = request.args.get('no', '')
    jurusans = db.session.execute(db.select(Jurusan).order_by(Jurusan.nama_jurusan)).scalars().all()
    tahun_ajarans = db.session.execute(db.select(TahunAjaran).order_by(TahunAjaran.tahun.desc())).scalars().all()

    # Bikin list option buat dropdown Jurusan (Otomatis kekunci yang lagi kepilih)
    options_jurusan = "".join(
        f'<option value="{j.id}" {"selected" if target.jurusan_id == j.id else ""}>{j.nama_jurusan}</option>'
        for j in jurusans
    )

    # Bikin list option buat dropdown Tahun Ajaran
    options_ta = "".join(
        f'<option value="{ta.id}" {"selected" if target.tahun_ajaran_id == ta.id else ""}>{ta.tahun} {"(Aktif)" if ta.is_active else ""}</option>'
        for ta in tahun_ajarans
    )

    return f"""
    <tr id="baris-kelas-{target.id}" class="table-warning-subtle">
        <td>{no}</td>
        <td>
            <input type="text" class="form-control form-control-sm fw-bold" name="nama_kelas" value="{target.nama_kelas}" form="form-edit-kelas-{target.id}" required>
        </td>
        <td>
            <select class="form-select form-select-sm fw-bold" name="jurusan_id" form="form-edit-kelas-{target.id}" required>
                {options_jurusan}
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm fw-bold" name="tahun_ajaran_id" form="form-edit-kelas-{target.id}" required>
                {options_ta}
            </select>
        </td>
        <td class="text-center">
            <form id="form-edit-kelas-{target.id}" 
                  hx-post="{url_for('akademik.edit_kelas', id=target.id)}?page={page}&search={search_query}" 
                  hx-target="#bagian-tabel-kelas" 
                  hx-swap="innerHTML">
            </form>
            <button type="submit" form="form-edit-kelas-{target.id}" class="btn btn-sm btn-success fw-bold me-1">Simpan</button>
            <button type="button" 
                    hx-get="{url_for('akademik.kelas_tabel')}?page={page}&search={search_query}" 
                    hx-target="#bagian-tabel-kelas" 
                    hx-swap="innerHTML" 
                    class="btn btn-sm btn-secondary fw-bold">
                Batal
            </button>
        </td>
    </tr>
    """.strip()

@akademik_bp.route('/kelas/<int:id>', methods=['DELETE'])
@login_required
def hapus_kelas(id):
    target = db.session.get(Kelas, id)
    if target:
        db.session.delete(target)
        db.session.commit()
    return ""

# rollover kelas
@akademik_bp.route('/kelas/roll-over', methods=['POST'])
@login_required
def roll_over_kelas():
    ta_asal_id = int(request.form.get('ta_asal_id'))
    ta_tujuan_id = int(request.form.get('ta_tujuan_id'))

    time.sleep(0.8)

    # cegah admin milih tahun asal dan tujuan yang sama
    if ta_asal_id == ta_tujuan_id:
        daftar = db.session.execute(
            db.select(Kelas).order_by(Kelas.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
        return render_template('akademik/_daftar_kelas.html',
                               daftar_kelas=daftar, current_page=1, total_pages=1, per_page=PER_PAGE, search="",
                               alert_message="<b>Gagal!</b> Tahun ajaran asal dan tujuan gak boleh sama.",
                               alert_category="danger")

    # ambil seluruh data kelas dari tahun ajaran asal
    kelas_asal = db.session.execute(db.select(Kelas).where(Kelas.tahun_ajaran_id == ta_asal_id)).scalars().all()

    if not kelas_asal:
        daftar = db.session.execute(
            db.select(Kelas).order_by(Kelas.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()
        return render_template('akademik/_daftar_kelas.html',
                               daftar_kelas=daftar, current_page=1, total_pages=1, per_page=PER_PAGE, search="",
                               alert_message="<b>Error!</b> Gak ada data kelas yang bisa disalin di tahun ajaran asal tersebut.",
                               alert_category="warning")

    jumlah_disalin = 0

    # proses cloning masal anti-duplikat
    for k in kelas_asal:
        # ngecek apakah nama kelas tersebut udah dibikin di tahun ajaran tujuan
        ada = db.session.execute(
            db.select(Kelas).where(Kelas.nama_kelas == k.nama_kelas, Kelas.tahun_ajaran_id == ta_tujuan_id)
        ).scalar_one_or_none()

        # kalo belum ada, buat baru clone-nya
        if not ada:
            kelas_baru = Kelas(nama_kelas=k.nama_kelas, jurusan_id=k.jurusan_id, tahun_ajaran_id=ta_tujuan_id)
            db.session.add(kelas_baru)
            jumlah_disalin += 1

    # commit ke database jika ada data baru yang dicloning
    if jumlah_disalin > 0:
        db.session.commit()
        msg = f"Sukses menduplikat massal <b>{jumlah_disalin} kelas</b> ke periode tahun ajaran baru."
        cat = "success"
    else:
        msg = "Info: Gak ada kelas baru yang disalin (semua struktur kelas dari tahun asal emang udah terdaftar di tahun tujuan)."
        cat = "info"

    # ambil data terbaru buat re-render partial tabel kanan (balik ke page 1 biar keliatan hasilnya)
    total_data = db.session.execute(db.select(func.count(Kelas.id))).scalar()
    total_pages = (total_data + PER_PAGE - 1) // PER_PAGE
    daftar = db.session.execute(db.select(Kelas).order_by(Kelas.id.desc()).limit(PER_PAGE).offset(0)).scalars().all()

    return render_template('akademik/_daftar_kelas.html',
                           daftar_kelas=daftar, current_page=1, total_pages=total_pages, per_page=PER_PAGE, search="",
                           alert_message=msg, alert_category=cat)

# kenaikan kelas
@akademik_bp.route('/kenaikan-kelas', methods=['GET'])
@login_required
def kenaikan_kelas():
    tahun_ajarans = db.session.execute(
        db.select(TahunAjaran).order_by(TahunAjaran.tahun.desc())
    ).scalars().all()
    return render_template('akademik/kenaikan_kelas.html', tahun_ajarans=tahun_ajarans)


@akademik_bp.route('/kenaikan-kelas/ambil-kelas', methods=['GET'])
@login_required
def ambil_kelas_dropdown():
    ta_id = request.args.get('ta_asal_id', type=int) or request.args.get('ta_tujuan_id', type=int)
    tipe = request.args.get('tipe', 'asal')  # asal atau tujuan

    if not ta_id:
        return f'<option value="">Pilih Tahun Ajaran {tipe.capitalize()} Dulu</option>'

    # Ambil kelas yang terdaftar di TA terpilih
    list_kelas = db.session.execute(
        db.select(Kelas).where(Kelas.tahun_ajaran_id == ta_id).order_by(Kelas.nama_kelas)
    ).scalars().all()

    html = f'<option value="">-- Pilih Kelas {tipe.capitalize()} --</option>'
    for k in list_kelas:
        html += f'<option value="{k.id}">{k.nama_kelas}</option>'
    return html


@akademik_bp.route('/kenaikan-kelas/list-siswa', methods=['GET'])
@login_required
def kenaikan_list_siswa():
    kelas_asal_id = request.args.get('kelas_asal_id', type=int)
    if not kelas_asal_id:
        return '<p class="text-muted text-center my-3">Pilih kelas asal untuk lihat daftar siswa.</p>'

    # ambil siswa yang ada di kelas asal
    list_siswa = db.session.execute(
        db.select(Siswa).where(Siswa.kelas_id == kelas_asal_id).order_by(Siswa.id)
    ).scalars().all()

    if not list_siswa:
        return '<div class="alert alert-warning text-center">Tidak ada siswa aktif di kelas ini.</div>'

    # list siswa
    html = '<ol class="list-group list-group-numbered">'
    for s in list_siswa:
        html += f'<li class="list-group-item d-flex justify-content-between align-items-start">{s.nama_siswa}</li>'
    html += '</ol>'
    return html


@akademik_bp.route('/kenaikan-kelas/proses', methods=['POST'])
@login_required
def proses_kenaikan_kelas():
    kelas_asal_id = request.form.get('kelas_asal_id', type=int)
    kelas_tujuan_id = request.form.get('kelas_tujuan_id', type=int)

    if not kelas_asal_id or not kelas_tujuan_id:
        return '<div class="alert alert-danger fw-bold">Kelas asal dan kelas tujuan wajib diisi!</div>'

    if kelas_asal_id == kelas_tujuan_id:
        return '<div class="alert alert-danger fw-bold">Kelas asal dan tujuan tidak boleh sama!</div>'

    siswa_asal = db.session.execute(
        db.select(Siswa).where(Siswa.kelas_id == kelas_asal_id)
    ).scalars().all()

    if not siswa_asal:
        return '<div class="alert alert-warning fw-bold">Tidak ada data siswa yang bisa dipindahkan dari kelas asal.</div>'

    jumlah_siswa = len(siswa_asal)
    for s in siswa_asal:
        s.kelas_id = kelas_tujuan_id

    db.session.commit()

    return f"""
    <div class="alert alert-success shadow-sm border-0 d-flex align-items-center" role="alert">
        <div>
            <i class="fa-solid fa-circle-check me-2 fs-5"></i> 
            <b>Berhasil!</b> Sebanyak <b>{jumlah_siswa} siswa</b> resmi naik/pindah kelas.
        </div>
    </div>
    <script>
        document.getElementById('daftar-siswa-container').innerHTML = '<div class="alert alert-info text-center">Siswa sudah dipindahkan. Silakan pilih kelas lain.</div>';
    </script>
    """