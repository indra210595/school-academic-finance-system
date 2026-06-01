from app import db  # instance db dari __init__.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, DateTime, Date, Numeric, Boolean
from datetime import datetime, date
from typing import List
from flask_login import UserMixin

class Role(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # 1 role bisa banyak user
    users: Mapped[List["User"]] = relationship("User", back_populates="role")
    user_roles: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="role")

class User(UserMixin,db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    user_roles: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="user")
    guru: Mapped["Guru"] = relationship("Guru", back_populates="user", uselist=False)
    siswa: Mapped["Siswa"] = relationship("Siswa", back_populates="user", uselist=False)
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="user")

class UserRole(db.Model):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

class TahunAjaran(db.Model):
    __tablename__ = "tahun_ajaran"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tahun: Mapped[str] = mapped_column(String(255), nullable=False)
    start_month: Mapped[int] = mapped_column(Integer, nullable=False)
    end_month: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    kelas_list: Mapped[List["Kelas"]] = relationship("Kelas", back_populates="tahun_ajaran")
    spp_list: Mapped[List["Spp"]] = relationship("Spp", back_populates="tahun_ajaran")


class Jurusan(db.Model):
    __tablename__ = "jurusan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nama_jurusan: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    deskripsi: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    kelas_list: Mapped[List["Kelas"]] = relationship("Kelas", back_populates="jurusan")
    spp_list: Mapped[List["Spp"]] = relationship("Spp", back_populates="jurusan")

class Kelas(db.Model):
    __tablename__ = "kelas"

    __table_args__ = (
        db.UniqueConstraint('nama_kelas', 'tahun_ajaran_id', name='unique_kelas_per_tahun'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nama_kelas: Mapped[str] = mapped_column(String(255), nullable=False)
    jurusan_id: Mapped[int] = mapped_column(Integer, ForeignKey('jurusan.id', ondelete='CASCADE'), nullable=False)
    tahun_ajaran_id: Mapped[int] = mapped_column(Integer, ForeignKey('tahun_ajaran.id', ondelete='CASCADE'),
                                                 nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    jurusan: Mapped["Jurusan"] = relationship("Jurusan", back_populates="kelas_list")
    tahun_ajaran: Mapped["TahunAjaran"] = relationship("TahunAjaran", back_populates="kelas_list")
    siswa_list: Mapped[List["Siswa"]] = relationship("Siswa", back_populates="kelas")


class MataPelajaran(db.Model):
    __tablename__ = "mata_pelajaran"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nama_mapel: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    deskripsi: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    guru_mapel_list: Mapped[List["GuruMapel"]] = relationship("GuruMapel", back_populates="mata_pelajaran")


class Guru(db.Model):
    __tablename__ = "guru"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nama_guru: Mapped[str] = mapped_column(String(255), nullable=False)
    jenis_kelamin: Mapped[str] = mapped_column(String(255), nullable=False)
    checkpoint_lahir: Mapped[date] = mapped_column(Date, name="tanggal_lahir", nullable=True)
    telepon: Mapped[str] = mapped_column(String(255), nullable=True)
    alamat: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    user: Mapped["User"] = relationship("User", back_populates="guru")
    mapel_list: Mapped[List["GuruMapel"]] = relationship("GuruMapel", back_populates="guru")


class GuruMapel(db.Model):
    __tablename__ = "guru_mapel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guru_id: Mapped[int] = mapped_column(Integer, ForeignKey('guru.id', ondelete='CASCADE'), nullable=False)
    mata_pelajaran_id: Mapped[int] = mapped_column(Integer, ForeignKey('mata_pelajaran.id', ondelete='CASCADE'),
                                                   nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    guru: Mapped["Guru"] = relationship("Guru", back_populates="mapel_list")
    mata_pelajaran: Mapped["MataPelajaran"] = relationship("MataPelajaran", back_populates="guru_mapel_list")


class WaliKelas(db.Model):
    __tablename__ = "wali_kelas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guru_id: Mapped[int] = mapped_column(Integer, ForeignKey('guru.id', ondelete='CASCADE'), nullable=False)
    kelas_id: Mapped[int] = mapped_column(Integer, ForeignKey('kelas.id', ondelete='CASCADE'), nullable=False)
    tahun_ajaran_id: Mapped[int] = mapped_column(Integer, ForeignKey('tahun_ajaran.id', ondelete='CASCADE'),
                                                 nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    guru: Mapped["Guru"] = relationship("Guru")
    kelas: Mapped["Kelas"] = relationship("Kelas")
    tahun_ajaran: Mapped["TahunAjaran"] = relationship("TahunAjaran")


class Siswa(db.Model):
    __tablename__ = "siswa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nis: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nama_siswa: Mapped[str] = mapped_column(String(255), nullable=False)
    jenis_kelamin: Mapped[str] = mapped_column(String(255), nullable=False)
    tanggal_lahir: Mapped[date] = mapped_column(Date, nullable=True)
    kelas_id: Mapped[int] = mapped_column(Integer, ForeignKey('kelas.id', ondelete='CASCADE'), nullable=False)
    status: Mapped[str] = mapped_column(String(255), default="aktif", nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    kelas: Mapped["Kelas"] = relationship("Kelas", back_populates="siswa_list")
    user: Mapped["User"] = relationship("User", back_populates="siswa")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="siswa")


class Pendaftaran(db.Model):
    __tablename__ = "pendaftaran"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nomor: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tahun_ajaran_id: Mapped[int] = mapped_column(Integer, ForeignKey('tahun_ajaran.id'), nullable=False)
    jurusan_id: Mapped[int] = mapped_column(Integer, ForeignKey('jurusan.id'), nullable=False)
    tanggal_daftar: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(255), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    jurusan = db.relationship('Jurusan', backref='all_pendaftaran')
    tahun_ajaran = db.relationship('TahunAjaran', backref='all_pendaftaran')
    calon_siswa = db.relationship('CalonSiswa', back_populates='pendaftaran', uselist=False, cascade='all, delete-orphan')


class CalonSiswa(db.Model):
    __tablename__ = "calon_siswa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pendaftaran_id = db.Column(db.BigInteger, db.ForeignKey('pendaftaran.id'), nullable=False)
    nama_lengkap: Mapped[str] = mapped_column(String(255), nullable=False)
    jenis_kelamin: Mapped[str] = mapped_column(String(255), nullable=False)
    tempat_lahir: Mapped[str] = mapped_column(String(255), nullable=False)
    tanggal_lahir: Mapped[date] = mapped_column(Date, nullable=False)
    agama: Mapped[str] = mapped_column(String(255), nullable=True)
    asal_sekolah: Mapped[str] = mapped_column(String(255), nullable=False)
    telepon = db.Column(db.String(20))
    email = db.Column(db.String(100))  # Buat kirim hasil pengumuman otomatis ntar

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    pendaftaran = db.relationship('Pendaftaran', back_populates='calon_siswa')
    orang_tua_list = db.relationship('OrangTua', back_populates='calon_siswa', cascade='all, delete-orphan')


class OrangTua(db.Model):
    __tablename__ = "orang_tua"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    calon_siswa_id: Mapped[int] = mapped_column(Integer, ForeignKey('calon_siswa.id', ondelete='CASCADE'),
                                                nullable=False)
    tipe: Mapped[str] = mapped_column(String(255), nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    tanggal_lahir: Mapped[date] = mapped_column(Date, nullable=True)
    pendidikan: Mapped[str] = mapped_column(String(255), nullable=True)
    pekerjaan: Mapped[str] = mapped_column(String(255), nullable=True)
    telepon: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    calon_siswa: Mapped["CalonSiswa"] = relationship("CalonSiswa", back_populates="orang_tua_list")

class Spp(db.Model):
    __tablename__ = "spp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tahun_ajaran_id: Mapped[int] = mapped_column(Integer, ForeignKey('tahun_ajaran.id', ondelete='CASCADE'),
                                                 nullable=False)
    jurusan_id: Mapped[int] = mapped_column(Integer, ForeignKey('jurusan.id', ondelete='SET NULL'), nullable=True)
    jumlah: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)
    # relasi
    tahun_ajaran: Mapped["TahunAjaran"] = relationship("TahunAjaran", back_populates="spp_list")
    jurusan: Mapped["Jurusan"] = relationship("Jurusan", back_populates="spp_list")



class Invoice(db.Model):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    siswa_id: Mapped[int] = mapped_column(Integer, ForeignKey('siswa.id', ondelete='CASCADE'), nullable=False)
    bulan: Mapped[int] = mapped_column(Integer, nullable=False)
    tahun: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(255), default="unpaid", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    siswa: Mapped["Siswa"] = relationship("Siswa", back_populates="invoices")
    items: Mapped[List["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="invoice")


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    nama_item: Mapped[str] = mapped_column(String(255), nullable=False)
    jumlah: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # relasi
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")


class Payment(db.Model):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    tanggal: Mapped[date] = mapped_column(Date, nullable=False)
    jumlah: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)

    # relasi
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
    user: Mapped["User"] = relationship("User", back_populates="payments")


class Alamat(db.Model):
    __tablename__ = "alamat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipe: Mapped[str] = mapped_column(String(255), nullable=False)
    ref_id: Mapped[int] = mapped_column(Integer, nullable=False)
    alamat: Mapped[str] = mapped_column(String, nullable=False)
    kelurahan: Mapped[str] = mapped_column(String(255), nullable=True)
    kecamatan: Mapped[str] = mapped_column(String(255), nullable=True)
    kota: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=True)