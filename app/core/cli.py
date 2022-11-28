import platform
import os
from prime_admin.models import Registration, Payment
import click
import csv
from shutil import copyfile
from config import basedir
from app.core.models import CoreModel, CoreModule
from app import MODULES
from app import mongo
from . import bp_core
from .models import CoreCity,CoreProvince
from app.auth.models import Earning, User, Role



def core_install():
    """
    Tatanggap to ng list ng modules tapos iinsert nya sa database yung mga models o tables nila, \
        para malaman ng system kung ano yung mga models(eg. Users,Customers)
    Parameters
    ----------
    modules
        Listahan ng mga modules na iinstall sa system
    """

    print("Installing...")

    try:

        if platform.system() == "Windows":
            provinces_path = basedir + "\\app" + "\\core" + "\\csv" + "\\provinces.csv"
            cities_path = basedir + "\\app" + "\\core" + "\\csv" + "\\cities.csv"
        elif platform.system() == "Linux":
            provinces_path = basedir + "/app/core/csv/provinces.csv"
            cities_path = basedir + "/app/core/csv/cities.csv"
        else:
            raise Exception("Platform not supported yet.")
        
        module_count = 0

        homebest_module = None

        for module in MODULES:
            # TODO: Iimprove to kasi kapag nag error ang isa damay lahat dahil sa last_id
            homebest_module = CoreModule.objects(name=module.module_name).first()
            # last_id = 0
            if not homebest_module:
                new_module = CoreModule(
                    name=module.module_name,
                    short_description=module.module_short_description,
                    long_description=module.module_long_description,
                    status='installed',
                    version=module.version
                    ).save()

                homebest_module = new_module
                    
                print("MODULE - {}: SUCCESS".format(new_module.name))
                # last_id = new_module.id

            model_count = 0

            for model in module.models:
                homebestmodel = CoreModel.objects(name=model.__amname__).first()

                if not homebestmodel:
                    new_model = CoreModel(
                        name=model.__amname__,
                        module=homebest_module,
                        description=model.__amdescription__,
                        ).save()

                    print("MODEL - {}: SUCCESS".format(new_model.name))

                model_count = model_count + 1

            if len(module.no_admin_models) > 0 :

                for xmodel in module.no_admin_models:
                    homebestmodel = CoreModel.objects(name=xmodel.__amname__).first()
                    
                    if not homebestmodel:
                        new_model = CoreModel(
                            name=xmodel.__amname__, 
                            module=homebest_module,
                            description=xmodel.__amdescription__,
                            admin_included=False
                        ).save()

                        print("MODEL - {}: SUCCESS".format(new_model.name))

            module_count = module_count + 1

        print("Inserting provinces to database...")
        if CoreProvince.objects.count() < 88:
            with open(provinces_path) as f:
                csv_file = csv.reader(f)

                for id, row in enumerate(csv_file):
                    if not id == 0:
                        CoreProvince(
                            name=row[2]
                        ).save()

            print("Provinces done!")

        else:
            print("Provinces exists!")
        print("")
        print("Inserting cities to database...")
        
        if CoreCity.objects.count() < 1647:
            with open(cities_path) as f:
                csv_file = csv.reader(f)

                for id,row in enumerate(csv_file):
                    if not id == 0:
                        
                        CoreCity(
                            name=row[2]
                        ).save()

            print("Cities done!")
        else:
            print("Cities exists!")

        print("Inserting system roles...")
        if Role.objects.count() > 0:
            print("Role already inserted!")
        else:
            Role(
                name="Admin",
            ).save()
            
            print("Admin role inserted!")

        if not User.objects.count() > 0:
            print("Creating a SuperUser/owner...")
            _create_superuser()

    except Exception as exc:
        print(str(exc))
        return False

    return True


@bp_core.cli.command('create_superuser')
def create_superuser():
    _create_superuser()


@bp_core.cli.command("create_module")
@click.argument("module_name")
def create_module(module_name):
    try:

        if platform.system() == "Windows":
            module_path = basedir + "\\app" + "\\" + module_name
            templates_path = basedir + "\\app" + "\\" + module_name + "\\" + "templates" + "\\" + module_name 
            core_init_path = basedir + "\\app" + "\\core" + \
                "\\module_template" + "\\__init__.py"
            core_models_path = basedir + "\\app" + \
                "\\core" + "\\module_template" + "\\models.py"
            core_routes_path = basedir + "\\app" + \
                "\\core" + "\\module_template" + "\\routes.py"
        elif platform.system() == "Linux":
            module_path = basedir + "/app" + "/" + module_name
            templates_path = basedir + "/app" + "/" + module_name + "/templates" + "/" + module_name
            core_init_path = basedir + "/app" + "/core" + "/module_template" + "/__init__.py"
            core_models_path = basedir + "/app" + "/core" + "/module_template" + "/models.py"
            core_routes_path = basedir + "/app" + "/core" + "/module_template" + "/routes.py"
        else:
            raise Exception
        
        core_file_list = [core_init_path, core_models_path, core_routes_path]

        if not os.path.exists(module_path):
            os.mkdir(module_path)
            os.makedirs(templates_path)
            for file_path in core_file_list:
                file_name = os.path.basename(file_path)
                copyfile(file_path, os.path.join(module_path, file_name))
    except OSError as e:
        print("Creation of the directory failed")
        print(e)
    else:
        print("Successfully created the directory %s " % module_path)


@bp_core.cli.command("install")
def install():

    if core_install():
        print("Installation complete!")

    else:
        print("Installation failed!")


def _create_superuser():
    try:
        role = Role.objects(name="Admin").first()

        user = User(
            fname="Administrator",
            lname="Administrator",
            username = input("Enter Username: "),
            email = None,
            is_superuser = 1,
            role=role,
            created_by = "System",
        )
        user.set_password(input("Enter password: "))
        user.save()
        print("SuperUser Created!")
    except Exception as exc:
        print(str(exc))


# @bp_core.cli.command("add_registration_date_field")
# def install():
#     registrations = Registration.objects()

#     for x in registrations:
#         registrations.registered_



@bp_core.cli.command("update_payments")
def update_payments():
    """
    Update ang lahat ng payments ng studyante na dating array of objects lang
    ngayon ay magigiging array of documents na 
    """
    registrations = Registration.objects(status="registered")

    for student in registrations:
        # if student.full_registration_number in ["2021080013","2021080012"]:
        student.copy_payments = student.payments
        student.payments = []

        for payment in student.copy_payments:
            print(payment)
            student.payments.append(
                Payment(
                    deposited="No",
                    payment_mode=payment['payment_mode'],
                    amount=payment['amount'],
                    current_balance=payment['current_balance'],
                    confirm_by=payment['confirm_by'],
                    date=payment['date']
                )
            )
        
        student.save()
        print("Updated:", student.full_registration_number)


@bp_core.cli.command("move_earnings")
def move_earnings():
    from bson.objectid import ObjectId

    # old_account: User = User.objects.get(id=)
    old_account = mongo.db.auth_users.find_one({"_id": ObjectId("6100b2fe033b20cb17477807")})
    new_account = mongo.db.auth_users.find_one({"_id": ObjectId("6100b2346d74f9d4bc2eb056")})
    # new_account: User = User.objects.get(id=ObjectId("61147ed9bf92c2b45fc25ed2"))
    
    print("old account: ", old_account['earnings'])
    print("new account: ", new_account['earnings'])
    
    # earning: Earning
    for earning in old_account['earnings']:
        # print(earning)
        
        contact_person_earning = {
            "_id": earning['_id'],
            "payment_mode": earning['payment_mode'],
            "savings": earning['savings'],
            "earnings": earning['earnings'],
            "branch": earning['branch'],
            "client": earning['client'],
            "date": earning['date'],
            "registered_by": ObjectId(earning['registered_by']),
            "payment_id": ObjectId(earning['payment_id']),
            'status': earning.get('status', '')
        }
        
        mongo.db.auth_users.update_one({"_id": new_account["_id"]},
        {"$push": {
            "earnings": contact_person_earning,
        }})
    
    # print("new account updated", new_account.earnings)
    
    # new_account.save()
    
    
@bp_core.cli.command('items')
def items():
    # mongo.db.lms_office_supplies.delete_many({'branch': {'$exists': False}})
    # mongo.db.lms_student_supplies.delete_many({'branch': {'$exists': False}})
    
    ####################################### OFFICE
    # branches = mongo.db.lms_branches.find()
    # office_supplies = list(mongo.db.lms_office_supplies.find())
    
    # for branch in branches:
    #     print(branch['name'])
    #     print(list(office_supplies))
    #     for office_supply in office_supplies:
    #         mongo.db.lms_office_supplies.insert({
    #             'branch': branch['_id'],
    #             'active': office_supply['active'],
    #             'is_deleted': office_supply['is_deleted'],
    #             'is_archived': office_supply['is_archived'],
    #             'created_by': office_supply['created_by'],
    #             'description': branch['name'] + " " + office_supply['description'],
    #             'maintaining': office_supply['maintaining'],
    #             'remaining': 0,
    #             'reserve': 0,
    #             'price': 0
    #         })
    #         print(branch['name'], office_supply['description'])

    
    ################## STUDENT
    branches = mongo.db.lms_branches.find()
    student_supplies = list(mongo.db.lms_student_supplies.find())
    
    for branch in branches:
        for student_supply in student_supplies:
            mongo.db.lms_student_supplies.insert({
                'branch': branch['_id'],
                'active': student_supply['active'],
                'is_deleted': student_supply['is_deleted'],
                'is_archived': student_supply['is_archived'],
                'created_by': student_supply['created_by'],
                'description': branch['name'] + " " + student_supply['description'],
                'maintaining': student_supply['maintaining'],
                'remaining': 0,
                'released': 0,
                'is_for_sale': student_supply.get('is_for_sale', False),
                'price': student_supply.get('price', 0)
            })
            print(branch['name'], student_supply['description'])

    print("success!")


