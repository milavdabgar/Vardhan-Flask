from app import create_app, db
from app.models import User, TechnicianAssignment, AMCContract, Equipment
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_database():
    # Define equipment types
    equipment_types = [
        "Computer",
        "Printer",
        "Air Conditioner",
        "Projector",
        "Laboratory Equipment"
    ]
    
    app = create_app()
    with app.app_context():
        # Create system admin
        admin = User.query.filter_by(email='admin@vardhaninsys.com').first()
        if admin is None:
            admin = User(
                email='admin@vardhaninsys.com',
                role='admin',
                full_name='System Administrator',
                contact_number='1234567890',
                is_active=True,
                created_at=datetime.utcnow()
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('System admin created successfully!')

        # Create colleges and their admins
        colleges = [
            "Engineering College",
            "Medical College",
            "Arts College"
        ]

        college_admins = []
        for i, college in enumerate(colleges, 1):
            admin = User.query.filter_by(email=f"college{i}@example.com").first()
            if admin is None:
                admin = User(
                    email=f"college{i}@example.com",
                    role="college_admin",
                    full_name=f"{college} Admin",
                    contact_number=f"123456789{i}",
                    institution=college,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                admin.set_password("password123")
                db.session.add(admin)
                college_admins.append(admin)
                print(f'College admin for {college} created successfully!')

        # Create junior technicians
        jr_techs = []
        for i in range(1, 4):
            tech = User.query.filter_by(email=f"jrtech{i}@example.com").first()
            if tech is None:
                tech = User(
                    email=f"jrtech{i}@example.com",
                    password_hash=generate_password_hash("password123"),
                    role="technician",
                    full_name=f"Junior Tech {i}",
                    contact_number=f"987654321{i}",
                    is_active=True
                )
                jr_techs.append(tech)
                db.session.add(tech)
                print(f'Junior technician {i} created successfully!')

        # Create senior technicians
        sr_techs = []
        for i in range(1, 3):
            tech = User.query.filter_by(email=f"srtech{i}@example.com").first()
            if tech is None:
                tech = User(
                    email=f"srtech{i}@example.com",
                    password_hash=generate_password_hash("password123"),
                    role="technician",
                    full_name=f"Senior Tech {i}",
                    contact_number=f"876543210{i}",
                    is_active=True
                )
                sr_techs.append(tech)
                db.session.add(tech)
                print(f'Senior technician {i} created successfully!')

        # Commit to get IDs
        db.session.commit()

        # Create AMC contracts first
        contracts = {}
        for i, college in enumerate(colleges):
            contract = AMCContract.query.filter_by(
                institution=college,
                contract_number=f"AMC{2025}{i+1:03d}"
            ).first()

            if contract is None:
                start_date = datetime(2025, 1, 1)
                contract = AMCContract(
                    institution=college,
                    contract_number=f"AMC{2025}{i+1:03d}",
                    contract_type='Computer and Printers',
                    start_date=start_date,
                    end_date=start_date + timedelta(days=365),
                    contract_value=100000 + (i * 25000),
                    status='ACTIVE',
                    created_by=admin.id
                )
                db.session.add(contract)
                db.session.flush()  # This will assign the ID to contract
                print(f'Created AMC contract for {college}')

                # Create equipment for this contract
                for j, eq_type in enumerate(equipment_types):
                    for k in range(1, 4):  # 3 pieces of each equipment type
                        equipment = Equipment(
                            name=f"{eq_type} {k}",
                            type=eq_type.upper(),
                            make="Vardhan Systems",
                            model=f"MDL{j+1}{k:02d}",
                            serial_number=f"SN{j+1}{k:03d}-{i+1}",
                            installation_date=start_date - timedelta(days=365),
                            location=f"Room {k:02d}, Block {chr(65+j)}",
                            status='ACTIVE',
                            specifications=f"Standard {eq_type} specifications",
                            contract_id=contract.id
                        )
                        db.session.add(equipment)
                        print(f'Created {eq_type} equipment for {college}')
            contracts[college] = contract

        # Clear existing data
        TechnicianAssignment.query.delete()
        Equipment.query.delete()
        AMCContract.query.delete()
        db.session.commit()

        # Create technician assignments
        # Get all existing technicians
        existing_jr_techs = [tech for tech in User.query.filter_by(role="technician").all() 
                           if tech.email.startswith("jrtech")]
        existing_sr_techs = [tech for tech in User.query.filter_by(role="technician").all() 
                           if tech.email.startswith("srtech")]

        # Now create technician assignments
        assignments = [
            # Engineering College
            (existing_jr_techs[0], colleges[0], False),
            (existing_jr_techs[1], colleges[0], False),
            (existing_sr_techs[0], colleges[0], True),
            
            # Medical College
            (existing_jr_techs[1], colleges[1], False),
            (existing_jr_techs[2], colleges[1], False),
            (existing_sr_techs[0], colleges[1], True),
            
            # Arts College
            (existing_jr_techs[0], colleges[2], False),
            (existing_jr_techs[2], colleges[2], False),
            (existing_sr_techs[1], colleges[2], True),
        ]

        for tech, college, is_senior in assignments:
            contract = contracts[college]
            assignment = TechnicianAssignment(
                technician_id=tech.id,
                contract_id=contract.id,
                is_senior=is_senior
            )
            db.session.add(assignment)
            print(f'Created assignment: {tech.full_name} -> {college} ({"Senior" if is_senior else "Junior"})')

        # Create sample AMC contracts
        equipment_types = [
            "Computer",
            "Printer",
            "Air Conditioner",
            "Projector",
            "Laboratory Equipment"
        ]

        for i, college in enumerate(colleges):
            contract = AMCContract.query.filter_by(
                institution=college,
                contract_number=f"AMC{2025}{i+1:03d}"
            ).first()

            if contract is None:
                start_date = datetime(2025, 1, 1)
                contract = AMCContract(
                    institution=college,
                    contract_number=f"AMC{2025}{i+1:03d}",
                    contract_type='Computer and Printers',
                    start_date=start_date,
                    end_date=start_date + timedelta(days=365),
                    contract_value=100000 + (i * 25000),
                    status='ACTIVE',
                    created_by=admin.id
                )
                db.session.add(contract)
                db.session.flush()  # This will assign the ID to contract
                print(f'Created AMC contract for {college}')

                # Create equipment for each contract
                for j, eq_type in enumerate(equipment_types):
                    for k in range(1, 4):  # 3 pieces of each equipment type
                        equipment = Equipment(
                            name=f"{eq_type} {k}",
                            type=eq_type.upper(),
                            make="Vardhan Systems",
                            model=f"MDL{j+1}{k:02d}",
                            serial_number=f"SN{j+1}{k:03d}-{i+1}",
                            installation_date=start_date - timedelta(days=365),
                            location=f"Room {k:02d}, Block {chr(65+j)}",
                            status='ACTIVE',
                            specifications=f"Standard {eq_type} specifications",
                            contract_id=contract.id
                        )
                        db.session.add(equipment)
                        print(f'Created {eq_type} equipment for {college}')

        db.session.commit()

        print("\nInitialization completed successfully!")
        print("\nUser Credentials:")
        print("System Admin:")
        print("Email: admin@vardhaninsys.com")
        print("Password: admin123")
        print("\nCollege Admins:")
        for i, college in enumerate(colleges, 1):
            print(f"{college}:")
            print(f"Email: college{i}@example.com")
            print(f"Password: password123")
        print("\nJunior Technicians:")
        for i in range(1, 4):
            print(f"Email: jrtech{i}@example.com")
            print(f"Password: password123")
        print("\nSenior Technicians:")
        for i in range(1, 3):
            print(f"Email: srtech{i}@example.com")
            print(f"Password: password123")

if __name__ == "__main__":
    init_database()
