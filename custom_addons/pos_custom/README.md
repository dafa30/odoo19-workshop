# Workshop — Smart POS & Loyalty Point dengan Odoo 19

Modul custom Odoo 19 untuk membangun fitur **Loyalty Point** pada Point of Sale dari nol.

---

## Prasyarat

- Odoo 19 sudah terinstall dan berjalan
- Modul `point_of_sale` dan `contacts` aktif
- Akses ke folder `addons` Odoo

---

## Struktur Folder (Final)

```
pos_custom/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_partner.py
│   ├── loyalty_history.py
│   ├── loyalty_reward_product.py
│   └── pos_order.py
├── wizards/
│   ├── __init__.py
│   └── loyalty_redeem_wizard.py
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
└── views/
    ├── res_partner_views.xml
    ├── loyalty_history_views.xml
    ├── loyalty_reward_product_views.xml
    └── loyalty_redeem_wizard_views.xml
```

---

---

# DAY 1 — Module Structure, Models & Views

---

## Langkah 1 — Persiapan Folder

Buat folder modul di dalam direktori `addons` Odoo:

```
odoo19/
└── addons/
    └── pos_custom/
```

Buat subfolder yang dibutuhkan:

```
pos_custom/models/
pos_custom/views/
pos_custom/security/
```

---

## Langkah 2 — Module Manifest (`__manifest__.py`)

File manifest adalah identitas modul. Odoo membaca file ini untuk mengenali nama, versi, dependensi, dan file data yang perlu dimuat.

**File:** `__manifest__.py`

```python
{
    'name': 'Smart POS & Loyalty Point',
    'version': '19.0.1.0.0',
    'author': 'Custom Dev',
    'summary': 'Tambah fitur Loyalty Point pada Point of Sale',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/loyalty_history_views.xml',
        'views/loyalty_reward_product_views.xml',
        'views/loyalty_redeem_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

**Penjelasan `depends`:**

| Modul | Alasan |
|---|---|
| `base` | Menyediakan model dasar seperti `res.partner` |
| `point_of_sale` | Menyediakan model `pos.order` dan menu POS |
| `contacts` | Menyediakan UI form pelanggan yang akan kita inherit |

> **Penting:** Urutan `data` sangat berpengaruh. `security.xml` harus dimuat sebelum `ir.model.access.csv` karena CSV mereferensi group yang didefinisikan di XML.

**File:** `__init__.py` (root)

```python
from . import models
from . import wizards
```

---

## Langkah 3 — Model Inheritance & Custom Model

### 3a. Inherit Model Pelanggan (`res.partner`)

**File:** `models/res_partner.py`

```python
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Integer(string='Loyalty Points', default=0)

    def action_redeem_points(self):
        self.ensure_one()
        return {
            'name': 'Redeem Loyalty Points',
            'type': 'ir.actions.act_window',
            'res_model': 'loyalty.redeem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }
```

**Konsep `_inherit`:**
- Tidak membuat tabel baru di database
- Menambahkan kolom `loyalty_points` ke tabel `res_partner` yang sudah ada
- Method `action_redeem_points` membuka popup wizard redeem

---

### 3b. Model Riwayat Poin (`loyalty.point.history`)

**File:** `models/loyalty_history.py`

```python
from odoo import fields, models


class LoyaltyPointHistory(models.Model):
    _name = 'loyalty.point.history'
    _description = 'Loyalty Point History'
    _order = 'date desc'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, ondelete='cascade')
    pos_order_id = fields.Many2one('pos.order', string='POS Order', ondelete='set null')
    points = fields.Integer(string='Points', required=True)
    type = fields.Selection([
        ('earn', 'Earn'),
        ('redeem', 'Redeem'),
    ], string='Type', required=True)
    product_id = fields.Many2one('product.product', string='Reward Product', ondelete='set null')
    notes = fields.Char(string='Notes')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
```

**Penjelasan Fields:**

| Field | Tipe | Keterangan |
|---|---|---|
| `partner_id` | Many2one | Relasi ke pelanggan. Jika dihapus, riwayat ikut terhapus (`cascade`) |
| `pos_order_id` | Many2one | Relasi ke transaksi POS. Jika dihapus, field dikosongkan (`set null`) |
| `points` | Integer | Jumlah poin yang didapat atau ditukar |
| `type` | Selection | `earn` = dapat poin, `redeem` = tukar poin |
| `product_id` | Many2one | Produk reward yang diredeem (hanya terisi saat type=redeem) |
| `notes` | Char | Catatan transaksi |
| `date` | Datetime | Waktu transaksi, otomatis diisi saat record dibuat |

---

### 3c. Model Setting Reward Product (`loyalty.reward.product`)

Model baru untuk mengkonfigurasi produk apa saja yang bisa diredeem dan berapa poin yang dibutuhkan.

**File:** `models/loyalty_reward_product.py`

```python
from odoo import fields, models


class LoyaltyRewardProduct(models.Model):
    _name = 'loyalty.reward.product'
    _description = 'Loyalty Reward Product'
    _order = 'points_required asc'

    product_id = fields.Many2one(
        'product.product', string='Product', required=True, ondelete='cascade'
    )
    points_required = fields.Integer(string='Points Required', required=True, default=1)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('product_unique', 'unique(product_id)', 'Produk ini sudah terdaftar sebagai reward.'),
        ('points_positive', 'CHECK(points_required > 0)', 'Points harus lebih dari 0.'),
    ]
```

**File:** `models/__init__.py`

```python
from . import res_partner
from . import loyalty_history
from . import loyalty_reward_product
from . import pos_order
```

---

## Langkah 4 — Security Groups (`security/security.xml`)

Mendefinisikan grup pengguna custom yang muncul di Settings → Users sebagai section tersendiri.

**File:** `security/security.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <!-- Privilege — container di User Settings -->
        <record id="privilege_pos_custom" model="res.groups.privilege">
            <field name="name">Smart POS &amp; Loyalty Point</field>
            <field name="sequence">90</field>
            <field name="category_id" ref="base.module_category_point_of_sale"/>
        </record>

        <!-- Group Kasir -->
        <record id="group_pos_loyalty_user" model="res.groups">
            <field name="name">Kasir</field>
            <field name="sequence">10</field>
            <field name="privilege_id" ref="privilege_pos_custom"/>
            <field name="implied_ids" eval="[(4, ref('base.group_user')), (4, ref('point_of_sale.group_pos_user'))]"/>
        </record>

        <!-- Group Manajer -->
        <record id="group_pos_loyalty_manager" model="res.groups">
            <field name="name">Manajer</field>
            <field name="sequence">20</field>
            <field name="privilege_id" ref="privilege_pos_custom"/>
            <field name="implied_ids" eval="[(4, ref('group_pos_loyalty_user')), (4, ref('point_of_sale.group_pos_manager'))]"/>
            <field name="user_ids" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
        </record>
    </data>
</odoo>
```

**Hierarki Group:**

```
Manajer  →  implied  →  Kasir  →  implied  →  base.group_user
                                            →  group_pos_user
         →  implied  →  group_pos_manager
```

---

## Langkah 5 — Hak Akses (`security/ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_loyalty_point_history_user,loyalty.point.history user,model_loyalty_point_history,pos_custom.group_pos_loyalty_user,1,0,0,0
access_loyalty_point_history_manager,loyalty.point.history manager,model_loyalty_point_history,pos_custom.group_pos_loyalty_manager,1,1,1,1
access_loyalty_reward_product_user,loyalty.reward.product user,model_loyalty_reward_product,pos_custom.group_pos_loyalty_user,1,0,0,0
access_loyalty_reward_product_manager,loyalty.reward.product manager,model_loyalty_reward_product,pos_custom.group_pos_loyalty_manager,1,1,1,1
access_loyalty_redeem_wizard_user,loyalty.redeem.wizard user,model_loyalty_redeem_wizard,pos_custom.group_pos_loyalty_user,1,1,1,1
access_loyalty_redeem_wizard_manager,loyalty.redeem.wizard manager,model_loyalty_redeem_wizard,pos_custom.group_pos_loyalty_manager,1,1,1,1
```

**Ringkasan hak akses:**

| Model | Kasir | Manajer |
|---|---|---|
| `loyalty.point.history` | Read only | Full access |
| `loyalty.reward.product` | Read only | Full access |
| `loyalty.redeem.wizard` | Full access (perlu buat wizard) | Full access |

---

## Langkah 6 — Views

### 6a. Form Pelanggan (`views/res_partner_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_partner_form_loyalty" model="ir.ui.view">
        <field name="name">res.partner.form.loyalty</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_form"/>
        <field name="arch" type="xml">
            <xpath expr="//div[@name='button_box']" position="inside">
                <button name="action_redeem_points"
                        type="object"
                        string="Redeem Points"
                        class="oe_stat_button"
                        icon="fa-gift"
                        groups="pos_custom.group_pos_loyalty_manager"
                        invisible="loyalty_points == 0"/>
            </xpath>
            <xpath expr="//field[@name='category_id']" position="after">
                <field name="loyalty_points" readonly="1"/>
            </xpath>
        </field>
    </record>
</odoo>
```

**Dua xpath yang digunakan:**
- `button_box` → sisipkan tombol **Redeem Points** (hanya manajer, hilang jika poin = 0)
- `category_id` → sisipkan field `loyalty_points` (read-only untuk semua)

---

### 6b. Loyalty History (`views/loyalty_history_views.xml`)

Menampilkan riwayat transaksi poin dengan kolom `product_id` dan `notes`, serta badge berwarna untuk kolom `type`.

```xml
<list string="Loyalty Point History">
    <field name="date"/>
    <field name="partner_id"/>
    <field name="type" widget="badge"
           decoration-success="type == 'earn'"
           decoration-danger="type == 'redeem'"/>
    <field name="points"/>
    <field name="product_id"/>
    <field name="pos_order_id"/>
    <field name="notes"/>
</list>
```

---

### 6c. Reward Products (`views/loyalty_reward_product_views.xml`)

List editable untuk konfigurasi produk reward. Menu hanya muncul untuk Manajer.

```xml
<menuitem id="menu_loyalty_reward_product"
          name="Reward Products"
          parent="point_of_sale.menu_point_root"
          action="action_loyalty_reward_product"
          groups="pos_custom.group_pos_loyalty_manager"
          sequence="51"/>
```

---

---

# DAY 2 — POS Integration, Redeem Wizard & Security

---

## Langkah 1 — POS Integration: Override `action_pos_order_paid`

### Kenapa `action_pos_order_paid` bukan `_process_saved_order`?

Di Odoo 19, flow saat order dibayar adalah:

```
sync_from_ui()
  └─ _process_order()
       └─ _process_saved_order(draft=False)
            └─ action_pos_order_paid()   ← state berubah ke 'paid' DI SINI
                 └─ self.write({'state': 'paid'})
```

Jika override di `_process_saved_order`, `amount_total` belum tentu ter-commit ke DB karena field ini `readonly` dan dihitung via `_compute_prices` secara terpisah. Override di `action_pos_order_paid` lebih aman karena semua field sudah final saat method ini dipanggil.

**File:** `models/pos_order.py`

```python
from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_pos_order_paid(self):
        res = super().action_pos_order_paid()
        if self.partner_id and self.amount_total > 0 and not self.is_refund:
            points_earned = int(self.amount_total // 10000)
            if points_earned > 0:
                self.partner_id.sudo().loyalty_points += points_earned
                self.env['loyalty.point.history'].sudo().create({
                    'partner_id': self.partner_id.id,
                    'pos_order_id': self.id,
                    'points': points_earned,
                    'type': 'earn',
                })
        return res
```

**Logika perhitungan poin:**

| Kondisi | Keterangan |
|---|---|
| `self.partner_id` | Order harus memiliki pelanggan terpilih |
| `self.amount_total > 0` | Bukan order nol atau negatif |
| `not self.is_refund` | Tidak menambah poin saat transaksi refund |
| `amount_total // 10000` | Setiap kelipatan Rp 10.000 = 1 poin |
| `.sudo()` | Kasir mungkin tidak punya write access ke `res.partner` secara langsung |

**Contoh:**
- Transaksi Rp 150.000 → `150000 // 10000` = **15 poin**
- Transaksi Rp 9.999 → `9999 // 10000` = **0 poin** (tidak ada poin)

---

## Langkah 2 — Redeem Wizard (`wizards/loyalty_redeem_wizard.py`)

Wizard adalah `TransientModel` — record-nya otomatis dihapus setelah sesi berakhir. Digunakan untuk form popup sementara.

**File:** `wizards/__init__.py`

```python
from . import loyalty_redeem_wizard
```

**File:** `wizards/loyalty_redeem_wizard.py`

```python
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LoyaltyRedeemWizard(models.TransientModel):
    _name = 'loyalty.redeem.wizard'
    _description = 'Redeem Loyalty Points Wizard'

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    loyalty_points = fields.Integer(related='partner_id.loyalty_points', string='Available Points')
    reward_product_id = fields.Many2one(
        'loyalty.reward.product', string='Reward Product', required=True,
        domain="[('points_required', '<=', loyalty_points), ('active', '=', True)]"
    )
    product_name = fields.Char(related='reward_product_id.product_id.name', string='Product')
    points_required = fields.Integer(related='reward_product_id.points_required', string='Points Required')
    points_after = fields.Integer(compute='_compute_points_after', string='Points After Redeem')
    notes = fields.Char(string='Notes')

    @api.depends('loyalty_points', 'points_required')
    def _compute_points_after(self):
        for rec in self:
            rec.points_after = rec.loyalty_points - (rec.points_required or 0)

    def action_confirm(self):
        self.ensure_one()
        if not self.reward_product_id:
            raise UserError(_('Pilih produk reward terlebih dahulu.'))
        if self.partner_id.loyalty_points < self.reward_product_id.points_required:
            raise ValidationError(_(
                'Poin tidak cukup. Dibutuhkan %(required)s poin, tersedia %(available)s poin.',
                required=self.reward_product_id.points_required,
                available=self.partner_id.loyalty_points,
            ))
        self.env['loyalty.point.history'].sudo().create({
            'partner_id': self.partner_id.id,
            'points': self.reward_product_id.points_required,
            'type': 'redeem',
            'product_id': self.reward_product_id.product_id.id,
            'notes': self.notes or (_('Redeem: %s') % self.reward_product_id.product_id.name),
        })
        self.partner_id.sudo().loyalty_points -= self.reward_product_id.points_required
        return {'type': 'ir.actions.act_window_close'}
```

**Fitur wizard:**

| Field | Keterangan |
|---|---|
| `loyalty_points` | Related field — otomatis ambil poin terkini dari pelanggan |
| `domain` pada `reward_product_id` | Filter otomatis: hanya tampilkan produk yang poinnya ≤ poin pelanggan |
| `points_after` | Computed field — preview sisa poin setelah redeem |
| `action_confirm` | Validasi ganda + buat history + kurangi poin |

---

## Langkah 3 — Wizard View (`views/loyalty_redeem_wizard_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_loyalty_redeem_wizard_form" model="ir.ui.view">
        <field name="name">loyalty.redeem.wizard.form</field>
        <field name="model">loyalty.redeem.wizard</field>
        <field name="arch" type="xml">
            <form string="Redeem Loyalty Points">
                <sheet>
                    <group string="Customer Info">
                        <field name="partner_id" readonly="1"/>
                        <field name="loyalty_points" readonly="1"/>
                    </group>
                    <group string="Pilih Reward">
                        <field name="reward_product_id"
                               options="{'no_create': True, 'no_open': True}"/>
                        <field name="product_name" readonly="1"
                               invisible="not reward_product_id"/>
                        <field name="points_required" readonly="1"
                               invisible="not reward_product_id"/>
                        <field name="points_after" readonly="1"
                               invisible="not reward_product_id"/>
                        <field name="notes" placeholder="Catatan opsional..."/>
                    </group>
                </sheet>
                <footer>
                    <button name="action_confirm"
                            type="object"
                            string="Konfirmasi Redeem"
                            class="btn-primary"/>
                    <button string="Batal" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

---

## Langkah 4 — Testing & Flow Validation

### Setup Awal (lakukan sekali setelah install)

1. Login sebagai **Manajer**
2. Buka **Point of Sale → Reward Products**
3. Tambahkan produk beserta poin yang dibutuhkan, contoh:

| Produk | Points Required |
|---|---|
| Kopi Gratis | 10 |
| Diskon Voucher | 50 |
| Merchandise | 100 |

### Skenario Test Earn Points

1. Buka sesi POS
2. Pilih pelanggan (wajib ada pelanggan)
3. Lakukan transaksi **Rp 150.000** → Bayar
4. Tutup sesi
5. Buka form pelanggan → poin bertambah **15**
6. Cek menu **Loyalty Point History** → tercatat 1 baris: type=Earn, points=15, pos_order terisi

### Skenario Test Redeem Points

1. Buka form pelanggan yang sudah punya poin
2. Klik tombol **Redeem Points** (hanya muncul untuk Manajer, hilang jika poin = 0)
3. Popup muncul → dropdown hanya tampilkan produk yang poinnya ≤ poin pelanggan
4. Pilih produk reward → preview **Points Required** dan **Points After Redeem** muncul
5. Klik **Konfirmasi Redeem**
6. Poin pelanggan berkurang sesuai produk yang dipilih
7. Cek **Loyalty Point History** → tercatat: type=Redeem, product_id terisi, notes otomatis

### Skenario Test Security

| Aksi | Kasir | Manajer |
|---|---|---|
| Lihat Loyalty Point History | ✅ | ✅ |
| Lihat tombol Redeem Points | ❌ | ✅ |
| Akses menu Reward Products | ❌ | ✅ |
| Edit/hapus history | ❌ | ✅ |

---

## Cara Upgrade Modul

```bash
# Dari direktori root Odoo
python odoo-bin -u pos_custom -d nama_database
```

---

## Konsep Kunci yang Dipelajari

### Day 1

| Konsep | Penerapan |
|---|---|
| `_inherit` | Menambah field/method ke model existing tanpa ubah kode asli |
| `_name` | Mendefinisikan model baru |
| `Many2one` | Relasi antar model |
| `Selection` | Field pilihan tetap (Earn / Redeem) |
| `<xpath>` | Menyisipkan elemen ke view yang sudah ada |
| `<list>` | Tag view list Odoo 19 (pengganti `<tree>`) |
| `res.groups.privilege` | Container grup di halaman User Settings |

### Day 2

| Konsep | Penerapan |
|---|---|
| Override method POS | `action_pos_order_paid` — titik yang tepat untuk inject logika setelah order paid |
| `TransientModel` | Wizard popup sementara (`loyalty.redeem.wizard`) |
| `domain` dinamis | Filter dropdown berdasarkan nilai field lain di form yang sama |
| `computed field` | `points_after` — kalkulasi real-time di wizard |
| `.sudo()` | Bypass permission check untuk operasi lintas model |
| `_sql_constraints` | Validasi unik dan check di level database |
| `groups` pada button | Sembunyikan tombol berdasarkan grup pengguna |
| `invisible` pada button | Sembunyikan tombol berdasarkan nilai field |

---

*Workshop: Bangun Smart POS & Loyalty Point Sendiri dari Nol dengan Odoo 19*
