# -*- coding: utf-8 -*-
"""إنشاء قاعدة البيانات مع البيانات الافتراضية"""
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# إضافة مجلد المشروع
sys.path.insert(0, str(Path(__file__).resolve().parent))

def seed_database():
    """يملأ قاعدة البيانات بالبيانات الافتراضية"""
    from app.database.database import engine, SessionLocal, Base
    from app.models import (
        user_models, branches_models, stations_models, customers_models,
        bus_models, trips_models, employees_models, expenses_models
    )
    from app.auth_utils import get_password_hash
    
    # إنشاء الجداول
    Base.metadata.create_all(bind=engine)
    print("OK: Tables created")
    
    db = SessionLocal()
    try:
        from app.models.user_models import User
        from app.models.branches_models import Branch
        from app.models.stations_models import Station, City
        from app.models.bus_models import Bus
        from app.models.customers_models import Customer
        
        # 1) المستخدمون
        if db.query(User).count() == 0:
            admin = User(
                username="admin",
                email="admin@buscore.com",
                hashed_password=get_password_hash("admin"),
                is_active=True,
                is_admin=True,
                role="admin",
                is_super_admin=True,
            )
            demo = User(
                username="demo",
                email="demo@buscore.com",
                hashed_password=get_password_hash("demo"),
                is_active=True,
                is_admin=True,
                role="admin",
                is_super_admin=False,
            )
            db.add(admin)
            db.add(demo)
            db.commit()
            print("OK: 2 users (admin, demo)")
        
        # 2) الفروع
        if db.query(Branch).count() == 0:
            branches = [
                Branch(code="BR-001", name="المركز الرئيسي - الخرطوم", name_en="Main Branch - Khartoum", city_id=4, phone="+249123456789", is_active=True),
                Branch(code="BR-002", name="فرع بورتسودان", name_en="Port Sudan Branch", city_id=27, phone="+249123456790", is_active=True),
            ]
            for b in branches:
                db.add(b)
            db.commit()
            print("OK: 2 branches")
        
        # 3) المدن
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
            print("OK: 5 cities")
        
        # 4) المحطات
        if db.query(Station).count() == 0:
            stations = [
                Station(name="محطة الخرطوم الرئيسية", name_en="Khartoum Main Station", city_id=1),
                Station(name="محطة ود مدني", name_en="Wad Madani Station", city_id=2),
                Station(name="محطة عطبرة", name_en="Atbara Station", city_id=3),
                Station(name="محطة بورتسودان", name_en="Port Sudan Station", city_id=4),
                Station(name="محطة كسلا", name_en="Kassala Station", city_id=5),
            ]
            for s in stations:
                db.add(s)
            db.commit()
            print("OK: 5 stations")
        
        # 5) الحافلات
        if db.query(Bus).count() == 0:
            buses = [
                Bus(plate_number="خ-5213", model="MERCEDES", year=2027, total_seats=55, is_active=True),
                Bus(plate_number="خ-1233", model="MERCEDES", year=2027, total_seats=55, is_active=True),
                Bus(plate_number="خ-5238", model="MERCEDES", year=2025, total_seats=55, is_active=True),
                Bus(plate_number="خ-7568", model="MERCEDES", year=2025, total_seats=55, is_active=True),
                Bus(plate_number="خ-9908", model="MERCEDES", year=2026, total_seats=55, is_active=True),
            ]
            for b in buses:
                db.add(b)
            db.commit()
            print("OK: 5 buses")
        
        # 6) العملاء
        if db.query(Customer).count() == 0:
            customers = [
                Customer(full_name="كمال عبدالله احمد", phone="+249987654321", email="kamal@example.com", customer_code="CUST-000001", is_active=True),
                Customer(full_name="عبدالمنعم علي محمد", phone="+249917764577", email="abdel@example.com", customer_code="CUST-000002", is_active=True),
                Customer(full_name="المنذر صلاح عمر", phone="+249987865423", email="munzir@example.com", customer_code="CUST-000003", is_active=True),
                Customer(full_name="ريم عبدالمنعم", phone="+249911111111", email="reem@example.com", customer_code="CUST-000004", is_active=True),
                Customer(full_name="اسلام سليمان", phone="+249922222222", email="islam@example.com", customer_code="CUST-000005", is_active=True),
            ]
            for c in customers:
                db.add(c)
            db.commit()
            print("OK: 5 customers")
        
        print()
        print("=" * 60)
        print("SEED COMPLETE")
        print("=" * 60)
    
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
