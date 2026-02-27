#!/usr/bin/env python3
"""
Demo data seeding script for Vocalis
Creates demo organization, users, patients, and prescriptions
Run this script to populate the database with sample data for presentations
"""

import uuid
import json
from datetime import datetime, timedelta
from database import DemoSessionLocal, demo_engine, Base
from models import (
    Organization, User, UserRole, Patient, Prescription, PatientVisit,
    Device, VisitDetail, NurseLocation, PhotoAttachment
)
import bcrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed-demo-data")

def hash_password_direct(password: str) -> str:
    """Hash password using bcrypt directly"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def create_demo_data():
    """Create comprehensive demo data for presentations in demo.db"""

    # Create tables in demo database
    Base.metadata.create_all(bind=demo_engine)
    db = DemoSessionLocal()

    try:
        # 1. Create Demo Organization
        logger.info("Creating demo organization...")
        org = Organization(
            id=str(uuid.uuid4()),
            name="Hôpital Saint-Louis Demo",
            address="123 Rue de la Santé, Paris",
            phone="+33 1 42 49 49 49",
            created_at=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        logger.info(f"✓ Organization created: {org.name}")

        # 2. Create Demo Users
        logger.info("Creating demo users...")

        # Doctor
        doctor = User(
            id=str(uuid.uuid4()),
            email="doctor@hopital-demo.fr",
            full_name="Dr. Marie Dubois",
            password_hash=hash_password_direct("demo123"),
            role=UserRole.DOCTOR,
            org_id=org.id,
            is_active=True,
            last_login=datetime.utcnow()
        )
        db.add(doctor)
        db.flush()
        logger.info(f"✓ Doctor user created: {doctor.email}")

        # Nurse
        nurse = User(
            id=str(uuid.uuid4()),
            email="nurse@hopital-demo.fr",
            full_name="Infirmière Sophie Martin",
            password_hash=hash_password_direct("demo123"),
            role=UserRole.NURSE,
            org_id=org.id,
            is_active=True,
            last_login=datetime.utcnow()
        )
        db.add(nurse)
        db.flush()
        logger.info(f"✓ Nurse user created: {nurse.email}")

        # 3. Create Demo Patients
        logger.info("Creating demo patients...")

        patients_data = [
            {
                "first_name": "Jean",
                "last_name": "Dupont",
                "date_of_birth": datetime(1965, 5, 15),
                "gender": "M",
                "phone": "+33 6 12 34 56 78",
                "email": "jean.dupont@email.com",
                "address": "45 Avenue des Champs, 75008 Paris",
                "allergies": ["Pénicilline", "Latex"],
                "chronic_conditions": ["Hypertension", "Diabète type 2"],
                "current_medications": ["Métoprolol", "Metformine"],
                "medical_notes": "Suivi régulier pour hypertension. Bon contrôle glycémique."
            },
            {
                "first_name": "Marie",
                "last_name": "Martin",
                "date_of_birth": datetime(1978, 3, 22),
                "gender": "F",
                "phone": "+33 6 23 45 67 89",
                "email": "marie.martin@email.com",
                "address": "78 Rue de Rivoli, 75004 Paris",
                "allergies": ["Aspirine"],
                "chronic_conditions": ["Asthme", "GERD"],
                "current_medications": ["Albuterol", "Oméprazole"],
                "medical_notes": "Asthme bien contrôlé. Pas de crises récentes."
            },
            {
                "first_name": "Pierre",
                "last_name": "Bernard",
                "date_of_birth": datetime(1955, 11, 8),
                "gender": "M",
                "phone": "+33 6 34 56 78 90",
                "email": "pierre.bernard@email.com",
                "address": "123 Boulevard Saint-Germain, 75005 Paris",
                "allergies": [],
                "chronic_conditions": ["Arthrite rhumatoïde", "Hypercholestérolémie"],
                "current_medications": ["Méthotrexate", "Atorvastatine"],
                "medical_notes": "Suivi régulier rhumatologue. Bonne réponse au traitement."
            },
            {
                "first_name": "Isabelle",
                "last_name": "Rousseau",
                "date_of_birth": datetime(1992, 7, 19),
                "gender": "F",
                "phone": "+33 6 45 67 89 01",
                "email": "isabelle.rousseau@email.com",
                "address": "56 Rue de l'Université, 75007 Paris",
                "allergies": ["Sulfonamides"],
                "chronic_conditions": ["Migraines chroniques"],
                "current_medications": ["Propranolol", "Sumatriptan (PRN)"],
                "medical_notes": "Migraines fréquentes. Trigger: stress et manque de sommeil."
            },
            {
                "first_name": "Claude",
                "last_name": "Leclerc",
                "date_of_birth": datetime(1970, 1, 10),
                "gender": "M",
                "phone": "+33 6 56 78 90 12",
                "email": "claude.leclerc@email.com",
                "address": "89 Avenue Montaigne, 75008 Paris",
                "allergies": [],
                "chronic_conditions": ["Fibrillation atriale", "Insuffisance cardiaque"],
                "current_medications": ["Warfarine", "Digoxine", "Furosémide"],
                "medical_notes": "Suivi cardiologie. INR à surveiller régulièrement."
            },
        ]

        patients = []
        for p_data in patients_data:
            patient = Patient(
                id=str(uuid.uuid4()),
                org_id=org.id,
                first_name=p_data["first_name"],
                last_name=p_data["last_name"],
                date_of_birth=p_data["date_of_birth"],
                gender=p_data["gender"],
                phone=p_data["phone"],
                email=p_data["email"],
                address=p_data["address"],
                allergies=json.dumps(p_data["allergies"]),
                chronic_conditions=json.dumps(p_data["chronic_conditions"]),
                current_medications=json.dumps(p_data["current_medications"]),
                medical_notes=p_data["medical_notes"],
                created_at=datetime.utcnow()
            )
            db.add(patient)
            patients.append(patient)

        db.flush()
        logger.info(f"✓ {len(patients)} demo patients created")

        # 4. Create Demo Prescriptions
        logger.info("Creating demo prescriptions...")

        prescriptions_data = [
            # For Jean Dupont
            {
                "patient": patients[0],
                "medication": "Métoprolol",
                "dosage": "100mg",
                "duration": "30 jours",
                "diagnosis": "Hypertension artérielle",
                "special_instructions": "Prendre matin et soir avec un verre d'eau. Ne pas arrêter brutalement.",
                "status": "active",
                "days_ago": 5
            },
            {
                "patient": patients[0],
                "medication": "Metformine",
                "dosage": "500mg",
                "duration": "90 jours",
                "diagnosis": "Diabète type 2",
                "special_instructions": "Prendre avec les repas. Peut causer troubles digestifs initialement.",
                "status": "active",
                "days_ago": 15
            },
            {
                "patient": patients[0],
                "medication": "Amoxicilline",
                "dosage": "500mg",
                "duration": "7 jours",
                "diagnosis": "Infection respiratoire",
                "special_instructions": "Tous les 8 heures. Terminer le traitement complet.",
                "status": "completed",
                "days_ago": 30
            },
            # For Marie Martin
            {
                "patient": patients[1],
                "medication": "Albuterol (Salbutamol)",
                "dosage": "100µg",
                "duration": "30 jours",
                "diagnosis": "Asthme",
                "special_instructions": "Utiliser 2 inhalations au besoin. Maximum 4 fois par jour.",
                "status": "active",
                "days_ago": 10
            },
            {
                "patient": patients[1],
                "medication": "Oméprazole",
                "dosage": "20mg",
                "duration": "60 jours",
                "diagnosis": "Reflux gastro-œsophagien (GERD)",
                "special_instructions": "Prendre 30 min avant le petit-déjeuner. Peut affecter absorption autres médicaments.",
                "status": "active",
                "days_ago": 20
            },
            # For Pierre Bernard
            {
                "patient": patients[2],
                "medication": "Méthotrexate",
                "dosage": "15mg",
                "duration": "Continu (hebdomadaire)",
                "diagnosis": "Arthrite rhumatoïde",
                "special_instructions": "Une fois par semaine (lundi). Faire bilan sanguin chaque mois.",
                "status": "active",
                "days_ago": 45
            },
            {
                "patient": patients[2],
                "medication": "Atorvastatine",
                "dosage": "40mg",
                "duration": "90 jours",
                "diagnosis": "Hypercholestérolémie",
                "special_instructions": "Prendre le soir. Peut causer myalgies. Surveiller transaminases.",
                "status": "active",
                "days_ago": 25
            },
            # For Isabelle Rousseau
            {
                "patient": patients[3],
                "medication": "Propranolol",
                "dosage": "80mg",
                "duration": "90 jours",
                "diagnosis": "Migraines chroniques (prévention)",
                "special_instructions": "Prendre matin et soir. Peut causer fatigue et bradycardie.",
                "status": "active",
                "days_ago": 8
            },
            {
                "patient": patients[3],
                "medication": "Sumatriptan",
                "dosage": "50mg",
                "duration": "6 mois",
                "diagnosis": "Migraines chroniques (crise)",
                "special_instructions": "Prendre dès début de crise. Ne pas dépasser 2 doses par jour.",
                "status": "active",
                "days_ago": 8
            },
            # For Claude Leclerc
            {
                "patient": patients[4],
                "medication": "Warfarine",
                "dosage": "5mg",
                "duration": "Continu",
                "diagnosis": "Fibrillation atriale",
                "special_instructions": "Dose ajustée selon INR. INR cible: 2-3. Surveillance mensuelle obligatoire.",
                "status": "active",
                "days_ago": 12
            },
            {
                "patient": patients[4],
                "medication": "Digoxine",
                "dosage": "250µg",
                "duration": "90 jours",
                "diagnosis": "Insuffisance cardiaque",
                "special_instructions": "Prendre matin. Marge thérapeutique étroite - surveillance étroite.",
                "status": "active",
                "days_ago": 18
            },
        ]

        for p_data in prescriptions_data:
            created_at = datetime.utcnow() - timedelta(days=p_data["days_ago"])
            prescription = Prescription(
                id=str(uuid.uuid4()),
                org_id=org.id,
                patient_id=p_data["patient"].id,
                created_by=doctor.id,
                patient_name=f"{p_data['patient'].first_name} {p_data['patient'].last_name}",
                patient_age=str((datetime.utcnow() - p_data["patient"].date_of_birth).days // 365),
                diagnosis=p_data["diagnosis"],
                medication=p_data["medication"],
                dosage=p_data["dosage"],
                duration=p_data["duration"],
                special_instructions=p_data["special_instructions"],
                status=p_data["status"],
                created_at=created_at
            )
            db.add(prescription)

        db.flush()
        logger.info(f"✓ {len(prescriptions_data)} demo prescriptions created")

        # 5. Create Demo Devices
        logger.info("Creating demo devices...")

        devices_data = [
            {"name": "Tensiomètre électronique", "model": "Omron M3", "serial": "SN001-2024"},
            {"name": "Glucomètre", "model": "Accu-Chek Guide", "serial": "SN002-2024"},
            {"name": "Saturomètre", "model": "Nonin PalmSat", "serial": "SN003-2024"},
            {"name": "Thermomètre frontal infrarouge", "model": "Braun ThermoScan", "serial": "SN004-2024"},
            {"name": "Débitmètre de pointe", "model": "AirZone", "serial": "SN005-2024"},
        ]

        devices = []
        for d_data in devices_data:
            device = Device(
                id=str(uuid.uuid4()),
                org_id=org.id,
                name=d_data["name"],
                model=d_data["model"],
                serial_number=d_data["serial"],
                status="available",
                created_at=datetime.utcnow()
            )
            db.add(device)
            devices.append(device)

        db.flush()
        logger.info(f"✓ {len(devices)} demo devices created")

        # 6. Create Demo Patient Visits
        logger.info("Creating demo patient visits...")

        # Get the prescription IDs we just created (simplified - take first few)
        prescriptions = db.query(Prescription).filter(
            Prescription.org_id == org.id
        ).all()

        visits_data = [
            {
                "prescription_idx": 0,
                "status": "completed",
                "address": "45 Avenue des Champs, 75008 Paris",
                "scheduled_date": datetime.utcnow() - timedelta(days=3),
                "notes": "Visite de suivi pour hypertension. Tensiomètre pris à domicile. Valeurs acceptables."
            },
            {
                "prescription_idx": 3,
                "status": "completed",
                "address": "78 Rue de Rivoli, 75004 Paris",
                "scheduled_date": datetime.utcnow() - timedelta(days=5),
                "notes": "Contrôle asthme. Patient rapporte bonne adhésion. Pas de crises cette semaine."
            },
            {
                "prescription_idx": 5,
                "status": "in_progress",
                "address": "123 Boulevard Saint-Germain, 75005 Paris",
                "scheduled_date": datetime.utcnow() - timedelta(days=1),
                "notes": "Visite de suivi arthrite. Patient se plaint douleurs articulaires. Recommandé physiothérapie."
            },
            {
                "prescription_idx": 7,
                "status": "pending",
                "address": "56 Rue de l'Université, 75007 Paris",
                "scheduled_date": datetime.utcnow() + timedelta(days=2),
                "notes": ""
            },
        ]

        for v_data in visits_data:
            if v_data["prescription_idx"] < len(prescriptions):
                visit = PatientVisit(
                    id=str(uuid.uuid4()),
                    org_id=org.id,
                    prescription_id=prescriptions[v_data["prescription_idx"]].id,
                    assigned_nurse=nurse.id,
                    patient_address=v_data["address"],
                    scheduled_date=v_data["scheduled_date"],
                    status=v_data["status"],
                    created_at=datetime.utcnow()
                )
                db.add(visit)
                if v_data["status"] in ["completed", "in_progress"]:
                    db.flush()
                    visit_detail = VisitDetail(
                        id=str(uuid.uuid4()),
                        visit_id=visit.id,
                        device_id=devices[0].id if devices else None,
                        nurse_notes=v_data["notes"],
                        patient_signature=None,
                        completed_at=datetime.utcnow() if v_data["status"] == "completed" else None
                    )
                    db.add(visit_detail)

        db.flush()
        logger.info(f"✓ {len(visits_data)} demo patient visits created")

        # 7. Create Demo Nurse Locations
        logger.info("Creating demo nurse locations...")

        locations_data = [
            {
                "latitude": 48.8566,
                "longitude": 2.3522,
                "accuracy": 10.5,
                "label": "Paris Centre",
                "days_ago": 2
            },
            {
                "latitude": 48.8749,
                "longitude": 2.2975,
                "accuracy": 15.2,
                "label": "Marais",
                "days_ago": 1
            },
            {
                "latitude": 48.8904,
                "longitude": 2.3568,
                "accuracy": 8.3,
                "label": "Belleville",
                "days_ago": 0
            },
        ]

        for loc in locations_data:
            nurse_location = NurseLocation(
                id=str(uuid.uuid4()),
                org_id=org.id,
                nurse_id=nurse.id,
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                accuracy=loc["accuracy"],
                recorded_at=datetime.utcnow() - timedelta(days=loc["days_ago"])
            )
            db.add(nurse_location)

        db.flush()
        logger.info(f"✓ {len(locations_data)} demo nurse locations created")

        # Commit all changes
        db.commit()
        logger.info("\n" + "="*60)
        logger.info("✅ DEMO DATA SUCCESSFULLY CREATED!")
        logger.info("="*60)
        logger.info(f"\nDemo Organization: {org.name}")
        logger.info(f"Demo Doctor: {doctor.email} / Password: demo123")
        logger.info(f"Demo Nurse: {nurse.email} / Password: demo123")
        logger.info(f"Demo Patients: {len(patients)}")
        logger.info(f"Demo Prescriptions: {len(prescriptions_data)}")
        logger.info(f"Demo Devices: {len(devices)}")
        logger.info(f"Demo Visits: {len(visits_data)}")
        logger.info("\nYou can now login to present the app!")
        logger.info("="*60 + "\n")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error creating demo data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_data()
