from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine, Base
from app.auth_utils import COOKIE_NAME, extract_username_from_token
from app.routers import routers_list
from app.routers import expenses_routes
from app.routers import employees_routes
from app.routers import positions_routes
from jinja2 import Environment, FileSystemLoader
from babel.support import Translations
import os
import sys
from pathlib import Path as _Path


# 
# دالة مساعدة لمسار الملفات (تعمل مع PyInstaller)
# 
def get_base_path():
    """يرجع المسار الأساسي  يعمل مع Python و PyInstaller"""
    if getattr(sys, 'frozen', False):
        # نعمل من .exe
        return _Path(sys._MEIPASS)
    else:
        # نعمل من Python عادي
        return _Path(__file__).resolve().parent.parent


BASE_PATH = get_base_path()

# مسار قاعدة البيانات  يفضّل demo.db إن وُجد
def get_db_path():
    """
    يرجع مسار قاعدة البيانات:
    - إذا كان demo.db موجوداً  يُستخدم (نسخة تجريبية)
    - وإلا  buscore.db (النسخة الأساسية)
    """
    if getattr(sys, 'frozen', False):
        # نعمل من .exe  بجانب الـ .exe
        exe_dir = _Path(sys.executable).parent
        demo_db = exe_dir / "demo.db"
        if demo_db.exists():
            print(f" وضع Demo: {demo_db.name}")
            return demo_db
        return exe_dir / "buscore.db"
    else:
        # Python عادي
        demo_db = BASE_PATH / "demo.db"
        if demo_db.exists():
            print(f" وضع Demo: {demo_db.name}")
            return demo_db
        return BASE_PATH / "buscore.db"

# استيراد النماذج
from app.models import stations_models, trips_models, bookings_models, payments_models, user_models, bus_models, expenses_models, employees_models, positions_models
from app.models import branches_models, customers_models
# إنشاء جداول قاعدة البيانات
Base.metadata.create_all(bind=engine)

# 
# FULL SEED  كل البيانات الأساسية
# 
def _seed_all_data():
    """يملأ قاعدة البيانات بكل البيانات الافتراضية"""
    from app.database.database import SessionLocal
    from app.auth_utils import get_password_hash

    db = SessionLocal()
    try:
        # 1) المستخدمون
        from app.models.user_models import User
        if db.query(User).count() == 0:
            db.add(User(username="admin", email="admin@buscore.com",
                       hashed_password=get_password_hash("admin"),
                       is_active=True, is_admin=True, role="admin", is_super_admin=True))
            db.add(User(username="demo", email="demo@buscore.com",
                       hashed_password=get_password_hash("demo"),
                       is_active=True, is_admin=True, role="admin"))
            db.commit()
            print("SEED: 2 users")

        # 2) الفروع
        try:
            from app.models.branches_models import Branch
            if db.query(Branch).count() == 0:
                db.add(Branch(code="BR-001", name="المركز الرئيسي - الخرطوم",
                             name_en="Main Branch - Khartoum",
                             phone="+249123456789", is_active=True))
                db.add(Branch(code="BR-002", name="فرع بورتسودان",
                             name_en="Port Sudan Branch",
                             phone="+249123456790", is_active=True))
                db.commit()
                print("SEED: 2 branches")
        except Exception as e:
            print(f"SEED branches error: {e}")

        # 3) المدن
        try:
            from app.models.stations_models import City
            if db.query(City).count() == 0:
                cities = [
                    ("الخرطوم", "KRT", "Khartoum"),
                    ("ود مدني", "MAD", "Wad Madani"),
                    ("عطبرة", "ABT", "Atbara"),
                    ("بورتسودان", "PZU", "Port Sudan"),
                    ("كسلا", "KSL", "Kassala"),
                ]
                for name, code, name_en in cities:
                    db.add(City(name=name, code=code, name_en=name_en))
                db.commit()
                print("SEED: 5 cities")
        except Exception as e:
            print(f"SEED cities error: {e}")

        # 4) المحطات
        try:
            from app.models.stations_models import Station, City
            if db.query(Station).count() == 0:
                khartoum = db.query(City).filter(City.code == "KRT").first()
                wadmadani = db.query(City).filter(City.code == "MAD").first()
                atbara = db.query(City).filter(City.code == "ABT").first()
                portsudan = db.query(City).filter(City.code == "PZU").first()
                kassala = db.query(City).filter(City.code == "KSL").first()

                stations = [
                    Station(name="محطة الخرطوم الرئيسية", name_en="Khartoum Main", city_id=khartoum.id if khartoum else None),
                    Station(name="محطة ود مدني", name_en="Wad Madani", city_id=wadmadani.id if wadmadani else None),
                    Station(name="محطة عطبرة", name_en="Atbara", city_id=atbara.id if atbara else None),
                    Station(name="محطة بورتسودان", name_en="Port Sudan", city_id=portsudan.id if portsudan else None),
                    Station(name="محطة كسلا", name_en="Kassala", city_id=kassala.id if kassala else None),
                ]
                for s in stations:
                    db.add(s)
                db.commit()
                print("SEED: 5 stations")
        except Exception as e:
            print(f"SEED stations error: {e}")

        # 5) الحافلات
        try:
            from app.models.bus_models import Bus
            if db.query(Bus).count() == 0:
                buses = [
                    ("خ-5213", "MERCEDES", 2027),
                    ("خ-1233", "MERCEDES", 2027),
                    ("خ-5238", "MERCEDES", 2025),
                    ("خ-7568", "MERCEDES", 2025),
                    ("خ-9908", "MERCEDES", 2026),
                ]
                for plate, model, year in buses:
                    db.add(Bus(plate_number=plate, model=model, year=year,
                              total_seats=55, is_active=True))
                db.commit()
                print("SEED: 5 buses")
        except Exception as e:
            print(f"SEED buses error: {e}")

        # 6) الرحلات
        try:
            from app.models.trips_models import Trip, Route
            from app.models.bus_models import Bus
            from app.models.stations_models import Station
            from datetime import datetime, timedelta

            if db.query(Route).count() == 0:
                st1 = db.query(Station).filter(Station.name_en == "Khartoum Main").first()
                st2 = db.query(Station).filter(Station.name_en == "Port Sudan").first()
                st3 = db.query(Station).filter(Station.name_en == "Wad Madani").first()
                st4 = db.query(Station).filter(Station.name_en == "Atbara").first()
                st5 = db.query(Station).filter(Station.name_en == "Kassala").first()

                routes_data = []
                if st1 and st2:
                    routes_data.append(Route(code="KRT-PZU", departure_station_id=st1.id, arrival_station_id=st2.id))
                if st1 and st3:
                    routes_data.append(Route(code="KRT-MAD", departure_station_id=st1.id, arrival_station_id=st3.id))
                if st1 and st4:
                    routes_data.append(Route(code="KRT-ABT", departure_station_id=st1.id, arrival_station_id=st4.id))
                if st1 and st5:
                    routes_data.append(Route(code="KRT-KSL", departure_station_id=st1.id, arrival_station_id=st5.id))
                for r in routes_data:
                    db.add(r)
                db.commit()
                print(f"SEED: {len(routes_data)} routes")

            if db.query(Trip).count() == 0:
                from app.models.trips_models import Route
                buses = db.query(Bus).all()
                routes = db.query(Route).all()
                base_time = datetime.now() + timedelta(days=1)
                count = 0
                for i, bus in enumerate(buses):
                    if i < len(routes):
                        route = routes[i % len(routes)]
                        departure = base_time.replace(hour=8 + i, minute=0, second=0, microsecond=0)
                        db.add(Trip(
                            route_id=route.id,
                            bus_id=bus.id,
                            total_seats=bus.total_seats or 55,
                            departure_time=departure,
                            arrival_time=departure + timedelta(hours=4),
                            price_at_time=25000 + (i * 1000),
                            is_active=True,
                            is_online_sellable=True,
                        ))
                        count += 1
                db.commit()
                print(f"SEED: {count} trips")
        except Exception as e:
            print(f"SEED trips error: {e}")
            import traceback
            traceback.print_exc()

        print("SEED: COMPLETE")

    except Exception as e:
        print(f"SEED FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

# 
# FastAPI App
# 
app = FastAPI(title="BusCore API", version="1.0.0")



try:
    _seed_all_data()
except Exception as _e:
    print(f"SEED outer error: {_e}")




# ========================================
# 🌐 إعدادات اللغة (Locale) — مكافئ LocaleMiddleware
# ========================================
SUPPORTED_LANGS = {"ar", "en"}
DEFAULT_LANG = "ar"
LANG_COOKIE_NAME = "lang"

def get_translations(lang: str):
    locale_dir = str(BASE_PATH / "locale")
    try:
        return Translations.load(locale_dir, [lang])
    except Exception:
        return None
    
def detect_lang(request: Request) -> str:
    """
    ترتيب أولوية اكتشاف اللغة:
    1) ?lang=xx في الرابط
    2) Cookie: lang
    3) Header: Accept-Language
    4) اللغة الافتراضية
    """
    # 1) من الرابط
    lang = request.query_params.get("lang")
    if lang:
        lang = lang.strip().lower()[:2]
        if lang in SUPPORTED_LANGS:
            return lang

    # 2) من الكوكيز
    lang = request.cookies.get(LANG_COOKIE_NAME)
    if lang:
        lang = lang.strip().lower()[:2]
        if lang in SUPPORTED_LANGS:
            return lang

    # 3) من هيدر Accept-Language
    header = request.headers.get("accept-language", "")
    if header:
        first = header.split(",")[0].split(";")[0].strip().lower()
        code = first.split("-")[0]
        if code in SUPPORTED_LANGS:
            return code

    # 4) الافتراضي
    return DEFAULT_LANG


@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    """حماية /admin/* — يفحص الـ Cookie"""
    path = request.url.path
    if path.startswith("/admin"):
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            return RedirectResponse(url="/login", status_code=303)
        username = extract_username_from_token(token)
        if not username:
            response = RedirectResponse(url="/login", status_code=303)
            response.delete_cookie(COOKIE_NAME, path="/")
            return response
    response = await call_next(request)
    return response


@app.middleware("http")
async def locale_middleware(request: Request, call_next):
    lang = detect_lang(request)
    request.state.lang = lang
    response = await call_next(request)
    response.headers["Content-Language"] = lang
    return response
# ========================================
# نهاية إعدادات اللغة
# ========================================


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# الملفات الثابتة
app.mount("/static", StaticFiles(directory=str(BASE_PATH / "app" / "static")), name="static")

# ✅ حل خبراء Jinja2 و FastAPI: استخدام Environment مباشرة مع تعطيل Cache
templates_env = Environment(
    loader=FileSystemLoader(str(BASE_PATH / "app" / "templates")),
    autoescape=True,
    enable_async=False,  # تعطيل Async
    cache_size=0  # تعطيل Cache
)

# دالة مساعدة للـ Rendering — الآن تمرر lang تلقائيًا لكل القوالب
def get_company_settings():
    """جلب إعدادات الشركة  للاستخدام في كل القوالب"""
    from app.database.database import SessionLocal
    from app.crud import settings_crud
    db = SessionLocal()
    try:
        settings = settings_crud.get_settings(db)
        if settings:
            return {
                "company_name": settings.company_name or "BusCore",
                "company_name_en": settings.company_name_en or "BusCore",
                "company_logo": settings.company_logo or "/static/images/logo.png",
                "company_phone": settings.company_phone or "",
                "company_email": settings.company_email or "",
                "company_address": settings.company_address or "",
                "company_address_en": settings.company_address_en or "",
                "primary_color": settings.primary_color or "#0d6efd",
                "secondary_color": settings.secondary_color or "#6c757d",
                "company_website": settings.company_website or "",
                "support_phone": settings.support_phone or "",
                "support_whatsapp": settings.support_whatsapp or "",
            }
        return {
            "company_name": "BusCore",
            "company_name_en": "BusCore",
            "company_logo": "/static/images/logo.png",
            "company_phone": "",
            "company_email": "",
            "company_address": "",
            "company_address_en": "",
            "primary_color": "#0d6efd",
            "secondary_color": "#6c757d",
            "company_website": "",
            "support_phone": "",
            "support_whatsapp": "",
        }
    except Exception as e:
        print(f"  خطأ في get_company_settings: {e}")
        return {
            "company_name": "BusCore",
            "company_name_en": "BusCore",
            "company_logo": "/static/images/logo.png",
            "primary_color": "#0d6efd",
            "secondary_color": "#6c757d",
            "company_phone": "",
            "company_email": "",
            "company_address": "",
            "company_address_en": "",
            "company_website": "",
            "support_phone": "",
            "support_whatsapp": "",
        }
    finally:
        db.close()


def render_template(name: str, context: dict):
    request = context.get("request")
    lang = getattr(request.state, "lang", DEFAULT_LANG) if request else DEFAULT_LANG

    translations = get_translations(lang)
    if translations:
        context["_"] = translations.gettext
    else:
        context["_"] = lambda s: s

    context.setdefault("lang", lang)
    context.setdefault("dir", "rtl" if lang == "ar" else "ltr")
    #  إضافة settings لكل قالب
    context.setdefault("settings", get_company_settings())
    template = templates_env.get_template(name)
    return HTMLResponse(content=template.render(context))

# الـ Routers
# الـ Routers
for router in routers_list:
    app.include_router(router)

# ✅ Router المحاسبة
# ✅ Router المحاسبة
app.include_router(expenses_routes.router)

# ✅ Router العاملين
app.include_router(employees_routes.router)

# ✅ Router الوظائف
app.include_router(positions_routes.router)
# ========================================
# صفحات HTML
# ========================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render_template("index.html", {"request": request})

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request):
    return render_template("search.html", {"request": request})

@app.get("/buses", response_class=HTMLResponse)
async def buses_showcase(request: Request):
    return render_template("buses_showcase.html", {"request": request})

@app.get("/booking", response_class=HTMLResponse)
async def booking(request: Request):
    return render_template("booking.html", {"request": request})

@app.get("/confirmation", response_class=HTMLResponse)
async def confirmation(request: Request):
    return render_template("confirmation.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """صفحة حقوق النشر والملكية الفكرية"""
    return render_template("about.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return render_template("login.html", {"request": request})

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return render_template("admin/dashboard.html", {"request": request})

# ========================================
# 🔐 لوحة تحكم الإدارة (Admin Dashboard)
# ========================================

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return render_template("admin/dashboard.html", {"request": request})

@app.get("/admin/cities", response_class=HTMLResponse)
async def admin_cities(request: Request):
    return render_template("admin/cities.html", {"request": request})

@app.get("/admin/stations", response_class=HTMLResponse)
async def admin_stations(request: Request):
    return render_template("admin/stations.html", {"request": request})

@app.get("/admin/routes", response_class=HTMLResponse)
async def admin_routes(request: Request):
    return render_template("admin/routes.html", {"request": request})

@app.get("/admin/trips", response_class=HTMLResponse)
async def admin_trips(request: Request):
    return render_template("admin/trips.html", {"request": request})

@app.get("/admin/buses", response_class=HTMLResponse)
async def admin_buses(request: Request):
    return render_template("admin/buses.html", {"request": request})

@app.get("/admin/bookings", response_class=HTMLResponse)
async def admin_bookings(request: Request):
    return render_template("admin/bookings.html", {"request": request})

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    return render_template("admin/users.html", {"request": request})

@app.get("/admin/system-map", response_class=HTMLResponse)
async def admin_system_map(request: Request):
    return render_template("admin/system_map.html", {"request": request})


@app.get("/admin/luggage", response_class=HTMLResponse)
async def admin_luggage(request: Request):
    return render_template("admin/luggage.html", {"request": request})

@app.get("/admin/live-trips", response_class=HTMLResponse)
async def admin_live_trips(request: Request):
    return render_template("admin/live_trips.html", {"request": request})

@app.get("/admin/branches", response_class=HTMLResponse)
async def admin_branches(request: Request):
    return render_template("admin/branches.html", {"request": request})

@app.get("/admin/customers", response_class=HTMLResponse)
async def admin_customers(request: Request):
    return render_template("admin/customers.html", {"request": request})


@app.get("/admin/accounting/settings", response_class=HTMLResponse)
async def admin_accounting_settings(request: Request):
    """صفحة إعدادات النظام المحاسبي"""
    return render_template("admin/accounting_settings.html", {"request": request})


@app.get("/admin/accounts", response_class=HTMLResponse)
async def admin_accounts(request: Request):
    """صفحة شجرة الحسابات"""
    return render_template("admin/accounts.html", {"request": request})


@app.get("/admin/positions", response_class=HTMLResponse)
async def admin_positions(request: Request):
    return render_template("admin/positions.html", {"request": request})


@app.get("/admin/employees", response_class=HTMLResponse)
async def admin_employees(request: Request):
    return render_template("admin/employees.html", {"request": request})

@app.get("/admin/employees/{employee_id}/statement", response_class=HTMLResponse)
async def admin_employee_statement(employee_id: int, request: Request):
    return render_template("admin/employee_statement.html", {"request": request, "employee_id": employee_id})

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request):
    return render_template("admin/settings.html", {"request": request})

@app.get("/admin/expenses", response_class=HTMLResponse)
async def admin_expenses(request: Request):
    return render_template("admin/expenses.html", {"request": request})

@app.get("/admin/financial-reports", response_class=HTMLResponse)
async def admin_financial_reports(request: Request):
    return render_template("admin/financial_reports.html", {"request": request})

@app.get("/admin/expense-categories", response_class=HTMLResponse)
async def admin_expense_categories(request: Request):
    return render_template("admin/expense_categories.html", {"request": request})

# ========================================
# API
# ========================================

@app.get("/admin/journal", response_class=HTMLResponse)
async def admin_journal(request: Request):
    """صفحة دفتر اليومية"""
    return render_template("admin/journal.html", {"request": request})


@app.get("/admin/bi", response_class=HTMLResponse)
async def admin_bi(request: Request):
    """لوحة تحليل البيانات"""
    return render_template("admin/bi.html", {"request": request})


@app.get("/api")
async def api_root():
    return {"message": "مرحباً بك في نظام BusCore!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}